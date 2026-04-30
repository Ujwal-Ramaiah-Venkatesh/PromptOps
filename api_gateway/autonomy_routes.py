"""
Autonomy Settings API Routes
=============================

Manage user autonomy tier preferences.

Week 13-15: ENHANCEMENT-001
Author: PromptOps Team
Date: 2026-04-30
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

from auth.dependencies import get_current_active_user, get_db
from auth.models import User
from database.autonomy_models import AutonomyTier, ActionRiskLevel, AutoExecutedAction
from autonomy.tier_classifier import RiskLevel
from utils.security_logger import get_client_ip

router = APIRouter(prefix="/api/v1/autonomy", tags=["autonomy"])


# ============================================================================
# Pydantic Models
# ============================================================================

class AutonomyTierSetting(BaseModel):
    """Single autonomy tier setting."""
    risk_level: str  # low, medium, high, critical
    behavior: str    # auto_execute, require_approval


class AutonomySettingsResponse(BaseModel):
    """Response with all autonomy settings."""
    user_email: str
    settings: List[AutonomyTierSetting]


class ActionTypeInfo(BaseModel):
    """Information about an action type."""
    action_type: str
    risk_level: str
    description: Optional[str]
    can_override: bool


class AutoExecutionHistoryItem(BaseModel):
    """Single auto-execution history item."""
    operation_id: str
    action_type: str
    risk_level: str
    command: str
    executed_at: datetime
    success: bool
    duration_ms: Optional[int]
    result_summary: Optional[str]


class AutoExecutionStats(BaseModel):
    """Auto-execution statistics."""
    total: int
    successful: int
    failed: int
    success_rate: float
    by_risk_level: Dict[str, int]
    by_action_type: Dict[str, int]


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/settings", response_model=AutonomySettingsResponse)
async def get_autonomy_settings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's autonomy tier settings.

    Returns configured settings or defaults if not configured.

    **Default behavior:** All risk levels require approval (safe mode)

    **Example response:**
    ```json
    {
        "user_email": "pm@promptops.com",
        "settings": [
            {"risk_level": "low", "behavior": "auto_execute"},
            {"risk_level": "medium", "behavior": "require_approval"},
            {"risk_level": "high", "behavior": "require_approval"},
            {"risk_level": "critical", "behavior": "require_approval"}
        ]
    }
    ```
    """
    # Query user's settings
    settings = db.query(AutonomyTier).filter(
        AutonomyTier.user_id == current_user.id
    ).all()

    if not settings:
        # Return defaults (all require approval - safe mode)
        settings_list = [
            AutonomyTierSetting(risk_level="low", behavior="require_approval"),
            AutonomyTierSetting(risk_level="medium", behavior="require_approval"),
            AutonomyTierSetting(risk_level="high", behavior="require_approval"),
            AutonomyTierSetting(risk_level="critical", behavior="require_approval"),
        ]
    else:
        # Convert database models to pydantic models
        settings_list = [
            AutonomyTierSetting(
                risk_level=s.risk_level,
                behavior=s.behavior
            ) for s in settings
        ]

        # Fill in missing risk levels with defaults
        existing_levels = {s.risk_level for s in settings_list}
        for level in ["low", "medium", "high", "critical"]:
            if level not in existing_levels:
                settings_list.append(
                    AutonomyTierSetting(risk_level=level, behavior="require_approval")
                )

    return AutonomySettingsResponse(
        user_email=current_user.email,
        settings=settings_list
    )


