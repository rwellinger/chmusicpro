"""Domain Orchestrator - Coordinates domain operations for multi-tenancy"""

from sqlalchemy.orm import Session

from db.domain_service import DomainService
from db.models import Domain, DomainRole, DomainType
from utils.logger import logger


domain_service = DomainService()


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
