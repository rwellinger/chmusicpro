"""Unit tests for ImageTextOverlayTransformer (pure functions, 100% testable)"""

from pathlib import Path

from business.image_text_overlay_transformer import ImageTextOverlayTransformer


class TestCalculateFontSize:
    """Test font size calculation (pixel vs percentage)"""

    def test_calculate_font_size_pixels(self):
        """Test font size as pixel value (>= 1.0)"""
        assert ImageTextOverlayTransformer.calculate_font_size(80, 1000) == 80
        assert ImageTextOverlayTransformer.calculate_font_size(120, 500) == 120
        assert ImageTextOverlayTransformer.calculate_font_size(50, 2000) == 50

    def test_calculate_font_size_pixels_float(self):
        """Test font size as float pixel value (>= 1.0)"""
        assert ImageTextOverlayTransformer.calculate_font_size(80.5, 1000) == 80
        assert ImageTextOverlayTransformer.calculate_font_size(120.9, 500) == 120

    def test_calculate_font_size_percentage(self):
        """Test font size as percentage (< 1.0)"""
        assert ImageTextOverlayTransformer.calculate_font_size(0.08, 1000) == 80
        assert ImageTextOverlayTransformer.calculate_font_size(0.05, 1000) == 50
        assert ImageTextOverlayTransformer.calculate_font_size(0.10, 500) == 50

    def test_calculate_font_size_edge_case_one(self):
        """Test edge case: exactly 1.0 should be treated as pixel"""
        assert ImageTextOverlayTransformer.calculate_font_size(1.0, 1000) == 1


class TestHexToRgb:
    """Test hex color conversion"""

    def test_hex_to_rgb_with_hash(self):
        """Test hex color conversion with hash prefix"""
        assert ImageTextOverlayTransformer.hex_to_rgb("#FFD700") == (255, 215, 0)
        assert ImageTextOverlayTransformer.hex_to_rgb("#000000") == (0, 0, 0)
        assert ImageTextOverlayTransformer.hex_to_rgb("#FFFFFF") == (255, 255, 255)

    def test_hex_to_rgb_without_hash(self):
        """Test hex color conversion without hash prefix"""
        assert ImageTextOverlayTransformer.hex_to_rgb("FFD700") == (255, 215, 0)
        assert ImageTextOverlayTransformer.hex_to_rgb("000000") == (0, 0, 0)
        assert ImageTextOverlayTransformer.hex_to_rgb("FFFFFF") == (255, 255, 255)

    def test_hex_to_rgb_lowercase(self):
        """Test hex color conversion handles lowercase"""
        assert ImageTextOverlayTransformer.hex_to_rgb("#ff5733") == (255, 87, 51)
        assert ImageTextOverlayTransformer.hex_to_rgb("ff5733") == (255, 87, 51)

    def test_hex_to_rgb_common_colors(self):
        """Test common web colors"""
        assert ImageTextOverlayTransformer.hex_to_rgb("#FF0000") == (255, 0, 0)  # Red
        assert ImageTextOverlayTransformer.hex_to_rgb("#00FF00") == (0, 255, 0)  # Green
        assert ImageTextOverlayTransformer.hex_to_rgb("#0000FF") == (0, 0, 255)  # Blue


class TestGridPositions:
    """Test grid position mappings"""

    def test_grid_positions_all_defined(self):
        """Test all 9 grid positions are defined"""
        expected_positions = [
            "top-left",
            "top-center",
            "top-right",
            "middle-left",
            "center",
            "middle-right",
            "bottom-left",
            "bottom-center",
            "bottom-right",
        ]
        for pos in expected_positions:
            assert pos in ImageTextOverlayTransformer.GRID_POSITIONS

    def test_grid_positions_coordinates(self):
        """Test grid position coordinate values"""
        # Corner positions
        assert ImageTextOverlayTransformer.GRID_POSITIONS["top-left"] == (0.10, 0.10)
        assert ImageTextOverlayTransformer.GRID_POSITIONS["top-right"] == (0.90, 0.10)
        assert ImageTextOverlayTransformer.GRID_POSITIONS["bottom-left"] == (0.10, 0.90)
        assert ImageTextOverlayTransformer.GRID_POSITIONS["bottom-right"] == (0.90, 0.90)

        # Center positions
        assert ImageTextOverlayTransformer.GRID_POSITIONS["center"] == (0.50, 0.50)
        assert ImageTextOverlayTransformer.GRID_POSITIONS["top-center"] == (0.50, 0.10)
        assert ImageTextOverlayTransformer.GRID_POSITIONS["bottom-center"] == (0.50, 0.90)

        # Middle positions
        assert ImageTextOverlayTransformer.GRID_POSITIONS["middle-left"] == (0.10, 0.50)
        assert ImageTextOverlayTransformer.GRID_POSITIONS["middle-right"] == (0.90, 0.50)

    def test_grid_positions_valid_ranges(self):
        """Test all grid positions are within valid range (0.0 - 1.0)"""
        for pos_name, (x, y) in ImageTextOverlayTransformer.GRID_POSITIONS.items():
            assert 0.0 <= x <= 1.0, f"{pos_name} x coordinate {x} out of range"
            assert 0.0 <= y <= 1.0, f"{pos_name} y coordinate {y} out of range"


