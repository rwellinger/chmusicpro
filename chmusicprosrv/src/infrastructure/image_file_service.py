"""Image File Service - Handles PIL/Pillow operations and file I/O"""

import time
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from utils.logger import logger


class ImageFileService:
    """Infrastructure service for image file operations (PIL + File System)"""

    FONTS_DIR = Path(__file__).parent.parent.parent / "fonts"

    @staticmethod
    def load_image(image_path: str) -> Image.Image:
        """
        Load image from file system

        Args:
            image_path: Path to image file

        Returns:
            PIL Image object in RGBA mode

        Raises:
            FileNotFoundError: If image doesn't exist
            IOError: If image can't be opened
        """
        try:
            img = Image.open(image_path).convert("RGBA")
            logger.debug("Image loaded", image_path=image_path, size=img.size)
            return img
        except FileNotFoundError as e:
            logger.error("Image not found", image_path=image_path, error=str(e))
            raise
        except Exception as e:
            logger.error("Failed to load image", image_path=image_path, error=str(e), error_type=type(e).__name__)
            raise

    @staticmethod
    def save_image(img: Image.Image, output_path: str) -> None:
        """
        Save image to file system

        Args:
            img: PIL Image object
            output_path: Path where to save the image

        Raises:
            IOError: If image can't be saved
        """
        try:
            # Convert RGBA to RGB for saving (JPEG doesn't support alpha)
            img_rgb = img.convert("RGB")
            img_rgb.save(output_path)
            logger.info("Image saved", output_path=output_path)
        except Exception as e:
            logger.error("Failed to save image", output_path=output_path, error=str(e), error_type=type(e).__name__)
            raise

    @staticmethod
    def load_font(font_path: Path | None, font_size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        """
        Load TrueType font or fallback to default

        Args:
            font_path: Path to .ttf file (or None for default font)
            font_size: Font size in pixels

        Returns:
            PIL ImageFont object
        """
        if font_path and font_path.exists():
            try:
                font = ImageFont.truetype(str(font_path), font_size)
                logger.debug("Font loaded", font_path=str(font_path), font_size=font_size)
                return font
            except Exception as e:
                logger.warning("Failed to load font, using default", font_path=str(font_path), error=str(e))
                return ImageFont.load_default()
        else:
            logger.debug("Using default font", font_size=font_size)
            return ImageFont.load_default()

    @staticmethod
    def get_text_dimensions(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> dict[str, Any]:
        """
        Get text bounding box dimensions

        Args:
            draw: PIL ImageDraw object
            text: Text to measure
            font: PIL ImageFont object

        Returns:
            {
                "width": text_width,
                "height": text_height,
                "bbox_left_offset": left_offset_from_bbox
            }
        """
        bbox = draw.textbbox((0, 0), text, font=font)
        return {
            "width": bbox[2] - bbox[0],
            "height": bbox[3] - bbox[1],
            "bbox_left_offset": bbox[0],  # Left padding in bounding box
        }

    @staticmethod
    def draw_text_with_outline(
        draw: ImageDraw.ImageDraw,
        position: tuple[int, int],
        text: str,
        font: ImageFont.FreeTypeFont,
        text_color: tuple[int, int, int],
        outline_color: tuple[int, int, int],
        outline_width: int,
        anchor: str | None = None,
    ) -> None:
        """
        Draw text with outline on image

        Args:
            draw: PIL ImageDraw object
            position: (x, y) coordinates
            text: Text to draw
            font: PIL ImageFont object
            text_color: RGB tuple for text
            outline_color: RGB tuple for outline
            outline_width: Pixel width of outline
            anchor: PIL text anchor (e.g., 'lt' for left-top)
        """
        x, y = position

        # Draw outline (by drawing text multiple times with offset)
        for adj_x in range(-outline_width, outline_width + 1):
            for adj_y in range(-outline_width, outline_width + 1):
                if adj_x != 0 or adj_y != 0:  # Skip center
                    draw.text((x + adj_x, y + adj_y), text, font=font, fill=outline_color, anchor=anchor)

        # Draw main text on top
        draw.text((x, y), text, font=font, fill=text_color, anchor=anchor)
        logger.debug("Text drawn", text=text[:20], position=position, anchor=anchor)

    @staticmethod
    def generate_unique_filename(base_path: str, suffix: str = "_with_text") -> str:
        """
        Generate unique filename with timestamp

        Args:
            base_path: Original image path
            suffix: Suffix to add before extension

        Returns:
            New unique file path with timestamp
        """
        path_obj = Path(base_path)
        base_name = path_obj.stem
        extension = path_obj.suffix
        parent_dir = path_obj.parent

        timestamp = int(time.time())
        output_filename = f"{base_name}{suffix}_{timestamp}{extension}"
        output_path = str(parent_dir / output_filename)

        logger.debug("Unique filename generated", original=base_path, generated=output_path)
        return output_path
