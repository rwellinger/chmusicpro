"""CRUD operations for project asset references (Images N:M)"""

from uuid import UUID

from sqlalchemy.orm import Session

from db.models import ProjectImageReference
from utils.logger import logger


def create_image_reference(
    db: Session,
    project_id: UUID,
    image_id: UUID,
    folder_id: UUID | None = None,
    display_order: int = 0,
) -> ProjectImageReference:
    """
    Create a new image-project reference (N:M)

    Args:
        db: Database session
        project_id: Project UUID
        image_id: Image UUID
        folder_id: Optional folder UUID
        display_order: Display order (default: 0)

    Returns:
        ProjectImageReference: Created reference
    """
    # Check if reference already exists
    existing = (
        db.query(ProjectImageReference)
        .filter(ProjectImageReference.project_id == project_id, ProjectImageReference.image_id == image_id)
        .first()
    )

    if existing:
        logger.warning(
            "Image reference already exists",
            project_id=str(project_id),
            image_id=str(image_id),
            existing_id=str(existing.id),
        )
        # Update folder if different
        if folder_id and existing.folder_id != folder_id:
            existing.folder_id = folder_id
            db.commit()
            db.refresh(existing)
            logger.info(
                "Updated existing image reference folder", reference_id=str(existing.id), folder_id=str(folder_id)
            )
        return existing

    reference = ProjectImageReference(
        project_id=project_id,
        image_id=image_id,
        folder_id=folder_id,
        display_order=display_order,
    )

    db.add(reference)
    db.commit()
    db.refresh(reference)

    logger.info(
        "Image reference created",
        reference_id=str(reference.id),
        project_id=str(project_id),
        image_id=str(image_id),
        folder_id=str(folder_id) if folder_id else None,
    )

    return reference


def get_image_references_by_project(db: Session, project_id: UUID) -> list[ProjectImageReference]:
    """
    Get all image references for a project

    Args:
        db: Database session
        project_id: Project UUID

    Returns:
        list[ProjectImageReference]: List of image references
    """
    references = (
        db.query(ProjectImageReference)
        .filter(ProjectImageReference.project_id == project_id)
        .order_by(ProjectImageReference.display_order, ProjectImageReference.created_at)
        .all()
    )

    logger.debug("Retrieved image references for project", project_id=str(project_id), count=len(references))
    return references


def get_image_references_by_image(db: Session, image_id: UUID) -> list[ProjectImageReference]:
    """
    Get all project references for an image (which projects use this image)

    Args:
        db: Database session
        image_id: Image UUID

    Returns:
        list[ProjectImageReference]: List of project references
    """
    references = (
        db.query(ProjectImageReference)
        .filter(ProjectImageReference.image_id == image_id)
        .order_by(ProjectImageReference.created_at)
        .all()
    )

    logger.debug("Retrieved project references for image", image_id=str(image_id), count=len(references))
    return references


def delete_image_reference(db: Session, reference_id: UUID) -> bool:
    """
    Delete an image-project reference

    Args:
        db: Database session
        reference_id: Reference UUID

    Returns:
        bool: True if deleted, False if not found
    """
    reference = db.query(ProjectImageReference).filter(ProjectImageReference.id == reference_id).first()

    if not reference:
        logger.warning("Image reference not found for deletion", reference_id=str(reference_id))
        return False

    db.delete(reference)
    db.commit()

    logger.info(
        "Image reference deleted",
        reference_id=str(reference_id),
        project_id=str(reference.project_id),
        image_id=str(reference.image_id),
    )
    return True


def delete_image_reference_by_ids(db: Session, project_id: UUID, image_id: UUID) -> bool:
    """
    Delete an image-project reference by project and image IDs

    Args:
        db: Database session
        project_id: Project UUID
        image_id: Image UUID

    Returns:
        bool: True if deleted, False if not found
    """
    reference = (
        db.query(ProjectImageReference)
        .filter(ProjectImageReference.project_id == project_id, ProjectImageReference.image_id == image_id)
        .first()
    )

    if not reference:
        logger.warning("Image reference not found for deletion", project_id=str(project_id), image_id=str(image_id))
        return False

    db.delete(reference)
    db.commit()

    logger.info("Image reference deleted", project_id=str(project_id), image_id=str(image_id))
    return True
