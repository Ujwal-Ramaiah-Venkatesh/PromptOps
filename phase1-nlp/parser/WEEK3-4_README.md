# Week 3-4: NLP Parser v1 Development

**Status:** ✅ READY TO START  
**Goal:** Integrate Claude Sonnet 4 and achieve >90% accuracy on golden tests  
**Estimated Time:** 14 hours over 2 weeks

---

## 📋 Tasks Overview

| ID | Task | Status | Est. Time | Files Created |
|----|------|--------|-----------|---------------|
| PARSER-001 | Write Claude system prompt | ✅ DONE | 2 hours | `claude_system_prompt.txt` |
| PARSER-002 | Integrate Claude API | ✅ DONE | 3 hours | `claude_integration.py` |
| CORNER-001 | Document corner cases | ✅ DONE | 1 hour | `CORNER_CASES_ANALYSIS.md` |
| TEST-001 | Create corner case tests | ✅ DONE | 2 hours | `test_corner_cases.py` |
| SECURITY-001 | Input sanitization | 🔴 TODO | 2 hours | `input_sanitization.py` |
| TEST-002 | Run all 50 golden tests | 🔴 TODO | 3 hours | Golden test results |
| UI-001 | Clarification Card UI | 🔴 TODO | 2 hours | React component |

---

## 🚀 **CRITICAL FIRST STEP: Get Claude API Key**

Before you can run anything, you MUST get a Claude Sonnet 4 API key:

### **Step 1: Get API Key**

1. Go to: https://console.anthropic.com/
2. Sign in or create account
3. Navigate to "API Keys"
4. Click "Create Key"
5. Name it: "PromptOps Development"
6. Copy the key (starts with `sk-ant-...`)

### **Step 2: Set Environment Variable**

**On Windows (PowerShell):**
```powershell
$env:ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

**On Windows (Command Prompt):**
```cmd
set ANTHROPIC_API_KEY=sk-ant-your-key-here
```

**On Linux/Mac:**
```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

**Permanent (recommended):**
Create `.env` file in project root:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Then install python-dotenv:
```bash
pip install python-dotenv
```

---

## 📦 Installation

### **Prerequisites**
- Python 3.9 or higher
- pip (Python package manager)
- Git (already installed)

### **Install Dependencies**

```bash
cd c:\Users\pqm847\Documents\PromptOps

# Install required packages
pip install anthropic>=0.34.0
pip install langgraph>=0.0.20
pip install python-dotenv>=1.0.0
pip install pytest>=7.4.0
```

---

## 🧪 Testing the Integration

### **Test 1: Connection Test**

Run this first to verify your API key works:

```bash
cd phase1-nlp\parser
python claude_integration.py
```

**Expected Output:**
```
====================================================================
PromptOps - Claude Sonnet 4 Integration Test
====================================================================

1. Testing API connection...
   ✓ Connection successful

2. Testing command parsing...

Test 1: "Deploy API v2.1.0 to production"
------------------------------------------------------------
✓ Intent: deploy
✓ Confidence: 0.98
✓ Risk: high
✓ Approval: True

[... more tests ...]

====================================================================
API Usage Summary
====================================================================
request_count: 6
total_input_tokens: 30245
total_output_tokens: 12483
total_cost_usd: 0.2784

====================================================================
Test Complete!
====================================================================
```

**If you see this, you're ready to proceed!**

---

### **Test 2: Corner Case Tests**

Run comprehensive test suite:

```bash
python test_corner_cases.py
```

**Expected Output:**
```
====================================================================
PromptOps NLP Parser - Corner Case Test Suite
====================================================================

test_ambiguous_deploy_no_version ... 
📝 Testing: "Deploy the API"
✓ Intent: deploy
✓ Confidence: 0.60
⚠ Ambiguity: 2 questions
ok

test_environment_normalization_prod ...
📝 Testing: "Deploy API v2.0 to prod"
✓ Intent: deploy
✓ Risk: high | Approval: True
ok

[... 50+ tests ...]

====================================================================
CORNER CASE TEST SUMMARY
====================================================================
Tests Run: 52
Successes: 48
Failures: 3
Errors: 1
Success Rate: 92.3%
```

**Target:** >90% success rate (>47 out of 52 tests passing)

---

### **Test 3: Golden Tests**

Run the 50 official golden tests:

```bash
python -m pytest test_golden_integration.py -v
```

(Note: Need to create `test_golden_integration.py` that loads from `tests/golden-tests/commands.json`)

