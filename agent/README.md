# SpecLens

**CDF Agentic QA Hackathon submission prepared for Raashid Shaik.**

SpecLens reads the official DemoBank PRD, extracts requirement bullets, routes them to test capabilities with a local TF-IDF/cosine-similarity NLP planner, then runs browser scenarios and exports evidence. It does not use an LLM or claim to be a general-purpose web agent.

## Quick start

Requirements: Python 3.11+, Node 20+, Chromium, and either the official PostgreSQL setup or the optional local PGlite runner.

From `agent/`:

```bash
python -m venv .venv
# Linux/macOS:
. .venv/bin/activate
# Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python -m playwright install chromium
python -m pytest -q
```

Start the official target using `../test-website/LOCAL_SETUP.md`, then:

```bash
python run.py --url http://localhost:5173 --api http://localhost:8000 \
  --prd ../test-website/PRD.md --output artifacts --allow-demo-target
```

For a genuine 3+ minute browser recording including the specification briefing, complete browser run and generated report, add `--demo`. The recording is continuous: the agent pauses four seconds after each scenario so viewers can inspect the result, and leaves the generated audit visible at the end. It does not speed up execution or substitute screenshots for a run.

Only use `--allow-demo-target` for the supplied synthetic DemoBank app. Transfers mutate its synthetic records. Reset the seed before comparing runs. The agent never resets a remote target or retries a state-changing action automatically.

### Optional container-compatible local runtime

The included demonstration was run with PostgreSQL compiled to WASM (PGlite 0.5.10), the official schema/seed, and a pool limited to one connection. This avoids root-only container restrictions. It is not a claim about production PostgreSQL or the organizer-hosted app.

```bash
npm ci --prefix local-runtime
npm ci --prefix ../test-website/frontend
python -m pip install -e ../test-website/backend
python launch_local.py --output artifacts --demo
```

`launch_local.py` starts the database, backend, frontend and agent in one process tree, waits for health, and terminates the services afterward. Every launch starts from the official seed. `local_backend.py` changes only the pool's connection limit for PGlite; no target business logic or seed records are patched.

## Architecture

1. **Interpret**: `planner.py` extracts exact Markdown bullets and retains source sections and stable requirement IDs.
2. **Route**: fit a TF-IDF representation of authored capability descriptions and PRD text; cosine similarity selects capability families. Scores are similarity measures, not calibrated confidence. Unknown requirements remain unverified.
3. **Execute**: `run.py` uses Playwright roles, labels, discovered account options, transaction IDs and explicit state waits. Scenario implementations are authored DemoBank adapters, not model-generated code. They cover session access, accounts, transfers, filters, profile, and a narrow viewport.
4. **Verify**: use Decimal balance arithmetic, before/after transaction comparisons, exact row-set comparisons and visible UI feedback. Read-only API calls share the browser session and supplement UI evidence; all financial mutations occur through the UI.
5. **Recover safely**: exceptions produce unverified outcomes and the next scenario continues; navigation reloads a known route and rereads current values. Failed transfers are never automatically replayed. Destructive scenarios run after ordinary transfers and use a fresh baseline per case.
6. **Export**: `results.json`, `audit.html`, one PNG and visible-text file per scenario, and an optional browser WebM recording. No cookies, passwords or request headers are exported.

## Coverage and evidence

There are 32 PRD bullets. The planner's candidate mappings are explicitly separate from assertion coverage. Only complete, directly supported bullet assertions receive requirement-level passed/failed verdicts. Remaining compound requirements are unverified even when some scenarios pass. Scenario IDs in `results.json` connect requirements to screenshots and visible text.

A failure is an observed mismatch, an unverified result is a harness/environment/coverage limitation. A click or success banner alone never establishes a pass. The report does not claim exhaustive security, accessibility, responsiveness, concurrency, rollback under process failure, or arbitrary-app generalization.

## Costs

No inference service is called: model/API calls 0, billed input/output tokens 0, inference API cost $0. CPU, browser recording, storage, development assistance and hosting costs are excluded and are not claimed to be free. Runtime is recorded in `results.json`.

## Reproducibility and integrity

Official starter commit: `c7b856cc0d7cfb367e96fda0e5c291eba10cbb10`.
The PRD SHA-256 is stored in each run. The official target source is included unchanged. The agent was developed with ChatGPT/Codex assistance; the entrant should review and understand it and confirm organizer rules on assisted development. Source inspection informed adapter integration; defect verdicts come from executed observations, not source comments.

The included report/video refer to the local compatibility environment. Rerun against the organizer-hosted URL before claiming hosted-target results. The API URL may differ from the frontend URL and must be supplied explicitly.

## Submission

1. Fork the official repository into your GitHub account as the organizer requests.
2. Copy this `agent/` directory into the fork, excluding virtual environments, node_modules, caches and service logs; commit and push. Keep the repository public.
3. Upload the walkthrough MP4 and audit PDF, plus the supporting evidence archive, to a location judges can view without access requests. Use "Anyone with the link can view" only for the intended submission files.
4. Fill out https://forms.gle/qviV38D1uMDir3Pq8 with the public repository, video, audit and cost links.
5. Check access in a signed-out/incognito window before submitting.

Email deadline: Wednesday October 21, 2026, 6 PM Eastern / 5 PM Central.
