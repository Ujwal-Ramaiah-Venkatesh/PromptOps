"""
Post-Deployment Application Monitoring
=======================================

Continuous monitoring for deployed applications:
- Health checks and uptime monitoring
- Performance metrics (response time, error rates)
- Security vulnerability scanning
- Auto-scaling triggers
- Alerting and notifications

Author: PromptOps Team
Date: 2026-06-03
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
import boto3
import requests
import logging
import asyncio
from collections import defaultdict

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/monitor/deployed", tags=["deployed-app-monitoring"])


# ============================================================================
# Data Models
# ============================================================================

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class SecuritySeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class MonitoringConfig(BaseModel):
    """Configuration for application monitoring"""
    app_name: str
    deployment_url: HttpUrl
    bucket_name: str
    region: str = "us-east-1"
    check_interval_seconds: int = 60
    alert_email: Optional[str] = None
    enable_auto_scaling: bool = False
    enable_security_scan: bool = True


class HealthCheckResult(BaseModel):
    """Result of health check"""
    app_name: str
    status: HealthStatus
    response_time_ms: float
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    timestamp: datetime
    uptime_percentage: Optional[float] = None


class SecurityVulnerability(BaseModel):
    """Security vulnerability finding"""
    id: str
    severity: SecuritySeverity
    title: str
    description: str
    affected_resource: str
    remediation: str
    detected_at: datetime


class PerformanceMetrics(BaseModel):
    """Performance metrics for deployed app"""
    app_name: str
    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    error_rate_percentage: float
    requests_per_minute: float
    timestamp: datetime


class ScalingRecommendation(BaseModel):
    """Auto-scaling recommendation"""
    app_name: str
    current_capacity: str
    recommended_capacity: str
    reason: str
    estimated_cost_impact: float
    timestamp: datetime


# ============================================================================
# In-Memory Storage (Replace with database in production)
# ============================================================================

monitored_apps: Dict[str, MonitoringConfig] = {}
health_history: Dict[str, List[HealthCheckResult]] = defaultdict(list)
security_findings: Dict[str, List[SecurityVulnerability]] = defaultdict(list)
performance_history: Dict[str, List[PerformanceMetrics]] = defaultdict(list)


# ============================================================================
# Helper Functions
# ============================================================================

def get_s3_client(region: str):
    """Get S3 client for specified region"""
    return boto3.client('s3', region_name=region)


def get_cloudwatch_client(region: str):
    """Get CloudWatch client for specified region"""
    return boto3.client('cloudwatch', region_name=region)


async def perform_health_check(config: MonitoringConfig) -> HealthCheckResult:
    """Perform health check on deployed application"""
    try:
        start_time = datetime.now()
        response = requests.get(
            str(config.deployment_url),
            timeout=10,
            allow_redirects=True
        )
        response_time = (datetime.now() - start_time).total_seconds() * 1000

        # Determine health status
        if response.status_code == 200:
            status = HealthStatus.HEALTHY
        elif 200 <= response.status_code < 300:
            status = HealthStatus.HEALTHY
        elif 400 <= response.status_code < 500:
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.UNHEALTHY

        # Calculate uptime percentage (last 24 hours)
        uptime_pct = calculate_uptime_percentage(config.app_name)

        return HealthCheckResult(
            app_name=config.app_name,
            status=status,
            response_time_ms=response_time,
            status_code=response.status_code,
            timestamp=datetime.now(),
            uptime_percentage=uptime_pct
        )

    except requests.Timeout:
        return HealthCheckResult(
            app_name=config.app_name,
            status=HealthStatus.UNHEALTHY,
            response_time_ms=10000.0,
            error_message="Request timeout (>10s)",
            timestamp=datetime.now()
        )
    except requests.RequestException as e:
        return HealthCheckResult(
            app_name=config.app_name,
            status=HealthStatus.UNHEALTHY,
            response_time_ms=0.0,
            error_message=str(e),
            timestamp=datetime.now()
        )


def calculate_uptime_percentage(app_name: str) -> float:
    """Calculate uptime percentage for last 24 hours"""
    if app_name not in health_history:
        return 100.0

    cutoff_time = datetime.now() - timedelta(hours=24)
    recent_checks = [
        h for h in health_history[app_name]
        if h.timestamp >= cutoff_time
    ]

    if not recent_checks:
        return 100.0

    healthy_count = sum(
        1 for check in recent_checks
        if check.status == HealthStatus.HEALTHY
    )

    return (healthy_count / len(recent_checks)) * 100


async def scan_security_vulnerabilities(config: MonitoringConfig) -> List[SecurityVulnerability]:
    """Scan deployed application for security vulnerabilities"""
    vulnerabilities = []

    try:
        s3 = get_s3_client(config.region)

        # Check 1: Bucket public access
        try:
            public_access_block = s3.get_public_access_block(Bucket=config.bucket_name)
            settings = public_access_block['PublicAccessBlockConfiguration']

            if not all([
                settings.get('BlockPublicAcls', False),
                settings.get('IgnorePublicAcls', False),
                settings.get('BlockPublicPolicy', False),
                settings.get('RestrictPublicBuckets', False)
            ]):
                vulnerabilities.append(SecurityVulnerability(
                    id=f"SEC-{config.app_name}-001",
                    severity=SecuritySeverity.HIGH,
                    title="S3 Bucket Allows Public Access",
                    description="Bucket has public access enabled. This may expose sensitive data.",
                    affected_resource=config.bucket_name,
                    remediation="Enable all S3 Block Public Access settings unless public hosting is required.",
                    detected_at=datetime.now()
                ))
        except s3.exceptions.NoSuchPublicAccessBlockConfiguration:
            vulnerabilities.append(SecurityVulnerability(
                id=f"SEC-{config.app_name}-001",
                severity=SecuritySeverity.MEDIUM,
                title="No Public Access Block Configuration",
                description="Bucket does not have public access block configuration set.",
                affected_resource=config.bucket_name,
                remediation="Configure S3 Block Public Access settings.",
                detected_at=datetime.now()
            ))

        # Check 2: Bucket encryption
        try:
            encryption = s3.get_bucket_encryption(Bucket=config.bucket_name)
        except s3.exceptions.ServerSideEncryptionConfigurationNotFoundError:
            vulnerabilities.append(SecurityVulnerability(
                id=f"SEC-{config.app_name}-002",
                severity=SecuritySeverity.MEDIUM,
                title="S3 Bucket Not Encrypted",
                description="Bucket does not have server-side encryption enabled.",
                affected_resource=config.bucket_name,
                remediation="Enable S3 server-side encryption (SSE-S3 or SSE-KMS).",
                detected_at=datetime.now()
            ))

        # Check 3: Bucket versioning
        try:
            versioning = s3.get_bucket_versioning(Bucket=config.bucket_name)
            if versioning.get('Status') != 'Enabled':
                vulnerabilities.append(SecurityVulnerability(
                    id=f"SEC-{config.app_name}-003",
                    severity=SecuritySeverity.LOW,
                    title="S3 Bucket Versioning Not Enabled",
                    description="Bucket versioning is disabled. Cannot recover from accidental deletions.",
                    affected_resource=config.bucket_name,
                    remediation="Enable S3 bucket versioning for data protection.",
                    detected_at=datetime.now()
                ))
        except Exception as e:
            logger.warning(f"Could not check bucket versioning: {e}")

        # Check 4: Access logging
        try:
            logging_config = s3.get_bucket_logging(Bucket=config.bucket_name)
            if 'LoggingEnabled' not in logging_config:
                vulnerabilities.append(SecurityVulnerability(
                    id=f"SEC-{config.app_name}-004",
                    severity=SecuritySeverity.LOW,
                    title="S3 Access Logging Not Enabled",
                    description="Bucket access logging is disabled. Cannot audit access patterns.",
                    affected_resource=config.bucket_name,
                    remediation="Enable S3 server access logging for audit trails.",
                    detected_at=datetime.now()
                ))
        except Exception as e:
            logger.warning(f"Could not check bucket logging: {e}")

        # Check 5: HTTP endpoint (no HTTPS)
        if str(config.deployment_url).startswith('http://'):
            vulnerabilities.append(SecurityVulnerability(
                id=f"SEC-{config.app_name}-005",
                severity=SecuritySeverity.HIGH,
                title="Application Not Using HTTPS",
                description="Application is accessible over HTTP. Data transmission is not encrypted.",
                affected_resource=str(config.deployment_url),
                remediation="Configure CloudFront with ACM certificate for HTTPS support.",
                detected_at=datetime.now()
            ))

    except Exception as e:
        logger.error(f"Security scan error for {config.app_name}: {e}")

    return vulnerabilities


async def check_scaling_needs(config: MonitoringConfig) -> Optional[ScalingRecommendation]:
    """Analyze performance and recommend scaling actions"""
    if not config.enable_auto_scaling:
        return None

    if config.app_name not in performance_history:
        return None

    # Get recent performance metrics
    cutoff_time = datetime.now() - timedelta(hours=1)
    recent_metrics = [
        m for m in performance_history[config.app_name]
        if m.timestamp >= cutoff_time
    ]

    if not recent_metrics:
        return None

    avg_response_time = sum(m.avg_response_time_ms for m in recent_metrics) / len(recent_metrics)
    avg_error_rate = sum(m.error_rate_percentage for m in recent_metrics) / len(recent_metrics)
    avg_rpm = sum(m.requests_per_minute for m in recent_metrics) / len(recent_metrics)

    # Scaling logic
    if avg_response_time > 1000 or avg_error_rate > 5.0:
        return ScalingRecommendation(
            app_name=config.app_name,
            current_capacity="Standard S3 hosting",
            recommended_capacity="CloudFront + S3 with edge caching",
            reason=f"High response time ({avg_response_time:.0f}ms) or error rate ({avg_error_rate:.1f}%)",
            estimated_cost_impact=10.0,  # $10/month estimate
            timestamp=datetime.now()
        )

    if avg_rpm > 1000:
        return ScalingRecommendation(
            app_name=config.app_name,
            current_capacity="Standard S3 hosting",
            recommended_capacity="CloudFront CDN distribution",
            reason=f"High traffic volume ({avg_rpm:.0f} requests/min)",
            estimated_cost_impact=15.0,
            timestamp=datetime.now()
        )

    return None


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/register", status_code=201)
async def register_application_monitoring(config: MonitoringConfig):
    """
    Register an application for continuous monitoring.

    Starts monitoring health, security, and performance metrics.
    """
    monitored_apps[config.app_name] = config

    # Perform initial health check
    initial_health = await perform_health_check(config)
    health_history[config.app_name].append(initial_health)

    # Perform initial security scan if enabled
    initial_vulnerabilities = []
    if config.enable_security_scan:
        initial_vulnerabilities = await scan_security_vulnerabilities(config)
        security_findings[config.app_name] = initial_vulnerabilities

    return {
        "status": "registered",
        "app_name": config.app_name,
        "monitoring_enabled": True,
        "check_interval_seconds": config.check_interval_seconds,
        "initial_health": initial_health.dict(),
        "initial_security_findings": len(initial_vulnerabilities),
        "message": f"Application {config.app_name} is now being monitored"
    }


@router.get("/health/{app_name}")
async def get_application_health(app_name: str):
    """Get current health status of deployed application"""
    if app_name not in monitored_apps:
        raise HTTPException(status_code=404, detail=f"Application {app_name} is not being monitored")

    # Perform fresh health check
    config = monitored_apps[app_name]
    health_result = await perform_health_check(config)
    health_history[app_name].append(health_result)

    # Keep only last 24 hours
    cutoff_time = datetime.now() - timedelta(hours=24)
    health_history[app_name] = [
        h for h in health_history[app_name]
        if h.timestamp >= cutoff_time
    ]

    return {
        "current_health": health_result.dict(),
        "history_count": len(health_history[app_name]),
        "uptime_24h": health_result.uptime_percentage
    }


@router.get("/security/{app_name}")
async def get_security_vulnerabilities(app_name: str, rescan: bool = False):
    """Get security vulnerability findings for deployed application"""
    if app_name not in monitored_apps:
        raise HTTPException(status_code=404, detail=f"Application {app_name} is not being monitored")

    config = monitored_apps[app_name]

    # Rescan if requested
    if rescan:
        vulnerabilities = await scan_security_vulnerabilities(config)
        security_findings[app_name] = vulnerabilities
    else:
        vulnerabilities = security_findings.get(app_name, [])

    # Group by severity
    by_severity = {
        "critical": [],
        "high": [],
        "medium": [],
        "low": [],
        "info": []
    }

    for vuln in vulnerabilities:
        by_severity[vuln.severity.value].append(vuln.dict())

    return {
        "app_name": app_name,
        "total_findings": len(vulnerabilities),
        "by_severity": by_severity,
        "last_scan": datetime.now().isoformat() if rescan else None,
        "vulnerabilities": [v.dict() for v in vulnerabilities]
    }


@router.get("/performance/{app_name}")
async def get_performance_metrics(app_name: str, hours: int = 1):
    """Get performance metrics for deployed application"""
    if app_name not in monitored_apps:
        raise HTTPException(status_code=404, detail=f"Application {app_name} is not being monitored")

    cutoff_time = datetime.now() - timedelta(hours=hours)
    recent_metrics = [
        m for m in performance_history.get(app_name, [])
        if m.timestamp >= cutoff_time
    ]

    if not recent_metrics:
        return {
            "app_name": app_name,
            "metrics": [],
            "summary": {
                "avg_response_time_ms": 0,
                "avg_error_rate": 0,
                "total_requests": 0
            }
        }

    avg_response_time = sum(m.avg_response_time_ms for m in recent_metrics) / len(recent_metrics)
    avg_error_rate = sum(m.error_rate_percentage for m in recent_metrics) / len(recent_metrics)
    total_requests = sum(m.requests_per_minute for m in recent_metrics) * 60

    return {
        "app_name": app_name,
        "time_range_hours": hours,
        "metrics": [m.dict() for m in recent_metrics],
        "summary": {
            "avg_response_time_ms": round(avg_response_time, 2),
            "avg_error_rate": round(avg_error_rate, 2),
            "total_requests_estimate": round(total_requests)
        }
    }


@router.get("/scaling/{app_name}")
async def get_scaling_recommendation(app_name: str):
    """Get auto-scaling recommendations for deployed application"""
    if app_name not in monitored_apps:
        raise HTTPException(status_code=404, detail=f"Application {app_name} is not being monitored")

    config = monitored_apps[app_name]
    recommendation = await check_scaling_needs(config)

    if recommendation:
        return {
            "needs_scaling": True,
            "recommendation": recommendation.dict()
        }
    else:
        return {
            "needs_scaling": False,
            "message": "Current capacity is sufficient"
        }


@router.get("/status/{app_name}")
async def get_monitoring_status(app_name: str):
    """Get overall monitoring status and summary"""
    if app_name not in monitored_apps:
        raise HTTPException(status_code=404, detail=f"Application {app_name} is not being monitored")

    config = monitored_apps[app_name]

    # Get latest data
    latest_health = health_history[app_name][-1] if health_history[app_name] else None
    vulnerabilities = security_findings.get(app_name, [])
    critical_vulns = [v for v in vulnerabilities if v.severity == SecuritySeverity.CRITICAL]
    high_vulns = [v for v in vulnerabilities if v.severity == SecuritySeverity.HIGH]

    return {
        "app_name": app_name,
        "deployment_url": str(config.deployment_url),
        "monitoring_since": health_history[app_name][0].timestamp.isoformat() if health_history[app_name] else None,
        "health": {
            "status": latest_health.status.value if latest_health else "unknown",
            "uptime_24h": latest_health.uptime_percentage if latest_health else None,
            "response_time_ms": latest_health.response_time_ms if latest_health else None
        },
        "security": {
            "total_findings": len(vulnerabilities),
            "critical": len(critical_vulns),
            "high": len(high_vulns),
            "last_scan": vulnerabilities[0].detected_at.isoformat() if vulnerabilities else None
        },
        "auto_scaling_enabled": config.enable_auto_scaling,
        "check_interval_seconds": config.check_interval_seconds
    }


@router.get("/list")
async def list_monitored_applications():
    """List all applications currently being monitored"""
    return {
        "total": len(monitored_apps),
        "applications": [
            {
                "app_name": name,
                "deployment_url": str(config.deployment_url),
                "region": config.region,
                "monitoring_enabled": True
            }
            for name, config in monitored_apps.items()
        ]
    }


@router.delete("/unregister/{app_name}")
async def unregister_application_monitoring(app_name: str):
    """Stop monitoring an application"""
    if app_name not in monitored_apps:
        raise HTTPException(status_code=404, detail=f"Application {app_name} is not being monitored")

    # Clean up
    del monitored_apps[app_name]
    if app_name in health_history:
        del health_history[app_name]
    if app_name in security_findings:
        del security_findings[app_name]
    if app_name in performance_history:
        del performance_history[app_name]

    return {
        "status": "unregistered",
        "app_name": app_name,
        "message": f"Monitoring stopped for {app_name}"
    }
