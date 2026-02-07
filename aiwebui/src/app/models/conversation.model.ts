/**
 * Conversation and Message models for AI Chat
 */

export interface Conversation {
    id: string;
    user_id: string;
    title: string;
    model: string;
    provider?: "internal" | "external";
    external_provider?: "openai" | "claude";
    system_context?: string;
    archived?: boolean;
    context_window_size?: number;
    current_token_count?: number;
    has_archived_messages?: boolean;
    created_at: string;
    updated_at?: string;
    message_count?: number;
}

export interface Message {
    id: string;
    conversation_id: string;
    role: "user" | "assistant" | "system";
    content: string;
    token_count?: number;
    created_at: string;
}

export interface OllamaModel {
    name: string;
    model: string;
    size: number;
    modified_at: string;
    details: {
        parameter_size: string;
        quantization_level: string;
        family: string;
    };
}

export interface OllamaChatModel {
    name: string;
    context_window: number;
    is_default: boolean;
}

export interface ConversationListResponse {
    conversations: Conversation[];
    total: number;
    skip: number;
    limit: number;
}

export interface ConversationDetailResponse {
    conversation: Conversation;
    messages: Message[];
}

export interface SendMessageResponse {
    user_message: Message;
    assistant_message: Message;
    conversation: Conversation;
}

export interface ConversationCreateRequest {
    title: string;
    model: string;
    provider?: "internal" | "external";
    external_provider?: "openai" | "claude";
    system_context?: string;
}

export interface OpenAIModel {
    name: string;
    context_window: number;
}

export interface ClaudeModel {
    name: string;
    context_window: number;
}
