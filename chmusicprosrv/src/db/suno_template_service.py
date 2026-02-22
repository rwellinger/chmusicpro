"""Suno Template Service - Database operations for suno template management"""

import traceback
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from db.models import SunoTemplate
from utils.logger import logger


class SunoTemplateService:
    """Service for suno template database operations"""

    def create_template(
        self,
        db: Session,
        user_id: str,
        domain_id: str,
        title: str,
        template_type: str = "song",
        source_sketch_id: str | None = None,
        original_lyrics: str | None = None,
        enhanced_lyrics: str | None = None,
        genre: str | None = None,
        bpm: int | None = None,
        vocal_type: str | None = None,
        instruments: str | None = None,
        mood: str | None = None,
        mix_character: str | None = None,
        style_prompt: str | None = None,
        is_instrumental: bool = False,
    ) -> SunoTemplate | None:
        """Create a new suno template record in the database"""
        try:
            template = SunoTemplate(
                user_id=user_id,
                domain_id=domain_id,
                title=title,
                template_type=template_type,
                source_sketch_id=source_sketch_id,
                original_lyrics=original_lyrics,
                enhanced_lyrics=enhanced_lyrics,
                genre=genre,
                bpm=bpm,
                vocal_type=vocal_type,
                instruments=instruments,
                mood=mood,
                mix_character=mix_character,
                style_prompt=style_prompt,
                is_instrumental=is_instrumental,
            )

            db.add(template)
            db.commit()
            db.refresh(template)

            logger.info(
                "suno_template_created",
                template_id=str(template.id),
                title=title,
                template_type=template_type,
            )
            return template

        except SQLAlchemyError as e:
            db.rollback()
            logger.error("suno_template_creation_db_error", error=str(e), error_type=type(e).__name__)
            return None
        except Exception as e:
            logger.error("suno_template_creation_failed", error=str(e), error_type=type(e).__name__)
            return None

    def get_template_by_id(
        self, db: Session, template_id: str | UUID, domain_id: str | None = None
    ) -> SunoTemplate | None:
        """Get suno template by ID"""
        try:
            query = db.query(SunoTemplate).filter(SunoTemplate.id == template_id)
            if domain_id:
                query = query.filter(SunoTemplate.domain_id == domain_id)
            template = query.first()
            if template:
                logger.debug("Suno template retrieved", template_id=str(template_id))
            else:
                logger.debug("Suno template not found", template_id=str(template_id))
            return template
        except Exception as e:
            logger.error(
                "error_getting_suno_template_by_id",
                template_id=str(template_id),
                error=str(e),
                error_type=type(e).__name__,
            )
            return None

    def get_templates_paginated(
        self,
        db: Session,
        domain_id: str,
        limit: int = 20,
        offset: int = 0,
        search: str = "",
        template_type: str | None = None,
        sort_by: str = "created_at",
        sort_direction: str = "desc",
    ) -> dict[str, Any]:
        """Get paginated list of suno templates with search and filtering"""
        try:
            query = db.query(SunoTemplate).options(joinedload(SunoTemplate.project))

            # Apply domain filter (tenant isolation)
            query = query.filter(SunoTemplate.domain_id == domain_id)

            # Apply template_type filter
            if template_type:
                query = query.filter(SunoTemplate.template_type == template_type)

            # Apply search filter if provided
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        SunoTemplate.title.ilike(search_term),
                        SunoTemplate.genre.ilike(search_term),
                    )
                )

            # Get total count before pagination
            total_count = query.count()

            # Apply sorting
            if sort_by == "title":
                if sort_direction == "desc":
                    query = query.order_by(SunoTemplate.title.desc().nullslast())
                else:
                    query = query.order_by(SunoTemplate.title.asc().nullsfirst())
            elif sort_by == "updated_at":
                if sort_direction == "desc":
                    query = query.order_by(SunoTemplate.updated_at.desc().nullslast())
                else:
                    query = query.order_by(SunoTemplate.updated_at.asc().nullsfirst())
            else:  # default to created_at
                if sort_direction == "desc":
                    query = query.order_by(SunoTemplate.created_at.desc())
                else:
                    query = query.order_by(SunoTemplate.created_at.asc())

            # Apply pagination
            templates = query.limit(limit).offset(offset).all()

            logger.debug(
                "suno_templates_retrieved_paginated",
                count=len(templates),
                total=total_count,
                limit=limit,
                offset=offset,
                template_type=template_type,
                search=search,
            )

            return {"items": templates, "total": total_count}
        except Exception as e:
            logger.error(
                "error_getting_paginated_suno_templates",
                error=str(e),
                error_type=type(e).__name__,
                stacktrace=traceback.format_exc(),
            )
            return {"items": [], "total": 0}

    def update_template(
        self,
        db: Session,
        template_id: str | UUID,
        domain_id: str | None = None,
        title: str | None = None,
        template_type: str | None = None,
        original_lyrics: str | None = None,
        enhanced_lyrics: str | None = None,
        genre: str | None = None,
        bpm: int | None = None,
        vocal_type: str | None = None,
        instruments: str | None = None,
        mood: str | None = None,
        mix_character: str | None = None,
        style_prompt: str | None = None,
        is_instrumental: bool | None = None,
        project_id: str | None = None,
        project_folder_id: str | None = None,
        clear_project: bool = False,
    ) -> SunoTemplate | None:
        """Update an existing suno template"""
        try:
            query = db.query(SunoTemplate).filter(SunoTemplate.id == template_id)
            if domain_id:
                query = query.filter(SunoTemplate.domain_id == domain_id)
            template = query.first()
            if not template:
                logger.warning("Suno template not found for update", template_id=str(template_id))
                return None

            updated_fields = []

            if title is not None:
                template.title = title
                updated_fields.append("title")
            if template_type is not None:
                template.template_type = template_type
                updated_fields.append("template_type")
            if original_lyrics is not None:
                template.original_lyrics = original_lyrics
                updated_fields.append("original_lyrics")
            if enhanced_lyrics is not None:
                template.enhanced_lyrics = enhanced_lyrics
                updated_fields.append("enhanced_lyrics")
            if genre is not None:
                template.genre = genre
                updated_fields.append("genre")
            if bpm is not None:
                template.bpm = bpm
                updated_fields.append("bpm")
            if vocal_type is not None:
                template.vocal_type = vocal_type
                updated_fields.append("vocal_type")
            if instruments is not None:
                template.instruments = instruments
                updated_fields.append("instruments")
            if mood is not None:
                template.mood = mood
                updated_fields.append("mood")
            if mix_character is not None:
                template.mix_character = mix_character
                updated_fields.append("mix_character")
            if style_prompt is not None:
                template.style_prompt = style_prompt
                updated_fields.append("style_prompt")
            if is_instrumental is not None:
                template.is_instrumental = is_instrumental
                updated_fields.append("is_instrumental")

            # Handle project assignment/unassignment
            if clear_project:
                template.project_id = None
                template.project_folder_id = None
                updated_fields.append("project_id")
                updated_fields.append("project_folder_id")
            else:
                if project_id is not None:
                    template.project_id = project_id
                    updated_fields.append("project_id")
                if project_folder_id is not None:
                    template.project_folder_id = project_folder_id
                    updated_fields.append("project_folder_id")

            # Update timestamp
            template.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(template)

            logger.info("Suno template updated", template_id=str(template_id), fields_updated=updated_fields)
            return template

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(
                "suno_template_update_db_error",
                template_id=str(template_id),
                error=str(e),
                error_type=type(e).__name__,
            )
            return None
        except Exception as e:
            logger.error(
                "suno_template_update_failed",
                template_id=str(template_id),
                error=str(e),
                error_type=type(e).__name__,
                stacktrace=traceback.format_exc(),
            )
            return None

    def delete_template(self, db: Session, template_id: str | UUID, domain_id: str | None = None) -> bool:
        """Delete a suno template by ID"""
        try:
            query = db.query(SunoTemplate).filter(SunoTemplate.id == template_id)
            if domain_id:
                query = query.filter(SunoTemplate.domain_id == domain_id)
            template = query.first()
            if template:
                db.delete(template)
                db.commit()
                logger.info("Suno template deleted", template_id=str(template_id))
                return True
            logger.warning("Suno template not found for deletion", template_id=str(template_id))
            return False
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(
                "suno_template_deletion_db_error",
                template_id=str(template_id),
                error=str(e),
                error_type=type(e).__name__,
            )
            return False
        except Exception as e:
            logger.error(
                "suno_template_deletion_failed",
                template_id=str(template_id),
                error=str(e),
                error_type=type(e).__name__,
                stacktrace=traceback.format_exc(),
            )
            return False


# Global service instance
suno_template_service = SunoTemplateService()
