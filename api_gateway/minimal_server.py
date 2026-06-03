"""
Minimal PromptOps API Server - No database, no auth dependencies
Quick start server for demo purposes
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn

app = FastAPI(
    title="PromptOps API Gateway",
    version="1.0.0",
    description="Agentic DevOps Platform - Demo Mode"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3003", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any]

class ParseIntentRequest(BaseModel):
    command: str
    user: str

# Mock users for demo
DEMO_USERS = {
    "admin@promptops.com": {
        "id": "user-1",
        "email": "admin@promptops.com",
        "name": "Admin User",
        "role": "admin",
        "password": "admin123"
    },
    "pm@promptops.com": {
        "id": "user-2",
        "email": "pm@promptops.com",
        "name": "PM User",
        "role": "pm",
        "password": "pm123"
    }
}

@app.get("/")
async def root():
    return {
        "message": "PromptOps API Gateway - Demo Mode",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "mode": "demo"
    }

@app.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Demo login - no real authentication"""
    user = DEMO_USERS.get(request.email)

    if not user or user["password"] != request.password:
        return {
            "access_token": "",
            "token_type": "bearer",
            "user": {}
        }

    return {
        "access_token": f"demo-token-{user['id']}",
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "role": user["role"]
        }
    }

@app.post("/api/v1/parse-intent")
async def parse_intent(request: ParseIntentRequest):
    """Demo intent parsing"""
    command = request.command.lower()

    if "deploy" in command:
        service = "frontend" if "frontend" in command else "backend"
        env = "production" if "prod" in command else "staging"

        return {
            "intent": {
                "intent_type": "deploy",
                "target_service": service,
                "target_env": env,
                "version": "v2.0.0",
                "confidence": 0.95
            }
        }

    elif "scale" in command:
        count = 10 if "10" in command else 5
        service = "backend" if "backend" in command else "frontend"

        return {
            "intent": {
                "intent_type": "scale",
                "target_service": service,
                "target_count": count,
                "confidence": 0.92
            }
        }

    return {
        "intent": {
            "intent_type": "unknown",
            "confidence": 0.45,
            "original_command": request.command
        }
    }

@app.get("/api/v1/audit")
async def get_audit_trail():
    """Demo audit trail"""
    return {
        "entries": [
            {
                "id": "audit-1",
                "timestamp": "2026-06-02T08:15:23Z",
                "user": "admin@promptops.com",
                "command": "Deploy frontend v2.0 to staging",
                "status": "completed"
            }
        ]
    }

@app.get("/api/v1/drift/recent")
async def get_drift():
    """Demo drift detection"""
    return {
        "events": [],
        "unacknowledged_count": 0
    }

# Autonomy Settings Routes
@app.get("/api/v1/autonomy/settings")
async def get_autonomy_settings():
    """Get autonomy settings"""
    return {
        "user_id": "user-1",
        "auto_execute_low": True,
        "auto_execute_medium": False,
        "auto_execute_high": False,
        "auto_execute_critical": False
    }

@app.put("/api/v1/autonomy/settings")
async def update_autonomy_settings(settings: Dict[str, Any]):
    """Update autonomy settings"""
    return {"success": True, **settings}

# Discovery Routes
@app.post("/api/v1/discovery/scan")
async def scan_resources(scan_request: Dict[str, Any]):
    """Scan AWS resources"""
    return {
        "scan_id": "scan-demo-123",
        "resources_found": 15,
        "status": "completed"
    }

@app.get("/api/v1/discovery/resources")
async def get_discovered_resources():
    """Get discovered resources"""
    return {
        "resources": [
            {
                "id": "i-1234567890",
                "type": "EC2",
                "name": "web-server-1",
                "region": "us-east-1"
            }
        ]
    }

# Ingestion Routes
@app.post("/api/v1/ingestion/import")
async def import_resource(import_request: Dict[str, Any]):
    """Import AWS resource to Terraform"""
    return {
        "import_id": "import-demo-456",
        "status": "completed",
        "terraform_generated": True
    }

if __name__ == "__main__":
    print("\n" + "="*70)
    print("  PromptOps API Gateway - Demo Mode")
    print("="*70)
    print("\n  Server starting...")
    print("  - API:  http://localhost:8000")
    print("  - Docs: http://localhost:8000/docs")
    print("\n  Demo Login Credentials:")
    print("  - Admin: admin@promptops.com / admin123")
    print("  - PM:    pm@promptops.com / pm123")
    print("\n" + "="*70 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
