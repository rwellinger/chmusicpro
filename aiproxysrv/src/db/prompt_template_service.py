"""Prompt Template Service - Database operations for prompt template management

Repository Layer - Pure CRUD operations (no business logic, no tests per CLAUDE.md)
"""

from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from db.models import PromptTemplate
from utils.logger import logger


class PromptTemplateService:
    """Service for prompt template database operations (CRUD only)"""

    def get_all_templates(self, db: Session) -> list[PromptTemplate]:
        """
        Get all prompt templates from database.

        Args:
            db: Database session

        Returns:
            List of PromptTemplate instances (empty list if error)
        """
        try:
            templates = db.query(PromptTemplate).all()
            logger.debug("Retrieved all templates", count=len(templates))
            return templates

        except SQLAlchemyError as e:
            logger.error("Failed to retrieve all templates", error=str(e), error_type=type(e).__name__)
            return []

    def get_templates_by_category(self, db: Session, category: str) -> list[PromptTemplate]:
        """
        Get all prompt templates for a specific category.

        Args:
            db: Database session
            category: Template category (e.g., "lyrics", "image")

        Returns:
            List of PromptTemplate instances for category (empty list if error)
        """
        try:
            templates = db.query(PromptTemplate).filter(PromptTemplate.category == category).all()
            logger.debug("Retrieved templates by category", category=category, count=len(templates))
            return templates

        except SQLAlchemyError as e:
            logger.error(
                "Failed to retrieve templates by category",
                category=category,
                error=str(e),
                error_type=type(e).__name__,
            )
            return []

    def get_template_by_category_action(self, db: Session, category: str, action: str) -> PromptTemplate | None:
        """
        Get specific prompt template by category and action.

        Args:
            db: Database session
            category: Template category (e.g., "lyrics")
            action: Template action (e.g., "generate")

        Returns:
            PromptTemplate instance if found, None otherwise
        """
        try:
            template = (
                db.query(PromptTemplate)
                .filter(PromptTemplate.category == category, PromptTemplate.action == action)
                .first()
            )

            if template:
                logger.debug("Retrieved template", category=category, action=action, template_id=template.id)
            else:
                logger.debug("Template not found", category=category, action=action)

            return template

        except SQLAlchemyError as e:
            logger.error(
                "Failed to retrieve template by category/action",
                category=category,
                action=action,
                error=str(e),
                error_type=type(e).__name__,
            )
            return None

    def create_template(self, db: Session, template_data: dict[str, Any]) -> PromptTemplate | None:
        """
        Create new prompt template in database.

        Args:
            db: Database session
            template_data: Dictionary with template fields
                Required: category, action, pre_condition, post_condition
                Optional: description, version, model, temperature, max_tokens, active

        Returns:
            PromptTemplate instance if successful, None otherwise
        """
        try:
            template = PromptTemplate(**template_data)

            db.add(template)
            db.commit()
            db.refresh(template)

            logger.info(
                "Template created",
                category=template.category,
                action=template.action,
                template_id=template.id,
                version=template.version,
            )
            return template

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(
                "Failed to create template",
                category=template_data.get("category"),
                action=template_data.get("action"),
                error=str(e),
                error_type=type(e).__name__,
            )
            return None

    def update_template(
        self, db: Session, category: str, action: str, update_data: dict[str, Any]
    ) -> PromptTemplate | None:
        """
        Update existing prompt template.

        Args:
            db: Database session
            category: Template category to update
            action: Template action to update
            update_data: Dictionary with fields to update

        Returns:
            Updated PromptTemplate instance if successful, None otherwise
        """
        try:
            template = self.get_template_by_category_action(db, category, action)

            if not template:
                logger.warning("Template not found for update", category=category, action=action)
                return None

            # Update only provided fields
            for key, value in update_data.items():
                if hasattr(template, key):
                    setattr(template, key, value)

            db.commit()
            db.refresh(template)

            logger.info(
                "Template updated",
                category=category,
                action=action,
                template_id=template.id,
                fields_updated=list(update_data.keys()),
            )
            return template

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(
                "Failed to update template",
                category=category,
                action=action,
                error=str(e),
                error_type=type(e).__name__,
            )
            return None

    def delete_template(self, db: Session, category: str, action: str) -> bool:
        """
        Delete prompt template from database.

        Args:
            db: Database session
            category: Template category to delete
            action: Template action to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            template = self.get_template_by_category_action(db, category, action)

            if not template:
                logger.warning("Template not found for deletion", category=category, action=action)
                return False

            template_id = template.id
            db.delete(template)
            db.commit()

            logger.info("Template deleted", category=category, action=action, template_id=template_id)
            return True

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(
                "Failed to delete template",
                category=category,
                action=action,
                error=str(e),
                error_type=type(e).__name__,
            )
            return False

    def template_exists(self, db: Session, category: str, action: str) -> bool:
        """
        Check if template exists in database.

        Args:
            db: Database session
            category: Template category
            action: Template action

        Returns:
            True if template exists, False otherwise
        """
        try:
            exists = (
                db.query(PromptTemplate)
                .filter(PromptTemplate.category == category, PromptTemplate.action == action)
                .count()
                > 0
            )
            return exists

        except SQLAlchemyError as e:
            logger.error(
                "Failed to check template existence",
                category=category,
                action=action,
                error=str(e),
                error_type=type(e).__name__,
            )
            return False
