"""System Context Template Orchestrator - Coordinates template operations

Orchestrator Layer - Coordinates services only (NOT testable per CLAUDE.md)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from db.system_context_template_service import SystemContextTemplateService
from utils.logger import logger


if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class SystemContextTemplateOrchestratorError(Exception):
    """Base exception for system context template orchestration errors"""

    pass


class SystemContextTemplateOrchestrator:
    """Orchestrates system context template operations"""

    def __init__(self):
        self.service = SystemContextTemplateService()

    def get_all_templates(self, db: Session, domain_id: UUID | None = None, active_only: bool = False) -> list[Any]:
        try:
            return self.service.get_all_templates(db, domain_id=domain_id, active_only=active_only)
        except Exception as e:
            logger.error("Failed to retrieve system context templates", error=str(e), error_type=type(e).__name__)
            raise SystemContextTemplateOrchestratorError(f"Failed to retrieve templates: {e}") from e

    def get_template_by_id(self, db: Session, template_id: UUID) -> Any | None:
        try:
            return self.service.get_template_by_id(db, template_id)
        except Exception as e:
            logger.error(
                "Failed to retrieve system context template",
                template_id=str(template_id),
                error=str(e),
                error_type=type(e).__name__,
            )
            raise SystemContextTemplateOrchestratorError(f"Failed to retrieve template: {e}") from e

    def create_template(self, db: Session, domain_id: UUID | None, template_data: dict[str, Any]) -> Any:
        try:
            # Check name uniqueness within domain
            existing = self.service.get_template_by_name(db, domain_id, template_data["name"])
            if existing:
                raise SystemContextTemplateOrchestratorError(
                    f"Template with name '{template_data['name']}' already exists"
                )

            if domain_id:
                template_data["domain_id"] = domain_id

            template = self.service.create_template(db, template_data)
            if not template:
                raise SystemContextTemplateOrchestratorError("Failed to create template")
            return template

        except SystemContextTemplateOrchestratorError:
            raise
        except Exception as e:
            logger.error(
                "Template creation failed",
                name=template_data.get("name"),
                error=str(e),
                error_type=type(e).__name__,
            )
            raise SystemContextTemplateOrchestratorError(f"Failed to create template: {e}") from e

    def update_template(self, db: Session, template_id: UUID, update_data: dict[str, Any]) -> Any:
        try:
            template = self.service.get_template_by_id(db, template_id)
            if not template:
                raise SystemContextTemplateOrchestratorError(f"Template not found: {template_id}")

            # Check name uniqueness if name is being changed
            if "name" in update_data and update_data["name"] != template.name:
                existing = self.service.get_template_by_name(db, template.domain_id, update_data["name"])
                if existing:
                    raise SystemContextTemplateOrchestratorError(
                        f"Template with name '{update_data['name']}' already exists"
                    )

            updated = self.service.update_template(db, template_id, update_data)
            if not updated:
                raise SystemContextTemplateOrchestratorError("Failed to update template")
            return updated

        except SystemContextTemplateOrchestratorError:
            raise
        except Exception as e:
            logger.error(
                "Template update failed",
                template_id=str(template_id),
                error=str(e),
                error_type=type(e).__name__,
            )
            raise SystemContextTemplateOrchestratorError(f"Failed to update template: {e}") from e

    def delete_template(self, db: Session, template_id: UUID) -> bool:
        try:
            deleted = self.service.delete_template(db, template_id)
            if not deleted:
                raise SystemContextTemplateOrchestratorError(f"Template not found: {template_id}")
            return True

        except SystemContextTemplateOrchestratorError:
            raise
        except Exception as e:
            logger.error(
                "Template deletion failed",
                template_id=str(template_id),
                error=str(e),
                error_type=type(e).__name__,
            )
            raise SystemContextTemplateOrchestratorError(f"Failed to delete template: {e}") from e
