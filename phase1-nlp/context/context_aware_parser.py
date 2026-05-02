"""
Context-Aware Parser - Enhanced NLP Parser
===========================================

Extends Week 3-4 ClaudeParser with infrastructure context awareness.
Reduces ambiguity by injecting relevant infrastructure state into prompts.

Features:
- Context injection before parsing
- Smart defaults from context
- Validation against current state
- Reduced ambiguity rate (target >50% reduction)
- Backward compatible with Week 3-4

Author: PromptOps Team - Week 7-8
Date: 2026-04-28
"""

import sys
import os
from typing import Dict, Any, Tuple, Optional
import logging

# Add Week 3-4 parser to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'parser'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from claude_integration import ClaudeParser
from context_injector import ContextInjector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Validation Result
# ============================================================================

class ValidationResult:
    """Result of context-based validation."""

    def __init__(
        self,
        is_valid: bool,
        errors: list = None,
        warnings: list = None,
        suggestions: dict = None
    ):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
        self.suggestions = suggestions or {}


# ============================================================================
# Context-Aware Parser
# ============================================================================

class ContextAwareParser(ClaudeParser):
    """
    Enhanced parser that uses infrastructure context to reduce ambiguity.

    Workflow:
    1. Load infrastructure context
    2. Extract relevant resources for command
    3. Inject context into system prompt
    4. Parse command with enhanced prompt
    5. Apply smart defaults from context
    6. Validate against context
    """

    def __init__(
        self,
        api_key: str,
        context_store_path: str = './context_snapshots',
        enable_context: bool = True
    ):
        """
        Initialize Context-Aware Parser.

        Args:
            api_key: Anthropic API key
            context_store_path: Path to context snapshots
            enable_context: Enable context injection (disable for testing)
        """
        # Initialize base parser
        super().__init__(api_key)

        # Initialize context injector
        self.context_injector = ContextInjector(
            context_store_path=context_store_path,
            max_context_tokens=2000
        )

        self.enable_context = enable_context
        self.context_store_path = context_store_path

        # Track context usage stats
        self.context_stats = {
            'total_parses': 0,
            'context_used': 0,
            'ambiguity_reduced': 0,
            'smart_defaults_applied': 0,
            'validation_failures': 0
        }

        logger.info(f"ContextAwareParser initialized: context={'enabled' if enable_context else 'disabled'}")

    # ========================================================================
    # Main Parsing Method
    # ========================================================================

    def parse_command_with_context(
        self,
        pm_command: str,
        retry_count: int = 0
    ) -> Tuple[bool, Dict[str, Any], str]:
        """
        Parse PM command with infrastructure context.

        Args:
            pm_command: PM command string
            retry_count: Current retry attempt

        Returns:
            Tuple of (success, parsed_intent, error_message)
        """
        self.context_stats['total_parses'] += 1

        try:
            # Step 1: Inject context into prompt
            enhanced_prompt = self.prompt  # Use base parser's prompt
            resources_included = 0

            if self.enable_context:
                injection_result = self.context_injector.inject_context(
                    pm_command=pm_command,
                    base_prompt=self.prompt
                )

                if injection_result.success and injection_result.resources_included > 0:
                    enhanced_prompt = injection_result.enhanced_prompt
                    resources_included = injection_result.resources_included
                    self.context_stats['context_used'] += 1

                    logger.info(f"✓ Context injected: {resources_included} resources, "
                               f"{injection_result.context_tokens} tokens")
                else:
                    logger.info("No relevant context found, using base prompt")

            # Step 2: Parse with enhanced prompt (temporarily replace prompt)
            original_prompt = self.prompt
            self.prompt = enhanced_prompt

            success, parsed_intent, error = self.parse_command(pm_command, retry_count)

            # Restore original prompt
            self.prompt = original_prompt

            if not success:
                return success, parsed_intent, error

            # Step 3: Apply smart defaults from context
            if self.enable_context:
                parsed_intent = self.apply_smart_defaults(parsed_intent)

            # Step 4: Validate against context
            if self.enable_context:
                validation = self.validate_against_context(parsed_intent)

                if not validation.is_valid:
                    logger.warning(f"Context validation failed: {validation.errors}")
                    self.context_stats['validation_failures'] += 1

                    # Add validation warnings to parsed intent
                    if 'warnings' not in parsed_intent:
                        parsed_intent['warnings'] = []
                    parsed_intent['warnings'].extend(validation.warnings)

                    # Add validation errors
                    if validation.errors:
                        parsed_intent['validation_errors'] = validation.errors

                # Apply suggestions
                if validation.suggestions:
                    for key, value in validation.suggestions.items():
                        if key not in parsed_intent or not parsed_intent[key]:
                            parsed_intent[key] = value
                            logger.info(f"Applied suggestion: {key}={value}")

            # Track metrics
            if parsed_intent.get('ambiguity_score', 0) < 0.3:  # Low ambiguity
                self.context_stats['ambiguity_reduced'] += 1

            return True, parsed_intent, ""

        except Exception as e:
            logger.error(f"Context-aware parsing failed: {str(e)}")
            return False, {}, str(e)

    # ========================================================================
    # Smart Defaults
    # ========================================================================

    def apply_smart_defaults(self, parsed_intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply smart defaults from infrastructure context.

        Defaults Applied:
        - Environment: Use production if only one prod resource exists
        - Region: Use most common region for the service
        - Current count: For scale operations
        - Current version: For rollback operations

        Args:
            parsed_intent: Parsed intent from Claude

        Returns:
            Enhanced parsed intent with defaults
        """
        try:
            # Load latest context
            context_data = self.context_injector._load_latest_context()
            if not context_data:
                return parsed_intent

            resources = context_data.get('resources', [])
            target_service = parsed_intent.get('target_service')

            if not target_service:
                return parsed_intent

            # Find matching resources
            matching_resources = [
                r for r in resources
                if target_service.lower() in r.get('service_name', '').lower()
            ]

            if not matching_resources:
                logger.info(f"No matching resources for {target_service}")
                return parsed_intent

            defaults_applied = 0

            # Default 1: Auto-fill environment
            if not parsed_intent.get('target_env') and len(matching_resources) == 1:
                environment = matching_resources[0].get('environment')
                if environment:
                    parsed_intent['target_env'] = environment
                    logger.info(f"✓ Auto-filled environment: {environment}")
                    defaults_applied += 1

            # Default 2: Auto-fill region
            if not parsed_intent.get('parameters', {}).get('region'):
                # Use most common region
                regions = [r.get('region') for r in matching_resources if r.get('region')]
                if regions:
                    most_common_region = max(set(regions), key=regions.count)
                    if 'parameters' not in parsed_intent:
                        parsed_intent['parameters'] = {}
                    parsed_intent['parameters']['region'] = most_common_region
                    logger.info(f"✓ Auto-filled region: {most_common_region}")
                    defaults_applied += 1

            # Default 3: Current count for scale operations
            if parsed_intent.get('intent_type') == 'scale':
                env = parsed_intent.get('target_env', 'production')
                resource = next(
                    (r for r in matching_resources if r.get('environment') == env),
                    matching_resources[0] if matching_resources else None
                )

                if resource:
                    current_state = resource.get('current_state', {})
                    current_count = current_state.get('desired_count') or current_state.get('running_count')

                    if current_count:
                        if 'parameters' not in parsed_intent:
                            parsed_intent['parameters'] = {}
                        parsed_intent['parameters']['current_count'] = current_count
                        logger.info(f"✓ Added current count: {current_count}")
                        defaults_applied += 1

            # Default 4: Current version for rollback
            if parsed_intent.get('intent_type') == 'rollback':
                env = parsed_intent.get('target_env', 'production')
                resource = next(
                    (r for r in matching_resources if r.get('environment') == env),
                    matching_resources[0] if matching_resources else None
                )

                if resource:
                    current_state = resource.get('current_state', {})
                    current_version = current_state.get('deployment_version') or current_state.get('task_definition')

                    if current_version:
                        if 'parameters' not in parsed_intent:
                            parsed_intent['parameters'] = {}
                        parsed_intent['parameters']['current_version'] = current_version
                        logger.info(f"✓ Added current version: {current_version}")
                        defaults_applied += 1

            # Default 5: Resource type
            if matching_resources and not parsed_intent.get('parameters', {}).get('resource_type'):
                resource_type = matching_resources[0].get('resource_type')
                if resource_type:
                    if 'parameters' not in parsed_intent:
                        parsed_intent['parameters'] = {}
                    parsed_intent['parameters']['resource_type'] = resource_type
                    logger.info(f"✓ Added resource type: {resource_type}")
                    defaults_applied += 1

            if defaults_applied > 0:
                self.context_stats['smart_defaults_applied'] += defaults_applied
                # Reduce ambiguity score since we filled in missing info
                current_ambiguity = parsed_intent.get('ambiguity_score', 0.5)
                parsed_intent['ambiguity_score'] = max(0.0, current_ambiguity - (defaults_applied * 0.1))

            return parsed_intent

        except Exception as e:
            logger.error(f"Smart defaults failed: {str(e)}")
            return parsed_intent

    # ========================================================================
    # Context Validation
    # ========================================================================

    def validate_against_context(self, parsed_intent: Dict[str, Any]) -> ValidationResult:
        """
        Validate parsed intent against current infrastructure state.

        Validations:
        - Service exists in context
        - Service is in expected state (can't scale stopped service)
        - Dependencies are healthy
        - Version exists (for rollback)

        Args:
            parsed_intent: Parsed intent to validate

        Returns:
            ValidationResult with errors and suggestions
        """
        errors = []
        warnings = []
        suggestions = {}

        try:
            # Load context
            context_data = self.context_injector._load_latest_context()
            if not context_data:
                warnings.append("No context available for validation")
                return ValidationResult(True, [], warnings, {})

            resources = context_data.get('resources', [])
            target_service = parsed_intent.get('target_service')
            target_env = parsed_intent.get('target_env')
            intent_type = parsed_intent.get('intent_type')

            # Validation 1: Service exists
            if target_service:
                matching_resources = [
                    r for r in resources
                    if target_service.lower() in r.get('service_name', '').lower()
                ]

                if not matching_resources:
                    errors.append(f"Service '{target_service}' not found in infrastructure")
                    return ValidationResult(False, errors, warnings, {})

                # Filter by environment if specified
                if target_env:
                    env_resources = [
                        r for r in matching_resources
                        if r.get('environment', '').lower() == target_env.lower()
                    ]

                    if not env_resources:
                        available_envs = list(set(r.get('environment') for r in matching_resources))
                        errors.append(
                            f"Service '{target_service}' not found in '{target_env}' environment. "
                            f"Available: {', '.join(available_envs)}"
                        )
                        suggestions['target_env'] = available_envs[0] if available_envs else None
                        return ValidationResult(False, errors, warnings, suggestions)

                    matching_resources = env_resources

                # Use first matching resource for validation
                resource = matching_resources[0]
                current_state = resource.get('current_state', {})

                # Validation 2: Service state
                status = current_state.get('status') or current_state.get('state')

                if intent_type == 'scale':
                    # Can't scale stopped/inactive services
                    if status in ['stopped', 'INACTIVE', 'terminated', 'stopping']:
                        errors.append(
                            f"Cannot scale {target_service}: service is {status}. "
                            f"Start the service first."
                        )
                        return ValidationResult(False, errors, warnings, {})

                if intent_type == 'deploy':
                    # Warn if service is not running
                    if status in ['stopped', 'INACTIVE']:
                        warnings.append(
                            f"Service {target_service} is currently {status}. "
                            f"Deployment may require manual start."
                        )

                # Validation 3: Dependencies
                dependencies = resource.get('dependencies', [])
                if dependencies:
                    unhealthy_deps = []
                    for dep_id in dependencies:
                        dep_resource = next(
                            (r for r in resources if dep_id in r['resource_id']),
                            None
                        )
                        if dep_resource:
                            dep_state = dep_resource.get('current_state', {})
                            dep_status = dep_state.get('status') or dep_state.get('state')
                            if dep_status in ['failed', 'stopped', 'unavailable']:
                                unhealthy_deps.append(dep_id)

                    if unhealthy_deps:
                        warnings.append(
                            f"Service has unhealthy dependencies: {', '.join(unhealthy_deps)}"
                        )

                # Validation 4: Rollback version exists
                if intent_type == 'rollback':
                    target_version = parsed_intent.get('parameters', {}).get('version')
                    if target_version:
                        # In production, would check version history
                        # For now, just log
                        logger.info(f"Rollback target version: {target_version}")

                # Validation 5: Drift warning
                drift_status = resource.get('drift_status', {})
                if drift_status.get('has_drift'):
                    drift_count = len(drift_status.get('drift_details', []))
                    warnings.append(
                        f"Service has {drift_count} unacknowledged drift event(s). "
                        f"Review drift before proceeding."
                    )

            # All validations passed
            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions
            )

        except Exception as e:
            logger.error(f"Context validation error: {str(e)}")
            warnings.append(f"Validation error: {str(e)}")
            return ValidationResult(True, [], warnings, {})

    # ========================================================================
    # Statistics
    # ========================================================================

    def get_context_stats(self) -> Dict[str, Any]:
        """
        Get context usage statistics.

        Returns:
            Dict with statistics
        """
        total = self.context_stats['total_parses']

        if total == 0:
            return self.context_stats

        return {
            **self.context_stats,
            'context_usage_rate': (self.context_stats['context_used'] / total) * 100,
            'ambiguity_reduction_rate': (self.context_stats['ambiguity_reduced'] / total) * 100,
            'validation_failure_rate': (self.context_stats['validation_failures'] / total) * 100,
            'avg_defaults_per_parse': self.context_stats['smart_defaults_applied'] / max(total, 1)
        }

    def print_context_stats(self):
        """Print context usage statistics."""
        stats = self.get_context_stats()

        print("\n" + "="*70)
        print("CONTEXT-AWARE PARSER - STATISTICS")
        print("="*70)
        print(f"Total Parses: {stats['total_parses']}")
        print(f"Context Used: {stats['context_used']} ({stats.get('context_usage_rate', 0):.1f}%)")
        print(f"Ambiguity Reduced: {stats['ambiguity_reduced']} ({stats.get('ambiguity_reduction_rate', 0):.1f}%)")
        print(f"Smart Defaults Applied: {stats['smart_defaults_applied']} "
              f"(avg {stats.get('avg_defaults_per_parse', 0):.1f} per parse)")
        print(f"Validation Failures: {stats['validation_failures']} ({stats.get('validation_failure_rate', 0):.1f}%)")
        print("="*70 + "\n")

    # ========================================================================
    # Backward Compatibility
    # ========================================================================

    def parse_command(self, pm_command: str, retry_count: int = 0) -> Tuple[bool, Dict[str, Any], str]:
        """
        Override parse_command to use context-aware parsing by default.

        Falls back to base parser if context is disabled.

        Args:
            pm_command: PM command string
            retry_count: Retry attempt

        Returns:
            Tuple of (success, parsed_intent, error_message)
        """
        if self.enable_context:
            return self.parse_command_with_context(pm_command, retry_count)
        else:
            return super().parse_command(pm_command, retry_count)


# ============================================================================
# LangGraph Integration
# ============================================================================

def context_aware_parse_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node for context-aware parsing.

    Args:
        state: LangGraph state with 'original_input'

    Returns:
        Updated state with 'parsed_intent'
    """
    import os

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        state['errors'].append("ANTHROPIC_API_KEY not set")
        state['workflow_status'] = 'error'
        return state

    parser = ContextAwareParser(api_key)

    success, parsed_intent, error = parser.parse_command_with_context(
        state['original_input']
    )

    if success:
        state['parsed_intent'] = parsed_intent
        state['workflow_status'] = 'parsed'
    else:
        state['errors'].append(f"Parse error: {error}")
        state['workflow_status'] = 'error'

    return state


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """CLI entry point for testing."""
    import argparse

    parser = argparse.ArgumentParser(description='Context-Aware Parser')
    parser.add_argument('command', help='PM command to parse')
    parser.add_argument('--context-dir', default='./context_snapshots', help='Context directory')
    parser.add_argument('--no-context', action='store_true', help='Disable context injection')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

    # Get API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set")
        print("Set with: export ANTHROPIC_API_KEY='sk-ant-...'")
        sys.exit(1)

    # Create parser
    context_parser = ContextAwareParser(
        api_key=api_key,
        context_store_path=args.context_dir,
        enable_context=not args.no_context
    )

    # Parse command
    print(f"\n{'='*70}")
    print(f"Parsing: {args.command}")
    print(f"Context: {'enabled' if not args.no_context else 'disabled'}")
    print(f"{'='*70}\n")

    success, parsed_intent, error = context_parser.parse_command_with_context(args.command)

    if success:
        print("✓ Parse successful\n")
        print("Parsed Intent:")
        print("-"*70)
        import json
        print(json.dumps(parsed_intent, indent=2))

        # Show context stats
        if not args.no_context:
            print("\n")
            context_parser.print_context_stats()
    else:
        print(f"✗ Parse failed: {error}")
        sys.exit(1)


if __name__ == '__main__':
    main()
