"""Prompt Template Orchestrator - Coordinates template operations (no testable business logic)

Orchestrator Layer - Coordinates services only (NOT testable per CLAUDE.md)
"""

from typing import Any

from sqlalchemy.orm import Session

from business.prompt_template_processor import PromptTemplateProcessor
from business.prompt_template_validator import (
    PromptTemplateValidationError,
    PromptTemplateValidator,
)
from db.prompt_template_service import PromptTemplateService
from utils.logger import logger


class PromptTemplateOrchestratorError(Exception):
    """Base exception for prompt template orchestration errors"""

    pass


class PromptTemplateOrchestrator:
    """
    Orchestrates prompt template operations (calls validator + processor + repository)

    NOT testable - pure coordination layer (per CLAUDE.md architecture)
    """

    def __init__(self):
        self.service = PromptTemplateService()

    def get_all_templates(self, db: Session) -> list[Any]:
        """
        Get all prompt templates from database.

        Coordination only - calls repository service.

        Args:
            db: Database session

        Returns:
            List of PromptTemplate instances

        Raises:
            PromptTemplateOrchestratorError: If retrieval fails
        """
        try:
            templates = self.service.get_all_templates(db)
            return templates

        except Exception as e:
            logger.error("Failed to retrieve all templates", error=str(e), error_type=type(e).__name__)
            raise PromptTemplateOrchestratorError(f"Failed to retrieve templates: {e}") from e

    def get_templates_by_category(self, db: Session, category: str) -> list[Any]:
        """
        Get all templates for a specific category.

        Coordination only - calls repository service.

        Args:
            db: Database session
            category: Template category

        Returns:
            List of PromptTemplate instances for category

        Raises:
            PromptTemplateOrchestratorError: If retrieval fails
        """
        try:
            templates = self.service.get_templates_by_category(db, category)
            return templates

        except Exception as e:
            logger.error(
                "Failed to retrieve category templates", category=category, error=str(e), error_type=type(e).__name__
            )
            raise PromptTemplateOrchestratorError(f"Failed to retrieve category templates: {e}") from e

    def get_template_by_category_action(self, db: Session, category: str, action: str) -> Any | None:
        """
        Get specific template by category and action.

        Coordination only - calls repository service.

        Args:
            db: Database session
            category: Template category
            action: Template action

        Returns:
            PromptTemplate instance if found, None otherwise

        Raises:
            PromptTemplateOrchestratorError: If retrieval fails
        """
        try:
            template = self.service.get_template_by_category_action(db, category, action)
            return template

        except Exception as e:
            logger.error(
                "Failed to retrieve template",
                category=category,
                action=action,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise PromptTemplateOrchestratorError(f"Failed to retrieve template: {e}") from e

    def create_template(self, db: Session, template_data: dict[str, Any]) -> Any:
        """
        Create new template with validation.

        Coordinates: Validator → Repository

        Args:
            db: Database session
            template_data: Dictionary with template fields
                Required: category, action, pre_condition, post_condition
                Optional: description, version, model, temperature, max_tokens

        Returns:
            Created PromptTemplate instance

        Raises:
            PromptTemplateValidationError: If validation fails
            PromptTemplateOrchestratorError: If creation fails
        """
        try:
            # Step 1: Validate required fields
            PromptTemplateValidator.validate_category_action_format(
                template_data.get("category", ""), template_data.get("action", "")
            )

            # Step 2: Check if template already exists
            if self.service.template_exists(db, template_data["category"], template_data["action"]):
                raise PromptTemplateOrchestratorError(
                    f"Template already exists for category '{template_data['category']}' and action '{template_data['action']}'"
                )

            # Step 4: Create template via repository
            template = self.service.create_template(db, template_data)

            if not template:
                raise PromptTemplateOrchestratorError("Failed to create template")

            return template

        except PromptTemplateValidationError:
            # Re-raise validation errors as-is
            raise
        except PromptTemplateOrchestratorError:
            # Re-raise orchestrator errors as-is
            raise
        except Exception as e:
            logger.error(
                "Template creation failed",
                category=template_data.get("category"),
                action=template_data.get("action"),
                error=str(e),
                error_type=type(e).__name__,
            )
            raise PromptTemplateOrchestratorError(f"Failed to create template: {e}") from e

    def update_template(self, db: Session, category: str, action: str, update_data: dict[str, Any]) -> Any:
        """
        Update existing template with validation and version increment.

        Coordinates: Validator → Processor (version) → Repository

        Args:
            db: Database session
            category: Template category to update
            action: Template action to update
            update_data: Dictionary with fields to update

        Returns:
            Updated PromptTemplate instance

        Raises:
            PromptTemplateValidationError: If validation fails
            PromptTemplateOrchestratorError: If update fails
        """
        try:
            # Step 1: Get current template
            template = self.service.get_template_by_category_action(db, category, action)

            if not template:
                raise PromptTemplateOrchestratorError(
                    f"Template not found for category '{category}' and action '{action}'"
                )

            # Step 2: Auto-increment version using validator
            current_version = template.version
            new_version = PromptTemplateValidator.validate_version_increment(current_version)
            update_data["version"] = new_version

            # Step 4: Update via repository
            updated_template = self.service.update_template(db, category, action, update_data)

            if not updated_template:
                raise PromptTemplateOrchestratorError("Failed to update template")

            return updated_template

        except PromptTemplateValidationError:
            # Re-raise validation errors as-is
            raise
        except PromptTemplateOrchestratorError:
            # Re-raise orchestrator errors as-is
            raise
        except Exception as e:
            logger.error(
                "Template update failed",
                category=category,
                action=action,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise PromptTemplateOrchestratorError(f"Failed to update template: {e}") from e

    def delete_template(self, db: Session, category: str, action: str) -> bool:
        """
        Delete (soft delete) template.

        Coordination only - calls repository service.

        Args:
            db: Database session
            category: Template category to delete
            action: Template action to delete

        Returns:
            True if deleted successfully

        Raises:
            PromptTemplateOrchestratorError: If deletion fails
        """
        try:
            deleted = self.service.delete_template(db, category, action)

            if not deleted:
                raise PromptTemplateOrchestratorError(
                    f"Template not found for category '{category}' and action '{action}'"
                )

            return True

        except PromptTemplateOrchestratorError:
            # Re-raise orchestrator errors as-is
            raise
        except Exception as e:
            logger.error(
                "Template deletion failed",
                category=category,
                action=action,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise PromptTemplateOrchestratorError(f"Failed to delete template: {e}") from e

    def process_template_with_input(self, db: Session, category: str, action: str, user_input: str) -> dict[str, Any]:
        """
        Get template and process with user input (complete AI parameters + prompt).

        Coordinates: Repository → Processor (with FallbackHandler)

        Args:
            db: Database session
            category: Template category
            action: Template action
            user_input: User's input text

        Returns:
            Dict with complete processing result:
            {
                "prompt": str,              # Complete prompt text
                "model": str,               # Resolved model name
                "temperature": float,       # Resolved temperature
                "max_tokens": int,          # Resolved max_tokens
                "fallback_count": int,      # Number of fallbacks used (0-3)
                "fallbacks_used": {...}     # Which parameters used fallback
            }

        Raises:
            PromptTemplateOrchestratorError: If template not found or processing fails
        """
        try:
            # Step 1: Get template from repository
            template = self.service.get_template_by_category_action(db, category, action)

            if not template:
                raise PromptTemplateOrchestratorError(
                    f"Template not found for category '{category}' and action '{action}'"
                )

            # Step 2: Process template (processor uses fallback handler internally)
            result = PromptTemplateProcessor.process_template(template, user_input)

            return result

        except PromptTemplateOrchestratorError:
            # Re-raise orchestrator errors as-is
            raise
        except Exception as e:
            logger.error(
                "Template processing failed",
                category=category,
                action=action,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise PromptTemplateOrchestratorError(f"Failed to process template: {e}") from e
