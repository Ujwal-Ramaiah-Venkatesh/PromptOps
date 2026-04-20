# PromptOps - Quick Start Guide

**Last Updated:** April 20, 2026  
**Current Phase:** Week 3-4 - NLP Parser v1 Development

---

## 🚀 **START HERE**

### **Step 1: Get Claude API Key (5 minutes)**

1. Go to: **https://console.anthropic.com/**
2. Sign in or create account
3. Navigate to **"API Keys"**
4. Click **"Create Key"**
5. Name it: **"PromptOps Development"**
6. Copy the key (starts with `sk-ant-...`)

### **Step 2: Set Environment Variable**

**Windows PowerShell:**
```powershell
$env:ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

**Permanent (Recommended):**
Create file `.env` in project root:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### **Step 3: Install Dependencies**

```bash
cd c:\Users\pqm847\Documents\PromptOps
pip install anthropic>=0.34.0 langgraph>=0.0.20 python-dotenv>=1.0.0 pytest>=7.4.0
```

### **Step 4: Test Connection**

```bash
cd phase1-nlp\parser
python claude_integration.py
```

**Expected:** ✓ Connection successful

### **Step 5: Run Tests**

```bash
python test_corner_cases.py
```

**Target:** >90% pass rate (>47/52 tests)

---

## 📁 **Project Structure**

```
PromptOps/
├── phase1-nlp/
│   ├── research/                      # Week 1-2 ✅
│   │   ├── pm-requests-corpus.json    # 143 real PM requests
│   │   └── intent-classification.json # 8 intent categories
│   └── parser/                        # Week 3-4 🔴 IN PROGRESS
│       ├── claude_system_prompt.txt   # ✅ System prompt (5,400 words)
│       ├── claude_integration.py      # ✅ API client
│       ├── test_corner_cases.py       # ✅ 52 tests
│       ├── CORNER_CASES_ANALYSIS.md   # ✅ 15 categories
│       └── WEEK3-4_README.md          # ✅ Complete guide
├── tests/
│   └── golden-tests/
│       └── commands.json              # 50 official tests
├── config/
│   └── command-library-schema.json    # Command schema
├── docs/
│   ├── UI_DESIGN_SPEC.md              # Complete UI spec
│   └── PHASE1_BLUEPRINT.md            # 12-week plan
├── PromptOps_Complete_Blueprint_100percent_Automation.md  # 125 pages
├── PromptOps_Market_Research_Report.md                    # Market analysis
├── WEEK3-4_STATUS.md                  # ✅ Current status
└── QUICK_START.md                     # ← YOU ARE HERE
```

---

## 🎯 **What We've Built**

### **Week 1-2 ✅ COMPLETE**
- PM request corpus (143 commands)
- Intent classification (8 categories)
- Golden test suite (50 tests)
- Command library schema
- LangGraph orchestration framework
- Complete documentation

### **Week 3-4 🟡 IN PROGRESS (57% done)**
- ✅ System prompt (handles 15 corner case categories)
- ✅ Claude API integration (with retry, validation, cost tracking)
- ✅ Corner case tests (52 tests ready to run)
- 🔴 Input sanitization (TODO)
- 🔴 Golden test validation (TODO - CRITICAL)
- 🔴 Clarification UI (TODO)

---

## ⚡ **Command Cheat Sheet**

### **Test Connection:**
```bash
python claude_integration.py
```

### **Run Corner Case Tests:**
```bash
python test_corner_cases.py
```

### **Check API Usage:**
```python
from claude_integration import ClaudeParser
parser = ClaudeParser()
stats = parser.get_usage_stats()
print(stats)
```

### **Estimate Monthly Costs:**
```python
from claude_integration import estimate_monthly_cost
print(estimate_monthly_cost(10000))  # For 10K commands/month
```

### **Parse Single Command:**
```python
from claude_integration import ClaudeParser
parser = ClaudeParser()
success, output, error = parser.parse_command("Deploy API v2.0 to production")
if success:
    print(f"Intent: {output['intent_type']}")
    print(f"Confidence: {output['confidence_score']}")
