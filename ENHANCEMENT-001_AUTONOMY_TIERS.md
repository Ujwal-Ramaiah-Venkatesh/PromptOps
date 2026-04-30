# ENHANCEMENT-001: Autonomy Tier System

**Priority:** HIGH (Behind Schedule)  
**Status:** 🔴 Not Started  
**Allocated:** 40 hours (1 week)  
**Timeline:** Week 13-15 (Current Sprint)  
**Phase:** Phase 1 Q2 (per blueprint)

---

## Overview

Implement configurable autonomy tiers to prevent PM "alert fatigue" while maintaining safety for high-risk operations. PMs can pre-authorize specific low-risk action categories to auto-execute without approval.

**Problem Solved:** In Phase 3 SRE, generating too many approval requests causes PMs to auto-approve without reading, defeating the safety mechanism.

**Solution:** Tiered system where PMs configure which risk levels require approval vs. auto-execute.

---

## Requirements

### Functional Requirements

1. **Risk Classification System:**
   - Classify every operation as LOW, MEDIUM, HIGH, or CRITICAL risk
   - Default risk levels for common operations
   - Configurable risk levels per action type

2. **Autonomy Configuration:**
   - Per-user autonomy settings
   - Configure behavior per risk level (auto-execute vs. require-approval)
   - Default: All require approval (safe mode)

3. **Auto-Execution Logic:**
   - Bypass approval workflow for auto-execute actions
   - Still log all auto-executed actions
   - Show PM post-facto notification

4. **Safety Guardrails:**
   - CRITICAL actions always require approval (non-configurable)
   - Production deployments always require approval
   - Database schema changes always require approval

### Non-Functional Requirements

1. **Security:** Audit all auto-executed actions
2. **Performance:** <50ms overhead for autonomy check
3. **Reliability:** Fail-safe (if autonomy check fails, require approval)
4. **Usability:** Clear defaults, easy to understand

---

## Architecture

### System Flow

```
┌─────────────────────────────────────────────────────┐
│ 1. PM Issues Command                                │
│    "Restart pod-frontend-7b8c9d in staging"         │
└───────────────────┬─────────────────────────────────┘
                    │
                    ↓
┌─────────────────────────────────────────────────────┐
│ 2. Intent Parser (Claude Sonnet 4)                  │
│    • Intent: restart_pod                            │
│    • Resource: pod-frontend-7b8c9d                  │
│    • Environment: staging                           │
└───────────────────┬─────────────────────────────────┘
                    │
                    ↓
┌─────────────────────────────────────────────────────┐
│ 3. Risk Classifier (NEW)                            │
│    • Action: restart_pod                            │
│    • Environment: staging                           │
│    • Risk Level: LOW                                │
└───────────────────┬─────────────────────────────────┘
                    │
                    ↓
┌─────────────────────────────────────────────────────┐
│ 4. Autonomy Check (NEW)                             │
│    • User: pm@promptops.com                         │
│    • Risk Level: LOW                                │
│    • User Setting for LOW: auto_execute             │
│    • Decision: AUTO-EXECUTE ✓                       │
└───────────────────┬─────────────────────────────────┘
                    │
                    ↓
┌─────────────────────────────────────────────────────┐
│ 5a. If Auto-Execute:                                │
│     • Execute immediately                           │
│     • Log action (security_logger)                  │
│     • Show notification to PM (post-facto)          │
│                                                     │
│ 5b. If Require Approval:                            │
│     • Show approval card to PM                      │
│     • Wait for approval                             │
│     • Execute after approval                        │
└─────────────────────────────────────────────────────┘
```

---

## Implementation Tasks

### Task 1: Database Schema (4 hours)

**File:** `database/migrations/007_add_autonomy_tables.sql`

