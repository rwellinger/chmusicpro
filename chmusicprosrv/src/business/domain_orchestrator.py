"""Domain Orchestrator - Coordinates domain operations for multi-tenancy"""

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from business.user_auth_service import UserAuthService
from config.settings import JWT_EXPIRATION_HOURS
from db.domain_service import DomainService
from db.models import Domain, DomainMembership, DomainRole, DomainType
from db.user_service import UserService
from utils.logger import logger


domain_service = DomainService()
user_service = UserService()
auth_service = UserAuthService()


class DomainOrchestratorError(Exception):
    """Base exception for domain orchestration errors"""

    pass


class DomainOrchestrator:
    """Orchestrates domain operations (calls domain service)"""

    def create_personal_domain_for_user(self, db: Session, user_id: str, email: str) -> Domain:
        """
        Create a personal domain for a new user with all required memberships.

        Creates:
        1. Personal domain (type=USER, name=user:{email})
        2. Owner membership in personal domain (is_default=true)
        3. Viewer membership in System domain (type=0)
        4. Viewer membership in KI Templates domain (type=1)
        """
        # Create personal domain
        personal_domain = domain_service.create_domain(
            db,
            domain_type=DomainType.USER,
            name=f"user:{email}",
            description=f"Personal domain for {email}",
        )
        personal_domain_id = str(personal_domain.id)

        # Owner membership in personal domain (default)
        domain_service.create_membership(
            db,
            domain_id=personal_domain_id,
            user_id=user_id,
            role=DomainRole.OWNER,
            is_default=True,
        )

        # Viewer membership in System domain
        system_domain = domain_service.get_reserved_domain(db, DomainType.SYSTEM)
        if system_domain:
            domain_service.create_membership(
                db,
                domain_id=str(system_domain.id),
                user_id=user_id,
                role=DomainRole.VIEWER,
                is_default=False,
            )

        # Viewer membership in KI Templates domain
        ki_domain = domain_service.get_reserved_domain(db, DomainType.KI_TEMPLATES)
        if ki_domain:
            domain_service.create_membership(
                db,
                domain_id=str(ki_domain.id),
                user_id=user_id,
                role=DomainRole.VIEWER,
                is_default=False,
            )

        logger.info(
            "Personal domain created with memberships",
            user_id=user_id,
            domain_id=personal_domain_id,
            email=email,
        )
        return personal_domain

    def resolve_active_domain(
        self, db: Session, user_id: str, requested_domain_id: str | None = None
    ) -> tuple[Domain, str]:
        """
        Resolve which domain is active for a user.

        Args:
            db: Database session
            user_id: User UUID as string
            requested_domain_id: Specific domain to activate (optional)

        Returns:
            Tuple of (Domain, role_in_domain)

        Raises:
            DomainOrchestratorError: If domain not found or user not a member
        """
        if requested_domain_id:
            # Verify user is a member of the requested domain
            role = domain_service.get_user_role_in_domain(db, requested_domain_id, user_id)
            if not role:
                raise DomainOrchestratorError("User is not a member of the requested domain")

            domain = domain_service.get_domain_by_id(db, requested_domain_id)
            if not domain:
                raise DomainOrchestratorError("Domain not found")

            return domain, role

        # Fall back to default domain
        default_domain = domain_service.get_default_domain_for_user(db, user_id)
        if not default_domain:
            raise DomainOrchestratorError("No default domain found for user")

        role = domain_service.get_user_role_in_domain(db, str(default_domain.id), user_id)
        return default_domain, role or DomainRole.VIEWER

    def switch_active_domain(self, db: Session, user_id: str, target_domain_id: str) -> tuple[str, str, str, str]:
        """
        Switch the user's active domain.

        Returns:
            Tuple of (token, domain_id, role, expires_at)

        Raises:
            DomainOrchestratorError: If domain not found or user not a member
        """
        # Verify membership
        role = domain_service.get_user_role_in_domain(db, target_domain_id, user_id)
        if not role:
            raise DomainOrchestratorError("User is not a member of the target domain")

        # Verify domain is active
        domain = domain_service.get_domain_by_id(db, target_domain_id)
        if not domain:
            raise DomainOrchestratorError("Domain not found or inactive")

        # Update default: clear all, set new
        domain_service.clear_default_for_user(db, user_id)
        domain_service.set_membership_as_default(db, target_domain_id, user_id)

        # Get user for JWT
        user = user_service.get_user_by_id(db, user_id)
        if not user:
            raise DomainOrchestratorError("User not found")

        # Generate new JWT with updated domain claims
        token = auth_service.generate_jwt_token(
            user_id=str(user.id),
            email=user.email,
            role=user.role,
            active_domain_id=str(domain.id),
            domain_role=role,
        )

        expires_at = (datetime.now(UTC) + timedelta(hours=JWT_EXPIRATION_HOURS)).isoformat()

        logger.info(
            "Domain switched",
            user_id=user_id,
            domain_id=target_domain_id,
            role=role,
        )
        return token, str(domain.id), role, expires_at

    def create_managed_domain(
        self,
        db: Session,
        domain_type: int,
        name: str,
        description: str | None,
        creator_user_id: str,
    ) -> Domain:
        """
        Create a new managed domain (Company or Producer).
        Creator becomes owner.

        Raises:
            DomainOrchestratorError: If type invalid or name not unique
        """
        # Only allow Company(3) and Producer(4)
        if domain_type not in (DomainType.COMPANY, DomainType.PRODUCER):
            raise DomainOrchestratorError("Only Company or Producer domains can be created")

        # Check name uniqueness
        existing = domain_service.get_domain_by_name(db, name)
        if existing:
            raise DomainOrchestratorError(f"Domain name '{name}' is already taken")

        domain = domain_service.create_domain(db, DomainType(domain_type), name, description)

        # Creator becomes owner
        domain_service.create_membership(
            db,
            domain_id=str(domain.id),
            user_id=creator_user_id,
            role=DomainRole.OWNER,
            is_default=False,
        )

        logger.info(
            "Managed domain created",
            domain_id=str(domain.id),
            domain_type=domain_type,
            creator_user_id=creator_user_id,
        )
        return domain

    def add_member_to_domain(self, db: Session, domain_id: str, user_email: str, role: str) -> DomainMembership:
        """
        Add a member to a domain by email.

        Raises:
            DomainOrchestratorError: If user not found, already member, or invalid role
        """
        # Validate role
        valid_roles = [r.value for r in DomainRole]
        if role not in valid_roles:
            raise DomainOrchestratorError(f"Invalid role '{role}'. Must be one of: {', '.join(valid_roles)}")

        # Look up user by email
        user = user_service.get_user_by_email(db, user_email)
        if not user:
            raise DomainOrchestratorError(f"User with email '{user_email}' not found")

        # Check not already member
        existing = domain_service.get_membership(db, domain_id, str(user.id))
        if existing:
            raise DomainOrchestratorError(f"User '{user_email}' is already a member of this domain")

        membership = domain_service.create_membership(
            db, domain_id=domain_id, user_id=str(user.id), role=DomainRole(role)
        )
        logger.info("Member added to domain", domain_id=domain_id, email=user_email, role=role)
        return membership

    def update_member_role(
        self, db: Session, domain_id: str, target_user_id: str, new_role: str, requesting_user_id: str
    ) -> DomainMembership:
        """
        Update a member's role in a domain.

        Raises:
            DomainOrchestratorError: If self-change, invalid role, or membership not found
        """
        if target_user_id == requesting_user_id:
            raise DomainOrchestratorError("Cannot change your own role")

        valid_roles = [r.value for r in DomainRole]
        if new_role not in valid_roles:
            raise DomainOrchestratorError(f"Invalid role '{new_role}'. Must be one of: {', '.join(valid_roles)}")

        membership = domain_service.update_membership_role(db, domain_id, target_user_id, new_role)
        if not membership:
            raise DomainOrchestratorError("Membership not found")

        logger.info("Member role updated", domain_id=domain_id, target_user_id=target_user_id, new_role=new_role)
        return membership

    def remove_member_from_domain(
        self, db: Session, domain_id: str, target_user_id: str, requesting_user_id: str
    ) -> bool:
        """
        Remove a member from a domain.

        Raises:
            DomainOrchestratorError: If self-removal or last owner
        """
        if target_user_id == requesting_user_id:
            raise DomainOrchestratorError("Cannot remove yourself from a domain")

        # Check if target is the last owner
        membership = domain_service.get_membership(db, domain_id, target_user_id)
        if not membership:
            raise DomainOrchestratorError("Membership not found")

        if membership.role == DomainRole.OWNER:
            # Count owners in domain
            members = domain_service.list_members_of_domain(db, domain_id)
            owner_count = sum(1 for m, _ in members if m.role == DomainRole.OWNER)
            if owner_count <= 1:
                raise DomainOrchestratorError("Cannot remove the last owner of a domain")

        result = domain_service.delete_membership(db, domain_id, target_user_id)
        logger.info("Member removed from domain", domain_id=domain_id, target_user_id=target_user_id)
        return result

    def check_domain_permission(
        self, db: Session, domain_id: str, user_id: str, allowed_roles: list[str]
    ) -> str | None:
        """
        Check if user has one of the allowed roles in a specific domain.
        System admins (role in System domain is owner/admin) always pass.

        Returns:
            The user's role if permitted, None if not.
        """
        # Check if user is System admin (always allowed)
        system_domain = domain_service.get_reserved_domain(db, DomainType.SYSTEM)
        if system_domain:
            system_role = domain_service.get_user_role_in_domain(db, str(system_domain.id), user_id)
            if system_role in (DomainRole.OWNER, DomainRole.ADMIN):
                return system_role

        # Check role in the target domain
        role = domain_service.get_user_role_in_domain(db, domain_id, user_id)
        if role and role in allowed_roles:
            return role

        return None
