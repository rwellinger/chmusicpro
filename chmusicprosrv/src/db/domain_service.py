"""
Domain Service for database operations (CRUD only)

Pure database operations - NO business logic
Follows 3-layer architecture: Controller -> Orchestrator -> Service (CRUD)
"""

import uuid

from sqlalchemy.orm import Session

from db.models import Domain, DomainMembership, DomainRole, DomainType, User
from utils.logger import logger


class DomainService:
    """Domain database operations (CRUD only)"""

    def create_domain(
        self,
        db: Session,
        domain_type: DomainType,
        name: str,
        description: str | None = None,
    ) -> Domain:
        """Create a new domain"""
        domain = Domain(
            id=uuid.uuid4(),
            type=int(domain_type),
            name=name,
            description=description,
        )
        db.add(domain)
        db.flush()
        logger.info("Domain created", domain_id=str(domain.id), name=name, type=int(domain_type))
        return domain

    def get_domain_by_id(self, db: Session, domain_id: str) -> Domain | None:
        """Get domain by ID"""
        try:
            domain_uuid = uuid.UUID(domain_id)
            return db.query(Domain).filter(Domain.id == domain_uuid, Domain.is_active).first()
        except (ValueError, TypeError):
            logger.warning("Invalid domain ID format", domain_id=domain_id)
            return None

    def get_domain_by_name(self, db: Session, name: str) -> Domain | None:
        """Get domain by name"""
        return db.query(Domain).filter(Domain.name == name, Domain.is_active).first()

    def get_domains_by_type(self, db: Session, domain_type: DomainType) -> list[Domain]:
        """Get all domains of a specific type"""
        return db.query(Domain).filter(Domain.type == int(domain_type), Domain.is_active).all()

    def list_domains_for_user(self, db: Session, user_id: str) -> list[tuple[Domain, DomainMembership]]:
        """Get all domains a user is a member of, with their membership info"""
        try:
            user_uuid = uuid.UUID(user_id)
            return (
                db.query(Domain, DomainMembership)
                .join(DomainMembership, Domain.id == DomainMembership.domain_id)
                .filter(DomainMembership.user_id == user_uuid, Domain.is_active)
                .all()
            )
        except (ValueError, TypeError):
            logger.warning("Invalid user ID format", user_id=user_id)
            return []

    def create_membership(
        self,
        db: Session,
        domain_id: str,
        user_id: str,
        role: DomainRole = DomainRole.MEMBER,
        is_default: bool = False,
    ) -> DomainMembership:
        """Create a domain membership for a user"""
        membership = DomainMembership(
            id=uuid.uuid4(),
            domain_id=uuid.UUID(domain_id),
            user_id=uuid.UUID(user_id),
            role=str(role),
            is_default=is_default,
        )
        db.add(membership)
        db.flush()
        logger.info(
            "Domain membership created",
            domain_id=domain_id,
            user_id=user_id,
            role=str(role),
            is_default=is_default,
        )
        return membership

    def get_membership(self, db: Session, domain_id: str, user_id: str) -> DomainMembership | None:
        """Get a specific membership"""
        try:
            return (
                db.query(DomainMembership)
                .filter(
                    DomainMembership.domain_id == uuid.UUID(domain_id),
                    DomainMembership.user_id == uuid.UUID(user_id),
                )
                .first()
            )
        except (ValueError, TypeError):
            return None

    def get_default_domain_for_user(self, db: Session, user_id: str) -> Domain | None:
        """Get the user's default domain"""
        try:
            user_uuid = uuid.UUID(user_id)
            result = (
                db.query(Domain)
                .join(DomainMembership, Domain.id == DomainMembership.domain_id)
                .filter(
                    DomainMembership.user_id == user_uuid,
                    DomainMembership.is_default.is_(True),
                    Domain.is_active,
                )
                .first()
            )
            return result
        except (ValueError, TypeError):
            logger.warning("Invalid user ID format", user_id=user_id)
            return None

    def get_user_role_in_domain(self, db: Session, domain_id: str, user_id: str) -> str | None:
        """Get user's role in a specific domain, or None if not a member"""
        membership = self.get_membership(db, domain_id, user_id)
        return membership.role if membership else None

    def get_reserved_domain(self, db: Session, domain_type: DomainType) -> Domain | None:
        """Get a reserved domain (System or KI Templates) by type"""
        return db.query(Domain).filter(Domain.type == int(domain_type)).first()

    def list_members_of_domain(self, db: Session, domain_id: str) -> list[tuple[DomainMembership, User]]:
        """Get all members of a domain with their user info"""
        try:
            domain_uuid = uuid.UUID(domain_id)
            return (
                db.query(DomainMembership, User)
                .join(User, DomainMembership.user_id == User.id)
                .filter(DomainMembership.domain_id == domain_uuid)
                .all()
            )
        except (ValueError, TypeError):
            logger.warning("Invalid domain ID format", domain_id=domain_id)
            return []

    def update_domain(self, db: Session, domain_id: str, update_data: dict) -> Domain | None:
        """Update domain fields"""
        domain = self.get_domain_by_id(db, domain_id)
        if not domain:
            return None
        for key, value in update_data.items():
            if hasattr(domain, key):
                setattr(domain, key, value)
        db.flush()
        logger.info("Domain updated", domain_id=domain_id, fields=list(update_data.keys()))
        return domain

    def deactivate_domain(self, db: Session, domain_id: str) -> Domain | None:
        """Deactivate a domain (soft delete)"""
        domain = self.get_domain_by_id(db, domain_id)
        if not domain:
            return None
        domain.is_active = False
        db.flush()
        logger.info("Domain deactivated", domain_id=domain_id)
        return domain

    def update_membership_role(
        self, db: Session, domain_id: str, user_id: str, new_role: str
    ) -> DomainMembership | None:
        """Update a member's role in a domain"""
        membership = self.get_membership(db, domain_id, user_id)
        if not membership:
            return None
        membership.role = new_role
        db.flush()
        logger.info("Membership role updated", domain_id=domain_id, user_id=user_id, new_role=new_role)
        return membership

    def delete_membership(self, db: Session, domain_id: str, user_id: str) -> bool:
        """Remove a member from a domain"""
        membership = self.get_membership(db, domain_id, user_id)
        if not membership:
            return False
        db.delete(membership)
        db.flush()
        logger.info("Membership deleted", domain_id=domain_id, user_id=user_id)
        return True

    def clear_default_for_user(self, db: Session, user_id: str) -> None:
        """Clear all is_default flags for a user"""
        try:
            user_uuid = uuid.UUID(user_id)
            db.query(DomainMembership).filter(
                DomainMembership.user_id == user_uuid,
                DomainMembership.is_default.is_(True),
            ).update({"is_default": False})
            db.flush()
        except (ValueError, TypeError):
            logger.warning("Invalid user ID format", user_id=user_id)

    def set_membership_as_default(self, db: Session, domain_id: str, user_id: str) -> DomainMembership | None:
        """Set a specific membership as the user's default"""
        membership = self.get_membership(db, domain_id, user_id)
        if not membership:
            return None
        membership.is_default = True
        db.flush()
        logger.info("Membership set as default", domain_id=domain_id, user_id=user_id)
        return membership
