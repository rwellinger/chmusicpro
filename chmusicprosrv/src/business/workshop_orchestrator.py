"""Workshop Orchestrator - Coordinates workshop operations (no testable business logic)"""

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from business.workshop_normalizer import WorkshopNormalizer
from db.sketch_service import sketch_service
from db.workshop_service import workshop_service
from utils.logger import logger


class WorkshopOrchestratorError(Exception):
    """Base exception for workshop orchestration errors"""

    pass


class WorkshopOrchestrator:
    """Orchestrates workshop operations (calls normalizer + repository)"""

    def create_workshop(
        self,
        db: Session,
        title: str,
        connect_topic: str | None = None,
        draft_language: str | None = "EN",
    ) -> Any:
        """
        Create a new workshop with data normalization

        Args:
            db: Database session
            title: Workshop title (required)
            connect_topic: Initial topic/theme (optional)

        Returns:
            Created LyricWorkshop instance

        Raises:
            WorkshopOrchestratorError: If creation fails
        """
        try:
            normalized_data = WorkshopNormalizer.normalize_workshop_data(
                {
                    "title": title,
                    "connect_topic": connect_topic,
                    "draft_language": draft_language,
                }
            )

            workshop = workshop_service.create_workshop(db=db, **normalized_data)

            if not workshop:
                raise WorkshopOrchestratorError("Failed to create workshop")

            return workshop

        except Exception as e:
            logger.error("Workshop creation failed", error=str(e), error_type=type(e).__name__)
            raise WorkshopOrchestratorError(f"Failed to create workshop: {e}") from e

    def update_workshop(
        self,
        db: Session,
        workshop_id: str | UUID,
        update_data: dict[str, Any],
    ) -> Any:
        """
        Update workshop with data normalization

        Args:
            db: Database session
            workshop_id: UUID of the workshop
            update_data: Dict with fields to update

        Returns:
            Updated LyricWorkshop instance

        Raises:
            WorkshopOrchestratorError: If update fails or workshop not found
        """
        try:
            normalized_data = WorkshopNormalizer.normalize_workshop_data(update_data)

            workshop = workshop_service.update_workshop(db=db, workshop_id=workshop_id, **normalized_data)

            if not workshop:
                raise WorkshopOrchestratorError(f"Workshop not found with ID: {workshop_id}")

            return workshop

        except WorkshopOrchestratorError:
            raise
        except Exception as e:
            logger.error(
                "Workshop update failed", workshop_id=str(workshop_id), error=str(e), error_type=type(e).__name__
            )
            raise WorkshopOrchestratorError(f"Failed to update workshop: {e}") from e

    def export_to_sketch(self, db: Session, workshop_id: str | UUID) -> Any:
        """
        Export workshop content to a new SongSketch

        Creates a SongSketch with the workshop's draft as lyrics and sets exported_sketch_id.

        Args:
            db: Database session
            workshop_id: UUID of the workshop

        Returns:
            Created SongSketch instance

        Raises:
            WorkshopOrchestratorError: If export fails
        """
        try:
            workshop = workshop_service.get_workshop_by_id(db, workshop_id)
            if not workshop:
                raise WorkshopOrchestratorError(f"Workshop not found with ID: {workshop_id}")

            # Create sketch from workshop data
            sketch = sketch_service.create_sketch(
                db=db,
                title=workshop.title,
                lyrics=workshop.shape_draft,
                prompt=workshop.connect_topic or "workshop export",
                tags=None,
                sketch_type="song",
                workflow="draft",
            )

            if not sketch:
                raise WorkshopOrchestratorError("Failed to create sketch from workshop")

            # Link workshop to exported sketch
            workshop_service.update_workshop(
                db=db,
                workshop_id=workshop_id,
                exported_sketch_id=str(sketch.id),
                current_phase="completed",
            )

            logger.info(
                "Workshop exported to sketch",
                workshop_id=str(workshop_id),
                sketch_id=str(sketch.id),
            )

            return sketch

        except WorkshopOrchestratorError:
            raise
        except Exception as e:
            logger.error(
                "Workshop export failed", workshop_id=str(workshop_id), error=str(e), error_type=type(e).__name__
            )
            raise WorkshopOrchestratorError(f"Failed to export workshop: {e}") from e
