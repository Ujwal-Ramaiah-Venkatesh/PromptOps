# PromptOps Quick Start Guide

Welcome to the PromptOps development team! This guide will get you up and running in 15 minutes.

## Prerequisites Checklist

Before you begin, ensure you have:

- [ ] Git installed
- [ ] Node.js 22+ installed ([download](https://nodejs.org/))
- [ ] Python 3.11+ installed ([download](https://www.python.org/downloads/))
- [ ] Docker Desktop installed ([download](https://www.docker.com/products/docker-desktop/))
- [ ] Terraform CLI 1.9+ ([download](https://www.terraform.io/downloads))
- [ ] Pulumi CLI 3.x+ ([download](https://www.pulumi.com/docs/install/))
- [ ] Code editor (VS Code recommended)
- [ ] Claude Sonnet 4 API key ([get key](https://console.anthropic.com/))
- [ ] AWS account access (sandbox/free tier)

---

## Step 1: Clone & Setup (5 minutes)

```bash
# Clone the repository
git clone <repo-url>
cd PromptOps

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
# Required: ANTHROPIC_API_KEY, AWS credentials
```

---

## Step 2: Install Dependencies (5 minutes)

### Node.js Dependencies
```bash
npm install
```

### Python Dependencies
```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Step 3: Verify Installation (2 minutes)

```bash
# Check Node.js version
node --version  # Should be 22+

# Check Python version
python --version  # Should be 3.11+

# Check Terraform
terraform --version  # Should be 1.9+

# Check Pulumi
pulumi version  # Should be 3.x+

# Check Docker
docker --version
```

---

## Step 4: AWS Setup (3 minutes)

```bash
# Configure AWS CLI
aws configure

# Test AWS access
aws sts get-caller-identity

# Should return your AWS account details
```

---

## Step 5: Test Claude API Access

Create a test file:

```bash
# test-claude.js
import Anthropic from '@anthropic-ai/sdk';
import dotenv from 'dotenv';

dotenv.config();

const client = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
});

async function testClaude() {
  const message = await client.messages.create({
    model: 'claude-sonnet-4-20250514',
    max_tokens: 100,
    messages: [
      { role: 'user', content: 'Reply with: PromptOps API connection successful!' }
    ]
  });
  
  console.log(message.content[0].text);
}

testClaude();
```

Run test:
```bash
node test-claude.js
# Should output: "PromptOps API connection successful!"
```

---

## Project Structure Overview

```
PromptOps/
├── docs/                      # 📚 Documentation
│   ├── PHASE1_BLUEPRINT.md   # Complete 12-week plan
│   ├── WEEK1_CHECKLIST.md    # Current week tasks
│   └── PROJECT_STATUS.md     # Progress tracker
│
├── config/                    # ⚙️ Configuration
│   └── command-library-schema.json  # NLP Parser contract
│
├── phase1-nlp/               # 🧠 Phase 1 Implementation
│   ├── research/             # PM command corpus
│   ├── parser/               # NLP Parser
│   ├── decomposition/        # Task decomposition engine
│   ├── context/              # Infrastructure context store
│   └── dashboard/            # PM-facing UI
│
└── tests/                    # 🧪 Test Suites
    ├── golden-tests/         # 50 golden PM commands
    └── security/             # Prompt injection tests
```

---

## Current Sprint: Week 1–2

**Goal:** Collect 200+ PM requests and build command library

### Your First Task

Check [docs/WEEK1_CHECKLIST.md](docs/WEEK1_CHECKLIST.md) and:
1. Find your assigned task
2. Review the task description
3. Check the tools you'll use (Claude Sonnet 4, LangGraph, Cursor)
4. Start working!

---

## Daily Workflow

### Morning
1. Pull latest changes: `git pull origin main`
2. Check Linear for your assigned tasks
3. Review Slack #promptops-build for updates

### During Work
1. Create feature branch: `git checkout -b feature/your-task-name`
2. Make your changes
3. Test locally
4. Commit frequently with clear messages

### End of Day
1. Push your branch: `git push origin feature/your-task-name`
2. Create Pull Request (if task complete)
3. Post update in #promptops-build

---

## Git Workflow

```bash
# Create feature branch
git checkout -b feature/task-description

# Make changes, then stage
git add <files>

# Commit with descriptive message
git commit -m "Add feature X for Week 1 Task Y"

# Push to remote
git push origin feature/task-description

# Create Pull Request on GitHub
# Minimum 1 reviewer required before merge to main
```

---

## Important Links

- **Phase 1 Blueprint**: [docs/PHASE1_BLUEPRINT.md](docs/PHASE1_BLUEPRINT.md)
- **Week 1 Tasks**: [docs/WEEK1_CHECKLIST.md](docs/WEEK1_CHECKLIST.md)
- **Status Tracker**: [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md)
- **Command Schema**: [config/command-library-schema.json](config/command-library-schema.json)

---

## Slack Channels

- **#promptops-build** — Daily updates, progress, questions
- **#promptops-incidents** — Production issues, blockers
- **#promptops-decisions** — Architecture discussions, trade-offs

---

## Need Help?

1. Check documentation in `/docs`
2. Ask in #promptops-build Slack channel
3. Review the Phase 1 Blueprint for context
4. Reach out to your team lead

---

## Phase 1 Success Criteria

Remember: Phase 2 doesn't start until Phase 1 achieves:
- ✅ >92% accuracy on 50 golden tests
- ✅ <3s p95 latency at 100 concurrent requests
- ✅ All 10 prompt injection vectors blocked
- ✅ PM Dashboard live with full approval flow

**Let's build the brain of PromptOps!** 🚀
