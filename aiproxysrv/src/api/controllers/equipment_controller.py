"""
Equipment Controller - HTTP request/response handling for equipment API.

CRITICAL: This is the HTTP LAYER (Pydantic validation + response formatting).
- Input validation with Pydantic
- Call orchestrator for business logic
- Format responses
- HTTP status codes
"""

from datetime import date

from pydantic import BaseModel, Field

from business.equipment_orchestrator import EquipmentOrchestratorError, equipment_orchestrator
from db.equipment_service import equipment_service
from utils.logger import logger


# ===================================
# Pydantic Schemas (Request/Response)
# ===================================


class EquipmentCreateRequest(BaseModel):
    """Schema for creating new equipment"""

    type: str = Field(..., description="Equipment type: Software or Plugin", min_length=1, max_length=50)
    name: str = Field(..., description="Equipment name", min_length=1, max_length=200)
    version: str | None = Field(None, description="Software/Plugin version", max_length=100)
    description: str | None = Field(None, description="Detailed description")
    software_tags: str | None = Field(None, description="Comma-separated software tags", max_length=1000)
    plugin_tags: str | None = Field(None, description="Comma-separated plugin tags", max_length=1000)
    manufacturer: str | None = Field(None, description="Manufacturer name", max_length=200)
    url: str | None = Field(None, description="Manufacturer website URL", max_length=500)
    username: str | None = Field(None, description="Login username", max_length=200)
    password: str | None = Field(None, description="Login password (will be encrypted)")
    license_management: str | None = Field(
        None, description="License type: online, ilok, license_key, other", max_length=100
    )
    license_key: str | None = Field(None, description="License key (will be encrypted)")
    license_description: str | None = Field(None, description="License description for 'other' type")
    purchase_date: date | None = Field(None, description="Purchase date (YYYY-MM-DD)")
    price: str | None = Field(None, description="Price with currency (e.g., 299.99 EUR) - will be encrypted")
    system_requirements: str | None = Field(None, description="System requirements")
    status: str = Field(default="active", description="Status: active, trial, expired, archived", max_length=50)


class EquipmentUpdateRequest(BaseModel):
    """Schema for updating existing equipment (all fields optional)"""

    name: str | None = Field(None, min_length=1, max_length=200)
    version: str | None = Field(None, max_length=100)
    description: str | None = None
    software_tags: str | None = Field(None, max_length=1000)
    plugin_tags: str | None = Field(None, max_length=1000)
    manufacturer: str | None = Field(None, max_length=200)
    url: str | None = Field(None, max_length=500)
    username: str | None = Field(None, max_length=200)
    password: str | None = None
    license_management: str | None = Field(None, max_length=100)
    license_key: str | None = None
    license_description: str | None = None
    purchase_date: date | None = None
    price: str | None = None
    system_requirements: str | None = None
    status: str | None = Field(None, max_length=50)


class EquipmentResponse(BaseModel):
    """Schema for equipment response (with decrypted fields)"""

    id: str
    type: str
    name: str
    version: str | None
    description: str | None
    software_tags: str | None
    plugin_tags: str | None
    manufacturer: str | None
    url: str | None
    username: str | None
    password: str | None  # Decrypted
    license_management: str | None
    license_key: str | None  # Decrypted
    license_description: str | None
    purchase_date: str | None  # ISO format string
    price: str | None  # Decrypted
    system_requirements: str | None
    status: str
    created_at: str  # ISO format string
    updated_at: str | None  # ISO format string


class EquipmentListItem(BaseModel):
    """Schema for equipment list item (minimal data, no sensitive fields)"""

    id: str
    type: str
    name: str
    manufacturer: str | None
    status: str
    created_at: str


class EquipmentListResponse(BaseModel):
    """Schema for paginated equipment list"""

    data: list[EquipmentListItem]
    pagination: dict


# ===================================
# Controller
# ===================================


