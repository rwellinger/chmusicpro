export type AIMode = "internal" | "external" | "hybrid";
export type AIProvider = "ollama" | "openai" | "claude";

export interface AIConfig {
    mode: AIMode;
    available_providers: AIProvider[];
    ollama_enabled: boolean;
    external_enabled: boolean;
    external_provider?: AIProvider;
    external_model?: string;
}
