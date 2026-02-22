export interface SunoTemplate {
    id: string;
    title: string;
    template_type: 'song' | 'instrumental';
    source_sketch_id?: string;
    original_lyrics?: string;
    enhanced_lyrics?: string;
    genre?: string;
    bpm?: number;
    vocal_type?: string;
    instruments?: string;
    mood?: string;
    mix_character?: string;
    style_prompt?: string;
    is_instrumental: boolean;
    project_id?: string;
    project_folder_id?: string;
    project_name?: string;
    created_at: string;
    updated_at?: string;
}

export interface SunoTemplateListResponse {
    data: SunoTemplate[];
    pagination: {
        total: number;
        limit: number;
        offset: number;
        has_more: boolean;
    };
}

export interface SunoTemplateDetailResponse {
    data: SunoTemplate;
    success: boolean;
    message?: string;
}
