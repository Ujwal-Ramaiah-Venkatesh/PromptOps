"""
LangGraph Agent Framework for NLP Parser Workflow
==================================================

This module implements the orchestration backbone for the NLP Parser using LangGraph.
It manages multi-step flows, state management, retries, and error handling for parsing
PM inputs into structured task decompositions.

Workflow:
    PM Input → input_validation → llm_parse → output_validation → Success
                    ↓                  ↓
              (on failure)        (on failure)
                    ↓                  ↓
              retry_handler ← ← ← ← ← ←
                    ↓
              (3 retries max)
                    ↓
              Ask PM to rephrase

Author: Backend Engineer - Phase 1 Week 1
Date: 2026-04-19
"""

from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional, List, Dict, Any
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# State Schema
# ============================================================================

class ParserState(TypedDict):
    """
    State object that flows through the LangGraph workflow.

    This state carries all context needed for parsing, validation, and retry logic.
    Each node can read from and write to this state.

    Attributes:
        original_input: Raw input from PM (unmodified)
        sanitized_input: Cleaned and validated input ready for LLM
        llm_response: Raw response from Claude Sonnet 4
        validated_output: Validated and structured JSON output
        retry_count: Number of retry attempts (max 3)
        errors: List of error messages encountered
        confidence_score: LLM's confidence in the parse (0.0-1.0)
        timestamp: When the parsing workflow started
        workflow_status: Current status (processing/success/failed/needs_rephrase)
    """
    original_input: str
    sanitized_input: str
    llm_response: Optional[Dict[Any, Any]]
    validated_output: Optional[Dict[Any, Any]]
    retry_count: int
    errors: List[str]
    confidence_score: float
    timestamp: str
    workflow_status: str


# ============================================================================
# Node Functions
# ============================================================================

def input_validation_node(state: ParserState) -> ParserState:
    """
    Node 1: Validate and sanitize PM input.

    Validates the input string for:
    - Non-empty content
    - Reasonable length (not too short/long)
    - No malicious patterns
    - Basic structure expectations

    Args:
        state: Current workflow state

    Returns:
        Updated state with sanitized_input or error
    """
    logger.info("=== INPUT VALIDATION NODE ===")
    logger.info(f"Original input length: {len(state.get('original_input', ''))}")

    original = state.get('original_input', '').strip()

    # Validation checks
    if not original:
        state['errors'].append("Input is empty")
        state['workflow_status'] = 'failed'
        logger.error("Validation failed: Empty input")
        return state

    if len(original) < 10:
        state['errors'].append("Input too short (minimum 10 characters)")
        state['workflow_status'] = 'failed'
        logger.error("Validation failed: Input too short")
        return state

    if len(original) > 10000:
        state['errors'].append("Input too long (maximum 10000 characters)")
        state['workflow_status'] = 'failed'
        logger.error("Validation failed: Input too long")
        return state

    # Basic sanitization
    # Remove potentially malicious patterns (basic implementation)
    sanitized = original.replace('\x00', '')  # Remove null bytes
    sanitized = sanitized.replace('\r\n', '\n')  # Normalize line endings

    # Check for minimum meaningful content
    word_count = len(sanitized.split())
    if word_count < 3:
        state['errors'].append("Input must contain at least 3 words")
        state['workflow_status'] = 'failed'
        logger.error("Validation failed: Too few words")
        return state

    # Success - update state
    state['sanitized_input'] = sanitized
    state['workflow_status'] = 'processing'
    logger.info(f"Input validation successful. Word count: {word_count}")

    return state