```sql
-- Autonomy tier configuration per user
CREATE TABLE autonomy_tiers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    risk_level VARCHAR(20) NOT NULL CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    behavior VARCHAR(30) NOT NULL CHECK (behavior IN ('auto_execute', 'require_approval')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, risk_level)
);

-- Create index for fast lookups
CREATE INDEX idx_autonomy_tiers_user_risk ON autonomy_tiers(user_id, risk_level);

-- Action type definitions with default risk levels
CREATE TABLE action_risk_levels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action_type VARCHAR(100) NOT NULL UNIQUE,
    default_risk_level VARCHAR(20) NOT NULL CHECK (default_risk_level IN ('low', 'medium', 'high', 'critical')),
    description TEXT,
    can_be_overridden BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Pre-populate with default action risk levels
INSERT INTO action_risk_levels (action_type, default_risk_level, description, can_be_overridden) VALUES
-- LOW RISK
('restart_pod', 'low', 'Restart a Kubernetes pod', TRUE),
('clear_cache', 'low', 'Clear application cache', TRUE),
('disk_cleanup_small', 'low', 'Cleanup disk space under 10GB', TRUE),
('log_rotation', 'low', 'Rotate application logs', TRUE),
('staging_deploy', 'low', 'Deploy to staging environment', TRUE),
('read_only_query', 'low', 'Execute read-only database query', TRUE),

-- MEDIUM RISK
('scale_up', 'medium', 'Scale up instances', TRUE),
('scale_down', 'medium', 'Scale down instances', TRUE),
('staging_rollback', 'medium', 'Rollback staging deployment', TRUE),
('config_change_dev', 'medium', 'Change configuration in dev/staging', TRUE),

-- HIGH RISK
('production_deploy', 'high', 'Deploy to production environment', FALSE),
('database_migration', 'high', 'Run database migration', FALSE),
('scale_down_prod', 'high', 'Scale down production instances', TRUE),

-- CRITICAL RISK (Always require approval)
('database_schema_change', 'critical', 'Modify database schema', FALSE),
('delete_data', 'critical', 'Delete production data', FALSE),
('iam_policy_change', 'critical', 'Modify IAM policies', FALSE),
('security_group_change', 'critical', 'Modify security groups', FALSE),
('production_rollback', 'critical', 'Rollback production deployment', FALSE);

-- Track auto-executed actions (audit trail)
CREATE TABLE auto_executed_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    operation_id VARCHAR(50) NOT NULL,
    action_type VARCHAR(100) NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    command TEXT NOT NULL,
    executed_at TIMESTAMP DEFAULT NOW(),
    duration_ms INTEGER,
    success BOOLEAN,
    result_summary TEXT
);

CREATE INDEX idx_auto_executed_user ON auto_executed_actions(user_id, executed_at DESC);
CREATE INDEX idx_auto_executed_operation ON auto_executed_actions(operation_id);
```

**Deliverable:**
- SQL migration file
- Apply to database
- Verify with test queries

---

### Task 2: Risk Classifier Module (8 hours)

**File:** `api_gateway/autonomy/tier_classifier.py`

