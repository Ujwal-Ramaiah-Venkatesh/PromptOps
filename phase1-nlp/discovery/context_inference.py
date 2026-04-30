"""
Context Inference Engine
=========================

Intelligently infers environment, project, and owner from resource metadata.

Week 16-18: ENHANCEMENT-003
Author: PromptOps Team
Date: 2026-04-30
"""

from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass
import re
from collections import Counter
import logging

from .aws_scanner import Resource

logger = logging.getLogger(__name__)


@dataclass
class TagPattern:
    """Detected tag pattern across resources."""
    tag_key: str
    frequency: float  # Percentage of resources with this tag
    common_values: List[str]
    is_consistent: bool  # True if >80% of resources have this tag


@dataclass
class NamingPattern:
    """Detected naming convention."""
    pattern: str  # Regex pattern
    example: str  # Example resource name
    fields: List[str]  # Extracted fields (e.g., ['app', 'env', 'number'])
    frequency: float  # How many resources match this pattern


class ContextInferenceEngine:
    """
    Infer context (environment, project, owner) from resource metadata.

    Uses multiple signals:
    - Tags (Environment, Project, Owner, etc.)
    - Resource names (web-prod-1, staging-db, etc.)
    - VPC/subnet associations
    - Instance types (t3.nano = dev, c5.4xlarge = prod)
    - Database sizes (10GB = dev, 1TB = prod)
    """

    # Common environment indicators
    ENV_KEYWORDS = {
        'production': ['prod', 'production', 'prd', 'live', 'main'],
        'staging': ['stage', 'staging', 'stg', 'preprod', 'pre-prod'],
        'development': ['dev', 'development', 'devel', 'sandbox', 'test'],
    }

    # Instance types that suggest environment
    DEV_INSTANCE_TYPES = ['t2.micro', 't2.small', 't3.nano', 't3.micro', 't3.small']
    PROD_INSTANCE_TYPES = ['c5.large', 'c5.xlarge', 'm5.large', 'r5.large']

    def __init__(self, resources: List[Resource]):
        """
        Initialize inference engine with discovered resources.

        Args:
            resources: List of discovered resources
        """
        self.resources = resources
        self.tag_patterns: Dict[str, TagPattern] = {}
        self.naming_patterns: List[NamingPattern] = []
        self.vpc_environments: Dict[str, str] = {}  # vpc_id -> environment
        self.subnet_environments: Dict[str, str] = {}  # subnet_id -> environment

        # Analyze patterns
        self._analyze_tag_patterns()
        self._analyze_naming_patterns()
        self._build_network_context()

    def enrich_all_resources(self) -> List[Resource]:
        """
        Enrich all resources with inferred context.

        Returns:
            List of resources with inferred_environment, inferred_project, inferred_owner populated
        """
        logger.info(f"Enriching {len(self.resources)} resources with context")

        for resource in self.resources:
            self._enrich_resource(resource)

        # Log summary
        with_env = sum(1 for r in self.resources if r.inferred_environment)
        with_project = sum(1 for r in self.resources if r.inferred_project)
        with_owner = sum(1 for r in self.resources if r.inferred_owner)

        logger.info(f"Enrichment complete: {with_env} with environment, "
                   f"{with_project} with project, {with_owner} with owner")

        return self.resources

    def _enrich_resource(self, resource: Resource):
        """Enrich single resource with inferred context."""
        # Infer environment
        env, env_confidence = self._infer_environment(resource)
        resource.inferred_environment = env

        # Infer project
        project, project_confidence = self._infer_project(resource)
        resource.inferred_project = project

        # Infer owner
        owner, owner_confidence = self._infer_owner(resource)
        resource.inferred_owner = owner

        # Overall confidence score (average)
        resource.confidence_score = (env_confidence + project_confidence + owner_confidence) / 3

    def _infer_environment(self, resource: Resource) -> Tuple[Optional[str], float]:
        """
        Infer environment (production/staging/development) with confidence score.

        Returns:
            Tuple of (environment, confidence_score)
        """
        signals = []

        # Signal 1: Direct tag (highest confidence)
        for tag_key in ['Environment', 'Env', 'environment', 'env']:
            if tag_key in resource.tags:
                env_value = resource.tags[tag_key].lower()
                # Normalize to standard names
                for standard_env, keywords in self.ENV_KEYWORDS.items():
                    if env_value in keywords:
                        signals.append((standard_env, 1.0))
                        break

        # Signal 2: Name contains environment keyword
        if resource.name:
            name_lower = resource.name.lower()
            for standard_env, keywords in self.ENV_KEYWORDS.items():
                for keyword in keywords:
                    if keyword in name_lower:
                        signals.append((standard_env, 0.7))
                        break

        # Signal 3: VPC/Subnet association
        if resource.resource_type == 'ec2' and resource.aws_state.get('vpc_id'):
            vpc_id = resource.aws_state['vpc_id']
            if vpc_id in self.vpc_environments:
                signals.append((self.vpc_environments[vpc_id], 0.6))

        if resource.resource_type == 'ec2' and resource.aws_state.get('subnet_id'):
            subnet_id = resource.aws_state['subnet_id']
            if subnet_id in self.subnet_environments:
                signals.append((self.subnet_environments[subnet_id], 0.6))

        # Signal 4: Instance type suggests environment (EC2 only)
        if resource.resource_type == 'ec2':
            instance_type = resource.aws_state.get('instance_type')
            if instance_type in self.DEV_INSTANCE_TYPES:
                signals.append(('development', 0.4))
            elif instance_type in self.PROD_INSTANCE_TYPES:
                signals.append(('production', 0.4))

        # Signal 5: Database size suggests environment (RDS only)
        if resource.resource_type == 'rds':
            allocated_storage = resource.aws_state.get('allocated_storage', 0)
            if allocated_storage < 50:  # Less than 50GB
                signals.append(('development', 0.3))
            elif allocated_storage > 500:  # More than 500GB
                signals.append(('production', 0.5))

        # Aggregate signals
        if not signals:
            return None, 0.0

        # Weight by confidence, pick most confident
        env_scores = {}
        for env, confidence in signals:
            env_scores[env] = env_scores.get(env, 0) + confidence

        best_env = max(env_scores, key=env_scores.get)
        best_confidence = min(env_scores[best_env], 1.0)  # Cap at 1.0

        return best_env, best_confidence

    def _infer_project(self, resource: Resource) -> Tuple[Optional[str], float]:
        """
        Infer project/application name with confidence score.

        Returns:
            Tuple of (project, confidence_score)
        """
        signals = []

        # Signal 1: Project tag (highest confidence)
        for tag_key in ['Project', 'project', 'Application', 'app', 'Service']:
            if tag_key in resource.tags:
                signals.append((resource.tags[tag_key], 1.0))

        # Signal 2: Extract from name pattern
        if resource.name:
            # Pattern: app-env-number (e.g., web-prod-1 → project: web)
            match = re.match(r'^([a-zA-Z0-9-]+?)[-_](prod|stage|dev)', resource.name, re.IGNORECASE)
            if match:
                app_name = match.group(1)
                signals.append((app_name, 0.6))

            # Pattern: env-app-number (e.g., prod-web-1 → project: web)
            match = re.match(r'^(prod|stage|dev)[-_]([a-zA-Z0-9-]+)', resource.name, re.IGNORECASE)
            if match:
                app_name = match.group(2).split('-')[0]  # Take first part
                signals.append((app_name, 0.5))

        # Aggregate signals
        if not signals:
            return None, 0.0

        # Pick highest confidence signal
        best_signal = max(signals, key=lambda x: x[1])
        return best_signal[0], best_signal[1]

    def _infer_owner(self, resource: Resource) -> Tuple[Optional[str], float]:
        """
        Infer resource owner with confidence score.

        Returns:
            Tuple of (owner, confidence_score)
        """
        signals = []

        # Signal 1: Owner tag (highest confidence)
        for tag_key in ['Owner', 'owner', 'Team', 'team', 'CreatedBy']:
            if tag_key in resource.tags:
                signals.append((resource.tags[tag_key], 1.0))

        # Signal 2: From CloudTrail (would need CloudTrail integration)
        # Placeholder for future implementation

        # Aggregate signals
        if not signals:
            return None, 0.0

        best_signal = max(signals, key=lambda x: x[1])
        return best_signal[0], best_signal[1]

    def _analyze_tag_patterns(self):
        """Analyze tag patterns across all resources."""
        logger.info("Analyzing tag patterns")

        # Count tag keys
        tag_key_counts = Counter()
        tag_values = {}  # tag_key -> list of values

        for resource in self.resources:
            for tag_key, tag_value in resource.tags.items():
                tag_key_counts[tag_key] += 1

                if tag_key not in tag_values:
                    tag_values[tag_key] = []
                tag_values[tag_key].append(tag_value)

        # Calculate patterns
        total_resources = len(self.resources)

        for tag_key, count in tag_key_counts.items():
            frequency = count / total_resources
            is_consistent = frequency > 0.8

            # Get most common values
            value_counter = Counter(tag_values[tag_key])
            common_values = [v for v, _ in value_counter.most_common(5)]

            pattern = TagPattern(
                tag_key=tag_key,
                frequency=frequency,
                common_values=common_values,
                is_consistent=is_consistent
            )

            self.tag_patterns[tag_key] = pattern

            if is_consistent:
                logger.info(f"Found consistent tag: {tag_key} ({frequency*100:.1f}%)")

    def _analyze_naming_patterns(self):
        """Detect naming conventions from resource names."""
        logger.info("Analyzing naming patterns")

        # Common patterns to look for
        patterns = [
            (r'^([a-zA-Z0-9-]+)-(prod|stage|dev)-(\d+)$', ['app', 'env', 'number']),
            (r'^(prod|stage|dev)-([a-zA-Z0-9-]+)-(\d+)$', ['env', 'app', 'number']),
            (r'^([a-zA-Z0-9-]+)-(prod|stage|dev)$', ['app', 'env']),
            (r'^([a-zA-Z0-9-]+)-(\d+)$', ['app', 'number']),
        ]

        for pattern_regex, fields in patterns:
            matches = 0
            example = None

            for resource in self.resources:
                if resource.name and re.match(pattern_regex, resource.name, re.IGNORECASE):
                    matches += 1
                    if not example:
                        example = resource.name

            if matches > 0:
                frequency = matches / len(self.resources)
                naming_pattern = NamingPattern(
                    pattern=pattern_regex,
                    example=example,
                    fields=fields,
                    frequency=frequency
                )
                self.naming_patterns.append(naming_pattern)

                if frequency > 0.3:  # More than 30% match
                    logger.info(f"Found naming pattern: {pattern_regex} "
                               f"({frequency*100:.1f}%, example: {example})")

    def _build_network_context(self):
        """Build VPC/subnet environment mappings."""
        logger.info("Building network context")

        # Map VPCs to environments based on tags
        vpc_resources = [r for r in self.resources if r.resource_type == 'vpc']
        for vpc in vpc_resources:
            env, confidence = self._infer_environment(vpc)
            if env and confidence > 0.7:
                self.vpc_environments[vpc.resource_id] = env
                logger.info(f"VPC {vpc.resource_id} → {env}")

        # Map subnets to environments
        subnet_resources = [r for r in self.resources if r.resource_type == 'subnet']
        for subnet in subnet_resources:
            # First try subnet tags
            env, confidence = self._infer_environment(subnet)

            # If not confident, use VPC environment
            if confidence < 0.7 and subnet.aws_state.get('vpc_id'):
                vpc_id = subnet.aws_state['vpc_id']
                if vpc_id in self.vpc_environments:
                    env = self.vpc_environments[vpc_id]
                    confidence = 0.6

            if env and confidence > 0.5:
                self.subnet_environments[subnet.resource_id] = env

    def get_coverage_report(self) -> Dict[str, any]:
        """
        Generate coverage report showing inference quality.

        Returns:
            Dict with coverage statistics
        """
        total = len(self.resources)
        with_env = sum(1 for r in self.resources if r.inferred_environment)
        with_project = sum(1 for r in self.resources if r.inferred_project)
        with_owner = sum(1 for r in self.resources if r.inferred_owner)

        # Confidence distribution
        high_confidence = sum(1 for r in self.resources if r.confidence_score >= 0.8)
        medium_confidence = sum(1 for r in self.resources if 0.5 <= r.confidence_score < 0.8)
        low_confidence = sum(1 for r in self.resources if 0 < r.confidence_score < 0.5)
        no_inference = sum(1 for r in self.resources if r.confidence_score == 0)

        return {
            'total_resources': total,
            'environment_coverage': {
                'count': with_env,
                'percentage': (with_env / total * 100) if total > 0 else 0
            },
            'project_coverage': {
                'count': with_project,
                'percentage': (with_project / total * 100) if total > 0 else 0
            },
            'owner_coverage': {
                'count': with_owner,
                'percentage': (with_owner / total * 100) if total > 0 else 0
            },
            'confidence_distribution': {
                'high': high_confidence,
                'medium': medium_confidence,
                'low': low_confidence,
                'none': no_inference
            },
            'tag_patterns': len(self.tag_patterns),
            'naming_patterns': len(self.naming_patterns)
        }
