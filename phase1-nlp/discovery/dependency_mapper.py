"""
Dependency Mapper
=================

Build dependency graph showing relationships between AWS resources.

Week 16-18: ENHANCEMENT-003
Author: PromptOps Team
Date: 2026-04-30
"""

from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import logging

from .aws_scanner import Resource

logger = logging.getLogger(__name__)


@dataclass
class Dependency:
    """Represents a dependency between two resources."""
    source_resource_id: str
    target_resource_id: str
    dependency_type: str  # security_group, network, iam, application
    confidence_score: float  # 0.0 to 1.0


@dataclass
class DependencyGraph:
    """Graph of resource dependencies."""
    dependencies: List[Dependency] = field(default_factory=list)
    resources: Dict[str, Resource] = field(default_factory=dict)

    def add_dependency(self, source_id: str, target_id: str,
                      dependency_type: str, confidence: float = 1.0):
        """Add a dependency to the graph."""
        dep = Dependency(
            source_resource_id=source_id,
            target_resource_id=target_id,
            dependency_type=dependency_type,
            confidence_score=confidence
        )
        self.dependencies.append(dep)

    def get_dependencies_for(self, resource_id: str) -> List[Dependency]:
        """Get all dependencies for a resource."""
        return [d for d in self.dependencies if d.source_resource_id == resource_id]

    def get_dependents_of(self, resource_id: str) -> List[Dependency]:
        """Get all resources that depend on this resource."""
        return [d for d in self.dependencies if d.target_resource_id == resource_id]

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'dependencies': [
                {
                    'source': d.source_resource_id,
                    'target': d.target_resource_id,
                    'type': d.dependency_type,
                    'confidence': d.confidence_score
                }
                for d in self.dependencies
            ],
            'total_dependencies': len(self.dependencies),
            'by_type': self._count_by_type()
        }

    def _count_by_type(self) -> Dict[str, int]:
        """Count dependencies by type."""
        counts = defaultdict(int)
        for dep in self.dependencies:
            counts[dep.dependency_type] += 1
        return dict(counts)


