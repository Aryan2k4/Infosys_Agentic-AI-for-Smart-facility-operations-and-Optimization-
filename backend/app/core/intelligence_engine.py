"""
Intelligence Engine — the LLM reasoning layer that sits above individual
agents (Energy, and later Maintenance/Occupancy/Security/Cost).

Two distinct capabilities live here:

1. summarize_energy_analysis() — a single-shot LLM call that takes the
   Energy Agent's already-computed rule-based output and writes a plain-
   English briefing. Useful, but NOT agentic: we decided what to compute
   and just asked the model to narrate it.

2. investigate_energy() — a genuinely agentic run. The model is given a
   goal and a set of real tools (app/core/agent_tools.py) and DECIDES for
   itself which analyses to run, in what order, and whether the evidence
   warrants flagging the finding to another agent. This is the actual
   "agentic AI" component of the platform, as distinct from a fixed
   pipeline or a single summarization call.
"""
from app.services.ai_providers.factory import get_ai_provider
from app.core.agent_tools import ALL_TOOLS
from app.core.maintenance_tools import ALL_TOOLS as MAINTENANCE_TOOLS
from app.core.occupancy_tools import ALL_TOOLS as OCCUPANCY_TOOLS
from app.core.security_tools import ALL_TOOLS as SECURITY_TOOLS

SUMMARY_SYSTEM_PROMPT = (
    "You are the Intelligence Engine of a facility operations AI platform. "
    "You receive structured analytics and rule-based recommendations from a "
    "domain agent (e.g. the Energy Agent) and must synthesize them into a "
    "short, prioritized, plain-English briefing for a facility manager. "
    "Be concrete and reference the actual numbers given. Do not invent data "
    "that wasn't provided. Keep it under 200 words."
)

INVESTIGATION_SYSTEM_PROMPT = (
    "You are the Energy Agent of a facility operations AI platform, "
    "investigating a building's energy efficiency. You have tools to pull "
    "consumption data, submeter breakdowns, anomalies, temperature and "
    "occupancy correlations, and an ML-based forecast (available at 1h, 6h, "
    "or 24h horizons — each backed by a separately trained model with "
    "different accuracy; the forecast tool's response includes a confidence "
    "field you should factor into how much weight you give the prediction, "
    "especially at 24h where accuracy is only marginal). You do NOT have to "
    "call every tool — decide which ones are actually relevant based on "
    "what you learn as you go, and only check longer forecast horizons if "
    "the near-term signal actually warrants it. If you find evidence "
    "suggesting an equipment fault (e.g. multiple high-severity anomalies) "
    "rather than a scheduling issue, use the flag_for_maintenance_review "
    "tool to hand it off. When you have enough information, write a short "
    "(under 200 words) plain-English investigation summary explaining what "
    "you checked, why, and what you found. Reference actual numbers from "
    "the tool results."
)


MAINTENANCE_INVESTIGATION_SYSTEM_PROMPT = (
    "You are the Maintenance Agent of a facility operations AI platform, "
    "investigating the health of a building's equipment fleet. You have "
    "tools to pull the fleet-wide health summary, drill into a specific "
    "asset's ML-predicted health (remaining useful life, health score, "
    "predicted maintenance date, and the model's own confidence), list the "
    "assets currently most at risk, and open a real maintenance work order. "
    "You do NOT have to call every tool — start broad (fleet summary), "
    "narrow to at-risk assets only if the fleet summary suggests a problem, "
    "and only open work orders for assets where the evidence is clear "
    "(Critical status, or Warning with limited remaining life) — do not "
    "open work orders speculatively for every asset you inspect. When you "
    "have enough information, write a short (under 200 words) plain-"
    "English investigation summary explaining what you checked, why, and "
    "what you found, referencing actual numbers from the tool results."
)


OCCUPANCY_INVESTIGATION_SYSTEM_PROMPT = (
    "You are the Occupancy Agent of a facility operations AI platform, "
    "investigating space utilization across a building. You have tools to "
    "pull the building-wide occupancy summary, drill into a specific "
    "zone's current status, list zones currently overcrowded, check the "
    "status of restricted zones specifically (e.g. server rooms — worth "
    "checking even when nowhere near the general overcrowding threshold, "
    "since ANY occupancy there is unusual), and — important — flag a "
    "restricted zone for Security review if it shows occupancy, since "
    "headcount data alone can't confirm who is present or whether their "
    "access was authorized. Only use the security handoff tool for "
    "zone_type='restricted' zones with actual current occupancy, not for "
    "ordinary workspace/meeting-room overcrowding. When you have enough "
    "information, write a short (under 200 words) plain-English "
    "investigation summary explaining what you checked, why, and what you "
    "found, referencing actual numbers from the tool results."
)


