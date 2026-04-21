"""
Decomposition Engine for PromptOps
===================================

Main engine that uses Claude Sonnet 4 to decompose high-level PM commands
into atomic, executable sub-tasks.

Integrates:
- Decomposition prompt (DECOMP-001)
- Claude API (reuses Week 3-4 patterns)
- Dependency resolver (DECOMP-003)
- Cost tracking
- LangGraph workflow

Author: PromptOps Team - Week 5-6
Date: 2026-04-21
"""

import os
import sys
import json
import logging
import re
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Anthropic SDK
try:
    import anthropic
except ImportError:
    print("ERROR: anthropic package not installed")
    print("Run: pip install anthropic>=0.34.0")
    sys.exit(1)

# Import dependency resolver
from decomposition.dependency_resolver import (
    DependencyResolver,
    DependencyAnalysis,
    validate_dependencies
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

MODEL_NAME = "claude-sonnet-4-20250514"
MAX_TOKENS = 8192  # Larger for decomposition (more complex output)
TEMPERATURE = 0.0  # Deterministic
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
EXPONENTIAL_BACKOFF = True
REQUEST_TIMEOUT = 60  # seconds (longer for complex decompositions)

# API Pricing (per million tokens)
INPUT_TOKEN_COST = 3.0 / 1_000_000  # $3 per 1M tokens
OUTPUT_TOKEN_COST = 15.0 / 1_000_000  # $15 per 1M tokens


# ============================================================================
# Decomposition Engine
# ============================================================================

class DecompositionEngine:
    """
    Main decomposition engine using Claude Sonnet 4.

    Takes a parsed PM intent and generates atomic sub-tasks with dependencies.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize decomposition engine.

        Args:
            api_key: Anthropic API key (or read from ANTHROPIC_API_KEY env var)
        """
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')

        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. Set environment variable or pass as parameter."
            )

        self.client = anthropic.Anthropic(api_key=self.api_key)

        # Load system prompt
        self.system_prompt = self._load_system_prompt()

        # Dependency resolver
        self.dependency_resolver = DependencyResolver()

        # Cost tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.request_count = 0

        logger.info("DecompositionEngine initialized")
        logger.info(f"Model: {MODEL_NAME}")
        logger.info(f"Max tokens: {MAX_TOKENS}")

    def _load_system_prompt(self) -> str:
        """
        Load decomposition system prompt from file.

        Returns:
            System prompt text
        """
        prompt_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "decomposition_prompt.txt"
        )

        if not os.path.exists(prompt_path):
            raise FileNotFoundError(f"System prompt not found: {prompt_path}")

        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt = f.read()

        logger.info(f"Loaded system prompt from: {prompt_path}")
        logger.info(f"Prompt length: {len(prompt)} characters")

        return prompt

    def decompose(
        self,
        parsed_intent: Dict[str, Any],
        retry_count: int = 0
    ) -> Tuple[bool, Dict[str, Any], str]:
        """
        Decompose parsed PM intent into sub-tasks.

        Args:
            parsed_intent: Parsed intent from Week 3-4 parser
            retry_count: Current retry attempt (internal use)

        Returns:
            Tuple of (success, decomposition_output, error_message)
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"Decomposing intent: {parsed_intent.get('intent_type', 'unknown')}")
        logger.info(f"Command: {parsed_intent.get('original_command', 'N/A')}")

        try:
            # 1. Build user message
            user_message = json.dumps(parsed_intent, indent=2)

            # 2. Call Claude API
            start_time = time.time()

            response = self.client.messages.create(
                model=MODEL_NAME,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                system=self.system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
                timeout=REQUEST_TIMEOUT
            )

            elapsed = time.time() - start_time

            logger.info(f"API response received in {elapsed:.2f} seconds")

            # 3. Extract response text
            response_text = response.content[0].text

            # 4. Track usage
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens

            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens
            self.request_count += 1

            request_cost = (input_tokens * INPUT_TOKEN_COST) + (output_tokens * OUTPUT_TOKEN_COST)
            self.total_cost += request_cost

            logger.info(f"Tokens: {input_tokens} input, {output_tokens} output")
            logger.info(f"Cost: ${request_cost:.4f}")

            # 5. Parse and validate response
            success, decomposition, error = self._validate_response(response_text, parsed_intent)

            if not success:
                logger.error(f"Validation failed: {error}")

                # Retry if possible
                if retry_count < MAX_RETRIES:
                    logger.warning(f"Retrying... (attempt {retry_count + 1}/{MAX_RETRIES})")

                    # Exponential backoff
                    delay = RETRY_DELAY * (2 ** retry_count if EXPONENTIAL_BACKOFF else 1)
                    time.sleep(delay)

                    return self.decompose(parsed_intent, retry_count + 1)
                else:
                    return False, {}, f"Validation failed after {MAX_RETRIES} retries: {error}"

            # 6. Dependency analysis
            sub_tasks = decomposition.get('sub_tasks', [])
            dep_analysis = self.dependency_resolver.analyze(sub_tasks)

            if not dep_analysis.is_valid:
                logger.error("Dependency validation failed")
                validation_errors = dep_analysis.validation_result.errors

                # Retry if circular dependencies or other graph issues
                if retry_count < MAX_RETRIES:
                    logger.warning(f"Retrying with stricter constraints... (attempt {retry_count + 1}/{MAX_RETRIES})")
                    time.sleep(RETRY_DELAY)
                    return self.decompose(parsed_intent, retry_count + 1)
                else:
                    return False, {}, f"Dependency validation failed: {'; '.join(validation_errors)}"

            # 7. Enhance decomposition with dependency analysis
            decomposition = self._enhance_with_analysis(decomposition, dep_analysis)

            logger.info(f"✓ Decomposition successful")
            logger.info(f"  Total sub-tasks: {len(sub_tasks)}")
            logger.info(f"  Execution phases: {len(dep_analysis.execution_phases)}")
            logger.info(f"  Critical path length: {len(dep_analysis.critical_path)}")
            logger.info(f"  Parallel speedup: {dep_analysis.total_sequential_time / dep_analysis.total_parallel_time:.2f}x")

            return True, decomposition, ""

        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            return False, {}, f"API error: {str(e)}"

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return False, {}, f"Unexpected error: {str(e)}"

    def _validate_response(
        self,
        response_text: str,
        original_intent: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any], str]:
        """
        Validate decomposition response from Claude.

        Args:
            response_text: Raw response text from Claude
            original_intent: Original parsed intent

        Returns:
            (is_valid, parsed_decomposition, error_message)
        """
        # 1. Remove markdown code blocks if present
        cleaned_text = response_text.strip()

        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]  # Remove ```json
        if cleaned_text.startswith("```"):
            cleaned_text = cleaned_text[3:]  # Remove ```

        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]  # Remove trailing ```

        cleaned_text = cleaned_text.strip()

        # 2. Parse JSON
        try:
            decomposition = json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            return False, {}, f"Invalid JSON: {e}"

        # 3. Check for error responses
        if decomposition.get('status') in ['error', 'too_complex', 'insufficient_information']:
            error_msg = decomposition.get('error_message') or decomposition.get('recommendation', 'Unknown error')
            return False, {}, error_msg

        # 4. Validate required fields
        required_fields = [
            'decomposition_id',
            'timestamp',
            'original_intent',
            'total_sub_tasks',
            'estimated_duration',
            'execution_strategy',
            'sub_tasks'
        ]

        for field in required_fields:
            if field not in decomposition:
                return False, {}, f"Missing required field: {field}"

        # 5. Validate sub_tasks array
        sub_tasks = decomposition.get('sub_tasks', [])

        if not isinstance(sub_tasks, list):
            return False, {}, "sub_tasks must be an array"

        if len(sub_tasks) < 1:
            return False, {}, "Must have at least 1 sub-task"

        if len(sub_tasks) > 20:
            return False, {}, f"Too many sub-tasks ({len(sub_tasks)}) - maximum is 20"

        # 6. Validate each sub-task
        required_task_fields = [
            'task_id',
            'sequence',
            'phase',
            'action',
            'target',
            'parameters',
            'dependencies',
            'can_run_parallel',
            'estimated_duration',
            'validation_criteria',
            'risk_level'
        ]

        task_ids = set()

        for i, task in enumerate(sub_tasks):
            # Check required fields
            for field in required_task_fields:
                if field not in task:
                    return False, {}, f"Task {i+1} missing field: {field}"

            # Validate task_id format
            task_id = task['task_id']
            if not re.match(r'^task-\d{3}$', task_id):
                return False, {}, f"Invalid task_id format: {task_id} (must be task-XXX)"

            # Check for duplicate task_ids
            if task_id in task_ids:
                return False, {}, f"Duplicate task_id: {task_id}"
            task_ids.add(task_id)

            # Validate dependencies reference existing tasks
            dependencies = task.get('dependencies', [])
            for dep in dependencies:
                if dep not in task_ids and dep not in [t['task_id'] for t in sub_tasks]:
                    return False, {}, f"Task {task_id} depends on non-existent task: {dep}"

            # Validate risk_level
            if task['risk_level'] not in ['low', 'medium', 'high', 'critical']:
                return False, {}, f"Invalid risk_level in {task_id}: {task['risk_level']}"

            # Validate validation_criteria
            if 'expected_status' not in task['validation_criteria']:
                return False, {}, f"Task {task_id} missing validation_criteria.expected_status"
            if 'timeout' not in task['validation_criteria']:
                return False, {}, f"Task {task_id} missing validation_criteria.timeout"

        # 7. Validate total_sub_tasks matches actual count
        if decomposition['total_sub_tasks'] != len(sub_tasks):
            return False, {}, f"total_sub_tasks ({decomposition['total_sub_tasks']}) doesn't match actual count ({len(sub_tasks)})"

        logger.info(f"✓ Response validation passed ({len(sub_tasks)} tasks)")

        return True, decomposition, ""

    def _enhance_with_analysis(
        self,
        decomposition: Dict[str, Any],
        analysis: DependencyAnalysis
    ) -> Dict[str, Any]:
        """
        Enhance decomposition with dependency analysis results.

        Args:
            decomposition: Original decomposition from Claude
            analysis: Dependency analysis result

        Returns:
            Enhanced decomposition
        """
        # Add/update execution_plan
        decomposition['execution_plan'] = {
            'phases': [
                {
                    'phase_number': phase.phase_number,
                    'phase_name': phase.phase_name,
                    'task_ids': phase.task_ids,
                    'execution_mode': phase.execution_mode,
                    'estimated_duration': phase.estimated_duration
                }
                for phase in analysis.execution_phases
            ],
            'critical_path': analysis.critical_path,
            'total_sequential_time': self._format_duration(analysis.total_sequential_time),
            'total_parallel_time': self._format_duration(analysis.total_parallel_time)
        }

        # Add validation metadata
        decomposition['validation'] = {
            'is_valid': True,
            'validation_errors': [],
            'dependency_graph_valid': True,
            'circular_dependencies_detected': False,
            'orphan_tasks_detected': len(analysis.validation_result.orphan_tasks) > 0,
            'orphan_tasks': analysis.validation_result.orphan_tasks
        }

        return decomposition

    def _format_duration(self, seconds: int) -> str:
        """Format seconds to human-readable string."""
        if seconds < 60:
            return f"{seconds} seconds"
        elif seconds < 3600:
            minutes = seconds // 60
            remaining = seconds % 60
            if remaining > 0:
                return f"{minutes} minutes {remaining} seconds"
            return f"{minutes} minutes"
        else:
            hours = seconds // 3600
            remaining_minutes = (seconds % 3600) // 60
            if remaining_minutes > 0:
                return f"{hours} hours {remaining_minutes} minutes"
            return f"{hours} hours"

    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get API usage statistics.

        Returns:
            Dict with usage stats
        """
        return {
            'request_count': self.request_count,
            'total_input_tokens': self.total_input_tokens,
            'total_output_tokens': self.total_output_tokens,
            'total_cost_usd': self.total_cost,
            'average_cost_per_request': self.total_cost / self.request_count if self.request_count > 0 else 0
        }


