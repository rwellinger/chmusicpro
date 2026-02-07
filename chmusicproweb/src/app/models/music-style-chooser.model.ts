export interface MusicStyleChooserConfig {
    selectedStyles: string[];
    selectedThemes: string[];
    selectedInstruments: string[];
    lastModified: Date;
}

export interface MusicStyleCategories {
    style: string[];
    theme: string[];
    instruments: string[];
    useCase: string[];
}

export const MUSIC_STYLE_CATEGORIES: MusicStyleCategories = {
    style: ["pop", "rock", "alternative", "jazz", "classical", "electronic", "techno", "hip-hop", "r&b", "country", "folk", "blues", "reggae", "funk", "world"],
    theme: ["love", "power", "friendship", "adventure", "nostalgia", "hope", "struggle", "celebration", "mystery", "nature", "dreams"],
    instruments: ["acoustic-guitar", "electric-guitar", "acoustic-bass", "electric-bass", "acoustic-piano", "electric-piano", "synth", "strings", "brass", "woodwind", "drums", "male-voice", "female-voice"],
    useCase: ["unused", "cover", "song", "inspiration", "video", "demo"] // lowercase for consistency
};

export const DEFAULT_STYLE_CHOOSER_CONFIG: MusicStyleChooserConfig = {
    selectedStyles: [],
    selectedThemes: [],
    selectedInstruments: [],
    lastModified: new Date()
};