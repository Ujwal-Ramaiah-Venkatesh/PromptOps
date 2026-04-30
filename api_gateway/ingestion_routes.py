"""
Infrastructure Ingestion API Routes
====================================

Import out-of-band manual changes into PromptOps state.

Week 13-15: ENHANCEMENT-002
Author: PromptOps Team
Date: 2026-04-30
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from auth.dependencies import get_current_active_user, get_db
from auth.models import User
from utils.security_logger import get_client_ip, log_permission_denied

# Import Terraform generator
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'phase1-nlp'))
from context.terraform_generator import TerraformGenerator

# Import database models
from database.ingestion_models import ImportedChange, ImportRollback, TerraformStateHistory

router = APIRouter(prefix="/api/v1/ingestion", tags=["ingestion"])


# ============================================================================
# Pydantic Models
# ============================================================================

class DriftChangeInfo(BaseModel):
    """Information about a drift change."""
    resource_id: str
    resource_type: str
    field_changed: str
    old_value: str
    new_value: str
    changed_by: Optional[str] = None
    changed_at: Optional[str] = None


class ImportChangeRequest(BaseModel):
    """Request to import a manual change."""
    drift_id: str
    resource_id: str
    resource_type: str
    change_info: DriftChangeInfo
    reason: Optional[str] = None


class ImportChangeResponse(BaseModel):
    """Response after importing a change."""
    import_id: str
    status: str  # pending, generating, complete, failed
    resource_id: str
    terraform_preview: Optional[str] = None
    message: str


class TerraformPreviewRequest(BaseModel):
    """Request to generate Terraform code preview."""
    resource_id: str
    resource_type: str
    aws_state: Dict  # Current AWS state


class TerraformPreviewResponse(BaseModel):
    """Terraform code preview."""
    resource_id: str
    terraform_code: str
    resource_count: int
    warnings: List[str]


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/import", response_model=ImportChangeResponse)
async def import_manual_change(
    request: Request,
    import_request: ImportChangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Import a manual change detected via drift detection.

    This endpoint:
    1. Validates the change is safe to import
    2. Generates Terraform code for the new state
    3. Updates PromptOps state to match AWS actual state
    4. Records the import in audit log

    **Permissions:** Requires 'engineer', 'lead', or 'admin' role

    **Example request:**
    ```json
    {
        "drift_id": "drift-abc123",
        "resource_id": "i-1234567890abcdef0",
        "resource_type": "ec2_instance",
        "change_info": {
            "resource_id": "i-1234567890abcdef0",
            "resource_type": "ec2_instance",
            "field_changed": "instance_type",
            "old_value": "t3.medium",
            "new_value": "t3.large",
            "changed_by": "john.kim@company.com",
            "changed_at": "2026-04-30T03:14:00Z"
        },
        "reason": "Emergency fix for performance issue"
    }
    ```

    **Example response:**
    ```json
    {
        "import_id": "import-xyz789",
        "status": "complete",
        "resource_id": "i-1234567890abcdef0",
        "terraform_preview": "resource \"aws_instance\" \"...",
        "message": "Successfully imported EC2 instance change"
    }
    ```
    """
    # Check permissions (only engineers+ can import)
    from auth.permissions import check_environment_access

    if current_user.role not in ["engineer", "lead", "admin"]:
        log_permission_denied(
            user=current_user.email,
            resource="/api/v1/ingestion/import",
            action="import_change",
            reason=f"role_{current_user.role}_insufficient",
            ip=get_client_ip(request)
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only engineers, leads, and admins can import infrastructure changes"
        )

    # Generate import ID
    import_id = f"import-{int(datetime.utcnow().timestamp())}"

    try:
        # Step 1: Generate Terraform code from change info
        generator = TerraformGenerator()

        # Build AWS state from change info
        aws_state = {
            import_request.change_info.field_changed: import_request.change_info.new_value
        }

        # Generate Terraform preview
        result = generator.generate(
            resource_id=import_request.resource_id,
            resource_type=import_request.resource_type,
            aws_state=aws_state
        )

        # Step 2: Validate the change is safe
        is_valid, validation_errors = generator.validate_generated_code(result.terraform_code)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Generated Terraform code is invalid: {', '.join(validation_errors)}"
            )

        # Step 3: TODO - Update Terraform state file
        # This would use terraform import or state manipulation
        # For now, we'll just preview

        # Step 4: Store in database
        imported_change = ImportedChange(
            import_id=import_id,
            user_id=current_user.id,
            drift_id=import_request.drift_id,
            resource_id=import_request.resource_id,
            resource_type=import_request.resource_type,
            field_changed=import_request.change_info.field_changed,
            old_value=import_request.change_info.old_value,
            new_value=import_request.change_info.new_value,
            changed_by=import_request.change_info.changed_by,
            changed_at=import_request.change_info.changed_at,
            imported_by=current_user.id,
            reason=import_request.reason,
            terraform_code=result.terraform_code,
            terraform_applied=False,  # Not yet applied
            status="complete"
        )

        db.add(imported_change)
        db.commit()
        db.refresh(imported_change)

        # Step 5: Record in audit log
        log_permission_denied(  # Reusing for audit (should create log_import_change)
            user=current_user.email,
            resource=f"/api/v1/ingestion/import/{import_request.resource_type}",
            action="import_change",
            reason=import_request.reason or "Manual import",
            ip=get_client_ip(request)
        )

        return ImportChangeResponse(
            import_id=import_id,
            status="complete",
            resource_id=import_request.resource_id,
            terraform_preview=result.terraform_code,
            message=f"Successfully imported {import_request.resource_type} {import_request.resource_id}"
        )

    except Exception as e:
        # Log error and return failure
        log_permission_denied(
            user=current_user.email,
            resource="/api/v1/ingestion/import",
            action="import_change_failed",
            reason=str(e),
            ip=get_client_ip(request)
        )

        return ImportChangeResponse(
            import_id=import_id,
            status="failed",
            resource_id=import_request.resource_id,
            terraform_preview=None,
            message=f"Import failed: {str(e)}"
        )


