export const SUNO_LYRICS_CHAR_LIMIT = 3000;
export const SUNO_LYRICS_WARNING_LIMIT = 2400;
export const SUNO_STYLE_CHAR_LIMIT = 1000;
export const SUNO_STYLE_WARNING_LIMIT = 800;

export interface SunoTag {
    label: string;
    tag: string;
    supportsModifiers: boolean;
}

export interface SunoTagCategory {
    key: string;
    labelKey: string;
    icon: string;
    mode: 'song' | 'edm' | 'both';
    tags: SunoTag[];
}

export const SUNO_TAG_CATEGORIES: SunoTagCategory[] = [
    {
        key: 'structure_song',
        labelKey: 'sunoEnhancer.categories.structureSong',
        icon: 'fa-list-ol',
        mode: 'song',
        tags: [
            {label: 'Intro', tag: 'INTRO', supportsModifiers: true},
            {label: 'Verse', tag: 'VERSE', supportsModifiers: true},
            {label: 'Verse 1', tag: 'VERSE 1', supportsModifiers: true},
            {label: 'Verse 2', tag: 'VERSE 2', supportsModifiers: true},
            {label: 'Pre-Chorus', tag: 'PRE-CHORUS', supportsModifiers: true},
            {label: 'Chorus', tag: 'CHORUS', supportsModifiers: true},
            {label: 'Post-Chorus', tag: 'POST-CHORUS', supportsModifiers: true},
            {label: 'Bridge', tag: 'BRIDGE', supportsModifiers: true},
            {label: 'Outro', tag: 'OUTRO', supportsModifiers: true},
            {label: 'Interlude', tag: 'INTERLUDE', supportsModifiers: true},
            {label: 'Refrain', tag: 'REFRAIN', supportsModifiers: true},
            {label: 'Hook', tag: 'HOOK', supportsModifiers: true},
        ]
    },
    {
        key: 'structure_edm',
        labelKey: 'sunoEnhancer.categories.structureEDM',
        icon: 'fa-bolt',
        mode: 'edm',
        tags: [
            {label: 'Intro', tag: 'INTRO', supportsModifiers: true},
            {label: 'Build', tag: 'BUILD', supportsModifiers: true},
            {label: 'Build-Up', tag: 'BUILD-UP', supportsModifiers: true},
            {label: 'Drop', tag: 'DROP', supportsModifiers: true},
            {label: 'Breakdown', tag: 'BREAKDOWN', supportsModifiers: true},
            {label: 'Rise', tag: 'RISE', supportsModifiers: true},
            {label: 'Riser', tag: 'RISER', supportsModifiers: true},
            {label: 'Climax', tag: 'CLIMAX', supportsModifiers: true},
            {label: 'Transition', tag: 'TRANSITION', supportsModifiers: true},
            {label: 'Ambient', tag: 'AMBIENT', supportsModifiers: true},
            {label: 'Bass Drop', tag: 'BASS DROP', supportsModifiers: true},
        ]
    },
    {
        key: 'instrument_solos',
        labelKey: 'sunoEnhancer.categories.instrumentSolos',
        icon: 'fa-guitar',
        mode: 'both',
        tags: [
            {label: 'Guitar Solo', tag: 'GUITAR SOLO', supportsModifiers: true},
            {label: 'Piano Solo', tag: 'PIANO SOLO', supportsModifiers: true},
            {label: 'Sax Solo', tag: 'SAX SOLO', supportsModifiers: true},
            {label: 'Violin Solo', tag: 'VIOLIN SOLO', supportsModifiers: true},
            {label: 'Trumpet Solo', tag: 'TRUMPET SOLO', supportsModifiers: true},
            {label: 'Drum Solo', tag: 'DRUM SOLO', supportsModifiers: true},
            {label: 'Bass Solo', tag: 'BASS SOLO', supportsModifiers: true},
            {label: 'Synth Solo', tag: 'SYNTH SOLO', supportsModifiers: true},
            {label: 'Harmonica Solo', tag: 'HARMONICA SOLO', supportsModifiers: true},
            {label: 'Flute Solo', tag: 'FLUTE SOLO', supportsModifiers: true},
            {label: 'Organ Solo', tag: 'ORGAN SOLO', supportsModifiers: true},
        ]
    },
    {
        key: 'breaks',
        labelKey: 'sunoEnhancer.categories.breaks',
        icon: 'fa-pause',
        mode: 'both',
        tags: [
            {label: 'Break', tag: 'BREAK', supportsModifiers: true},
            {label: 'Instrumental Break', tag: 'INSTRUMENTAL BREAK', supportsModifiers: true},
            {label: 'Percussion Break', tag: 'PERCUSSION BREAK', supportsModifiers: true},
            {label: 'Break for 4 Beats', tag: 'BREAK FOR 4 BEATS', supportsModifiers: false},
            {label: 'Break for 8 Beats', tag: 'BREAK FOR 8 BEATS', supportsModifiers: false},
        ]
    },
    {
        key: 'endings',
        labelKey: 'sunoEnhancer.categories.endings',
        icon: 'fa-flag-checkered',
        mode: 'both',
        tags: [
            {label: 'Outro', tag: 'OUTRO', supportsModifiers: true},
            {label: 'Outro: Fade Out', tag: 'OUTRO: FADE OUT', supportsModifiers: false},
            {label: 'Outro: Big Finish', tag: 'OUTRO: BIG FINISH', supportsModifiers: false},
            {label: 'End', tag: 'END', supportsModifiers: false},
            {label: 'Fade Out', tag: 'FADE OUT', supportsModifiers: false},
        ]
    },
    {
        key: 'effects',
        labelKey: 'sunoEnhancer.categories.effects',
        icon: 'fa-wand-sparkles',
        mode: 'both',
        tags: [
            {label: 'Rain', tag: 'RAIN', supportsModifiers: false},
            {label: 'Thunder', tag: 'THUNDER', supportsModifiers: false},
            {label: 'Wind', tag: 'WIND', supportsModifiers: false},
            {label: 'Birds Chirping', tag: 'BIRDS CHIRPING', supportsModifiers: false},
            {label: 'Crowd Noise', tag: 'CROWD NOISE', supportsModifiers: false},
            {label: 'Applause', tag: 'APPLAUSE', supportsModifiers: false},
            {label: 'Vinyl Crackle', tag: 'VINYL CRACKLE', supportsModifiers: false},
            {label: 'Static', tag: 'STATIC', supportsModifiers: false},
            {label: 'Heartbeat', tag: 'HEARTBEAT', supportsModifiers: false},
            {label: 'Footsteps', tag: 'FOOTSTEPS', supportsModifiers: false},
            {label: 'Ocean Waves', tag: 'OCEAN WAVES', supportsModifiers: false},
            {label: 'Clock Ticking', tag: 'CLOCK TICKING', supportsModifiers: false},
            {label: 'Whispers', tag: 'WHISPERS', supportsModifiers: false},
        ]
    },
];

export const SUNO_MODIFIERS: string[] = [
    'SOFT',
    'GENTLE',
    'POWERFUL',
    'STRONG',
    'INTIMATE',
    'MINIMAL',
    'LAYERED VOCALS',
    'AMBIENT',
    'HYPNOTIC',
    'DRIVING',
    'ENERGETIC',
    'WARM',
    'BRIGHT',
    'DEEP',
    'BIG FINISH',
    'DREAMY',
    'AGGRESSIVE',
    'MELANCHOLIC',
    'EUPHORIC',
    'SPARSE',
];
