"""
Auto-Executor
=============

Handles auto-execution of pre-authorized operations.

Week 13-15: ENHANCEMENT-001
Author: PromptOps Team
Date: 2026-04-30
"""

from typing import Dict, Optional, Callable, Any
from datetime import datetime
from .tier_classifier import TierClassifier, RiskAssessment, RiskLevel
from database.autonomy_models import AutonomyTier, AutoExecutedAction
import logging
import time

logger = logging.getLogger(__name__)


class AutoExecutor:
    """
    Determines if an operation should auto-execute or require approval.

    Example usage:
        executor = AutoExecutor(db_session)
        should_execute, assessment = executor.should_auto_execute(user, intent)

        if should_execute:
            result = await executor.execute_auto_action(user, intent, execute_fn)
        else:
            # Show approval card to PM
            pass
    """

    def __init__(self, db_session):
        """
        Initialize auto-executor.

        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session
        self.classifier = TierClassifier(db_session)

    def should_auto_execute(self, user, intent: Dict) -> tuple[bool, RiskAssessment]:
        """
        Determine if operation should auto-execute.

        Args:
            user: User object (with id attribute)
            intent: Parsed intent dictionary

        Returns:
            Tuple of (should_execute: bool, risk_assessment: RiskAssessment)

        Example:
            should_exec, assessment = executor.should_auto_execute(user, intent)
            if should_exec:
                print(f"Auto-executing {assessment.action_type}")
            else:
                print(f"Requires approval: {assessment.reason}")
        """
        # Classify risk level
        risk_assessment = self.classifier.classify(intent)

        # CRITICAL actions NEVER auto-execute (safety guarantee)
        if risk_assessment.risk_level == RiskLevel.CRITICAL:
            logger.info(
                f"Action {risk_assessment.action_type} is CRITICAL - "
                f"requires approval (user={user.email})"
            )
            return False, risk_assessment

        # Get user's autonomy setting for this risk level
        user_setting = self._get_user_setting(user.id, risk_assessment.risk_level.value)

        # Check if user has auto_execute enabled for this risk level
        should_execute = (user_setting == "auto_execute")

        if should_execute:
            logger.info(
                f"Auto-executing {risk_assessment.action_type} "
                f"(risk={risk_assessment.risk_level.value}, user={user.email})"
            )
        else:
            logger.info(
                f"Requiring approval for {risk_assessment.action_type} "
                f"(risk={risk_assessment.risk_level.value}, user={user.email})"
            )

        return should_execute, risk_assessment

    def _get_user_setting(self, user_id: str, risk_level: str) -> str:
        """
        Get user's autonomy setting for a risk level.

        Args:
            user_id: User UUID
            risk_level: Risk level string (low, medium, high, critical)

        Returns:
            'auto_execute' or 'require_approval'
            Default: 'require_approval' (fail-safe)
        """
        try:
            setting = self.db.query(AutonomyTier).filter(
                AutonomyTier.user_id == user_id,
                AutonomyTier.risk_level == risk_level
            ).first()

            if setting:
                return setting.behavior

        except Exception as e:
            logger.error(f"Failed to get autonomy setting: {e}")

        # Default: require approval (fail-safe)
        return "require_approval"

    async def execute_auto_action(
        self,
        user,
        intent: Dict,
        execution_fn: Callable,
        risk_assessment: Optional[RiskAssessment] = None
    ) -> Any:
        """
        Execute an auto-approved action.

        Args:
            user: User object
            intent: Parsed intent dictionary
            execution_fn: Async function to execute the action
                         Should accept intent and return result
            risk_assessment: Optional pre-computed risk assessment

        Returns:
            Result from execution_fn

        Raises:
            Exception: If execution fails (logged and re-raised)

        Example:
            async def execute_restart_pod(intent):
                # ... restart logic
                return {"status": "restarted", "pod_id": "..."}

            result = await executor.execute_auto_action(
                user, intent, execute_restart_pod
            )
        """
        operation_id = intent.get("operation_id", f"auto-{int(time.time())}")
        action_type = intent.get("intent_type", "unknown")
        command = intent.get("original_command", "")

        # Get risk assessment if not provided
        if risk_assessment is None:
            _, risk_assessment = self.should_auto_execute(user, intent)

        start_time = time.time()
        success = False
        result_summary = ""

        try:
            logger.info(f"Executing auto-action: {action_type} (op={operation_id})")

            # Execute the action
            result = await execution_fn(intent)

            success = True
            result_summary = str(result)[:500]  # Truncate to 500 chars

            logger.info(
                f"Auto-execution successful: {action_type} "
                f"(op={operation_id}, duration={(time.time() - start_time):.2f}s)"
            )

            return result

        except Exception as e:
            success = False
            result_summary = f"Error: {str(e)}"[:500]

            logger.error(
                f"Auto-execution failed: {action_type} "
                f"(op={operation_id}, error={str(e)})"
            )

            raise

        finally:
            # Always log auto-execution (success or failure)
            duration_ms = int((time.time() - start_time) * 1000)

            self._log_auto_execution(
                user=user,
                operation_id=operation_id,
                action_type=action_type,
                risk_level=risk_assessment.risk_level.value,
                command=command,
                success=success,
                duration_ms=duration_ms,
                result_summary=result_summary,
                ip=intent.get("client_ip", "unknown"),
                user_agent=intent.get("user_agent")
            )

    def _log_auto_execution(
        self,
        user,
        operation_id: str,
        action_type: str,
        risk_level: str,
        command: str,
        success: bool,
        duration_ms: int,
        result_summary: str,
        ip: str,
        user_agent: Optional[str] = None
    ):
        """
        Log auto-executed action to database and security log.

        Args:
            user: User object
            operation_id: Unique operation identifier
            action_type: Type of action (e.g., restart_pod)
            risk_level: Risk level (low/medium/high)
            command: Original command text
            success: Whether execution succeeded
            duration_ms: Execution duration in milliseconds
            result_summary: Brief result summary (max 500 chars)
            ip: IP address
            user_agent: User agent string
        """
        try:
            # Insert into auto_executed_actions table
            action = AutoExecutedAction(
                user_id=user.id,
                operation_id=operation_id,
                action_type=action_type,
                risk_level=risk_level,
                command=command,
                executed_at=datetime.utcnow(),
                duration_ms=duration_ms,
                success=success,
                result_summary=result_summary,
                ip_address=ip,
                user_agent=user_agent
            )
            self.db.add(action)
            self.db.commit()

            logger.debug(f"Logged auto-execution to database: {operation_id}")

        except Exception as e:
            logger.error(f"Failed to log auto-execution to database: {e}")
            self.db.rollback()

        # Also log to security logger
        try:
            from utils.security_logger import log_auto_execution

            log_auto_execution(
                user=user.email,
                action_type=action_type,
                risk_level=risk_level,
                success=success,
                ip=ip
            )

        except Exception as e:
            logger.error(f"Failed to log to security logger: {e}")

    def get_auto_execution_history(
        self,
        user_id: str,
        limit: int = 50,
        action_type: Optional[str] = None
    ) -> list:
        """
        Get user's auto-execution history.

        Args:
            user_id: User UUID
            limit: Maximum number of records to return
            action_type: Optional filter by action type

        Returns:
            List of AutoExecutedAction objects
        """
        query = self.db.query(AutoExecutedAction).filter(
            AutoExecutedAction.user_id == user_id
        )

        if action_type:
            query = query.filter(AutoExecutedAction.action_type == action_type)

        query = query.order_by(AutoExecutedAction.executed_at.desc())
        query = query.limit(limit)

        return query.all()

    def get_auto_execution_stats(self, user_id: str) -> Dict:
        """
        Get statistics about user's auto-executions.

        Args:
            user_id: User UUID

        Returns:
            Dictionary with statistics:
            - total: Total auto-executions
            - successful: Successful auto-executions
            - failed: Failed auto-executions
            - by_risk_level: Count by risk level
            - by_action_type: Count by action type
        """
        try:
            actions = self.db.query(AutoExecutedAction).filter(
                AutoExecutedAction.user_id == user_id
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

            return {
                "total": total,
                "successful": successful,
                "failed": failed,
                "success_rate": (successful / total * 100) if total > 0 else 0,
                "by_risk_level": by_risk_level,
                "by_action_type": by_action_type
            }

        except Exception as e:
            logger.error(f"Failed to get auto-execution stats: {e}")
            return {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "success_rate": 0,
                "by_risk_level": {},
                "by_action_type": {}
            }
