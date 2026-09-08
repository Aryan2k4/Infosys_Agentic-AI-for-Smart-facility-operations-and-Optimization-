"""
Real Gemini-backed provider. Requires GEMINI_API_KEY in the environment.
Uses the google-genai SDK — same choice as AG-ASE-2026 for consistency.

MODEL DEPRECATION NOTE (fixed AGAIN here — second time this exact bug has
hit this project, see git history/prior comment below the fold): this
provider defaulted to "gemini-2.0-flash", then "gemini-2.5-flash" — BOTH
now dead or unreliable for real users (a live user's actual error log
showed a 404 on "models/gemini-2.0-flash" with Google's own error message
recommending "models/gemini-3.6-flash" — meaning by the time that error
was hit, gemini-2.5-flash AND gemini-2.5-flash-lite had ALREADY failed
too, since MODEL_FALLBACK_CHAIN only surfaces the LAST model's error when
every model in the chain fails). Every real API call was returning 404s
and silently falling back to MockProvider — again the exact "looks like
mock, key seems fine, no visible error" failure mode.

Now defaults to gemini-3.6-flash (Google's own docs still list this as a
stable model as of Sept 2026 — safest current default), falling back to
gemini-3.7-flash (newer, GA August 2026 — very capable but newer means a
higher chance of tighter rate limits or tier restrictions on some keys, so
it's second not first) then gemini-2.5-flash-lite (confirmed still priced/
alive as of Sept 2026, cheapest, good last-resort). gemini-2.0-flash and
gemini-2.5-flash are DELIBERATELY removed from this chain, not just
reordered — they're confirmed dead/unreliable, so retrying them wastes an
attempt before reaching a model that might actually work.

IF THIS BREAKS AGAIN: don't just swap in whatever model a future error
message recommends and call it fixed — Google renames/replaces its
recommended-replacement chain every few months (2.0→2.5→3.6/3.7 is the
pattern so far). Check https://ai.google.dev/gemini-api/docs/deprecations
AND https://ai.google.dev/gemini-api/docs/models for what's CURRENTLY
stable (not just currently recommended-as-a-replacement, since today's
replacement is next quarter's deprecated model) before updating this list.
"""
import os
import logging
from typing import Callable
from app.services.ai_providers.base import AIProvider

logger = logging.getLogger(__name__)

# Tried in order; only advances to the next if the current one raises —
# survives a model being retired without falling all the way back to mock.
MODEL_FALLBACK_CHAIN = ["gemini-3.6-flash", "gemini-3.7-flash", "gemini-2.5-flash-lite"]


class GeminiProvider(AIProvider):
    def __init__(self, model: str = MODEL_FALLBACK_CHAIN[0]):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY not set. Add it to backend/.env to use GeminiProvider, "
                "or use MockProvider for local dev without a key."
            )
        from google import genai
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self._models_to_try = [model] + [m for m in MODEL_FALLBACK_CHAIN if m != model]

    def _call_with_fallback(self, fn):
        last_error = None
        attempted = []
        for model in self._models_to_try:
            try:
                result = fn(model)
                if model != self.model:
                    logger.warning(f"Gemini model '{self.model}' failed; '{model}' succeeded instead. "
                                    f"Consider updating the default in gemini_provider.py.")
                return result
            except Exception as e:
                last_error = e
                attempted.append(f"{model}: {e}")
                continue
        # Log EVERY model's failure, not just the last one — a fresh error
        # message showing only the last-tried model's 404 (e.g.
        # gemini-2.5-flash-lite) makes it easy to assume just that one
        # model needs updating, when actually every model ahead of it in
        # the chain failed too. This exact ambiguity delayed diagnosing a
        # real production issue once already.
        logger.error("All Gemini models in the fallback chain failed:\n" + "\n".join(attempted))
        raise last_error

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        def call(model):
            response = self.client.models.generate_content(
                model=model,
                contents=user_prompt,
                config={"system_instruction": system_prompt},
            )
            return response.text
        return self._call_with_fallback(call)

    def run_agentic_task(self, system_prompt: str, task_prompt: str, tools: list[Callable]) -> dict:
        """
        Real agentic execution: passes the tool functions directly to
        Gemini. The SDK's Automatic Function Calling (AFC) lets the model
        decide which tools to call and in what order — it calls them,
        feeds results back to the model, and loops until the model returns
        a final answer (default cap: 10 remote calls).
        """
        from google.genai import types

        def call(model):
            response = self.client.models.generate_content(
                model=model,
                contents=task_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    tools=tools,
                ),
            )

            trace = []
            history = getattr(response, "automatic_function_calling_history", None) or []
            for content in history:
                for part in getattr(content, "parts", []) or []:
                    fc = getattr(part, "function_call", None)
                    fr = getattr(part, "function_response", None)
                    if fc:
                        trace.append({"tool": fc.name, "args": dict(fc.args or {}), "result": None})
                    elif fr and trace:
                        trace[-1]["result"] = fr.response

            return {"final_text": response.text, "tool_calls": trace}

        return self._call_with_fallback(call)
