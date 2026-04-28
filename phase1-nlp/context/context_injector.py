"""
Context Injector - Prompt Enhancement
======================================

Injects relevant infrastructure context into Claude prompts to reduce ambiguity
and enable context-aware parsing.

Features:
- Relevance filtering based on PM command
- Token budget management (<2000 tokens)
- Concise, Claude-optimized formatting
- Dependency inclusion
- Freshness indicators

Author: PromptOps Team - Week 7-8
Date: 2026-04-28
"""

import json
import os
import re
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class ContextInjectionResult:
    """Result of context injection operation."""
    success: bool
    enhanced_prompt: str
    resources_included: int
    context_tokens: int
    resources_matched: List[str]
    error: Optional[str] = None


# ============================================================================
# Context Injector
# ============================================================================

class ContextInjector:
    """
    Injects relevant infrastructure context into Claude prompts.

    Workflow:
    1. Extract service names from PM command
    2. Match against context store
    3. Include dependencies
    4. Format for Claude
    5. Inject into system prompt
    """

    def __init__(
        self,
        context_store_path: str = './context_snapshots',
        max_context_tokens: int = 2000,
        token_estimation_ratio: float = 0.25  # ~4 chars per token
    ):
        """
        Initialize Context Injector.

        Args:
            context_store_path: Path to context snapshots directory
            max_context_tokens: Maximum tokens for context section
            token_estimation_ratio: Characters per token ratio
        """
        self.context_store_path = context_store_path
        self.max_context_tokens = max_context_tokens
        self.token_estimation_ratio = token_estimation_ratio

        logger.info(f"ContextInjector initialized: max_tokens={max_context_tokens}")

    # ========================================================================
    # Main Injection Methods
    # ========================================================================

    def inject_context(
        self,
        pm_command: str,
        base_prompt: str,
        context_data: Optional[Dict[str, Any]] = None
    ) -> ContextInjectionResult:
        """
        Inject relevant infrastructure context into prompt.

        Args:
            pm_command: Original PM command
            base_prompt: System prompt to enhance
            context_data: Pre-loaded context (optional, will load latest if not provided)

        Returns:
            ContextInjectionResult with enhanced prompt
        """
        try:
            # Load context if not provided
            if context_data is None:
                context_data = self._load_latest_context()
                if context_data is None:
                    logger.warning("No context data available")
                    return ContextInjectionResult(
                        success=False,
                        enhanced_prompt=base_prompt,
                        resources_included=0,
                        context_tokens=0,
                        resources_matched=[],
                        error="No context data available"
                    )

            # Extract relevant resources
            relevant_resources = self.extract_relevant_resources(
                pm_command,
                context_data.get('resources', [])
            )

            if not relevant_resources:
                logger.info("No relevant resources found for command")
                return ContextInjectionResult(
                    success=True,
                    enhanced_prompt=base_prompt,
                    resources_included=0,
                    context_tokens=0,
                    resources_matched=[],
                    error=None
                )

            # Format context
            context_section = self.format_context_for_claude(
                relevant_resources,
                context_data.get('last_updated')
            )

            # Check token budget
            context_tokens = self.calculate_context_tokens(context_section)
            if context_tokens > self.max_context_tokens:
                logger.warning(f"Context exceeds token budget: {context_tokens} > {self.max_context_tokens}")
                # Trim resources
                relevant_resources = self._trim_resources(relevant_resources, context_tokens)
                context_section = self.format_context_for_claude(
                    relevant_resources,
                    context_data.get('last_updated')
                )
                context_tokens = self.calculate_context_tokens(context_section)

            # Inject into prompt
            enhanced_prompt = self._inject_into_prompt(base_prompt, context_section)

            resource_ids = [r['resource_id'] for r in relevant_resources]

            return ContextInjectionResult(
                success=True,
                enhanced_prompt=enhanced_prompt,
                resources_included=len(relevant_resources),
                context_tokens=context_tokens,
                resources_matched=resource_ids,
                error=None
            )

        except Exception as e:
            logger.error(f"Context injection failed: {str(e)}")
            return ContextInjectionResult(
                success=False,
                enhanced_prompt=base_prompt,
                resources_included=0,
                context_tokens=0,
                resources_matched=[],
                error=str(e)
            )

    # ========================================================================
    # Resource Extraction
    # ========================================================================

    def extract_relevant_resources(
        self,
        pm_command: str,
        all_resources: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract resources relevant to the PM command.

        Strategy:
        1. Extract service names from command
        2. Match against resource service_name
        3. Include dependencies
        4. Filter by environment if specified
        5. Prioritize production if ambiguous

        Args:
            pm_command: PM command string
            all_resources: All available resources

        Returns:
            List of relevant resources
        """
        # Extract keywords
        service_names = self._extract_service_names(pm_command)
        environment = self._extract_environment(pm_command)

        logger.info(f"Extracted: services={service_names}, environment={environment}")

        relevant_resources = []
        matched_ids = set()

        # Direct matches
        for resource in all_resources:
            resource_service = resource.get('service_name', '').lower()
            resource_env = resource.get('environment', '').lower()

            # Check if service name matches
            service_match = any(
                svc in resource_service or resource_service in svc
                for svc in service_names
            )

            if not service_match:
                continue

            # Check environment filter
            if environment and resource_env != environment:
                continue

            relevant_resources.append(resource)
            matched_ids.add(resource['resource_id'])

        # Include dependencies
        dependency_resources = self._get_dependencies(relevant_resources, all_resources, matched_ids)
        relevant_resources.extend(dependency_resources)

        # If no environment specified and multiple matches, prioritize production
        if not environment and len(relevant_resources) > 5:
            relevant_resources = self._prioritize_by_environment(relevant_resources)

        logger.info(f"Matched {len(relevant_resources)} relevant resources")

        return relevant_resources

    def _extract_service_names(self, pm_command: str) -> List[str]:
        """Extract service names from PM command."""
        # Common service name patterns
        common_services = [
            'frontend', 'backend', 'api', 'worker', 'scheduler',
            'database', 'db', 'cache', 'redis', 'postgres', 'mysql',
            'queue', 'sqs', 'kafka', 'rabbit', 'rabbitmq',
            'monitoring', 'prometheus', 'grafana', 'elk', 'elasticsearch',
            'nginx', 'apache', 'haproxy', 'load-balancer', 'alb'
        ]

        command_lower = pm_command.lower()
        found_services = []

        for service in common_services:
            if service in command_lower:
                found_services.append(service)

        # Extract hyphenated names (e.g., "user-service")
        hyphenated = re.findall(r'\b([a-z]+-[a-z]+)\b', command_lower)
        found_services.extend(hyphenated)

        # If no services found, look for quoted strings
        if not found_services:
            quoted = re.findall(r'"([^"]+)"', pm_command)
            found_services.extend([q.lower() for q in quoted])

        return list(set(found_services))

    def _extract_environment(self, pm_command: str) -> Optional[str]:
        """Extract environment from PM command."""
        command_lower = pm_command.lower()

        if any(word in command_lower for word in ['prod', 'production']):
            return 'production'
        elif any(word in command_lower for word in ['staging', 'stage']):
            return 'staging'
        elif any(word in command_lower for word in ['dev', 'development']):
            return 'development'

        return None

    def _get_dependencies(
        self,
        resources: List[Dict[str, Any]],
        all_resources: List[Dict[str, Any]],
        matched_ids: Set[str]
    ) -> List[Dict[str, Any]]:
        """Get dependency resources."""
        dependency_resources = []

        for resource in resources:
            for dep_id in resource.get('dependencies', []):
                if dep_id in matched_ids:
                    continue

                # Find dependency resource
                for dep_resource in all_resources:
                    if dep_resource['resource_id'] == dep_id or dep_id in dep_resource['resource_id']:
                        dependency_resources.append(dep_resource)
                        matched_ids.add(dep_resource['resource_id'])
                        break

        return dependency_resources

    def _prioritize_by_environment(self, resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize production, then staging, then development."""
        env_priority = {'production': 0, 'staging': 1, 'development': 2}

        sorted_resources = sorted(
            resources,
            key=lambda r: env_priority.get(r.get('environment', 'development'), 3)
        )

        # Take top 10 resources
        return sorted_resources[:10]

    def _trim_resources(
        self,
        resources: List[Dict[str, Any]],
        current_tokens: int
    ) -> List[Dict[str, Any]]:
        """Trim resources to fit token budget."""
        target_tokens = int(self.max_context_tokens * 0.9)  # 90% of budget
        trim_ratio = target_tokens / current_tokens

        target_count = max(1, int(len(resources) * trim_ratio))

        logger.warning(f"Trimming resources: {len(resources)} → {target_count}")

        return resources[:target_count]

    # ========================================================================
    # Context Formatting
    # ========================================================================

    def format_context_for_claude(
        self,
        resources: List[Dict[str, Any]],
        last_updated: Optional[str] = None
    ) -> str:
        """
        Format resources into Claude-optimized context.

        Format:
        - Concise, structured
        - Only relevant fields
        - Clear service grouping
        - Freshness indicator

        Args:
            resources: List of relevant resources
            last_updated: Timestamp of context

        Returns:
            Formatted context string
        """
        lines = []

        # Header
        timestamp = last_updated or datetime.now(timezone.utc).isoformat()
        lines.append("=== INFRASTRUCTURE CONTEXT ===")
        lines.append(f"Updated: {self._format_timestamp(timestamp)}")
        lines.append("")

        # Group by service name
        by_service = {}
        for resource in resources:
            service_name = resource.get('service_name', 'unknown')
            if service_name not in by_service:
                by_service[service_name] = []
            by_service[service_name].append(resource)

        # Format each service
        for service_name, service_resources in sorted(by_service.items()):
            for resource in service_resources:
                lines.append(self._format_resource(resource))
                lines.append("")

        lines.append("=== END CONTEXT ===")

        return "\n".join(lines)

    def _format_resource(self, resource: Dict[str, Any]) -> str:
        """Format a single resource."""
        lines = []

        resource_type = resource['resource_type']
        service_name = resource['service_name']
        environment = resource['environment']
        region = resource['region']
        current_state = resource.get('current_state', {})

        # Header
        lines.append(f"SERVICE: {service_name}")
        lines.append(f"- Type: {resource_type}")
        lines.append(f"- Environment: {environment}")
        lines.append(f"- Region: {region}")

        # Type-specific formatting
        if resource_type == 'ecs_service':
            lines.extend(self._format_ecs_service(current_state))
        elif resource_type == 'ec2_instance':
            lines.extend(self._format_ec2_instance(current_state))
        elif resource_type == 'rds_database':
            lines.extend(self._format_rds_database(current_state))
        elif resource_type == 'lambda_function':
            lines.extend(self._format_lambda_function(current_state))
        elif resource_type == 'alb':
            lines.extend(self._format_alb(current_state))
        else:
            lines.append(f"- Status: {current_state.get('status', 'unknown')}")

        # Dependencies
        dependencies = resource.get('dependencies', [])
        if dependencies:
            lines.append(f"- Dependencies: {', '.join(dependencies[:3])}")

        # Drift warning
        drift_status = resource.get('drift_status', {})
        if drift_status.get('has_drift'):
            lines.append(f"⚠️ DRIFT DETECTED: {len(drift_status.get('drift_details', []))} change(s)")

        return "\n".join(lines)

    def _format_ecs_service(self, state: Dict[str, Any]) -> List[str]:
        """Format ECS service state."""
        return [
            f"- Status: {state.get('status', 'UNKNOWN')}",
            f"- Instances: {state.get('running_count', 0)}/{state.get('desired_count', 0)} running",
            f"- Task Definition: {state.get('task_definition', 'unknown')}",
            f"- Launch Type: {state.get('launch_type', 'UNKNOWN')}",
            f"- CPU/Memory: {state.get('cpu', 'N/A')}/{state.get('memory', 'N/A')}",
        ]

    def _format_ec2_instance(self, state: Dict[str, Any]) -> List[str]:
        """Format EC2 instance state."""
        return [
            f"- State: {state.get('state', 'unknown')}",
            f"- Instance Type: {state.get('instance_type', 'unknown')}",
            f"- IP: {state.get('public_ip', state.get('private_ip', 'N/A'))}",
        ]

    def _format_rds_database(self, state: Dict[str, Any]) -> List[str]:
        """Format RDS database state."""
        return [
            f"- Status: {state.get('status', 'unknown')}",
            f"- Engine: {state.get('engine', 'unknown')} {state.get('engine_version', '')}",
            f"- Instance Class: {state.get('instance_class', 'unknown')}",
            f"- Multi-AZ: {'Yes' if state.get('multi_az') else 'No'}",
            f"- Endpoint: {state.get('endpoint', 'N/A')}",
        ]

    def _format_lambda_function(self, state: Dict[str, Any]) -> List[str]:
        """Format Lambda function state."""
        return [
            f"- Runtime: {state.get('runtime', 'unknown')}",
            f"- Memory: {state.get('memory_size', 0)} MB",
            f"- Timeout: {state.get('timeout', 0)}s",
            f"- Last Modified: {self._format_timestamp(state.get('last_modified', ''))}",
        ]

    def _format_alb(self, state: Dict[str, Any]) -> List[str]:
        """Format ALB state."""
        return [
            f"- State: {state.get('state', 'unknown')}",
            f"- DNS: {state.get('dns_name', 'N/A')}",
            f"- Scheme: {state.get('scheme', 'unknown')}",
            f"- Target Groups: {len(state.get('target_groups', []))}",
        ]

    def _format_timestamp(self, timestamp: str) -> str:
        """Format timestamp for display."""
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M UTC')
        except:
            return timestamp[:16] if len(timestamp) > 16 else timestamp

    # ========================================================================
    # Prompt Injection
    # ========================================================================

    def _inject_into_prompt(self, base_prompt: str, context_section: str) -> str:
        """
        Inject context section into system prompt.

        Injection point:
        - After initial instructions
        - Before examples (if any)
        - Clearly delimited
        """
        # Find a good injection point
        # Strategy: inject before "Examples:" or at the end

        if "Examples:" in base_prompt or "EXAMPLES:" in base_prompt:
            # Inject before examples
            injection_point = base_prompt.find("Examples:")
            if injection_point == -1:
                injection_point = base_prompt.find("EXAMPLES:")

            enhanced = (
                base_prompt[:injection_point] +
                "\n\n" + context_section + "\n\n" +
                base_prompt[injection_point:]
            )
        else:
            # Inject at end
            enhanced = base_prompt + "\n\n" + context_section

        return enhanced

    # ========================================================================
    # Token Calculation
    # ========================================================================

    def calculate_context_tokens(self, context: str) -> int:
        """
        Estimate token count for context string.

        Uses character-based estimation (~4 chars per token).
        """
        char_count = len(context)
        estimated_tokens = int(char_count * self.token_estimation_ratio)
        return estimated_tokens

    # ========================================================================
    # Context Loading
    # ========================================================================

    def _load_latest_context(self) -> Optional[Dict[str, Any]]:
        """Load the latest context snapshot."""
        if not os.path.exists(self.context_store_path):
            logger.warning(f"Context store path not found: {self.context_store_path}")
            return None

        # Find latest snapshot
        snapshot_files = sorted(
            [f for f in os.listdir(self.context_store_path)
             if f.startswith('snap-') and f.endswith('.json')],
            reverse=True
        )

        if not snapshot_files:
            logger.warning("No snapshots found")
            return None

        latest_file = os.path.join(self.context_store_path, snapshot_files[0])

        try:
            with open(latest_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load context: {str(e)}")
            return None

    def load_context_by_id(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """Load a specific context snapshot."""
        snapshot_path = os.path.join(self.context_store_path, f'{snapshot_id}.json')

        if not os.path.exists(snapshot_path):
            logger.warning(f"Snapshot not found: {snapshot_id}")
            return None

        try:
            with open(snapshot_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load snapshot {snapshot_id}: {str(e)}")
            return None


# ============================================================================
# Utility Functions
# ============================================================================

def inject_context_into_parser(
    pm_command: str,
    parser_prompt: str,
    context_store_path: str = './context_snapshots'
) -> Tuple[str, int]:
    """
    Convenience function to inject context into parser prompt.

    Args:
        pm_command: PM command
        parser_prompt: Parser system prompt
        context_store_path: Path to context snapshots

    Returns:
        Tuple of (enhanced_prompt, resources_included)
    """
    injector = ContextInjector(context_store_path=context_store_path)
    result = injector.inject_context(pm_command, parser_prompt)

    if result.success:
        logger.info(f"✓ Context injected: {result.resources_included} resources, {result.context_tokens} tokens")
    else:
        logger.warning(f"✗ Context injection failed: {result.error}")

    return result.enhanced_prompt, result.resources_included


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """CLI entry point for testing."""
    import argparse

    parser = argparse.ArgumentParser(description='Test context injection')
    parser.add_argument('command', help='PM command to test')
    parser.add_argument('--context-dir', default='./context_snapshots', help='Context directory')
    parser.add_argument('--max-tokens', type=int, default=2000, help='Max context tokens')
    parser.add_argument('--show-prompt', action='store_true', help='Show full enhanced prompt')

    args = parser.parse_args()

    # Sample base prompt
    base_prompt = """You are a DevOps command parser. Convert PM commands to structured JSON.

Output format:
{
  "intent_type": "deploy|scale|rollback|monitor",
  "target_service": "service name",
  "target_env": "production|staging|development",
  "parameters": {}
}

Parse the following command:"""

    injector = ContextInjector(
        context_store_path=args.context_dir,
        max_context_tokens=args.max_tokens
    )

    result = injector.inject_context(args.command, base_prompt)

    print(f"\n{'='*70}")
    print(f"Context Injection Test")
    print(f"{'='*70}")
    print(f"Command: {args.command}")
    print(f"Success: {result.success}")
    print(f"Resources: {result.resources_included}")
    print(f"Tokens: {result.context_tokens}/{args.max_tokens}")
    print(f"Matched: {', '.join(result.resources_matched[:5])}")

    if result.error:
        print(f"Error: {result.error}")

    if args.show_prompt:
        print(f"\n{'='*70}")
        print(f"Enhanced Prompt")
        print(f"{'='*70}")
        print(result.enhanced_prompt)


if __name__ == '__main__':
    main()