```python
"""
Autonomy Tier Classifier
========================

Classifies operations by risk level for autonomy tier system.

Author: PromptOps Team - Week 13-15
"""

from enum import Enum
from typing import Dict, Optional
from dataclasses import dataclass


class RiskLevel(Enum):
    """Risk levels for operations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskAssessment:
    """Risk assessment result."""
    risk_level: RiskLevel
    action_type: str
    reason: str
    can_auto_execute: bool
    factors: Dict[str, str]


class TierClassifier:
    """
    Classifies operations by risk level.
    
    Considers:
    - Action type (restart vs. delete)
    - Environment (staging vs. production)
    - Resource type (pod vs. database)
    - Data sensitivity (logs vs. user data)
    """
    
    def __init__(self, db_session):
        self.db = db_session
        self._load_risk_levels()
    
    def _load_risk_levels(self):
        """Load action risk levels from database."""
        # Query action_risk_levels table
        # Cache in memory for performance
        pass
    
    def classify(self, intent: Dict) -> RiskAssessment:
        """
        Classify an operation's risk level.
        
        Args:
            intent: Parsed intent from NLP engine
            
        Returns:
            RiskAssessment with risk level and reasoning
        """
        action_type = intent.get("intent_type")
        environment = intent.get("target_env", "unknown")
        resource_type = intent.get("resource_type", "unknown")
        
        # Get base risk level from action type
        base_risk = self._get_base_risk(action_type)
        
        # Adjust risk based on environment
        adjusted_risk = self._adjust_for_environment(base_risk, environment)
        
        # Adjust risk based on resource type
        final_risk = self._adjust_for_resource(adjusted_risk, resource_type)
        
        # Build reasoning
        factors = {
            "action": action_type,
            "environment": environment,
            "resource": resource_type,
            "base_risk": base_risk.value,
            "final_risk": final_risk.value
        }
        
        reason = self._build_reason(factors)
        
        # CRITICAL actions can never auto-execute
        can_auto_execute = final_risk != RiskLevel.CRITICAL
        
        return RiskAssessment(
            risk_level=final_risk,
            action_type=action_type,
            reason=reason,
            can_auto_execute=can_auto_execute,
            factors=factors
        )
    
    def _get_base_risk(self, action_type: str) -> RiskLevel:
        """Get base risk level for action type from database."""
        # Query database or use defaults
        defaults = {
            "deploy": RiskLevel.HIGH,
            "restart_pod": RiskLevel.LOW,
            "scale": RiskLevel.MEDIUM,
            "rollback": RiskLevel.HIGH,
            "delete": RiskLevel.CRITICAL,
            "schema_change": RiskLevel.CRITICAL,
        }
        return defaults.get(action_type, RiskLevel.MEDIUM)
    
    def _adjust_for_environment(self, base_risk: RiskLevel, env: str) -> RiskLevel:
        """Increase risk for production environments."""
        if env == "production":
            # Bump up risk level for production
            if base_risk == RiskLevel.LOW:
                return RiskLevel.MEDIUM
            elif base_risk == RiskLevel.MEDIUM:
                return RiskLevel.HIGH
        return base_risk
    
    def _adjust_for_resource(self, risk: RiskLevel, resource: str) -> RiskLevel:
        """Adjust risk based on resource type."""
        critical_resources = ["database", "iam", "security_group"]
        if any(cr in resource.lower() for cr in critical_resources):
            return RiskLevel.CRITICAL
        return risk
    
    def _build_reason(self, factors: Dict) -> str:
        """Build human-readable reasoning."""
        return (f"Action '{factors['action']}' in '{factors['environment']}' "
                f"classified as {factors['final_risk'].upper()} risk")
```

**Deliverable:**
- TierClassifier class
- Risk classification logic
- Unit tests

---

### Task 3: Autonomy Settings API (8 hours)

**File:** `api_gateway/autonomy_routes.py`

