"""Suno Template Orchestrator - Coordinates suno template operations (no testable business logic)"""

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from business.suno_template_normalizer import SunoTemplateNormalizer
from db.sketch_service import sketch_service
from db.suno_template_service import suno_template_service
from utils.logger import logger


class SunoTemplateOrchestratorError(Exception):
    """Base exception for suno template orchestration errors"""

    pass


class SunoTemplateOrchestrator:
    """Orchestrates suno template operations (calls normalizer + repository)"""

    def create_template(
        self,
        db: Session,
        user_id: str,
        domain_id: str,
        title: str,
        template_type: str = "song",
        enhanced_lyrics: str | None = None,
        genre: str | None = None,
        bpm: int | None = None,
        vocal_type: str | None = None,
        instruments: str | None = None,
        mood: str | None = None,
        mix_character: str | None = None,
        style_prompt: str | None = None,
        is_instrumental: bool = False,
    ) -> Any:
        """Create a new suno template with data normalization"""
        try:
            normalized_data = SunoTemplateNormalizer.normalize_template_data(
                {
                    "title": title,
                    "enhanced_lyrics": enhanced_lyrics,
                    "genre": genre,
                    "vocal_type": vocal_type,
                    "instruments": instruments,
                    "mood": mood,
                    "mix_character": mix_character,
                    "style_prompt": style_prompt,
                }
            )

            # Auto-generate style prompt if not provided manually
            if not normalized_data.get("style_prompt"):
                normalized_data["style_prompt"] = SunoTemplateNormalizer.build_style_prompt(
                    genre=normalized_data.get("genre"),
                    bpm=bpm,
                    vocal_type=normalized_data.get("vocal_type"),
                    instruments=normalized_data.get("instruments"),
                    mood=normalized_data.get("mood"),
                    mix_character=normalized_data.get("mix_character"),
                    is_instrumental=is_instrumental,
                )

            template = suno_template_service.create_template(
                db=db,
                user_id=user_id,
                domain_id=domain_id,
                template_type=template_type,
                bpm=bpm,
                is_instrumental=is_instrumental,
                **normalized_data,
            )

            if not template:
                raise SunoTemplateOrchestratorError("Failed to create suno template")

            return template

        except Exception as e:
            logger.error("Suno template creation failed", error=str(e), error_type=type(e).__name__)
            raise SunoTemplateOrchestratorError(f"Failed to create suno template: {e}") from e

    def create_from_sketch(
        self,
        db: Session,
        user_id: str,
        domain_id: str,
        sketch_id: str,
    ) -> Any:
        """Create a suno template from a sketch (Song-Modus)"""
        try:
            sketch = sketch_service.get_sketch_by_id(db, sketch_id, domain_id=domain_id)
            if not sketch:
                raise SunoTemplateOrchestratorError(f"Sketch not found with ID: {sketch_id}")

            template = suno_template_service.create_template(
                db=db,
                user_id=user_id,
                domain_id=domain_id,
                title=sketch.title or "Untitled",
                template_type="song",
                source_sketch_id=str(sketch.id),
                original_lyrics=sketch.lyrics,
                enhanced_lyrics=sketch.lyrics,
                genre=sketch.tags,
                style_prompt=sketch.prompt,
            )

            if not template:
                raise SunoTemplateOrchestratorError("Failed to create suno template from sketch")

            logger.info(
                "Suno template created from sketch",
                template_id=str(template.id),
                sketch_id=str(sketch.id),
            )

            return template

        except SunoTemplateOrchestratorError:
            raise
        except Exception as e:
            logger.error(
                "Suno template creation from sketch failed",
                sketch_id=sketch_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise SunoTemplateOrchestratorError(f"Failed to create suno template from sketch: {e}") from e

    def update_template(
        self,
        db: Session,
        domain_id: str,
        template_id: str | UUID,
        update_data: dict[str, Any],
    ) -> Any:
        """Update suno template with data normalization and auto style prompt regeneration"""
        try:
            normalized_data = SunoTemplateNormalizer.normalize_template_data(update_data)

            # Check if style fields changed and style_prompt was not explicitly set
            style_fields = {"genre", "bpm", "vocal_type", "instruments", "mood", "mix_character", "is_instrumental"}
            style_fields_changed = bool(style_fields & set(normalized_data.keys()))

            if style_fields_changed and "style_prompt" not in normalized_data:
                # Load current template to merge with updates
                current = suno_template_service.get_template_by_id(db, template_id, domain_id=domain_id)
                if current:
                    normalized_data["style_prompt"] = SunoTemplateNormalizer.build_style_prompt(
                        genre=normalized_data.get("genre", current.genre),
                        bpm=normalized_data.get("bpm", current.bpm),
                        vocal_type=normalized_data.get("vocal_type", current.vocal_type),
                        instruments=normalized_data.get("instruments", current.instruments),
                        mood=normalized_data.get("mood", current.mood),
                        mix_character=normalized_data.get("mix_character", current.mix_character),
                        is_instrumental=normalized_data.get("is_instrumental", current.is_instrumental),
                    )

            template = suno_template_service.update_template(
                db=db, template_id=template_id, domain_id=domain_id, **normalized_data
            )

            if not template:
                raise SunoTemplateOrchestratorError(f"Suno template not found with ID: {template_id}")

            return template

        except SunoTemplateOrchestratorError:
            raise
        except Exception as e:
            logger.error(
                "Suno template update failed",
                template_id=str(template_id),
                error=str(e),
                error_type=type(e).__name__,
            )
            raise SunoTemplateOrchestratorError(f"Failed to update suno template: {e}") from e

    def assign_to_project(
        self,
        db: Session,
        domain_id: str,
        template_id: str,
        project_id: str,
    ) -> dict | None:
        """Assign suno template to a project"""
        from uuid import UUID

        from db.song_project_service import get_project_by_id

        try:
            project = get_project_by_id(db, UUID(project_id))
            if not project:
                raise ValueError(f"Project not found: {project_id}")

            updated_template = suno_template_service.update_template(
                db=db,
                template_id=template_id,
                domain_id=domain_id,
                project_id=project_id,
                project_folder_id=None,
            )

            if not updated_template:
                return None

            logger.info(
                "Suno template assigned to project",
                template_id=template_id,
                project_id=project_id,
            )

            return {
                "id": str(updated_template.id),
                "title": updated_template.title,
                "project_id": str(updated_template.project_id) if updated_template.project_id else None,
                "project_folder_id": str(updated_template.project_folder_id)
                if updated_template.project_folder_id
                else None,
            }

        except Exception as e:
            logger.error(
                "Failed to assign suno template to project",
                template_id=template_id,
                project_id=project_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    def unassign_from_project(self, db: Session, domain_id: str, template_id: str) -> dict | None:
        """Remove suno template from its assigned project"""
        try:
            updated_template = suno_template_service.update_template(
                db=db,
                template_id=template_id,
                domain_id=domain_id,
                clear_project=True,
            )

            if not updated_template:
                return None

            logger.info("Suno template unassigned from project", template_id=template_id)

            return {
                "id": str(updated_template.id),
                "title": updated_template.title,
                "project_id": None,
                "project_folder_id": None,
            }

        except Exception as e:
            logger.error(
                "Failed to unassign suno template from project",
                template_id=template_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise
