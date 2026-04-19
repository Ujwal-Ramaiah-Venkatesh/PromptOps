# Week 1 Immediate Action Items
**Due:** First 5 working days (Before any code)

## Infrastructure Setup
- [ ] Provision AWS sandbox account (free tier)
- [ ] Share credentials via secure method (1Password/AWS IAM Identity Center)
- [ ] Verify AWS CLI access and test basic commands

## Repository & Project Management
- [ ] Create GitHub organization (if needed)
- [ ] Set up branch protection on `main` (minimum 1 PR reviewer)
- [ ] Create Linear project "PromptOps Launch"
- [ ] Input Phase 1 Week 1 tasks into Linear
- [ ] Assign task owners

## Team Access & Tools
- [ ] All engineers obtain Anthropic API keys for Claude Sonnet 4
- [ ] Set up rate limit monitoring for Claude API
- [ ] Install Node.js 22+
- [ ] Install Python 3.11+
- [ ] Install Docker Desktop
- [ ] Install Terraform CLI 1.9+
- [ ] Install Pulumi CLI 3.x+
- [ ] Install k6 (load testing tool)

## Team Communication
- [ ] Set up Slack channels:
  - [ ] #promptops-build (daily updates)
  - [ ] #promptops-incidents (production issues)
  - [ ] #promptops-decisions (architectural choices)

## Team Alignment
- [ ] Conduct 2-hour team kickoff meeting
- [ ] Walk through full 4-phase blueprint
- [ ] Ensure every engineer understands all phases
- [ ] Q&A session for clarifications

## Week 1–2 Research Tasks

### Task 1: Collect 200+ Real PM Requests
**Owner:** Research Lead | **Duration:** 3 days | **Tool:** Claude Sonnet 4 batch analysis

- [ ] Identify 5+ public sources (Jira, GitHub issues, PM forums, Reddit)
- [ ] Scrape/collect raw PM infrastructure requests
- [ ] Store in `phase1-nlp/research/pm-requests-corpus.json`
- [ ] Use Claude Sonnet 4 to batch-analyze linguistic patterns
- [ ] Document common phrases, ambiguities, and edge cases

### Task 2: Classify Requests into 8 Intent Categories
**Owner:** NLP Engineer | **Duration:** 2 days | **Tool:** Claude Sonnet 4

The 8 intent categories:
1. **deploy** — Deploy new services, apps, or infrastructure
2. **scale** — Scale up/down existing resources
3. **rollback** — Revert to previous state
4. **monitor** — Set up observability, alerts, dashboards
5. **audit** — Review security, compliance, costs
6. **cost** — Cost analysis, optimization, budget alerts
7. **security** — Security hardening, patching, IAM changes
8. **diagnose** — Troubleshoot incidents, investigate issues

- [ ] Classify all 200+ collected requests into exactly one category
- [ ] Store in `phase1-nlp/research/intent-classification.json`
- [ ] Document edge cases where classification is ambiguous
- [ ] Calculate distribution across 8 categories

### Task 3: Build Command Library JSON Schema
**Owner:** Backend Engineer | **Duration:** 2 days | **Tool:** Cursor Agent Mode

- [ ] Define schema fields: `intent_type`, `target_service`, `target_env`, `parameters`, `confidence_floor`
- [ ] Create JSON Schema file at `config/command-library-schema.json`
- [ ] Add validation rules (e.g., `target_env` must be one of: dev, staging, prod)
- [ ] Document schema in README

### Task 4: Write 50 "Golden Test" PM Commands
**Owner:** QA Engineer | **Duration:** 3 days | **Tool:** Claude Sonnet 4

- [ ] Create 50 real-world PM command examples
- [ ] Cover all 8 intent categories across all environments
- [ ] Include edge cases: ambiguous, multi-step, contradictory
- [ ] Store in `tests/golden-tests/commands.json`
- [ ] Document expected output for each command
- [ ] This becomes permanent regression suite (never deleted, only added to)

### Task 5: Set Up LangGraph Agent Framework
**Owner:** Backend Engineer | **Duration:** 2 days | **Tool:** LangGraph + Cursor

- [ ] Install LangGraph dependencies
- [ ] Create basic agent structure: nodes, edges, state management
- [ ] Implement retry logic for LLM failures
- [ ] Create orchestration backbone at `phase1-nlp/parser/langgraph-setup.py`
- [ ] Write tests for basic flow execution

---

## Success Metrics for Week 1–2
- [ ] 200+ PM requests collected and stored
- [ ] All requests classified into 8 categories
- [ ] Command Library schema complete and documented
- [ ] 50 golden test commands written with expected outputs
- [ ] LangGraph framework running with basic test flow

---

## Notes
- No parser code should be written in Week 1–2
- Focus is entirely on understanding PM language patterns
- All research outputs feed directly into Week 3–4 parser development