```python
"""
Autonomy Settings API Routes
=============================

Manage user autonomy tier preferences.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict
from auth.dependencies import get_current_active_user, get_db
from auth.models import User
from autonomy.tier_classifier import RiskLevel

router = APIRouter(prefix="/api/v1/autonomy", tags=["autonomy"])


class AutonomyTierSetting(BaseModel):
    risk_level: str  # low, medium, high, critical
    behavior: str    # auto_execute, require_approval


class AutonomySettingsResponse(BaseModel):
    user_email: str
    settings: List[AutonomyTierSetting]
    

@router.get("/settings", response_model=AutonomySettingsResponse)
async def get_autonomy_settings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's autonomy tier settings.
    
    Returns configured settings or defaults if not configured.
    """
    # Query autonomy_tiers table
    settings = db.query(AutonomyTier).filter(
        AutonomyTier.user_id == current_user.id
    ).all()
    
    if not settings:
        # Return defaults (all require approval)
        settings = [
            AutonomyTierSetting(risk_level="low", behavior="require_approval"),
            AutonomyTierSetting(risk_level="medium", behavior="require_approval"),
            AutonomyTierSetting(risk_level="high", behavior="require_approval"),
            AutonomyTierSetting(risk_level="critical", behavior="require_approval"),
        ]
    else:
        settings = [
            AutonomyTierSetting(
                risk_level=s.risk_level,
                behavior=s.behavior
            ) for s in settings
        ]
    
    return AutonomySettingsResponse(
        user_email=current_user.email,
        settings=settings
    )


@router.post("/settings")
async def update_autonomy_settings(
    settings: List[AutonomyTierSetting],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update user's autonomy tier settings.
    
    Note: CRITICAL risk level always requires approval (cannot be changed).
    """
    # Validate settings
    for setting in settings:
        if setting.risk_level not in ["low", "medium", "high", "critical"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid risk level: {setting.risk_level}"
            )
        
        if setting.behavior not in ["auto_execute", "require_approval"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid behavior: {setting.behavior}"
            )
        
        # Enforce: CRITICAL always requires approval
        if setting.risk_level == "critical" and setting.behavior != "require_approval":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CRITICAL risk level must always require approval"
            )
    
    # Update or insert settings
    for setting in settings:
        existing = db.query(AutonomyTier).filter(
            AutonomyTier.user_id == current_user.id,
            AutonomyTier.risk_level == setting.risk_level
        ).first()
        
        if existing:
            existing.behavior = setting.behavior
            existing.updated_at = datetime.utcnow()
        else:
            new_setting = AutonomyTier(
                user_id=current_user.id,
                risk_level=setting.risk_level,
                behavior=setting.behavior
            )
            db.add(new_setting)
    
    db.commit()
    
    return {"message": "Autonomy settings updated successfully"}


@router.get("/action-types")
async def get_action_types(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get list of action types and their default risk levels.
    
    Useful for showing PM what each action type means.
    """
    action_types = db.query(ActionRiskLevel).all()
    
    return {
        "action_types": [
            {
                "action": at.action_type,
                "risk_level": at.default_risk_level,
                "description": at.description,
                "can_override": at.can_be_overridden
            }
            for at in action_types
        ]
    }
```

**Deliverable:**
- API routes (GET/POST /api/v1/autonomy/settings)
- Request/response models
- Validation logic
- Integration tests

---

### Task 4: Auto-Execute Logic (12 hours)

**File:** `api_gateway/autonomy/auto_executor.py`

```python
"""
Auto-Executor
=============

Handles auto-execution of pre-authorized operations.
"""

from typing import Dict, Optional
from autonomy.tier_classifier import TierClassifier, RiskAssessment
from utils.security_logger import log_auto_execution
import logging

logger = logging.getLogger(__name__)


class AutoExecutor:
    """
    Determines if an operation should auto-execute or require approval.
    """
    
    def __init__(self, db_session):
        self.db = db_session
        self.classifier = TierClassifier(db_session)
    
    def should_auto_execute(self, user, intent: Dict) -> tuple[bool, RiskAssessment]:
        """
        Determine if operation should auto-execute.
        
        Returns:
            (should_execute: bool, risk_assessment: RiskAssessment)
        """
        # Classify risk level
        risk_assessment = self.classifier.classify(intent)
        
        # CRITICAL actions NEVER auto-execute
        if risk_assessment.risk_level.value == "critical":
            return False, risk_assessment
        
        # Get user's autonomy setting for this risk level
        user_setting = self._get_user_setting(user.id, risk_assessment.risk_level.value)
        
        # Check if user has auto_execute enabled for this risk level
        should_execute = (user_setting == "auto_execute")
        
        return should_execute, risk_assessment
    
    def _get_user_setting(self, user_id: str, risk_level: str) -> str:
        """
        Get user's autonomy setting for a risk level.
        
        Returns: 'auto_execute' or 'require_approval'
        Default: 'require_approval' (safe)
        """
        setting = self.db.query(AutonomyTier).filter(
            AutonomyTier.user_id == user_id,
            AutonomyTier.risk_level == risk_level
        ).first()
        
        if setting:
            return setting.behavior
        
        # Default: require approval (fail-safe)
        return "require_approval"
    
    async def execute_auto_action(self, user, intent: Dict, execution_fn):
        """
        Execute an auto-approved action.
        
        Args:
            user: User object
            intent: Parsed intent
            execution_fn: Async function to execute the action
        """
        import time
        start_time = time.time()
        
        try:
            # Execute the action
            result = await execution_fn(intent)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Log auto-execution
            self._log_auto_execution(
                user=user,
                intent=intent,
                success=True,
                duration_ms=duration_ms,
                result_summary=str(result)[:500]
            )
            
            return result
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Log failed auto-execution
            self._log_auto_execution(
                user=user,
                intent=intent,
                success=False,
                duration_ms=duration_ms,
                result_summary=f"Error: {str(e)}"
            )
            
            raise
    
    def _log_auto_execution(self, user, intent, success, duration_ms, result_summary):
        """Log auto-executed action to database and security log."""
        # Insert into auto_executed_actions table
        action = AutoExecutedAction(
            user_id=user.id,
            operation_id=intent.get("operation_id", "unknown"),
            action_type=intent.get("intent_type"),
            risk_level=intent.get("risk_level", "unknown"),
            command=intent.get("original_command", ""),
            executed_at=datetime.utcnow(),
            duration_ms=duration_ms,
            success=success,
            result_summary=result_summary
        )
        self.db.add(action)
        self.db.commit()
        
        # Log to security logger
        log_auto_execution(
            user=user.email,
            action_type=intent.get("intent_type"),
            risk_level=intent.get("risk_level"),
            success=success,
            ip=intent.get("client_ip", "unknown")
        )
```

