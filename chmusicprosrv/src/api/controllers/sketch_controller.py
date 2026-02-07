"""Controller for sketch management"""

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from business.sketch_orchestrator import SketchOrchestrator, SketchOrchestratorError
from db.sketch_service import sketch_service
from schemas.common_schemas import PaginationMeta
from schemas.sketch_schemas import (
    SketchCreateRequest,
    SketchDuplicateRequest,
    SketchListResponse,
    SketchResponse,
    SketchUpdateRequest,
)
from utils.logger import logger


class SketchController:
    """Controller for sketch operations"""

    @staticmethod
    def create_sketch(db: Session, sketch_data: SketchCreateRequest) -> tuple[dict[str, Any], int]:
        """
        Create a new sketch (uses business layer for normalization)

        Args:
            db: Database session
            sketch_data: Sketch creation data (Pydantic model)

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            sketch_orchestrator = SketchOrchestrator()
            sketch = sketch_orchestrator.create_sketch(
                db=db,
                title=sketch_data.title,
                lyrics=sketch_data.lyrics,
                prompt=sketch_data.prompt,
                tags=sketch_data.tags,
                sketch_type=sketch_data.sketch_type,
            )

            response = SketchResponse.model_validate(sketch)
            return {"data": response.model_dump(), "message": "Sketch created successfully"}, 201

        except SketchOrchestratorError as e:
            logger.error("sketch_creation_error", error=str(e))
            return {"error": f"Failed to create sketch: {str(e)}"}, 500
        except Exception as e:
            logger.error("sketch_creation_error", error=str(e), error_type=type(e).__name__)
            return {"error": f"Failed to create sketch: {str(e)}"}, 500

    @staticmethod
    def get_sketches(
        db: Session,
        limit: int = 20,
        offset: int = 0,
        search: str = "",
        workflow: str | None = None,
        sketch_type: str | None = None,
        sort_by: str = "created_at",
        sort_direction: str = "desc",
    ) -> tuple[dict[str, Any], int]:
        """
        Get list of sketches with pagination, search and filtering

        Args:
            db: Database session
            limit: Number of sketches to return
            offset: Number of sketches to skip
            search: Search term to filter by title, lyrics, prompt, or tags
            workflow: Optional workflow filter (draft, used, archived)
            sketch_type: Optional sketch type filter (song, inspiration)
            sort_by: Field to sort by (created_at, updated_at, title)
            sort_direction: Sort direction (asc, desc)

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            result = sketch_service.get_sketches_paginated(
                db=db,
                limit=limit,
                offset=offset,
                search=search,
                workflow=workflow,
                sketch_type=sketch_type,
                sort_by=sort_by,
                sort_direction=sort_direction,
            )

            sketches = result.get("items", [])
            total = result.get("total", 0)

            # Enrich sketches with project_name from relationship
            enriched_sketches = []
            for sketch in sketches:
                # Extract project_name from relationship if available
                if hasattr(sketch, "project") and sketch.project:
                    sketch.project_name = sketch.project.project_name
                else:
                    sketch.project_name = None
                enriched_sketches.append(sketch)

            # Convert sketches to Pydantic models
            sketch_responses = [SketchResponse.model_validate(sketch) for sketch in enriched_sketches]

            # Create pagination metadata
            pagination = PaginationMeta(
                total=total,
                offset=offset,
                limit=limit,
                has_more=(offset + len(sketches)) < total,
            )

            response = SketchListResponse(
                data=sketch_responses,
                pagination=pagination,
            )

            return response.model_dump(), 200

        except Exception as e:
            logger.error("sketch_list_error", error=str(e), error_type=type(e).__name__)
            return {"error": f"Failed to retrieve sketches: {str(e)}"}, 500

    @staticmethod
    def get_sketch_by_id(db: Session, sketch_id: str) -> tuple[dict[str, Any], int]:
        """
        Get a specific sketch by ID

        Args:
            db: Database session
            sketch_id: UUID of the sketch

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Validate UUID format
            try:
                UUID(sketch_id)
            except ValueError:
                return {"error": "Invalid sketch ID format"}, 400

            sketch = sketch_service.get_sketch_by_id(db, sketch_id)

            if not sketch:
                return {"error": f"Sketch not found with ID: {sketch_id}"}, 404

            response = SketchResponse.model_validate(sketch)
            return {"data": response.model_dump()}, 200

        except Exception as e:
            logger.error("sketch_get_error", sketch_id=sketch_id, error=str(e), error_type=type(e).__name__)
            return {"error": f"Failed to retrieve sketch: {str(e)}"}, 500

    @staticmethod
    def update_sketch(db: Session, sketch_id: str, update_data: SketchUpdateRequest) -> tuple[dict[str, Any], int]:
        """
        Update an existing sketch (uses business layer for normalization)

        Args:
            db: Database session
            sketch_id: UUID of the sketch
            update_data: Update data (Pydantic model)

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Validate UUID format
            try:
                UUID(sketch_id)
            except ValueError:
                return {"error": "Invalid sketch ID format"}, 400

            # Get all fields that were explicitly provided in the request
            # This includes fields set to None (to allow clearing fields)
            # model_fields_set contains only fields that were actually in the request payload
            update_dict = {field: getattr(update_data, field) for field in update_data.model_fields_set}

            if not update_dict:
                return {"error": "No fields to update"}, 400

            sketch_orchestrator = SketchOrchestrator()
            sketch = sketch_orchestrator.update_sketch(db=db, sketch_id=sketch_id, update_data=update_dict)

            response = SketchResponse.model_validate(sketch)
            return {"data": response.model_dump(), "message": "Sketch updated successfully"}, 200

        except SketchOrchestratorError as e:
            if "not found" in str(e).lower():
                return {"error": f"Sketch not found with ID: {sketch_id}"}, 404
            logger.error("sketch_update_error", sketch_id=sketch_id, error=str(e))
            return {"error": f"Failed to update sketch: {str(e)}"}, 500
        except Exception as e:
            logger.error("sketch_update_error", sketch_id=sketch_id, error=str(e), error_type=type(e).__name__)
            return {"error": f"Failed to update sketch: {str(e)}"}, 500

    @staticmethod
    def delete_sketch(db: Session, sketch_id: str) -> tuple[dict[str, Any], int]:
        """
        Delete a sketch

        Args:
            db: Database session
            sketch_id: UUID of the sketch

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Validate UUID format
            try:
                UUID(sketch_id)
            except ValueError:
                return {"error": "Invalid sketch ID format"}, 400

            success = sketch_service.delete_sketch(db, sketch_id)

            if not success:
                return {"error": f"Sketch not found with ID: {sketch_id}"}, 404

            return {"message": "Sketch deleted successfully", "deleted": True}, 200

        except Exception as e:
            logger.error("sketch_delete_error", sketch_id=sketch_id, error=str(e), error_type=type(e).__name__)
            return {"error": f"Failed to delete sketch: {str(e)}"}, 500

    @staticmethod
    def duplicate_sketch(
        db: Session,
        sketch_id: str,
        duplicate_data: SketchDuplicateRequest,
    ) -> tuple[dict[str, Any], int]:
        """
        Duplicate a sketch (simple copy without translation)

        Args:
            db: Database session
            sketch_id: UUID of sketch to duplicate
            duplicate_data: Duplication options (title_suffix)

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Validate UUID format
            try:
                UUID(sketch_id)
            except ValueError:
                return {"error": "Invalid sketch ID format"}, 400

            orchestrator = SketchOrchestrator()
            duplicate = orchestrator.duplicate_sketch(
                db=db,
                original_sketch_id=sketch_id,
                new_title_suffix=duplicate_data.new_title_suffix,
            )

            response = SketchResponse.model_validate(duplicate)
            return {"data": response.model_dump(), "message": "Sketch duplicated successfully"}, 201

        except SketchOrchestratorError as e:
            if "not found" in str(e).lower():
                return {"error": f"Sketch not found with ID: {sketch_id}"}, 404
            logger.error("sketch_duplication_error", sketch_id=sketch_id, error=str(e))
            return {"error": f"Failed to duplicate sketch: {str(e)}"}, 500
        except Exception as e:
            logger.error("sketch_duplication_error", sketch_id=sketch_id, error=str(e), error_type=type(e).__name__)
            return {"error": f"Failed to duplicate sketch: {str(e)}"}, 500

    @staticmethod
    def assign_to_project(
        db: Session,
        sketch_id: str,
        project_id: str,
        folder_id: str | None = None,
    ) -> tuple[dict[str, Any], int]:
        """
        Assign sketch to a project (1:1 relationship)

        Args:
            db: Database session
            sketch_id: Sketch UUID
            project_id: Project UUID
            folder_id: Optional folder UUID

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Validate UUID formats
            try:
                UUID(sketch_id)
                UUID(project_id)
                if folder_id:
                    UUID(folder_id)
            except ValueError as e:
                return {"error": f"Invalid UUID format: {str(e)}"}, 400

            orchestrator = SketchOrchestrator()
            result = orchestrator.assign_to_project(
                db=db,
                sketch_id=sketch_id,
                project_id=project_id,
                folder_id=folder_id,
            )

            if not result:
                return {"error": "Sketch not found"}, 404

            logger.info(
                "Sketch assigned to project",
                sketch_id=sketch_id,
                project_id=project_id,
                folder_id=folder_id,
            )

            return {"success": True, "data": result}, 200

        except ValueError as e:
            logger.warning("Sketch assignment validation failed", sketch_id=sketch_id, error=str(e))
            return {"error": str(e)}, 404
        except Exception as e:
            logger.error(
                "Failed to assign sketch to project",
                sketch_id=sketch_id,
                project_id=project_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            return {"error": f"Failed to assign sketch to project: {str(e)}"}, 500

    @staticmethod
    def unassign_from_project(db: Session, sketch_id: str) -> tuple[dict[str, Any], int]:
        """
        Remove sketch from its assigned project (link only, sketch remains)

        Args:
            db: Database session
            sketch_id: Sketch UUID

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Validate UUID format
            try:
                UUID(sketch_id)
            except ValueError:
                return {"error": "Invalid sketch ID format"}, 400

            orchestrator = SketchOrchestrator()
            result = orchestrator.unassign_from_project(db=db, sketch_id=sketch_id)

            if not result:
                return {"error": "Sketch not found"}, 404

            logger.info("Sketch unassigned from project", sketch_id=sketch_id)

            return {"success": True, "data": result}, 200

        except ValueError as e:
            logger.warning("Sketch unassign validation failed", sketch_id=sketch_id, error=str(e))
            return {"error": str(e)}, 404
        except Exception as e:
            logger.error(
                "Failed to unassign sketch from project",
                sketch_id=sketch_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            return {"error": f"Failed to unassign sketch from project: {str(e)}"}, 500
