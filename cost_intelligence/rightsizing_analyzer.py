"""
Right-Sizing Analyzer
=====================

Analyzes resource utilization and recommends optimal sizing.

Features:
- P95 CPU/Memory analysis
- Instance type recommendations
- Cost savings calculation
- Overprovisioning detection
- Multi-cloud support

Author: PromptOps Team - Q3 2026
Date: July 9, 2026
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta


class ResourceType(Enum):
    """Supported resource types"""
    EC2 = "ec2"
    RDS = "rds"
    ECS = "ecs"
    LAMBDA = "lambda"
    EKS = "eks"


class RecommendationAction(Enum):
    """Recommended actions"""
    DOWNSIZE = "downsize"
    UPSIZE = "upsize"
    KEEP = "keep"
    TERMINATE = "terminate"
    SWITCH_TYPE = "switch_type"


@dataclass
class UtilizationMetrics:
    """Resource utilization metrics"""
    cpu_p95: float
    cpu_avg: float
    cpu_max: float
    memory_p95: float
    memory_avg: float
    memory_max: float
    samples: int
    period_days: int


@dataclass
class InstanceSpec:
    """Instance/resource specification"""
    instance_type: str
    vcpus: int
    memory_gb: float
    price_hourly: float
    category: str  # 'general', 'compute', 'memory', 'storage'


@dataclass
class RightsizingRecommendation:
    """Right-sizing recommendation"""
    resource_id: str
    resource_type: ResourceType
    current_spec: InstanceSpec
    recommended_spec: InstanceSpec
    action: RecommendationAction
    utilization: UtilizationMetrics
    savings_monthly: float
    savings_percentage: float
    confidence: float
    reasoning: str
    risks: List[str]


@dataclass
class RightsizingConfig:
    """Configuration for right-sizing analysis"""
    # Utilization thresholds (%)
    cpu_underutilized_threshold: float = 30.0
    cpu_overutilized_threshold: float = 80.0
    memory_underutilized_threshold: float = 40.0
    memory_overutilized_threshold: float = 85.0

    # Idle resource thresholds
    cpu_idle_threshold: float = 10.0
    memory_idle_threshold: float = 15.0

    # Minimum observation period (days)
    min_observation_days: int = 7

    # Safety margin (%)
    safety_margin: float = 20.0


# AWS EC2 Instance Pricing (simplified - hourly rates in USD)
# In production, this would come from AWS Pricing API
AWS_INSTANCE_PRICING = {
    # T3 family (burstable)
    't3.nano': {'vcpus': 2, 'memory': 0.5, 'price': 0.0052, 'category': 'general'},
    't3.micro': {'vcpus': 2, 'memory': 1, 'price': 0.0104, 'category': 'general'},
    't3.small': {'vcpus': 2, 'memory': 2, 'price': 0.0208, 'category': 'general'},
    't3.medium': {'vcpus': 2, 'memory': 4, 'price': 0.0416, 'category': 'general'},
    't3.large': {'vcpus': 2, 'memory': 8, 'price': 0.0832, 'category': 'general'},

    # M5 family (general purpose)
    'm5.large': {'vcpus': 2, 'memory': 8, 'price': 0.096, 'category': 'general'},
    'm5.xlarge': {'vcpus': 4, 'memory': 16, 'price': 0.192, 'category': 'general'},
    'm5.2xlarge': {'vcpus': 8, 'memory': 32, 'price': 0.384, 'category': 'general'},
    'm5.4xlarge': {'vcpus': 16, 'memory': 64, 'price': 0.768, 'category': 'general'},

    # C5 family (compute optimized)
    'c5.large': {'vcpus': 2, 'memory': 4, 'price': 0.085, 'category': 'compute'},
    'c5.xlarge': {'vcpus': 4, 'memory': 8, 'price': 0.17, 'category': 'compute'},
    'c5.2xlarge': {'vcpus': 8, 'memory': 16, 'price': 0.34, 'category': 'compute'},
    'c5.4xlarge': {'vcpus': 16, 'memory': 32, 'price': 0.68, 'category': 'compute'},

    # R5 family (memory optimized)
    'r5.large': {'vcpus': 2, 'memory': 16, 'price': 0.126, 'category': 'memory'},
    'r5.xlarge': {'vcpus': 4, 'memory': 32, 'price': 0.252, 'category': 'memory'},
    'r5.2xlarge': {'vcpus': 8, 'memory': 64, 'price': 0.504, 'category': 'memory'},
    'r5.4xlarge': {'vcpus': 16, 'memory': 128, 'price': 1.008, 'category': 'memory'},
}


class RightsizingAnalyzer:
    """
    Analyzes resource utilization and generates right-sizing recommendations.

    Features:
    - P95-based utilization analysis
    - Multiple recommendation strategies
    - Cost-aware recommendations
    - Safety margin consideration
    - Confidence scoring

    Example:
        analyzer = RightsizingAnalyzer()
        recommendation = analyzer.analyze(resource_id, utilization_data)
    """

    def __init__(self, config: Optional[RightsizingConfig] = None):
        """Initialize analyzer with configuration"""
        self.config = config or RightsizingConfig()
        self.instance_catalog = self._build_instance_catalog()

    def analyze(
        self,
        resource_id: str,
        current_instance_type: str,
        utilization_data: List[Dict],
        resource_type: ResourceType = ResourceType.EC2
    ) -> RightsizingRecommendation:
        """
        Analyze resource and generate right-sizing recommendation.

        Args:
            resource_id: Resource identifier
            current_instance_type: Current instance type
            utilization_data: List of {timestamp, cpu, memory} dicts
            resource_type: Type of resource

        Returns:
            Right-sizing recommendation
        """
        # Calculate utilization metrics
        metrics = self._calculate_utilization_metrics(utilization_data)

        # Get current instance spec
        current_spec = self._get_instance_spec(current_instance_type)

        # Determine recommendation
        recommendation = self._generate_recommendation(
            resource_id,
            resource_type,
            current_spec,
            metrics
        )

        return recommendation

    def analyze_fleet(
        self,
        resources: List[Dict],
        resource_type: ResourceType = ResourceType.EC2
    ) -> Dict:
        """
        Analyze entire fleet of resources.

        Args:
            resources: List of {id, instance_type, utilization_data} dicts
            resource_type: Type of resources

        Returns:
            Fleet analysis with aggregated savings
        """
        recommendations = []
        total_savings = 0.0
        total_current_cost = 0.0

        for resource in resources:
            rec = self.analyze(
                resource['id'],
                resource['instance_type'],
                resource['utilization_data'],
                resource_type
            )
            recommendations.append(rec)
            total_savings += rec.savings_monthly
            total_current_cost += rec.current_spec.price_hourly * 730  # 730 hours/month

        # Aggregate by action type
        actions_breakdown = {}
        for rec in recommendations:
            action = rec.action.value
            actions_breakdown[action] = actions_breakdown.get(action, 0) + 1

        return {
            'total_resources': len(resources),
            'recommendations': recommendations,
            'actions_breakdown': actions_breakdown,
            'total_monthly_savings': round(total_savings, 2),
            'total_current_monthly_cost': round(total_current_cost, 2),
            'savings_percentage': round(total_savings / total_current_cost * 100, 2) if total_current_cost > 0 else 0,
            'high_confidence_recommendations': len([r for r in recommendations if r.confidence >= 0.8])
        }

    def find_optimal_instance(
        self,
        required_cpu: float,
        required_memory: float,
        workload_type: str = 'general'
    ) -> InstanceSpec:
        """
        Find optimal instance type for given requirements.

        Args:
            required_cpu: Required vCPUs
            required_memory: Required memory (GB)
            workload_type: Workload type ('general', 'compute', 'memory')

        Returns:
            Optimal instance specification
        """
        # Add safety margin
        required_cpu *= (1 + self.config.safety_margin / 100)
        required_memory *= (1 + self.config.safety_margin / 100)

        # Filter by workload type
        candidates = [
            spec for spec in self.instance_catalog
            if spec.category == workload_type
            and spec.vcpus >= required_cpu
            and spec.memory_gb >= required_memory
        ]

        if not candidates:
            # Fallback to general purpose
            candidates = [
                spec for spec in self.instance_catalog
                if spec.vcpus >= required_cpu
                and spec.memory_gb >= required_memory
            ]

        # Find cheapest that meets requirements
        return min(candidates, key=lambda x: x.price_hourly)

    # ========================================================================
    # Internal Methods
    # ========================================================================

    def _calculate_utilization_metrics(
        self,
        utilization_data: List[Dict]
    ) -> UtilizationMetrics:
        """Calculate P95 and average utilization metrics"""
        if not utilization_data:
            raise ValueError("No utilization data provided")

        cpu_values = np.array([d['cpu'] for d in utilization_data])
        memory_values = np.array([d['memory'] for d in utilization_data])

        # Calculate timestamps range
        if 'timestamp' in utilization_data[0]:
            timestamps = [d['timestamp'] for d in utilization_data]
            period_days = (max(timestamps) - min(timestamps)).days
        else:
            period_days = len(utilization_data) // 24  # Assume hourly data

        return UtilizationMetrics(
            cpu_p95=np.percentile(cpu_values, 95),
            cpu_avg=np.mean(cpu_values),
            cpu_max=np.max(cpu_values),
            memory_p95=np.percentile(memory_values, 95),
            memory_avg=np.mean(memory_values),
            memory_max=np.max(memory_values),
            samples=len(utilization_data),
            period_days=period_days
        )

    def _generate_recommendation(
        self,
        resource_id: str,
        resource_type: ResourceType,
        current_spec: InstanceSpec,
        metrics: UtilizationMetrics
    ) -> RightsizingRecommendation:
        """Generate right-sizing recommendation based on utilization"""
        # Check if resource is idle
        if (metrics.cpu_avg < self.config.cpu_idle_threshold and
            metrics.memory_avg < self.config.memory_idle_threshold):
            return self._recommend_termination(
                resource_id, resource_type, current_spec, metrics
            )

        # Check if underutilized
        if (metrics.cpu_avg < self.config.cpu_underutilized_threshold and
            metrics.memory_avg < self.config.memory_underutilized_threshold):
            return self._recommend_downsize(
                resource_id, resource_type, current_spec, metrics
            )

        # Check if overutilized
        if (metrics.cpu_avg > self.config.cpu_overutilized_threshold or
            metrics.memory_avg > self.config.memory_overutilized_threshold):
            return self._recommend_upsize(
                resource_id, resource_type, current_spec, metrics
            )

        # Well-sized
        return self._recommend_keep(
            resource_id, resource_type, current_spec, metrics
        )

    def _recommend_downsize(
        self,
        resource_id: str,
        resource_type: ResourceType,
        current_spec: InstanceSpec,
        metrics: UtilizationMetrics
    ) -> RightsizingRecommendation:
        """Recommend downsizing"""
        # Calculate required resources based on P95 + safety margin
        required_cpu = (metrics.cpu_p95 / 100) * current_spec.vcpus
        required_memory = (metrics.memory_p95 / 100) * current_spec.memory_gb

        # Find optimal instance
        recommended_spec = self.find_optimal_instance(
            required_cpu, required_memory, current_spec.category
        )

        # Calculate savings
        current_monthly = current_spec.price_hourly * 730
        recommended_monthly = recommended_spec.price_hourly * 730
        savings = current_monthly - recommended_monthly
        savings_pct = (savings / current_monthly * 100) if current_monthly > 0 else 0

        # Calculate confidence
        confidence = self._calculate_confidence(metrics, 'downsize')

        # Identify risks
        risks = []
        if metrics.cpu_max > 90:
            risks.append("CPU spikes above 90% detected")
        if metrics.memory_max > 90:
            risks.append("Memory spikes above 90% detected")
        if metrics.period_days < self.config.min_observation_days:
            risks.append(f"Limited observation period ({metrics.period_days} days)")

        reasoning = (
            f"Resource is underutilized. P95 CPU: {metrics.cpu_p95:.1f}%, "
            f"P95 Memory: {metrics.memory_p95:.1f}%. "
            f"Downsizing from {current_spec.instance_type} to {recommended_spec.instance_type} "
            f"will save ${savings:.2f}/month while maintaining adequate capacity."
        )

        return RightsizingRecommendation(
            resource_id=resource_id,
            resource_type=resource_type,
            current_spec=current_spec,
            recommended_spec=recommended_spec,
            action=RecommendationAction.DOWNSIZE,
            utilization=metrics,
            savings_monthly=round(savings, 2),
            savings_percentage=round(savings_pct, 2),
            confidence=confidence,
            reasoning=reasoning,
            risks=risks
        )

    def _recommend_upsize(
        self,
        resource_id: str,
        resource_type: ResourceType,
        current_spec: InstanceSpec,
        metrics: UtilizationMetrics
    ) -> RightsizingRecommendation:
        """Recommend upsizing"""
        # Find next larger instance
        larger_instances = [
            spec for spec in self.instance_catalog
            if spec.category == current_spec.category
            and (spec.vcpus > current_spec.vcpus or spec.memory_gb > current_spec.memory_gb)
            and spec.price_hourly > current_spec.price_hourly
        ]

        if not larger_instances:
            recommended_spec = current_spec
            action = RecommendationAction.KEEP
        else:
            recommended_spec = min(larger_instances, key=lambda x: x.price_hourly)
            action = RecommendationAction.UPSIZE

        # Calculate cost increase
        current_monthly = current_spec.price_hourly * 730
        recommended_monthly = recommended_spec.price_hourly * 730
        cost_increase = recommended_monthly - current_monthly

        confidence = self._calculate_confidence(metrics, 'upsize')

        reasoning = (
            f"Resource is overutilized. P95 CPU: {metrics.cpu_p95:.1f}%, "
            f"P95 Memory: {metrics.memory_p95:.1f}%. "
            f"Upsizing to {recommended_spec.instance_type} recommended to avoid performance issues."
        )

        return RightsizingRecommendation(
            resource_id=resource_id,
            resource_type=resource_type,
            current_spec=current_spec,
            recommended_spec=recommended_spec,
            action=action,
            utilization=metrics,
            savings_monthly=round(-cost_increase, 2),  # Negative = cost increase
            savings_percentage=round(-cost_increase / current_monthly * 100, 2),
            confidence=confidence,
            reasoning=reasoning,
            risks=["Performance degradation if not upsized"]
        )

    def _recommend_keep(
        self,
        resource_id: str,
        resource_type: ResourceType,
        current_spec: InstanceSpec,
        metrics: UtilizationMetrics
    ) -> RightsizingRecommendation:
        """Recommend keeping current size"""
        confidence = self._calculate_confidence(metrics, 'keep')

        reasoning = (
            f"Resource is well-sized. P95 CPU: {metrics.cpu_p95:.1f}%, "
            f"P95 Memory: {metrics.memory_p95:.1f}%. "
            f"Current instance type {current_spec.instance_type} is appropriate."
        )

        return RightsizingRecommendation(
            resource_id=resource_id,
            resource_type=resource_type,
            current_spec=current_spec,
            recommended_spec=current_spec,
            action=RecommendationAction.KEEP,
            utilization=metrics,
            savings_monthly=0.0,
            savings_percentage=0.0,
            confidence=confidence,
            reasoning=reasoning,
            risks=[]
        )

    def _recommend_termination(
        self,
        resource_id: str,
        resource_type: ResourceType,
        current_spec: InstanceSpec,
        metrics: UtilizationMetrics
    ) -> RightsizingRecommendation:
        """Recommend terminating idle resource"""
        current_monthly = current_spec.price_hourly * 730
        confidence = self._calculate_confidence(metrics, 'terminate')

        reasoning = (
            f"Resource appears idle. P95 CPU: {metrics.cpu_p95:.1f}%, "
            f"P95 Memory: {metrics.memory_p95:.1f}%. "
            f"Consider terminating to save ${current_monthly:.2f}/month."
        )

        return RightsizingRecommendation(
            resource_id=resource_id,
            resource_type=resource_type,
            current_spec=current_spec,
            recommended_spec=current_spec,
            action=RecommendationAction.TERMINATE,
            utilization=metrics,
            savings_monthly=round(current_monthly, 2),
            savings_percentage=100.0,
            confidence=confidence,
            reasoning=reasoning,
            risks=["Verify resource is truly unused before terminating"]
        )

    def _calculate_confidence(self, metrics: UtilizationMetrics, action: str) -> float:
        """Calculate confidence score for recommendation"""
        confidence = 0.5

        # More samples = higher confidence
        if metrics.samples >= 1000:
            confidence += 0.2
        elif metrics.samples >= 500:
            confidence += 0.1

        # Longer observation = higher confidence
        if metrics.period_days >= 30:
            confidence += 0.2
        elif metrics.period_days >= 14:
            confidence += 0.1

        # Consistent utilization = higher confidence
        if action in ['downsize', 'terminate']:
            if metrics.cpu_max < metrics.cpu_p95 * 1.2:  # Low variance
                confidence += 0.1

        return min(round(confidence, 2), 1.0)

    def _get_instance_spec(self, instance_type: str) -> InstanceSpec:
        """Get instance specification"""
        if instance_type not in AWS_INSTANCE_PRICING:
            raise ValueError(f"Unknown instance type: {instance_type}")

        spec = AWS_INSTANCE_PRICING[instance_type]
        return InstanceSpec(
            instance_type=instance_type,
            vcpus=spec['vcpus'],
            memory_gb=spec['memory'],
            price_hourly=spec['price'],
            category=spec['category']
        )

    def _build_instance_catalog(self) -> List[InstanceSpec]:
        """Build catalog of available instances"""
        catalog = []
        for instance_type, spec in AWS_INSTANCE_PRICING.items():
            catalog.append(InstanceSpec(
                instance_type=instance_type,
                vcpus=spec['vcpus'],
                memory_gb=spec['memory'],
                price_hourly=spec['price'],
                category=spec['category']
            ))
        return sorted(catalog, key=lambda x: x.price_hourly)


# ============================================================================
# Utility Functions
# ============================================================================

def generate_utilization_data(
    days: int = 30,
    cpu_avg: float = 30.0,
    memory_avg: float = 40.0,
    variance: float = 10.0
) -> List[Dict]:
    """Generate sample utilization data for testing"""
    data = []
    start_date = datetime.utcnow() - timedelta(days=days)

    for hour in range(days * 24):
        data.append({
            'timestamp': start_date + timedelta(hours=hour),
            'cpu': max(0, min(100, np.random.normal(cpu_avg, variance))),
            'memory': max(0, min(100, np.random.normal(memory_avg, variance)))
        })

    return data
