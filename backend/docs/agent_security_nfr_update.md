# Agent Coordination, Security, and NFR Update

Date: 2026-03-13

## 1) Unified Agent Coordination Layer

Implemented a shared orchestration module for agent execution:

- File: `src/agents/orchestrator.py`
- Capabilities:
  - Task state machine: `created -> running/retrying -> succeeded/failed/timed_out`
  - Timeout control per task
  - Retry policy per task
  - Transition history for debugging and postmortem analysis
- Integrated into:
  - `POST /api/trip/create` (profile + itinerary stages)
  - `POST /api/trip/evaluate` (post-trip evaluation stage)
  - `POST /api/trip/profile/analyze` (profile stage)

Configurable env vars (with defaults in `.env.example`):

- `AGENT_PROFILE_TIMEOUT_SECONDS`
- `AGENT_PROFILE_RETRIES`
- `AGENT_ITINERARY_TIMEOUT_SECONDS`
- `AGENT_ITINERARY_RETRIES`
- `AGENT_EVAL_TIMEOUT_SECONDS`
- `AGENT_EVAL_RETRIES`

## 2) Traceability and Log Tracking

Implemented end-to-end trace id propagation:

- Python APIs:
  - File: `src/observability.py`
  - Middleware sets/propagates `X-Trace-Id`
  - Structured log format includes `[trace=...]`
- Node APIs:
  - File: `src/server.js`
  - Request middleware injects `traceId`
  - Response includes `X-Trace-Id`

Result:

- All main error responses now carry `trace_id`
- Request latency and status are trace-correlated in logs

## 3) Security and Compliance Hardening

### 3.1 Removed hardcoded secrets

- `DEEPSEEK_API_KEY` hardcoded fallback removed
- `AMAP_API_KEY` and `AMAP_SECURITY_KEY` moved to environment variables
- DB password fallback updated to empty default (no embedded password)

Updated files:

- `run_trip.py`
- `src/agents/itinerary_planner_agent.py`
- `src/navigation/main.py`
- `src/service/navigation.py`
- `src/service/poi_search.py`

### 3.2 Unified environment variable management

- Added `backend/.env.example` as a single configuration template
- Includes auth/db/agent timeout/map/LLM keys

### 3.3 Log sanitization and least exposure

- Sensitive values are masked in logs (`password/token/secret/api_key/bearer`)
- Internal exception details are no longer returned to API clients
- API error messages now return concise text + `trace_id`

## 4) Non-Functional Validation

Validation script:

- `scripts/non_functional_validation.py`
- Measures:
  - Response time metrics (`avg`, `p95`, `p99`, `max`)
  - Concurrency throughput (RPS)
  - Error rate/success rate
  - Basic recovery signal (first-try success + retry recovery)

### 4.1 Baseline results (local test)

#### Endpoint: `GET http://127.0.0.1:3204/`

- Requests: `80`
- Concurrency: `16`
- Throughput: `371.98 rps`
- Success rate: `100.0%`
- Error rate: `0.0%`
- Latency: `avg 20.45ms`, `p95 145.72ms`, `p99 147.62ms`, `max 147.79ms`
- Stability: first try success (`attempts_used=1`)

#### Endpoint: `GET http://127.0.0.1:3001/api/health`

- Requests: `80`
- Concurrency: `16`
- Throughput: `272.41 rps`
- Success rate: `100.0%`
- Error rate: `0.0%`
- Latency: `avg 39.49ms`, `p95 159.17ms`, `p99 165.15ms`, `max 171.53ms`
- Stability: first try success (`attempts_used=1`)

### 4.2 Recovery strategy now in place

- Runtime recovery:
  - Timeout + retry policy in orchestrator
  - Explicit timeout state for failed tasks
- Operational recovery:
  - Trace-id-based fault isolation
  - Error responses include trace id for rapid correlation

## 5) Reproduction Commands

From `backend/`:

```bash
python scripts/non_functional_validation.py --url http://127.0.0.1:3204/ --requests 80 --concurrency 16 --timeout 4
python scripts/non_functional_validation.py --url http://127.0.0.1:3001/api/health --requests 80 --concurrency 16 --timeout 4
```
