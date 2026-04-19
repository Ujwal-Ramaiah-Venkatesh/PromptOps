# Phase 1 Research: PM Command Corpus

## Objective
Collect and analyze 200+ real Project Manager infrastructure requests to understand linguistic patterns before building the NLP parser.

## Research Outputs

### 1. PM Requests Corpus
**File:** `pm-requests-corpus.json`
- 200+ real PM commands collected from Jira, GitHub issues, PM forums
- Each entry includes: original text, source, date collected
- Used to train intent classification

### 2. Intent Classification
**File:** `intent-classification.json`
- All 200+ requests classified into 8 intent categories
- Categories: deploy, scale, rollback, monitor, audit, cost, security, diagnose
- Distribution analysis across categories

### 3. Linguistic Patterns
**File:** `linguistic-patterns.md`
- Common phrases and vocabulary PMs use
- Ambiguous patterns that need clarification
- Edge cases and contradictory commands

## Data Sources
1. **Public Jira Issues** — Infrastructure/DevOps projects
2. **GitHub Issues** — Cloud provider repos, IaC tool repos
3. **Reddit** — r/devops, r/aws, r/kubernetes
4. **Stack Overflow** — Questions tagged with infrastructure/cloud
5. **PM Community Forums** — ProductHunt, Indie Hackers

## Collection Process
1. Identify relevant sources with public infrastructure discussions
2. Extract requests using Claude Sonnet 4 batch analysis
3. Anonymize any sensitive information
4. Normalize format into standardized JSON structure
5. Validate quality: ensure requests are infrastructure-related

## Timeline
- **Week 1–2**: Collection and classification
- **Week 3**: Used to inform parser system prompt design
- **Ongoing**: Corpus expands as we discover new PM patterns
