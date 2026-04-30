"""
Start API Gateway with mock database for testing authentication
This bypasses the need for PostgreSQL during initial testing
"""

import sys
import os

# Add parent directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uvicorn
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock database - in-memory user storage
MOCK_USERS = {}

class MockDB:
    """Mock database session"""
    def __init__(self):
        self.filter_email = None

    def query(self, model):
        return MockQuery(model, self)

    def add(self, obj):
        if hasattr(obj, 'email'):
            MOCK_USERS[obj.email] = obj

    def commit(self):
        pass

    def refresh(self, obj):
        pass

    def close(self):
        pass

class MockQuery:
    def __init__(self, model, db):
        self.model = model
        self.db = db
        self._filter_email = None

    def filter(self, *args, **kwargs):
        # Extract email from filter arguments
        # The filter is typically User.email == "some@email.com"
        # We need to extract "some@email.com"
        for arg in args:
            if hasattr(arg, 'right'):
                if hasattr(arg.right, 'value'):
                    self._filter_email = arg.right.value
        self.db.filter_email = self._filter_email
        return self

    def first(self):
        # Return user if filter email was set
        if self.db.filter_email and self.db.filter_email in MOCK_USERS:
            return MOCK_USERS[self.db.filter_email]
        return None

    def all(self):
        return list(MOCK_USERS.values())

def get_mock_db():
    """Get mock database session"""
    db = MockDB()
    try:
        yield db
    finally:
        db.close()

# Import models before overriding dependencies
from auth.models import User
from auth.jwt import get_password_hash
from auth.permissions import require_environment_access, check_environment_access

# Import secrets manager (SECURITY-005)
from utils.secrets import get_secrets_manager

# Import security logging (SECURITY-006)
from utils.security_logger import (
    log_deployment, log_scaling_operation, log_environment_access_denied,
    log_permission_denied, log_rate_limit_exceeded, get_client_ip
)

# Import mock auth dependency (doesn't need database)
from mock_auth_dependency import get_current_active_user_mock, MOCK_USERS as MOCK_USERS_IMPORT

# Override auth dependencies to use mock DB
import auth.dependencies
auth.dependencies.get_db = get_mock_db

# Import auth routes module from parent directory
import auth_routes

app = FastAPI(title="PromptOps API Gateway (Mock DB)", version="1.0.0")

# Initialize Secrets Manager - SECURITY-005
secrets_manager = get_secrets_manager()
logger.info(f"Secrets Manager initialized for environment: {os.getenv('ENVIRONMENT', 'development')}")

