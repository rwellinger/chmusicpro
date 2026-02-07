"""Controller for workshop management"""

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from business.workshop_orchestrator import WorkshopOrchestrator, WorkshopOrchestratorError
from db.workshop_service import workshop_service
from schemas.common_schemas import PaginationMeta
from schemas.sketch_schemas import SketchResponse
from schemas.workshop_schemas import (
    WorkshopCreateRequest,
    WorkshopListResponse,
    WorkshopResponse,
    WorkshopUpdateRequest,
)
from utils.logger import logger


class WorkshopController:
    """Controller for workshop operations"""

    @staticmethod
    def create_workshop(db: Session, workshop_data: WorkshopCreateRequest) -> tuple[dict[str, Any], int]:
        """
        Create a new workshop (uses business layer for normalization)

        Args:
            db: Database session
            workshop_data: Workshop creation data (Pydantic model)

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            orchestrator = WorkshopOrchestrator()
            workshop = orchestrator.create_workshop(
                db=db,
                title=workshop_data.title,
                connect_topic=workshop_data.connect_topic,
                draft_language=workshop_data.draft_language,
            )

            response = WorkshopResponse.model_validate(workshop)
            return {"data": response.model_dump(), "message": "Workshop created successfully"}, 201

        except WorkshopOrchestratorError as e:
            logger.error("workshop_creation_error", error=str(e))
            return {"error": f"Failed to create workshop: {str(e)}"}, 500
        except Exception as e:
            logger.error("workshop_creation_error", error=str(e), error_type=type(e).__name__)
            return {"error": f"Failed to create workshop: {str(e)}"}, 500

    @staticmethod
    def get_workshops(
        db: Session,
        limit: int = 20,
        offset: int = 0,
        search: str = "",
        phase: str | None = None,
        sort_by: str = "created_at",
        sort_direction: str = "desc",
    ) -> tuple[dict[str, Any], int]:
        """
        Get list of workshops with pagination, search and filtering

        Args:
            db: Database session
            limit: Number of workshops to return
            offset: Number of workshops to skip
            search: Search term to filter by title or connect_topic
            phase: Optional phase filter (connect, collect, shape, completed)
            sort_by: Field to sort by (created_at, updated_at, title)
            sort_direction: Sort direction (asc, desc)

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            result = workshop_service.get_workshops_paginated(
                db=db,
                limit=limit,
                offset=offset,
                search=search,
                phase=phase,
                sort_by=sort_by,
                sort_direction=sort_direction,
            )

            workshops = result.get("items", [])
            total = result.get("total", 0)

            workshop_responses = [WorkshopResponse.model_validate(w) for w in workshops]

            pagination = PaginationMeta(
                total=total,
                offset=offset,
                limit=limit,
                has_more=(offset + len(workshops)) < total,
            )

            response = WorkshopListResponse(
                data=workshop_responses,
                pagination=pagination,
            )

            return response.model_dump(), 200

        except Exception as e:
            logger.error("workshop_list_error", error=str(e), error_type=type(e).__name__)
            return {"error": f"Failed to retrieve workshops: {str(e)}"}, 500

    @staticmethod
    def get_workshop_by_id(db: Session, workshop_id: str) -> tuple[dict[str, Any], int]:
        """
        Get a specific workshop by ID

        Args:
            db: Database session
            workshop_id: UUID of the workshop

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            try:
                UUID(workshop_id)
            except ValueError:
                return {"error": "Invalid workshop ID format"}, 400

            workshop = workshop_service.get_workshop_by_id(db, workshop_id)

            if not workshop:
                return {"error": f"Workshop not found with ID: {workshop_id}"}, 404

            response = WorkshopResponse.model_validate(workshop)
            return {"data": response.model_dump()}, 200

        except Exception as e:
            logger.error("workshop_get_error", workshop_id=workshop_id, error=str(e), error_type=type(e).__name__)
            return {"error": f"Failed to retrieve workshop: {str(e)}"}, 500

    @staticmethod
    def update_workshop(
        db: Session, workshop_id: str, update_data: WorkshopUpdateRequest
    ) -> tuple[dict[str, Any], int]:
        """
        Update an existing workshop (uses business layer for normalization)

        Args:
            db: Database session
            workshop_id: UUID of the workshop
            update_data: Update data (Pydantic model)

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            try:
                UUID(workshop_id)
            except ValueError:
                return {"error": "Invalid workshop ID format"}, 400

            update_dict = {field: getattr(update_data, field) for field in update_data.model_fields_set}

            if not update_dict:
                return {"error": "No fields to update"}, 400

            orchestrator = WorkshopOrchestrator()
            workshop = orchestrator.update_workshop(db=db, workshop_id=workshop_id, update_data=update_dict)

            response = WorkshopResponse.model_validate(workshop)
            return {"data": response.model_dump(), "message": "Workshop updated successfully"}, 200

        except WorkshopOrchestratorError as e:
            if "not found" in str(e).lower():
                return {"error": f"Workshop not found with ID: {workshop_id}"}, 404
            logger.error("workshop_update_error", workshop_id=workshop_id, error=str(e))
            return {"error": f"Failed to update workshop: {str(e)}"}, 500
        except Exception as e:
            logger.error("workshop_update_error", workshop_id=workshop_id, error=str(e), error_type=type(e).__name__)
            return {"error": f"Failed to update workshop: {str(e)}"}, 500

    @staticmethod
    def delete_workshop(db: Session, workshop_id: str) -> tuple[dict[str, Any], int]:
        """
        Delete a workshop

        Args:
            db: Database session
            workshop_id: UUID of the workshop

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            try:
                UUID(workshop_id)
            except ValueError:
                return {"error": "Invalid workshop ID format"}, 400

            success = workshop_service.delete_workshop(db, workshop_id)

            if not success:
                return {"error": f"Workshop not found with ID: {workshop_id}"}, 404

            return {"message": "Workshop deleted successfully", "deleted": True}, 200

        except Exception as e:
            logger.error("workshop_delete_error", workshop_id=workshop_id, error=str(e), error_type=type(e).__name__)
            return {"error": f"Failed to delete workshop: {str(e)}"}, 500

    @staticmethod
    def export_to_sketch(db: Session, workshop_id: str) -> tuple[dict[str, Any], int]:
        """
        Export workshop to a new SongSketch

        Args:
            db: Database session
            workshop_id: UUID of the workshop

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            try:
                UUID(workshop_id)
            except ValueError:
                return {"error": "Invalid workshop ID format"}, 400

            orchestrator = WorkshopOrchestrator()
            sketch = orchestrator.export_to_sketch(db=db, workshop_id=workshop_id)

            response = SketchResponse.model_validate(sketch)
            return {"data": response.model_dump(), "message": "Workshop exported to sketch successfully"}, 201

        except WorkshopOrchestratorError as e:
            if "not found" in str(e).lower():
                return {"error": f"Workshop not found with ID: {workshop_id}"}, 404
            logger.error("workshop_export_error", workshop_id=workshop_id, error=str(e))
            return {"error": f"Failed to export workshop: {str(e)}"}, 500
        except Exception as e:
            logger.error("workshop_export_error", workshop_id=workshop_id, error=str(e), error_type=type(e).__name__)
            return {"error": f"Failed to export workshop: {str(e)}"}, 500