**Deliverable:**
- AutoExecutor class
- should_auto_execute() logic
- execute_auto_action() wrapper
- Audit logging
- Unit tests

---

### Task 5: Integration with Decomposition Engine (4 hours)

**File:** Update `phase1-nlp/decomposition/task_decomposer.py`

```python
# Add to decompose() method:

from autonomy.tier_classifier import TierClassifier
from autonomy.auto_executor import AutoExecutor

# After parsing intent:
risk_assessment = tier_classifier.classify(intent)
should_auto, risk_info = auto_executor.should_auto_execute(current_user, intent)

# Include in response:
return {
    "decomposition": {
        "decomposition_id": decomposition_id,
        "risk_assessment": {
            "risk_level": risk_info.risk_level.value,
            "reason": risk_info.reason,
            "can_auto_execute": risk_info.can_auto_execute
        },
        "autonomy_decision": {
            "should_auto_execute": should_auto,
            "requires_approval": not should_auto,
            "approval_type": "manual" if not should_auto else "automatic"
        },
        # ... rest of decomposition
    }
}
```

**Deliverable:**
- Integration with decomposition engine
- Risk assessment in response
- Autonomy decision included
- Integration tests

---

### Task 6: Security Logging Extension (2 hours)

**File:** Update `api_gateway/utils/security_logger.py`

```python
def log_auto_execution(user: str, action_type: str, risk_level: str, 
                       success: bool, ip: str):
    """
    Log auto-executed action.
    
    Args:
        user: User email who configured auto-execute
        action_type: Type of action (e.g., restart_pod)
        risk_level: Risk level (low/medium/high)
        success: Whether execution succeeded
        ip: IP address
    """
    level = logging.INFO if success else logging.ERROR
    event = _format_event("auto_execution", {
        "user": user,
        "action_type": action_type,
        "risk_level": risk_level,
        "success": success,
        "ip_address": ip,
        "result": "SUCCESS" if success else "FAILED",
        "approval_bypassed": True
    })
    security_logger.log(level, event)
```

**Deliverable:**
- log_auto_execution() function
- Structured logging format
- Tests

---

### Task 7: Unit Tests (2 hours)

**File:** `tests/test_autonomy_tiers.py`