# ============================================================================
# LangGraph Integration
# ============================================================================

def decomposition_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node that decomposes parsed intent into sub-tasks.

    Integrates with Week 3-4 parser output.

    Args:
        state: LangGraph state dict with 'parsed_intent' field

    Returns:
        Updated state with 'decomposition' field
    """
    logger.info("=== DECOMPOSITION NODE ===")

    parsed_intent = state.get('parsed_intent')

    if not parsed_intent:
        state['errors'].append("No parsed_intent found in state")
        state['workflow_status'] = 'failed'
        return state

    # Initialize engine
    engine = DecompositionEngine()

    # Decompose
    success, decomposition, error = engine.decompose(parsed_intent)

    if not success:
        state['errors'].append(f"Decomposition failed: {error}")
        state['workflow_status'] = 'failed'
        logger.error(f"Decomposition failed: {error}")
    else:
        state['decomposition'] = decomposition
        state['workflow_status'] = 'decomposed'
        logger.info(f"✓ Decomposition successful: {decomposition['total_sub_tasks']} tasks")

    return state


# ============================================================================
# Utility Functions
# ============================================================================

def estimate_monthly_cost(decompositions_per_month: int) -> float:
    """
    Estimate monthly API cost for decomposition.

    Args:
        decompositions_per_month: Number of decompositions per month

    Returns:
        Estimated cost in USD
    """
    # Average tokens per decomposition (rough estimate)
    avg_input_tokens = 6000  # System prompt + parsed intent
    avg_output_tokens = 3000  # Decomposition JSON

    avg_cost_per_decomposition = (
        (avg_input_tokens * INPUT_TOKEN_COST) +
        (avg_output_tokens * OUTPUT_TOKEN_COST)
    )

    return avg_cost_per_decomposition * decompositions_per_month


def test_connection() -> bool:
    """
    Test connection to Claude API.

    Returns:
        True if successful, False otherwise
    """
    try:
        engine = DecompositionEngine()
        logger.info("✓ API connection successful")
        return True
    except Exception as e:
        logger.error(f"✗ API connection failed: {e}")
        return False


# ============================================================================
# Main (for testing)
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("PromptOps Decomposition Engine - Test")
    print("="*70)

    # Check API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("\n✗ ERROR: ANTHROPIC_API_KEY not set")
        print("\nSet your API key:")
        print("  Windows: $env:ANTHROPIC_API_KEY=\"sk-ant-...\"")
        print("  Linux:   export ANTHROPIC_API_KEY=\"sk-ant-...\"")
        sys.exit(1)

    print("\n✓ API key found")

    # Test connection
    print("\nTesting API connection...")
    if not test_connection():
        sys.exit(1)

    # Test decomposition with sample intent
    print("\n" + "="*70)
    print("Test Decomposition: Simple Deploy")
    print("="*70)

    sample_intent = {
        "command_id": "cmd-2026-05-05-test123",
        "timestamp": "2026-05-05T14:30:22Z",
        "original_command": "Deploy frontend v1.2.3 to staging",
        "intent_type": "deploy",
        "confidence_score": 0.95,
        "target_service": "frontend",
        "target_env": "staging",
        "parameters": {
            "version": "v1.2.3"
        },
        "requires_approval": False,
        "risk_level": "medium",
        "ambiguity_detected": False
    }

    engine = DecompositionEngine()
    success, decomposition, error = engine.decompose(sample_intent)

    if success:
        print("\n✓ Decomposition successful!")
        print(f"\nTotal sub-tasks: {decomposition['total_sub_tasks']}")
        print(f"Estimated duration: {decomposition['estimated_duration']}")
        print(f"Execution strategy: {decomposition['execution_strategy']}")

        print(f"\nSub-tasks:")
        for task in decomposition['sub_tasks']:
            print(f"  {task['task_id']}: {task['action']} ({task['phase']})")

        print(f"\nExecution phases:")
        for phase in decomposition['execution_plan']['phases']:
            print(f"  Phase {phase['phase_number']}: {phase['phase_name']}")
            print(f"    Tasks: {len(phase['task_ids'])}, Mode: {phase['execution_mode']}")

        print(f"\nCritical path: {len(decomposition['execution_plan']['critical_path'])} tasks")
        print(f"Parallel time: {decomposition['execution_plan']['total_parallel_time']}")

        # Usage stats
        stats = engine.get_usage_stats()
        print(f"\n" + "="*70)
        print("API Usage")
        print("="*70)
        print(f"Requests: {stats['request_count']}")
        print(f"Input tokens: {stats['total_input_tokens']:,}")
        print(f"Output tokens: {stats['total_output_tokens']:,}")
        print(f"Total cost: ${stats['total_cost_usd']:.4f}")

        # Monthly estimates
        print(f"\n" + "="*70)
        print("Monthly Cost Estimates")
        print("="*70)
        for count in [100, 500, 1000, 5000]:
            cost = estimate_monthly_cost(count)
            print(f"  {count:,} decompositions/month: ${cost:.2f}")

    else:
        print(f"\n✗ Decomposition failed: {error}")
        sys.exit(1)

    print("\n" + "="*70)
    print("Test Complete!")
    print("="*70)