def llm_parse_node(state: ParserState) -> ParserState:
    """
    Node 2: Call Claude Sonnet 4 to parse intent.

    This node will call the Claude Sonnet 4 API to parse the sanitized input
    into structured task decomposition. Currently uses a placeholder response.

    In production, this will:
    - Construct the prompt with context
    - Call Claude Sonnet 4 API
    - Extract structured JSON from response
    - Calculate confidence score

    Args:
        state: Current workflow state

    Returns:
        Updated state with llm_response or error
    """
    logger.info("=== LLM PARSE NODE ===")
    logger.info(f"Parsing input (length: {len(state.get('sanitized_input', ''))})")
    logger.info(f"Retry count: {state.get('retry_count', 0)}")

    try:
        # TODO: Replace with actual Claude Sonnet 4 API call
        # Placeholder response simulating successful parse
        sanitized_input = state.get('sanitized_input', '')

        # Simulate API call delay and processing
        placeholder_response = {
            "intent": "task_decomposition",
            "confidence": 0.92,
            "tasks": [
                {
                    "id": "task_1",
                    "description": f"Parsed from: {sanitized_input[:50]}...",
                    "priority": "high",
                    "estimated_effort": "medium"
                }
            ],
            "metadata": {
                "model": "claude-sonnet-4",
                "timestamp": datetime.now().isoformat(),
                "tokens_used": len(sanitized_input.split()) * 2  # Rough estimate
            }
        }

        # Simulate occasional failures for testing retry logic
        # In production, this would be actual API failures
        if state.get('retry_count', 0) == 0 and "test_retry" in sanitized_input.lower():
            raise Exception("Simulated API failure for retry testing")

        state['llm_response'] = placeholder_response
        state['confidence_score'] = placeholder_response['confidence']
        state['workflow_status'] = 'processing'
        logger.info(f"LLM parse successful. Confidence: {placeholder_response['confidence']}")

    except Exception as e:
        error_msg = f"LLM parsing failed: {str(e)}"
        state['errors'].append(error_msg)
        state['workflow_status'] = 'retry_needed'
        logger.error(error_msg)

    return state


def output_validation_node(state: ParserState) -> ParserState:
    """
    Node 3: Validate JSON output against schema.

    Validates the LLM response for:
    - Required fields present
    - Correct data types
    - Value ranges (e.g., confidence 0.0-1.0)
    - Business logic constraints

    Args:
        state: Current workflow state

    Returns:
        Updated state with validated_output or error
    """
    logger.info("=== OUTPUT VALIDATION NODE ===")

    llm_response = state.get('llm_response')

    if not llm_response:
        state['errors'].append("No LLM response to validate")
        state['workflow_status'] = 'retry_needed'
        logger.error("Validation failed: No LLM response")
        return state

    try:
        # Validate required fields
        required_fields = ['intent', 'confidence', 'tasks']
        for field in required_fields:
            if field not in llm_response:
                raise ValueError(f"Missing required field: {field}")

        # Validate confidence score
        confidence = llm_response.get('confidence', 0.0)
        if not isinstance(confidence, (int, float)):
            raise ValueError("Confidence must be a number")
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")

        # Validate tasks structure
        tasks = llm_response.get('tasks', [])
        if not isinstance(tasks, list):
            raise ValueError("Tasks must be a list")
        if len(tasks) == 0:
            raise ValueError("At least one task is required")

        # Validate each task
        for idx, task in enumerate(tasks):
            if not isinstance(task, dict):
                raise ValueError(f"Task {idx} must be a dictionary")
            if 'id' not in task or 'description' not in task:
                raise ValueError(f"Task {idx} missing required fields")

        # Check confidence threshold
        if confidence < 0.7:
            logger.warning(f"Low confidence score: {confidence}")
            state['errors'].append(f"Low confidence: {confidence}")
            state['workflow_status'] = 'retry_needed'
            return state

        # Validation successful
        state['validated_output'] = llm_response
        state['workflow_status'] = 'success'
        logger.info(f"Output validation successful. Tasks validated: {len(tasks)}")

    except Exception as e:
        error_msg = f"Output validation failed: {str(e)}"
        state['errors'].append(error_msg)
        state['workflow_status'] = 'retry_needed'
        logger.error(error_msg)

    return state