---

## 📊 Understanding the Parser Output

When you parse a command like: `"Deploy API v2.1.0 to production"`

You get this JSON structure:

```json
{
  "command_id": "cmd-2026-04-20-143022-a1b2c3",
  "timestamp": "2026-04-20T14:30:22Z",
  "original_command": "Deploy API v2.1.0 to production",
  "intent_type": "deploy",
  "confidence_score": 0.98,
  "target_service": "api",
  "target_env": "production",
  "parameters": {
    "version": "v2.1.0",
    "strategy": "canary"
  },
  "requires_approval": true,
  "risk_level": "high",
  "ambiguity_detected": false,
  "clarification_questions": [],
  "warnings": [
    "Production deployment requires approval from Engineering Manager"
  ],
  "estimated_cost_impact": null,
  "estimated_duration": "7-8 minutes",
  "dependencies": [],
  "rollback_plan": "Revert to previous version (v2.0.9)",
  "security_checks": [
    "User has deploy:production permission",
    "Version v2.1.0 security scan passed"
  ]
}
```

### **Key Fields:**

- **intent_type:** One of 8 categories (deploy, scale, rollback, monitor, audit, cost, security, diagnose)
- **confidence_score:** 0.0-1.0 (how confident the AI is)
- **ambiguity_detected:** true if <85% confidence
- **clarification_questions:** What to ask PM if ambiguous
- **requires_approval:** Whether human must approve
- **risk_level:** low/medium/high/critical
- **warnings:** Important alerts for PM
- **dependencies:** Prerequisites needed first
- **rollback_plan:** How to undo if something goes wrong

---

## 🔍 Debugging

### **Common Issues:**

**1. "ANTHROPIC_API_KEY not found"**
- Solution: Set environment variable (see Step 2 above)
- Verify: `echo $env:ANTHROPIC_API_KEY` (PowerShell)

**2. "API error: Invalid API key"**
- Solution: Check key starts with `sk-ant-`
- Try: Create new key at console.anthropic.com

**3. "ModuleNotFoundError: No module named 'anthropic'"**
- Solution: `pip install anthropic>=0.34.0`

**4. "Rate limit exceeded"**
- Solution: Wait 60 seconds, or upgrade API tier
- Free tier: 50 requests/minute

**5. Tests failing with JSON errors**
- Issue: Claude sometimes outputs markdown instead of pure JSON
- Solution: Check `_validate_response()` function strips markdown
- Debug: Print raw response text

---

## 💰 Cost Estimation

### **Development Phase (Week 3-4):**

| Activity | Commands | Estimated Cost |
|----------|----------|----------------|
| Initial testing | 50 | $2.50 |
| Corner case tests | 52 | $2.60 |
| Golden tests | 50 | $2.50 |
| Debugging/iteration | 200 | $10.00 |
| **Total** | **352** | **$17.60** |

### **Production Estimates:**

```python
from claude_integration import estimate_monthly_cost

# For 1,000 commands/month
print(estimate_monthly_cost(1000))
# Output: $50/month

# For 10,000 commands/month
print(estimate_monthly_cost(10000))
# Output: $500/month

# For 50,000 commands/month
print(estimate_monthly_cost(50000))
# Output: $2,500/month
```

**Note:** These costs are for Claude API only. Add infrastructure costs separately.

---

## 📈 Success Metrics

### **Week 3-4 Exit Criteria:**

✅ **PASS:** Must achieve ALL of these:

1. **Parser Accuracy:** >90% on golden tests (>45/50)
2. **Confidence Score:** Average >0.85 across all parses
3. **Ambiguity Detection:** Correctly identifies <85% confidence
4. **Response Time:** P95 <3 seconds per parse
5. **Zero Crashes:** No unhandled exceptions
6. **Cost:** <$50 total for Week 3-4 development

❌ **FAIL:** If ANY of these:

- <90% accuracy on golden tests
- Average confidence <0.80
- Response time P95 >5 seconds
- Frequent crashes or errors
- Cost >$100 (API usage out of control)

---

## 🐛 Known Issues & Limitations

### **Current Limitations (Week 3-4):**

1. **No Context Layer (Week 7-8):**
   - Can't check if version already deployed
   - Can't detect current infrastructure state
   - Can't validate resource limits

2. **No Task Decomposition (Week 5-6):**
   - Multi-step commands parsed but not decomposed yet
   - Dependencies identified but not validated

