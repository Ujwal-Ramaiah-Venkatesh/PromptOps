"""
Claude Sonnet 4 API Integration for PromptOps NLP Parser
=========================================================

This module integrates Claude Sonnet 4 (via Anthropic API) with the LangGraph
orchestration framework. It handles:
- System prompt loading
- API calls with retry logic
- Response validation
- Error handling
- Token usage tracking
- Cost monitoring

Author: Backend Engineer - Phase 1 Week 3-4
Date: 2026-04-20
"""

import os
import json
import logging
import time
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import anthropic
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

# Load API key from environment
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
if not ANTHROPIC_API_KEY:
    logger.warning("ANTHROPIC_API_KEY not found in environment. Set it before using.")

# Model configuration
MODEL_NAME = "claude-sonnet-4-20250514"  # Latest Claude Sonnet 4
MAX_TOKENS = 4096  # Maximum tokens for response
TEMPERATURE = 0.0  # Deterministic output (no creativity needed)
TIMEOUT = 30  # API timeout in seconds

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
EXPONENTIAL_BACKOFF = True

# Cost tracking (as of 2026-04-20)
COST_PER_MILLION_INPUT_TOKENS = 3.0  # $3/million tokens
COST_PER_MILLION_OUTPUT_TOKENS = 15.0  # $15/million tokens


# ============================================================================
# System Prompt Loader
# ============================================================================

def load_system_prompt() -> str:
    """
    Load the comprehensive system prompt from file.

    Returns:
        System prompt as string

    Raises:
        FileNotFoundError: If prompt file doesn't exist
    """
    prompt_path = os.path.join(
        os.path.dirname(__file__),
        'claude_system_prompt.txt'
    )

    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            system_prompt = f.read()
        logger.info(f"System prompt loaded: {len(system_prompt)} characters")
        return system_prompt
    except FileNotFoundError:
        logger.error(f"System prompt file not found: {prompt_path}")
        raise


# ============================================================================
# Claude API Client
# ============================================================================

