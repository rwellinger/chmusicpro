export interface ModelContextWindow {
    id: number;
    model_name: string;
    context_window: number;
    provider: string;
    description?: string;
    created_at?: string;
    updated_at?: string;
}

export interface ModelContextWindowCreate {
    model_name: string;
    context_window: number;
    provider: string;
    description?: string;
}

export interface ModelContextWindowUpdate {
    model_name?: string;
    context_window?: number;
    provider?: string;
    description?: string;
}
