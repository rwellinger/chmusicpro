"""System Context Template Service - Database operations (CRUD only)

Repository Layer - Pure CRUD operations (no business logic)
"""

from typing import Any
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from db.models import SystemContextTemplate
from utils.logger import logger


class SystemContextTemplateService:
    """Service for system context template database operations (CRUD only)"""

    def get_all_templates(
        self, db: Session, domain_id: UUID | None = None, active_only: bool = False
    ) -> list[SystemContextTemplate]:
        try:
            query = db.query(SystemContextTemplate)

            if domain_id:
                query = query.filter(SystemContextTemplate.domain_id == domain_id)

            if active_only:
                query = query.filter(SystemContextTemplate.active)

            templates = query.order_by(SystemContextTemplate.sort_order).all()
            logger.debug("Retrieved system context templates", count=len(templates), active_only=active_only)
            return templates

        except SQLAlchemyError as e:
            logger.error("Failed to retrieve system context templates", error=str(e), error_type=type(e).__name__)
            return []

    def get_template_by_id(self, db: Session, template_id: UUID) -> SystemContextTemplate | None:
        try:
            template = db.query(SystemContextTemplate).filter(SystemContextTemplate.id == template_id).first()
            if template:
                logger.debug("Retrieved system context template", template_id=str(template_id))
            else:
                logger.debug("System context template not found", template_id=str(template_id))
            return template

        except SQLAlchemyError as e:
            logger.error(
                "Failed to retrieve system context template",
                template_id=str(template_id),
                error=str(e),
                error_type=type(e).__name__,
            )
            return None

    def get_template_by_name(self, db: Session, domain_id: UUID | None, name: str) -> SystemContextTemplate | None:
        try:
            query = db.query(SystemContextTemplate).filter(SystemContextTemplate.name == name)
            if domain_id:
                query = query.filter(SystemContextTemplate.domain_id == domain_id)
            else:
                query = query.filter(SystemContextTemplate.domain_id.is_(None))
            return query.first()

        except SQLAlchemyError as e:
            logger.error("Failed to check template by name", name=name, error=str(e), error_type=type(e).__name__)
            return None

    def create_template(self, db: Session, template_data: dict[str, Any]) -> SystemContextTemplate | None:
        try:
            template = SystemContextTemplate(**template_data)
            db.add(template)
            db.commit()
            db.refresh(template)
            logger.info("System context template created", template_id=str(template.id), name=template.name)
            return template

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(
                "Failed to create system context template",
                name=template_data.get("name"),
                error=str(e),
                error_type=type(e).__name__,
            )
            return None

    def update_template(
        self, db: Session, template_id: UUID, update_data: dict[str, Any]
    ) -> SystemContextTemplate | None:
        try:
            template = self.get_template_by_id(db, template_id)
            if not template:
                logger.warning("System context template not found for update", template_id=str(template_id))
                return None

            for key, value in update_data.items():
                if hasattr(template, key):
                    setattr(template, key, value)

            db.commit()
            db.refresh(template)
            logger.info(
                "System context template updated",
                template_id=str(template_id),
                fields_updated=list(update_data.keys()),
            )
            return template

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(
                "Failed to update system context template",
                template_id=str(template_id),
                error=str(e),
                error_type=type(e).__name__,
            )
            return None

    def delete_template(self, db: Session, template_id: UUID) -> bool:
        try:
            template = self.get_template_by_id(db, template_id)
            if not template:
                logger.warning("System context template not found for deletion", template_id=str(template_id))
                return False

            db.delete(template)
            db.commit()
            logger.info("System context template deleted", template_id=str(template_id))
            return True

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(
                "Failed to delete system context template",
                template_id=str(template_id),
                error=str(e),
                error_type=type(e).__name__,
            )
            return False
