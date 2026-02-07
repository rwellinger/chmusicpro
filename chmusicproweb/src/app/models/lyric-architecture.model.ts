export enum SongSection {
    INTRO = "INTRO",
    VERSE = "VERSE",
    PRE_CHORUS = "PRE_CHORUS",
    CHORUS = "CHORUS",
    BRIDGE = "BRIDGE",
    OUTRO = "OUTRO"
}

export interface SongSectionItem {
    id: string; // Unique identifier for drag & drop
    section: SongSection;
    displayName: string; // e.g., "VERSE1", "VERSE2", "INTRO"
    originalIndex?: number; // For reordering
}

export interface LyricArchitectureConfig {
    sections: SongSectionItem[];
    lastModified: Date;
}

export interface SongSectionDefinition {
    section: SongSection;
    displayName: string;
    description: string;
    icon: string;
    allowMultiple: boolean;
    maxCount?: number;
}

export const AVAILABLE_SECTIONS: SongSectionDefinition[] = [
    {
        section: SongSection.INTRO,
        displayName: "Intro",
        description: "Opening section of the song",
        icon: "fa-play",
        allowMultiple: false,
        maxCount: 1
    },
    {
        section: SongSection.VERSE,
        displayName: "Verse",
        description: "Main storytelling sections",
        icon: "fa-align-left",
        allowMultiple: true
    },
    {
        section: SongSection.PRE_CHORUS,
        displayName: "Pre-Chorus",
        description: "Builds up to the chorus",
        icon: "fa-arrow-up",
        allowMultiple: true
    },
    {
        section: SongSection.CHORUS,
        displayName: "Chorus",
        description: "Main hook and memorable part",
        icon: "fa-star",
        allowMultiple: true
    },
    {
        section: SongSection.BRIDGE,
        displayName: "Bridge",
        description: "Contrasting middle section",
        icon: "fa-bridge",
        allowMultiple: true
    },
    {
        section: SongSection.OUTRO,
        displayName: "Outro",
        description: "Ending section of the song",
        icon: "fa-stop",
        allowMultiple: false,
        maxCount: 1
    }
];

export const DEFAULT_ARCHITECTURE: LyricArchitectureConfig = {
    sections: [
        {
            id: "verse1",
            section: SongSection.VERSE,
            displayName: "VERSE1"
        },
        {
            id: "chorus1",
            section: SongSection.CHORUS,
            displayName: "CHORUS"
        },
        {
            id: "verse2",
            section: SongSection.VERSE,
            displayName: "VERSE2"
        },
        {
            id: "chorus2",
            section: SongSection.CHORUS,
            displayName: "CHORUS"
        }
    ],
    lastModified: new Date()
};