class EquipmentController:
    """HTTP request/response handling for equipment"""

    @staticmethod
    def create_equipment(db, user_id: str, equipment_data: EquipmentCreateRequest) -> tuple[dict, int]:
        """
        Create new equipment.

        Args:
            db: Database session
            user_id: User UUID (from JWT)
            equipment_data: Validated equipment data

        Returns:
            Tuple of (response_dict, status_code)

        Example:
            result, status_code = EquipmentController.create_equipment(db, user_id, equipment_data)
            # ({'data': {'id': '...'}, 'message': 'Equipment created successfully'}, 201)
        """
        try:
            equipment = equipment_orchestrator.create_equipment(
                db, user_id, equipment_data.model_dump(exclude_none=True)
            )
            logger.info("Equipment created via API", equipment_id=str(equipment.id), user_id=user_id)
            return {"data": {"id": str(equipment.id)}, "message": "Equipment created successfully"}, 201
        except EquipmentOrchestratorError as e:
            logger.error("Equipment creation failed via API", error=str(e), user_id=user_id)
            return {"error": f"Failed to create equipment: {str(e)}"}, 500
        except Exception as e:
            logger.error("Unexpected error in equipment creation", error=str(e), error_type=type(e).__name__)
            return {"error": "Internal server error"}, 500

    @staticmethod
    def get_equipment(db, equipment_id: str, user_id: str) -> tuple[dict, int]:
        """
        Get equipment by ID with decrypted sensitive fields.

        Args:
            db: Database session
            equipment_id: Equipment UUID
            user_id: User UUID (from JWT)

        Returns:
            Tuple of (response_dict, status_code)

        Example:
            result, status_code = EquipmentController.get_equipment(db, equipment_id, user_id)
            # ({'data': {...}}, 200) or ({'error': 'Equipment not found'}, 404)
        """
        try:
            equipment_dict = equipment_orchestrator.get_equipment_with_decryption(db, equipment_id, user_id)
            if not equipment_dict:
                logger.warning("Equipment not found via API", equipment_id=equipment_id, user_id=user_id)
                return {"error": "Equipment not found"}, 404

            logger.debug("Equipment retrieved via API", equipment_id=equipment_id, user_id=user_id)
            return {"data": equipment_dict}, 200
        except Exception as e:
            logger.error("Failed to get equipment via API", error=str(e), equipment_id=equipment_id, user_id=user_id)
            return {"error": "Internal server error"}, 500

    @staticmethod
    def list_equipment(
        db,
        user_id: str,
        limit: int,
        offset: int,
        type_filter: str | None,
        status_filter: str | None,
        search: str | None,
    ) -> tuple[dict, int]:
        """
        List equipment with pagination and filters (no sensitive fields).

        Args:
            db: Database session
            user_id: User UUID (from JWT)
            limit: Items per page
            offset: Pagination offset
            type_filter: Filter by type
            status_filter: Filter by status
            search: Search term

        Returns:
            Tuple of (response_dict, status_code)

        Example:
            result, status_code = EquipmentController.list_equipment(db, user_id, 20, 0, None, None, None)
            # ({'data': [...], 'pagination': {...}}, 200)
        """
        try:
            result = equipment_service.get_equipment_paginated(
                db, user_id, limit, offset, type_filter, status_filter, search
            )

            # Convert to list response format (no sensitive fields)
            equipment_list = [
                {
                    "id": str(eq.id),
                    "type": eq.type,
                    "name": eq.name,
                    "manufacturer": eq.manufacturer,
                    "status": eq.status,
                    "created_at": eq.created_at.isoformat() if eq.created_at else None,
                }
                for eq in result["data"]
            ]

            logger.debug(
                "Equipment list retrieved via API",
                total=result["pagination"]["total"],
                limit=limit,
                offset=offset,
                user_id=user_id,
            )
            return {"data": equipment_list, "pagination": result["pagination"]}, 200
        except Exception as e:
            logger.error("Failed to list equipment via API", error=str(e), user_id=user_id)
            return {"error": "Internal server error"}, 500

    @staticmethod
    def update_equipment(db, equipment_id: str, user_id: str, update_data: EquipmentUpdateRequest) -> tuple[dict, int]:
        """
        Update equipment.

        Args:
            db: Database session
            equipment_id: Equipment UUID
            user_id: User UUID (from JWT)
            update_data: Validated update data

        Returns:
            Tuple of (response_dict, status_code)

        Example:
            result, status_code = EquipmentController.update_equipment(db, equipment_id, user_id, update_data)
            # ({'data': {'id': '...'}, 'message': 'Equipment updated successfully'}, 200)
        """
        try:
            equipment = equipment_orchestrator.update_equipment(
                db, equipment_id, user_id, update_data.model_dump(exclude_none=True)
            )
            logger.info("Equipment updated via API", equipment_id=equipment_id, user_id=user_id)
            return {"data": {"id": str(equipment.id)}, "message": "Equipment updated successfully"}, 200
        except EquipmentOrchestratorError as e:
            logger.error("Equipment update failed via API", error=str(e), equipment_id=equipment_id, user_id=user_id)
            return {"error": f"Failed to update equipment: {str(e)}"}, 500
        except Exception as e:
            logger.error(
                "Unexpected error in equipment update", error=str(e), equipment_id=equipment_id, user_id=user_id
            )
            return {"error": "Internal server error"}, 500

    @staticmethod
    def delete_equipment(db, equipment_id: str, user_id: str) -> tuple[dict, int]:
        """
        Delete equipment.

        Args:
            db: Database session
            equipment_id: Equipment UUID
            user_id: User UUID (from JWT)

        Returns:
            Tuple of (response_dict, status_code)

        Example:
            result, status_code = EquipmentController.delete_equipment(db, equipment_id, user_id)
            # ({'message': 'Equipment deleted successfully'}, 200) or ({'error': 'Equipment not found'}, 404)
        """
        try:
            success = equipment_service.delete_equipment(db, equipment_id, user_id)
            if not success:
                logger.warning("Equipment not found for deletion via API", equipment_id=equipment_id, user_id=user_id)
                return {"error": "Equipment not found"}, 404

            logger.info("Equipment deleted via API", equipment_id=equipment_id, user_id=user_id)
            return {"message": "Equipment deleted successfully"}, 200
        except Exception as e:
            logger.error("Failed to delete equipment via API", error=str(e), equipment_id=equipment_id, user_id=user_id)
            return {"error": "Internal server error"}, 500
