"""Controller for suno template management"""

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from business.suno_template_orchestrator import SunoTemplateOrchestrator, SunoTemplateOrchestratorError
from db.suno_template_service import suno_template_service
from schemas.common_schemas import PaginationMeta
from schemas.suno_template_schemas import (
    SunoTemplateCreateRequest,
    SunoTemplateListResponse,
    SunoTemplateResponse,
    SunoTemplateUpdateRequest,
)
from utils.logger import logger


class SunoTemplateController:
    """Controller for suno template operations"""

    @staticmethod
    def create_template(
        db: Session, user_id: str, domain_id: str, template_data: SunoTemplateCreateRequest
    ) -> tuple[dict[str, Any], int]:
        """Create a new suno template"""
        try:
            orchestrator = SunoTemplateOrchestrator()
            template = orchestrator.create_template(
                db=db,
                user_id=user_id,
                domain_id=domain_id,
                title=template_data.title,
                template_type=template_data.template_type,
                enhanced_lyrics=template_data.enhanced_lyrics,
                genre=template_data.genre,
                bpm=template_data.bpm,
                vocal_type=template_data.vocal_type,
                instruments=template_data.instruments,
                mood=template_data.mood,
                mix_character=template_data.mix_character,
                style_prompt=template_data.style_prompt,
                is_instrumental=template_data.is_instrumental,
            )

            response = SunoTemplateResponse.model_validate(template)
            return {"data": response.model_dump(), "message": "Suno template created successfully"}, 201

        except SunoTemplateOrchestratorError as e:
            logger.error("suno_template_creation_error", error=str(e))
            return {"error": f"Failed to create suno template: {str(e)}"}, 500
        except Exception as e:
            logger.error("suno_template_creation_error", error=str(e), error_type=type(e).__name__)
            return {"error": f"Failed to create suno template: {str(e)}"}, 500

    @staticmethod
    def get_templates(
        db: Session,
        domain_id: str,
        limit: int = 20,
        offset: int = 0,
        search: str = "",
        template_type: str | None = None,
        sort_by: str = "created_at",
        sort_direction: str = "desc",
    ) -> tuple[dict[str, Any], int]:
        """Get list of suno templates with pagination, search and filtering"""
        try:
            result = suno_template_service.get_templates_paginated(
                db=db,
                domain_id=domain_id,
                limit=limit,
                offset=offset,
                search=search,
                template_type=template_type,
                sort_by=sort_by,
                sort_direction=sort_direction,
            )

            templates = result.get("items", [])
            total = result.get("total", 0)

            # Enrich templates with project_name from relationship
            for template in templates:
                if hasattr(template, "project") and template.project:
                    template.project_name = template.project.project_name
                else:
                    template.project_name = None

            template_responses = [SunoTemplateResponse.model_validate(t) for t in templates]

            pagination = PaginationMeta(
                total=total,
                offset=offset,
                limit=limit,
                has_more=(offset + len(templates)) < total,
            )

            response = SunoTemplateListResponse(
                data=template_responses,
                pagination=pagination,
            )

            return response.model_dump(), 200

        except Exception as e:
            logger.error("suno_template_list_error", error=str(e), error_type=type(e).__name__)
            return {"error": f"Failed to retrieve suno templates: {str(e)}"}, 500

    @staticmethod
    def get_template_by_id(db: Session, domain_id: str, template_id: str) -> tuple[dict[str, Any], int]:
        """Get a specific suno template by ID"""
        try:
            try:
                UUID(template_id)
            except ValueError:
                return {"error": "Invalid template ID format"}, 400

            template = suno_template_service.get_template_by_id(db, template_id, domain_id=domain_id)

            if not template:
                return {"error": f"Suno template not found with ID: {template_id}"}, 404

            # Enrich with project_name
            if hasattr(template, "project") and template.project:
                template.project_name = template.project.project_name
            else:
                template.project_name = None

            response = SunoTemplateResponse.model_validate(template)
            return {"data": response.model_dump()}, 200

        except Exception as e:
            logger.error("suno_template_get_error", template_id=template_id, error=str(e), error_type=type(e).__name__)
            return {"error": f"Failed to retrieve suno template: {str(e)}"}, 500

    @staticmethod
    def update_template(
        db: Session, domain_id: str, template_id: str, update_data: SunoTemplateUpdateRequest
    ) -> tuple[dict[str, Any], int]:
        """Update an existing suno template"""
        try:
            try:
                UUID(template_id)
            except ValueError:
                return {"error": "Invalid template ID format"}, 400

            update_dict = {field: getattr(update_data, field) for field in update_data.model_fields_set}

            if not update_dict:
                return {"error": "No fields to update"}, 400

            orchestrator = SunoTemplateOrchestrator()
            template = orchestrator.update_template(
                db=db, domain_id=domain_id, template_id=template_id, update_data=update_dict
            )

            # Enrich with project_name
            if hasattr(template, "project") and template.project:
                template.project_name = template.project.project_name
            else:
                template.project_name = None

            response = SunoTemplateResponse.model_validate(template)
            return {"data": response.model_dump(), "message": "Suno template updated successfully"}, 200

        except SunoTemplateOrchestratorError as e:
            if "not found" in str(e).lower():
                return {"error": f"Suno template not found with ID: {template_id}"}, 404
            logger.error("suno_template_update_error", template_id=template_id, error=str(e))
            return {"error": f"Failed to update suno template: {str(e)}"}, 500
        except Exception as e:
            logger.error(
                "suno_template_update_error", template_id=template_id, error=str(e), error_type=type(e).__name__
            )
            return {"error": f"Failed to update suno template: {str(e)}"}, 500

    @staticmethod
    def delete_template(db: Session, domain_id: str, template_id: str) -> tuple[dict[str, Any], int]:
        """Delete a suno template"""
        try:
            try:
                UUID(template_id)
            except ValueError:
                return {"error": "Invalid template ID format"}, 400

            success = suno_template_service.delete_template(db, template_id, domain_id=domain_id)

            if not success:
                return {"error": f"Suno template not found with ID: {template_id}"}, 404

            return {"message": "Suno template deleted successfully", "deleted": True}, 200

        except Exception as e:
            logger.error(
                "suno_template_delete_error", template_id=template_id, error=str(e), error_type=type(e).__name__
            )
            return {"error": f"Failed to delete suno template: {str(e)}"}, 500

    @staticmethod
    def create_from_sketch(db: Session, user_id: str, domain_id: str, sketch_id: str) -> tuple[dict[str, Any], int]:
        """Create a suno template from a sketch (Song-Modus)"""
        try:
            try:
                UUID(sketch_id)
            except ValueError:
                return {"error": "Invalid sketch ID format"}, 400

            orchestrator = SunoTemplateOrchestrator()
            template = orchestrator.create_from_sketch(db=db, user_id=user_id, domain_id=domain_id, sketch_id=sketch_id)

            response = SunoTemplateResponse.model_validate(template)
            return {"data": response.model_dump(), "message": "Suno template created from sketch successfully"}, 201

        except SunoTemplateOrchestratorError as e:
            if "not found" in str(e).lower():
                return {"error": f"Sketch not found with ID: {sketch_id}"}, 404
            logger.error("suno_template_from_sketch_error", sketch_id=sketch_id, error=str(e))
            return {"error": f"Failed to create suno template from sketch: {str(e)}"}, 500
        except Exception as e:
            logger.error(
                "suno_template_from_sketch_error", sketch_id=sketch_id, error=str(e), error_type=type(e).__name__
            )
            return {"error": f"Failed to create suno template from sketch: {str(e)}"}, 500

    @staticmethod
    def assign_to_project(
        db: Session,
        domain_id: str,
        template_id: str,
        project_id: str,
        folder_id: str | None = None,
    ) -> tuple[dict[str, Any], int]:
        """Assign suno template to a project"""
        try:
            try:
                UUID(template_id)
                UUID(project_id)
                if folder_id:
                    UUID(folder_id)
            except ValueError as e:
                return {"error": f"Invalid UUID format: {str(e)}"}, 400

            orchestrator = SunoTemplateOrchestrator()
            result = orchestrator.assign_to_project(
                db=db,
                domain_id=domain_id,
                template_id=template_id,
                project_id=project_id,
                folder_id=folder_id,
            )

            if not result:
                return {"error": "Suno template not found"}, 404

            return {"success": True, "data": result}, 200

        except ValueError as e:
            logger.warning("Suno template assignment validation failed", template_id=template_id, error=str(e))
            return {"error": str(e)}, 404
        except Exception as e:
            logger.error(
                "Failed to assign suno template to project",
                template_id=template_id,
                project_id=project_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            return {"error": f"Failed to assign suno template to project: {str(e)}"}, 500

    @staticmethod
    def unassign_from_project(db: Session, domain_id: str, template_id: str) -> tuple[dict[str, Any], int]:
        """Remove suno template from its assigned project"""
        try:
            try:
                UUID(template_id)
            except ValueError:
                return {"error": "Invalid template ID format"}, 400

            orchestrator = SunoTemplateOrchestrator()
            result = orchestrator.unassign_from_project(db=db, domain_id=domain_id, template_id=template_id)

            if not result:
                return {"error": "Suno template not found"}, 404

            return {"success": True, "data": result}, 200

        except ValueError as e:
            logger.warning("Suno template unassign validation failed", template_id=template_id, error=str(e))
            return {"error": str(e)}, 404
        except Exception as e:
            logger.error(
                "Failed to unassign suno template from project",
                template_id=template_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            return {"error": f"Failed to unassign suno template from project: {str(e)}"}, 500