class TestGetGridCoordinates:
    """Test grid coordinate retrieval"""

    def test_get_grid_coordinates_center(self):
        """Test getting center grid coordinates"""
        x, y = ImageTextOverlayTransformer.get_grid_coordinates("center")
        assert x == 0.50 and y == 0.50

    def test_get_grid_coordinates_top_left(self):
        """Test getting top-left grid coordinates"""
        x, y = ImageTextOverlayTransformer.get_grid_coordinates("top-left")
        assert x == 0.10 and y == 0.10

    def test_get_grid_coordinates_bottom_right(self):
        """Test getting bottom-right grid coordinates"""
        x, y = ImageTextOverlayTransformer.get_grid_coordinates("bottom-right")
        assert x == 0.90 and y == 0.90

    def test_get_grid_coordinates_invalid_fallback(self):
        """Test fallback to center for invalid position"""
        x, y = ImageTextOverlayTransformer.get_grid_coordinates("invalid-position")
        assert x == 0.50 and y == 0.50


class TestGetCustomCoordinates:
    """Test custom coordinate extraction and validation"""

    def test_get_custom_coordinates_valid(self):
        """Test valid custom coordinates"""
        x, y = ImageTextOverlayTransformer.get_custom_coordinates({"x": 0.3, "y": 0.7})
        assert x == 0.3 and y == 0.7

    def test_get_custom_coordinates_clamped_high(self):
        """Test coordinates clamped to 1.0 when too high"""
        x, y = ImageTextOverlayTransformer.get_custom_coordinates({"x": 1.5, "y": 2.0})
        assert x == 1.0 and y == 1.0

    def test_get_custom_coordinates_clamped_low(self):
        """Test coordinates clamped to 0.0 when negative"""
        x, y = ImageTextOverlayTransformer.get_custom_coordinates({"x": -0.5, "y": -1.0})
        assert x == 0.0 and y == 0.0

    def test_get_custom_coordinates_missing_x(self):
        """Test default x=0.5 when missing"""
        x, y = ImageTextOverlayTransformer.get_custom_coordinates({"y": 0.7})
        assert x == 0.5 and y == 0.7

    def test_get_custom_coordinates_missing_y(self):
        """Test default y=0.5 when missing"""
        x, y = ImageTextOverlayTransformer.get_custom_coordinates({"x": 0.3})
        assert x == 0.3 and y == 0.5

    def test_get_custom_coordinates_empty_dict(self):
        """Test default center when empty dict"""
        x, y = ImageTextOverlayTransformer.get_custom_coordinates({})
        assert x == 0.5 and y == 0.5


class TestCalculateTextPositionCustom:
    """Test custom text position calculation"""

    def test_calculate_text_position_custom_center(self):
        """Test custom position at center"""
        x, y = ImageTextOverlayTransformer.calculate_text_position_custom(1000, 800, 0.5, 0.5, 10)
        assert x == 490  # 1000 * 0.5 - 10 (bbox offset)
        assert y == 400  # 800 * 0.5

    def test_calculate_text_position_custom_top_left(self):
        """Test custom position at top-left"""
        x, y = ImageTextOverlayTransformer.calculate_text_position_custom(1000, 800, 0.1, 0.1, 5)
        assert x == 95  # 1000 * 0.1 - 5
        assert y == 80  # 800 * 0.1

    def test_calculate_text_position_custom_zero_offset(self):
        """Test custom position with zero bbox offset"""
        x, y = ImageTextOverlayTransformer.calculate_text_position_custom(1000, 800, 0.5, 0.5, 0)
        assert x == 500
        assert y == 400