@router.post("/settings")
async def update_autonomy_settings(
    settings: List[AutonomyTierSetting],
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update user's autonomy tier settings.

    **Rules:**
    - CRITICAL risk level always requires approval (cannot be changed)
    - Valid risk_levels: low, medium, high, critical
    - Valid behaviors: auto_execute, require_approval

    **Example request:**
    ```json
    [
        {"risk_level": "low", "behavior": "auto_execute"},
        {"risk_level": "medium", "behavior": "auto_execute"},
        {"risk_level": "high", "behavior": "require_approval"},
        {"risk_level": "critical", "behavior": "require_approval"}
    ]
    ```
    """
    # Validate settings
    valid_risk_levels = ["low", "medium", "high", "critical"]
    valid_behaviors = ["auto_execute", "require_approval"]

    for setting in settings:
        if setting.risk_level not in valid_risk_levels:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid risk level: {setting.risk_level}. "
                       f"Must be one of: {', '.join(valid_risk_levels)}"
            )

        if setting.behavior not in valid_behaviors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid behavior: {setting.behavior}. "
                       f"Must be one of: {', '.join(valid_behaviors)}"
            )

        # Enforce: CRITICAL always requires approval (non-negotiable)
        if setting.risk_level == "critical" and setting.behavior != "require_approval":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CRITICAL risk level must always require approval for safety"
            )

    # Update or insert settings
    for setting in settings:
        existing = db.query(AutonomyTier).filter(
            AutonomyTier.user_id == current_user.id,
            AutonomyTier.risk_level == setting.risk_level
        ).first()

        if existing:
            # Update existing setting
            existing.behavior = setting.behavior
            existing.updated_at = datetime.utcnow()
        else:
            # Create new setting
            new_setting = AutonomyTier(
                user_id=current_user.id,
                risk_level=setting.risk_level,
                behavior=setting.behavior
            )
            db.add(new_setting)

    db.commit()

    # Log the settings change
    from utils.security_logger import log_config_change
    log_config_change(
        user=current_user.email,
        config_key="autonomy_settings",
        old_value="(previous settings)",
        new_value=str([s.dict() for s in settings]),
        ip=get_client_ip(request)
    )

    return {
        "message": "Autonomy settings updated successfully",
        "user": current_user.email,
        "settings_count": len(settings)
    }


@router.get("/action-types", response_model=List[ActionTypeInfo])
async def get_action_types(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    risk_level: Optional[str] = None
):
    """
    Get list of action types and their default risk levels.

    Useful for showing PM what each action type means.

    **Query parameters:**
    - risk_level: Optional filter (low, medium, high, critical)

    **Example response:**
    ```json
    [
        {
            "action_type": "restart_pod",
            "risk_level": "low",
            "description": "Restart a Kubernetes pod",
            "can_override": true
        },
        ...
    ]
    ```
    """
    query = db.query(ActionRiskLevel)

    if risk_level:
        if risk_level not in ["low", "medium", "high", "critical"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid risk level: {risk_level}"
            )
        query = query.filter(ActionRiskLevel.default_risk_level == risk_level)

    action_types = query.order_by(
        ActionRiskLevel.default_risk_level,
        ActionRiskLevel.action_type
    ).all()

    return [
        ActionTypeInfo(
            action_type=at.action_type,
            risk_level=at.default_risk_level,
            description=at.description,
            can_override=at.can_be_overridden
        )
        for at in action_types
    ]


@router.get("/history", response_model=List[AutoExecutionHistoryItem])
async def get_auto_execution_history(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = 50,
    action_type: Optional[str] = None
):
    """
    Get user's auto-execution history.

    Shows all actions that were auto-executed without approval.

    **Query parameters:**
    - limit: Max number of records (default: 50, max: 100)
    - action_type: Optional filter by action type

    **Example response:**
    ```json
    [
        {
            "operation_id": "auto-1714492800",
            "action_type": "restart_pod",
            "risk_level": "low",
            "command": "restart pod-frontend-7b8c9d in staging",
            "executed_at": "2026-04-30T10:30:00Z",
            "success": true,
            "duration_ms": 1234,
            "result_summary": "Pod restarted successfully"
        },
        ...
    ]
    ```
    """
    if limit > 100:
        limit = 100

    query = db.query(AutoExecutedAction).filter(
        AutoExecutedAction.user_id == current_user.id
    )

    if action_type:
        query = query.filter(AutoExecutedAction.action_type == action_type)

    actions = query.order_by(
        AutoExecutedAction.executed_at.desc()
    ).limit(limit).all()

    return [
        AutoExecutionHistoryItem(
            operation_id=a.operation_id,
            action_type=a.action_type,
            risk_level=a.risk_level,
            command=a.command,
            executed_at=a.executed_at,
            success=a.success,
            duration_ms=a.duration_ms,
            result_summary=a.result_summary
        )
        for a in actions
    ]


@router.get("/stats", response_model=AutoExecutionStats)
async def get_auto_execution_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get statistics about user's auto-executions.

    **Example response:**
    ```json
    {
        "total": 42,
        "successful": 40,
        "failed": 2,
        "success_rate": 95.2,
        "by_risk_level": {
            "low": 35,
            "medium": 7
        },
        "by_action_type": {
            "restart_pod": 20,
            "clear_cache": 15,
            "scale_up": 7
        }
    }
    ```
    """
    actions = db.query(AutoExecutedAction).filter(
        AutoExecutedAction.user_id == current_user.id
    ).all()

    total = len(actions)
    successful = sum(1 for a in actions if a.success)
    failed = total - successful

    by_risk_level = {}
    by_action_type = {}

    for action in actions:
        # Count by risk level
        risk = action.risk_level
        by_risk_level[risk] = by_risk_level.get(risk, 0) + 1

        # Count by action type
        atype = action.action_type
        by_action_type[atype] = by_action_type.get(atype, 0) + 1

    return AutoExecutionStats(
        total=total,
        successful=successful,
        failed=failed,
        success_rate=(successful / total * 100) if total > 0 else 0,
        by_risk_level=by_risk_level,
        by_action_type=by_action_type
    )


@router.delete("/settings")
async def reset_autonomy_settings(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Reset autonomy settings to defaults (all require approval).

    This is a safe way to return to "manual approval for everything" mode.
    """
    # Delete all user's autonomy settings
    deleted_count = db.query(AutonomyTier).filter(
        AutonomyTier.user_id == current_user.id
    ).delete()

    db.commit()

    # Log the reset
    from utils.security_logger import log_config_change
    log_config_change(
        user=current_user.email,
        config_key="autonomy_settings",
        old_value=f"{deleted_count} custom settings",
        new_value="reset to defaults (all require approval)",
        ip=get_client_ip(request)
    )

    return {
        "message": "Autonomy settings reset to defaults",
        "settings_removed": deleted_count,
        "new_behavior": "All risk levels now require approval"
    }
