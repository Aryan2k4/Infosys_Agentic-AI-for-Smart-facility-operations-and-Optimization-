# Infosys_Agentic AI for Smart Facility Operations and Optimization

> **Submission scope: Milestones 1–3 only.** Everything in this repository — all four
> agents (Energy, Maintenance, Occupancy, Security), the ML models, the agentic
> tool-calling layer, and both dashboards — is fully implemented and tested (39/39
> passing). The "Next up (Milestone 4)" section near the end is **forward-looking
> roadmap text only** — none of it is built, and none of it is part of this submission.

MIT Licensed — see [`LICENSE`](./LICENSE). For how this codebase extends to future
milestones without rewrites, see [`ARCHITECTURE.md`](./ARCHITECTURE.md).

## Milestone 1 (Weeks 1–2): Energy Intelligence & Monitoring — ✅ Implemented

This milestone delivers:

| Requirement | Where it lives |
|---|---|
| Integrate utility and IoT data | `backend/app/services/data_service.py` (`ingest_from_csv`, `.csv`/`.xlsx` upload) + `backend/data/build_dataset.py` |
| Build Energy Agent | `backend/app/agents/energy_agent.py` |
| Develop energy consumption analytics | `backend/app/utils/energy_analytics.py` |
| Create energy monitoring dashboard | `frontend/src/pages/energy/EnergyDashboardPage.jsx` + `GET /api/energy/dashboard` |
| Generate energy efficiency recommendations | `EnergyAgent.recommend()` (rule-based engine, 7 rules) |

### Two additional components — actual ML and LLM, not just rules

The rule-based recommendations above are deterministic heuristics, not machine learning.
Two more components were added specifically to include real predictive ML and real LLM
reasoning, since a rule-engine alone doesn't demonstrate either:

**1. ML forecasting — three separate trained models, one per horizon** (`backend/ml_models/energy/train_forecast_model.py`)
- Trains **1h, 6h, and 24h** forecasting models *separately* rather than one model for
  everything — near-term forecasting (where the current reading is highly informative) and
  next-day forecasting (where it barely matters) are genuinely different problems, so one
  model tuned for both would be worse at each
- For each horizon: compares Linear Regression / Random Forest / Gradient Boosting, evaluated
  with **both** a held-out time-ordered test split **and** 5-fold `TimeSeriesSplit`
  cross-validation (folds always train-on-past/validate-on-future, never shuffled — shuffling
  a time series leaks future information into training)
