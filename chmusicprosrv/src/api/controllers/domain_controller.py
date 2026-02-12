"""Controller for domain management"""

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from business.domain_orchestrator import DomainOrchestrator, DomainOrchestratorError
from db.models import DomainType
from schemas.domain_schemas import (
    DomainCreateRequest,
    DomainListResponse,
    DomainMemberAddRequest,
    DomainMemberListResponse,
    DomainMemberResponse,
    DomainMemberUpdateRequest,
    DomainResponse,
    DomainSwitchRequest,
    DomainSwitchResponse,
    DomainUpdateRequest,
    DomainWithRoleResponse,
)
from utils.logger import logger


orchestrator = DomainOrchestrator()


class DomainController:
    """Controller for domain operations"""

    @staticmethod
    def list_user_domains(db: Session, user_id: str) -> tuple[dict[str, Any], int]:
        """List all domains the user is a member of"""
        try:
            from db.domain_service import DomainService

            svc = DomainService()
            domains_with_memberships = svc.list_domains_for_user(db, user_id)

            # System admins see all domains, normal users only non-reserved ones
            reserved_types = {int(DomainType.SYSTEM), int(DomainType.KI_TEMPLATES)}
            system_role = svc.get_user_role_in_domain(
                db, str(svc.get_reserved_domain(db, DomainType.SYSTEM).id), user_id
            )
            is_system_admin = system_role in ("admin", "owner")

            domain_responses = []
            for domain, membership in domains_with_memberships:
                if not is_system_admin and domain.type in reserved_types:
                    continue
                domain_responses.append(
                    DomainWithRoleResponse(
                        domain=DomainResponse.model_validate(domain),
                        role=membership.role,
                        is_default=membership.is_default,
                    )
                )

            response = DomainListResponse(domains=domain_responses)
            return response.model_dump(), 200

        except Exception as e:
            logger.error("domain_list_error", error=str(e), error_type=type(e).__name__)
            return {"error": f"Failed to list domains: {str(e)}"}, 500

    @staticmethod
    def get_domain_detail(db: Session, domain_id: str, user_id: str) -> tuple[dict[str, Any], int]:
        """Get domain detail (user must be a member)"""
        try:
            try:
                UUID(domain_id)
            except ValueError:
                return {"error": "Invalid domain ID format"}, 400

            # Check membership via orchestrator
            role = orchestrator.check_domain_permission(db, domain_id, user_id, ["owner", "admin", "member", "viewer"])
            if not role:
                return {"error": "Not a member of this domain"}, 403

            from db.domain_service import DomainService

            svc = DomainService()
            domain = svc.get_domain_by_id(db, domain_id)
            if not domain:
                return {"error": "Domain not found"}, 404

            membership = svc.get_membership(db, domain_id, user_id)
            response = DomainWithRoleResponse(
                domain=DomainResponse.model_validate(domain),
                role=membership.role if membership else role,
                is_default=membership.is_default if membership else False,
            )
            return {"data": response.model_dump()}, 200

        except Exception as e:
            logger.error("domain_detail_error", domain_id=domain_id, error=str(e), error_type=type(e).__name__)
            return {"error": f"Failed to get domain: {str(e)}"}, 500

    @staticmethod
    def create_domain(db: Session, user_id: str, data: DomainCreateRequest) -> tuple[dict[str, Any], int]:
        """Create a new managed domain"""
        try:
            domain = orchestrator.create_managed_domain(
                db,
                domain_type=data.type,
                name=data.name,
                description=data.description,
                creator_user_id=user_id,
            )
            response = DomainResponse.model_validate(domain)
            return {"data": response.model_dump(), "message": "Domain created successfully"}, 201

        except DomainOrchestratorError as e:
            return {"error": str(e)}, 400
        except Exception as e:
            logger.error("domain_create_error", error=str(e), error_type=type(e).__name__)
            return {"error": f"Failed to create domain: {str(e)}"}, 500

    @staticmethod
    def update_domain(
        db: Session, domain_id: str, user_id: str, data: DomainUpdateRequest
    ) -> tuple[dict[str, Any], int]:
        """Update a domain (owner/admin of domain or system admin)"""
        try:
            try:
                UUID(domain_id)
            except ValueError:
                return {"error": "Invalid domain ID format"}, 400

            # Check permission
            role = orchestrator.check_domain_permission(db, domain_id, user_id, ["owner", "admin"])
            if not role:
                return {"error": "Insufficient permissions"}, 403

            update_dict = {field: getattr(data, field) for field in data.model_fields_set}
            if not update_dict:
                return {"error": "No fields to update"}, 400

            from db.domain_service import DomainService

            svc = DomainService()
            domain = svc.update_domain(db, domain_id, update_dict)
            if not domain:
                return {"error": "Domain not found"}, 404

            response = DomainResponse.model_validate(domain)
            return {"data": response.model_dump(), "message": "Domain updated successfully"}, 200

        except Exception as e:
            logger.error("domain_update_error", domain_id=domain_id, error=str(e), error_type=type(e).__name__)
            return {"error": f"Failed to update domain: {str(e)}"}, 500

    @staticmethod
    def deactivate_domain(db: Session, domain_id: str) -> tuple[dict[str, Any], int]:
        """Deactivate a domain (system admin only - enforced by decorator)"""
        try:
            try:
                UUID(domain_id)
            except ValueError:
                return {"error": "Invalid domain ID format"}, 400

            from db.domain_service import DomainService
            from db.models import DomainType

            svc = DomainService()
            domain = svc.get_domain_by_id(db, domain_id)
            if not domain:
                return {"error": "Domain not found"}, 404

            if domain.type in (DomainType.SYSTEM, DomainType.KI_TEMPLATES):
                return {"error": "Reserved domains cannot be deactivated"}, 403

            deactivated = svc.deactivate_domain(db, domain_id)
            if not deactivated:
                return {"error": "Failed to deactivate domain"}, 500

            return {"message": "Domain deactivated successfully"}, 200

        except Exception as e:
            logger.error("domain_deactivate_error", domain_id=domain_id, error=str(e), error_type=type(e).__name__)
            return {"error": f"Failed to deactivate domain: {str(e)}"}, 500

    @staticmethod
    def switch_domain(db: Session, user_id: str, data: DomainSwitchRequest) -> tuple[dict[str, Any], int]:
        """Switch active domain for user"""
        try:
            token, domain_id, role, expires_at = orchestrator.switch_active_domain(db, user_id, data.domain_id)

            from db.domain_service import DomainService

            svc = DomainService()
            domain = svc.get_domain_by_id(db, domain_id)
            membership = svc.get_membership(db, domain_id, user_id)

            response = DomainSwitchResponse(
                token=token,
                domain=DomainWithRoleResponse(
                    domain=DomainResponse.model_validate(domain),
                    role=role,
                    is_default=membership.is_default if membership else True,
                ),
                expires_at=expires_at,
            )
            return response.model_dump(), 200

        except DomainOrchestratorError as e:
            return {"error": str(e)}, 400
        except Exception as e:
            logger.error("domain_switch_error", error=str(e), error_type=type(e).__name__)
            return {"error": f"Failed to switch domain: {str(e)}"}, 500

    @staticmethod
    def list_domain_members(db: Session, domain_id: str, user_id: str) -> tuple[dict[str, Any], int]:
        """List members of a domain (owner/admin or system admin)"""
        try:
            try:
                UUID(domain_id)
            except ValueError:
                return {"error": "Invalid domain ID format"}, 400

            role = orchestrator.check_domain_permission(db, domain_id, user_id, ["owner", "admin"])
            if not role:
                return {"error": "Insufficient permissions"}, 403

            from db.domain_service import DomainService

            svc = DomainService()
            members_data = svc.list_members_of_domain(db, domain_id)

            members = []
            for membership, user in members_data:
                members.append(
                    DomainMemberResponse(
                        membership_id=str(membership.id),
                        user_id=str(membership.user_id),
                        email=user.email,
                        first_name=user.first_name,
                        last_name=user.last_name,
                        role=membership.role,
                        is_default=membership.is_default,
                        created_at=membership.created_at,
                    )
                )

            response = DomainMemberListResponse(members=members)
            return response.model_dump(), 200

        except Exception as e:
            logger.error("domain_members_error", domain_id=domain_id, error=str(e), error_type=type(e).__name__)
            return {"error": f"Failed to list members: {str(e)}"}, 500

    @staticmethod
    def add_domain_member(
        db: Session, domain_id: str, user_id: str, data: DomainMemberAddRequest
    ) -> tuple[dict[str, Any], int]:
        """Add a member to a domain (owner/admin or system admin)"""
        try:
            try:
                UUID(domain_id)
            except ValueError:
                return {"error": "Invalid domain ID format"}, 400

            role = orchestrator.check_domain_permission(db, domain_id, user_id, ["owner", "admin"])
            if not role:
                return {"error": "Insufficient permissions"}, 403

            membership = orchestrator.add_member_to_domain(db, domain_id, data.email, data.role)
            return {"message": f"Member '{data.email}' added successfully", "membership_id": str(membership.id)}, 201

        except DomainOrchestratorError as e:
            return {"error": str(e)}, 400
        except Exception as e:
            logger.error("domain_add_member_error", domain_id=domain_id, error=str(e), error_type=type(e).__name__)
            return {"error": f"Failed to add member: {str(e)}"}, 500

    @staticmethod
    def update_domain_member(
        db: Session,
        domain_id: str,
        target_user_id: str,
        data: DomainMemberUpdateRequest,
        requesting_user_id: str,
    ) -> tuple[dict[str, Any], int]:
        """Update a member's role (owner/admin or system admin)"""
        try:
            try:
                UUID(domain_id)
                UUID(target_user_id)
            except ValueError:
                return {"error": "Invalid ID format"}, 400

            role = orchestrator.check_domain_permission(db, domain_id, requesting_user_id, ["owner", "admin"])
            if not role:
                return {"error": "Insufficient permissions"}, 403

            orchestrator.update_member_role(db, domain_id, target_user_id, data.role, requesting_user_id)
            return {"message": "Member role updated successfully"}, 200

        except DomainOrchestratorError as e:
            return {"error": str(e)}, 400
        except Exception as e:
            logger.error(
                "domain_update_member_error",
                domain_id=domain_id,
                target_user_id=target_user_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            return {"error": f"Failed to update member: {str(e)}"}, 500

    @staticmethod
    def remove_domain_member(
        db: Session,
        domain_id: str,
        target_user_id: str,
        requesting_user_id: str,
    ) -> tuple[dict[str, Any], int]:
        """Remove a member from a domain (owner/admin or system admin)"""
        try:
            try:
                UUID(domain_id)
                UUID(target_user_id)
            except ValueError:
                return {"error": "Invalid ID format"}, 400

            role = orchestrator.check_domain_permission(db, domain_id, requesting_user_id, ["owner", "admin"])
            if not role:
                return {"error": "Insufficient permissions"}, 403

            orchestrator.remove_member_from_domain(db, domain_id, target_user_id, requesting_user_id)
            return {"message": "Member removed successfully"}, 200

        except DomainOrchestratorError as e:
            return {"error": str(e)}, 400
        except Exception as e:
            logger.error(
                "domain_remove_member_error",
                domain_id=domain_id,
                target_user_id=target_user_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            return {"error": f"Failed to remove member: {str(e)}"}, 500
