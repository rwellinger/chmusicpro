"""Unit tests for ImageEnhancementService"""

import pytest

from business.image_enhancement_service import ImageEnhancementService


@pytest.mark.unit
class TestImageEnhancementService:
    """Test ImageEnhancementService methods"""

    def test_construct_enhanced_prompt_no_styles(self):
        """Test prompt construction with no styles (all auto/None)"""
        result = ImageEnhancementService.construct_enhanced_prompt(
            base_prompt="a beautiful sunset",
            artistic_style="auto",
            composition="auto",
            lighting="auto",
            color_palette="auto",
            detail_level="auto",
        )

        assert result == "a beautiful sunset"

    def test_construct_enhanced_prompt_single_style(self):
        """Test prompt construction with single style"""
        result = ImageEnhancementService.construct_enhanced_prompt(
            base_prompt="a beautiful sunset",
            artistic_style="photorealistic",
        )

        assert result == "a beautiful sunset, photorealistic style, realistic rendering, high fidelity"

    def test_construct_enhanced_prompt_multiple_styles(self):
        """Test prompt construction with multiple styles"""
        result = ImageEnhancementService.construct_enhanced_prompt(
            base_prompt="a clown",
            artistic_style="cartoon",
            composition="portrait",
            lighting="studio",
            color_palette="vibrant",
            detail_level="highly-detailed",
        )

        expected_fragments = [
            "a clown",
            "cartoon illustration, cel-shaded, bold outlines",
            "portrait composition, vertical framing, subject-focused",
            "professional studio lighting, controlled setup, even illumination",
            "vibrant color palette, saturated colors, bold hues",
            "highly detailed, intricate, sharp focus, meticulous",
        ]
        expected = ", ".join(expected_fragments)

        assert result == expected

    def test_construct_enhanced_prompt_mixed_auto_and_styles(self):
        """Test prompt construction with mix of auto and specific styles"""
        result = ImageEnhancementService.construct_enhanced_prompt(
            base_prompt="futuristic city",
            artistic_style="3d-render",
            composition="auto",  # Should be skipped
            lighting="night",
            color_palette="auto",  # Should be skipped
            detail_level="moderate",
        )

        expected_fragments = [
            "futuristic city",
            "3D render, CGI, computer generated imagery",
            "night scene, low light, atmospheric darkness, nocturnal",
            "moderate detail, balanced complexity",
        ]
        expected = ", ".join(expected_fragments)

        assert result == expected

    def test_construct_enhanced_prompt_all_none(self):
        """Test prompt construction with all None values"""
        result = ImageEnhancementService.construct_enhanced_prompt(
            base_prompt="a landscape",
            artistic_style=None,
            composition=None,
            lighting=None,
            color_palette=None,
            detail_level=None,
        )

        assert result == "a landscape"

    def test_construct_enhanced_prompt_unknown_style_ignored(self):
        """Test that unknown style values are safely ignored"""
        result = ImageEnhancementService.construct_enhanced_prompt(
            base_prompt="a scene",
            artistic_style="unknown-style",  # Not in mappings
            composition="landscape",
        )

        # Unknown style should be ignored, valid style should be included
        assert "a scene" in result
        assert "landscape composition" in result
        assert "unknown-style" not in result

    def test_has_manual_styles_all_auto(self):
        """Test has_manual_styles returns False when all are auto"""
        result = ImageEnhancementService.has_manual_styles(
            artistic_style="auto",
            composition="auto",
            lighting="auto",
            color_palette="auto",
            detail_level="auto",
        )

        assert result is False

    def test_has_manual_styles_all_none(self):
        """Test has_manual_styles returns False when all are None"""
        result = ImageEnhancementService.has_manual_styles(
            artistic_style=None,
            composition=None,
            lighting=None,
            color_palette=None,
            detail_level=None,
        )

        assert result is False

    def test_has_manual_styles_single_manual(self):
        """Test has_manual_styles returns True with single manual style"""
        result = ImageEnhancementService.has_manual_styles(
            artistic_style="photorealistic",
            composition="auto",
            lighting="auto",
            color_palette="auto",
            detail_level="auto",
        )

        assert result is True

    def test_has_manual_styles_multiple_manual(self):
        """Test has_manual_styles returns True with multiple manual styles"""
        result = ImageEnhancementService.has_manual_styles(
            artistic_style="cartoon",
            composition="portrait",
            lighting="auto",
            color_palette="vibrant",
            detail_level="auto",
        )

        assert result is True

    def test_has_manual_styles_mixed_none_and_auto(self):
        """Test has_manual_styles with mix of None and auto"""
        result = ImageEnhancementService.has_manual_styles(
            artistic_style=None,
            composition="auto",
            lighting=None,
            color_palette="auto",
            detail_level=None,
        )

        assert result is False

    def test_style_mappings_complete(self):
        """Test that all style mappings contain 'auto' key"""
        assert "auto" in ImageEnhancementService.STYLE_MAPPINGS
        assert "auto" in ImageEnhancementService.COMPOSITION_MAPPINGS
        assert "auto" in ImageEnhancementService.LIGHTING_MAPPINGS
        assert "auto" in ImageEnhancementService.COLOR_PALETTE_MAPPINGS
        assert "auto" in ImageEnhancementService.DETAIL_LEVEL_MAPPINGS

        # And auto should map to empty string
        assert ImageEnhancementService.STYLE_MAPPINGS["auto"] == ""
        assert ImageEnhancementService.COMPOSITION_MAPPINGS["auto"] == ""
        assert ImageEnhancementService.LIGHTING_MAPPINGS["auto"] == ""
        assert ImageEnhancementService.COLOR_PALETTE_MAPPINGS["auto"] == ""
        assert ImageEnhancementService.DETAIL_LEVEL_MAPPINGS["auto"] == ""

    def test_construct_enhanced_prompt_preserves_base_prompt(self):
        """Test that base prompt is always preserved as first fragment"""
        base = "my original prompt"
        result = ImageEnhancementService.construct_enhanced_prompt(
            base_prompt=base,
            artistic_style="watercolor",
        )

        # Should start with base prompt
        assert result.startswith(base)

    def test_construct_enhanced_prompt_whitespace_handling(self):
        """Test that whitespace in base prompt is trimmed"""
        result = ImageEnhancementService.construct_enhanced_prompt(
            base_prompt="  a sunset  ",
            artistic_style="oil-painting",
        )

        # Should trim whitespace from base prompt
        assert result.startswith("a sunset,")
        assert not result.startswith("  ")
