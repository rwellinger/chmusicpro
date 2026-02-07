"""Image Controller - Handles HTTP requests for image operations"""

from typing import Any

from business.image_orchestrator import ImageGenerationError, ImageOrchestrator
from db.image_service import ImageService
from utils.logger import logger


class ImageController:
    """Controller for image HTTP request handling"""

    def __init__(self):
        self.orchestrator = ImageOrchestrator()

    def generate_image(
        self,
        prompt: str,
        size: str,
        title: str | None = None,
        user_prompt: str | None = None,
        artistic_style: str | None = None,
        composition: str | None = None,
        lighting: str | None = None,
        color_palette: str | None = None,
        detail_level: str | None = None,
    ) -> tuple[dict[str, Any], int]:
        """
        Generate image via business service

        Args:
            prompt: AI-enhanced image generation prompt (from Ollama)
            size: Image size specification
            title: Optional image title
            user_prompt: Optional original user input (before AI enhancement)
            artistic_style: Optional artistic style (auto, photorealistic, digital-art, etc.)
            composition: Optional composition (auto, portrait, landscape, etc.)
            lighting: Optional lighting (auto, natural, studio, dramatic, etc.)
            color_palette: Optional color palette (auto, vibrant, muted, etc.)
            detail_level: Optional detail level (auto, minimal, moderate, highly-detailed)

        Returns:
            Tuple of (response_data, status_code)
        """
        # Basic validation
        if not prompt or not size:
            return {"error": "Missing prompt or size"}, 400

        try:
            result = self.orchestrator.generate_image(
                prompt=prompt,
                size=size,
                title=title,
                user_prompt=user_prompt,
                artistic_style=artistic_style,
                composition=composition,
                lighting=lighting,
                color_palette=color_palette,
                detail_level=detail_level,
            )
            return result, 200

        except ImageGenerationError as e:
            logger.error(f"Image generation failed: {e}")
            return {"error": str(e)}, 500
        except Exception as e:
            logger.error(f"Unexpected error in image generation: {type(e).__name__}: {e}")
            return {"error": "Internal server error"}, 500

    def get_images(
        self,
        limit: int = 20,
        offset: int = 0,
        search: str = "",
        sort_by: str = "created_at",
        sort_direction: str = "desc",
    ) -> tuple[dict[str, Any], int]:
        """
        Get list of generated images with pagination, search and sorting

        Args:
            limit: Number of images to return (default 20)
            offset: Number of images to skip (default 0)
            search: Search term for title and prompt (default '')
            sort_by: Field to sort by (default 'created_at')
            sort_direction: Sort direction 'asc' or 'desc' (default 'desc')

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            result = self.orchestrator.get_images_with_pagination(
                limit=limit, offset=offset, search=search, sort_by=sort_by, sort_direction=sort_direction
            )
            return result, 200

        except ImageGenerationError as e:
            logger.error(f"Failed to retrieve images: {e}")
            return {"error": str(e)}, 500
        except Exception as e:
            logger.error(f"Unexpected error retrieving images: {type(e).__name__}: {e}")
            return {"error": "Internal server error"}, 500

    def get_image_by_id(self, image_id: str) -> tuple[dict[str, Any], int]:
        """
        Get single image by ID

        Args:
            image_id: ID of the image

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            result = self.orchestrator.get_image_details(image_id)

            if result is None:
                return {"error": "Image not found"}, 404

            return result, 200

        except ImageGenerationError as e:
            logger.error(f"Failed to retrieve image {image_id}: {e}")
            return {"error": str(e)}, 500
        except Exception as e:
            logger.error(f"Unexpected error retrieving image {image_id}: {type(e).__name__}: {e}")
            return {"error": "Internal server error"}, 500

    def delete_image(self, image_id: str) -> tuple[dict[str, Any], int]:
        """
        Delete image by ID

        Args:
            image_id: ID of the image to delete

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            success = self.orchestrator.delete_single_image(image_id)

            if not success:
                return {"error": "Image not found"}, 404

            return {"message": "Image deleted successfully"}, 200

        except ImageGenerationError as e:
            logger.error(f"Failed to delete image {image_id}: {e}")
            return {"error": str(e)}, 500
        except Exception as e:
            logger.error(f"Unexpected error deleting image {image_id}: {type(e).__name__}: {e}")
            return {"error": "Internal server error"}, 500

    def bulk_delete_images(self, image_ids: list[str]) -> tuple[dict[str, Any], int]:
        """
        Delete multiple images by IDs

        Args:
            image_ids: List of image IDs to delete

        Returns:
            Tuple of (response_data, status_code)
        """
        if not image_ids:
            return {"error": "No image IDs provided"}, 400

        if len(image_ids) > 100:
            return {"error": "Too many images (max 100 per request)"}, 400

        try:
            result = self.orchestrator.bulk_delete_images(image_ids)

            # Determine response status based on results
            summary = result["summary"]
            if summary["deleted"] > 0:
                status_code = 200
                if summary["not_found"] > 0 or summary["errors"] > 0:
                    status_code = 207  # Multi-Status
            else:
                status_code = 400 if summary["errors"] > 0 else 404

            return result, status_code

        except ImageGenerationError as e:
            logger.error(f"Bulk delete failed: {e}")
            return {"error": str(e)}, 500
        except Exception as e:
            logger.error(f"Unexpected error in bulk delete: {type(e).__name__}: {e}")
            return {"error": "Internal server error"}, 500

    def update_image_metadata(self, image_id: str, title: str = None, tags: str = None) -> tuple[dict[str, Any], int]:
        """
        Update image metadata (title and/or tags)

        Args:
            image_id: ID of the image to update
            title: Optional new title
            tags: Optional tags (comma-separated string)

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            result = self.orchestrator.update_image_metadata(image_id, title, tags)

            if result is None:
                return {"error": "Image not found"}, 404

            return result, 200

        except ImageGenerationError as e:
            logger.error(f"Failed to update image {image_id}: {e}")
            return {"error": str(e)}, 500
        except Exception as e:
            logger.error(f"Unexpected error updating image {image_id}: {type(e).__name__}: {e}")
            return {"error": "Internal server error"}, 500

    def get_images_for_text_overlay(self) -> tuple[dict[str, Any], int]:
        """
        Get list of images suitable for text overlay
        - Only images with title
        - Sorted: album-cover first, then by created_at DESC

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            result = self.orchestrator.get_images_for_text_overlay()
            return result, 200

        except ImageGenerationError as e:
            logger.error(f"Failed to retrieve images for text overlay: {e}")
            return {"error": str(e)}, 500
        except Exception as e:
            logger.error(f"Unexpected error retrieving images for text overlay: {type(e).__name__}: {e}")
            return {"error": "Internal server error"}, 500

    def add_text_overlay(
        self,
        image_id: str,
        user_id: str,
        title: str,
        artist: str | None = None,
        font_style: str = "bold",
        # Current parameters
        title_position: str | dict[str, float] = "center",
        title_font_size: float = 0.08,
        title_color: str = "#FFFFFF",
        title_outline_color: str = "#000000",
        artist_position: str | dict[str, float] | None = None,
        artist_font_size: float = 0.05,
        artist_color: str | None = None,
        artist_outline_color: str | None = None,
        artist_font_style: str | None = None,
        # Legacy (deprecated, ignored)
        position: str | None = None,
        text_color: str | None = None,
        outline_color: str | None = None,
    ) -> tuple[dict[str, Any], int]:
        """
        Add text overlay to existing image (3-layer architecture)

        Args:
            image_id: ID of the source image
            user_id: ID of the authenticated user (for auth)
            title: Title text to render
            artist: Optional artist name
            font_style: Font style (bold/elegant/light)
            title_position: Grid position or custom dict for title
            title_font_size: Font size (pixels or percentage)
            title_color: Hex color for title
            title_outline_color: Hex outline color for title
            artist_position: Grid/custom position or None (below title)
            artist_font_size: Font size (pixels or percentage)
            artist_color: Hex color for artist (if None, uses title_color)
            artist_outline_color: Hex outline for artist (if None, uses title_outline_color)
            artist_font_style: Font style for artist (if None, uses title font)
            position: DEPRECATED - ignored (use title_position)
            text_color: DEPRECATED - ignored (use title_color)
            outline_color: DEPRECATED - ignored (use title_outline_color)

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Delegate to orchestrator (3-layer architecture)
            result = self.orchestrator.add_text_overlay_to_image(
                source_image_id=image_id,
                title=title,
                artist=artist,
                font_style=font_style,
                title_position=title_position,
                title_font_size=title_font_size,
                title_color=title_color,
                title_outline_color=title_outline_color,
                artist_position=artist_position,
                artist_font_size=artist_font_size,
                artist_color=artist_color,
                artist_outline_color=artist_outline_color,
                artist_font_style=artist_font_style,
            )

            logger.info(
                "Text overlay created successfully",
                source_image_id=image_id,
                new_image_id=result["image_id"],
                image_url=result["image_url"],
            )

            response_data = {
                "success": True,
                "image_id": result["image_id"],
                "image_url": result["image_url"],
                "metadata": result["metadata"],
            }

            logger.debug("Text overlay response", response_data=response_data)
            return response_data, 200

        except ImageGenerationError as e:
            logger.error("Text overlay failed", image_id=image_id, error=str(e))
            return {"error": str(e)}, 500
        except Exception as e:
            logger.error(
                "Unexpected error adding text overlay", image_id=image_id, error_type=type(e).__name__, error=str(e)
            )
            return {"error": f"Internal server error: {str(e)}"}, 500

    def assign_to_project(
        self,
        image_id: str,
        project_id: str,
        folder_id: str | None = None,
    ) -> tuple[dict[str, Any], int]:
        """
        Assign image to a project (N:M relationship via project_image_references)

        Args:
            image_id: Image UUID
            project_id: Project UUID
            folder_id: Optional folder UUID

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            result = self.orchestrator.assign_image_to_project(
                image_id=image_id,
                project_id=project_id,
                folder_id=folder_id,
            )

            logger.info(
                "Image assigned to project",
                image_id=image_id,
                project_id=project_id,
                folder_id=folder_id,
                reference_id=result.get("reference_id"),
            )

            return {"success": True, "data": result}, 200

        except ValueError as e:
            logger.warning("Image assignment validation failed", image_id=image_id, project_id=project_id, error=str(e))
            return {"error": str(e)}, 404
        except Exception as e:
            logger.error(
                "Failed to assign image to project",
                image_id=image_id,
                project_id=project_id,
                error_type=type(e).__name__,
                error=str(e),
            )
            return {"error": f"Internal server error: {str(e)}"}, 500

    def get_projects_for_image(self, image_id: str) -> tuple[dict[str, Any], int]:
        """
        Get list of projects this image is assigned to.

        Args:
            image_id: Image UUID

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            projects = ImageService.get_projects_for_image(image_id)
            return {"projects": projects}, 200

        except Exception as e:
            logger.error(
                "Failed to get projects for image", image_id=image_id, error_type=type(e).__name__, error=str(e)
            )
            return {"error": f"Internal server error: {str(e)}"}, 500

    def unassign_from_project(self, image_id: str, project_id: str) -> tuple[dict[str, Any], int]:
        """
        Remove image from project (link only, image remains)

        Args:
            image_id: Image UUID
            project_id: Project UUID

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            result = self.orchestrator.unassign_image_from_project(image_id, project_id)

            logger.info("Image unassigned from project", image_id=image_id, project_id=project_id)

            return {"success": True, "data": result}, 200

        except ValueError as e:
            logger.warning("Image unassign validation failed", image_id=image_id, project_id=project_id, error=str(e))
            return {"error": str(e)}, 404
        except Exception as e:
            logger.error(
                "Failed to unassign image from project",
                image_id=image_id,
                project_id=project_id,
                error_type=type(e).__name__,
                error=str(e),
            )
            return {"error": f"Internal server error: {str(e)}"}, 500
