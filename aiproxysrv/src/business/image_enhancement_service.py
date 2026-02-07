"""Service for image prompt enhancement with style mappings"""


class ImageEnhancementService:
    """Service for constructing enhanced prompts with style preferences"""

    # Style mappings from frontend values to DALL-E prompt fragments
    STYLE_MAPPINGS = {
        "auto": "",
        "photorealistic": "photorealistic style, realistic rendering, high fidelity",
        "digital-art": "digital art, modern illustration, digital painting",
        "oil-painting": "oil painting style, painterly brushstrokes, classical art",
        "watercolor": "watercolor painting, soft wet medium, flowing colors",
        "cartoon": "cartoon illustration, cel-shaded, bold outlines",
        "anime": "anime/manga art style, Japanese animation aesthetic",
        "sketch": "pencil sketch, hand-drawn, charcoal, monochrome",
        "3d-render": "3D render, CGI, computer generated imagery",
    }

    COMPOSITION_MAPPINGS = {
        "auto": "",
        "portrait": "portrait composition, vertical framing, subject-focused",
        "landscape": "landscape composition, horizontal framing, wide view",
        "wide-angle": "wide-angle shot, expansive view, environmental context",
        "close-up": "close-up shot, detailed view, tight framing",
        "rule-of-thirds": "rule of thirds composition, balanced placement",
        "centered": "centered composition, symmetrical, focal point",
        "album-cover": "",  # Album cover enhancement handled by frontend (includes title + artist)
    }

    LIGHTING_MAPPINGS = {
        "auto": "",
        "natural": "natural daylight, soft ambient lighting, outdoor illumination",
        "studio": "professional studio lighting, controlled setup, even illumination",
        "dramatic": "dramatic lighting, strong shadows, moody atmosphere, chiaroscuro",
        "golden-hour": "golden hour lighting, warm sunset glow, magical hour",
        "night": "night scene, low light, atmospheric darkness, nocturnal",
    }

    COLOR_PALETTE_MAPPINGS = {
        "auto": "",
        "vibrant": "vibrant color palette, saturated colors, bold hues",
        "muted": "muted color palette, subtle tones, understated colors",
        "monochrome": "monochrome, black and white, grayscale",
        "high-contrast": "high contrast, bold colors, striking color differences",
        "warm": "warm color palette, oranges and reds, cozy tones",
        "cool": "cool color palette, blues and greens, calming tones",
        "pastel": "pastel colors, soft hues, gentle tones",
    }

    DETAIL_LEVEL_MAPPINGS = {
        "auto": "",
        "minimal": "minimalist, simple, clean, uncluttered",
        "moderate": "moderate detail, balanced complexity",
        "highly-detailed": "highly detailed, intricate, sharp focus, meticulous",
    }

    @staticmethod
    def construct_enhanced_prompt(
        base_prompt: str,
        artistic_style: str | None = None,
        composition: str | None = None,
        lighting: str | None = None,
        color_palette: str | None = None,
        detail_level: str | None = None,
    ) -> str:
        """
        Construct enhanced prompt by combining base prompt with style fragments.

        Args:
            base_prompt: Original user prompt
            artistic_style: Selected artistic style (e.g., 'photorealistic', 'auto')
            composition: Selected composition (e.g., 'landscape', 'auto')
            lighting: Selected lighting (e.g., 'golden-hour', 'auto')
            color_palette: Selected color palette (e.g., 'warm', 'auto')
            detail_level: Selected detail level (e.g., 'highly-detailed', 'auto')

        Returns:
            Enhanced prompt string with style fragments appended
        """
        fragments = [base_prompt.strip()]

        # Add style fragments (skip 'auto' or None values)
        if artistic_style and artistic_style != "auto":
            fragment = ImageEnhancementService.STYLE_MAPPINGS.get(artistic_style, "")
            if fragment:
                fragments.append(fragment)

        if composition and composition != "auto":
            fragment = ImageEnhancementService.COMPOSITION_MAPPINGS.get(composition, "")
            if fragment:
                fragments.append(fragment)

        if lighting and lighting != "auto":
            fragment = ImageEnhancementService.LIGHTING_MAPPINGS.get(lighting, "")
            if fragment:
                fragments.append(fragment)

        if color_palette and color_palette != "auto":
            fragment = ImageEnhancementService.COLOR_PALETTE_MAPPINGS.get(color_palette, "")
            if fragment:
                fragments.append(fragment)

        if detail_level and detail_level != "auto":
            fragment = ImageEnhancementService.DETAIL_LEVEL_MAPPINGS.get(detail_level, "")
            if fragment:
                fragments.append(fragment)

        # Join with comma-space
        return ", ".join(fragments)

    @staticmethod
    def has_manual_styles(
        artistic_style: str | None = None,
        composition: str | None = None,
        lighting: str | None = None,
        color_palette: str | None = None,
        detail_level: str | None = None,
    ) -> bool:
        """
        Check if any manual styles are selected (not 'auto' or None).

        Args:
            artistic_style: Selected artistic style
            composition: Selected composition
            lighting: Selected lighting
            color_palette: Selected color palette
            detail_level: Selected detail level

        Returns:
            True if at least one manual style is selected
        """
        return any(
            [
                artistic_style and artistic_style != "auto",
                composition and composition != "auto",
                lighting and lighting != "auto",
                color_palette and color_palette != "auto",
                detail_level and detail_level != "auto",
            ]
        )
