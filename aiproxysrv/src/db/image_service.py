"""Image database service layer"""

from sqlalchemy.orm import joinedload

from db.database import SessionLocal
from db.models import GeneratedImage
from utils.logger import logger


class ImageService:
    """Service class for image database operations"""

    @staticmethod
    def save_generated_image(
        prompt: str,
        size: str,
        filename: str,
        file_path: str,
        local_url: str,
        model_used: str,
        prompt_hash: str,
        title: str | None = None,
        user_prompt: str | None = None,
        enhanced_prompt: str | None = None,
        artistic_style: str | None = None,
        composition: str | None = None,
        lighting: str | None = None,
        color_palette: str | None = None,
        detail_level: str | None = None,
        s3_key: str | None = None,
    ) -> GeneratedImage | None:
        """
        Save generated image metadata to database

        Returns:
            GeneratedImage instance if successful, None if failed
        """
        db = SessionLocal()
        try:
            generated_image = GeneratedImage(
                user_prompt=user_prompt,
                prompt=prompt,
                enhanced_prompt=enhanced_prompt,
                size=size,
                filename=filename,
                file_path=file_path,
                local_url=local_url,
                s3_key=s3_key,
                storage_backend="s3",
                model_used=model_used,
                prompt_hash=prompt_hash,
                title=title,
                artistic_style=artistic_style,
                composition=composition,
                lighting=lighting,
                color_palette=color_palette,
                detail_level=detail_level,
            )
            db.add(generated_image)
            db.commit()
            db.refresh(generated_image)
            logger.info(
                "image_metadata_saved", image_id=str(generated_image.id), filename=filename, model=model_used, size=size
            )
            return generated_image
        except Exception as e:
            db.rollback()
            import traceback

            logger.error(
                "image_metadata_save_failed",
                error=str(e),
                error_type=type(e).__name__,
                stacktrace=traceback.format_exc(),
            )
            return None
        finally:
            db.close()

    @staticmethod
    def get_image_by_filename(filename: str) -> GeneratedImage | None:
        """Get image metadata by filename"""
        db = SessionLocal()
        try:
            return db.query(GeneratedImage).filter(GeneratedImage.filename == filename).first()
        finally:
            db.close()

    @staticmethod
    def get_images_by_prompt_hash(prompt_hash: str) -> list[GeneratedImage]:
        """Get all images with the same prompt hash"""
        db = SessionLocal()
        try:
            return db.query(GeneratedImage).filter(GeneratedImage.prompt_hash == prompt_hash).all()
        finally:
            db.close()

    @staticmethod
    def get_recent_images(limit: int = 10) -> list[GeneratedImage]:
        """Get most recently generated images"""
        db = SessionLocal()
        try:
            return db.query(GeneratedImage).order_by(GeneratedImage.created_at.desc()).limit(limit).all()
        finally:
            db.close()

    @staticmethod
    def get_recent_images_paginated(limit: int = 20, offset: int = 0) -> list[GeneratedImage]:
        """Get most recently generated images with pagination (deprecated - use get_images_paginated)"""
        return ImageService.get_images_paginated(limit=limit, offset=offset)

    @staticmethod
    def get_images_paginated(
        limit: int = 20, offset: int = 0, search: str = "", sort_by: str = "created_at", sort_direction: str = "desc"
    ) -> list[GeneratedImage]:
        """Get images with pagination, search and sorting"""
        from sqlalchemy.orm import joinedload

        db = SessionLocal()
        try:
            query = db.query(GeneratedImage).options(joinedload(GeneratedImage.project_references))

            # Apply search filter if provided
            if search:
                search_term = f"%{search}%"
                from sqlalchemy import or_

                query = query.filter(
                    or_(
                        GeneratedImage.title.ilike(search_term),
                        GeneratedImage.user_prompt.ilike(search_term),
                        GeneratedImage.prompt.ilike(search_term),
                    )
                )

            # Apply sorting
            if sort_by == "title":
                # Handle null titles by treating them as empty strings for sorting
                if sort_direction == "desc":
                    query = query.order_by(GeneratedImage.title.desc().nullslast())
                else:
                    query = query.order_by(GeneratedImage.title.asc().nullsfirst())
            elif sort_by == "prompt":
                if sort_direction == "desc":
                    query = query.order_by(GeneratedImage.prompt.desc())
                else:
                    query = query.order_by(GeneratedImage.prompt.asc())
            else:  # default to created_at
                if sort_direction == "desc":
                    query = query.order_by(GeneratedImage.created_at.desc())
                else:
                    query = query.order_by(GeneratedImage.created_at.asc())

            return query.limit(limit).offset(offset).all()
        finally:
            db.close()

    @staticmethod
    def get_total_images_count(search: str = "") -> int:
        """Get total count of generated images with optional search filter"""
        db = SessionLocal()
        try:
            query = db.query(GeneratedImage)

            # Apply search filter if provided
            if search:
                search_term = f"%{search}%"
                from sqlalchemy import or_

                query = query.filter(
                    or_(
                        GeneratedImage.title.ilike(search_term),
                        GeneratedImage.user_prompt.ilike(search_term),
                        GeneratedImage.prompt.ilike(search_term),
                    )
                )

            return query.count()
        finally:
            db.close()

    @staticmethod
    def get_image_by_id(image_id: str) -> GeneratedImage | None:
        """Get image metadata by ID"""
        db = SessionLocal()
        try:
            return (
                db.query(GeneratedImage)
                .options(joinedload(GeneratedImage.project_references))
                .filter(GeneratedImage.id == image_id)
                .first()
            )
        finally:
            db.close()

    @staticmethod
    def get_images_for_text_overlay() -> list[GeneratedImage]:
        """
        Get images suitable for text overlay
        - Only images with title (not NULL and not empty)
        - Exclude images that already have text overlay (text_overlay_metadata is not NULL)
        - Sorted: composition='album-cover' first, then by created_at DESC
        """
        db = SessionLocal()
        try:
            from sqlalchemy import case

            # Create a sort expression: album-cover = 0, others = 1 (so album-cover comes first)
            album_cover_priority = case((GeneratedImage.composition == "album-cover", 0), else_=1)

            query = (
                db.query(GeneratedImage)
                .options(joinedload(GeneratedImage.project_references))  # Eager load to prevent lazy load errors
                .filter(GeneratedImage.title.isnot(None))
                .filter(GeneratedImage.title != "")
                .filter(GeneratedImage.text_overlay_metadata.is_(None))  # Exclude overlay images
                .order_by(album_cover_priority, GeneratedImage.created_at.desc())
            )

            return query.all()
        finally:
            db.close()

    @staticmethod
    def delete_image_metadata(image_id: str) -> bool:
        """Delete image metadata by ID"""
        db = SessionLocal()
        try:
            image = db.query(GeneratedImage).filter(GeneratedImage.id == image_id).first()
            if image:
                db.delete(image)
                db.commit()
                logger.info("Image metadata deleted", image_id=str(image_id))
                return True
            logger.warning("Image not found for deletion", image_id=str(image_id))
            return False
        except Exception as e:
            db.rollback()
            import traceback

            logger.error(
                "image_metadata_deletion_failed",
                image_id=str(image_id),
                error=str(e),
                error_type=type(e).__name__,
                stacktrace=traceback.format_exc(),
            )
            return False
        finally:
            db.close()

    @staticmethod
    def update_image_metadata(image_id: str, title: str = None, tags: str = None) -> bool:
        """Update image metadata (title and/or tags) by ID"""
        db = SessionLocal()
        try:
            image = db.query(GeneratedImage).filter(GeneratedImage.id == image_id).first()
            if not image:
                return False

            # Update fields if provided
            if title is not None:
                image.title = title.strip() if title.strip() else None
            if tags is not None:
                image.tags = tags.strip() if tags.strip() else None

            db.commit()
            logger.info(
                "image_metadata_updated",
                image_id=str(image_id),
                title_updated=title is not None,
                tags_updated=tags is not None,
            )
            return True
        except Exception as e:
            db.rollback()
            import traceback

            logger.error(
                "image_metadata_update_failed",
                image_id=str(image_id),
                error=str(e),
                error_type=type(e).__name__,
                stacktrace=traceback.format_exc(),
            )
            return False
        finally:
            db.close()

    @staticmethod
    def get_projects_for_image(image_id: str) -> list[dict]:
        """
        Get list of projects this image is assigned to.
        Returns list of dicts with project_id and project_name.
        """
        from db.models import ProjectImageReference, SongProject

        db = SessionLocal()
        try:
            # Query project_image_references joined with song_projects
            references = (
                db.query(ProjectImageReference, SongProject)
                .join(SongProject, ProjectImageReference.project_id == SongProject.id)
                .filter(ProjectImageReference.image_id == image_id)
                .all()
            )

            projects = []
            for _ref, project in references:
                projects.append({"project_id": str(project.id), "project_name": project.project_name})

            logger.debug("Projects retrieved for image", image_id=image_id, count=len(projects))
            return projects
        except Exception as e:
            logger.error(
                "Failed to get projects for image", image_id=image_id, error=str(e), error_type=type(e).__name__
            )
            return []
        finally:
            db.close()


# Standalone wrapper function for orchestrator imports
def get_image_by_id(_db, image_id):
    """Wrapper function for ImageService.get_image_by_id (db parameter ignored, service uses own session)"""
    return ImageService.get_image_by_id(image_id)
