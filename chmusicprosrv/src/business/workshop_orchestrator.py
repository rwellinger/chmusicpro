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
        user_id: str,
        domain_id: str,
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

            workshop = workshop_service.create_workshop(db=db, user_id=user_id, domain_id=domain_id, **normalized_data)

            if not workshop:
                raise WorkshopOrchestratorError("Failed to create workshop")

            return workshop

        except Exception as e:
            logger.error("Workshop creation failed", error=str(e), error_type=type(e).__name__)
            raise WorkshopOrchestratorError(f"Failed to create workshop: {e}") from e

    def update_workshop(
        self,
        db: Session,
        domain_id: str,
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

            workshop = workshop_service.update_workshop(
                db=db, workshop_id=workshop_id, domain_id=domain_id, **normalized_data
            )

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

    def assign_to_project(
        self,
        db: Session,
        domain_id: str,
        workshop_id: str,
        project_id: str,
        folder_id: str | None = None,
    ) -> dict | None:
        """
        Assign workshop to a project (1:1 relationship)

        Args:
            db: Database session
            workshop_id: Workshop UUID
            project_id: Project UUID
            folder_id: Optional folder UUID

        Returns:
            dict: Updated workshop data or None if not found

        Raises:
            ValueError: If project or folder not found
        """
        from uuid import UUID

        from db.song_project_service import get_folder_by_id, get_project_by_id

        try:
            project = get_project_by_id(db, UUID(project_id))
            if not project:
                raise ValueError(f"Project not found: {project_id}")

            if folder_id:
                folder = get_folder_by_id(db, UUID(folder_id))
                if not folder:
                    raise ValueError(f"Folder not found: {folder_id}")
                if folder.project_id != UUID(project_id):
                    raise ValueError(f"Folder {folder_id} does not belong to project {project_id}")

            updated_workshop = workshop_service.update_workshop(
                db=db,
                workshop_id=workshop_id,
                domain_id=domain_id,
                project_id=project_id,
                project_folder_id=folder_id,
            )

            if not updated_workshop:
                return None

            logger.info(
                "Workshop assigned to project",
                workshop_id=workshop_id,
                project_id=project_id,
                folder_id=folder_id,
            )

            return {
                "id": str(updated_workshop.id),
                "title": updated_workshop.title,
                "project_id": str(updated_workshop.project_id) if updated_workshop.project_id else None,
                "project_folder_id": str(updated_workshop.project_folder_id)
                if updated_workshop.project_folder_id
                else None,
            }

        except Exception as e:
            logger.error(
                "Failed to assign workshop to project",
                workshop_id=workshop_id,
                project_id=project_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    def unassign_from_project(self, db: Session, domain_id: str, workshop_id: str) -> dict | None:
        """
        Remove workshop from its assigned project (link only, workshop remains)

        Args:
            db: Database session
            workshop_id: Workshop UUID

        Returns:
            dict: Updated workshop data or None if not found
        """
        try:
            updated_workshop = workshop_service.update_workshop(
                db=db,
                workshop_id=workshop_id,
                domain_id=domain_id,
                clear_project=True,
            )

            if not updated_workshop:
                return None

            logger.info("Workshop unassigned from project", workshop_id=workshop_id)

            return {
                "id": str(updated_workshop.id),
                "title": updated_workshop.title,
                "project_id": None,
                "project_folder_id": None,
            }

        except Exception as e:
            logger.error(
                "Failed to unassign workshop from project",
                workshop_id=workshop_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    def export_to_sketch(self, db: Session, user_id: str, domain_id: str, workshop_id: str | UUID) -> Any:
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
            workshop = workshop_service.get_workshop_by_id(db, workshop_id, domain_id=domain_id)
            if not workshop:
                raise WorkshopOrchestratorError(f"Workshop not found with ID: {workshop_id}")

            # Create sketch from workshop data (inherits domain + user_id as audit)
            sketch = sketch_service.create_sketch(
                db=db,
                user_id=user_id,
                domain_id=domain_id,
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
                domain_id=domain_id,
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
