"""Image Text Overlay Transformer - Pure functions for text overlay calculations (100% testable)"""

from typing import Any


class ImageTextOverlayTransformer:
    """Pure functions for text overlay position and size calculations"""

    # Font file mappings
    FONT_FILES = {
        "bold": "Anton-Regular.ttf",  # Heavy display font
        "elegant": "PlayfairDisplay-Regular.ttf",  # Serif
        "light": "Roboto-Light.ttf",  # Thin sans-serif
        # Comic styles
        "bangers": "Bangers-Regular.ttf",  # Bold comic
        "comic": "ComicNeue-Regular.ttf",  # Modern comic
        "bubblegum": "BubblegumSans-Regular.ttf",  # Playful comic
        "righteous": "Righteous-Regular.ttf",  # Retro comic
        # Display fonts for music titles
        "bebas": "BebasNeue-Regular.ttf",  # Ultra condensed
        "bungee": "Bungee-Regular.ttf",  # Urban 3D
        "montserrat": "Montserrat-Regular.ttf",  # Geometric clean
        "oswald": "Oswald-Regular.ttf",  # Condensed gothic
    }

    # Grid position mappings (3x3 grid)
    GRID_POSITIONS = {
        "top-left": (0.10, 0.10),
        "top-center": (0.50, 0.10),
        "top-right": (0.90, 0.10),
        "middle-left": (0.10, 0.50),
        "center": (0.50, 0.50),
        "middle-right": (0.90, 0.50),
        "bottom-left": (0.10, 0.90),
        "bottom-center": (0.50, 0.90),
        "bottom-right": (0.90, 0.90),
    }

    @staticmethod
    def calculate_font_size(font_size_input: float | int, img_height: int) -> int:
        """
        Calculate font size in pixels

        Args:
            font_size_input: Either pixel value (>= 1.0) or percentage (< 1.0)
            img_height: Image height in pixels

        Returns:
            Font size in pixels
        """
        if isinstance(font_size_input, int) or (isinstance(font_size_input, float) and font_size_input >= 1.0):
            # Pixel value
            return int(font_size_input)
        else:
            # Percentage value (legacy support)
            return int(img_height * font_size_input)

    @staticmethod
    def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
        """
        Convert hex color to RGB tuple

        Args:
            hex_color: Hex color string (with or without #)

        Returns:
            RGB tuple (r, g, b)
        """
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

    @staticmethod
    def get_grid_coordinates(position: str) -> tuple[float, float]:
        """
        Get grid position as percentages

        Args:
            position: Grid position name (e.g., "center", "top-left")

        Returns:
            (x_pct, y_pct) where 0.0 <= value <= 1.0
        """
        return ImageTextOverlayTransformer.GRID_POSITIONS.get(position, (0.5, 0.5))

    @staticmethod
    def get_custom_coordinates(position: dict[str, float]) -> tuple[float, float]:
        """
        Extract and validate custom position coordinates

        Args:
            position: Dict with "x" and "y" keys (0.0-1.0)

        Returns:
            (x_pct, y_pct) clamped to 0.0-1.0 range
        """
        x_pct = max(0.0, min(1.0, position.get("x", 0.5)))
        y_pct = max(0.0, min(1.0, position.get("y", 0.5)))
        return (x_pct, y_pct)

    @staticmethod
    def calculate_text_position_custom(
        img_width: int,
        img_height: int,
        grid_x_pct: float,
        grid_y_pct: float,
        bbox_left_offset: int,
    ) -> tuple[int, int]:
        """
        Calculate text position for custom placement

        Args:
            img_width: Image width in pixels
            img_height: Image height in pixels
            grid_x_pct: X position as percentage (0.0-1.0)
            grid_y_pct: Y position as percentage (0.0-1.0)
            bbox_left_offset: Left padding from bounding box

        Returns:
            (x, y) pixel coordinates
        """
        # Custom position: compensate for left padding (matches frontend marker)
        x = int(img_width * grid_x_pct) - bbox_left_offset
        y = int(img_height * grid_y_pct)
        return (x, y)

    @staticmethod
    def calculate_text_position_grid(
        img_width: int,
        img_height: int,
        grid_x_pct: float,
        grid_y_pct: float,
        text_width: int,
        text_height: int,
    ) -> tuple[int, int]:
        """
        Calculate text position for grid placement with alignment

        Args:
            img_width: Image width in pixels
            img_height: Image height in pixels
            grid_x_pct: X position as percentage (0.0-1.0)
            grid_y_pct: Y position as percentage (0.0-1.0)
            text_width: Text width in pixels
            text_height: Text height in pixels

        Returns:
            (x, y) pixel coordinates
        """
        # X-axis alignment
        if grid_x_pct == 0.10:  # Left-aligned
            x = int(img_width * grid_x_pct)
        elif grid_x_pct == 0.90:  # Right-aligned
            x = int(img_width * grid_x_pct) - text_width
        else:  # Center-aligned
            x = int(img_width * grid_x_pct) - (text_width // 2)

        # Y-axis alignment
        if grid_y_pct == 0.10:  # Top-aligned
            y = int(img_height * grid_y_pct)
        elif grid_y_pct == 0.90:  # Bottom-aligned
            y = int(img_height * grid_y_pct) - text_height
        else:  # Center-aligned
            y = int(img_height * grid_y_pct) - (text_height // 2)

        return (x, y)

    @staticmethod
    def calculate_artist_offset(
        title_font_size_input: float | int, img_height: int, artist_position: Any | None
    ) -> int:
        """
        Calculate vertical offset for artist text below title

        Args:
            title_font_size_input: Title font size (pixel or percentage)
            img_height: Image height in pixels
            artist_position: Artist position (if None, place below title)

        Returns:
            Vertical offset in pixels (0 if artist has custom position)
        """
        if artist_position:
            # Artist has custom position, no offset needed
            return 0

        # Place artist below title with 1.2x spacing
        title_font_size = ImageTextOverlayTransformer.calculate_font_size(title_font_size_input, img_height)
        return int(title_font_size * 1.2)

    @staticmethod
    def get_font_path(font_style: str, fonts_dir) -> Any:
        """
        Get font file path for given style

        Args:
            font_style: Font style name (bold/elegant/light)
            fonts_dir: Path to fonts directory

        Returns:
            Path object to font file
        """
        font_file = ImageTextOverlayTransformer.FONT_FILES.get(font_style, "Anton-Regular.ttf")
        return fonts_dir / font_file