def retry_handler_node(state: ParserState) -> ParserState:
    """
    Node 4: Handle LLM failures with retry logic.

    Manages retry attempts with:
    - Maximum 3 retry attempts
    - Incremental backoff (implicit in workflow)
    - Error aggregation
    - Decision on whether to retry or ask PM to rephrase

    Args:
        state: Current workflow state

    Returns:
        Updated state with retry decision
    """
    logger.info("=== RETRY HANDLER NODE ===")

    current_retry = state.get('retry_count', 0)
    max_retries = 3

    logger.info(f"Retry attempt: {current_retry + 1}/{max_retries}")
    logger.info(f"Errors encountered: {state.get('errors', [])}")

    if current_retry >= max_retries:
        # Max retries reached - ask PM to rephrase
        state['workflow_status'] = 'needs_rephrase'
        error_summary = " | ".join(state.get('errors', []))
        logger.error(f"Max retries reached. Errors: {error_summary}")
        logger.info("Requesting PM to rephrase input")
    else:
        # Increment retry count and prepare for retry
        state['retry_count'] = current_retry + 1
        state['workflow_status'] = 'retrying'
        logger.info(f"Preparing retry attempt {state['retry_count']}")

    return state


# ============================================================================
# Conditional Edge Functions
# ============================================================================

def should_parse(state: ParserState) -> str:
    """
    Conditional edge: Determine if input validation passed.

    Returns:
        'parse' if validation passed, 'end' if failed
    """
    status = state.get('workflow_status', 'failed')
    logger.info(f"Routing decision after input_validation: {status}")

    if status == 'processing':
        return 'parse'
    else:
        return 'end'


def should_validate(state: ParserState) -> str:
    """
    Conditional edge: Determine if LLM parse succeeded.

    Returns:
        'validate' if parse succeeded, 'retry' if failed
    """
    status = state.get('workflow_status', 'failed')
    logger.info(f"Routing decision after llm_parse: {status}")

    if status == 'processing':
        return 'validate'
    elif status == 'retry_needed':
        return 'retry'
    else:
        return 'end'


def should_retry(state: ParserState) -> str:
    """
    Conditional edge: Determine if output validation passed.

    Returns:
        'end' if validation passed, 'retry' if needs retry
    """
    status = state.get('workflow_status', 'failed')
    logger.info(f"Routing decision after output_validation: {status}")

    if status == 'success':
        return 'end'
    elif status == 'retry_needed':
        return 'retry'
    else:
        return 'end'


def should_continue_after_retry(state: ParserState) -> str:
    """
    Conditional edge: Determine if retry should happen or PM rephrase needed.

    Returns:
        'parse' if retrying, 'end' if max retries reached
    """
    status = state.get('workflow_status', 'failed')
    logger.info(f"Routing decision after retry_handler: {status}")

    if status == 'retrying':
        return 'parse'
    elif status == 'needs_rephrase':
        return 'end'
    else:
        return 'end'


# ============================================================================
# Graph Construction
# ============================================================================