class TestCalculateTextPositionGrid:
    """Test grid text position calculation with alignment"""

    def test_calculate_text_position_grid_center(self):
        """Test grid position at center (center-aligned)"""
        x, y = ImageTextOverlayTransformer.calculate_text_position_grid(1000, 800, 0.5, 0.5, 200, 100)
        assert x == 400  # 1000 * 0.5 - (200 // 2)
        assert y == 350  # 800 * 0.5 - (100 // 2)

    def test_calculate_text_position_grid_top_left(self):
        """Test grid position at top-left (left + top aligned)"""
        x, y = ImageTextOverlayTransformer.calculate_text_position_grid(1000, 800, 0.1, 0.1, 200, 100)
        assert x == 100  # 1000 * 0.1 (left-aligned)
        assert y == 80  # 800 * 0.1 (top-aligned)

    def test_calculate_text_position_grid_bottom_right(self):
        """Test grid position at bottom-right (right + bottom aligned)"""
        x, y = ImageTextOverlayTransformer.calculate_text_position_grid(1000, 800, 0.9, 0.9, 200, 100)
        assert x == 700  # 1000 * 0.9 - 200 (right-aligned)
        assert y == 620  # 800 * 0.9 - 100 (bottom-aligned)

    def test_calculate_text_position_grid_middle_left(self):
        """Test grid position at middle-left (left + center aligned)"""
        x, y = ImageTextOverlayTransformer.calculate_text_position_grid(1000, 800, 0.1, 0.5, 200, 100)
        assert x == 100  # 1000 * 0.1 (left-aligned)
        assert y == 350  # 800 * 0.5 - (100 // 2) (center-aligned)


class TestCalculateArtistOffset:
    """Test artist vertical offset calculation"""

    def test_calculate_artist_offset_no_custom_position(self):
        """Test offset when artist follows title (no custom position)"""
        offset = ImageTextOverlayTransformer.calculate_artist_offset(80, 1000, None)
        assert offset == 96  # 80 * 1.2

    def test_calculate_artist_offset_percentage_font_size(self):
        """Test offset with percentage font size"""
        offset = ImageTextOverlayTransformer.calculate_artist_offset(0.08, 1000, None)
        assert offset == 96  # calculate_font_size(0.08, 1000) = 80 → 80 * 1.2

    def test_calculate_artist_offset_with_custom_position(self):
        """Test zero offset when artist has custom position"""
        offset = ImageTextOverlayTransformer.calculate_artist_offset(80, 1000, {"x": 0.5, "y": 0.7})
        assert offset == 0

    def test_calculate_artist_offset_with_grid_position(self):
        """Test zero offset when artist has grid position"""
        offset = ImageTextOverlayTransformer.calculate_artist_offset(80, 1000, "bottom-center")
        assert offset == 0


class TestFontFiles:
    """Test font file mappings"""

    def test_font_files_mapping(self):
        """Test font style mappings are complete"""
        assert "bold" in ImageTextOverlayTransformer.FONT_FILES
        assert "elegant" in ImageTextOverlayTransformer.FONT_FILES
        assert "light" in ImageTextOverlayTransformer.FONT_FILES

        # Verify file names
        assert ImageTextOverlayTransformer.FONT_FILES["bold"] == "Anton-Regular.ttf"
        assert ImageTextOverlayTransformer.FONT_FILES["elegant"] == "PlayfairDisplay-Regular.ttf"
        assert ImageTextOverlayTransformer.FONT_FILES["light"] == "Roboto-Light.ttf"


class TestGetFontPath:
    """Test font path retrieval"""

    def test_get_font_path_bold(self):
        """Test getting bold font path"""
        fonts_dir = Path("/fonts")
        path = ImageTextOverlayTransformer.get_font_path("bold", fonts_dir)
        assert path == fonts_dir / "Anton-Regular.ttf"

    def test_get_font_path_elegant(self):
        """Test getting elegant font path"""
        fonts_dir = Path("/fonts")
        path = ImageTextOverlayTransformer.get_font_path("elegant", fonts_dir)
        assert path == fonts_dir / "PlayfairDisplay-Regular.ttf"

    def test_get_font_path_invalid_fallback(self):
        """Test fallback to default font for invalid style"""
        fonts_dir = Path("/fonts")
        path = ImageTextOverlayTransformer.get_font_path("invalid-style", fonts_dir)
        assert path == fonts_dir / "Anton-Regular.ttf"  # Default is bold
