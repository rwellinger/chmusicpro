import {inject, Injectable} from "@angular/core";
import {Observable} from "rxjs";
import {OpenAIModel} from "../../models/conversation.model";
import {ModelCacheService} from "../config/model-cache.service";

@Injectable({
    providedIn: "root"
})
export class OpenaiChatService {
    private modelCache = inject(ModelCacheService);

    /**
     * Get available OpenAI models (via cache)
     */
    public getModels(): Observable<OpenAIModel[]> {
        return this.modelCache.getOpenAIModels();
    }

    // LocalStorage methods for System Context persistence
    private readonly STORAGE_KEY = "openaiChatSystemContext";

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