# Rate Limiting Configuration - SECURITY-004
# Prevents brute force attacks and API abuse
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# Custom rate limit handler with logging
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler that logs rate limit violations"""
    log_rate_limit_exceeded(
        endpoint=request.url.path,
        ip=get_client_ip(request),
        limit=str(exc.detail)
    )
    return _rate_limit_exceeded_handler(request, exc)

app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)

# CORS Configuration - Environment-specific
# SECURITY-003: Restrict CORS to specific domains
# SECURITY-005: Load from secrets manager
ALLOWED_ORIGINS = secrets_manager.get_cors_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Specific domains only (no wildcard)
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Specific methods
    allow_headers=["Authorization", "Content-Type", "Accept"],  # Specific headers
    max_age=600  # Cache preflight requests for 10 minutes
)

# Initialize mock users (shared with mock_auth_dependency)
admin_user = User(
    id='admin-default-001',
    email='admin@promptops.com',
    hashed_password='$2b$12$FWb9Kpi4TQoC.78ba2XDY.n50JU2QOxcHJmLqh4.tLfEvycx5K1rO',
    full_name='System Administrator',
    role='admin',
    is_active=True
)
MOCK_USERS['admin@promptops.com'] = admin_user
MOCK_USERS_IMPORT['admin@promptops.com'] = admin_user

pm_user = User(
    id='pm-test-001',
    email='pm@promptops.com',
    hashed_password='$2b$12$WHS87d2rbQe/krsZaFGj4ucGPF2E7egbwXh53SmvM4SFtT6rMtpjq',
    full_name='Product Manager',
    role='pm',
    is_active=True
)
MOCK_USERS['pm@promptops.com'] = pm_user
MOCK_USERS_IMPORT['pm@promptops.com'] = pm_user

class ParseIntentRequest(BaseModel):
    command: str
    user: str

class DecomposeRequest(BaseModel):
    intent: dict
    user: str

class ExecuteRequest(BaseModel):
    decomposition_id: str
    target_env: str
    user: str

class ScaleRequest(BaseModel):
    service: str
    desired_count: int
    environment: str

# Include auth routes
app.include_router(auth_routes.router)

# Include autonomy routes (ENHANCEMENT-001)
import autonomy_routes
app.include_router(autonomy_routes.router)

# Include ingestion routes (ENHANCEMENT-002)
import ingestion_routes
app.include_router(ingestion_routes.router)

# Include discovery routes (ENHANCEMENT-003)
import discovery_routes
app.include_router(discovery_routes.router)

@app.get("/")
@limiter.limit("100/minute")
async def root(request: Request):
    return {
        "message": "PromptOps API Gateway",
        "version": "1.0.0",
        "status": "running",
        "mode": "mock-db",
        "auth": "enabled",
        "rate_limiting": "enabled"
    }

@app.get("/health")
@limiter.limit("100/minute")
async def health_check(request: Request):
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "parser": "ok",
            "decomposer": "ok",
            "database": "mock (in-memory)",
            "authentication": "enabled",
            "rate_limiting": "enabled"
        },
        "test_users": [
            {"email": "admin@promptops.com", "password": "admin123", "role": "admin"},
            {"email": "pm@promptops.com", "password": "pm123", "role": "pm"}
        ]
    }

@app.post("/api/v1/parse-intent")
@limiter.limit("100/minute")
async def parse_intent(
    request: Request,
    parse_request: ParseIntentRequest,
    current_user: User = Depends(get_current_active_user_mock)
):
    """
    Parse natural language command into structured intent

    **Rate Limit**: 100 requests per minute per IP

    Requires: Valid JWT token (any authenticated user)
    """
    command = parse_request.command.lower()

    if "deploy" in command:
        intent_type = "deploy"
        if "frontend" in command:
            service = "frontend"
        elif "api" in command or "backend" in command:
            service = "api"
        else:
            service = "unknown"

        if "staging" in command:
            env = "staging"
        elif "production" in command or "prod" in command:
            env = "production"
        else:
            env = "staging"

        version = "v2.0.0"
        if "v2.1" in command:
            version = "v2.1.0"
        elif "v3" in command:
            version = "v3.0.0"

        return {
            "intent": {
                "intent_type": intent_type,
                "target_service": service,
                "target_env": env,
                "version": version,
                "confidence": 0.95,
                "parameters": {
                    "service": service,
                    "environment": env,
                    "version": version
                },
                "missing_params": [],
                "context_used": {}
            },
            "parse_time_ms": 342
        }

    elif "scale" in command:
        count = 5
        if "10" in command:
            count = 10
        elif "3" in command:
            count = 3

        if "backend" in command:
            service = "backend"
        elif "frontend" in command:
            service = "frontend"
        else:
            service = "backend"

        return {
            "intent": {
                "intent_type": "scale",
                "target_service": service,
                "target_count": count,
                "confidence": 0.92,
                "parameters": {
                    "service": service,
                    "desired_count": count
                },
                "missing_params": []
            },
            "parse_time_ms": 298
        }

    else:
        return {
            "intent": {
                "intent_type": "unknown",
                "confidence": 0.45,
                "original_command": request.command,
                "missing_params": ["action", "target"]
            },
            "parse_time_ms": 156
        }

@app.post("/api/v1/decompose")
@limiter.limit("100/minute")
async def decompose_task(
    request: Request,
    decompose_request: DecomposeRequest,
    current_user: User = Depends(get_current_active_user_mock)
):
    """
    Decompose parsed intent into executable sub-tasks

    **Rate Limit**: 100 requests per minute per IP

    Requires: Valid JWT token (any authenticated user)
    """
    intent = decompose_request.intent
    intent_type = intent.get("intent_type", "unknown")

    if intent_type == "deploy":
        service = intent.get("target_service", "frontend")
        env = intent.get("target_env", "staging")
        version = intent.get("version", "v2.0.0")

        risk = "high" if env == "production" else "medium"
        requires_approval = env == "production"

        return {
            "decomposition": {
                "decomposition_id": "decomp-abc123",
                "operation_id": "op-xyz789",
                "total_sub_tasks": 6,
                "estimated_duration": 420,
                "risk_assessment": {
                    "overall_risk": risk,
                    "requires_approval": requires_approval,
                    "approval_level": "manager" if requires_approval else None
                },
                "sub_tasks": [
                    {
                        "task_id": "task-1",
                        "description": f"Validate {service} {version} exists in artifact registry",
                        "estimated_time": 10
                    },
                    {
                        "task_id": "task-2",
                        "description": f"Create backup of {env} environment",
                        "estimated_time": 30
                    },
                    {
                        "task_id": "task-3",
                        "description": f"Update {service} task definition to {version}",
                        "estimated_time": 20
                    },
                    {
                        "task_id": "task-4",
                        "description": f"Deploy to {env} ECS cluster",
                        "estimated_time": 120
                    },
                    {
                        "task_id": "task-5",
                        "description": "Wait for healthy status and run smoke tests",
                        "estimated_time": 180
                    },
                    {
                        "task_id": "task-6",
                        "description": "Update audit log and notify team",
                        "estimated_time": 60
                    }
                ]
            },
            "decompose_time_ms": 1456
        }

    elif intent_type == "scale":
        service = intent.get("target_service", "backend")
        count = intent.get("target_count", 5)

        return {
            "decomposition": {
                "decomposition_id": "decomp-def456",
                "operation_id": "op-abc123",
                "total_sub_tasks": 4,
                "estimated_duration": 180,
                "risk_assessment": {
                    "overall_risk": "low",
                    "requires_approval": False
                },
                "sub_tasks": [
                    {
                        "task_id": "task-1",
                        "description": f"Get current {service} instance count",
                        "estimated_time": 10
                    },
                    {
                        "task_id": "task-2",
                        "description": f"Update ECS service desired count to {count}",
                        "estimated_time": 20
                    },
                    {
                        "task_id": "task-3",
                        "description": "Wait for new instances to become healthy",
                        "estimated_time": 120
                    },
                    {
                        "task_id": "task-4",
                        "description": "Verify all instances running and healthy",
                        "estimated_time": 30
                    }
                ]
            },
            "decompose_time_ms": 892
        }

    return {
        "decomposition": {
            "decomposition_id": "decomp-unknown",
            "total_sub_tasks": 0,
            "error": "Unable to decompose unknown intent type"
        }
    }

@app.get("/api/v1/audit")
@limiter.limit("60/minute")
async def get_audit_trail(
    request: Request,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user_mock)
):
    """
    Get audit trail of all operations

    **Rate Limit**: 60 requests per minute per IP

    Requires: Valid JWT token (all roles can view)
    """
    return {
        "entries": [
            {
                "id": "audit-1",
                "timestamp": "2026-04-30T08:15:23Z",
                "user": "sarah.chen@company.com",
                "command": "Deploy frontend v2.0 to staging",
                "status": "completed",
                "target_env": "staging",
                "duration_seconds": 142
            },
            {
                "id": "audit-2",
                "timestamp": "2026-04-30T07:42:11Z",
                "user": "mike.johnson@company.com",
                "command": "Scale backend to 10 instances",
                "status": "completed",
                "target_env": "production",
                "duration_seconds": 98
            }
        ],
        "total": 2,
        "page": 1
    }

@app.get("/api/v1/drift/recent")
@limiter.limit("60/minute")
async def get_drift(
    request: Request,
    current_user: User = Depends(get_current_active_user_mock)
):
    """
    Get recent drift detection events

    **Rate Limit**: 60 requests per minute per IP

    Requires: Valid JWT token (all roles can view)
    """
    return {
        "events": [],
        "unacknowledged_count": 0,
        "last_check": "2026-04-30T08:20:00Z"
    }

@app.post("/api/v1/execute")
@limiter.limit("20/minute")
async def execute_deployment(
    request: Request,
    execute_request: ExecuteRequest,
    current_user: User = Depends(get_current_active_user_mock)
):
    """
    Execute deployment or operation

    **Rate Limit**: 20 requests per minute per IP (production operations are rate-limited)

    Requires:
    - Authenticated user
    - Appropriate role for target environment:
      - staging: pm, engineer, lead, admin
      - production: engineer, lead, admin
    """
    # Check environment access
    try:
        check_environment_access(execute_request.target_env, current_user)
    except HTTPException as e:
        # Log environment access denial
        log_environment_access_denied(
            current_user.email,
            current_user.role,
            execute_request.target_env,
            get_client_ip(request)
        )
        raise

    # Log deployment
    execution_id = "exec-demo-123"
    log_deployment(
        user=current_user.email,
        role=current_user.role,
        service="application",  # In real implementation, extract from decomposition
        environment=execute_request.target_env,
        version="latest",
        deployment_id=execution_id,
        ip=get_client_ip(request)
    )

    # Simulate execution
    return {
        "execution_id": execution_id,
        "decomposition_id": execute_request.decomposition_id,
        "status": "running",
        "message": f"Execution started by {current_user.email} in {execute_request.target_env}",
        "user_role": current_user.role,
        "environment": execute_request.target_env,
        "started_at": "2026-04-30T09:30:00Z"
    }

@app.post("/api/v1/scale")
@limiter.limit("30/minute")
async def scale_service(
    request: Request,
    scale_request: ScaleRequest,
    current_user: User = Depends(get_current_active_user_mock)
):
    """
    Scale service instances

    **Rate Limit**: 30 requests per minute per IP

    Requires:
    - pm, engineer, lead, or admin role
    - Cannot scale production if viewer role
    """
    # Check environment access
    try:
        check_environment_access(scale_request.environment, current_user)
    except HTTPException as e:
        # Log access denial
        log_environment_access_denied(
            current_user.email,
            current_user.role,
            scale_request.environment,
            get_client_ip(request)
        )
        raise

    # PMs and above can scale
    if current_user.role == "viewer":
        log_permission_denied(
            user=current_user.email,
            resource="/api/v1/scale",
            action="scale_service",
            reason="viewer_role",
            ip=get_client_ip(request)
        )
        raise HTTPException(
            status_code=403,
            detail="Viewers cannot scale services"
        )

    # Log scaling operation
    previous_count = 3  # In real implementation, get from current state
    log_scaling_operation(
        user=current_user.email,
        service=scale_request.service,
        environment=scale_request.environment,
        from_count=previous_count,
        to_count=scale_request.desired_count,
        ip=get_client_ip(request)
    )

    return {
        "message": f"Scaling {scale_request.service} to {scale_request.desired_count} instances in {scale_request.environment}",
        "service": scale_request.service,
        "previous_count": previous_count,
        "desired_count": scale_request.desired_count,
        "environment": scale_request.environment,
        "initiated_by": current_user.email,
        "status": "in_progress"
    }

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  PromptOps API Gateway with Authentication")
    print("  Database: In-Memory Mock")
    print("="*60)
    print("\n  Test Users:")
    print("    Admin: admin@promptops.com / admin123")
    print("    PM:    pm@promptops.com / pm123")
    print("\n  Starting server...")
    print("  API: http://localhost:8000")
    print("  Docs: http://localhost:8000/docs")
    print("\n  Authentication endpoints:")
    print("    POST /api/v1/auth/register")
    print("    POST /api/v1/auth/login")
    print("    GET  /api/v1/auth/me")
    print("    GET  /api/v1/auth/users")
    print("\n" + "="*60 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
