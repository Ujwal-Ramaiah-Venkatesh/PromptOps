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

        # Detect intent type
        intent_type = "unknown"
        if any(word in command_lower for word in ["deploy", "deployment"]):
            intent_type = "deployment"
        elif any(word in command_lower for word in ["scale", "scaling"]):
            intent_type = "scaling"
        elif any(word in command_lower for word in ["rollback", "revert"]):
            intent_type = "rollback"
        elif any(word in command_lower for word in ["show", "list", "get"]):
            intent_type = "query"

        # Extract service name (look for common app names or "application")
        service = None
        words = command.split()
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

        # Extract parameters
        params = {}
        if "aws" in command_lower:
            params["cloud_provider"] = "aws"
        if "instances" in command_lower:
            for word in words:
                if word.isdigit():
                    params["instance_count"] = int(word)

        return {
            "intent_type": intent_type,
            "target_service": service,
            "target_env": env,
            "parameters": params,
            "confidence": 0.85,
            "ambiguity_score": 0.15,
            "missing_params": [],
            "requires_approval": env == "production",
            "warnings": []
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
