import {Injectable} from "@angular/core";
import {
    AVAILABLE_SECTIONS,
    DEFAULT_ARCHITECTURE,
    LyricArchitectureConfig,
    SongSection,
    SongSectionItem
} from "../models/lyric-architecture.model";

@Injectable({
    providedIn: "root"
})
export class LyricArchitectureService {
    private readonly STORAGE_KEY = "lyric-architecture-config";

    constructor() {
    }

    getConfig(): LyricArchitectureConfig {
        const stored = localStorage.getItem(this.STORAGE_KEY);
        if (stored) {
            try {
                const config = JSON.parse(stored);
                return {
                    ...config,
                    lastModified: new Date(config.lastModified)
                };
            } catch (error) {
                console.warn("Failed to parse lyric architecture config, using default:", error);
            }
        }
        return {...DEFAULT_ARCHITECTURE};
    }

    saveConfig(config: LyricArchitectureConfig): void {
        const toSave = {
            ...config,
            lastModified: new Date()
        };
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(toSave));
    }

    resetToDefault(): LyricArchitectureConfig {
        const defaultConfig = {...DEFAULT_ARCHITECTURE};
        this.saveConfig(defaultConfig);
        return defaultConfig;
    }

    addSection(section: SongSection): LyricArchitectureConfig {
        const config = this.getConfig();

        // Check if section allows multiple instances
        const sectionDef = AVAILABLE_SECTIONS.find(s => s.section === section);
        if (!sectionDef) {
            throw new Error(`Unknown section: ${section}`);
        }

        // For single-instance sections, check if already exists
        if (!sectionDef.allowMultiple) {
            const exists = config.sections.some(s => s.section === section);
            if (exists) {
                throw new Error(`Section ${section} can only be added once`);
            }
        }

        const newItem = this.createSectionItem(section, config.sections);
        config.sections.push(newItem);
        this.saveConfig(config);
        return config;
    }

    addSectionAtIndex(section: SongSection, index: number): LyricArchitectureConfig {
        const config = this.getConfig();

        // Check if section allows multiple instances
        const sectionDef = AVAILABLE_SECTIONS.find(s => s.section === section);
        if (!sectionDef) {
            throw new Error(`Unknown section: ${section}`);
        }

        // For single-instance sections, check if already exists
        if (!sectionDef.allowMultiple) {
            const exists = config.sections.some(s => s.section === section);
            if (exists) {
                throw new Error(`Section ${section} can only be added once`);
            }
        }

        const newItem = this.createSectionItem(section, config.sections);

        // Insert at specific index instead of pushing to end
        const targetIndex = Math.max(0, Math.min(index, config.sections.length));
        config.sections.splice(targetIndex, 0, newItem);

        // Renumber verses after insertion
        this.renumberVerses(config.sections);

        this.saveConfig(config);
        return config;
    }

    removeSection(itemId: string): LyricArchitectureConfig {
        const config = this.getConfig();
        config.sections = config.sections.filter(s => s.id !== itemId);

        // Renumber verses after removal
        this.renumberVerses(config.sections);

        this.saveConfig(config);
        return config;
    }

    reorderSections(sectionIds: string[]): LyricArchitectureConfig {
        const config = this.getConfig();
        const reordered: SongSectionItem[] = [];

        // Reorder based on provided IDs
        for (const id of sectionIds) {
            const section = config.sections.find(s => s.id === id);
            if (section) {
                reordered.push(section);
            }
        }

        config.sections = reordered;

        // Renumber verses after reordering
        this.renumberVerses(config.sections);

        this.saveConfig(config);
        return config;
    }

    generateArchitectureString(config?: LyricArchitectureConfig): string {
        const currentConfig = config || this.getConfig();

        if (currentConfig.sections.length === 0) {
            return "";
        }

        const sectionNames = currentConfig.sections.map(s => s.displayName);
        return `Song structure: ${sectionNames.join(" - ")}`;
    }

    canAddSection(section: SongSection): boolean {
        const config = this.getConfig();
        const sectionDef = AVAILABLE_SECTIONS.find(s => s.section === section);

        if (!sectionDef) return false;
        if (sectionDef.allowMultiple) return true;

        // For single-instance sections, check if already exists
        return !config.sections.some(s => s.section === section);
    }

    getSectionCount(section: SongSection, config?: LyricArchitectureConfig): number {
        const currentConfig = config || this.getConfig();
        return currentConfig.sections.filter(s => s.section === section).length;
    }

    private createSectionItem(section: SongSection, existingSections: SongSectionItem[]): SongSectionItem {
        const id = this.generateUniqueId();

        let displayName: string;
        if (section === SongSection.VERSE) {
            const verseCount = this.getSectionCount(SongSection.VERSE, {
                sections: existingSections,
                lastModified: new Date()
            });
            displayName = `VERSE${verseCount + 1}`;
        } else {
            displayName = section;
        }

        return {
            id,
            section,
            displayName
        };
    }

    private renumberVerses(sections: SongSectionItem[]): void {
        let verseNumber = 1;

        for (const section of sections) {
            if (section.section === SongSection.VERSE) {
                section.displayName = `VERSE${verseNumber}`;
                verseNumber++;
            }
        }
    }

    private generateUniqueId(): string {
        return `section_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
}