```

---

## 📊 **Current Status**

### **Completed (4/7 tasks):**
- ✅ System prompt written
- ✅ Claude API integrated
- ✅ Corner cases documented (75 scenarios)
- ✅ Test suite created (52 tests)

### **Remaining (3/7 tasks):**
- 🔴 Input sanitization layer
- 🔴 Run golden tests (>90% accuracy required)
- 🔴 Clarification Card UI

### **Exit Criteria:**
| Metric | Target | Current |
|--------|--------|---------|
| Golden test accuracy | >90% | 0% (not tested) |
| Response time (P95) | <3s | TBD |
| API cost (Week 3-4) | <$50 | $0 |

---

## 🐛 **Troubleshooting**

### **"ANTHROPIC_API_KEY not found"**
```bash
# Check if set:
echo $env:ANTHROPIC_API_KEY

# Set it:
$env:ANTHROPIC_API_KEY="sk-ant-your-key"
```

### **"ModuleNotFoundError"**
```bash
pip install anthropic langgraph python-dotenv pytest
```

### **"Rate limit exceeded"**
- Wait 60 seconds
- Free tier: 50 requests/minute

### **Tests failing?**
1. Check API key is valid
2. Review test output for specific errors
3. Check system prompt at `claude_system_prompt.txt`
4. Increase logging: `logging.level = DEBUG`

---

## 💰 **Cost Reference**

### **API Pricing:**
- Input: $3/million tokens
- Output: $15/million tokens

### **Estimated Costs:**
- 1 command: ~$0.05
- 100 commands: ~$5
- 1,000 commands: ~$50
- 10,000 commands: ~$500/month

### **Week 3-4 Budget:**
- Corner case tests (52): ~$2.60
- Golden tests (50): ~$2.50
- Debugging (100): ~$5.00
- **Total:** ~$10 for Week 3-4

---

## 📚 **Key Documents**

| Document | Purpose |
|----------|---------|
| [WEEK3-4_README.md](phase1-nlp/parser/WEEK3-4_README.md) | Complete guide with FAQ |
| [WEEK3-4_STATUS.md](WEEK3-4_STATUS.md) | Current progress report |
| [CORNER_CASES_ANALYSIS.md](phase1-nlp/parser/CORNER_CASES_ANALYSIS.md) | 75 edge cases |
| [PromptOps_Complete_Blueprint_100percent_Automation.md](PromptOps_Complete_Blueprint_100percent_Automation.md) | Full vision (125 pages) |
| [PromptOps_Market_Research_Report.md](PromptOps_Market_Research_Report.md) | Market analysis |

---

## 🎯 **Next Actions (Priority Order)**

1. **TODAY:** Get Claude API key ⚡
2. **TODAY:** Run connection test ⚡
3. **TODAY:** Run corner case tests ⚡
4. **Day 2-3:** Build input sanitization
5. **Day 4-5:** Run golden tests (>90% required)
6. **Day 6-7:** Build Clarification UI (optional)

---

## 📞 **Need Help?**

### **API Issues:**
- Status: https://status.anthropic.com/
- Docs: https://docs.anthropic.com/

### **Code Issues:**
- Check logs in terminal
- Review error messages
- Test individual functions

### **Questions:**
- Review: `WEEK3-4_README.md` (comprehensive FAQ)
- Check: `CORNER_CASES_ANALYSIS.md` (75 scenarios)
- Read: System prompt (`claude_system_prompt.txt`)

---

## ✅ **Success Checklist**

**Before proceeding to Week 5-6, you MUST:**
- [ ] Claude API key obtained and working
- [ ] Connection test passes (6 commands parse successfully)
- [ ] Corner case tests: >80% pass rate
- [ ] Input sanitization: 10 prompt injection patterns blocked
- [ ] Golden tests: >90% accuracy (>45/50 passing)
- [ ] Response time: P95 <3 seconds
- [ ] API costs: <$50 for Week 3-4
- [ ] No unhandled exceptions

---

## 🚀 **You're Ready!**

**Everything is built and ready to test. Just need the API key!**

```bash
# Get API key from: https://console.anthropic.com/
# Set environment variable
# Run: python claude_integration.py
# Watch the magic happen! 🤖
```

**Good luck building the world's first 100% autonomous infrastructure parser!** 🎉
