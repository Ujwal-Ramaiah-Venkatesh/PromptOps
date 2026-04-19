# ✅ Repository Setup Complete — What's Next?

**Status:** Foundation laid. Ready for Week 1 research tasks.  
**Date:** April 19, 2026

---

## What We Just Built

### 1. Git Repository ✅
- Initialized with proper `.gitignore` and `.gitattributes`
- 4 commits on `master` branch
- Clean working directory (ready for branch protection)

### 2. Project Structure ✅
```
PromptOps/
├── docs/           ← Phase 1 blueprint, checklists, status tracker
├── config/         ← Command Library JSON schema (contract)
├── phase1-nlp/     ← Parser, decomposition, context, dashboard (empty, ready for code)
└── tests/          ← Golden tests (50 target), security tests
```

### 3. Documentation ✅
- **README.md** — Project overview for newcomers
- **QUICKSTART.md** — 15-minute setup guide for team
- **docs/PHASE1_BLUEPRINT.md** — Complete 12-week detailed plan
- **docs/WEEK1_CHECKLIST.md** — Immediate action items
- **docs/PROJECT_STATUS.md** — Progress tracker

### 4. Configuration Files ✅
- **package.json** — Node.js dependencies (Anthropic SDK, LangGraph, Express)
- **requirements.txt** — Python dependencies (anthropic, langgraph, boto3, pydantic)
- **.env.example** — Environment template with all required keys
- **config/command-library-schema.json** — The contract between NLP Parser and all agents

---

## 🚨 Critical: Before Writing Any Code

### Immediate Action Items (Next 2 Days)

#### 1. Infrastructure Access
- [ ] **AWS Sandbox Account**: Provision free tier account
  - Go to https://aws.amazon.com/free/
  - Create new account or use existing sandbox
  - Note Account ID, Access Key, Secret Key
  - Add to `.env` file (copy from `.env.example`)

#### 2. API Access
- [ ] **Claude Sonnet 4 API Key**: 
  - Visit https://console.anthropic.com/
  - Create API key for `claude-sonnet-4-20250514`
  - Add to `.env` as `ANTHROPIC_API_KEY`
  - Set up rate limit monitoring

#### 3. Team Setup
- [ ] **GitHub**: 
  - Push to GitHub: `git remote add origin <url> && git push -u origin master`
  - Enable branch protection on `main`/`master` (require 1 PR review)
- [ ] **Linear**: 
  - Create project "PromptOps Launch"
  - Create cycle "Phase 1 Week 1-2"
  - Import tasks from `docs/WEEK1_CHECKLIST.md`
  - Assign task owners
- [ ] **Slack**: 
  - Create #promptops-build
  - Create #promptops-incidents  
  - Create #promptops-decisions

#### 4. Dev Environment (Every Team Member)
- [ ] Install Node.js 22+
- [ ] Install Python 3.11+
- [ ] Install Docker Desktop
- [ ] Install Terraform CLI 1.9+
- [ ] Install Pulumi CLI 3.x+
- [ ] Install k6 (load testing)
- [ ] Clone repo and run `npm install` + `pip install -r requirements.txt`

#### 5. Team Kickoff (2-Hour Meeting)
**Agenda:**
1. Walk through entire 4-phase blueprint (30 min)
2. Deep dive into Phase 1 exit criteria (15 min)
3. Week 1-2 task assignments (20 min)
4. Tool training: Claude Sonnet 4, LangGraph, Cursor (30 min)
5. Q&A and clarifications (25 min)

**Outcome:** Every engineer must understand:
- Why Phase 1 is the most critical phase
- How their Week 1 task feeds into Week 3-4 parser development
- The 8 intent categories and why they were chosen
- The >92% accuracy exit gate and why it's non-negotiable

---

## 📋 Week 1-2 Research Tasks (Start Immediately After Setup)

