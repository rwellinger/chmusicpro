export interface SystemContextTemplate {
    id: string;
    name: string;
    description?: string;
    content: string;
    sort_order: number;
    active: boolean;
    created_at: string;
    updated_at?: string;
}

export interface SystemContextTemplateCreate {
    name: string;
    description?: string;
    content: string;
    sort_order: number;
    active: boolean;
}

export interface SystemContextTemplateUpdate {
    name?: string;
    description?: string;
    content?: string;
    sort_order?: number;
    active?: boolean;
}

export interface SystemContextTemplateListResponse {
    templates: SystemContextTemplate[];
    total: number;
}
