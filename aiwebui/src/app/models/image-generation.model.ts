/**
 * TypeScript models for Image Generation feature
 * Matches backend schemas in aiproxysrv/src/schemas/image_schemas.py
 */

// ============================================================================
// Type Definitions (String Unions for Dropdowns)
// ============================================================================

export type ArtisticStyle =
    | "auto"
    | "photorealistic"
    | "digital-art"
    | "oil-painting"
    | "watercolor"
    | "cartoon"
    | "anime"
    | "sketch"
    | "3d-render";

export type CompositionStyle =
    | "auto"
    | "portrait"
    | "landscape"
    | "wide-angle"
    | "close-up"
    | "rule-of-thirds"
    | "centered"
    | "album-cover";

export type LightingStyle = "auto" | "natural" | "studio" | "dramatic" | "golden-hour" | "night";

export type ColorPaletteStyle =
    | "auto"
    | "vibrant"
    | "muted"
    | "monochrome"
    | "high-contrast"
    | "warm"
    | "cool"
    | "pastel";

export type DetailLevel = "auto" | "minimal" | "moderate" | "highly-detailed";

export type EnhanceQuality = "auto" | "quality" | "fast" | "off";

// ============================================================================
// Interfaces
// ============================================================================

/**
 * Style preferences for guided image generation
 * Stored in LocalStorage and sent to backend
 */
export interface StylePreferences {
    artisticStyle: ArtisticStyle;
    composition: CompositionStyle;
    lighting: LightingStyle;
    colorPalette: ColorPaletteStyle;
    detailLevel: DetailLevel;
    enhanceQuality: EnhanceQuality;
}

/**
 * Image generation request (matches backend ImageGenerateRequest)
 */
export interface ImageGenerationRequest {
    prompt: string;
    user_prompt?: string;
    size?: string;
    title?: string;
    artistic_style?: string;
    composition?: string;
    lighting?: string;
    color_palette?: string;
    detail_level?: string;
}

/**
 * Image response (matches backend ImageResponse)
 */
export interface Image {
    id: string;
    title: string | null;
    user_prompt: string | null;
    prompt: string;
    enhanced_prompt: string | null;
    size: string | null;
    status: string;
    url: string | null;
    created_at: string;
    completed_at: string | null;
    tags: string[] | null;
    artistic_style: string | null;
    composition: string | null;
    lighting: string | null;
    color_palette: string | null;
    detail_level: string | null;
}

/**
 * Dropdown option for mat-select
 */
export interface SelectOption<T = string> {
    value: T;
    labelKey: string; // i18n key, e.g. 'imageGenerator.styles.artisticStyle.options.photorealistic'
}

// ============================================================================
// Default Values
// ============================================================================

export const DEFAULT_STYLE_PREFERENCES: StylePreferences = {
    artisticStyle: "auto",
    composition: "auto",
    lighting: "auto",
    colorPalette: "auto",
    detailLevel: "auto",
    enhanceQuality: "auto",
};
