# Testing Guide - Week 5-6 Decomposition Engine

## Prerequisites

### 1. Get Claude API Key

1. Visit: https://console.anthropic.com/settings/keys
2. Create a new API key
3. Copy the key (starts with `sk-ant-`)

### 2. Set Environment Variable

**PowerShell:**
```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-your-key-here"
```

**Bash (Git Bash):**
```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

**Verify it's set:**
```bash
echo $ANTHROPIC_API_KEY
```

## Test Suites

### 1. Unit Tests (25 tests)

**Location:** `phase1-nlp/decomposition/test_decomposition.py`

**Run:**
```bash
cd c:/Users/pqm847/Documents/PromptOps
python phase1-nlp/decomposition/test_decomposition.py
```

**What it tests:**
- ✅ Simple commands (5 tests): deploy, scale, rollback, monitor, cost
- ✅ Complex multi-step (10 tests): canary, blue-green, DB migration, etc.
- ✅ Dependency edge cases (5 tests): parallel, sequential, diamond patterns
- ✅ Failure scenarios (5 tests): missing params, ambiguous commands

**Expected:** >21/25 passing (>85% success rate)

**Estimated time:** 2-3 minutes  
**Estimated cost:** ~$0.60 (25 decompositions × $0.025)

---

### 2. Integration Tests (7 tests)

**Location:** `tests/integration/decomposition_integration_test.py`

**Run:**
```bash
cd c:/Users/pqm847/Documents/PromptOps
python tests/integration/decomposition_integration_test.py
```

**What it tests:**
- ✅ Full pipeline: Parser → Decomposition → Dependency Resolution
- ✅ Production deployments with approval gates
- ✅ Scaling operations with validation
- ✅ Rollback plan generation
- ✅ Complex multi-step workflows
- ✅ Parallelization detection
- ✅ Cost tracking accuracy
- ✅ LangGraph state management

**Expected:** 7/7 passing (100%)

**Estimated time:** 1-2 minutes  
**Estimated cost:** ~$0.20 (7 decompositions × $0.025)

---

### 3. Dependency Resolver Tests (No API Key Required)

**Quick validation without API:**

```bash
cd c:/Users/pqm847/Documents/PromptOps
python -c "
from phase1_nlp.decomposition.dependency_resolver import DependencyResolver

# Test circular dependency detection
tasks = [
    {'task_id': 'A', 'dependencies': ['B']},
    {'task_id': 'B', 'dependencies': ['C']},
    {'task_id': 'C', 'dependencies': ['A']}  # Creates cycle: A→B→C→A
]

resolver = DependencyResolver()
resolver.build_graph(tasks)
validation = resolver.validate()

print('=== Dependency Resolver Test ===')
print(f'Is Valid: {validation.is_valid}')
print(f'Circular Dependencies Detected: {len(validation.circular_dependencies)}')
print(f'Cycles: {validation.circular_dependencies}')
print('✅ Test passed!' if len(validation.circular_dependencies) > 0 else '❌ Test failed!')
"
```

---

## Quick Smoke Test (Without API Key)

Test the components that don't require Claude API:

```bash
cd c:/Users/pqm847/Documents/PromptOps

# Test imports
python -c "
print('Testing imports...')
from phase1_nlp.decomposition.dependency_resolver import DependencyResolver
from phase1_nlp.decomposition.decomposition_engine import DecompositionEngine
print('✅ All imports successful')
"

# Test dependency resolver
python -c "
from phase1_nlp.decomposition.dependency_resolver import DependencyResolver

tasks = [
    {'task_id': 'T1', 'dependencies': [], 'estimated_duration': 60},
    {'task_id': 'T2', 'dependencies': ['T1'], 'estimated_duration': 120},
    {'task_id': 'T3', 'dependencies': ['T1'], 'estimated_duration': 90},
    {'task_id': 'T4', 'dependencies': ['T2', 'T3'], 'estimated_duration': 60}
]

resolver = DependencyResolver()
resolver.build_graph(tasks)
validation = resolver.validate()

print('=== Dependency Graph Analysis ===')
print(f'Valid: {validation.is_valid}')
print(f'Topological Order: {validation.topological_order}')
print(f'Critical Path: {resolver.calculate_critical_path()}')
print('✅ Dependency resolver working!')
"
```

---

## Test Output Examples

### Successful Test Output

```
======================================================================
PromptOps Decomposition - Test Suite
======================================================================

