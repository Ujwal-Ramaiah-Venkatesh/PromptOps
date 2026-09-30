"""
Cost Intelligence Engine
========================

ML-powered cost optimization and forecasting for cloud infrastructure.

Features:
- Anomaly detection (Z-score, IQR, Isolation Forest, Moving Average)
- Cost forecasting (Facebook Prophet, <5% MAPE target)
- Right-sizing analysis (P95-based recommendations)
- Savings opportunity identification
- Multi-cloud support

Author: PromptOps Team - Q3 2026
Date: July 9, 2026
"""

from .anomaly_detector import (
    CostAnomalyDetector,
    Anomaly,
    AnomalyMethod,
    AnomalySeverity,
    AnomalyDetectionConfig,
    generate_sample_cost_data,
    analyze_anomalies
)

from .cost_forecaster import (
    CostForecaster,
    Forecast,
    ForecastAnalysis,
    ForecastConfig,
    generate_cost_projection,
    compare_forecasts
)

from .rightsizing_analyzer import (
    RightsizingAnalyzer,
    RightsizingRecommendation,
    UtilizationMetrics,
    InstanceSpec,
    ResourceType,
    RecommendationAction,
    RightsizingConfig,
    generate_utilization_data
)

__version__ = "1.0.0"
__author__ = "PromptOps Team"

__all__ = [
    # Anomaly Detection
    'CostAnomalyDetector',
    'Anomaly',
    'AnomalyMethod',
    'AnomalySeverity',
    'AnomalyDetectionConfig',
    'generate_sample_cost_data',
    'analyze_anomalies',

    # Cost Forecasting
    'CostForecaster',
    'Forecast',
    'ForecastAnalysis',
    'ForecastConfig',
    'generate_cost_projection',
    'compare_forecasts',

    # Right-Sizing
    'RightsizingAnalyzer',
    'RightsizingRecommendation',
    'UtilizationMetrics',
    'InstanceSpec',
    'ResourceType',
    'RecommendationAction',
    'RightsizingConfig',
    'generate_utilization_data',
]
