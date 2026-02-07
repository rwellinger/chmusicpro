"""Controller for prompt template management - Uses Orchestrator Pattern"""

from typing import Any

from sqlalchemy.orm import Session

from business.prompt_template_orchestrator import (
    PromptTemplateOrchestrator,
    PromptTemplateOrchestratorError,
)
from business.prompt_template_validator import PromptTemplateValidationError
from schemas.prompt_schemas import (
    PromptCategoryResponse,
    PromptTemplateCreate,
    PromptTemplateResponse,
    PromptTemplatesGroupedResponse,
    PromptTemplateUpdate,
)
from utils.logger import logger


class PromptController:
    """Controller for prompt template HTTP request handling (uses orchestrator)"""

    def __init__(self):
        self.orchestrator = PromptTemplateOrchestrator()

    def get_all_templates(self, db: Session) -> tuple[dict[str, Any], int]:
        """Get all prompt templates grouped by category and action"""
        try:
            templates = self.orchestrator.get_all_templates(db)

            # Filter active templates and group by category/action
            grouped: dict[str, dict[str, Any]] = {}
            for template in templates:
                if not template.active:
                    continue

                if template.category not in grouped:
                    grouped[template.category] = {}

                template_data = PromptTemplateResponse.model_validate(template)
                grouped[template.category][template.action] = template_data

            logger.info("Retrieved all templates", total_count=len(templates), category_count=len(grouped))

            response = PromptTemplatesGroupedResponse(categories=grouped)
            return response.model_dump(), 200

        except PromptTemplateOrchestratorError as e:
            logger.error("Orchestrator error retrieving templates", error=str(e), error_type=type(e).__name__)
            return {"error": f"Failed to retrieve templates: {str(e)}"}, 500
        except Exception as e:
            logger.error("Unexpected error retrieving templates", error=str(e), error_type=type(e).__name__)
            return {"error": f"Failed to retrieve templates: {str(e)}"}, 500

    def get_category_templates(self, db: Session, category: str) -> tuple[dict[str, Any], int]:
        """Get all templates for a specific category"""
        try:
            templates = self.orchestrator.get_templates_by_category(db, category)

            # Filter active templates
            active_templates = [t for t in templates if t.active]

            if not active_templates:
                logger.warning("No active templates found for category", category=category)
                return {"error": f"No templates found for category '{category}'"}, 404

            # Group by action
            templates_by_action: dict[str, PromptTemplateResponse] = {}
            for template in active_templates:
                template_data = PromptTemplateResponse.model_validate(template)
                templates_by_action[template.action] = template_data

            logger.info("Retrieved category templates", category=category, count=len(active_templates))

            response = PromptCategoryResponse(category=category, templates=templates_by_action)
            return response.model_dump(), 200

        except PromptTemplateOrchestratorError as e:
            logger.error(
                "Orchestrator error retrieving category templates",
                category=category,
                error=str(e),
                error_type=type(e).__name__,
            )
            return {"error": f"Failed to retrieve category templates: {str(e)}"}, 500
        except Exception as e:
            logger.error(
                "Unexpected error retrieving category templates",
                category=category,
                error=str(e),
                error_type=type(e).__name__,
            )
            return {"error": f"Failed to retrieve category templates: {str(e)}"}, 500

    def get_specific_template(self, db: Session, category: str, action: str) -> tuple[dict[str, Any], int]:
        """Get a specific template by category and action"""
        try:
            template = self.orchestrator.get_template_by_category_action(db, category, action)

            if not template:
                logger.warning("Template not found", category=category, action=action)
                return {"error": f"Template not found for category '{category}' and action '{action}'"}, 404

            if not template.active:
                logger.warning("Template is inactive", category=category, action=action, template_id=template.id)
                return {"error": f"Template not found for category '{category}' and action '{action}'"}, 404

            logger.info(
                "Retrieved template",
                category=category,
                action=action,
                template_id=template.id,
                model=template.model,
                temperature=template.temperature,
                max_tokens=template.max_tokens,
                version=template.version,
            )

            response = PromptTemplateResponse.model_validate(template)
            return response.model_dump(), 200

        except PromptTemplateOrchestratorError as e:
            logger.error(
                "Orchestrator error retrieving template",
                category=category,
                action=action,
                error=str(e),
                error_type=type(e).__name__,
            )
            return {"error": f"Failed to retrieve template: {str(e)}"}, 500
        except Exception as e:
            logger.error(
                "Unexpected error retrieving template",
                category=category,
                action=action,
                error=str(e),
                error_type=type(e).__name__,
            )
            return {"error": f"Failed to retrieve template: {str(e)}"}, 500

    def update_template(
        self, db: Session, category: str, action: str, update_data: PromptTemplateUpdate
    ) -> tuple[dict[str, Any], int]:
        """Update an existing template with automatic version increment"""
        try:
            # Convert Pydantic model to dict (exclude unset fields)
            update_dict = update_data.model_dump(exclude_unset=True)

            # Orchestrator handles validation + version increment
            updated_template = self.orchestrator.update_template(db, category, action, update_dict)

            logger.info(
                "Template updated",
                category=category,
                action=action,
                template_id=updated_template.id,
                new_version=updated_template.version,
                fields_updated=list(update_dict.keys()),
            )

            response = PromptTemplateResponse.model_validate(updated_template)
            return response.model_dump(), 200

        except PromptTemplateValidationError as e:
            logger.warning("Validation error updating template", category=category, action=action, error=str(e))
            return {"error": f"Validation error: {str(e)}"}, 400
        except PromptTemplateOrchestratorError as e:
            error_msg = str(e)
            if "not found" in error_msg.lower():
                logger.warning("Template not found for update", category=category, action=action)
                return {"error": f"Template not found for category '{category}' and action '{action}'"}, 404
            logger.error(
                "Orchestrator error updating template",
                category=category,
                action=action,
                error=error_msg,
                error_type=type(e).__name__,
            )
            return {"error": f"Failed to update template: {error_msg}"}, 500
        except Exception as e:
            logger.error(
                "Unexpected error updating template",
                category=category,
                action=action,
                error=str(e),
                error_type=type(e).__name__,
            )
            return {"error": f"Failed to update template: {str(e)}"}, 500

    def create_template(self, db: Session, template_data: PromptTemplateCreate) -> tuple[dict[str, Any], int]:
        """Create a new prompt template"""
        try:
            # Convert Pydantic model to dict
            template_dict = template_data.model_dump()

            # Orchestrator handles validation + creation
            new_template = self.orchestrator.create_template(db, template_dict)

            logger.info(
                "Template created",
                category=new_template.category,
                action=new_template.action,
                template_id=new_template.id,
                version=new_template.version,
            )

            response = PromptTemplateResponse.model_validate(new_template)
            return response.model_dump(), 201

        except PromptTemplateValidationError as e:
            logger.warning(
                "Validation error creating template",
                category=template_data.category,
                action=template_data.action,
                error=str(e),
            )
            return {"error": f"Validation error: {str(e)}"}, 400
        except PromptTemplateOrchestratorError as e:
            error_msg = str(e)
            if "already exists" in error_msg.lower():
                logger.warning("Template already exists", category=template_data.category, action=template_data.action)
                return {
                    "error": f"Template already exists for category '{template_data.category}' and action '{template_data.action}'"
                }, 409
            logger.error(
                "Orchestrator error creating template",
                category=template_data.category,
                action=template_data.action,
                error=error_msg,
                error_type=type(e).__name__,
            )
            return {"error": f"Failed to create template: {error_msg}"}, 500
        except Exception as e:
            logger.error(
                "Unexpected error creating template",
                category=template_data.category,
                action=template_data.action,
                error=str(e),
                error_type=type(e).__name__,
            )
            return {"error": f"Failed to create template: {str(e)}"}, 500

    def delete_template(self, db: Session, category: str, action: str) -> tuple[dict[str, Any], int]:
        """Soft delete a template (set active=False via orchestrator)"""
        try:
            # Orchestrator handles deletion
            self.orchestrator.delete_template(db, category, action)

            logger.info("Template deleted", category=category, action=action)

            return {"message": f"Template for category '{category}' and action '{action}' has been deactivated"}, 200

        except PromptTemplateOrchestratorError as e:
            error_msg = str(e)
            if "not found" in error_msg.lower():
                logger.warning("Template not found for deletion", category=category, action=action)
                return {"error": f"Template not found for category '{category}' and action '{action}'"}, 404
            logger.error(
                "Orchestrator error deleting template",
                category=category,
                action=action,
                error=error_msg,
                error_type=type(e).__name__,
            )
            return {"error": f"Failed to delete template: {error_msg}"}, 500
        except Exception as e:
            logger.error(
                "Unexpected error deleting template",
                category=category,
                action=action,
                error=str(e),
                error_type=type(e).__name__,
            )
            return {"error": f"Failed to delete template: {str(e)}"}, 500