def create_parser_graph() -> StateGraph:
    """
    Create and configure the LangGraph workflow for NLP parsing.

    This function constructs the state graph with all nodes and edges,
    defining the complete orchestration flow for parsing PM inputs.

    Returns:
        Compiled StateGraph ready for execution
    """
    logger.info("Creating LangGraph parser workflow")

    # Initialize the graph with our state schema
    workflow = StateGraph(ParserState)

    # Add nodes to the graph
    workflow.add_node("input_validation", input_validation_node)
    workflow.add_node("llm_parse", llm_parse_node)
    workflow.add_node("output_validation", output_validation_node)
    workflow.add_node("retry_handler", retry_handler_node)

    # Set entry point
    workflow.set_entry_point("input_validation")

    # Add conditional edges
    # From input_validation: go to llm_parse if valid, else end
    workflow.add_conditional_edges(
        "input_validation",
        should_parse,
        {
            "parse": "llm_parse",
            "end": END
        }
    )

    # From llm_parse: go to output_validation if success, retry_handler if failed
    workflow.add_conditional_edges(
        "llm_parse",
        should_validate,
        {
            "validate": "output_validation",
            "retry": "retry_handler",
            "end": END
        }
    )

    # From output_validation: end if success, retry_handler if failed
    workflow.add_conditional_edges(
        "output_validation",
        should_retry,
        {
            "retry": "retry_handler",
            "end": END
        }
    )

    # From retry_handler: go back to llm_parse if retrying, else end
    workflow.add_conditional_edges(
        "retry_handler",
        should_continue_after_retry,
        {
            "parse": "llm_parse",
            "end": END
        }
    )

    # Compile the graph
    compiled_graph = workflow.compile()
    logger.info("LangGraph parser workflow compiled successfully")

    return compiled_graph


# ============================================================================
# Execution Helper
# ============================================================================

def execute_parser_workflow(pm_input: str) -> Dict[Any, Any]:
    """
    Execute the parser workflow with the given PM input.

    This is the main entry point for running the parsing workflow.
    It initializes the state, executes the graph, and returns the result.

    Args:
        pm_input: Raw input string from PM

    Returns:
        Dictionary containing:
        - status: success/failed/needs_rephrase
        - output: Validated output if successful
        - errors: List of errors if failed
        - retry_count: Number of retries attempted
        - confidence_score: LLM confidence score
    """
    logger.info("=" * 60)
    logger.info("STARTING PARSER WORKFLOW EXECUTION")
    logger.info("=" * 60)

    # Initialize state
    initial_state: ParserState = {
        'original_input': pm_input,
        'sanitized_input': '',
        'llm_response': None,
        'validated_output': None,
        'retry_count': 0,
        'errors': [],
        'confidence_score': 0.0,
        'timestamp': datetime.now().isoformat(),
        'workflow_status': 'processing'
    }

    # Create and execute graph
    graph = create_parser_graph()

    try:
        # Execute the workflow
        final_state = graph.invoke(initial_state)

        # Prepare response
        result = {
            'status': final_state.get('workflow_status', 'failed'),
            'output': final_state.get('validated_output'),
            'errors': final_state.get('errors', []),
            'retry_count': final_state.get('retry_count', 0),
            'confidence_score': final_state.get('confidence_score', 0.0),
            'timestamp': final_state.get('timestamp', '')
        }

        logger.info("=" * 60)
        logger.info(f"WORKFLOW COMPLETED: {result['status']}")
        logger.info(f"Retries: {result['retry_count']}, Confidence: {result['confidence_score']}")
        logger.info("=" * 60)

        return result

    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}")
        return {
            'status': 'failed',
            'output': None,
            'errors': [str(e)],
            'retry_count': 0,
            'confidence_score': 0.0,
            'timestamp': datetime.now().isoformat()
        }


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    """
    Basic test execution when run directly.
    """
    print("LangGraph Parser Framework - Direct Execution Test")
    print("=" * 60)

    # Test case 1: Valid input
    test_input_1 = "Create a user authentication system with login, signup, and password reset features"
    print(f"\nTest 1 - Valid Input:\n{test_input_1}\n")
    result_1 = execute_parser_workflow(test_input_1)
    print(f"Result: {result_1['status']}")
    print(f"Confidence: {result_1['confidence_score']}")

    # Test case 2: Invalid input (too short)
    test_input_2 = "Do task"
    print(f"\nTest 2 - Invalid Input (too short):\n{test_input_2}\n")
    result_2 = execute_parser_workflow(test_input_2)
    print(f"Result: {result_2['status']}")
    print(f"Errors: {result_2['errors']}")

    print("\n" + "=" * 60)
    print("Direct execution test complete")
