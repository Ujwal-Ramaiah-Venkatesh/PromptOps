# LangGraph NLP Parser Framework

## Overview

This directory contains the LangGraph-based orchestration framework for the NLP Parser workflow. It manages multi-step flows, state management, retries, and error handling for parsing PM inputs into structured task decompositions.

## Files

### `langgraph-setup.py`
The main orchestration framework implementing:
- **State Management**: ParserState TypedDict carrying context through the workflow
- **4 Core Nodes**:
  - `input_validation`: Validates and sanitizes PM input
  - `llm_parse`: Calls Claude Sonnet 4 to parse intent (placeholder implementation)
  - `output_validation`: Validates JSON output against schema
  - `retry_handler`: Handles LLM failures with retry logic
- **Conditional Edges**: Route workflow based on success/failure
- **Retry Logic**: Up to 3 retries before requesting PM to rephrase
- **Logging**: Comprehensive logging at each node

### `test_langgraph.py`
Comprehensive test suite with 7 test cases:
1. Valid input success
2. Empty input failure
3. Too short input failure
4. Complex multi-feature input
5. Minimal valid input (edge case)
6. Special characters handling
7. Retry logic simulation

## Workflow Structure

```
PM Input → input_validation → llm_parse → output_validation → Success
                ↓                  ↓
          (on failure)        (on failure)
                ↓                  ↓
          retry_handler ← ← ← ← ← ←
                ↓
          (3 retries max)
                ↓
          Ask PM to rephrase
```

## State Schema

```python
class ParserState(TypedDict):
    original_input: str          # Raw PM input
    sanitized_input: str         # Cleaned input
    llm_response: Optional[dict] # Raw LLM response
    validated_output: Optional[dict] # Validated output
    retry_count: int             # Retry attempts (max 3)
    errors: List[str]            # Error messages
    confidence_score: float      # LLM confidence (0.0-1.0)
    timestamp: str               # Workflow start time
    workflow_status: str         # Current status
```

## Installation

1. Ensure Python 3.9+ is installed
2. Install dependencies:
   ```bash
   pip install -r ../../requirements.txt
   ```

## Usage

### Direct Execution
```bash
python langgraph-setup.py
```
This runs two built-in test cases demonstrating the framework.

### Running Tests
```bash
python test_langgraph.py
```
This runs the comprehensive test suite with 7 test cases.

### Programmatic Usage
```python
from langgraph_setup import execute_parser_workflow

pm_input = "Create a user authentication system with login and signup"
result = execute_parser_workflow(pm_input)

print(f"Status: {result['status']}")
print(f"Output: {result['output']}")
print(f"Confidence: {result['confidence_score']}")
```

## Features

### Input Validation
- Non-empty check
- Length validation (10-10000 chars)
- Minimum word count (3 words)
- Basic sanitization (null bytes, line endings)

### LLM Integration (Placeholder)
- Ready for Claude Sonnet 4 API integration
- Confidence scoring
- Token usage tracking
- Metadata capture

### Output Validation
- Required fields check
- Data type validation
- Confidence threshold (0.7 minimum)
- Business logic constraints

### Retry Logic
- Maximum 3 retry attempts
- Error aggregation
- Automatic retry on LLM failures
- Request PM rephrase after max retries

### Error Handling
- Comprehensive error capture
- Error messages at each node
- Graceful failure handling
- Clear error reporting

## Next Steps

1. **Integrate Claude Sonnet 4 API**: Replace placeholder in `llm_parse_node`
2. **Add Prompt Engineering**: Define system prompts and examples
3. **Enhance Validation**: Add domain-specific validation rules
4. **Implement Caching**: Cache successful parses
5. **Add Metrics**: Track performance and success rates
6. **Optimize Retry**: Implement exponential backoff

## Dependencies

Required packages (from requirements.txt):
- `langgraph>=0.2.0` - State graph orchestration
- `anthropic>=0.34.0` - Claude API client
- `pydantic>=2.5.0` - Data validation

## Logging

All nodes produce structured logs with:
- Timestamp
- Log level (INFO/ERROR)
- Node name
- Context information

View logs during execution to track workflow progress.

## Testing

The test suite covers:
- ✓ Valid input scenarios
- ✓ Invalid input scenarios
- ✓ Edge cases
- ✓ Retry logic
- ✓ Error handling
- ✓ State management
- ✓ Framework structure verification

Expected output: 7/7 tests passing

## Architecture Notes

### Why LangGraph?
- **State Management**: Built-in state passing between nodes
- **Conditional Routing**: Easy to define success/failure paths
- **Retry Logic**: Natural fit for retry handling
- **Visualization**: Can generate workflow diagrams
- **Extensibility**: Easy to add new nodes and edges

### Design Decisions
1. **Separate Nodes**: Each step is isolated for testability
2. **Conditional Edges**: Route based on state, not hardcoded
3. **Retry Handler Node**: Centralized retry logic
4. **State-First**: All context in state, no side effects
5. **Placeholder LLM**: Framework works without real API calls

## Author
Backend Engineer - Phase 1 Week 1  
Date: 2026-04-19