```python
"""
Autonomy Tier System Tests
"""

def test_risk_classification():
    """Test risk classifier correctly classifies actions."""
    pass

def test_autonomy_settings_defaults():
    """Test default settings (all require approval)."""
    pass

def test_cannot_auto_execute_critical():
    """Test CRITICAL actions never auto-execute."""
    pass

def test_auto_execute_low_risk():
    """Test low-risk actions auto-execute when configured."""
    pass

def test_require_approval_when_not_configured():
    """Test fail-safe: require approval if setting unknown."""
    pass

def test_audit_logging():
    """Test all auto-executions are logged."""
    pass
```

**Deliverable:**
- Comprehensive test suite
- Edge cases covered
- 100% code coverage for new modules

---

## API Endpoints Summary

### New Endpoints:
```
GET  /api/v1/autonomy/settings
POST /api/v1/autonomy/settings
GET  /api/v1/autonomy/action-types
GET  /api/v1/autonomy/auto-executed-history
```

---

## Frontend Integration (Deferred to Future Sprint)

**Not in scope for Week 13-15**, but design API to support:

Future UI component: `AutonomySettings.tsx`
```typescript
// Settings page
Settings → Autonomy Preferences
☑ Auto-execute pod restarts (LOW risk)
☑ Auto-execute disk cleanup under 10GB (LOW risk)
☐ Auto-execute staging deployments (MEDIUM risk)
☐ Require my approval for production deploys (HIGH risk)
[Cannot change] Production database changes always require approval (CRITICAL)
```

---

## Testing Checklist

- [ ] Risk classifier correctly identifies LOW/MEDIUM/HIGH/CRITICAL
- [ ] Default settings (all require approval) work
- [ ] Update settings API validates input
- [ ] CRITICAL actions cannot be set to auto-execute
- [ ] Auto-executor checks user settings correctly
- [ ] Fail-safe: Unknown settings default to require-approval
- [ ] All auto-executions logged to security log
- [ ] All auto-executions logged to database (audit trail)
- [ ] Integration with decomposition engine works
- [ ] API endpoints return correct data
- [ ] Performance: <50ms overhead for autonomy check

---

## Rollout Plan

### Phase 1: Backend Only (Week 13-15) ← CURRENT
- Database schema
- API endpoints
- Risk classification
- Auto-execute logic
- Tests

**Users can configure via API/curl initially**

### Phase 2: Frontend UI (Week 16-18)
- Settings page component
- Autonomy preferences UI
- Action type explanations
- Auto-executed actions history

### Phase 3: Advanced Features (Future)
- ML-based risk classification
- Per-action overrides
- Temporary autonomy (time-limited)
- Team-level defaults

---

## Success Criteria

- [ ] Database schema created and populated
- [ ] 3 API endpoints working (GET/POST settings, GET action-types)
- [ ] Risk classifier correctly classifies 95% of test cases
- [ ] Auto-executor logic prevents CRITICAL auto-execution
- [ ] All auto-executions logged (security + audit)
- [ ] 100% test coverage for new code
- [ ] Integration tests passing
- [ ] Documentation complete

---

## Estimated Timeline

| Task | Hours | Days |
|------|-------|------|
| 1. Database Schema | 4h | 0.5d |
| 2. Risk Classifier | 8h | 1d |
| 3. Autonomy Settings API | 8h | 1d |
| 4. Auto-Execute Logic | 12h | 1.5d |
| 5. Decomposition Integration | 4h | 0.5d |
| 6. Security Logging | 2h | 0.25d |
| 7. Unit Tests | 2h | 0.25d |
| **TOTAL** | **40h** | **5 days** |

**Target Completion:** End of Week 13-15

---

## Next Steps

1. ✅ Review this specification
2. 🔨 Start Task 1: Database Schema
3. 🔨 Continue sequentially through tasks 2-7
4. ✅ Run full test suite
5. ✅ Deploy to staging
6. ✅ Document API endpoints
7. 📝 Plan Frontend UI for next sprint

---

**Ready to implement! Start with Task 1: Database Schema.**