SECURITY_INVESTIGATION_SYSTEM_PROMPT = (
    "You are the Security Agent of a facility operations AI platform, "
    "investigating access-control activity across a building. You have "
    "tools to pull the building-wide security summary, list recent events "
    "the anomaly detector flagged (with an anomaly score — higher means "
    "more statistically unusual), check a specific access point's "
    "configured risk level (low/medium/high), and open a real security "
    "alert. The anomaly detector is honest but imperfect (see its own "
    "precision/recall in the tool results if surfaced) — weigh anomaly "
    "score together with the access point's risk level, and only open "
    "alerts where the evidence is clear (a high anomaly score at a "
    "medium/high-risk access point, or a repeated-denial pattern) rather "
    "than for every flagged event. When you have enough information, "
    "write a short (under 200 words) plain-English investigation summary "
    "explaining what you checked, why, and what you found, referencing "
    "actual numbers from the tool results."
)


def summarize_energy_analysis(analysis: dict, recommendations: list[dict]) -> tuple[str, str]:
    provider, provider_name = get_ai_provider()

    consumption = analysis.get("consumption", {})
    breakdown = analysis.get("breakdown", {})
    trend = analysis.get("trend_pct_vs_prev_period")
    occupancy = analysis.get("occupancy", {})

    user_prompt = f"""
Energy analysis for this period:
- Total consumption: {consumption.get('total_kwh')} kWh
- Peak load: {consumption.get('peak_kwh')} kWh
- Trend vs previous period: {trend}%
- Load breakdown: HVAC {breakdown.get('hvac_pct')}%, Lighting {breakdown.get('lighting_pct')}%, \
Plug load {breakdown.get('plug_load_pct')}%, Other {breakdown.get('other_pct')}%
- Unoccupied-period load: {occupancy.get('unoccupied_load_pct_of_occupied', 'n/a')}% of occupied-period average

Top recommendations (already ranked by severity):
{chr(10).join(f"- [{r['severity'].upper()}] {r['title']}: {r['description']}" for r in recommendations[:5])}

Write a short briefing synthesizing the above for a facility manager.
"""
    return provider.generate(SUMMARY_SYSTEM_PROMPT, user_prompt), provider_name


def investigate_energy(building_id: str = "BLD-HQ-01") -> dict:
    """
    Runs the agentic investigation: the model (or, with MockProvider, a
    simulated stand-in) decides which of the available tools to call and
    in what order to reach a conclusion about this building's energy
    efficiency. Returns the final narrative plus the full decision trace.
    """
    provider, provider_name = get_ai_provider()
    task_prompt = f"Investigate energy efficiency for building {building_id}."
    result = provider.run_agentic_task(INVESTIGATION_SYSTEM_PROMPT, task_prompt, ALL_TOOLS)
    return {
        "building_id": building_id,
        "final_summary": result["final_text"],
        "tool_calls": result["tool_calls"],
        "tool_call_count": len(result["tool_calls"]),
        "provider": provider_name,
    }


def investigate_maintenance(building_id: str = "BLD-HQ-01") -> dict:
    """
    Same genuinely-agentic pattern as investigate_energy(), pointed at the
    Maintenance Agent's tools instead. The model (or MockProvider's
    conditional simulation) decides which assets are worth a closer look
    and whether the evidence warrants opening a real work order.
    """
    provider, provider_name = get_ai_provider()
    task_prompt = f"Investigate equipment health for building {building_id}."
    result = provider.run_agentic_task(MAINTENANCE_INVESTIGATION_SYSTEM_PROMPT, task_prompt, MAINTENANCE_TOOLS)
    return {
        "building_id": building_id,
        "final_summary": result["final_text"],
        "tool_calls": result["tool_calls"],
        "tool_call_count": len(result["tool_calls"]),
        "provider": provider_name,
    }


def investigate_occupancy(building_id: str = "BLD-HQ-01") -> dict:
    """
    Same genuinely-agentic pattern, pointed at the Occupancy Agent's tools.
    The model decides which zones are worth a closer look and whether a
    restricted zone's occupancy warrants a real handoff to Security.
    """
    provider, provider_name = get_ai_provider()
    task_prompt = f"Investigate space utilization and occupancy for building {building_id}."
    result = provider.run_agentic_task(OCCUPANCY_INVESTIGATION_SYSTEM_PROMPT, task_prompt, OCCUPANCY_TOOLS)
    return {
        "building_id": building_id,
        "final_summary": result["final_text"],
        "tool_calls": result["tool_calls"],
        "tool_call_count": len(result["tool_calls"]),
        "provider": provider_name,
    }


def investigate_security(building_id: str = "BLD-HQ-01") -> dict:
    """
    Same genuinely-agentic pattern, pointed at the Security Agent's tools.
    The model decides which flagged events warrant a real alert, weighing
    anomaly score against access-point risk level rather than alerting on
    every flag.
    """
    provider, provider_name = get_ai_provider()
    task_prompt = f"Investigate access-control activity for building {building_id}."
    result = provider.run_agentic_task(SECURITY_INVESTIGATION_SYSTEM_PROMPT, task_prompt, SECURITY_TOOLS)
    return {
        "building_id": building_id,
        "final_summary": result["final_text"],
        "tool_calls": result["tool_calls"],
        "tool_call_count": len(result["tool_calls"]),
        "provider": provider_name,
    }
