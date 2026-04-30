"""
Simplified API Server for PromptOps Demo
This version has minimal dependencies and works standalone
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import uvicorn
import os

# Import auth models and routes
from auth.models import Base
from auth import auth_routes

app = FastAPI(title="PromptOps API Gateway", version="1.0.0")

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/promptops")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ParseIntentRequest(BaseModel):
    command: str
    user: str

class DecomposeRequest(BaseModel):
    intent: dict
    user: str

# Include auth routes
app.include_router(auth_routes.router)

@app.get("/")
async def root():
    return {
        "message": "PromptOps API Gateway",
        "version": "1.0.0",
        "status": "running",
        "mode": "demo"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "parser": "ok",
            "decomposer": "ok",
            "database": "ok (simulated)"
        }
    }

@app.post("/api/v1/parse-intent")
async def parse_intent(request: ParseIntentRequest):
    """Demo intent parsing - returns simulated response"""

    # Simple keyword matching for demo
    command = request.command.lower()

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

        version = "v2.0.0"  # Default
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
        count = 5  # Default
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
async def decompose_task(request: DecomposeRequest):
    """Demo task decomposition - returns simulated response"""

    intent = request.intent
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
async def get_audit_trail(limit: int = 50):
    """Demo audit trail - returns simulated data"""
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
async def get_drift():
    """Demo drift detection - returns simulated data"""
    return {
        "events": [],
        "unacknowledged_count": 0,
        "last_check": "2026-04-30T08:20:00Z"
    }

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  PromptOps API Gateway - Demo Mode")
    print("="*60)
    print("\n  Starting server...")
    print("  API: http://localhost:8000")
    print("  Docs: http://localhost:8000/docs")
    print("\n" + "="*60 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
