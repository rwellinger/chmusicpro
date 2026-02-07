import {inject, Injectable} from "@angular/core";
import {Observable} from "rxjs";
import {ClaudeModel} from "../../models/conversation.model";
import {ModelCacheService} from "../config/model-cache.service";

@Injectable({
    providedIn: "root"
})
export class ClaudeChatService {
    private modelCache = inject(ModelCacheService);

    /**
     * Get available Claude models (via cache)
     */
    public getModels(): Observable<ClaudeModel[]> {
        return this.modelCache.getClaudeModels();
    }

    // LocalStorage methods for System Context persistence
    private readonly STORAGE_KEY = "claudeChatSystemContext";

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
