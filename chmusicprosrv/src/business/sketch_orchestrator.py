"""Sketch Orchestrator - Coordinates sketch operations (no testable business logic)"""

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from business.sketch_normalizer import SketchNormalizer
from db.sketch_service import sketch_service
from utils.logger import logger


class SketchOrchestratorError(Exception):
    """Base exception for sketch orchestration errors"""

    pass


class SketchOrchestrator:
    """Orchestrates sketch operations (calls normalizer + repository)"""

    def create_sketch(
        self,
        db: Session,
        title: str | None,
        lyrics: str | None,
        prompt: str,
        tags: str | None = None,
        sketch_type: str = "song",
        workflow: str = "draft",
        description_long: str | None = None,
        description_short: str | None = None,
        description_tags: str | None = None,
        info: str | None = None,
    ) -> Any:
        """
        Create a new sketch with data normalization

        Args:
            db: Database session
            title: Sketch title (optional)
            lyrics: Song lyrics (optional)
            prompt: Music style prompt (required)
            tags: Comma-separated tags (optional)
            sketch_type: Sketch type (default: song)
            workflow: Workflow status (default: draft)
            description_long: Long description for release (optional)
            description_short: Short description for release (optional)
            description_tags: Release tags (optional)
            info: Working notes (optional)

        Returns:
            Created SongSketch instance

        Raises:
            SketchOrchestratorError: If creation fails
        """
        try:
            # Business logic: Normalize all string fields
            normalized_data = SketchNormalizer.normalize_sketch_data(
                {
                    "title": title,
                    "lyrics": lyrics,
                    "prompt": prompt,
                    "tags": tags,
                    "description_long": description_long,
                    "description_short": description_short,
                    "description_tags": description_tags,
                    "info": info,
                }
            )

            # Repository: Create sketch with normalized data
            sketch = sketch_service.create_sketch(db=db, sketch_type=sketch_type, workflow=workflow, **normalized_data)

            if not sketch:
                raise SketchOrchestratorError("Failed to create sketch")

            return sketch

        except Exception as e:
            logger.error("Sketch creation failed", error=str(e), error_type=type(e).__name__)
            raise SketchOrchestratorError(f"Failed to create sketch: {e}") from e

    def update_sketch(
        self,
        db: Session,
        sketch_id: str | UUID,
        update_data: dict[str, Any],
    ) -> Any:
        """
        Update sketch with data normalization

        Args:
            db: Database session
            sketch_id: UUID of the sketch
            update_data: Dict with fields to update

        Returns:
            Updated SongSketch instance

        Raises:
            SketchOrchestratorError: If update fails or sketch not found
        """
        try:
            # Business logic: Normalize all string fields
            normalized_data = SketchNormalizer.normalize_sketch_data(update_data)

            # Repository: Update sketch with normalized data
            sketch = sketch_service.update_sketch(db=db, sketch_id=sketch_id, **normalized_data)

            if not sketch:
                raise SketchOrchestratorError(f"Sketch not found with ID: {sketch_id}")

            return sketch

        except SketchOrchestratorError:
            raise
        except Exception as e:
            logger.error("Sketch update failed", sketch_id=str(sketch_id), error=str(e), error_type=type(e).__name__)
            raise SketchOrchestratorError(f"Failed to update sketch: {e}") from e

    def get_sketches_with_workflow_filter(
        self,
        db: Session,
        limit: int = 20,
        offset: int = 0,
        search: str = "",
        workflow: str | None = None,
        sort_by: str = "created_at",
        sort_direction: str = "desc",
        exclude_archived: bool = True,
    ) -> dict[str, Any]:
        """
        Get sketches with workflow filtering business rule

        Business Rule: When no workflow is specified and exclude_archived=True,
        exclude archived sketches from results.

        Args:
            db: Database session
            limit: Number of sketches to return
            offset: Number of sketches to skip
            search: Search term
            workflow: Optional workflow filter (draft, used, archived)
            sort_by: Field to sort by
            sort_direction: Sort direction (asc, desc)
            exclude_archived: Exclude archived by default (business rule)

        Returns:
            Dict with 'items' and 'total' keys
        """
        try:
            # Business rule: Apply default workflow filter
            effective_workflow = workflow

            if workflow is None and exclude_archived:
                # Business logic: Default behavior excludes archived
                logger.debug("Applying default filter: excluding archived sketches")
                # Note: This will be handled by passing workflow=None to repository
                # and letting it apply its default filter

            # Repository: Get paginated sketches
            result = sketch_service.get_sketches_paginated(
                db=db,
                limit=limit,
                offset=offset,
                search=search,
                workflow=effective_workflow,
                sort_by=sort_by,
                sort_direction=sort_direction,
            )

            return result

        except Exception as e:
            logger.error("Failed to retrieve sketches", error=str(e), error_type=type(e).__name__)
            raise SketchOrchestratorError(f"Failed to retrieve sketches: {e}") from e

    def assign_to_project(
        self,
        db: Session,
        sketch_id: str,
        project_id: str,
        folder_id: str | None = None,
    ) -> dict | None:
        """
        Assign sketch to a project (1:1 relationship)

        Args:
            db: Database session
            sketch_id: Sketch UUID
            project_id: Project UUID
            folder_id: Optional folder UUID

        Returns:
            dict: Updated sketch data or None if not found

        Raises:
            ValueError: If project or folder not found
        """
        from uuid import UUID

        from db.song_project_service import get_folder_by_id, get_project_by_id

        try:
            # Validate project exists
            project = get_project_by_id(db, UUID(project_id))
            if not project:
                raise ValueError(f"Project not found: {project_id}")

            # Validate folder if provided
            if folder_id:
                folder = get_folder_by_id(db, UUID(folder_id))
                if not folder:
                    raise ValueError(f"Folder not found: {folder_id}")
                if folder.project_id != UUID(project_id):
                    raise ValueError(f"Folder {folder_id} does not belong to project {project_id}")

            # Update sketch
            updated_sketch = sketch_service.update_sketch(
                db=db,
                sketch_id=sketch_id,
                project_id=project_id,
                project_folder_id=folder_id,
            )

            if not updated_sketch:
                return None

            logger.info(
                "Sketch assigned to project",
                sketch_id=sketch_id,
                project_id=project_id,
                folder_id=folder_id,
            )

            return {
                "id": str(updated_sketch.id),
                "title": updated_sketch.title,
                "project_id": str(updated_sketch.project_id) if updated_sketch.project_id else None,
                "project_folder_id": str(updated_sketch.project_folder_id)
                if updated_sketch.project_folder_id
                else None,
            }

        except Exception as e:
            logger.error(
                "Failed to assign sketch to project",
                sketch_id=sketch_id,
                project_id=project_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    def unassign_from_project(self, db: Session, sketch_id: str) -> dict | None:
        """
        Remove sketch from its assigned project (link only, sketch remains)

        Args:
            db: Database session
            sketch_id: Sketch UUID

        Returns:
            dict: Updated sketch data or None if not found
        """
        try:
            # Update sketch to remove project assignment
            updated_sketch = sketch_service.update_sketch(
                db=db,
                sketch_id=sketch_id,
                clear_project=True,
            )

            if not updated_sketch:
                return None

            logger.info("Sketch unassigned from project", sketch_id=sketch_id)

            return {
                "id": str(updated_sketch.id),
                "title": updated_sketch.title,
                "project_id": None,
                "project_folder_id": None,
            }

        except Exception as e:
            logger.error(
                "Failed to unassign sketch from project",
                sketch_id=sketch_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    def duplicate_sketch(
        self,
        db: Session,
        original_sketch_id: str | UUID,
        new_title_suffix: str | None = None,
    ) -> Any:
        """
        Duplicate sketch (simple copy without translation)

        Args:
            db: Database session
            original_sketch_id: UUID of sketch to duplicate
            new_title_suffix: Suffix for new title (default: ' (Copy)')

        Returns:
            New SongSketch instance

        Raises:
            SketchOrchestratorError: If duplication fails
        """
        try:
            # Get original sketch
            original = sketch_service.get_sketch_by_id(db, original_sketch_id)
            if not original:
                raise SketchOrchestratorError(f"Original sketch not found: {original_sketch_id}")

            # Determine new title
            suffix = new_title_suffix if new_title_suffix else " (Copy)"
            new_title = f"{original.title}{suffix}" if original.title else None

            # Auto-convert inspiration → song on duplicate (workflow optimization)
            new_sketch_type = "song" if original.sketch_type == "inspiration" else original.sketch_type

            # Create duplicate via repository
            duplicate = sketch_service.duplicate_sketch(
                db=db,
                original_sketch_id=original_sketch_id,
                new_title=new_title,
                new_lyrics=original.lyrics,
                new_sketch_type=new_sketch_type,
            )

            if not duplicate:
                raise SketchOrchestratorError("Failed to create duplicate sketch")

            return duplicate

        except Exception as e:
            logger.error("Sketch duplication failed", sketch_id=str(original_sketch_id), error=str(e))
            raise SketchOrchestratorError(f"Failed to duplicate sketch: {e}") from e