- Compared against **two** naive baselines per horizon ("no change from now" and "same value
  as this time yesterday") since "no change" stops being a fair baseline as the horizon grows
- Reports feature importances for the winning model — not just an accuracy number
- **Honest results, not cherry-picked**: 1h and 6h models are strong (~65-67% better than the
  best naive baseline). The 24h model is only marginally better (~5%) — this is reported as-is
  in `model_metrics.json` and surfaced as a `confidence: low` flag in the API/UI rather than
  hidden, because forecasting a full day out from 15-minute-resolution features is a genuinely
  hard problem and claiming otherwise would be dishonest
- Served via `GET /api/energy/forecast?horizon=1h|6h|24h`

**2. LLM-based Intelligence Engine** (`backend/app/core/intelligence_engine.py`)
- Takes the Energy Agent's structured analysis + recommendations and asks an LLM to
  synthesize a short plain-English briefing for a facility manager
- Uses the same `AIProvider` abstraction pattern as AG-ASE-2026: `MockProvider` (no API
  key needed, deterministic — default), `GroqProvider` (real Groq, recommended — fast,
  generous free tier), and `GeminiProvider` (real Gemini) are all interchangeable via
  `AI_PROVIDER` in `.env`. If a real provider is configured but its key is missing/invalid,
  this falls back to `MockProvider` gracefully instead of crashing the request — the
  response's `provider` field always reflects what actually ran
- Served via `GET /api/energy/briefing`

To train the forecast models (already trained and included in this delivery, re-run if
you swap in a new dataset):
```bash
cd backend
python ml_models/energy/train_forecast_model.py
```

To use real Groq instead of the mock briefing/investigation, set in `backend/.env`:
```
AI_PROVIDER=groq
GROQ_API_KEY=your_key_here   # get one free at https://console.groq.com/keys
```

### Three distinct AI/decision layers — not just one

It's worth being explicit about what's actually "AI" here, since it's easy to build
something that *looks* AI-flavored but is really just rules with a chatbot bolted on:

1. **Rule-based recommendations** (`EnergyAgent.recommend()`) — deterministic heuristics.
   Not ML, not LLM. Fast, explainable, always available.
2. **ML forecasting** (`ml_models/energy/train_forecast_model.py`) — three actual trained
   regression models (1h/6h/24h horizons), each evaluated against naive baselines and
   cross-validated. See the ML section above for honest, unfiltered metrics.
3. **Agentic investigation** (`app/core/agent_tools.py` + `investigate_energy()`) — the
   model is given *tools*, not pre-computed answers, and decides for itself which to call,
   in what order, and whether to hand a finding off to another agent. This is the part
   that makes the system "agentic" in the actual technical sense (tool-use + autonomous
   multi-step decision-making), as opposed to a single LLM call that narrates data we
   already gathered.

   - `GET /api/energy/investigate` — the model receives a goal ("investigate energy
     efficiency for this building") and 7 real tools: consumption summary, submeter
     breakdown, anomaly detection, temperature correlation, occupancy correlation, a
     **horizon-aware** ML forecast (the model picks 1h/6h/24h itself), and a
     maintenance-flagging handoff. It is *not* told which ones to use.
   - **Genuine multi-step branching, not a fixed checklist**: e.g. the 24h forecast is only
     checked if the 1h forecast already shows a meaningful shift (≥8%) — a real decision made
     from an *intermediate result*, not a hardcoded sequence. Temperature correlation is only
     checked if HVAC is a large load share; maintenance is only flagged if there's real
     anomaly evidence (2+ high-severity). Every branch point is driven by what an earlier
     tool actually returned.
   - With `AI_PROVIDER=mock` (default, no API key): the branches above are scripted (clearly
     labeled `[MockProvider — simulated agentic run...]` in the output) so the flow can be
     built, demoed, and tested without a key — but the *shape* of the reasoning (call, inspect
     result, decide next action) is genuine, not just a fixed list of calls run every time.
   - With `AI_PROVIDER=groq` (recommended) + a real `GROQ_API_KEY`, or `AI_PROVIDER=gemini`
     + `GEMINI_API_KEY`: **this is the real thing** — the model itself reads each tool's
     result and decides the next call, via Groq's OpenAI-compatible tool calling (manual
     loop, `app/services/ai_providers/groq_provider.py`) or Gemini's Automatic Function
     Calling. Swap the key in and the exact same tools, same endpoint, same frontend all
     become genuinely autonomous — nothing else changes.
   - The full decision trace (every tool called, its arguments, and its result) is
     returned and rendered live in the dashboard's **Agent Reasoning Trace** panel —
     an auditable record of what the AI actually did, not just what it said.

### UI

Light and dark themes (toggle in the header, persisted across sessions), Space Grotesk /
Inter / JetBrains Mono type system, and a signature **Agent Reasoning Trace** panel that
live-reveals the agent's actual tool-call decisions rather than a static chart.

### About the data
`backend/data/build_dataset.py` builds `backend/data/raw/energy_readings_raw.csv` by
combining **three independent real, public datasets** onto a shared 15-minute timeline
(35,040 rows / 365 days, ending today):

| Signal | Real source | Notes |
|---|---|---|
| Power Consumption | PJM Interconnection hourly grid load (2002-2018) | Rescaled from grid MW to facility kWh; real diurnal/weekly/seasonal shape preserved |
| Outdoor Temperature | Environment Canada hourly weather station data (2012) | Real recorded temperatures, upsampled to 15-min |
| Occupancy | UCI "Occupancy Detection" dataset (Candanedo, 2016) | Real minute-level office sensor data; the real weekday/weekend occupied-fraction pattern is tiled across the window and converted to a small headcount |

**Important caveat, stated plainly:** these three datasets don't share an actual
overlapping real-world recording period (different buildings, different years). Each
signal's real shape, cycles, and noise are genuine — but they are stitched onto one
timeline rather than being one continuous real recording of a single building. This is
the same trade-off documented for the submeter split below, made explicit so it's never
presented as more than it is. Submeters (HVAC/Lighting/Plug-load/Other) are still derived
from the real power signal using standard commercial building load-share ratios.

This is the seam where a production deployment swaps in a live utility API poller,
IoT/BACnet feed, and a real building's occupancy sensors — nothing downstream (agent,
analytics, API, dashboard) needs to change.

