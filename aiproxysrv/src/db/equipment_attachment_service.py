"""
Repository layer for equipment_attachments database operations.

CRITICAL: This is a PURE CRUD layer (no business logic).
- CRUD operations ONLY
- NO file validation (that's in transformer)
- NO S3 operations (that's in orchestrator)
"""

from uuid import UUID

from sqlalchemy.orm import Session

from db.models import EquipmentAttachment
from utils.logger import logger


class EquipmentAttachmentService:
    """Repository for equipment_attachments CRUD operations"""

    def create_attachment(
        self,
        db: Session,
        equipment_id: UUID,
        user_id: UUID,
        filename: str,
        s3_key: str,
        file_size: int,
        content_type: str,
    ) -> EquipmentAttachment | None:
        """Create attachment record in database."""
        try:
            attachment = EquipmentAttachment(
                equipment_id=equipment_id,
                user_id=user_id,
                filename=filename,
                s3_key=s3_key,
                file_size=file_size,
                content_type=content_type,
            )
            db.add(attachment)
            db.commit()
            db.refresh(attachment)
            logger.debug("Attachment created", attachment_id=str(attachment.id), filename=filename)
            return attachment
        except Exception as e:
            db.rollback()
            logger.error("Failed to create attachment", error=str(e), filename=filename)
            return None

    def get_attachments_by_equipment(self, db: Session, equipment_id: UUID, user_id: UUID) -> list[EquipmentAttachment]:
        """Get all attachments for equipment (user-scoped)."""
        try:
            attachments = (
                db.query(EquipmentAttachment)
                .filter(
                    EquipmentAttachment.equipment_id == equipment_id,
                    EquipmentAttachment.user_id == user_id,
                )
                .order_by(EquipmentAttachment.uploaded_at.desc())
                .all()
            )
            return attachments
        except Exception as e:
            logger.error("Failed to get attachments", error=str(e), equipment_id=str(equipment_id))
            return []

    def get_attachment_by_id(self, db: Session, attachment_id: UUID, user_id: UUID) -> EquipmentAttachment | None:
        """Get attachment by ID (user-scoped for security)."""
        try:
            attachment = (
                db.query(EquipmentAttachment)
                .filter(
                    EquipmentAttachment.id == attachment_id,
                    EquipmentAttachment.user_id == user_id,
                )
                .first()
            )
            return attachment
        except Exception as e:
            logger.error("Failed to get attachment", error=str(e), attachment_id=str(attachment_id))
            return None

    def delete_attachment(self, db: Session, attachment_id: UUID, user_id: UUID) -> bool:
        """Delete attachment (user-scoped)."""
        try:
            attachment = self.get_attachment_by_id(db, attachment_id, user_id)
            if not attachment:
                return False

            db.delete(attachment)
            db.commit()
            logger.info("Attachment deleted", attachment_id=str(attachment_id), filename=attachment.filename)
            return True
        except Exception as e:
            db.rollback()
            logger.error("Failed to delete attachment", error=str(e), attachment_id=str(attachment_id))
            return False

    def update_s3_key(self, db: Session, attachment_id: UUID, user_id: UUID, s3_key: str) -> EquipmentAttachment | None:
        """Update S3 key after upload."""
        try:
            attachment = self.get_attachment_by_id(db, attachment_id, user_id)
            if not attachment:
                return None

            attachment.s3_key = s3_key
            db.commit()
            db.refresh(attachment)
            return attachment
        except Exception as e:
            db.rollback()
            logger.error("Failed to update s3_key", error=str(e), attachment_id=str(attachment_id))
            return None


# Global instance
equipment_attachment_service = EquipmentAttachmentService()
