# Phase 1: Foundation & NLP Intent Engine

**Timeline:** April 7 – June 27, 2026 | 12 Weeks | Sprint 1–6

## Objective
Build the NLP Parser that converts PM's plain-English commands into structured, machine-executable JSON task lists — with zero hallucinations.

## Weekly Breakdown

### Week 1–2 (Apr 7–18): User Intent Research & Command Library
**Goal:** Understand PM vocabulary before writing any parser code.

**Tasks:**
1. Collect 200+ real PM requests from Jira, GitHub, PM forums
2. Classify into 8 intent categories: deploy, scale, rollback, monitor, audit, cost, security, diagnose
3. Build Command Library JSON schema
4. Write 50 "Golden Test" PM commands (permanent regression suite)
5. Set up LangGraph agent framework

**Deliverables:**
- `research/pm-requests-corpus.json` (200+ real requests)
- `research/intent-classification.json` (8 categories)
- `config/command-library-schema.json`
- `tests/golden-tests/commands.json` (50 test commands)
- `parser/langgraph-setup.py` (orchestration backbone)

---

### Week 3–4 (Apr 21–May 2): NLP Parser v1 — Intent-to-JSON
**Goal:** Build first version that converts PM text → structured JSON.

**Tasks:**
1. Write system prompt for Claude Sonnet 4 (strict JSON output)
2. Build ambiguity detection (confidence < 85% → clarification)
3. Build Clarification Card UI component
4. Implement input sanitization layer (pre-LLM filter)
5. Run all 50 golden tests (target >90% accuracy)

**Deliverables:**
- `parser/system-prompt.txt`
- `parser/ambiguity-detector.py`
- `dashboard/components/ClarificationCard.tsx`
- `parser/input-sanitizer.py`
- `tests/golden-tests/results-week3.json`

---

### Week 5–6 (May 5–16): Task Decomposition Engine
**Goal:** Decompose each intent into 5–15 ordered DevOps sub-tasks.

**Tasks:**
1. Design decomposition prompt
2. Build sub-task JSON schema (with rollback_action)
3. Implement dependency graph resolver
4. Test 10 complex multi-step commands
5. Build Task Preview UI

**Deliverables:**
- `decomposition/decomposition-prompt.txt`
- `config/subtask-schema.json`
- `decomposition/dependency-resolver.py`
- `tests/decomposition-tests.json`
- `dashboard/components/TaskPreview.tsx`

---

### Week 7–8 (May 19–May 30): Context & Memory Layer
**Goal:** Remember infrastructure state between sessions.

**Tasks:**
1. Design Infrastructure Context Store (DynamoDB)
2. Build context injection pipeline
3. Implement context refresh (drift detection every 15 min)
4. Build drift detection alert UI
5. Test context-aware parsing

**Deliverables:**
- `context/context-store-schema.json`
- `context/context-injector.py`
- `context/drift-detector.py`
- `dashboard/components/DriftAlert.tsx`
- `tests/context-tests.json`

---

### Week 9–10 (Jun 2–13): PM Dashboard Shell
**Goal:** Build the front-end interface PMs will use.

**Tasks:**
1. Design dashboard layout (4 panels)
2. Build command input component (real-time intent preview)
3. Build approval flow UI (risky actions require typed confirmation)
4. Build audit trail view (immutable log)
5. Mobile responsiveness (for 3 AM on-call)

**Deliverables:**
- `dashboard/layouts/MainDashboard.tsx`
- `dashboard/components/CommandInput.tsx`
- `dashboard/components/ApprovalFlow.tsx`
- `dashboard/components/AuditTrail.tsx`
- `dashboard/styles/mobile.css`

---

### Week 11–12 (Jun 16–27): Integration & Testing
**Goal:** Wire everything together and prove reliability.

**Tasks:**
1. End-to-end integration test (all 8 intent categories)
2. Full regression suite (50 golden tests at >92% accuracy)
3. Adversarial testing (prompt injection attempts)
4. Performance test (p95 < 3s at 100 concurrent requests)
5. Phase 1 stakeholder demo

**Deliverables:**
- `tests/integration/e2e-tests.js`
- `tests/golden-tests/final-results.json` (>92% pass)
- `tests/security/adversarial-tests.json`
- `tests/performance/load-test-results.json`
- `docs/phase1-demo-transcript.md`

---

## Exit Criteria
All must be met before Phase 2 begins:

- ✅ NLP Parser achieving >92% accuracy on 50 golden test commands
- ✅ Command Library JSON schema complete (8 intents, 50+ examples)
- ✅ Task decomposition working for 10 complex commands with rollback actions
- ✅ Infrastructure Context Store connected to AWS with 15-min drift detection
- ✅ PM Dashboard live: command input, intent preview, approval flow, audit trail
- ✅ Performance: <3s p95 latency at 100 concurrent requests
- ✅ Security: all 10 prompt injection test vectors blocked

---

## Risk Mitigation

| Risk | Severity | Mitigation |
|------|----------|------------|
| LLM returns malformed JSON | High | JSON Schema validation + 3 retries + fallback to PM rephrase |
| Ambiguity scoring misses dangerous misinterpretation | Extreme | All prod-tagged resources require explicit PM confirmation |
| Context store grows too large | Medium | Chunk context; inject only relevant resources per command |
| Prompt injection via PM input | Extreme | Pre-LLM sanitization layer + delimiter wrapping |

---

## AI Tool Assignments

| Tool | Role |
|------|------|
| Claude Sonnet 4 | Primary LLM for NLP parsing, decomposition, classification, evaluation |
| LangGraph | Agent orchestration (multi-step flows, state, retries, parallelization) |
| Cursor (Agent Mode) | AI-powered IDE for backend/frontend autonomous development |
| v0.dev | Rapid UI component generation (PM dashboard) |
| OPA (Open Policy Agent) | Deterministic security guardrails (input sanitization in Rego) |
