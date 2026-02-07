export interface Workshop {
    id: string;
    title: string;
    connect_topic?: string;
    connect_inspirations?: string;
    collect_mindmap?: string;
    collect_stories?: string;
    collect_words?: string;
    shape_structure?: string;
    shape_rhymes?: string;
    shape_draft?: string;
    current_phase: WorkshopPhase;
    draft_language?: string;
    exported_sketch_id?: string;
    created_at: string;
    updated_at?: string;
}

export type WorkshopPhase = "connect" | "collect" | "shape" | "completed";

export interface WorkshopListResponse {
    data: Workshop[];
    pagination: {
        total: number;
        limit: number;
        offset: number;
        has_more: boolean;
    };
}

export interface WorkshopDetailResponse {
    data: Workshop;
    success: boolean;
    message?: string;
}
