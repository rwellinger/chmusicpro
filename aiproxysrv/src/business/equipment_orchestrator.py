"""
Equipment Orchestrator - Coordinates equipment operations with encryption and normalization.

CRITICAL: This is an ORCHESTRATOR (coordination only, NOT unit-testable per CLAUDE.md).
- Coordinates services (Normalizer, EncryptionService, EquipmentService)
- NO business logic (business logic goes in Normalizer/Transformer)
- NO direct database queries (database operations in EquipmentService)
- This layer is NOT covered by unit tests (orchestration, not logic)
"""

from uuid import UUID

from business.encryption_service import encryption_service
from business.equipment_normalizer import EquipmentNormalizer
from business.equipment_transformer import (
    generate_s3_attachment_key,
    get_content_type_from_filename,
    validate_file_extension,
    validate_file_size,
)
from config.settings import S3_EQUIPMENT_DATA_BUCKET
from db.equipment_attachment_service import equipment_attachment_service
from db.equipment_service import equipment_service
from infrastructure.storage import get_storage
from utils.logger import logger


class EquipmentOrchestratorError(Exception):
    """Custom exception for orchestrator errors"""

    pass


class EquipmentOrchestrator:
    """Coordinates equipment operations with encryption and normalization"""

    def __init__(self):
        """Initialize orchestrator with lazy S3 storage"""
        self._storage = None

    @property
    def storage(self):
        """Lazy-load S3 storage for equipment attachments bucket"""
        if self._storage is None:
            self._storage = get_storage(bucket=S3_EQUIPMENT_DATA_BUCKET)
        return self._storage

    def create_equipment(self, db, user_id: str, equipment_data: dict):
        """
        Create equipment with encryption and normalization.

        Workflow:
            1. Normalize data (via EquipmentNormalizer)
            2. Encrypt sensitive fields (password, license_key, price)
            3. Add user_id
            4. Create in database (via EquipmentService)

        Args:
            db: Database session
            user_id: User UUID (from JWT)
            equipment_data: Equipment data dict (plaintext)

        Returns:
            Created Equipment object

        Raises:
            EquipmentOrchestratorError: If creation fails

        Example:
            equipment = equipment_orchestrator.create_equipment(
                db,
                user_id="123e4567-e89b-12d3-a456-426614174000",
                equipment_data={
                    "type": "Software",
                    "name": "Logic Pro X",
                    "password": "my-secret-password",
                    "price": "299.99 EUR"
                }
            )
        """
        try:
            # 1. Normalize data
            normalized = EquipmentNormalizer.normalize_equipment_data(equipment_data)

            # 2. Encrypt sensitive fields and remove plaintext versions
            # Always remove plaintext fields (even if None/empty) to avoid SQLAlchemy errors
            password = normalized.pop("password", None)
            if password:
                normalized["password_encrypted"] = encryption_service.encrypt(password)

            license_key = normalized.pop("license_key", None)
            if license_key:
                normalized["license_key_encrypted"] = encryption_service.encrypt(license_key)

            price = normalized.pop("price", None)
            if price:
                normalized["price_encrypted"] = encryption_service.encrypt(price)

            # 3. Add user_id
            normalized["user_id"] = user_id

            # 4. Create in database
            equipment = equipment_service.create_equipment(db, **normalized)
            if not equipment:
                raise EquipmentOrchestratorError("Failed to create equipment in database")

            logger.info(
                "Equipment created successfully",
                equipment_id=str(equipment.id),
                type=equipment.type,
                name=equipment.name,
                user_id=user_id,
            )
            return equipment
        except Exception as e:
            logger.error("Equipment creation failed", error=str(e), error_type=type(e).__name__, user_id=user_id)
            raise EquipmentOrchestratorError(f"Failed to create equipment: {str(e)}")

    def get_equipment_with_decryption(self, db, equipment_id: str, user_id: str) -> dict | None:
        """
        Get equipment and decrypt sensitive fields.

        Workflow:
            1. Get equipment from database (via EquipmentService)
            2. Decrypt sensitive fields (password, license_key, price)
            3. Return as dict with decrypted fields

        Args:
            db: Database session
            equipment_id: Equipment UUID
            user_id: User UUID (from JWT)

        Returns:
            Equipment data dict with decrypted fields, or None if not found

        Example:
            equipment_dict = equipment_orchestrator.get_equipment_with_decryption(db, equipment_id, user_id)
            # {
            #     "id": "...",
            #     "name": "Logic Pro X",
            #     "password": "my-secret-password",  # Decrypted
            #     "price": "299.99 EUR",             # Decrypted
            #     ...
            # }
        """
        equipment = equipment_service.get_equipment_by_id(db, equipment_id, user_id)
        if not equipment:
            logger.warning("Equipment not found", equipment_id=equipment_id, user_id=user_id)
            return None

        # Convert to dict
        equipment_dict = {
            "id": str(equipment.id),
            "type": equipment.type,
            "name": equipment.name,
            "version": equipment.version,
            "description": equipment.description,
            "software_tags": equipment.software_tags,
            "plugin_tags": equipment.plugin_tags,
            "manufacturer": equipment.manufacturer,
            "url": equipment.url,
            "username": equipment.username,
            "license_management": equipment.license_management,
            "license_description": equipment.license_description,
            "purchase_date": equipment.purchase_date.isoformat() if equipment.purchase_date else None,
            "system_requirements": equipment.system_requirements,
            "status": equipment.status,
            "created_at": equipment.created_at.isoformat() if equipment.created_at else None,
            "updated_at": equipment.updated_at.isoformat() if equipment.updated_at else None,
        }

        # Decrypt sensitive fields
        equipment_dict["password"] = encryption_service.decrypt(equipment.password_encrypted)
        equipment_dict["license_key"] = encryption_service.decrypt(equipment.license_key_encrypted)
        equipment_dict["price"] = encryption_service.decrypt(equipment.price_encrypted)

        logger.debug("Equipment retrieved with decryption", equipment_id=equipment_id, user_id=user_id)
        return equipment_dict

    def update_equipment(self, db, equipment_id: str, user_id: str, update_data: dict):
        """
        Update equipment with encryption and normalization.

        Workflow:
            1. Normalize data (via EquipmentNormalizer)
            2. Encrypt sensitive fields if present (password, license_key, price)
            3. Update in database (via EquipmentService)

        Args:
            db: Database session
            equipment_id: Equipment UUID
            user_id: User UUID (from JWT)
            update_data: Equipment update data dict (plaintext)

        Returns:
            Updated Equipment object

        Raises:
            EquipmentOrchestratorError: If update fails

        Example:
            equipment = equipment_orchestrator.update_equipment(
                db, equipment_id, user_id, {"status": "archived", "price": "349.99 EUR"}
            )
        """
        try:
            # 1. Normalize data
            normalized = EquipmentNormalizer.normalize_equipment_data(update_data)

            # 2. Encrypt sensitive fields and remove plaintext versions
            # Always remove plaintext fields (even if None/empty) to avoid SQLAlchemy errors
            if "password" in normalized:
                password = normalized.pop("password")
                if password:
                    normalized["password_encrypted"] = encryption_service.encrypt(password)

            if "license_key" in normalized:
                license_key = normalized.pop("license_key")
                if license_key:
                    normalized["license_key_encrypted"] = encryption_service.encrypt(license_key)

            if "price" in normalized:
                price = normalized.pop("price")
                if price:
                    normalized["price_encrypted"] = encryption_service.encrypt(price)

            # 3. Update in database
            equipment = equipment_service.update_equipment(db, equipment_id, user_id, normalized)
            if not equipment:
                raise EquipmentOrchestratorError("Failed to update equipment (not found or database error)")

            logger.info(
                "Equipment updated successfully",
                equipment_id=equipment_id,
                user_id=user_id,
                fields_updated=list(update_data.keys()),
            )
            return equipment
        except Exception as e:
            logger.error(
                "Equipment update failed", error=str(e), error_type=type(e).__name__, equipment_id=equipment_id
            )
            raise EquipmentOrchestratorError(f"Failed to update equipment: {str(e)}")

    def upload_attachment(
        self,
        db,
        equipment_id: str,
        user_id: str,
        file_data: bytes,
        filename: str,
    ) -> tuple[dict | None, str | None]:
        """
        Upload attachment for equipment.

        Workflow:
            1. Validate file extension (transformer)
            2. Validate file size (transformer)
            3. Verify equipment exists and user owns it
            4. Create DB record with temporary s3_key
            5. Generate S3 key with attachment ID (transformer)
            6. Upload to S3 (infrastructure)
            7. Update DB record with real S3 key

        Args:
            db: Database session
            equipment_id: Equipment UUID
            user_id: User UUID (from JWT)
            file_data: Raw file bytes
            filename: Original filename

        Returns:
            Tuple of (attachment_data_dict, error_message)

        Example:
            result, error = equipment_orchestrator.upload_attachment(
                db, equipment_id, user_id, file_bytes, "license.pdf"
            )
        """
        try:
            # 1. Validate extension
            is_valid, error = validate_file_extension(filename)
            if not is_valid:
                return None, error

            # 2. Validate size
            file_size = len(file_data)
            is_valid, error = validate_file_size(file_size)
            if not is_valid:
                return None, error

            # 3. Verify equipment exists and user owns it
            equipment = equipment_service.get_equipment_by_id(db, equipment_id, user_id)
            if not equipment:
                return None, "Equipment not found"

            # 4. Create attachment record to get ID
            content_type = get_content_type_from_filename(filename)
            attachment = equipment_attachment_service.create_attachment(
                db=db,
                equipment_id=UUID(equipment_id),
                user_id=UUID(user_id),
                filename=filename,
                s3_key="temp",  # Will update after upload
                file_size=file_size,
                content_type=content_type,
            )

            if not attachment:
                return None, "Failed to create attachment record"

            # 5. Generate S3 key with real attachment ID
            s3_key = generate_s3_attachment_key(user_id, equipment_id, str(attachment.id), filename)

            # 6. Upload to S3
            try:
                self.storage.upload(file_data, s3_key, content_type=content_type)
            except Exception as e:
                # Rollback DB record
                equipment_attachment_service.delete_attachment(db, attachment.id, UUID(user_id))
                logger.error("S3 upload failed", error=str(e), filename=filename)
                return None, f"Failed to upload file: {str(e)}"

            # 7. Update attachment with real S3 key
            attachment = equipment_attachment_service.update_s3_key(db, attachment.id, UUID(user_id), s3_key)
            if not attachment:
                return None, "Failed to update attachment with S3 key"

            logger.info(
                "Attachment uploaded",
                attachment_id=str(attachment.id),
                filename=filename,
                equipment_id=equipment_id,
            )

            return {
                "id": str(attachment.id),
                "filename": attachment.filename,
                "file_size": attachment.file_size,
                "content_type": attachment.content_type,
                "uploaded_at": attachment.uploaded_at.isoformat(),
            }, None

        except Exception as e:
            logger.error("Upload attachment failed", error=str(e), filename=filename)
            return None, f"Upload failed: {str(e)}"

    def delete_attachment_with_cleanup(
        self,
        db,
        attachment_id: str,
        user_id: str,
    ) -> bool:
        """
        Delete attachment and cleanup S3 file.

        Args:
            db: Database session
            attachment_id: Attachment UUID
            user_id: User UUID (from JWT)

        Returns:
            True if successful
        """
        try:
            # Get attachment
            attachment = equipment_attachment_service.get_attachment_by_id(db, UUID(attachment_id), UUID(user_id))
            if not attachment:
                return False

            s3_key = attachment.s3_key

            # Delete from DB
            if not equipment_attachment_service.delete_attachment(db, UUID(attachment_id), UUID(user_id)):
                return False

            # Delete from S3
            if s3_key and s3_key != "temp":
                try:
                    self.storage.delete(s3_key)
                except Exception as e:
                    logger.warning("S3 delete failed (non-critical)", error=str(e), s3_key=s3_key)

            logger.info("Attachment deleted with cleanup", attachment_id=attachment_id)
            return True

        except Exception as e:
            logger.error("Delete attachment failed", error=str(e), attachment_id=attachment_id)
            return False


# Global instance
equipment_orchestrator = EquipmentOrchestrator()
