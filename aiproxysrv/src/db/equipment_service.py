"""
Repository layer for equipment database operations.

CRITICAL: This is a PURE CRUD layer (no business logic, no encryption).
- Business logic goes in src/business/equipment_orchestrator.py
- Encryption handled in orchestrator layer
- This layer ONLY does database operations
"""

import uuid

from sqlalchemy import or_
from sqlalchemy.orm import Session

from db.models import Equipment
from utils.logger import logger


class EquipmentService:
    """Repository for equipment database operations (CRUD only)"""

    def create_equipment(self, db: Session, **kwargs) -> Equipment | None:
        """
        Create new equipment entry.

        Args:
            db: Database session
            **kwargs: Equipment fields (including encrypted fields)

        Returns:
            Created Equipment object or None on failure

        Example:
            equipment = equipment_service.create_equipment(
                db=db,
                type="Software",
                name="Logic Pro X",
                user_id=user_id,
                password_encrypted=encrypted_password
            )
        """
        try:
            equipment = Equipment(**kwargs)
            db.add(equipment)
            db.commit()
            db.refresh(equipment)
            logger.debug(
                "Equipment created",
                equipment_id=str(equipment.id),
                type=equipment.type,
                name=equipment.name,
                user_id=str(equipment.user_id),
            )
            return equipment
        except Exception as e:
            db.rollback()
            logger.error(
                "Failed to create equipment",
                error=str(e),
                error_type=type(e).__name__,
                equipment_type=kwargs.get("type"),
            )
            return None

    def get_equipment_by_id(self, db: Session, equipment_id: str, user_id: str) -> Equipment | None:
        """
        Get equipment by ID (user-scoped for security).

        Args:
            db: Database session
            equipment_id: Equipment UUID
            user_id: User UUID (JWT)

        Returns:
            Equipment object or None if not found

        Example:
            equipment = equipment_service.get_equipment_by_id(db, equipment_id, user_id)
        """
        try:
            equipment = (
                db.query(Equipment)
                .filter(Equipment.id == uuid.UUID(equipment_id), Equipment.user_id == uuid.UUID(user_id))
                .first()
            )
            if equipment:
                logger.debug("Equipment retrieved", equipment_id=equipment_id, user_id=user_id)
            return equipment
        except Exception as e:
            logger.error("Failed to get equipment", error=str(e), equipment_id=equipment_id, user_id=user_id)
            return None

    def get_equipment_paginated(
        self,
        db: Session,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        type_filter: str | None = None,
        status_filter: str | None = None,
        search: str | None = None,
    ) -> dict:
        """
        Get paginated equipment list with filters.

        Args:
            db: Database session
            user_id: User UUID (JWT)
            limit: Items per page (max 100)
            offset: Pagination offset
            type_filter: Filter by type ('Software' | 'Plugin')
            status_filter: Filter by status ('active' | 'trial' | 'expired' | 'archived')
            search: Search in name, manufacturer, tags

        Returns:
            Dict with 'data' (list of Equipment) and 'pagination' metadata

        Example:
            result = equipment_service.get_equipment_paginated(
                db, user_id, limit=20, offset=0, type_filter='Software', search='Logic'
            )
            # {'data': [...], 'pagination': {'total': 42, 'limit': 20, 'offset': 0, 'has_more': True}}
        """
        try:
            query = db.query(Equipment).filter(Equipment.user_id == uuid.UUID(user_id))

            # Apply filters
            if type_filter:
                query = query.filter(Equipment.type == type_filter)
            if status_filter:
                query = query.filter(Equipment.status == status_filter)
            if search:
                search_pattern = f"%{search}%"
                query = query.filter(
                    or_(
                        Equipment.name.ilike(search_pattern),
                        Equipment.manufacturer.ilike(search_pattern),
                        Equipment.software_tags.ilike(search_pattern),
                        Equipment.plugin_tags.ilike(search_pattern),
                    )
                )

            # Get total count
            total = query.count()

            # Apply pagination (sorted alphabetically by name)
            equipment_list = query.order_by(Equipment.name.asc()).offset(offset).limit(limit).all()

            logger.debug(
                "Equipment list retrieved",
                total=total,
                limit=limit,
                offset=offset,
                user_id=user_id,
                type_filter=type_filter,
                status_filter=status_filter,
                search=search,
            )

            return {
                "data": equipment_list,
                "pagination": {"total": total, "limit": limit, "offset": offset, "has_more": (offset + limit) < total},
            }
        except Exception as e:
            logger.error("Failed to get equipment list", error=str(e), user_id=user_id)
            return {"data": [], "pagination": {"total": 0, "limit": limit, "offset": offset, "has_more": False}}

    def update_equipment(self, db: Session, equipment_id: str, user_id: str, update_data: dict) -> Equipment | None:
        """
        Update equipment (user-scoped for security).

        Args:
            db: Database session
            equipment_id: Equipment UUID
            user_id: User UUID (JWT)
            update_data: Dict with fields to update (including encrypted fields)

        Returns:
            Updated Equipment object or None on failure

        Example:
            equipment = equipment_service.update_equipment(
                db, equipment_id, user_id, {'name': 'New Name', 'status': 'archived'}
            )
        """
        try:
            equipment = self.get_equipment_by_id(db, equipment_id, user_id)
            if not equipment:
                logger.warning("Equipment not found for update", equipment_id=equipment_id, user_id=user_id)
                return None

            # Update fields
            for key, value in update_data.items():
                if hasattr(equipment, key):
                    setattr(equipment, key, value)

            db.commit()
            db.refresh(equipment)
            logger.debug(
                "Equipment updated",
                equipment_id=equipment_id,
                user_id=user_id,
                fields_updated=list(update_data.keys()),
            )
            return equipment
        except Exception as e:
            db.rollback()
            logger.error("Failed to update equipment", error=str(e), equipment_id=equipment_id, user_id=user_id)
            return None

    def delete_equipment(self, db: Session, equipment_id: str, user_id: str) -> bool:
        """
        Delete equipment (user-scoped for security).

        Args:
            db: Database session
            equipment_id: Equipment UUID
            user_id: User UUID (JWT)

        Returns:
            True if deleted, False if not found or error

        Example:
            success = equipment_service.delete_equipment(db, equipment_id, user_id)
        """
        try:
            equipment = self.get_equipment_by_id(db, equipment_id, user_id)
            if not equipment:
                logger.warning("Equipment not found for deletion", equipment_id=equipment_id, user_id=user_id)
                return False

            db.delete(equipment)
            db.commit()
            logger.info("Equipment deleted", equipment_id=equipment_id, user_id=user_id, name=equipment.name)
            return True
        except Exception as e:
            db.rollback()
            logger.error("Failed to delete equipment", error=str(e), equipment_id=equipment_id, user_id=user_id)
            return False


# Global instance
equipment_service = EquipmentService()