### Task 1: Collect 200+ PM Requests
**Owner:** Research Lead  
**Duration:** 3 days  
**Output:** `phase1-nlp/research/pm-requests-corpus.json`

**Sources to scrape:**
- Public Jira issues (search: "infrastructure", "deploy", "scale", "AWS")
- GitHub issues in repos: terraform-aws-modules, pulumi/pulumi, aws/aws-cli
- Reddit: r/devops, r/aws, r/kubernetes (sort by top posts, last 6 months)
- Stack Overflow: questions tagged [infrastructure], [aws], [devops]

**Tool:** Use Claude Sonnet 4 batch API to extract and normalize PM language

### Task 2: Classify into 8 Intent Categories
**Owner:** NLP Engineer  
**Duration:** 2 days  
**Output:** `phase1-nlp/research/intent-classification.json`

For each of 200+ requests, classify into exactly one:
1. deploy
2. scale
3. rollback
4. monitor
5. audit
6. cost
7. security
8. diagnose

**Tool:** Claude Sonnet 4 with system prompt enforcing single-category classification

### Task 3: Build Command Library
**Owner:** Backend Engineer  
**Duration:** 2 days  
**Output:** Populate `config/command-library-schema.json` with 50+ real examples

Take the schema that exists and add real PM command examples to the `examples` array.

### Task 4: Write 50 Golden Test Commands
**Owner:** QA Engineer  
**Duration:** 3 days  
**Output:** `tests/golden-tests/commands.json`

Create 50 test cases covering:
- All 8 intent categories
- All 3 environments (dev, staging, prod)
- Simple (1-step) and complex (multi-step) commands
- Ambiguous commands that should trigger clarification
- Edge cases (contradictory, incomplete)

**Format:**
```json
{
  "test_id": "deploy-001",
  "pm_input": "Deploy the API to production",
  "expected_intent_type": "deploy",
  "expected_target_service": "api",
  "expected_target_env": "prod",
  "expected_parameters": {
    "action_verb": "deploy",
    "resource_type": "application"
  },
  "expected_confidence_floor": 0.85,
  "notes": "Simple deploy command"
}
```

### Task 5: Set Up LangGraph Framework
**Owner:** Backend Engineer  
**Duration:** 2 days  
**Output:** `phase1-nlp/parser/langgraph-setup.py`

Build orchestration backbone:
- Define nodes: input validation, LLM call, output validation, retry
- Define edges: flow between nodes
- Implement state management: carry context between nodes
- Implement retry logic: up to 3 retries on LLM failure
- Create basic test flow: input → parse → output

---

## ⚠️ Week 1-2 Exit Gate

Before moving to Week 3-4 (Parser v1), verify:

- ✅ 200+ PM requests collected and stored
- ✅ All requests classified into 8 categories
- ✅ 50 golden test commands written with expected outputs
- ✅ LangGraph framework running with basic test flow
- ✅ Command Library schema populated with real examples

**If any of the above are incomplete, Week 3-4 cannot start.**

---

## 🔗 Quick Links

- **Setup Guide**: [QUICKSTART.md](QUICKSTART.md)
- **Phase 1 Plan**: [docs/PHASE1_BLUEPRINT.md](docs/PHASE1_BLUEPRINT.md)
- **Week 1 Tasks**: [docs/WEEK1_CHECKLIST.md](docs/WEEK1_CHECKLIST.md)
- **Status Tracker**: [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md)
- **Schema**: [config/command-library-schema.json](config/command-library-schema.json)

---

## 🎯 Remember the Mission

**PromptOps Goal:** Allow PMs to manage infrastructure using plain English.

**Phase 1 Goal:** Build the NLP brain that converts PM text → executable JSON with >92% accuracy.

**Week 1-2 Goal:** Understand PM language patterns before writing a single line of parser code.

---

## Questions?

- Post in #promptops-build
- Review docs/ folder
- Ask your team lead
- Check this repo's README.md

**Now go provision that AWS account and get those Claude API keys!** 🚀
