import {inject, Injectable} from "@angular/core";
import {TranslateService} from "@ngx-translate/core";
import {
    DEFAULT_STYLE_CHOOSER_CONFIG,
    MUSIC_STYLE_CATEGORIES,
    MusicStyleChooserConfig
} from "../models/music-style-chooser.model";

@Injectable({
    providedIn: "root"
})
export class MusicStyleChooserService {
    private readonly STORAGE_KEY = "music-style-chooser-config";
    private translate = inject(TranslateService);

    getConfig(): MusicStyleChooserConfig {
        const stored = localStorage.getItem(this.STORAGE_KEY);
        if (stored) {
            try {
                const config = JSON.parse(stored);
                return {
                    selectedStyles: config.selectedStyles || [],
                    selectedThemes: config.selectedThemes || [],
                    selectedInstruments: config.selectedInstruments || [], // Backward compatibility
                    lastModified: new Date(config.lastModified || new Date())
                };
            } catch (error) {
                console.warn("Failed to parse music style chooser config, using default:", error);
            }
        }
        return {...DEFAULT_STYLE_CHOOSER_CONFIG};
    }

    saveConfig(config: MusicStyleChooserConfig): void {
        const toSave = {
            ...config,
            lastModified: new Date()
        };
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(toSave));
    }

    resetToDefault(): MusicStyleChooserConfig {
        const defaultConfig = {...DEFAULT_STYLE_CHOOSER_CONFIG};
        this.saveConfig(defaultConfig);
        return defaultConfig;
    }

    toggleStyle(style: string): MusicStyleChooserConfig {
        const config = this.getConfig();
        const index = config.selectedStyles.indexOf(style);

        if (index > -1) {
            config.selectedStyles.splice(index, 1);
        } else {
            if (MUSIC_STYLE_CATEGORIES.style.includes(style)) {
                config.selectedStyles.push(style);
            }
        }

        this.saveConfig(config);
        return config;
    }

    toggleTheme(theme: string): MusicStyleChooserConfig {
        const config = this.getConfig();
        const index = config.selectedThemes.indexOf(theme);

        if (index > -1) {
            config.selectedThemes.splice(index, 1);
        } else {
            if (MUSIC_STYLE_CATEGORIES.theme.includes(theme)) {
                config.selectedThemes.push(theme);
            }
        }

        this.saveConfig(config);
        return config;
    }

    toggleInstrument(instrument: string): MusicStyleChooserConfig {
        const config = this.getConfig();
        const index = config.selectedInstruments.indexOf(instrument);

        if (index > -1) {
            config.selectedInstruments.splice(index, 1);
        } else {
            if (MUSIC_STYLE_CATEGORIES.instruments.includes(instrument)) {
                config.selectedInstruments.push(instrument);
            }
        }

        this.saveConfig(config);
        return config;
    }

    generateStylePrompt(config?: MusicStyleChooserConfig, isInstrumental?: boolean): string {
        const currentConfig = config || this.getConfig();

        // Ensure all arrays exist with fallbacks
        const styles = currentConfig.selectedStyles || [];
        const themes = currentConfig.selectedThemes || [];
        let instruments = currentConfig.selectedInstruments || [];

        // Remove vocals if instrumental mode (including legacy 'vocals')
        if (isInstrumental) {
            instruments = instruments.filter(i => i !== "male-voice" && i !== "female-voice" && i !== "vocals");
        }

        if (styles.length === 0 && themes.length === 0 && instruments.length === 0) {
            return "";
        }

        // Get current language
        const currentLang = this.translate.currentLang || "en";
        const isGerman = currentLang === "de";

        // i18n strings
        const i18n = {
            music: isGerman ? "Musik" : "music",
            with: isGerman ? "mit" : "with",
            withThemesOf: isGerman ? "mit Themen von" : "with themes of",
            vocals: isGerman ? "Gesang" : "vocals"
        };

        let prompt = "";

        if (styles.length > 0) {
            prompt = styles.join(", ") + " " + i18n.music;
        } else {
            prompt = i18n.music;
        }

        if (instruments.length > 0) {
            // Separate voice instruments from other instruments
            const voiceInstruments = instruments.filter(i => i === "male-voice" || i === "female-voice");
            const otherInstruments = instruments.filter(i => i !== "male-voice" && i !== "female-voice");

            // Vocals first (better hit rate for Mureka)
            if (voiceInstruments.length > 0) {
                const voiceType = voiceInstruments[0].replace("-voice", "");
                const voiceLabel = isGerman
                    ? (voiceType === "male" ? "männlicher" : "weiblicher") + " " + i18n.vocals
                    : voiceType + " " + i18n.vocals;
                prompt += " " + i18n.with + " " + voiceLabel;
            }

            // Other instruments after vocals
            if (otherInstruments.length > 0) {
                if (voiceInstruments.length > 0) {
                    prompt += ", " + otherInstruments.join(", ");
                } else {
                    prompt += " " + i18n.with + " " + otherInstruments.join(", ");
                }
            }
        }

        if (themes.length > 0) {
            prompt += " " + i18n.withThemesOf + " " + themes.join(", ");
        }

        return prompt;
    }

    isStyleSelected(style: string, config?: MusicStyleChooserConfig): boolean {
        const currentConfig = config || this.getConfig();
        return (currentConfig.selectedStyles || []).includes(style);
    }

    isThemeSelected(theme: string, config?: MusicStyleChooserConfig): boolean {
        const currentConfig = config || this.getConfig();
        return (currentConfig.selectedThemes || []).includes(theme);
    }

    isInstrumentSelected(instrument: string, config?: MusicStyleChooserConfig): boolean {
        const currentConfig = config || this.getConfig();
        return (currentConfig.selectedInstruments || []).includes(instrument);
    }

    getAvailableStyles(): string[] {
        return [...MUSIC_STYLE_CATEGORIES.style];
    }

    getAvailableThemes(): string[] {
        return [...MUSIC_STYLE_CATEGORIES.theme];
    }

    getAvailableInstruments(): string[] {
        return [...MUSIC_STYLE_CATEGORIES.instruments];
    }

    /**
     * Parse a prompt string to extract music style selections.
     * Returns config and isAutoMode flag if the prompt matches the auto-mode pattern.
     * Returns null if the prompt doesn't match or contains invalid selections.
     */
    parsePromptToSelections(prompt: string): { config: MusicStyleChooserConfig; isAutoMode: boolean } | null {
        if (!prompt || prompt.trim() === "") {
            return null;
        }

        const trimmedPrompt = prompt.trim();

        // Check if prompt matches auto-mode pattern (EN or DE)
        // Pattern: "{styles} music|Musik [with|mit {instruments}] [with themes of|mit Themen von {themes}]"

        const musicRegex = /(.*?)\s+(music|Musik)/i;
        const musicMatch = trimmedPrompt.match(musicRegex);

        if (!musicMatch) {
            return null; // Doesn't match basic pattern
        }

        // Extract styles (everything before "music|Musik")
        const stylesStr = musicMatch[1].trim();
        const extractedStyles = stylesStr ? stylesStr.split(",").map(s => s.trim()).filter(s => s) : [];

        // Extract instruments (after "with|mit" and before "with themes of|mit Themen von")
        const instrumentsRegex = /(?:with|mit)\s+(.+?)(?:\s+(?:with themes of|mit Themen von)|$)/i;
        const instrumentsMatch = trimmedPrompt.match(instrumentsRegex);
        let extractedInstruments: string[] = [];

        if (instrumentsMatch) {
            const instrumentsStr = instrumentsMatch[1].trim();
            extractedInstruments = instrumentsStr.split(",").map(s => s.trim()).filter(s => s);

            // Filter out "male vocals" / "female vocals" / "männlicher Gesang" / "weiblicher Gesang"
            // and convert back to "male-voice" / "female-voice"
            extractedInstruments = extractedInstruments.map(inst => {
                if (inst.match(/male\s+vocals/i)) return "male-voice";
                if (inst.match(/female\s+vocals/i)) return "female-voice";
                if (inst.match(/männlicher\s+Gesang/i)) return "male-voice";
                if (inst.match(/weiblicher\s+Gesang/i)) return "female-voice";
                return inst;
            });
        }

        // Extract themes (after "with themes of|mit Themen von")
        const themesRegex = /(?:with themes of|mit Themen von)\s+(.+)$/i;
        const themesMatch = trimmedPrompt.match(themesRegex);
        const extractedThemes = themesMatch ? themesMatch[1].split(",").map(s => s.trim()).filter(s => s) : [];

        // Validate all extracted values against available categories
        const validStyles = extractedStyles.filter(s => MUSIC_STYLE_CATEGORIES.style.includes(s));
        const validInstruments = extractedInstruments.filter(i => MUSIC_STYLE_CATEGORIES.instruments.includes(i));
        const validThemes = extractedThemes.filter(t => MUSIC_STYLE_CATEGORIES.theme.includes(t));

        // Only consider it auto-mode if at least some selections were found and all are valid
        if (extractedStyles.length > 0 && validStyles.length !== extractedStyles.length) {
            return null; // Invalid styles found
        }
        if (extractedInstruments.length > 0 && validInstruments.length !== extractedInstruments.length) {
            return null; // Invalid instruments found
        }
        if (extractedThemes.length > 0 && validThemes.length !== extractedThemes.length) {
            return null; // Invalid themes found
        }

        // Must have at least one selection
        if (validStyles.length === 0 && validInstruments.length === 0 && validThemes.length === 0) {
            return null;
        }

        return {
            config: {
                selectedStyles: validStyles,
                selectedInstruments: validInstruments,
                selectedThemes: validThemes,
                lastModified: new Date()
            },
            isAutoMode: true
        };
    }
}