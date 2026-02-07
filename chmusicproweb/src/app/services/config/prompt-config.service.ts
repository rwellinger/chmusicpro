import {inject, Injectable} from "@angular/core";
import {HttpClient} from "@angular/common/http";
import {map, Observable, of} from "rxjs";
import {environment} from "../../../environments/environment";

export interface PromptTemplate {
    pre_condition: string;
    post_condition: string;
    description?: string;
    version?: string;
    model?: string;
    temperature?: number;
    max_tokens?: number;
}

export type PromptCategory = Record<string, PromptTemplate>;

export type PromptTemplates = Record<string, PromptCategory>;

interface PromptTemplateResponse extends PromptTemplate {
    id: number;
    category: string;
    action: string;
    active: boolean;
    created_at: string;
    updated_at?: string;
    model?: string;
    temperature?: number;
    max_tokens?: number;
}

interface PromptTemplatesGroupedResponse {
    categories: Record<string, Record<string, PromptTemplateResponse>>;
}

@Injectable({
    providedIn: "root"
})
export class PromptConfigService {
    private readonly apiUrl = `${environment.apiUrl}/api/v1/prompts`;
    private cachedTemplates: PromptTemplates | null = null;
    private lastCacheTime: number = 0;
    private readonly cacheTimeout = 60 * 1000; // 60 seconds

    private http = inject(HttpClient);


    private isCacheValid(): boolean {
        return this.cachedTemplates !== null &&
            (Date.now() - this.lastCacheTime) < this.cacheTimeout;
    }

    private convertResponseToTemplates(response: PromptTemplatesGroupedResponse): PromptTemplates {
        const templates: PromptTemplates = {};

        for (const [category, actions] of Object.entries(response.categories)) {
            templates[category] = {};
            for (const [action, template] of Object.entries(actions)) {
                templates[category][action] = {
                    pre_condition: template.pre_condition,
                    post_condition: template.post_condition,
                    description: template.description,
                    version: template.version,
                    model: template.model,
                    temperature: template.temperature,
                    max_tokens: template.max_tokens
                };
            }
        }

        return templates;
    }

    private loadFromAPI(): Observable<PromptTemplates> {
        return this.http.get<PromptTemplatesGroupedResponse>(this.apiUrl).pipe(
            map(response => this.convertResponseToTemplates(response))
        );
    }

    getPromptTemplate(category: string, action: string): PromptTemplate | null {
        // Use cached templates if available and valid
        if (this.isCacheValid()) {
            const categoryTemplates = this.cachedTemplates![category];
            return categoryTemplates ? (categoryTemplates[action] || null) : null;
        }

        // No fallback - templates must be loaded from database
        throw new Error(`No prompt template found for ${category}/${action} - database not loaded or template missing`);
    }

    getPromptTemplateAsync(category: string, action: string): Observable<PromptTemplate | null> {
        if (this.isCacheValid()) {
            const template = this.getPromptTemplate(category, action);
            return of(template);
        }

        return this.loadFromAPI().pipe(
            map(templates => {
                this.cachedTemplates = templates;
                this.lastCacheTime = Date.now();

                const categoryTemplates = templates[category];
                return categoryTemplates ? (categoryTemplates[action] || null) : null;
            })
        );
    }

    getAllTemplates(): PromptTemplates {
        if (!this.cachedTemplates) {
            throw new Error("Prompt templates not loaded from database");
        }
        return this.cachedTemplates;
    }

    getAllTemplatesAsync(): Observable<PromptTemplates> {
        if (this.isCacheValid()) {
            return of(this.cachedTemplates!);
        }

        return this.loadFromAPI().pipe(
            map(templates => {
                this.cachedTemplates = templates;
                this.lastCacheTime = Date.now();
                return templates;
            })
        );
    }

    getCategoryTemplates(category: string): PromptCategory | null {
        const templates = this.getAllTemplates();
        const categoryTemplates = templates[category];
        if (!categoryTemplates) {
            throw new Error(`No prompt templates found for category '${category}' - check database`);
        }
        return categoryTemplates;
    }

    getCategoryTemplatesAsync(category: string): Observable<PromptCategory | null> {
        return this.getAllTemplatesAsync().pipe(
            map(templates => templates[category] || null)
        );
    }

    refreshCache(): Observable<PromptTemplates> {
        this.cachedTemplates = null;
        this.lastCacheTime = 0;
        return this.loadFromAPI().pipe(
            map(templates => {
                this.cachedTemplates = templates;
                this.lastCacheTime = Date.now();
                return templates;
            })
        );
    }
}