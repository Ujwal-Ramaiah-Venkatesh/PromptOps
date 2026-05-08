"""
Parser API Routes
==================

Natural language command parsing endpoint.

Author: PromptOps Team
Date: 2026-04-30
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import sys
import os

# Add phase1-nlp to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'phase1-nlp'))

router = APIRouter(prefix="/api/v1/parser", tags=["parser"])


# Simple mock parser for demo
class SimpleMockParser:
    """Mock parser for demo mode."""

    def parse(self, command: str) -> Dict[str, Any]:
        """Parse command and return intent."""
        command_lower = command.lower()
        words = command.split()

        # Detect intent type
        intent_type = "unknown"
        confidence = 0.85

        # Discovery/Query intents
        if any(word in command_lower for word in ["find", "search", "discover", "scan"]):
            intent_type = "discovery"
            confidence = 0.90
        elif any(word in command_lower for word in ["show", "list", "get", "view", "display"]):
            intent_type = "query"
            confidence = 0.88
        # Cost/Budget intents
        elif any(word in command_lower for word in ["cost", "spending", "budget", "price"]):
            intent_type = "cost_analysis"
            confidence = 0.92
        # Deployment intents
        elif any(word in command_lower for word in ["deploy", "deployment", "release"]):
            intent_type = "deployment"
            confidence = 0.90
        # Scaling intents
        elif any(word in command_lower for word in ["scale", "scaling", "resize"]):
            intent_type = "scaling"
            confidence = 0.88
        # Rollback intents
        elif any(word in command_lower for word in ["rollback", "revert", "undo"]):
            intent_type = "rollback"
            confidence = 0.90
        # Optimization intents
        elif any(word in command_lower for word in ["optimize", "recommendation", "savings"]):
            intent_type = "optimization"
            confidence = 0.87

        # Extract resource type
        resource_type = None
        if any(word in command_lower for word in ["ec2", "instance", "instances", "vm", "virtual machine"]):
            resource_type = "ec2_instance"
        elif any(word in command_lower for word in ["s3", "bucket", "storage"]):
            resource_type = "s3_bucket"
        elif any(word in command_lower for word in ["rds", "database", "db"]):
            resource_type = "rds_database"
        elif any(word in command_lower for word in ["lambda", "function"]):
            resource_type = "lambda_function"
        elif "eks" in command_lower or "kubernetes" in command_lower:
            resource_type = "eks_cluster"

        # Extract service name (look for common app names or "application")
        service = None
        for i, word in enumerate(words):
            if word.lower() in ["application", "app", "service", "api", "frontend", "backend"]:
                if i > 0:
                    service = words[i-1].lower()
                break

        # Detect environment
        env = "production"
        if any(word in command_lower for word in ["staging", "stage"]):
            env = "staging"
        elif any(word in command_lower for word in ["dev", "development"]):
            env = "development"
        elif any(word in command_lower for word in ["test", "testing"]):
            env = "testing"

        # Extract parameters
        params = {}

        # Cloud provider
        if "aws" in command_lower:
            params["cloud_provider"] = "aws"
        elif "gcp" in command_lower or "google" in command_lower:
            params["cloud_provider"] = "gcp"
        elif "azure" in command_lower:
            params["cloud_provider"] = "azure"

        # Region
        regions = ["us-east-1", "us-west-2", "eu-west-1", "ap-south-1", "us-central1"]
        for region in regions:
            if region in command_lower:
                params["region"] = region
                break

        # Resource type
        if resource_type:
            params["resource_type"] = resource_type

        # Instance count
        if "instances" in command_lower:
            for word in words:
                if word.isdigit():
                    params["instance_count"] = int(word)

        # Status filter
        if "running" in command_lower:
            params["status"] = "running"
        elif "stopped" in command_lower:
            params["status"] = "stopped"
        elif "idle" in command_lower:
            params["status"] = "idle"

        # Determine missing parameters
        missing_params = []
        if intent_type == "discovery" and "region" not in params:
            missing_params.append("region")
        if intent_type == "deployment" and not service:
            missing_params.append("service_name")

        return {
            "intent_type": intent_type,
            "target_service": service,
            "target_env": env,
            "parameters": params,
            "confidence": confidence,
            "ambiguity_score": round(1.0 - confidence, 2),
            "missing_params": missing_params,
            "requires_approval": env == "production" and intent_type in ["deployment", "scaling", "rollback"],
            "warnings": ["This is a mock parser. Full NLP requires Claude API integration."] if intent_type == "unknown" else []
        }


# Initialize parser
parser = SimpleMockParser()


# ============================================================================
# Request/Response Models
# ============================================================================

class ParseRequest(BaseModel):
    """Parse command request."""
    command: str


class ParsedIntent(BaseModel):
    """Parsed intent response."""
    intent_type: str
    target_service: Optional[str] = None
    target_env: Optional[str] = None
    parameters: Dict[str, Any] = {}
    confidence: float
    ambiguity_score: float = 0.0
    missing_params: List[str] = []
    requires_approval: bool = False
    warnings: List[str] = []


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/parse", response_model=ParsedIntent)
async def parse_command(request: ParseRequest):
    """
    Parse natural language command into structured intent.

    **Example request:**
    ```json
    {
        "command": "Deploy Flipkar application on AWS"
    }
    ```

    **Example response:**
    ```json
    {
        "intent_type": "deployment",
        "target_service": "flipkar",
        "target_env": "production",
        "parameters": {
            "cloud_provider": "aws"
        },
        "confidence": 0.85,
        "requires_approval": true
    }
    ```
    """
    if not request.command or not request.command.strip():
        raise HTTPException(status_code=400, detail="Command cannot be empty")

    try:
        # Parse the command
        result = parser.parse(request.command)

        # Extract intent details
        return ParsedIntent(
            intent_type=result.get('intent_type', 'unknown'),
            target_service=result.get('target_service'),
            target_env=result.get('target_env', 'production'),
            parameters=result.get('parameters', {}),
            confidence=result.get('confidence', 0.0),
            ambiguity_score=result.get('ambiguity_score', 0.0),
            missing_params=result.get('missing_params', []),
            requires_approval=result.get('requires_approval', True),
            warnings=result.get('warnings', [])
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse command: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Check parser service health."""
    return {
        "status": "healthy",
        "service": "parser",
        "version": "1.0.0"
    }


# ============================================================================
# FastAPI App (for standalone use)
# ============================================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="PromptOps Parser API",
    version="1.0.0",
    description="Natural language command parsing service"
)

# Enable CORS for local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the router
app.include_router(router)

# Root health check
@app.get("/health")
async def root_health():
    """Root health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "parser": "ok"
        }
    }
