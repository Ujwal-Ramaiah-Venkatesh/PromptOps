"""
PromptOps API Gateway
=====================

Unified REST API layer connecting frontend dashboard to backend services.

Provides endpoints for:
- Intent parsing (NLP)
- Task decomposition
- Execution management
- Audit trail
- Drift detection

Author: PromptOps Team - Week 11-12
Date: 2026-04-28
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, status, Form, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4
import sys
import os
import logging

# Configure logging early so import-time warnings are safe
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from phase1-nlp directory
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'phase1-nlp'))
from parser.claude_integration import ClaudeParser
from decomposition.decomposition_engine import DecompositionEngine
from context.context_aware_parser import ContextAwareParser
from context.drift_detector import DriftDetector

# Import routers
try:
    from cicd_routes import router as cicd_router
except Exception as e:
    logger.warning(f"Failed to import cicd_routes: {e}")
    cicd_router = None

try:
    from cloudwatch_routes import router as cloudwatch_router
except Exception as e:
    logger.warning(f"Failed to import cloudwatch_routes: {e}")
    cloudwatch_router = None

try:
    from deployment_routes import router as deployment_router
except Exception as e:
    logger.warning(f"Failed to import deployment_routes: {e}")
    deployment_router = None

try:
    from static_deploy_routes import router as static_deploy_router
except Exception as e:
    logger.warning(f"Failed to import static_deploy_routes: {e}")
    static_deploy_router = None

# ============================================================================
# FastAPI App Initialization
# ============================================================================

app = FastAPI(
    title="PromptOps API",
    description="API Gateway for PromptOps infrastructure management system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ============================================================================
# CORS Configuration
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:3001",  # Alternative port
        "https://dashboard.promptops.com"  # Production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Register Routers
# ============================================================================

if cicd_router:
    app.include_router(cicd_router)
    logger.info("✓ CI/CD router registered at /api/v1/cicd")
else:
    logger.warning("✗ CI/CD router could not be registered")

if deployment_router:
    app.include_router(deployment_router)
    logger.info("✓ Deployment router registered at /api/v1/deployment")
else:
    logger.warning("✗ Deployment router could not be registered")

if static_deploy_router:
    app.include_router(static_deploy_router)
    logger.info("✓ Static deploy router registered at /api/v1/deploy")
else:
    logger.warning("✗ Static deploy router could not be registered")

if cloudwatch_router:
    app.include_router(cloudwatch_router)
    logger.info("✓ CloudWatch observability router registered at /api/v1/monitoring/cloudwatch")
else:
    logger.warning("✗ CloudWatch router could not be registered")

# ============================================================================
# Pydantic Models
# ============================================================================

class ParseIntentRequest(BaseModel):
    command: str = Field(..., min_length=3, max_length=500, description="Natural language command")
    user: EmailStr = Field(..., description="User email address")

    class Config:
        json_schema_extra = {
            "example": {
                "command": "Deploy frontend v2.0 to staging",
                "user": "pm@company.com"
            }
        }


class ParsedIntent(BaseModel):
    intent_type: str
    target_service: str
    target_env: Optional[str] = None
    parameters: Dict[str, Any] = {}
    confidence: float
    ambiguity_score: float
    missing_params: List[str] = []
    requires_approval: bool
    warnings: Optional[List[str]] = None


class ParseIntentResponse(BaseModel):
    intent: ParsedIntent
    parse_time_ms: int


class DecomposeRequest(BaseModel):
    intent: Dict[str, Any]
    user: EmailStr

    class Config:
        json_schema_extra = {
            "example": {
                "intent": {
                    "intent_type": "deploy",
                    "target_service": "frontend",
                    "target_env": "staging",
                    "parameters": {"version": "v2.0"}
                },
                "user": "pm@company.com"
            }
        }


class RiskAssessment(BaseModel):
    overall_risk: str
    risk_factors: List[str]
    estimated_cost_impact: float
    affected_users: int
    requires_approval: bool
    approval_level: str


class Decomposition(BaseModel):
    decomposition_id: str
    operation_id: str
    timestamp: str
    total_sub_tasks: int
    estimated_duration: int
    risk_assessment: RiskAssessment
    original_intent: Dict[str, Any]
    sub_tasks: List[Dict[str, Any]] = []
    rollback_plan: Optional[Dict[str, Any]] = None
    current_state: Optional[Dict[str, Any]] = None
    target_state: Optional[Dict[str, Any]] = None


class DecomposeResponse(BaseModel):
    decomposition: Decomposition
    decompose_time_ms: int


class ExecuteRequest(BaseModel):
    decomposition_id: str
    user: EmailStr
    approved: bool
    approval_phrase: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "decomposition_id": "decomp-abc123",
                "user": "pm@company.com",
                "approved": True,
                "approval_phrase": "APPROVE xyz789"
            }
        }


class ExecuteResponse(BaseModel):
    execution_id: str
    status: str
    started_at: str
    message: str


class ExecutionStatus(BaseModel):
    execution_id: str
    status: str
    completed_tasks: int
    total_tasks: int
    current_task: Optional[str] = None
    logs: List[str] = []
    error_message: Optional[str] = None
    started_at: str
    completed_at: Optional[str] = None


class AuditEntry(BaseModel):
    id: str
    timestamp: str
    user: str
    command: str
    intent_type: str
    target_service: str
    target_env: str
    status: str
    risk_level: str
    duration: Optional[int] = None
    error_message: Optional[str] = None
    task_plan: Optional[Dict[str, Any]] = None
    execution_log: Optional[List[str]] = None


class AuditResponse(BaseModel):
    entries: List[AuditEntry]
    total: int
    page: int
    page_size: int


class DriftEvent(BaseModel):
    id: str
    timestamp: str
    resource_type: str
    resource_id: str
    field: str
    expected_value: Any
    actual_value: Any
    severity: str
    auto_fixable: bool
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[str] = None


class DriftResponse(BaseModel):
    events: List[DriftEvent]
    unacknowledged_count: int
    last_check: str


class DriftActionRequest(BaseModel):
    user: EmailStr


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str
    services: Dict[str, str]


class AuthUser(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: str
    is_active: bool = True


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: AuthUser


# ============================================================================
# Global State (In-memory for now, will move to DB)
# ============================================================================

# Store decompositions
decompositions_store: Dict[str, Dict[str, Any]] = {}

# Store executions
executions_store: Dict[str, Dict[str, Any]] = {}

# Store audit entries
audit_store: List[Dict[str, Any]] = []

# Store drift events
drift_store: List[Dict[str, Any]] = []

# Mock auth users for local dashboard testing
mock_users: Dict[str, Dict[str, Any]] = {
    "admin@promptops.com": {
        "id": "1",
        "email": "admin@promptops.com",
        "full_name": "Admin User",
        "role": "admin",
        "password": "admin123",
        "is_active": True,
    },
    "pm@promptops.com": {
        "id": "2",
        "email": "pm@promptops.com",
        "full_name": "Product Manager",
        "role": "pm",
        "password": "pm123",
        "is_active": True,
    },
}


def _build_mock_token(email: str) -> str:
    return f"mock-token:{email}"


def _get_current_user_from_header(authorization: Optional[str] = Header(default=None)) -> AuthUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token = authorization.split(" ", 1)[1]
    if not token.startswith("mock-token:"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    email = token.replace("mock-token:", "", 1)
    user = mock_users.get(email)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    return AuthUser(**{k: v for k, v in user.items() if k != "password"})

# ============================================================================
# Initialize Backend Services
# ============================================================================

API_KEY = os.getenv("ANTHROPIC_API_KEY")

if not API_KEY:
    logger.warning("ANTHROPIC_API_KEY not set. Some endpoints will fail.")
    parser = None
    decomposer = None
else:
    try:
        parser = ContextAwareParser(api_key=API_KEY)
        decomposer = DecompositionEngine(api_key=API_KEY)
        logger.info("Backend services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize backend services: {e}")
        parser = None
        decomposer = None

# ============================================================================
# Health Check
# ============================================================================

@app.post("/api/v1/auth/login", response_model=LoginResponse, tags=["Auth"])
async def login(username: str = Form(...), password: str = Form(...)):
    """Local mock login used by dashboard manual testing."""
    user = mock_users.get(username)
    if not user or user.get("password") != password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    auth_user = AuthUser(**{k: v for k, v in user.items() if k != "password"})
    return {
        "access_token": _build_mock_token(auth_user.email),
        "token_type": "bearer",
        "user": auth_user,
    }


@app.get("/api/v1/auth/me", response_model=AuthUser, tags=["Auth"])
async def get_current_user(current_user: AuthUser = Depends(_get_current_user_from_header)):
    return current_user


@app.post("/api/v1/auth/logout", tags=["Auth"])
async def logout(current_user: AuthUser = Depends(_get_current_user_from_header)):
    return {"message": f"Logged out {current_user.email}"}

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    services = {
        "parser": "ok" if parser else "unavailable",
        "decomposer": "ok" if decomposer else "unavailable",
        "database": "ok"  # Will check DB connection later
    }

    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "services": services
    }

# ============================================================================
# Intent Parsing
# ============================================================================

@app.post("/api/v1/parse-intent", response_model=ParseIntentResponse, tags=["Intent"])
async def parse_intent(request: ParseIntentRequest):
    """
    Parse natural language command into structured intent.

    Uses context-aware parser for better accuracy.
    """
    if not parser:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Parser service unavailable. Check ANTHROPIC_API_KEY."
        )

    try:
        start_time = datetime.utcnow()

        # Call context-aware parser
        success, intent_dict, message = parser.parse_command_with_context(request.command)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )

        parse_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        logger.info(f"Parsed intent for user {request.user}: {intent_dict['intent_type']}")

        return {
            "intent": intent_dict,
            "parse_time_ms": parse_time
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Parse intent error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse intent: {str(e)}"
        )

# ============================================================================
# Task Decomposition
# ============================================================================

@app.post("/api/v1/decompose", response_model=DecomposeResponse, tags=["Decomposition"])
async def decompose_task(request: DecomposeRequest):
    """
    Decompose parsed intent into executable sub-tasks.

    Returns task plan with risk assessment and rollback plan.
    """
    if not decomposer:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Decomposer service unavailable. Check ANTHROPIC_API_KEY."
        )

    try:
        start_time = datetime.utcnow()

        # Call decomposition engine
        success, decomposition_dict, message = decomposer.decompose(request.intent)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )

        decompose_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        # Store decomposition
        decomp_id = decomposition_dict["decomposition_id"]
        decompositions_store[decomp_id] = {
            **decomposition_dict,
            "user": request.user,
            "created_at": datetime.utcnow().isoformat()
        }

        logger.info(f"Decomposed task for user {request.user}: {decomp_id}")

        return {
            "decomposition": decomposition_dict,
            "decompose_time_ms": decompose_time
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Decompose error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to decompose task: {str(e)}"
        )

# ============================================================================
# Task Execution
# ============================================================================

@app.post("/api/v1/execute", response_model=ExecuteResponse, tags=["Execution"])
async def execute_task(request: ExecuteRequest, background_tasks: BackgroundTasks):
    """
    Execute approved task plan.

    Runs sub-tasks sequentially or in parallel based on dependencies.
    """
    # Get decomposition
    decomposition = decompositions_store.get(request.decomposition_id)

    if not decomposition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Decomposition {request.decomposition_id} not found"
        )

    # Check approval
    if decomposition["risk_assessment"]["requires_approval"] and not request.approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Task requires approval but was not approved"
        )

    # Verify approval phrase (if high-risk)
    if request.approved and decomposition["risk_assessment"]["overall_risk"] in ["high", "critical"]:
        expected_phrase = f"APPROVE {decomposition['operation_id']}"
        if request.approval_phrase != expected_phrase:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Invalid approval phrase. Expected: {expected_phrase}"
            )

    # Create execution
    execution_id = f"exec-{uuid4().hex[:12]}"
    execution = {
        "execution_id": execution_id,
        "decomposition_id": request.decomposition_id,
        "status": "queued",
        "completed_tasks": 0,
        "total_tasks": decomposition["total_sub_tasks"],
        "current_task": None,
        "logs": [],
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        "approved_by": request.user if request.approved else None
    }

    executions_store[execution_id] = execution

    # Add to audit log
    audit_store.append({
        "id": str(uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "user": request.user,
        "command": decomposition.get("original_command", "N/A"),
        "intent_type": decomposition["original_intent"]["intent_type"],
        "target_service": decomposition["original_intent"]["target_service"],
        "target_env": decomposition["original_intent"].get("target_env", "N/A"),
        "status": "executing",
        "risk_level": decomposition["risk_assessment"]["overall_risk"],
        "decomposition_id": request.decomposition_id,
        "execution_id": execution_id
    })

    # Start execution in background
    # background_tasks.add_task(run_execution, execution_id, decomposition)

    logger.info(f"Started execution {execution_id} for user {request.user}")

    return {
        "execution_id": execution_id,
        "status": "queued",
        "started_at": execution["started_at"],
        "message": "Task execution started"
    }

# ============================================================================
# Get Execution Status
# ============================================================================

@app.get("/api/v1/execution/{execution_id}", response_model=ExecutionStatus, tags=["Execution"])
async def get_execution_status(execution_id: str):
    """Get current status of task execution."""
    execution = executions_store.get(execution_id)

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution {execution_id} not found"
        )

    return execution

# ============================================================================
# Audit Trail
# ============================================================================

@app.get("/api/v1/audit", response_model=AuditResponse, tags=["Audit"])
async def get_audit_trail(
    limit: int = 50,
    offset: int = 0,
    user: Optional[str] = None,
    env: Optional[str] = None,
    status: Optional[str] = None
):
    """
    Get audit trail with filtering.

    Supports pagination and filtering by user, environment, status.
    """
    # Filter entries
    filtered = audit_store

    if user:
        filtered = [e for e in filtered if e["user"] == user]
    if env:
        filtered = [e for e in filtered if e.get("target_env") == env]
    if status:
        filtered = [e for e in filtered if e["status"] == status]

    # Sort by timestamp (newest first)
    filtered = sorted(filtered, key=lambda x: x["timestamp"], reverse=True)

    # Paginate
    total = len(filtered)
    entries = filtered[offset:offset + limit]

    return {
        "entries": entries,
        "total": total,
        "page": offset // limit + 1,
        "page_size": limit
    }

# ============================================================================
# Export Audit
# ============================================================================

@app.get("/api/v1/audit/export", tags=["Audit"])
async def export_audit(format: str = "csv"):
    """Export audit trail to CSV or JSON."""
    import csv
    import json
    from io import StringIO

    if format == "csv":
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=["timestamp", "user", "command", "status"])
        writer.writeheader()
        for entry in audit_store:
            writer.writerow({
                "timestamp": entry["timestamp"],
                "user": entry["user"],
                "command": entry.get("command", "N/A"),
                "status": entry["status"]
            })

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=audit-{datetime.utcnow().date()}.csv"}
        )

    elif format == "json":
        return audit_store

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format must be 'csv' or 'json'"
        )

# ============================================================================
# Drift Detection
# ============================================================================

@app.get("/api/v1/drift/recent", response_model=DriftResponse, tags=["Drift"])
async def get_recent_drift():
    """Get recent drift events."""
    # Filter unacknowledged
    unacknowledged = [e for e in drift_store if not e.get("acknowledged_by")]

    return {
        "events": drift_store[-10:],  # Last 10 events
        "unacknowledged_count": len(unacknowledged),
        "last_check": datetime.utcnow().isoformat()
    }


@app.post("/api/v1/drift/{drift_id}/acknowledge", tags=["Drift"])
async def acknowledge_drift(drift_id: str, request: DriftActionRequest):
    """Acknowledge drift event."""
    # Find drift event
    drift = next((e for e in drift_store if e["id"] == drift_id), None)

    if not drift:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drift event {drift_id} not found"
        )

    # Mark as acknowledged
    drift["acknowledged_by"] = request.user
    drift["acknowledged_at"] = datetime.utcnow().isoformat()

    logger.info(f"Drift {drift_id} acknowledged by {request.user}")

    return {"success": True, "message": "Drift event acknowledged"}


@app.post("/api/v1/drift/{drift_id}/revert", tags=["Drift"])
async def revert_drift(drift_id: str, request: DriftActionRequest):
    """Revert drift to expected state."""
    # Find drift event
    drift = next((e for e in drift_store if e["id"] == drift_id), None)

    if not drift:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Drift event {drift_id} not found"
        )

    if not drift.get("auto_fixable"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This drift event is not auto-fixable"
        )

    # TODO: Implement actual revert logic
    # For now, just mark as reverted
    drift["reverted_by"] = request.user
    drift["reverted_at"] = datetime.utcnow().isoformat()

    logger.info(f"Drift {drift_id} reverted by {request.user}")

    return {"success": True, "message": "Drift event reverted"}

# ============================================================================
# Root Endpoint
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """API root endpoint."""
    return {
        "name": "PromptOps API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