class ClaudeParser:
    """
    Claude Sonnet 4 API client for NLP intent parsing.

    Handles all API interactions, retries, validation, and cost tracking.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Claude API client.

        Args:
            api_key: Anthropic API key (defaults to env variable)
        """
        self.api_key = api_key or ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not provided and not found in environment")

        self.client = Anthropic(api_key=self.api_key)
        self.system_prompt = load_system_prompt()

        # Cost tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.request_count = 0

        logger.info(f"ClaudeParser initialized with model: {MODEL_NAME}")

    def parse_command(
        self,
        pm_input: str,
        retry_count: int = 0
    ) -> Tuple[bool, Dict[Any, Any], str]:
        """
        Parse PM command using Claude Sonnet 4.

        Args:
            pm_input: Plain English command from PM
            retry_count: Current retry attempt (for logging)

        Returns:
            Tuple of (success: bool, parsed_output: dict, error_message: str)

        Example:
            success, output, error = parser.parse_command("Deploy API v2.0 to prod")
            if success:
                print(f"Intent: {output['intent_type']}")
                print(f"Confidence: {output['confidence_score']}")
        """
        logger.info(f"=== PARSING COMMAND (Attempt {retry_count + 1}) ===")
        logger.info(f"Input: {pm_input}")

        # Build prompt
        user_prompt = f"{self.system_prompt}\n\nCOMMAND TO PARSE:\n{pm_input}"

        # Call API with retry logic
        for attempt in range(MAX_RETRIES):
            try:
                start_time = time.time()

                # Make API call
                response = self.client.messages.create(
                    model=MODEL_NAME,
                    max_tokens=MAX_TOKENS,
                    temperature=TEMPERATURE,
                    messages=[
                        {"role": "user", "content": user_prompt}
                    ]
                )

                elapsed = time.time() - start_time
                logger.info(f"API call completed in {elapsed:.2f}s")

                # Track usage
                self.request_count += 1
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens

                self.total_input_tokens += input_tokens
                self.total_output_tokens += output_tokens

                # Calculate cost
                cost = (
                    (input_tokens / 1_000_000) * COST_PER_MILLION_INPUT_TOKENS +
                    (output_tokens / 1_000_000) * COST_PER_MILLION_OUTPUT_TOKENS
                )
                self.total_cost += cost

                logger.info(f"Tokens: {input_tokens} in, {output_tokens} out")
                logger.info(f"Cost: ${cost:.4f} (Total: ${self.total_cost:.4f})")

                # Extract response text
                response_text = response.content[0].text

                # Validate and parse JSON
                success, parsed_json, error = self._validate_response(response_text)

                if success:
                    logger.info("✓ Parsing successful")
                    return True, parsed_json, ""
                else:
                    logger.warning(f"✗ Validation failed: {error}")
                    if attempt < MAX_RETRIES - 1:
                        logger.info(f"Retrying... (Attempt {attempt + 2}/{MAX_RETRIES})")
                        time.sleep(RETRY_DELAY * (2 ** attempt if EXPONENTIAL_BACKOFF else 1))
                        continue
                    else:
                        return False, {}, f"Validation failed after {MAX_RETRIES} attempts: {error}"

            except anthropic.APIError as e:
                logger.error(f"Anthropic API error: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (2 ** attempt if EXPONENTIAL_BACKOFF else 1))
                    continue
                else:
                    return False, {}, f"API error: {str(e)}"

            except Exception as e:
                logger.error(f"Unexpected error: {e}", exc_info=True)
                return False, {}, f"Unexpected error: {str(e)}"

        return False, {}, "Max retries exceeded"

    def _validate_response(self, response_text: str) -> Tuple[bool, Dict[Any, Any], str]:
        """
        Validate Claude's response is valid JSON matching our schema.

        Args:
            response_text: Raw text response from Claude

        Returns:
            Tuple of (valid: bool, parsed_json: dict, error_message: str)
        """
        logger.info("=== VALIDATING RESPONSE ===")

        # Remove markdown code blocks if present
        text = response_text.strip()
        if text.startswith("```json"):
            text = text[7:]  # Remove ```json
        if text.startswith("```"):
            text = text[3:]  # Remove ```
        if text.endswith("```"):
            text = text[:-3]  # Remove ```
        text = text.strip()

        # Parse JSON
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as e:
            return False, {}, f"Invalid JSON: {str(e)}"

        # Validate required fields
        required_fields = [
            'command_id', 'timestamp', 'original_command', 'intent_type',
            'confidence_score', 'target_service', 'target_env', 'parameters',
            'requires_approval', 'risk_level', 'ambiguity_detected',
            'clarification_questions', 'warnings', 'estimated_cost_impact',
            'estimated_duration', 'dependencies', 'rollback_plan', 'security_checks'
        ]

        missing_fields = [field for field in required_fields if field not in parsed]
        if missing_fields:
            return False, {}, f"Missing required fields: {', '.join(missing_fields)}"

        # Validate intent_type
        valid_intents = ['deploy', 'scale', 'rollback', 'monitor', 'audit', 'cost', 'security', 'diagnose']
        if parsed['intent_type'] not in valid_intents:
            return False, {}, f"Invalid intent_type: {parsed['intent_type']}. Must be one of: {valid_intents}"

        # Validate confidence_score
        if not isinstance(parsed['confidence_score'], (int, float)):
            return False, {}, f"confidence_score must be number, got: {type(parsed['confidence_score'])}"
        if not 0.0 <= parsed['confidence_score'] <= 1.0:
            return False, {}, f"confidence_score must be 0.0-1.0, got: {parsed['confidence_score']}"

        # Validate risk_level
        valid_risk_levels = ['low', 'medium', 'high', 'critical']
        if parsed['risk_level'] not in valid_risk_levels:
            return False, {}, f"Invalid risk_level: {parsed['risk_level']}. Must be one of: {valid_risk_levels}"

        # Validate target_env (if not null)
        if parsed['target_env'] is not None:
            valid_envs = ['production', 'staging', 'dev', 'demo']
            if parsed['target_env'] not in valid_envs:
                return False, {}, f"Invalid target_env: {parsed['target_env']}. Must be one of: {valid_envs} or null"

        # Validate ambiguity logic
        if parsed['ambiguity_detected'] and not parsed['clarification_questions']:
            return False, {}, "ambiguity_detected is true but no clarification_questions provided"

        # Validate approval logic
        if parsed['risk_level'] in ['high', 'critical'] and not parsed['requires_approval']:
            logger.warning(f"HIGH/CRITICAL risk without approval - auto-correcting")
            parsed['requires_approval'] = True

        logger.info("✓ Validation passed")
        return True, parsed, ""

    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get API usage statistics.

        Returns:
            Dictionary with usage stats
        """
        return {
            'request_count': self.request_count,
            'total_input_tokens': self.total_input_tokens,
            'total_output_tokens': self.total_output_tokens,
            'total_tokens': self.total_input_tokens + self.total_output_tokens,
            'total_cost_usd': round(self.total_cost, 4),
            'avg_cost_per_request': round(self.total_cost / max(self.request_count, 1), 4)
        }


# ============================================================================
# Integration with LangGraph
# ============================================================================

def llm_parse_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node that calls Claude Sonnet 4 for parsing.

    This function integrates with the LangGraph workflow defined in langgraph-setup.py.
    It replaces the placeholder in the original code.

    Args:
        state: ParserState dict from LangGraph workflow

    Returns:
        Updated state with llm_response or errors
    """
    logger.info("=== LLM PARSE NODE (Claude Sonnet 4) ===")

    # Get sanitized input
    sanitized_input = state.get('sanitized_input', '')
    if not sanitized_input:
        state['errors'].append("No sanitized input provided")
        state['workflow_status'] = 'failed'
        return state

    # Initialize Claude parser
    try:
        parser = ClaudeParser()
    except ValueError as e:
        state['errors'].append(f"Claude API initialization failed: {str(e)}")
        state['workflow_status'] = 'failed'
        return state

    # Parse command
    retry_count = state.get('retry_count', 0)
    success, parsed_output, error_message = parser.parse_command(
        pm_input=sanitized_input,
        retry_count=retry_count
    )

    if success:
        state['llm_response'] = parsed_output
        state['confidence_score'] = parsed_output.get('confidence_score', 0.0)
        state['workflow_status'] = 'processing'

        # Log usage stats
        stats = parser.get_usage_stats()
        logger.info(f"API Usage: {stats}")
    else:
        state['errors'].append(error_message)
        state['workflow_status'] = 'failed'
        logger.error(f"Parsing failed: {error_message}")

    return state


# ============================================================================
# Utility Functions
# ============================================================================

def test_claude_connection() -> bool:
    """
    Test if Claude API is accessible and working.

    Returns:
        True if connection successful, False otherwise
    """
    logger.info("=== TESTING CLAUDE API CONNECTION ===")

    try:
        parser = ClaudeParser()

        # Test with simple command
        success, output, error = parser.parse_command("Check API health")

        if success:
            logger.info("✓ Claude API connection successful")
            logger.info(f"Test parse: intent={output['intent_type']}, confidence={output['confidence_score']}")
            stats = parser.get_usage_stats()
            logger.info(f"Test cost: ${stats['total_cost_usd']}")
            return True
        else:
            logger.error(f"✗ Test parse failed: {error}")
            return False

    except Exception as e:
        logger.error(f"✗ Connection test failed: {e}", exc_info=True)
        return False


def estimate_monthly_cost(commands_per_month: int) -> Dict[str, Any]:
    """
    Estimate monthly Claude API costs based on usage.

    Args:
        commands_per_month: Expected number of commands per month

    Returns:
        Cost breakdown dictionary
    """
    # Assumptions based on system prompt size
    avg_input_tokens_per_command = 5000  # System prompt + user input
    avg_output_tokens_per_command = 2000  # JSON response

    total_input_tokens = commands_per_month * avg_input_tokens_per_command
    total_output_tokens = commands_per_month * avg_output_tokens_per_command

    input_cost = (total_input_tokens / 1_000_000) * COST_PER_MILLION_INPUT_TOKENS
    output_cost = (total_output_tokens / 1_000_000) * COST_PER_MILLION_OUTPUT_TOKENS
    total_cost = input_cost + output_cost

    return {
        'commands_per_month': commands_per_month,
        'total_input_tokens': total_input_tokens,
        'total_output_tokens': total_output_tokens,
        'input_cost_usd': round(input_cost, 2),
        'output_cost_usd': round(output_cost, 2),
        'total_monthly_cost_usd': round(total_cost, 2),
        'cost_per_command': round(total_cost / commands_per_month, 4)
    }


# ============================================================================
# Main (for testing)
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("PromptOps - Claude Sonnet 4 Integration Test")
    print("="*60 + "\n")

    # Test connection
    print("1. Testing API connection...")
    if test_claude_connection():
        print("   ✓ Connection successful\n")
    else:
        print("   ✗ Connection failed\n")
        exit(1)

    # Test various commands
    print("2. Testing command parsing...\n")

    test_commands = [
        "Deploy API v2.1.0 to production",
        "Scale backend to handle 2x traffic",
        "Why is the API slow?",
        "Reduce AWS bill by 30%",
        "Deploy the API",  # Ambiguous
        "Depoly api-serivce to proudction",  # Typos
    ]

    parser = ClaudeParser()

    for i, command in enumerate(test_commands, 1):
        print(f"\nTest {i}: \"{command}\"")
        print("-" * 60)

        success, output, error = parser.parse_command(command)

        if success:
            print(f"✓ Intent: {output['intent_type']}")
            print(f"✓ Confidence: {output['confidence_score']:.2f}")
            print(f"✓ Risk: {output['risk_level']}")
            print(f"✓ Approval: {output['requires_approval']}")

            if output['ambiguity_detected']:
                print(f"⚠ Ambiguity detected:")
                for q in output['clarification_questions']:
                    print(f"  - {q}")

            if output['warnings']:
                print(f"⚠ Warnings:")
                for w in output['warnings']:
                    print(f"  - {w}")
        else:
            print(f"✗ Error: {error}")

    # Show usage stats
    print("\n" + "="*60)
    print("API Usage Summary")
    print("="*60)
    stats = parser.get_usage_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")

    # Show cost estimates
    print("\n" + "="*60)
    print("Monthly Cost Estimates")
    print("="*60)

    for commands_per_month in [1000, 5000, 10000, 50000]:
        estimate = estimate_monthly_cost(commands_per_month)
        print(f"\n{estimate['commands_per_month']:,} commands/month:")
        print(f"  Cost: ${estimate['total_monthly_cost_usd']:,.2f}")
        print(f"  Per command: ${estimate['cost_per_command']:.4f}")

    print("\n" + "="*60)
    print("Test Complete!")
    print("="*60 + "\n")
