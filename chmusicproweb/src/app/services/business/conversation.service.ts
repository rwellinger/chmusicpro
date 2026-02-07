import {inject, Injectable} from "@angular/core";
import {HttpClient} from "@angular/common/http";
import {Observable} from "rxjs";
import {
    Conversation,
    ConversationCreateRequest,
    ConversationDetailResponse,
    ConversationListResponse,
    OllamaChatModel,
    OllamaModel,
    SendMessageResponse
} from "../../models/conversation.model";
import {ApiConfigService} from "../config/api-config.service";
import {ModelCacheService} from "../config/model-cache.service";

@Injectable({
    providedIn: "root"
})
export class ConversationService {
    private http = inject(HttpClient);
    private apiConfig = inject(ApiConfigService);
    private modelCache = inject(ModelCacheService);

    /**
     * List all conversations for the authenticated user
     */
    public getConversations(skip: number = 0, limit: number = 20, provider?: string, archived?: boolean): Observable<ConversationListResponse> {
        return this.http.get<ConversationListResponse>(
            this.apiConfig.endpoints.conversation.list(skip, limit, provider, archived)
        );
    }

    /**
     * Get a specific conversation with its messages
     */
    public getConversation(id: string): Observable<ConversationDetailResponse> {
        return this.http.get<ConversationDetailResponse>(
            this.apiConfig.endpoints.conversation.detail(id)
        );
    }

    /**
     * Create a new conversation
     */
    public createConversation(data: ConversationCreateRequest): Observable<Conversation> {
        return this.http.post<Conversation>(
            this.apiConfig.endpoints.conversation.create,
            data
        );
    }

    /**
     * Update a conversation (title, archived)
     */
    public updateConversation(id: string, data: { title?: string; archived?: boolean }): Observable<Conversation> {
        return this.http.patch<Conversation>(
            this.apiConfig.endpoints.conversation.update(id),
            data
        );
    }

    /**
     * Archive or unarchive a conversation
     */
    public archiveConversation(id: string, archived: boolean): Observable<Conversation> {
        return this.updateConversation(id, {archived});
    }

    /**
     * Delete a conversation
     */
    public deleteConversation(id: string): Observable<{ message: string }> {
        return this.http.delete<{ message: string }>(
            this.apiConfig.endpoints.conversation.delete(id)
        );
    }

    /**
     * Send a message in a conversation and get AI response
     */
    public sendMessage(conversationId: string, content: string): Observable<SendMessageResponse> {
        return this.http.post<SendMessageResponse>(
            this.apiConfig.endpoints.conversation.sendMessage(conversationId),
            {content}
        );
    }

    /**
     * Get available Ollama models (via cache)
     */
    public getModels(): Observable<OllamaModel[]> {
        return this.modelCache.getOllamaModels();
    }

    /**
     * Get available Ollama chat models (via cache)
     * Returns models based on OLLAMA_CHAT_MODELS configuration
     */
    public getChatModels(): Observable<OllamaChatModel[]> {
        return this.modelCache.getOllamaChatModels();
    }

    /**
     * Compress conversation by archiving old messages
     */
    public compressConversation(id: string, keepRecent?: number): Observable<{
        message: string;
        archived_messages: number;
        summary_created: boolean;
        new_token_count: number;
        token_percentage: number;
    }> {
        return this.http.post<{
            message: string;
            archived_messages: number;
            summary_created: boolean;
            new_token_count: number;
            token_percentage: number;
        }>(
            this.apiConfig.endpoints.conversation.compress(id, keepRecent),
            {}
        );
    }

    /**
     * Restore archived messages (optional feature)
     */
    public restoreArchive(id: string): Observable<{
        message: string;
        restored_messages: number;
        new_token_count: number;
    }> {
        return this.http.post<{
            message: string;
            restored_messages: number;
            new_token_count: number;
        }>(
            this.apiConfig.endpoints.conversation.restoreArchive(id),
            {}
        );
    }

    /**
     * Get conversation with archived messages (for export)
     */
    public getConversationForExport(id: string): Observable<ConversationDetailResponse> {
        return this.http.get<ConversationDetailResponse>(
            this.apiConfig.endpoints.conversation.exportFull(id)
        );
    }

    // LocalStorage methods for System Context persistence
    private readonly STORAGE_KEY = "aiChatSystemContext";

    /**
     * Load saved system context from localStorage
     */
    public loadSystemContext(): string {
        return localStorage.getItem(this.STORAGE_KEY) || "";
    }

    /**
     * Save system context to localStorage
     */
    public saveSystemContext(context: string): void {
        if (context.trim()) {
            localStorage.setItem(this.STORAGE_KEY, context);
        } else {
            this.clearSystemContext();
        }
    }

    /**
     * Clear saved system context from localStorage
     */
    public clearSystemContext(): void {
        localStorage.removeItem(this.STORAGE_KEY);
    }
}