class DependencyMapper:
    """
    Map dependencies between AWS resources.

    Detects:
    - Security group dependencies (EC2 → SG, RDS → SG)
    - Network dependencies (EC2 → Subnet → VPC)
    - IAM dependencies (EC2 → IAM Role)
    - Application dependencies (ECS → RDS via security groups)
    """

    def __init__(self, resources: List[Resource]):
        """
        Initialize dependency mapper.

        Args:
            resources: List of discovered resources
        """
        self.resources = resources
        self.resource_map = {r.resource_id: r for r in resources}

    def build_dependency_graph(self) -> DependencyGraph:
        """
        Build complete dependency graph.

        Returns:
            DependencyGraph with all detected dependencies
        """
        logger.info(f"Building dependency graph for {len(self.resources)} resources")

        graph = DependencyGraph()
        graph.resources = self.resource_map

        # Map different types of dependencies
        self._map_security_group_dependencies(graph)
        self._map_network_dependencies(graph)
        self._map_iam_dependencies(graph)
        self._infer_application_dependencies(graph)

        logger.info(f"Dependency graph complete: {len(graph.dependencies)} dependencies")

        return graph

    def _map_security_group_dependencies(self, graph: DependencyGraph):
        """Map security group dependencies."""
        logger.info("Mapping security group dependencies")

        for resource in self.resources:
            security_groups = None

            # EC2 instances
            if resource.resource_type == 'ec2':
                security_groups = resource.aws_state.get('security_groups', [])

            # RDS databases
            elif resource.resource_type == 'rds':
                security_groups = resource.aws_state.get('security_groups', [])

            # Add dependencies
            if security_groups:
                for sg_id in security_groups:
                    if sg_id in self.resource_map:
                        graph.add_dependency(
                            source_id=resource.resource_id,
                            target_id=sg_id,
                            dependency_type='security_group',
                            confidence=1.0
                        )

    def _map_network_dependencies(self, graph: DependencyGraph):
        """Map network (VPC, subnet) dependencies."""
        logger.info("Mapping network dependencies")

        for resource in self.resources:
            # Resources with subnet_id
            if resource.resource_type in ['ec2', 'rds']:
                subnet_id = resource.aws_state.get('subnet_id')
                if subnet_id and subnet_id in self.resource_map:
                    graph.add_dependency(
                        source_id=resource.resource_id,
                        target_id=subnet_id,
                        dependency_type='network',
                        confidence=1.0
                    )

                # Also add VPC dependency
                vpc_id = resource.aws_state.get('vpc_id')
                if vpc_id and vpc_id in self.resource_map:
                    graph.add_dependency(
                        source_id=resource.resource_id,
                        target_id=vpc_id,
                        dependency_type='network',
                        confidence=1.0
                    )

            # Subnets depend on VPCs
            if resource.resource_type == 'subnet':
                vpc_id = resource.aws_state.get('vpc_id')
                if vpc_id and vpc_id in self.resource_map:
                    graph.add_dependency(
                        source_id=resource.resource_id,
                        target_id=vpc_id,
                        dependency_type='network',
                        confidence=1.0
                    )

    def _map_iam_dependencies(self, graph: DependencyGraph):
        """Map IAM role dependencies."""
        logger.info("Mapping IAM dependencies")

        for resource in self.resources:
            # EC2 instances with IAM instance profiles
            if resource.resource_type == 'ec2':
                iam_profile_arn = resource.aws_state.get('iam_instance_profile')
                if iam_profile_arn:
                    # Extract role name from ARN
                    # Would need to map to actual IAM role resource
                    # Placeholder for now
                    pass

    def _infer_application_dependencies(self, graph: DependencyGraph):
        """
        Infer application-level dependencies.

        Uses heuristics:
        - Resources sharing security groups likely communicate
        - Same VPC + similar names suggest application relationship
        """
        logger.info("Inferring application dependencies")

        # Build security group usage map
        sg_usage = defaultdict(list)  # sg_id -> [resource_ids]

        for resource in self.resources:
            if resource.resource_type in ['ec2', 'rds']:
                security_groups = resource.aws_state.get('security_groups', [])
                for sg_id in security_groups:
                    sg_usage[sg_id].append(resource.resource_id)

        # Infer dependencies between resources sharing security groups
        for sg_id, resource_ids in sg_usage.items():
            # If multiple resources share a security group, they likely communicate
            if len(resource_ids) >= 2:
                # Common pattern: EC2 → RDS (web server → database)
                ec2_resources = [rid for rid in resource_ids if self.resource_map[rid].resource_type == 'ec2']
                rds_resources = [rid for rid in resource_ids if self.resource_map[rid].resource_type == 'rds']

                for ec2_id in ec2_resources:
                    for rds_id in rds_resources:
                        graph.add_dependency(
                            source_id=ec2_id,
                            target_id=rds_id,
                            dependency_type='application',
                            confidence=0.7  # Inferred, not explicit
                        )

    def get_dependency_report(self, graph: DependencyGraph) -> Dict:
        """
        Generate dependency analysis report.

        Returns:
            Dict with dependency statistics
        """
        total_deps = len(graph.dependencies)
        by_type = graph._count_by_type()

        # Find resources with most dependencies
        dependency_counts = defaultdict(int)
        for dep in graph.dependencies:
            dependency_counts[dep.source_resource_id] += 1

        most_dependent = sorted(dependency_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        # Find resources most depended upon
        dependent_counts = defaultdict(int)
        for dep in graph.dependencies:
            dependent_counts[dep.target_resource_id] += 1

        most_depended_upon = sorted(dependent_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            'total_dependencies': total_deps,
            'by_type': by_type,
            'most_dependent_resources': [
                {
                    'resource_id': rid,
                    'resource_type': self.resource_map[rid].resource_type,
                    'dependency_count': count
                }
                for rid, count in most_dependent
            ],
            'most_depended_upon_resources': [
                {
                    'resource_id': rid,
                    'resource_type': self.resource_map[rid].resource_type,
                    'dependent_count': count
                }
                for rid, count in most_depended_upon
            ]
        }