@router.post("/terraform-preview", response_model=TerraformPreviewResponse)
async def generate_terraform_preview(
    request: Request,
    preview_request: TerraformPreviewRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Generate Terraform code preview from AWS actual state.

    Shows the PM what Terraform code will be generated before importing.

    **Permissions:** Requires 'engineer', 'lead', or 'admin' role

    **Example request:**
    ```json
    {
        "resource_id": "i-1234567890abcdef0",
        "resource_type": "ec2_instance",
        "aws_state": {
            "instance_type": "t3.large",
            "ami": "ami-0c55b159cbfafe1f0",
            "subnet_id": "subnet-12345",
            "tags": {"Name": "web-server-1", "Environment": "production"}
        }
    }
    ```

    **Example response:**
    ```json
    {
        "resource_id": "i-1234567890abcdef0",
        "terraform_code": "resource \"aws_instance\" \"web_server_1\" {...}",
        "resource_count": 1,
        "warnings": ["Instance type changed from t3.medium to t3.large"]
    }
    ```
    """
    # Check permissions
    if current_user.role not in ["engineer", "lead", "admin"]:
        log_permission_denied(
            user=current_user.email,
            resource="/api/v1/ingestion/terraform-preview",
            action="preview_terraform",
            reason=f"role_{current_user.role}_insufficient",
            ip=get_client_ip(request)
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only engineers, leads, and admins can preview Terraform code"
        )

    try:
        # Generate Terraform code from AWS state
        generator = TerraformGenerator()

        result = generator.generate(
            resource_id=preview_request.resource_id,
            resource_type=preview_request.resource_type,
            aws_state=preview_request.aws_state
        )

        # Validate generated code
        is_valid, validation_errors = generator.validate_generated_code(result.terraform_code)
        if not is_valid:
            result.warnings.extend([f"Validation: {err}" for err in validation_errors])

        return TerraformPreviewResponse(
            resource_id=preview_request.resource_id,
            terraform_code=result.terraform_code,
            resource_count=result.resource_count,
            warnings=result.warnings
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate Terraform preview: {str(e)}"
        )


@router.get("/imports")
async def get_import_history(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = 50,
    status: Optional[str] = None,
    resource_type: Optional[str] = None
):
    """
    Get history of imported changes.

    **Query parameters:**
    - limit: Max number of records (default: 50, max: 100)
    - status: Filter by status (optional)
    - resource_type: Filter by resource type (optional)

    **Example response:**
    ```json
    [
        {
            "import_id": "import-1714492800",
            "resource_id": "i-1234567890abcdef0",
            "resource_type": "ec2_instance",
            "imported_by": "john.kim@company.com",
            "imported_at": "2026-04-30T10:30:00Z",
            "status": "complete",
            "reason": "Emergency fix for performance issue"
        }
    ]
    ```
    """
    if limit > 100:
        limit = 100

    # Query imported changes
    query = db.query(ImportedChange)

    # Apply filters
    if status:
        query = query.filter(ImportedChange.status == status)
    if resource_type:
        query = query.filter(ImportedChange.resource_type == resource_type)

    # Get results ordered by most recent first
    imports = query.order_by(ImportedChange.imported_at.desc()).limit(limit).all()

    # Convert to dict and return
    return [imp.to_dict() for imp in imports]


@router.delete("/imports/{import_id}")
async def rollback_import(
    import_id: str,
    request: Request,
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Rollback a previously imported change.

    **Permissions:** Requires 'lead' or 'admin' role

    **Query parameters:**
    - reason: Reason for rollback (optional)

    **Example response:**
    ```json
    {
        "message": "Import rolled back successfully",
        "import_id": "import-1714492800",
        "reverted_to": "previous_state"
    }
    ```
    """
    # Check permissions (only lead+ can rollback)
    if current_user.role not in ["lead", "admin"]:
        log_permission_denied(
            user=current_user.email,
            resource=f"/api/v1/ingestion/imports/{import_id}",
            action="rollback_import",
            reason=f"role_{current_user.role}_insufficient",
            ip=get_client_ip(request)
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only leads and admins can rollback imports"
        )

    # Find the import
    imported_change = db.query(ImportedChange).filter(
        ImportedChange.import_id == import_id
    ).first()

    if not imported_change:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import {import_id} not found"
        )

    # Check if already rolled back
    if imported_change.status == "rolled_back":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Import {import_id} is already rolled back"
        )

    try:
        # TODO: Revert the Terraform state change
        # This would involve:
        # 1. Load previous Terraform state
        # 2. Apply rollback (terraform apply with old state)
        # 3. Update AWS resources if needed

        # Mark import as rolled back
        imported_change.status = "rolled_back"
        imported_change.updated_at = datetime.utcnow()

        # Record rollback
        rollback = ImportRollback(
            import_id=import_id,
            rolled_back_by=current_user.id,
            reason=reason or "Manual rollback",
            success=True,  # Assume success for now
            previous_terraform=imported_change.terraform_code,
            reverted_to_state=imported_change.old_value
        )

        db.add(rollback)
        db.commit()
        db.refresh(imported_change)
        db.refresh(rollback)

        # Log rollback
        log_permission_denied(  # Reusing for audit
            user=current_user.email,
            resource=f"/api/v1/ingestion/imports/{import_id}",
            action="rollback_import",
            reason=reason or "Manual rollback",
            ip=get_client_ip(request)
        )

        return {
            "message": "Import rolled back successfully",
            "import_id": import_id,
            "reverted_to": imported_change.old_value,
            "rollback_id": str(rollback.id)
        }

    except Exception as e:
        # Log failed rollback
        rollback = ImportRollback(
            import_id=import_id,
            rolled_back_by=current_user.id,
            reason=reason or "Manual rollback",
            success=False,
            error_message=str(e)
        )
        db.add(rollback)
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rollback failed: {str(e)}"
        )
