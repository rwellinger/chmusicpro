"""Workshop Service - Database operations for workshop management"""

import traceback
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from db.models import LyricWorkshop
from utils.logger import logger


class WorkshopService:
    """Service for workshop database operations"""

    def create_workshop(
        self,
        db: Session,
        title: str,
        connect_topic: str | None = None,
        draft_language: str | None = "EN",
    ) -> LyricWorkshop | None:
        """
        Create a new workshop record in the database

        Args:
            db: Database session
            title: Workshop title (required)
            connect_topic: Initial topic/theme (optional)

        Returns:
            LyricWorkshop instance if successful, None otherwise
        """
        try:
            workshop = LyricWorkshop(
                title=title,
                connect_topic=connect_topic,
                draft_language=draft_language,
            )

            db.add(workshop)
            db.commit()
            db.refresh(workshop)

            logger.info(
                "workshop_created",
                workshop_id=str(workshop.id),
                title=title,
            )
            return workshop

        except SQLAlchemyError as e:
            db.rollback()
            logger.error("workshop_creation_db_error", error=str(e), error_type=type(e).__name__)
            return None
        except Exception as e:
            logger.error("workshop_creation_failed", error=str(e), error_type=type(e).__name__)
            return None

    def get_workshop_by_id(self, db: Session, workshop_id: str | UUID) -> LyricWorkshop | None:
        """
        Get workshop by ID

        Args:
            db: Database session
            workshop_id: UUID of the workshop

        Returns:
            LyricWorkshop instance if found, None otherwise
        """
        try:
            workshop = db.query(LyricWorkshop).filter(LyricWorkshop.id == workshop_id).first()
            if workshop:
                logger.debug("Workshop retrieved", workshop_id=str(workshop_id))
            else:
                logger.debug("Workshop not found", workshop_id=str(workshop_id))
            return workshop
        except Exception as e:
            logger.error(
                "error_getting_workshop_by_id", workshop_id=str(workshop_id), error=str(e), error_type=type(e).__name__
            )
            return None

    def get_workshops_paginated(
        self,
        db: Session,
        limit: int = 20,
        offset: int = 0,
        search: str = "",
        phase: str | None = None,
        sort_by: str = "created_at",
        sort_direction: str = "desc",
    ) -> dict[str, Any]:
        """
        Get paginated list of workshops with search and filtering

        Args:
            db: Database session
            limit: Number of workshops to return (default 20)
            offset: Number of workshops to skip (default 0)
            search: Search term to filter by title or connect_topic
            phase: Optional phase filter (connect, collect, shape, completed)
            sort_by: Field to sort by (created_at, updated_at, title)
            sort_direction: Sort direction (asc, desc)

        Returns:
            Dictionary with 'items' (list of workshops) and 'total' (count)
        """
        try:
            query = db.query(LyricWorkshop)

            # Apply phase filter
            if phase:
                query = query.filter(LyricWorkshop.current_phase == phase)

            # Apply search filter if provided
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        LyricWorkshop.title.ilike(search_term),
                        LyricWorkshop.connect_topic.ilike(search_term),
                    )
                )

            # Get total count before pagination
            total_count = query.count()

            # Apply sorting
            if sort_by == "title":
                if sort_direction == "desc":
                    query = query.order_by(LyricWorkshop.title.desc().nullslast())
                else:
                    query = query.order_by(LyricWorkshop.title.asc().nullsfirst())
            elif sort_by == "updated_at":
                if sort_direction == "desc":
                    query = query.order_by(LyricWorkshop.updated_at.desc().nullslast())
                else:
                    query = query.order_by(LyricWorkshop.updated_at.asc().nullsfirst())
            else:  # default to created_at
                if sort_direction == "desc":
                    query = query.order_by(LyricWorkshop.created_at.desc())
                else:
                    query = query.order_by(LyricWorkshop.created_at.asc())

            # Apply pagination
            workshops = query.limit(limit).offset(offset).all()

            logger.debug(
                "workshops_retrieved_paginated",
                count=len(workshops),
                total=total_count,
                limit=limit,
                offset=offset,
                phase=phase,
                search=search,
                sort_by=sort_by,
                sort_direction=sort_direction,
            )

            return {"items": workshops, "total": total_count}
        except Exception as e:
            logger.error(
                "error_getting_paginated_workshops",
                error=str(e),
                error_type=type(e).__name__,
                stacktrace=traceback.format_exc(),
            )
            return {"items": [], "total": 0}

    def update_workshop(
        self,
        db: Session,
        workshop_id: str | UUID,
        title: str | None = None,
        connect_topic: str | None = None,
        connect_inspirations: str | None = None,
        collect_mindmap: str | None = None,
        collect_stories: str | None = None,
        collect_words: str | None = None,
        shape_structure: str | None = None,
        shape_rhymes: str | None = None,
        shape_draft: str | None = None,
        current_phase: str | None = None,
        draft_language: str | None = None,
        exported_sketch_id: str | UUID | None = None,
    ) -> LyricWorkshop | None:
        """
        Update an existing workshop

        Args:
            db: Database session
            workshop_id: UUID of the workshop
            All other args: Optional field updates

        Returns:
            Updated LyricWorkshop instance if successful, None otherwise
        """
        try:
            workshop = db.query(LyricWorkshop).filter(LyricWorkshop.id == workshop_id).first()
            if not workshop:
                logger.warning("Workshop not found for update", workshop_id=str(workshop_id))
                return None

            updated_fields = []

            if title is not None:
                workshop.title = title
                updated_fields.append("title")
            if connect_topic is not None:
                workshop.connect_topic = connect_topic
                updated_fields.append("connect_topic")
            if connect_inspirations is not None:
                workshop.connect_inspirations = connect_inspirations
                updated_fields.append("connect_inspirations")
            if collect_mindmap is not None:
                workshop.collect_mindmap = collect_mindmap
                updated_fields.append("collect_mindmap")
            if collect_stories is not None:
                workshop.collect_stories = collect_stories
                updated_fields.append("collect_stories")
            if collect_words is not None:
                workshop.collect_words = collect_words
                updated_fields.append("collect_words")
            if shape_structure is not None:
                workshop.shape_structure = shape_structure
                updated_fields.append("shape_structure")
            if shape_rhymes is not None:
                workshop.shape_rhymes = shape_rhymes
                updated_fields.append("shape_rhymes")
            if shape_draft is not None:
                workshop.shape_draft = shape_draft
                updated_fields.append("shape_draft")
            if current_phase is not None:
                workshop.current_phase = current_phase
                updated_fields.append("current_phase")
            if draft_language is not None:
                workshop.draft_language = draft_language
                updated_fields.append("draft_language")
            if exported_sketch_id is not None:
                workshop.exported_sketch_id = exported_sketch_id
                updated_fields.append("exported_sketch_id")

            # Update timestamp
            workshop.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(workshop)

            logger.info("Workshop updated", workshop_id=str(workshop_id), fields_updated=updated_fields)
            return workshop

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(
                "workshop_update_db_error", workshop_id=str(workshop_id), error=str(e), error_type=type(e).__name__
            )
            return None
        except Exception as e:
            logger.error(
                "workshop_update_failed",
                workshop_id=str(workshop_id),
                error=str(e),
                error_type=type(e).__name__,
                stacktrace=traceback.format_exc(),
            )
            return None

    def delete_workshop(self, db: Session, workshop_id: str | UUID) -> bool:
        """
        Delete a workshop by ID

        Args:
            db: Database session
            workshop_id: UUID of the workshop

        Returns:
            True if successful, False otherwise
        """
        try:
            workshop = db.query(LyricWorkshop).filter(LyricWorkshop.id == workshop_id).first()
            if workshop:
                db.delete(workshop)
                db.commit()
                logger.info("Workshop deleted", workshop_id=str(workshop_id))
                return True
            logger.warning("Workshop not found for deletion", workshop_id=str(workshop_id))
            return False
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(
                "workshop_deletion_db_error", workshop_id=str(workshop_id), error=str(e), error_type=type(e).__name__
            )
            return False
        except Exception as e:
            logger.error(
                "workshop_deletion_failed",
                workshop_id=str(workshop_id),
                error=str(e),
                error_type=type(e).__name__,
                stacktrace=traceback.format_exc(),
            )
            return False


# Global service instance
workshop_service = WorkshopService()
