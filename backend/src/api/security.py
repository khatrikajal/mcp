"""
Security API Endpoints

Provides endpoints for security management, RBAC, and audit logs.
"""
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.src.db.connection import get_db
from backend.src.db.models import User, ThreatLevel
from backend.src.api.auth_utils import get_current_user
from backend.src.services.security_service import SecurityService, get_security_service
from backend.src.services.rbac_service import RBACService
from backend.src.services.audit_service import AuditService

router = APIRouter(prefix="/security", tags=["Security"])


# ==================== Request/Response Models ====================

class PromptCheckRequest(BaseModel):
    text: str
    use_llm: bool = True


class PromptCheckResponse(BaseModel):
    is_injection: bool
    threat_level: str
    detected_patterns: List[str]


class IPBlockRequest(BaseModel):
    ip_address: str
    duration_minutes: int = 60
    reason: str = ""


class RoleCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    permission_names: List[str] = []


class RoleUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permission_names: Optional[List[str]] = None


class RoleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    is_system_role: bool
    permission_count: int
    user_count: int


class PermissionResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    category: str


class UserRoleAssignRequest(BaseModel):
    role_id: int


class UserPermissionsResponse(BaseModel):
    user_id: int
    permissions: List[str]
    roles: List[str]


# ==================== Prompt Injection Detection ====================

