"""Controller for model context window management"""

from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from business.model_context_window_orchestrator import model_context_window_orchestrator
from schemas.model_context_window_schemas import (
    ModelContextWindowCreate,
    ModelContextWindowListResponse,
    ModelContextWindowResponse,
    ModelContextWindowUpdate,
)
from utils.logger import logger


class ModelContextWindowController:
    """Controller for model context window CRUD operations (admin-only)"""

    @staticmethod
    def list_entries(db: Session) -> tuple[dict[str, Any], int]:
        """Get all model context window entries"""
        try:
            entries = model_context_window_orchestrator.list_all(db)
            items = [ModelContextWindowResponse.model_validate(e) for e in entries]
            response = ModelContextWindowListResponse(items=items, total=len(items))
            return response.model_dump(), 200
        except Exception as e:
            logger.error("model_context_window_list_failed", error=str(e))
            return {"error": f"Failed to retrieve entries: {str(e)}"}, 500

    @staticmethod
    def create_entry(db: Session, data: ModelContextWindowCreate) -> tuple[dict[str, Any], int]:
        """Create a new model context window entry"""
        try:
            entry = model_context_window_orchestrator.create_entry(
                db,
                model_name=data.model_name,
                context_window=data.context_window,
                provider=data.provider,
                description=data.description,
            )
            response = ModelContextWindowResponse.model_validate(entry)
            return response.model_dump(), 201
        except IntegrityError:
            db.rollback()
            return {"error": f"Model '{data.model_name}' already exists"}, 409
        except Exception as e:
            db.rollback()
            logger.error("model_context_window_create_failed", error=str(e))
            return {"error": f"Failed to create entry: {str(e)}"}, 500

    @staticmethod
    def update_entry(db: Session, entry_id: int, data: ModelContextWindowUpdate) -> tuple[dict[str, Any], int]:
        """Update an existing model context window entry"""
        try:
            update_data = data.model_dump(exclude_unset=True)
            if not update_data:
                return {"error": "No fields to update"}, 400

            entry = model_context_window_orchestrator.update_entry(db, entry_id, update_data)
            if not entry:
                return {"error": f"Entry with ID {entry_id} not found"}, 404

            response = ModelContextWindowResponse.model_validate(entry)
            return response.model_dump(), 200
        except IntegrityError:
            db.rollback()
            return {"error": f"Model name '{data.model_name}' already exists"}, 409
        except Exception as e:
            db.rollback()
            logger.error("model_context_window_update_failed", id=entry_id, error=str(e))
            return {"error": f"Failed to update entry: {str(e)}"}, 500

    @staticmethod
    def delete_entry(db: Session, entry_id: int) -> tuple[dict[str, Any], int]:
        """Delete a model context window entry"""
        try:
            deleted = model_context_window_orchestrator.delete_entry(db, entry_id)
            if not deleted:
                return {"error": f"Entry with ID {entry_id} not found"}, 404
            return {"message": f"Entry with ID {entry_id} has been deleted"}, 200
        except Exception as e:
            db.rollback()
            logger.error("model_context_window_delete_failed", id=entry_id, error=str(e))
            return {"error": f"Failed to delete entry: {str(e)}"}, 500
