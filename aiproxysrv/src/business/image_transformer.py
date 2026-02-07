"""Image Transformer - Pure functions for image data transformations (testable business logic)"""

import hashlib
import time
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from db.models import GeneratedImage


class ImageTransformer:
    """Transform image data to various formats (pure functions, 100% testable)"""

    @staticmethod
    def generate_prompt_hash(prompt: str) -> str:
        """
        Generate MD5 hash from prompt (first 10 characters)

        Pure function - no DB, no file system, fully unit-testable

        Args:
            prompt: Image prompt string

        Returns:
            First 10 characters of MD5 hash

        Example:
            hash_value = ImageTransformer.generate_prompt_hash("A sunset")
            # Returns: "3f2a5b1c9d"
        """
        return hashlib.md5(prompt.encode()).hexdigest()[:10]

    @staticmethod
    def generate_filename(prompt: str, timestamp: int | None = None) -> str:
        """
        Generate filename from prompt hash and timestamp

        Pure function (timestamp can be injected for testing)

        Args:
            prompt: Image prompt string
            timestamp: Optional timestamp (uses current time if None)

        Returns:
            Filename in format: {hash}_{timestamp}.png

        Example:
            filename = ImageTransformer.generate_filename("A sunset", 1234567890)
            # Returns: "3f2a5b1c9d_1234567890.png"
        """
        prompt_hash = ImageTransformer.generate_prompt_hash(prompt)
        ts = timestamp if timestamp is not None else int(time.time())
        return f"{prompt_hash}_{ts}.png"

    @staticmethod
    def get_display_url(local_url: str, has_text_overlay: bool) -> str:
        """
        Get display URL (overlay version if text overlay exists)

        Pure function - no DB, no file system, fully unit-testable

        Args:
            local_url: Original local URL
            has_text_overlay: Whether text overlay metadata exists

        Returns:
            Display URL (overlay version if applicable)

        Example:
            url = ImageTransformer.get_display_url("/images/photo.png", True)
            # Returns: "/images/photo_with_text.png"

            url = ImageTransformer.get_display_url("/images/photo.png", False)
            # Returns: "/images/photo.png"
        """
        if has_text_overlay and "_with_text" not in local_url:
            # Replace .png with _with_text.png for overlay version
            return local_url.replace(".png", "_with_text.png")
        return local_url

    @staticmethod
    def transform_image_to_api_format(image: "GeneratedImage", include_file_path: bool = False) -> dict[str, Any]:
        """
        Transform database image object to API response format

        Pure function - only transforms data, no DB/file operations

        Args:
            image: Database GeneratedImage model object
            include_file_path: Whether to include file_path in response

        Returns:
            Dict with API response format

        Example:
            image_data = ImageTransformer.transform_image_to_api_format(image_obj)
            # Returns: {"id": "...", "url": "...", "display_url": "...", ...}
        """
        # Determine display URL using transformation logic
        has_text_overlay = image.text_overlay_metadata is not None
        display_url = ImageTransformer.get_display_url(image.local_url, has_text_overlay)

        # Check if image has project references (N:M relationship)
        projects_count = 0
        if hasattr(image, "project_references") and image.project_references:
            projects_count = len(image.project_references)

        image_data = {
            "id": str(image.id),
            "user_prompt": image.user_prompt,
            "prompt": image.prompt,
            "enhanced_prompt": image.enhanced_prompt,
            "size": image.size,
            "filename": image.filename,
            "url": image.local_url,
            "display_url": display_url,
            "model_used": image.model_used,
            "title": image.title,
            "tags": image.tags,
            "text_overlay_metadata": image.text_overlay_metadata,
            "projects_count": projects_count,  # Number of projects this image is assigned to
            "created_at": image.created_at.isoformat() if image.created_at else None,
            "updated_at": image.updated_at.isoformat() if image.updated_at else None,
            "prompt_hash": image.prompt_hash,
            "artistic_style": image.artistic_style,
            "composition": image.composition,
            "lighting": image.lighting,
            "color_palette": image.color_palette,
            "detail_level": image.detail_level,
        }

        if include_file_path:
            image_data["file_path"] = image.file_path

        return image_data
