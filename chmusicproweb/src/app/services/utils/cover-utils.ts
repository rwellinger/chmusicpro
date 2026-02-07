/**
 * Cover Utilities - Shared functions for cover image placeholders
 *
 * Used by Song Release Gallery and Song Projects to generate consistent
 * placeholder covers with initials and color hashing.
 */

/**
 * Extract initials from a name (1-2 characters)
 *
 * @param name - Name to extract initials from
 * @returns Initials (uppercase, 1-2 chars)
 *
 * @example
 * getInitials('My Album') // 'MA'
 * getInitials('Summer') // 'SU'
 * getInitials('') // '?'
 */
export function getInitials(name: string): string {
    if (!name) return "?";

    const words = name.trim().split(/\s+/);

    if (words.length === 1) {
        // Single word: take first 2 characters
        return words[0].substring(0, 2).toUpperCase();
    }

    // Multiple words: take first letter of first 2 words
    return (words[0][0] + words[1][0]).toUpperCase();
}

/**
 * Generate consistent color from string (for cover placeholder backgrounds)
 *
 * Uses a simple hash function to generate a consistent HSL color from any string.
 * Same input always produces the same color.
 *
 * @param text - Text to generate color from
 * @returns HSL color string (e.g., 'hsl(120, 60%, 55%)')
 *
 * @example
 * getColorFromString('My Album') // 'hsl(234, 60%, 55%)'
 * getColorFromString('My Album') // Always returns same color
 */
export function getColorFromString(text: string): string {
    if (!text) return "#5a6268"; // Default gray

    // Simple hash function
    let hash = 0;
    for (let i = 0; i < text.length; i++) {
        hash = text.charCodeAt(i) + ((hash << 5) - hash);
    }

    // Generate HSL color (pastel-like colors for better readability)
    const hue = Math.abs(hash % 360);
    const saturation = 60; // Medium saturation for pleasant colors
    const lightness = 55; // Medium lightness for good contrast

    return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}