@router.post("/check-prompt", response_model=PromptCheckResponse)
def check_prompt_injection(
    request: PromptCheckRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check a text for prompt injection attempts.

    This endpoint can be used to validate user inputs before processing.
    """
    security_service = get_security_service()

    is_injection, threat_level, patterns = security_service.detect_prompt_injection(
        text=request.text,
        use_llm=request.use_llm
    )

    # Log high-severity detections
    if threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
        from backend.src.db.models import SecurityEventType
        audit_service = AuditService(db)
        audit_service.log_event(
            event_type=SecurityEventType.PROMPT_INJECTION_DETECTED,
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            threat_level=threat_level,
            description=f"Prompt injection detected: {patterns}",
            request_data={"text_preview": request.text[:200]}
        )

    return PromptCheckResponse(
        is_injection=is_injection,
        threat_level=threat_level.value,
        detected_patterns=patterns
    )


@router.post("/sanitize-input")
def sanitize_input(
    text: str,
    current_user: User = Depends(get_current_user)
):
    """
    Sanitize user input by removing potentially dangerous content.
    """
    security_service = get_security_service()
    sanitized = security_service.sanitize_input(text)

    return {
        "original_length": len(text),
        "sanitized_length": len(sanitized),
        "sanitized_text": sanitized
    }


# ==================== IP Management ====================

@router.get("/ip-check")
def check_ip_address(
    ip_address: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check if an IP address is allowed.

    Requires permission: admin:manage_settings
    """
    rbac = RBACService(db)
    if not rbac.has_permission(current_user.id, "admin:manage_settings"):
        raise HTTPException(status_code=403, detail="Permission denied")

    security_service = get_security_service()
    is_allowed, reason = security_service.is_ip_allowed(ip_address)

    return {
        "ip_address": ip_address,
        "is_allowed": is_allowed,
        "reason": reason
    }


@router.post("/ip-block")
def block_ip_address(
    request: IPBlockRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Temporarily block an IP address.

    Requires permission: admin:manage_settings
    """
    rbac = RBACService(db)
    if not rbac.has_permission(current_user.id, "admin:manage_settings"):
        raise HTTPException(status_code=403, detail="Permission denied")

    security_service = get_security_service()
    security_service.block_ip(
        ip_address=request.ip_address,
        duration_minutes=request.duration_minutes,
        reason=request.reason
    )

    # Log the action
    from backend.src.db.models import SecurityEventType
    audit_service = AuditService(db)
    audit_service.log_event(
        event_type=SecurityEventType.IP_BLOCKED,
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        description=f"Blocked IP {request.ip_address} for {request.duration_minutes} minutes: {request.reason}"
    )

    return {
        "status": "blocked",
        "ip_address": request.ip_address,
        "duration_minutes": request.duration_minutes,
        "expires_at": (datetime.utcnow() + timedelta(minutes=request.duration_minutes)).isoformat()
    }


# ==================== Rate Limiting ====================

@router.get("/rate-limit-status")
def get_rate_limit_status(
    action: str,
    tool_name: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Check current rate limit status for an action.
    """
    from backend.src.core.config import (
        RATE_LIMIT_DEFAULT, RATE_LIMIT_CHAT, RATE_LIMIT_EMAIL,
        RATE_LIMIT_CALENDAR, RATE_LIMIT_MEETING
    )

    security_service = get_security_service()
    key = security_service.get_rate_limit_key(
        user_id=current_user.id,
        action=action,
        tool_name=tool_name
    )

    # Get limit based on action
    limits = {
        "chat": RATE_LIMIT_CHAT,
        "email": RATE_LIMIT_EMAIL,
        "calendar": RATE_LIMIT_CALENDAR,
        "meeting": RATE_LIMIT_MEETING,
    }
    limit = limits.get(action, RATE_LIMIT_DEFAULT)

    is_allowed, current, remaining = security_service.check_rate_limit(key, limit)

    return {
        "action": action,
        "tool_name": tool_name,
        "limit": limit,
        "current": current,
        "remaining": remaining,
        "is_allowed": is_allowed
    }


# ==================== Role Management ====================

@router.get("/permissions", response_model=List[PermissionResponse])
def list_permissions(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all available permissions.

    Requires permission: admin:manage_roles
    """
    rbac = RBACService(db)
    if not rbac.has_permission(current_user.id, "admin:manage_roles"):
        raise HTTPException(status_code=403, detail="Permission denied")

    if category:
        permissions = rbac.get_permissions_by_category(category)
    else:
        permissions = rbac.get_all_permissions()

    return [
        PermissionResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            category=p.category
        )
        for p in permissions
    ]


@router.post("/permissions/initialize")
def initialize_permissions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initialize default permissions in the database.

    Requires permission: admin:manage_roles
    """
    rbac = RBACService(db)
    if not rbac.has_permission(current_user.id, "admin:manage_roles"):
        raise HTTPException(status_code=403, detail="Permission denied")

    created = rbac.initialize_permissions()
    return {"status": "success", "permissions_created": created}


@router.get("/roles", response_model=List[RoleResponse])
def list_roles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all roles in the organization.

    Requires permission: admin:manage_roles
    """
    rbac = RBACService(db)
    if not rbac.has_permission(current_user.id, "admin:manage_roles"):
        raise HTTPException(status_code=403, detail="Permission denied")

    roles = rbac.get_organization_roles(current_user.organization_id)

    from backend.src.db.models import UserRole as UserRoleAssignment, RolePermission

    result = []
    for role in roles:
        # Count users and permissions
        user_count = db.query(UserRoleAssignment).filter(
            UserRoleAssignment.role_id == role.id
        ).count()

        permission_count = db.query(RolePermission).filter(
            RolePermission.role_id == role.id
        ).count()

        result.append(RoleResponse(
            id=role.id,
            name=role.name,
            description=role.description,
            is_system_role=role.is_system_role,
            permission_count=permission_count,
            user_count=user_count
        ))

    return result


@router.post("/roles", response_model=RoleResponse)
def create_role(
    request: RoleCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new role.

    Requires permission: admin:manage_roles
    """
    rbac = RBACService(db)
    if not rbac.has_permission(current_user.id, "admin:manage_roles"):
        raise HTTPException(status_code=403, detail="Permission denied")

    try:
        role = rbac.create_role(
            organization_id=current_user.organization_id,
            name=request.name,
            description=request.description,
            permission_names=request.permission_names
        )

        from backend.src.db.models import RolePermission
        permission_count = db.query(RolePermission).filter(
            RolePermission.role_id == role.id
        ).count()

        return RoleResponse(
            id=role.id,
            name=role.name,
            description=role.description,
            is_system_role=role.is_system_role,
            permission_count=permission_count,
            user_count=0
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/roles/{role_id}", response_model=RoleResponse)
def update_role(
    role_id: int,
    request: RoleUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a role.

    Requires permission: admin:manage_roles
    """
    rbac = RBACService(db)
    if not rbac.has_permission(current_user.id, "admin:manage_roles"):
        raise HTTPException(status_code=403, detail="Permission denied")

    try:
        role = rbac.update_role(
            role_id=role_id,
            name=request.name,
            description=request.description,
            permission_names=request.permission_names
        )

        from backend.src.db.models import UserRole as UserRoleAssignment, RolePermission
        permission_count = db.query(RolePermission).filter(
            RolePermission.role_id == role.id
        ).count()
        user_count = db.query(UserRoleAssignment).filter(
            UserRoleAssignment.role_id == role.id
        ).count()

        return RoleResponse(
            id=role.id,
            name=role.name,
            description=role.description,
            is_system_role=role.is_system_role,
            permission_count=permission_count,
            user_count=user_count
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/roles/{role_id}")
def delete_role(
    role_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a role.

    Requires permission: admin:manage_roles
    """
    rbac = RBACService(db)
    if not rbac.has_permission(current_user.id, "admin:manage_roles"):
        raise HTTPException(status_code=403, detail="Permission denied")

    try:
        rbac.delete_role(role_id)
        return {"status": "deleted", "role_id": role_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/roles/{role_id}/initialize-defaults")
def initialize_default_roles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initialize default roles for the organization.

    Requires permission: admin:manage_roles
    """
    rbac = RBACService(db)
    if not rbac.has_permission(current_user.id, "admin:manage_roles"):
        raise HTTPException(status_code=403, detail="Permission denied")

    roles = rbac.initialize_default_roles(current_user.organization_id)
    return {
        "status": "success",
        "roles_created": [r.name for r in roles.values() if r]
    }


# ==================== User Role Assignment ====================

@router.get("/users/{user_id}/permissions", response_model=UserPermissionsResponse)
def get_user_permissions(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all permissions for a user.

    Users can view their own permissions, admins can view anyone's.
    """
    rbac = RBACService(db)

    # Users can view their own permissions
    if user_id != current_user.id and not rbac.has_permission(current_user.id, "admin:manage_users"):
        raise HTTPException(status_code=403, detail="Permission denied")

    # Verify user is in same organization
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user or target_user.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="User not found")

    permissions = rbac.get_user_permissions(user_id)
    roles = rbac.get_user_roles(user_id)

    return UserPermissionsResponse(
        user_id=user_id,
        permissions=list(permissions),
        roles=[r.name for r in roles]
    )


@router.post("/users/{user_id}/roles")
def assign_role_to_user(
    user_id: int,
    request: UserRoleAssignRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Assign a role to a user.

    Requires permission: admin:manage_users
    """
    rbac = RBACService(db)
    if not rbac.has_permission(current_user.id, "admin:manage_users"):
        raise HTTPException(status_code=403, detail="Permission denied")

    # Verify user is in same organization
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user or target_user.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="User not found")

    assignment = rbac.assign_role_to_user(
        user_id=user_id,
        role_id=request.role_id,
        assigned_by_user_id=current_user.id
    )

    return {
        "status": "assigned",
        "user_id": user_id,
        "role_id": request.role_id,
        "created_at": assignment.created_at.isoformat()
    }


@router.delete("/users/{user_id}/roles/{role_id}")
def remove_role_from_user(
    user_id: int,
    role_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove a role from a user.

    Requires permission: admin:manage_users
    """
    rbac = RBACService(db)
    if not rbac.has_permission(current_user.id, "admin:manage_users"):
        raise HTTPException(status_code=403, detail="Permission denied")

    # Verify user is in same organization
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user or target_user.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="User not found")

    removed = rbac.remove_role_from_user(user_id, role_id)

    if not removed:
        raise HTTPException(status_code=404, detail="Role assignment not found")

    return {"status": "removed", "user_id": user_id, "role_id": role_id}


# ==================== Permission Report ====================

@router.get("/permission-report")
def get_permission_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a report of permission usage in the organization.

    Requires permission: admin:manage_roles
    """
    rbac = RBACService(db)
    if not rbac.has_permission(current_user.id, "admin:manage_roles"):
        raise HTTPException(status_code=403, detail="Permission denied")

    return rbac.get_permission_report(current_user.organization_id)


# ==================== Tool Argument Validation ====================

@router.post("/validate-tool-args")
def validate_tool_arguments(
    tool_name: str,
    arguments: dict,
    current_user: User = Depends(get_current_user)
):
    """
    Validate tool arguments for security issues.
    """
    security_service = get_security_service()
    is_valid, issues = security_service.validate_tool_arguments(tool_name, arguments)

    return {
        "tool_name": tool_name,
        "is_valid": is_valid,
        "issues": issues
    }
