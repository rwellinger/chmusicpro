"""Controller for system context template management"""

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from business.system_context_template_orchestrator import (
    SystemContextTemplateOrchestrator,
    SystemContextTemplateOrchestratorError,
)
from schemas.system_context_template_schemas import (
    SystemContextTemplateCreate,
    SystemContextTemplateListResponse,
    SystemContextTemplateResponse,
    SystemContextTemplateUpdate,
)
from utils.logger import logger


class SystemContextTemplateController:
    """Controller for system context template HTTP request handling"""

    def __init__(self):
        self.orchestrator = SystemContextTemplateOrchestrator()

    def get_all_templates(self, db: Session) -> tuple[dict[str, Any], int]:
        """Get all system context templates"""
        try:
            templates = self.orchestrator.get_all_templates(db)
            templates_data = [SystemContextTemplateResponse.model_validate(t) for t in templates]
            response = SystemContextTemplateListResponse(templates=templates_data, total=len(templates_data))
            return response.model_dump(), 200

        except SystemContextTemplateOrchestratorError as e:
            logger.error("Orchestrator error retrieving templates", error=str(e))
            return {"error": f"Failed to retrieve templates: {str(e)}"}, 500
        except Exception as e:
            logger.error("Unexpected error retrieving templates", error=str(e), error_type=type(e).__name__)
            return {"error": f"Failed to retrieve templates: {str(e)}"}, 500

    def get_active_templates(self, db: Session) -> tuple[dict[str, Any], int]:
        """Get only active system context templates (for chat dropdown)"""
        try:
            templates = self.orchestrator.get_all_templates(db, active_only=True)
            templates_data = [SystemContextTemplateResponse.model_validate(t) for t in templates]
            response = SystemContextTemplateListResponse(templates=templates_data, total=len(templates_data))
            return response.model_dump(), 200

        except SystemContextTemplateOrchestratorError as e:
            logger.error("Orchestrator error retrieving active templates", error=str(e))
            return {"error": f"Failed to retrieve templates: {str(e)}"}, 500
        except Exception as e:
            logger.error("Unexpected error retrieving active templates", error=str(e), error_type=type(e).__name__)
            return {"error": f"Failed to retrieve templates: {str(e)}"}, 500

    def get_template_by_id(self, db: Session, template_id: UUID) -> tuple[dict[str, Any], int]:
        """Get a specific template by ID"""
        try:
            template = self.orchestrator.get_template_by_id(db, template_id)
            if not template:
                return {"error": f"Template not found: {template_id}"}, 404

            response = SystemContextTemplateResponse.model_validate(template)
            return response.model_dump(), 200

        except SystemContextTemplateOrchestratorError as e:
            logger.error("Orchestrator error retrieving template", template_id=str(template_id), error=str(e))
            return {"error": f"Failed to retrieve template: {str(e)}"}, 500
        except Exception as e:
            logger.error("Unexpected error retrieving template", template_id=str(template_id), error=str(e))
            return {"error": f"Failed to retrieve template: {str(e)}"}, 500

    def create_template(self, db: Session, template_data: SystemContextTemplateCreate) -> tuple[dict[str, Any], int]:
        """Create a new system context template"""
        try:
            template_dict = template_data.model_dump()
            new_template = self.orchestrator.create_template(db, None, template_dict)

            response = SystemContextTemplateResponse.model_validate(new_template)
            return response.model_dump(), 201

        except SystemContextTemplateOrchestratorError as e:
            error_msg = str(e)
            if "already exists" in error_msg.lower():
                return {"error": error_msg}, 409
            logger.error("Orchestrator error creating template", error=error_msg)
            return {"error": f"Failed to create template: {error_msg}"}, 500
        except Exception as e:
            logger.error("Unexpected error creating template", error=str(e), error_type=type(e).__name__)
            return {"error": f"Failed to create template: {str(e)}"}, 500

    def update_template(
        self, db: Session, template_id: UUID, update_data: SystemContextTemplateUpdate
    ) -> tuple[dict[str, Any], int]:
        """Update an existing system context template"""
        try:
            update_dict = update_data.model_dump(exclude_unset=True)
            updated_template = self.orchestrator.update_template(db, template_id, update_dict)

            response = SystemContextTemplateResponse.model_validate(updated_template)
            return response.model_dump(), 200

        except SystemContextTemplateOrchestratorError as e:
            error_msg = str(e)
            if "not found" in error_msg.lower():
                return {"error": f"Template not found: {template_id}"}, 404
            if "already exists" in error_msg.lower():
                return {"error": error_msg}, 409
            logger.error("Orchestrator error updating template", template_id=str(template_id), error=error_msg)
            return {"error": f"Failed to update template: {error_msg}"}, 500
        except Exception as e:
            logger.error("Unexpected error updating template", template_id=str(template_id), error=str(e))
            return {"error": f"Failed to update template: {str(e)}"}, 500

    def delete_template(self, db: Session, template_id: UUID) -> tuple[dict[str, Any], int]:
        """Delete a system context template"""
        try:
            self.orchestrator.delete_template(db, template_id)
            return {"message": f"Template {template_id} deleted"}, 200

        except SystemContextTemplateOrchestratorError as e:
            error_msg = str(e)
            if "not found" in error_msg.lower():
                return {"error": f"Template not found: {template_id}"}, 404
            logger.error("Orchestrator error deleting template", template_id=str(template_id), error=error_msg)
            return {"error": f"Failed to delete template: {error_msg}"}, 500
        except Exception as e:
            logger.error("Unexpected error deleting template", template_id=str(template_id), error=str(e))
            return {"error": f"Failed to delete template: {str(e)}"}, 500
