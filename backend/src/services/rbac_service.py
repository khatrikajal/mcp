"""
RBAC Service

Role-Based Access Control with fine-grained permissions.
Supports custom roles, permission inheritance, and organization-level access control.
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Set
from sqlalchemy.orm import Session
from sqlalchemy import and_

from backend.src.db.models import (
    User,
    Organization,
    Agent,
    Permission,
    Role,
    RolePermission,
    UserRole as UserRoleAssignment,
    UserRole as UserRoleEnum,
)

logger = logging.getLogger(__name__)


# Default permissions available in the system
DEFAULT_PERMISSIONS = [
    # Agent permissions
    {"name": "agent:create", "category": "agent", "description": "Create new agents"},
    {"name": "agent:read", "category": "agent", "description": "View agents"},
    {"name": "agent:update", "category": "agent", "description": "Update agent configurations"},
    {"name": "agent:delete", "category": "agent", "description": "Delete agents"},
    {"name": "agent:share", "category": "agent", "description": "Share agents with other users"},

    # Conversation permissions
    {"name": "conversation:create", "category": "conversation", "description": "Start conversations"},
    {"name": "conversation:read", "category": "conversation", "description": "View conversations"},
    {"name": "conversation:delete", "category": "conversation", "description": "Delete conversations"},

    # Tool permissions
    {"name": "tool:execute", "category": "tool", "description": "Execute tools"},
    {"name": "tool:configure", "category": "tool", "description": "Configure tool settings"},

    # Approval permissions
    {"name": "approval:request", "category": "approval", "description": "Request approvals"},
    {"name": "approval:grant", "category": "approval", "description": "Grant approvals"},
    {"name": "approval:reject", "category": "approval", "description": "Reject approvals"},
    {"name": "approval:view_all", "category": "approval", "description": "View all approval requests"},

    # Meeting permissions
    {"name": "meeting:delegate", "category": "meeting", "description": "Delegate meetings to AI"},
    {"name": "meeting:view_reports", "category": "meeting", "description": "View meeting reports"},

    # Interview permissions
    {"name": "interview:create", "category": "interview", "description": "Schedule interviews"},
    {"name": "interview:conduct", "category": "interview", "description": "Conduct interviews"},
    {"name": "interview:view_reports", "category": "interview", "description": "View interview reports"},

    # Memory permissions
    {"name": "memory:read", "category": "memory", "description": "View agent memories"},
    {"name": "memory:write", "category": "memory", "description": "Create/update memories"},
    {"name": "memory:delete", "category": "memory", "description": "Delete memories"},

    # Analytics permissions
    {"name": "analytics:view", "category": "analytics", "description": "View analytics dashboard"},
    {"name": "analytics:export", "category": "analytics", "description": "Export analytics data"},

    # Admin permissions
    {"name": "admin:manage_users", "category": "admin", "description": "Manage organization users"},
    {"name": "admin:manage_roles", "category": "admin", "description": "Manage roles and permissions"},
    {"name": "admin:view_audit_logs", "category": "admin", "description": "View security audit logs"},
    {"name": "admin:manage_settings", "category": "admin", "description": "Manage organization settings"},
]


# Default role templates
DEFAULT_ROLE_TEMPLATES = {
    "admin": {
        "description": "Full access to all features",
        "permissions": ["*"],  # All permissions
    },
    "user": {
        "description": "Standard user access",
        "permissions": [
            "agent:create", "agent:read", "agent:update", "agent:delete",
            "conversation:create", "conversation:read", "conversation:delete",
            "tool:execute",
            "approval:request", "approval:grant", "approval:reject",
            "meeting:delegate", "meeting:view_reports",
            "interview:create", "interview:conduct", "interview:view_reports",
            "memory:read", "memory:write",
            "analytics:view",
        ],
    },
    "viewer": {
        "description": "Read-only access",
        "permissions": [
            "agent:read",
            "conversation:read",
            "meeting:view_reports",
            "interview:view_reports",
            "memory:read",
            "analytics:view",
        ],
    },
    "interviewer": {
        "description": "Interview-focused access",
        "permissions": [
            "agent:read",
            "conversation:read", "conversation:create",
            "tool:execute",
            "interview:create", "interview:conduct", "interview:view_reports",
        ],
    },
    "meeting_manager": {
        "description": "Meeting delegation access",
        "permissions": [
            "agent:read",
            "conversation:read", "conversation:create",
            "tool:execute",
            "meeting:delegate", "meeting:view_reports",
            "approval:grant", "approval:reject",
        ],
    },
}


class RBACService:
    """
    Service for Role-Based Access Control.
    """

    def __init__(self, db: Session):
        self.db = db
        self._permission_cache: Dict[int, Set[str]] = {}

    # ==================== Permission Management ====================

    def initialize_permissions(self) -> int:
        """
        Initialize default permissions in the database.

        Returns:
            Number of permissions created
        """
        created = 0
        for perm_data in DEFAULT_PERMISSIONS:
            existing = self.db.query(Permission).filter(
                Permission.name == perm_data["name"]
            ).first()

            if not existing:
                permission = Permission(
                    name=perm_data["name"],
                    description=perm_data["description"],
                    category=perm_data["category"],
                )
                self.db.add(permission)
                created += 1

        self.db.commit()
        logger.info(f"Initialized {created} permissions")
        return created

    def get_all_permissions(self) -> List[Permission]:
        """Get all available permissions."""
        return self.db.query(Permission).order_by(Permission.category, Permission.name).all()

    def get_permissions_by_category(self, category: str) -> List[Permission]:
        """Get permissions filtered by category."""
        return self.db.query(Permission).filter(
            Permission.category == category
        ).order_by(Permission.name).all()

    # ==================== Role Management ====================

    def create_role(
        self,
        organization_id: int,
        name: str,
        description: Optional[str] = None,
        permission_names: Optional[List[str]] = None,
        is_system_role: bool = False
    ) -> Role:
        """
        Create a new role for an organization.

        Args:
            organization_id: Organization ID
            name: Role name
            description: Role description
            permission_names: List of permission names to assign
            is_system_role: Whether this is a built-in role

        Returns:
            Created Role
        """
        # Check if role already exists
        existing = self.db.query(Role).filter(
            and_(Role.organization_id == organization_id, Role.name == name)
        ).first()

        if existing:
            raise ValueError(f"Role '{name}' already exists in this organization")

        role = Role(
            organization_id=organization_id,
            name=name,
            description=description,
            is_system_role=is_system_role,
        )
        self.db.add(role)
        self.db.flush()

        # Assign permissions
        if permission_names:
            self._assign_permissions_to_role(role.id, permission_names)

        self.db.commit()
        self.db.refresh(role)

        logger.info(f"Created role '{name}' for organization {organization_id}")
        return role

    def initialize_default_roles(self, organization_id: int) -> Dict[str, Role]:
        """
        Initialize default roles for an organization.

        Args:
            organization_id: Organization ID

        Returns:
            Dict of role name to Role object
        """
        roles = {}

        for role_name, role_data in DEFAULT_ROLE_TEMPLATES.items():
            try:
                # Get permission names based on template
                if role_data["permissions"] == ["*"]:
                    permission_names = [p["name"] for p in DEFAULT_PERMISSIONS]
                else:
                    permission_names = role_data["permissions"]

                role = self.create_role(
                    organization_id=organization_id,
                    name=role_name,
                    description=role_data["description"],
                    permission_names=permission_names,
                    is_system_role=True,
                )
                roles[role_name] = role
            except ValueError:
                # Role already exists
                roles[role_name] = self.db.query(Role).filter(
                    and_(Role.organization_id == organization_id, Role.name == role_name)
                ).first()

        logger.info(f"Initialized default roles for organization {organization_id}")
        return roles

    def get_role(self, role_id: int) -> Optional[Role]:
        """Get a role by ID."""
        return self.db.query(Role).filter(Role.id == role_id).first()

    def get_organization_roles(self, organization_id: int) -> List[Role]:
        """Get all roles for an organization."""
        return self.db.query(Role).filter(
            Role.organization_id == organization_id
        ).order_by(Role.is_system_role.desc(), Role.name).all()

    def update_role(
        self,
        role_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        permission_names: Optional[List[str]] = None
    ) -> Role:
        """
        Update a role.

        Args:
            role_id: Role ID
            name: New name
            description: New description
            permission_names: New list of permission names

        Returns:
            Updated Role
        """
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise ValueError(f"Role {role_id} not found")

        if role.is_system_role and name and name != role.name:
            raise ValueError("Cannot rename system roles")

        if name:
            role.name = name
        if description is not None:
            role.description = description

        if permission_names is not None:
            # Remove existing permissions
            self.db.query(RolePermission).filter(
                RolePermission.role_id == role_id
            ).delete()
            # Assign new permissions
            self._assign_permissions_to_role(role_id, permission_names)

        self.db.commit()
        self.db.refresh(role)

        # Invalidate cache for users with this role
        self._invalidate_role_cache(role_id)

        return role

    def delete_role(self, role_id: int) -> bool:
        """
        Delete a role.

        Args:
            role_id: Role ID

        Returns:
            True if deleted
        """
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise ValueError(f"Role {role_id} not found")

        if role.is_system_role:
            raise ValueError("Cannot delete system roles")

        # Check if any users have this role
        user_count = self.db.query(UserRoleAssignment).filter(
            UserRoleAssignment.role_id == role_id
        ).count()

        if user_count > 0:
            raise ValueError(f"Cannot delete role with {user_count} assigned users")

        self.db.delete(role)
        self.db.commit()

        return True

    def _assign_permissions_to_role(self, role_id: int, permission_names: List[str]):
        """Assign permissions to a role."""
        for perm_name in permission_names:
            permission = self.db.query(Permission).filter(
                Permission.name == perm_name
            ).first()

            if permission:
                role_perm = RolePermission(
                    role_id=role_id,
                    permission_id=permission.id,
                )
                self.db.add(role_perm)

    # ==================== User Role Assignment ====================

    def assign_role_to_user(
        self,
        user_id: int,
        role_id: int,
        assigned_by_user_id: Optional[int] = None
    ) -> UserRoleAssignment:
        """
        Assign a role to a user.

        Args:
            user_id: User ID
            role_id: Role ID
            assigned_by_user_id: ID of user making assignment

        Returns:
            UserRole assignment
        """
        # Check if already assigned
        existing = self.db.query(UserRoleAssignment).filter(
            and_(
                UserRoleAssignment.user_id == user_id,
                UserRoleAssignment.role_id == role_id
            )
        ).first()

        if existing:
            return existing

        assignment = UserRoleAssignment(
            user_id=user_id,
            role_id=role_id,
            assigned_by_user_id=assigned_by_user_id,
        )
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)

        # Invalidate cache
        if user_id in self._permission_cache:
            del self._permission_cache[user_id]

        return assignment

    def remove_role_from_user(self, user_id: int, role_id: int) -> bool:
        """
        Remove a role from a user.

        Args:
            user_id: User ID
            role_id: Role ID

        Returns:
            True if removed
        """
        assignment = self.db.query(UserRoleAssignment).filter(
            and_(
                UserRoleAssignment.user_id == user_id,
                UserRoleAssignment.role_id == role_id
            )
        ).first()

        if not assignment:
            return False

        self.db.delete(assignment)
        self.db.commit()

        # Invalidate cache
        if user_id in self._permission_cache:
            del self._permission_cache[user_id]

        return True

    def get_user_roles(self, user_id: int) -> List[Role]:
        """Get all roles assigned to a user."""
        assignments = self.db.query(UserRoleAssignment).filter(
            UserRoleAssignment.user_id == user_id
        ).all()

        return [a.role for a in assignments]

    # ==================== Permission Checking ====================

    def get_user_permissions(self, user_id: int, use_cache: bool = True) -> Set[str]:
        """
        Get all permissions for a user (aggregated from all roles).

        Args:
            user_id: User ID
            use_cache: Whether to use cached permissions

        Returns:
            Set of permission names
        """
        if use_cache and user_id in self._permission_cache:
            return self._permission_cache[user_id]

        permissions = set()

        # Get all roles for user
        roles = self.get_user_roles(user_id)

        for role in roles:
            # Get permissions for each role
            role_perms = self.db.query(RolePermission).filter(
                RolePermission.role_id == role.id
            ).all()

            for rp in role_perms:
                permissions.add(rp.permission.name)

        # Cache the permissions
        self._permission_cache[user_id] = permissions

        return permissions

    def has_permission(self, user_id: int, permission_name: str) -> bool:
        """
        Check if a user has a specific permission.

        Args:
            user_id: User ID
            permission_name: Permission to check

        Returns:
            True if user has permission
        """
        permissions = self.get_user_permissions(user_id)
        return permission_name in permissions

    def has_any_permission(self, user_id: int, permission_names: List[str]) -> bool:
        """
        Check if a user has any of the given permissions.

        Args:
            user_id: User ID
            permission_names: List of permissions to check

        Returns:
            True if user has any of the permissions
        """
        permissions = self.get_user_permissions(user_id)
        return bool(permissions.intersection(set(permission_names)))

    def has_all_permissions(self, user_id: int, permission_names: List[str]) -> bool:
        """
        Check if a user has all of the given permissions.

        Args:
            user_id: User ID
            permission_names: List of permissions to check

        Returns:
            True if user has all permissions
        """
        permissions = self.get_user_permissions(user_id)
        return set(permission_names).issubset(permissions)

    def check_permission(
        self,
        user_id: int,
        permission_name: str,
        raise_exception: bool = True
    ) -> bool:
        """
        Check permission and optionally raise an exception.

        Args:
            user_id: User ID
            permission_name: Permission to check
            raise_exception: Whether to raise PermissionError if denied

        Returns:
            True if user has permission

        Raises:
            PermissionError: If user doesn't have permission and raise_exception is True
        """
        has_perm = self.has_permission(user_id, permission_name)

        if not has_perm and raise_exception:
            raise PermissionError(f"User {user_id} does not have permission: {permission_name}")

        return has_perm

    # ==================== Resource-Level Permissions ====================

    def can_access_agent(
        self,
        user_id: int,
        agent_id: int,
        action: str = "read"
    ) -> bool:
        """
        Check if a user can access a specific agent.

        Args:
            user_id: User ID
            agent_id: Agent ID
            action: Action type (read, update, delete, share)

        Returns:
            True if user can access
        """
        permission_name = f"agent:{action}"
        if not self.has_permission(user_id, permission_name):
            return False

        # Get the user and agent
        user = self.db.query(User).filter(User.id == user_id).first()
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()

        if not user or not agent:
            return False

        # Check if same organization
        if user.organization_id != agent.organization_id:
            return False

        # Agent owner always has full access
        if agent.user_id == user_id:
            return True

        # Admins have full access
        if self.has_permission(user_id, "admin:manage_users"):
            return True

        # For shared agents, check if user has read access
        # (Agent sharing would be handled by AgentShare model if implemented)
        if action == "read":
            return True  # All org members can read org agents

        return False

    def can_manage_user(self, admin_user_id: int, target_user_id: int) -> bool:
        """
        Check if a user can manage another user.

        Args:
            admin_user_id: User attempting management
            target_user_id: User being managed

        Returns:
            True if allowed
        """
        if not self.has_permission(admin_user_id, "admin:manage_users"):
            return False

        # Get both users
        admin = self.db.query(User).filter(User.id == admin_user_id).first()
        target = self.db.query(User).filter(User.id == target_user_id).first()

        if not admin or not target:
            return False

        # Must be in same organization
        return admin.organization_id == target.organization_id

    # ==================== Cache Management ====================

    def _invalidate_role_cache(self, role_id: int):
        """Invalidate cache for all users with a specific role."""
        assignments = self.db.query(UserRoleAssignment).filter(
            UserRoleAssignment.role_id == role_id
        ).all()

        for assignment in assignments:
            if assignment.user_id in self._permission_cache:
                del self._permission_cache[assignment.user_id]

    def clear_cache(self):
        """Clear all cached permissions."""
        self._permission_cache.clear()

    def clear_user_cache(self, user_id: int):
        """Clear cached permissions for a specific user."""
        if user_id in self._permission_cache:
            del self._permission_cache[user_id]

    # ==================== Reporting ====================

    def get_permission_report(self, organization_id: int) -> Dict[str, Any]:
        """
        Get a report of permissions usage in an organization.

        Args:
            organization_id: Organization ID

        Returns:
            Permission usage report
        """
        roles = self.get_organization_roles(organization_id)

        report = {
            "total_roles": len(roles),
            "roles": [],
        }

        for role in roles:
            # Count users with this role
            user_count = self.db.query(UserRoleAssignment).filter(
                UserRoleAssignment.role_id == role.id
            ).count()

            # Get permissions
            role_perms = self.db.query(RolePermission).filter(
                RolePermission.role_id == role.id
            ).all()

            report["roles"].append({
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "is_system_role": role.is_system_role,
                "user_count": user_count,
                "permission_count": len(role_perms),
                "permissions": [rp.permission.name for rp in role_perms],
            })

        return report


# Singleton instance
_rbac_service = None


def get_rbac_service(db: Session) -> RBACService:
    """Get RBAC service instance."""
    global _rbac_service
    if _rbac_service is None:
        _rbac_service = RBACService(db)
    else:
        _rbac_service.db = db
    return _rbac_service