**If your team has a real single-source dataset** (e.g. a Kaggle set with power +
temperature + occupancy already recorded together, like `hammadkhan29/energy-consumption-temperature-occupancy-dataset`),
that's strictly better than this composite — just point `ENERGY_RAW_CSV` at it with
matching column names (`building_id, sensor_id, timestamp, total_kwh, hvac_kwh,
lighting_kwh, plug_load_kwh, other_kwh, outdoor_temp_c, occupancy_count`) and re-run
`POST /api/energy/ingest`. See [`DATASET_REQUEST.md`](./DATASET_REQUEST.md) for a
ready-to-send note asking a teammate for that file.

### Running locally

**Backend**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
# -> http://localhost:8000/docs (Swagger UI)
# Data auto-ingests on first startup.
```
> **Windows note:** if `uvicorn app.main:app --reload` fails with an "Application
> Control policy has blocked this file" error, use `python -m uvicorn app.main:app
> --reload` instead — routes through `python.exe` rather than the blocked
> `uvicorn.exe` entrypoint. Same fix applies to other pip-installed `.exe` tools.

**Frontend**
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
# -> http://localhost:5173/energy
```

**Or with Docker**
```bash
docker-compose up --build
```

### API endpoints (Milestone 1)
- `POST /api/energy/ingest` — (re)load data from the configured source feed
- `POST /api/energy/ingest/upload` — upload a `.csv` or `.xlsx` file directly (e.g. a
  teammate's Kaggle export) and ingest it. Column names are auto-detected/mapped —
  see [`DATASET_REQUEST.md`](./DATASET_REQUEST.md)
- `GET /api/energy/consumption` — total/avg/peak/min consumption summary
- `GET /api/energy/analytics` — full analysis: consumption + submeter breakdown + trend +
  anomalies + temperature correlation + occupancy correlation
- `GET /api/energy/recommendations` — ranked rule-based efficiency recommendations
- `GET /api/energy/forecast?horizon=1h|6h|24h` — **ML**: multi-horizon consumption
  prediction (separate trained model per horizon, with an honest `confidence` field)
- `GET /api/energy/briefing` — **LLM (single-shot)**: plain-English synthesis of pre-computed analysis
- `GET /api/energy/investigate` — **Agentic**: model decides which tools to call and in what
  order (including which forecast horizon to check); returns the final narrative plus the
  full tool-call trace
- `GET /api/energy/dashboard` — single call powering the dashboard UI
- `GET /api/energy/readings?limit=N` — raw time series for charting (includes
  `outdoor_temp_c` and `occupancy_count` per row)

### Tests
```bash
cd backend
pytest tests/ -v
```
13/13 passing — covers ingestion, consumption summary, analytics shape, recommendation
validity, dashboard payload, readings pagination, temperature/occupancy correlation,
`.xlsx` upload with auto-mapped external column names, multi-horizon ML forecast, LLM
briefing, and the agentic investigation (verifies the agent actually calls multiple real
tools with real results, not a canned response).

### What the Energy Agent actually does
1. Pulls ingested readings for a building
2. Runs analytics: totals/peaks, HVAC/Lighting/Plug/Other breakdown, trend vs. prior
   period, per-hour-of-day anomaly detection (z-score against that hour's own historical
   mean), off-hours "phantom load" ratio, temperature correlation (weather-normalized
   load response), and occupancy correlation (load tied to actual headcount vs. not)
3. Applies 7 rule-based checks (off-hours waste, HVAC over-share, rising trend, lighting
   over-share, repeated anomaly clusters, unoccupied-period waste, HVAC not tracking
   outdoor temperature) to generate ranked recommendations with estimated savings %
4. Exposes it all through `run()` — the single entrypoint other agents/the API call

This agent structure (init → analyze → recommend → run) is meant as the template the
Maintenance, Occupancy, Security, and Cost agents in later milestones should follow. The
UCI occupancy dataset used here is directly reusable as a starting point for a future
Occupancy Agent.

### Milestone 2 (Weeks 3–4): Predictive Maintenance — ✅ Implemented

This milestone adds a second, independent agent — Maintenance — built on the exact same
four-step template as the Energy Agent (`__init__` → `analyze()` → `recommend()` → `run()`),
so the codebase now proves the architecture generalizes rather than being a one-off.

**Data source.** NASA C-MAPSS Turbofan Engine Degradation Simulation, FD001 subset
(Saxena & Goebel, 2008) — real aircraft-engine sensor measurements, run to actual
mechanical failure. 100 engines for training, plus NASA's own official held-out test set
of 100 more engines with a separate answer key (`RUL_FD001.txt`). The sensor *values* and
degradation patterns are 100% real; the sensor *names* and asset identities are relabeled
onto fictional facility equipment (e.g. "sensor 11" → `vibration_index`, "Engine unit 42"
→ `Chiller-042`) — a disclosed, honest relabeling, not real facility sensor data. Full
detail in `backend/data/build_maintenance_dataset.py`.

**ML model.** Predicts Remaining Useful Life (RUL) — operating cycles remaining before
an asset needs maintenance. Linear Regression, Random Forest, Gradient Boosting, and
Histogram Gradient Boosting were compared, plus a blended ensemble of the top performers;
**the ensemble blend won** with held-out test MAE of **14.47 cycles** (R² 0.753) vs. a
naive "always guess the average" baseline of 34.83 cycles — a **58.5% improvement**.
Also trains a quantile-regression model alongside the point-prediction model, so every
RUL prediction ships with an honest 80% prediction interval (p10–p90), not just a single
number — empirical coverage on the held-out set is **80.0%**, matching the nominal target.
Evaluated on NASA's own 100 held-out test engines, genuinely never seen during training.
Exact numbers: `backend/ml_models/maintenance/model_metrics.json`.

**Maintenance Agent** (`backend/app/agents/maintenance_agent.py`):
- `analyze()` — scores every asset in the fleet from its latest sensor readings using the
  trained RUL model, computing a 0–100 health score and status (Excellent/Good/Warning/Critical)
- `recommend()` — turns that into ranked maintenance alerts
- `run()` — single entrypoint used by the `/maintenance/fleet` endpoint and by other agents

**Agentic layer** (`GET /maintenance/investigate`, same pattern as the Energy Agent's
`/api/energy/investigate`): the model is given real tools — check fleet-wide health, check
one asset's health, list at-risk assets, open a work order — and decides for itself which
to call and whether to act, rather than following a fixed script. The full tool-call trace
is returned and can be rendered in the Agent Trace Viewer.

**Cross-agent handoff.** In Milestone 1, the Energy Agent's `flag_for_maintenance_review`
tool was a placeholder that only logged a line. It now calls the *same* `open_work_order()`
function the Maintenance Agent uses internally, so a real row is written to the
`maintenance_events` table tagged `source="energy_agent"`. The Work Orders panel visually
distinguishes these handoff orders from ones the Maintenance Agent opened on its own — this
is the first evidence in the project of two agents genuinely cooperating, not just two
features sitting side by side in one repo. Covered by
`test_cross_agent_handoff_creates_real_work_order` in `backend/tests/test_maintenance.py`.

**New API endpoints (Milestone 2)** — all under `/maintenance`, see
`backend/app/api/maintenance_routes.py`:

| Method | Endpoint | What it does |
|---|---|---|
| POST | `/maintenance/ingest` | Loads the NASA C-MAPSS fleet dataset into the database |
| GET | `/maintenance/fleet` | Fleet summary + all scored assets + top alerts (powers the dashboard) |
| GET | `/maintenance/assets` | List of assets with health scores |
| GET | `/maintenance/assets/{asset_id}` | Single-asset health detail |
| GET | `/maintenance/assets/{asset_id}/history` | Raw sensor history for one asset |
| GET | `/maintenance/alerts` | Ranked maintenance alerts |
| GET | `/maintenance/work-orders` | All work orders, including `energy_agent` handoffs |
| GET | `/maintenance/investigate` | Agentic endpoint — model chooses tools, full trace returned |
| GET | `/maintenance/model/scatter` | Actual-vs-predicted RUL on the 100 held-out NASA test engines |

**Frontend.** New `/maintenance` dashboard route reachable from the sidebar
(`components/shell/AppShell.jsx`): 4 fleet KPI cards, a hand-built SVG **Fleet Health
Radar** (asset points arranged on a circle, distance from center = health score, color by
status, hover tooltip), a sortable Asset Table, a Maintenance Alerts panel, a Work Orders
panel that highlights `energy_agent` handoffs, and a reliability scatter chart
(actual vs. predicted RUL, same diagnostic pattern as the Energy forecast scatter).

**Tests.** 24/24 passing (13 from Milestone 1 + 11 new for Milestone 2) —
`cd backend && python -m pytest tests/ -v`.

### Milestone 3 (Weeks 5–6): Occupancy & Security Intelligence — ✅ Implemented

Two more independent agents, same four-step template (`__init__` → `analyze()` →
`recommend()` → `run()`) as Energy and Maintenance — the architecture now has four
working instances, not two.

**Occupancy Agent** (`backend/app/agents/occupancy_agent.py`)

*Data source.* The real classifier is trained directly on the UCI "Occupancy Detection"
dataset (Candanedo & Feldheim, 2016) — real minute-level ambient sensor readings
(temperature, humidity, light, CO2, humidity ratio) with ground-truth occupancy from
time-stamped photos. Trained on `datatraining.csv`, evaluated on UCI's own two official
held-out test splits (`datatest.csv` + `datatest2.csv`), genuinely never touched during
training. For the *live multi-zone fleet* (8 zones — open offices, meeting rooms,
cafeteria, lobby, server room, executive wing), a real day-of-week/time-of-day occupancy
*profile* is extracted from that same real dataset and projected onto each zone with its
own capacity and independent noise — a disclosed synthetic step, same honesty pattern as
the Energy module's submeter split. Full detail in `backend/data/build_occupancy_dataset.py`.

*ML model.* Logistic Regression vs. Gradient Boosting compared for real-time occupancy
detection from ambient sensor readings; **Logistic Regression won** with held-out
**accuracy 98.25%** (F1 0.964) vs. a naive majority-class baseline of 75.7% — comfortably
clearing the ≥80% evaluation target. Exact numbers: `backend/ml_models/occupancy/model_metrics.json`.

*What it does:* scores every zone's current headcount/utilization into a status bucket
(Low/Moderate/Busy/Overcrowded), rolls that up into a building-wide summary, and builds
hour-of-day heatmap data per zone. Rule-based recommendations flag overcrowded zones and
chronically underused workspace.

**Security Agent** (`backend/app/agents/security_agent.py`)

*Data source.* **Fully synthetic and disclosed as such** — there is no practical, license-
clear public dataset of real building access-control events. Generated with a realistic
statistical structure (business-hours traffic shape, per-door risk profiles) and
*deliberately injected, labeled* anomalies (unauthorized restricted-zone access,
after-hours access, repeated-denial/brute-force patterns) so detection can be evaluated
honestly rather than just asserted. Full disclosure and methodology in
`backend/data/build_security_dataset.py`.

*ML model.* Unsupervised Isolation Forest, trained **without** ever seeing the injected
ground-truth label, then scored against it afterward: **precision 0.45, recall 0.59, F1
0.51** — realistic, not oversold, numbers for unsupervised anomaly detection.
Per-anomaly-type breakdown (e.g. 72.6% of unauthorized restricted-zone access events
detected, vs. 29.8% of repeated-denial patterns) reported honestly rather than only the
aggregate. This validates the detection *method* against known injected patterns — it has
**not** been validated against real security incidents, and that limitation is stated
wherever these results are surfaced. Exact numbers: `backend/ml_models/security/model_metrics.json`.

*What it does:* runs the live detector against the recent event stream, ranks flagged
events by anomaly score, and opens real alerts for the ones where score and access-point
risk level together clear the bar — not every flagged event.

**Cross-agent handoff (Occupancy → Security).** If a *restricted* zone (e.g. the Server
Room) shows any occupancy at all, the Occupancy Agent can't tell who's inside or whether
their access was authorized — that's exactly the gap the Security Agent's badge-event data
fills. The Occupancy Agent's `flag_restricted_zone_for_security_review` tool calls the
*same* `security_service.open_alert()` function the Security Agent uses internally, so a
real row lands in the `security_alerts` table tagged `source="occupancy_agent"` — the
second real cross-agent handoff in this codebase, following the same pattern as
Energy→Maintenance in Milestone 2.

**Agentic layer.** `GET /occupancy/investigate` and `GET /security/investigate`, same
pattern as the other two agents: real tools, the model decides which to call and whether
to act, full tool-call trace returned. Covered by `test_investigate_runs_and_returns_trace`
in both `test_occupancy.py` and `test_security.py`.

**New API endpoints (Milestone 3):**

| Method | Endpoint | What it does |
|---|---|---|
| POST | `/occupancy/ingest` | Loads the multi-zone occupancy dataset |
| GET | `/occupancy/building` | Building summary + all scored zones + heatmap + alerts (powers the dashboard) |
| GET | `/occupancy/zones/{zone_id}` | Single-zone status detail |
| GET | `/occupancy/zones/{zone_id}/history` | Raw headcount history for one zone |
| GET | `/occupancy/alerts` | Ranked occupancy alerts, including security handoffs |
| GET | `/occupancy/investigate` | Agentic endpoint |
| POST | `/security/ingest` | Loads the access-control event dataset |
| GET | `/security/building` | Building summary + flagged events + access points + alerts |
| GET | `/security/events` | Recent raw access events (ground-truth anomaly labels excluded — the live API never leaks the answer key) |
| GET | `/security/alerts` | All alerts, including Occupancy Agent handoffs |
| GET | `/security/investigate` | Agentic endpoint |

**Frontend.** Two new dashboard routes reachable from the sidebar: `/occupancy`
(KPI row, hour-of-day utilization heatmap, zone status table, agent investigation panel,
alerts) and `/security` (KPI row, flagged-events list with anomaly scores, access-point
risk panel, agent investigation panel, alerts panel that visually distinguishes Occupancy
Agent handoffs).

**Tests.** 39/39 passing (24 from Milestones 1–2 + 15 new for Milestone 3) —
`cd backend && python -m pytest tests/ -v`.

### Future roadmap — not part of this submission (Milestone 4, unbuilt)
- Cost Optimization Agent + executive dashboard
- Cross-agent orchestrator that can reason across all four agents at once, not just
  point-to-point handoffs (Energy→Maintenance, Occupancy→Security)
- Swap CSV ingestion for a live connector (utility API / MQTT / BACnet / CMMS / real
  access-control system)
- Persist recommendations + track acceptance/dismissal
- Production deployment (see original roadmap's Week 7–8 scope)

---

## Contributors

| Name | Role |
|---|---|
| Aryan Goswami | Architecture, ML Forecasting Pipeline, Agentic AI Layer, Backend-Frontend Integration |
| Dharshna | Frontend & Dashboard UI, Theme System, Agent Trace Visualization |
| Ramya Sri | Data Pipeline, Analytics Engine, Testing, Documentation |

## License

This project is licensed under the MIT License — see [LICENSE](./LICENSE) for details.
