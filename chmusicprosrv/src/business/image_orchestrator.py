"""Image Orchestrator - Coordinates image operations (no testable business logic)"""

from typing import TYPE_CHECKING, Any, Optional

from business.bulk_delete_transformer import BulkDeleteTransformer, DeleteResult
from business.image_transformer import ImageTransformer
from business.image_validator import ImageValidator
from config.settings import DELETE_PHYSICAL_FILES, OPENAI_MODEL, S3_IMAGES_BUCKET
from db.image_service import ImageService
from infrastructure.storage import get_storage
from utils.logger import logger


if TYPE_CHECKING:
    from db.models import GeneratedImage


class ImageGenerationError(Exception):
    """Base exception for image generation errors"""

    pass


class ImageOrchestrator:
    """Orchestrates image operations (calls services + repository)"""

    def __init__(self):
        self._s3_storage = None  # Lazy init to allow server startup when MinIO is down

    @property
    def s3_storage(self):
        """Lazy-load S3 storage (only when first accessed)"""
        if self._s3_storage is None:
            self._s3_storage = get_storage(bucket=S3_IMAGES_BUCKET)
        return self._s3_storage

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
    ) -> dict[str, Any]:
        """
        Generate image with validation and business logic

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
            Dict containing image URL and metadata

        Raises:
            ImageGenerationError: If generation fails
        """
        # Business logic: Validate request (delegated to validator)
        from business.image_validator import ImageValidationError

        try:
            ImageValidator.validate_prompt(prompt)
            ImageValidator.validate_size(size)
        except ImageValidationError as e:
            raise ImageGenerationError(str(e)) from e

        prompt_preview = prompt[:50] + ("..." if len(prompt) > 50 else "")
        logger.info("Starting image generation", prompt_preview=prompt_preview, size=size)

        # Construct enhanced prompt with style preferences
        from .image_enhancement_service import ImageEnhancementService

        enhanced_prompt = ImageEnhancementService.construct_enhanced_prompt(
            base_prompt=prompt,
            artistic_style=artistic_style,
            composition=composition,
            lighting=lighting,
            color_palette=color_palette,
            detail_level=detail_level,
        )

        # Use enhanced_prompt for generation, or original if no styles applied
        final_prompt = enhanced_prompt if enhanced_prompt != prompt else prompt

        try:
            # Generate image via external API (delegated to external service)
            from .external_api_service import OpenAIService

            openai_service = OpenAIService()
            image_url = openai_service.generate_image(final_prompt, size)

            # Download and save image to S3
            filename, s3_key = self._process_and_save_image(image_url, prompt)

            # Save metadata to database and get the generated image record
            generated_image = self._save_image_metadata(
                user_prompt=user_prompt,
                prompt=prompt,  # Ollama-enhanced prompt
                enhanced_prompt=enhanced_prompt if enhanced_prompt != prompt else None,
                size=size,
                filename=filename,
                file_path=s3_key,
                local_url="",
                title=title,
                artistic_style=artistic_style,
                composition=composition,
                lighting=lighting,
                color_palette=color_palette,
                detail_level=detail_level,
                s3_key=s3_key,
            )

            # Generate relative backend proxy path (frontend adds base URL via ApiConfigService)
            backend_path = f"/api/v1/image/s3/{generated_image.id}" if generated_image else ""

            logger.info(f"Image generated successfully: {filename}")
            response = {"url": backend_path, "saved_path": s3_key}

            # Include image metadata if database save was successful
            if generated_image:
                response["id"] = str(generated_image.id)
                response["user_prompt"] = generated_image.user_prompt
                response["prompt"] = generated_image.prompt
                response["enhanced_prompt"] = generated_image.enhanced_prompt
                response["artistic_style"] = generated_image.artistic_style
                response["composition"] = generated_image.composition
                response["lighting"] = generated_image.lighting
                response["color_palette"] = generated_image.color_palette
                response["detail_level"] = generated_image.detail_level
                logger.info("Image saved to database", image_id=generated_image.id, filename=filename)
            else:
                logger.warning("Image generated but failed to save metadata to database", filename=filename)

            return response

        except Exception as e:
            logger.error("Image generation failed", error_type=type(e).__name__, error=str(e))
            raise ImageGenerationError(f"Generation failed: {e}") from e

    def get_images_with_pagination(
        self,
        limit: int = 20,
        offset: int = 0,
        search: str = "",
        sort_by: str = "created_at",
        sort_direction: str = "desc",
    ) -> dict[str, Any]:
        """
        Get paginated list of images with search and sorting

        Args:
            limit: Number of images to return
            offset: Number of images to skip
            search: Search term for filtering
            sort_by: Field to sort by
            sort_direction: Sort direction ('asc' or 'desc')

        Returns:
            Dict containing images and pagination info
        """
        try:
            images = ImageService.get_images_paginated(
                limit=limit, offset=offset, search=search, sort_by=sort_by, sort_direction=sort_direction
            )
            total_count = ImageService.get_total_images_count(search=search)

            # Transform to API response format
            image_list = [self._transform_image_to_api_format(image) for image in images]

            return {
                "images": image_list,
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + limit < total_count,
                },
            }

        except Exception as e:
            logger.error("Error retrieving images", error=str(e))
            raise ImageGenerationError(f"Failed to retrieve images: {e}") from e

    def get_images_for_text_overlay(self) -> dict[str, Any]:
        """
        Get list of images suitable for text overlay
        - Only images with title (not NULL and not empty)
        - Sorted: composition='album-cover' first, then by created_at DESC
        - No pagination (return all matching images)

        Returns:
            Dict containing filtered and sorted images
        """
        try:
            images = ImageService.get_images_for_text_overlay()

            # Transform to API response format
            image_list = [self._transform_image_to_api_format(image) for image in images]

            return {"images": image_list}

        except Exception as e:
            logger.error("Error retrieving images for text overlay", error=str(e))
            raise ImageGenerationError(f"Failed to retrieve images for text overlay: {e}") from e

    def get_image_details(self, image_id: str) -> dict[str, Any] | None:
        """
        Get detailed information for a single image

        Args:
            image_id: ID of the image

        Returns:
            Dict containing image details or None if not found
        """
        try:
            image = ImageService.get_image_by_id(image_id)
            if not image:
                return None

            return self._transform_image_to_api_format(image, include_file_path=True)

        except Exception as e:
            logger.error("Error retrieving image", image_id=image_id, error=str(e))
            raise ImageGenerationError(f"Failed to retrieve image: {e}") from e

    def delete_single_image(self, image_id: str) -> bool:
        """
        Delete a single image including files and metadata

        Args:
            image_id: ID of the image to delete

        Returns:
            True if successful, False if image not found

        Raises:
            ImageGenerationError: If deletion fails
        """
        try:
            image = ImageService.get_image_by_id(image_id)
            if not image:
                return False

            # Archive S3 image if physical deletion is enabled
            if DELETE_PHYSICAL_FILES and image.s3_key:
                # Archive S3 image: shared/{id}.png → archive/{id}.png
                archive_key = image.s3_key.replace("shared/", "archive/", 1)
                move_success = self.s3_storage.move(image.s3_key, archive_key)
                if move_success:
                    logger.info("S3 image archived", image_id=image_id, source=image.s3_key, archive=archive_key)
                else:
                    logger.warning("Failed to archive S3 image", image_id=image_id, s3_key=image.s3_key)
            else:
                logger.info("Skipping physical file deletion (disabled)", image_id=image_id)

            # Delete metadata from database
            success = ImageService.delete_image_metadata(image_id)
            if success:
                logger.info("Image deleted successfully", image_id=image_id)
                return True
            else:
                raise ImageGenerationError("Failed to delete image metadata")

        except Exception as e:
            logger.error("Error deleting image", image_id=image_id, error_type=type(e).__name__, error=str(e))
            raise ImageGenerationError(f"Failed to delete image: {e}") from e

    def bulk_delete_images(self, image_ids: list[str]) -> dict[str, Any]:
        """
        Delete multiple images with detailed results

        Args:
            image_ids: List of image IDs to delete

        Returns:
            Dict containing deletion results and summary
        """
        # Business logic: Validate bulk delete request (delegated to validator)
        from business.image_validator import ImageValidationError

        try:
            ImageValidator.validate_bulk_delete_count(image_ids)
        except ImageValidationError as e:
            raise ImageGenerationError(str(e)) from e

        # Orchestration: Process each delete operation
        delete_results = []
        for image_id in image_ids:
            try:
                # Check if image exists
                image = ImageService.get_image_by_id(image_id)
                if not image:
                    delete_results.append(DeleteResult(image_id, "not_found"))
                    continue

                # Archive physical file if enabled
                if DELETE_PHYSICAL_FILES and image.s3_key:
                    # Archive S3 image: shared/{id}.png → archive/{id}.png
                    archive_key = image.s3_key.replace("shared/", "archive/", 1)
                    move_success = self.s3_storage.move(image.s3_key, archive_key)
                    if not move_success:
                        logger.warning(
                            "Failed to archive S3 image during bulk delete", image_id=image_id, s3_key=image.s3_key
                        )

                # Delete metadata from database
                success = ImageService.delete_image_metadata(image_id)
                if success:
                    delete_results.append(DeleteResult(image_id, "deleted"))
                    logger.info("Bulk delete: Image deleted", image_id=image_id)
                else:
                    delete_results.append(DeleteResult(image_id, "error", "Failed to delete metadata"))

            except Exception as e:
                error_msg = f"{type(e).__name__}: {e}"
                delete_results.append(DeleteResult(image_id, "error", error_msg))
                logger.error("Bulk delete: Error deleting image", image_id=image_id, error=error_msg)

        # Business logic: Aggregate results (delegated to transformer)
        aggregated_results = BulkDeleteTransformer.aggregate_results(delete_results)
        response = BulkDeleteTransformer.format_bulk_delete_response(aggregated_results, len(image_ids))

        logger.info("Bulk delete completed", summary=response["summary"])
        return response

    def update_image_metadata(self, image_id: str, title: str = None, tags: str = None) -> dict[str, Any] | None:
        """
        Update image metadata

        Args:
            image_id: ID of the image to update
            title: Optional new title
            tags: Optional tags (comma-separated string)

        Returns:
            Updated image data or None if not found
        """
        try:
            # Check if image exists
            image = ImageService.get_image_by_id(image_id)
            if not image:
                return None

            # Update metadata
            success = ImageService.update_image_metadata(image_id, title, tags)
            if not success:
                raise ImageGenerationError("Failed to update image metadata")

            logger.info("Image metadata updated successfully", image_id=image_id)

            # Return updated image data
            updated_image = ImageService.get_image_by_id(image_id)
            return self._transform_image_to_api_format(updated_image, include_file_path=True) if updated_image else None

        except Exception as e:
            logger.error("Error updating image", image_id=image_id, error_type=type(e).__name__, error=str(e))
            raise ImageGenerationError(f"Failed to update image: {e}") from e

    def add_text_overlay_to_image(
        self,
        source_image_id: str,
        title: str,
        artist: str | None = None,
        font_style: str = "bold",
        title_position: str | dict[str, float] = "center",
        title_font_size: float | int = 80,
        title_color: str = "#FFFFFF",
        title_outline_color: str = "#000000",
        artist_position: str | dict[str, float] | None = None,
        artist_font_size: float | int = 40,
        artist_color: str | None = None,
        artist_outline_color: str | None = None,
        artist_font_style: str | None = None,
        outline_width: int = 3,
    ) -> dict[str, Any]:
        """
        Add text overlay to existing image (3-layer architecture)

        Args:
            source_image_id: ID of the source image
            title: Title text (will be uppercase)
            artist: Optional artist name (will be uppercase with "BY" prefix)
            font_style: Font style for title (bold/elegant/light)
            title_position: Grid position or custom dict
            title_font_size: Font size (pixels or percentage)
            title_color: Hex color for title
            title_outline_color: Hex outline color for title
            artist_position: Grid/custom position or None (below title)
            artist_font_size: Font size (pixels or percentage)
            artist_color: Hex color for artist (if None, uses title_color)
            artist_outline_color: Hex outline for artist (if None, uses title_outline_color)
            artist_font_style: Font style for artist (if None, uses same as title)
            outline_width: Pixel width of outline

        Returns:
            {
                "image_id": "new_image_id",
                "image_url": "/api/v1/image/filename.png",
                "metadata": {...}
            }

        Raises:
            ImageGenerationError: If image not found or overlay fails
        """
        from PIL import ImageDraw

        from business.image_text_overlay_transformer import ImageTextOverlayTransformer
        from infrastructure.image_file_service import ImageFileService

        try:
            # Get source image from DB
            source_image = ImageService.get_image_by_id(source_image_id)
            if not source_image:
                raise ImageGenerationError(f"Source image not found: {source_image_id}")

            logger.info("Adding text overlay", source_image_id=source_image_id, title=title)

            # === INFRASTRUCTURE LAYER: Load image from S3 ===
            import io
            import uuid

            from PIL import Image

            logger.debug("Loading source image from S3", s3_key=source_image.s3_key)
            image_data = self.s3_storage.download(source_image.s3_key)
            img = Image.open(io.BytesIO(image_data)).convert("RGBA")

            draw = ImageDraw.Draw(img)

            # === BUSINESS LAYER: Calculate title parameters ===
            title_font_size_px = ImageTextOverlayTransformer.calculate_font_size(title_font_size, img.height)
            title_text_rgb = ImageTextOverlayTransformer.hex_to_rgb(title_color)
            title_outline_rgb = ImageTextOverlayTransformer.hex_to_rgb(title_outline_color)

            # Get font path
            title_font_path = ImageTextOverlayTransformer.get_font_path(font_style, ImageFileService.FONTS_DIR)
            if not title_font_path.exists():
                logger.warning("Title font not found, using default", font_path=str(title_font_path))
                title_font_path = None

            # === INFRASTRUCTURE LAYER: Load title font ===
            title_font = ImageFileService.load_font(title_font_path, title_font_size_px)

            # === INFRASTRUCTURE LAYER: Get text dimensions ===
            title_text = title.upper()
            title_dims = ImageFileService.get_text_dimensions(draw, title_text, title_font)

            # === BUSINESS LAYER: Calculate title position ===
            is_custom = isinstance(title_position, dict)
            if is_custom:
                grid_x, grid_y = ImageTextOverlayTransformer.get_custom_coordinates(title_position)
                title_x, title_y = ImageTextOverlayTransformer.calculate_text_position_custom(
                    img.width, img.height, grid_x, grid_y, title_dims["bbox_left_offset"]
                )
                title_anchor = "lt"  # Left-top anchor for custom
            else:
                grid_x, grid_y = ImageTextOverlayTransformer.get_grid_coordinates(title_position)
                title_x, title_y = ImageTextOverlayTransformer.calculate_text_position_grid(
                    img.width, img.height, grid_x, grid_y, title_dims["width"], title_dims["height"]
                )
                title_anchor = None  # Default anchor for grid

            # === INFRASTRUCTURE LAYER: Draw title ===
            ImageFileService.draw_text_with_outline(
                draw,
                (title_x, title_y),
                title_text,
                title_font,
                title_text_rgb,
                title_outline_rgb,
                outline_width,
                title_anchor,
            )

            # === ARTIST TEXT (if provided) ===
            if artist:
                artist_text = f"BY {artist.upper()}"

                # Business logic: Artist parameters
                actual_artist_color = artist_color if artist_color else title_color
                actual_artist_outline = artist_outline_color if artist_outline_color else title_outline_color
                actual_artist_pos = artist_position if artist_position else title_position
                actual_artist_font_style = artist_font_style if artist_font_style else font_style

                artist_font_size_px = ImageTextOverlayTransformer.calculate_font_size(artist_font_size, img.height)
                artist_text_rgb = ImageTextOverlayTransformer.hex_to_rgb(actual_artist_color)
                artist_outline_rgb = ImageTextOverlayTransformer.hex_to_rgb(actual_artist_outline)

                # Get artist font
                artist_font_path = ImageTextOverlayTransformer.get_font_path(
                    actual_artist_font_style, ImageFileService.FONTS_DIR
                )
                if not artist_font_path.exists():
                    logger.warning("Artist font not found, using default", font_path=str(artist_font_path))
                    artist_font_path = None

                # Infrastructure: Load artist font
                artist_font = ImageFileService.load_font(artist_font_path, artist_font_size_px)

                # Infrastructure: Get artist dimensions
                artist_dims = ImageFileService.get_text_dimensions(draw, artist_text, artist_font)

                # Business: Calculate artist position
                is_custom_artist = isinstance(actual_artist_pos, dict)
                if is_custom_artist:
                    grid_x_a, grid_y_a = ImageTextOverlayTransformer.get_custom_coordinates(actual_artist_pos)
                    artist_x, artist_y = ImageTextOverlayTransformer.calculate_text_position_custom(
                        img.width, img.height, grid_x_a, grid_y_a, artist_dims["bbox_left_offset"]
                    )
                    artist_anchor = "lt"
                else:
                    grid_x_a, grid_y_a = ImageTextOverlayTransformer.get_grid_coordinates(actual_artist_pos)
                    artist_x, artist_y = ImageTextOverlayTransformer.calculate_text_position_grid(
                        img.width, img.height, grid_x_a, grid_y_a, artist_dims["width"], artist_dims["height"]
                    )
                    artist_anchor = None

                # Business: Calculate offset (if artist follows title)
                artist_offset = ImageTextOverlayTransformer.calculate_artist_offset(
                    title_font_size, img.height, artist_position
                )
                artist_y += artist_offset

                # Infrastructure: Draw artist
                ImageFileService.draw_text_with_outline(
                    draw,
                    (artist_x, artist_y),
                    artist_text,
                    artist_font,
                    artist_text_rgb,
                    artist_outline_rgb,
                    outline_width,
                    artist_anchor,
                )

            # === INFRASTRUCTURE LAYER: Save image to S3 ===
            # Convert PIL Image to bytes
            img_rgb = img.convert("RGB")
            output_buffer = io.BytesIO()
            img_rgb.save(output_buffer, format="PNG")
            image_data = output_buffer.getvalue()

            # Generate unique S3 key
            new_image_id = str(uuid.uuid4())
            s3_key = f"shared/{new_image_id}.png"
            output_filename = f"{new_image_id}_with_text.png"

            # Upload to S3
            self.s3_storage.upload(image_data, s3_key)
            logger.info("Text overlay image saved to S3", s3_key=s3_key)

            # === REPOSITORY LAYER: Create new DB record ===
            new_image = ImageService.save_generated_image(
                prompt=source_image.prompt,
                size=source_image.size,
                filename=output_filename,
                file_path=s3_key,
                local_url="",
                model_used=source_image.model_used,
                prompt_hash=source_image.prompt_hash,
                title=title,
                user_prompt=source_image.user_prompt,
                enhanced_prompt=source_image.enhanced_prompt,
                artistic_style=source_image.artistic_style,
                composition=source_image.composition,
                lighting=source_image.lighting,
                color_palette=source_image.color_palette,
                detail_level=source_image.detail_level,
                s3_key=s3_key,
            )

            if not new_image:
                raise ImageGenerationError("Failed to create new image record")

            # Update text overlay metadata
            from db.database import SessionLocal

            db = SessionLocal()
            try:
                new_image.text_overlay_metadata = {
                    "title": title,
                    "artist": artist,
                    "font_style": font_style,
                    "title_position": title_position,
                    "title_font_size": title_font_size,
                    "title_color": title_color,
                    "artist_position": artist_position,
                    "artist_font_size": artist_font_size,
                    "artist_color": artist_color,
                    "artist_font_style": artist_font_style,
                }
                db.add(new_image)
                db.commit()
                db.refresh(new_image)
            finally:
                db.close()

            # Generate relative backend proxy path (frontend adds base URL via ApiConfigService)
            backend_path = f"/api/v1/image/s3/{new_image.id}"

            logger.info("Text overlay added successfully", new_image_id=str(new_image.id), s3_key=s3_key)

            return {
                "image_id": str(new_image.id),
                "image_url": backend_path,
                "metadata": new_image.text_overlay_metadata,
            }

        except ImageGenerationError:
            raise
        except Exception as e:
            logger.error(
                "Text overlay failed", source_image_id=source_image_id, error=str(e), error_type=type(e).__name__
            )
            raise ImageGenerationError(f"Failed to add text overlay: {e}") from e

    def _process_and_save_image(self, image_url: str, prompt: str) -> tuple[str, str]:
        """Download and save image to S3

        Returns:
            tuple: (filename, s3_key)
        """
        import uuid

        import requests

        # Generate unique ID and filename
        image_id = str(uuid.uuid4())
        filename = ImageTransformer.generate_filename(prompt)

        # Download image from OpenAI
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        image_data = response.content

        # Generate S3 key: shared/{image_id}.png
        # Note: Using "shared" prefix (no multi-tenant for images yet)
        s3_key = f"shared/{image_id}.png"

        # Upload to S3
        self.s3_storage.upload(image_data, s3_key)

        logger.info("Image stored in S3", s3_key=s3_key, filename=filename, bucket=S3_IMAGES_BUCKET)
        return filename, s3_key

    def _save_image_metadata(
        self,
        prompt: str,
        size: str,
        filename: str,
        file_path: str,
        local_url: str,
        title: str | None = None,
        user_prompt: str | None = None,
        enhanced_prompt: str | None = None,
        artistic_style: str | None = None,
        composition: str | None = None,
        lighting: str | None = None,
        color_palette: str | None = None,
        detail_level: str | None = None,
        s3_key: str | None = None,
    ) -> Optional["GeneratedImage"]:
        """Save image metadata to database"""
        # Business logic: Generate prompt hash (delegated to transformer)
        prompt_hash = ImageTransformer.generate_prompt_hash(prompt)

        return ImageService.save_generated_image(
            user_prompt=user_prompt,
            prompt=prompt,
            enhanced_prompt=enhanced_prompt,
            size=size,
            filename=filename,
            file_path=file_path,
            local_url=local_url,
            model_used=OPENAI_MODEL,
            prompt_hash=prompt_hash,
            title=title,
            artistic_style=artistic_style,
            composition=composition,
            lighting=lighting,
            color_palette=color_palette,
            detail_level=detail_level,
            s3_key=s3_key,
        )

    def _transform_image_to_api_format(self, image, include_file_path: bool = False) -> dict[str, Any]:
        """Transform database image object to API response format with backend proxy URLs"""
        # Business logic: Transform to API format (delegated to transformer)
        result = ImageTransformer.transform_image_to_api_format(image, include_file_path)

        # Generate backend proxy URL (streams via /api/v1/image/s3/<id>)
        backend_path = f"/api/v1/image/s3/{image.id}"
        result["url"] = backend_path
        result["display_url"] = backend_path
        logger.debug("Generated backend proxy path for image", image_id=str(image.id), s3_key=image.s3_key)

        return result

    def assign_image_to_project(
        self,
        image_id: str,
        project_id: str,
        folder_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Assign an image to a project (N:M relationship)

        Args:
            image_id: Image UUID
            project_id: Project UUID
            folder_id: Optional folder UUID

        Returns:
            dict: Assignment result with reference_id

        Raises:
            ValueError: If image or project not found
        """
        from uuid import UUID

        from db.database import get_db
        from db.image_service import get_image_by_id
        from db.project_asset_service import create_image_reference
        from db.song_project_service import get_project_by_id

        db = next(get_db())

        try:
            # Validate image exists
            image = get_image_by_id(db, UUID(image_id))
            if not image:
                raise ValueError(f"Image not found: {image_id}")

            # Validate project exists
            project = get_project_by_id(db, UUID(project_id))
            if not project:
                raise ValueError(f"Project not found: {project_id}")

            # Validate folder if provided
            if folder_id:
                from db.song_project_service import get_folder_by_id

                folder = get_folder_by_id(db, UUID(folder_id))
                if not folder:
                    raise ValueError(f"Folder not found: {folder_id}")
                if folder.project_id != UUID(project_id):
                    raise ValueError(f"Folder {folder_id} does not belong to project {project_id}")

            # Create reference (or update existing)
            reference = create_image_reference(
                db=db,
                project_id=UUID(project_id),
                image_id=UUID(image_id),
                folder_id=UUID(folder_id) if folder_id else None,
            )

            logger.info(
                "Image assigned to project",
                reference_id=str(reference.id),
                image_id=image_id,
                project_id=project_id,
                folder_id=folder_id,
            )

            return {
                "reference_id": str(reference.id),
                "project_id": str(reference.project_id),
                "image_id": str(reference.image_id),
                "folder_id": str(reference.folder_id) if reference.folder_id else None,
            }

        finally:
            db.close()

    def unassign_image_from_project(self, image_id: str, project_id: str) -> dict[str, Any]:
        """
        Remove image from project (link only, image remains)

        Args:
            image_id: Image UUID
            project_id: Project UUID

        Returns:
            dict: Unassignment result

        Raises:
            ValueError: If image-project reference not found
        """
        from uuid import UUID

        from db.database import get_db
        from db.project_asset_service import delete_image_reference_by_ids

        db = next(get_db())

        try:
            # Delete the reference
            success = delete_image_reference_by_ids(db, UUID(project_id), UUID(image_id))

            if not success:
                raise ValueError(f"Image {image_id} is not assigned to project {project_id}")

            logger.info(
                "Image unassigned from project",
                image_id=image_id,
                project_id=project_id,
            )

            return {
                "image_id": image_id,
                "project_id": project_id,
            }

        finally:
            db.close()
