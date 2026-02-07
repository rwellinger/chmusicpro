export interface PromptTemplate {
    id: number;
    category: string;
    action: string;
    pre_condition: string;
    post_condition: string;
    description?: string;
    version?: string;
    model?: string;  // Renamed from model_hint
    temperature?: number;  // Ollama Chat API temperature (0.0-2.0)
    max_tokens?: number;  // Maximum tokens to generate
    active: boolean;
    created_at: string;
    updated_at?: string;
}

export interface PromptTemplateUpdate {
    pre_condition?: string;
    post_condition?: string;
    description?: string;
    model?: string;  // AI model for this template
    temperature?: number;  // Ollama Chat API temperature (0.0-2.0)
    max_tokens?: number;  // Maximum tokens to generate
}

export interface PromptTemplatesResponse {
    categories: Record<string, Record<string, PromptTemplate>>;
}

export interface PromptCategoryResponse {
    category: string;
    templates: Record<string, PromptTemplate>;
}