Testing complete pipeline:
  Week 3-4 Parser → Week 5-6 Decomposition → Dependency Resolution

test_001_simple_deploy (__main__.TestDecomposition)
Test: Simple deployment to staging ... 
[1/1] Decomposing: "Deploy frontend v2.0 to staging"
✓ Success: 8 sub-tasks, 4 phases, 25 mins
ok

test_002_canary_deployment (__main__.TestDecomposition)
Test: Canary deployment with gradual rollout ... 
[1/1] Decomposing: "Deploy API v3.0 with canary rollout: 5%→50%→100%"
✓ Success: 12 sub-tasks, 5 phases, 45 mins
ok

...

----------------------------------------------------------------------
Ran 25 tests in 142.35s

OK (passed=23, failures=2)

SUMMARY
=======
Tests run: 25
Successes: 23
Failures: 2
Success Rate: 92%

✓ TARGET ACHIEVED (>85%)
```

### Failed Test Output

```
FAIL: test_012_impossible_time (__main__.TestDecomposition)
Test: Impossible time constraint
----------------------------------------------------------------------
AssertionError: Decomposition should fail for impossible constraint

Expected: decomp_success = False
Got: decomp_success = True
```

---

## Troubleshooting

### "ANTHROPIC_API_KEY not set"

**Solution:**
```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-your-key-here"
```

### "ModuleNotFoundError: No module named 'anthropic'"

**Solution:**
```bash
pip install anthropic
```

### "ModuleNotFoundError: No module named 'phase1_nlp'"

**Solution:**
```bash
cd c:/Users/pqm847/Documents/PromptOps
python -c "import sys; sys.path.insert(0, 'phase1-nlp'); print('Fixed')"
```

The test files already handle this with:
```python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'phase1-nlp'))
```

### "Rate limit exceeded"

**Solution:** Wait 60 seconds between test runs. Anthropic has rate limits on API requests.

### Tests taking too long

**Normal:** Each test makes a Claude API call (3-5s each)
- 25 unit tests ≈ 2-3 minutes
- 7 integration tests ≈ 1-2 minutes

---

## Cost Tracking

After running tests, check costs:

```python
from phase1_nlp.decomposition.decomposition_engine import DecompositionEngine
import os

engine = DecompositionEngine(os.environ.get('ANTHROPIC_API_KEY'))

# After running tests
stats = engine.get_usage_stats()
print(f"Total Cost: ${stats['total_cost_usd']:.4f}")
print(f"Total Requests: {stats['total_requests']}")
print(f"Avg Cost/Request: ${stats['average_cost_usd']:.4f}")
```

---

## Manual Testing

Test a single decomposition manually:

```python
from phase1_nlp.decomposition.decomposition_engine import DecompositionEngine
from phase1_nlp.parser.claude_integration import ClaudeParser
import os

api_key = os.environ.get('ANTHROPIC_API_KEY')

# Step 1: Parse command
parser = ClaudeParser(api_key)
success, parsed_intent, error = parser.parse_command("Deploy frontend v2.0 to staging")

print(f"Parse Success: {success}")
print(f"Intent: {parsed_intent}")

# Step 2: Decompose
engine = DecompositionEngine(api_key)
success, decomposition, error = engine.decompose(parsed_intent)

print(f"\nDecomposition Success: {success}")
print(f"Sub-tasks: {decomposition.get('total_sub_tasks', 0)}")
print(f"Estimated Duration: {decomposition.get('estimated_duration', 0)} mins")

# Step 3: Check tasks
for task in decomposition.get('sub_tasks', []):
    print(f"  [{task['task_id']}] {task['action']} - {task['estimated_duration']}s")
```

---

## Next Steps After Testing

1. **If tests pass (>85%):**
   - ✅ Week 5-6 validated
   - Ready to proceed to Week 7-8

2. **If tests fail (<85%):**
   - Review failure patterns
   - Adjust decomposition prompt
   - Tune validation thresholds
   - Re-run specific failing tests

3. **Check completion report:**
   - `phase1-nlp/decomposition/WEEK5-6_COMPLETION_REPORT.md`

---

## Quick Start Command

```bash
# Set API key (replace with your actual key)
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Run all tests
cd c:/Users/pqm847/Documents/PromptOps
python phase1-nlp/decomposition/test_decomposition.py
python tests/integration/decomposition_integration_test.py

# Expected total time: 3-5 minutes
# Expected total cost: ~$0.80
```

---

*Generated: 2026-04-21*  
*Week 5-6 Testing Guide*
