# PromptOps

**Agentic DevOps Utility** — Manage cloud infrastructure using plain English.

## Phase 1: Foundation & NLP Intent Engine
**Timeline:** April 7 – June 27, 2026 | 12 Weeks | Sprint 1–6

### Current Status
🚧 **Week 1**: User Intent Research & Command Library (In Progress)

## Project Overview
PromptOps allows Project Managers and startup founders to manage cloud infrastructure without knowing DevOps commands. The system converts plain-English requests into executable infrastructure tasks.

### Architecture (4 Phases)
1. **Phase 1** (Current): NLP Intent Engine — Brain of the system
2. **Phase 2**: Architect Agent — Infrastructure provisioning
3. **Phase 3**: SRE Agent — Observability & incident response
4. **Phase 4**: Chaos Testing Agent — Resilience validation

## Phase 1 Exit Criteria
- ✅ >92% accuracy on 50 golden test commands
- ✅ Task decomposition with rollback actions
- ✅ Infrastructure context store with drift detection
- ✅ PM Dashboard with approval flow
- ✅ <3s p95 latency at 100 concurrent requests
- ✅ All prompt injection vectors blocked

## Getting Started

### Prerequisites
- Node.js 22+
- Python 3.11+
- Docker Desktop
- Terraform CLI 1.9+
- Pulumi CLI 3.x+
- Claude Sonnet 4 API access

### Installation
```bash
# Clone repository
git clone <repo-url>
cd PromptOps

# Install dependencies (coming soon)
npm install
pip install -r requirements.txt
```

## Project Structure
```
/docs/                  # Architecture & design documents
/phase1-nlp/           # Phase 1: NLP Intent Engine
  /research/           # PM command research & analysis
  /parser/             # NLP Parser implementation
  /decomposition/      # Task decomposition engine
  /context/            # Infrastructure context store
  /dashboard/          # PM-facing UI
/tests/                # Test suites
  /golden-tests/       # 50 golden PM commands
  /security/           # Prompt injection & adversarial tests
/config/               # Configuration files
```

## Team Communication
- **#promptops-build**: Daily updates
- **#promptops-incidents**: Production issues
- **#promptops-decisions**: Architectural choices

## License
MIT (or your preferred license)