3. **No Execution (Phase 2):**
   - Parser only - doesn't actually deploy/scale/etc
   - Execution agents come in Phase 2

4. **Limited Service Discovery:**
   - Doesn't know which services exist
   - Can't validate service names (just parses)
   - Fuzzy matching not implemented yet

### **Workarounds:**

- For now, focus on **parsing accuracy**
- Execution validation comes later
- Context awareness in Week 7-8

---

## 📚 File Structure

```
phase1-nlp/parser/
├── claude_system_prompt.txt          ✅ Comprehensive system prompt (5,400 words)
├── claude_integration.py              ✅ API client + LangGraph integration
├── test_corner_cases.py               ✅ 52 corner case tests
├── CORNER_CASES_ANALYSIS.md           ✅ 15 categories documented
├── langgraph-setup.py                 ✅ Orchestration framework (from Week 1-2)
├── test_langgraph.py                  ✅ LangGraph tests (from Week 1-2)
├── WEEK3-4_README.md                  ✅ This file
├── __init__.py                        ✅ Package init (from Week 1-2)
├── ARCHITECTURE.md                    ✅ Architecture docs (from Week 1-2)
└── README.md                          ✅ Parser overview (from Week 1-2)
```

---

## 🎯 Next Steps After Week 3-4

Once you achieve >90% golden test accuracy:

**Week 5-6: Task Decomposition Engine**
- Break multi-step commands into sub-tasks
- Dependency resolution
- Parallel execution planning

**Week 7-8: Context & Memory Layer**
- DynamoDB infrastructure state store
- Drift detection
- Real-time context injection

**Week 9-10: PM Dashboard**
- React UI with command input
- Task preview screen
- Clarification card component

---

## ❓ FAQ

**Q: Do I need to pay for Claude API?**
A: Yes, but very cheap during development (~$20 for Week 3-4). Free tier: 50 req/min.

**Q: Can I use GPT-4 instead of Claude?**
A: Technically yes, but we designed prompts for Claude Sonnet 4. Would need adjustments.

**Q: What if I get <90% accuracy?**
A: Iterate on system prompt, add more examples, tune confidence thresholds.

**Q: How long does each parse take?**
A: Average 1-2 seconds. P95 should be <3 seconds.

**Q: Can I run tests in parallel?**
A: Yes, but watch API rate limits (50 req/min on free tier).

**Q: What's the difference between confidence_score and requires_approval?**
A: Confidence = AI certainty. Approval = safety policy (based on risk_level).

---

## 📞 Support

**Issues?**
- Check logs: Look for ERROR or WARNING messages
- Debug mode: Set `logging.level = DEBUG` in code
- API status: https://status.anthropic.com/

**Questions?**
- Review: `CORNER_CASES_ANALYSIS.md` (common scenarios)
- Check: System prompt (`claude_system_prompt.txt`)
- Test: Run `python claude_integration.py` to verify setup

---

## ✅ Daily Checklist

**Day 1 (Today - April 20):**
- [ ] Get Claude API key from console.anthropic.com
- [ ] Set ANTHROPIC_API_KEY environment variable
- [ ] Install dependencies: `pip install anthropic langgraph python-dotenv pytest`
- [ ] Run connection test: `python claude_integration.py`
- [ ] Verify all 6 test commands parse successfully
- [ ] Review system prompt: `claude_system_prompt.txt`
- [ ] Read corner cases: `CORNER_CASES_ANALYSIS.md`

**Day 2-3:**
- [ ] Run corner case tests: `python test_corner_cases.py`
- [ ] Achieve >80% pass rate on corner cases
- [ ] Debug any failing tests
- [ ] Tune system prompt if needed
- [ ] Document any new edge cases found

**Day 4-5:**
- [ ] Create golden test integration
- [ ] Run all 50 golden tests
- [ ] Achieve >90% accuracy (>45/50 passing)
- [ ] Measure response time (P95 <3s)
- [ ] Track API usage and costs

**Day 6-7:**
- [ ] Build input sanitization layer (SECURITY-001)
- [ ] Test prompt injection prevention
- [ ] Create Clarification Card UI (UI-001)
- [ ] Final validation: All exit criteria met
- [ ] Document Week 3-4 completion

---

**🚀 YOU'RE READY TO START! Run the connection test now:**

```bash
cd c:\Users\pqm847\Documents\PromptOps\phase1-nlp\parser
python claude_integration.py
```

**Good luck! Let's build the world's first 100% autonomous infrastructure parser!** 🤖
