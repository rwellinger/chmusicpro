import {inject, Injectable} from "@angular/core";
import {HttpClient, HttpErrorResponse} from "@angular/common/http";
import {firstValueFrom, Observable, throwError} from "rxjs";
import {catchError, map, tap} from "rxjs/operators";
import {
    PromptCategoryResponse,
    PromptTemplate,
    PromptTemplatesResponse,
    PromptTemplateUpdate
} from "../../models/prompt-template.model";
import {ApiConfigService} from "./api-config.service";
import {PromptConfigService} from "./prompt-config.service";

@Injectable({
    providedIn: "root"
})
export class PromptTemplateService {
    private http = inject(HttpClient);
    private apiConfig = inject(ApiConfigService);
    private promptConfig = inject(PromptConfigService);

    getAllTemplates(): Observable<PromptTemplate[]> {
        return this.http.get<PromptTemplatesResponse>(this.apiConfig.endpoints.prompt.list)
            .pipe(
                map(response => {
                    const templates: PromptTemplate[] = [];
                    Object.values(response.categories).forEach(category => {
                        Object.values(category).forEach(template => {
                            templates.push(template);
                        });
                    });
                    return templates.sort((a, b) => a.category.localeCompare(b.category) || a.action.localeCompare(b.action));
                }),
                catchError(this.handleError)
            );
    }

    getCategoryTemplates(category: string): Observable<PromptTemplate[]> {
        return this.http.get<PromptCategoryResponse>(this.apiConfig.endpoints.prompt.category(category))
            .pipe(
                map(response => Object.values(response.templates)),
                catchError(this.handleError)
            );
    }

    getTemplate(category: string, action: string): Observable<PromptTemplate> {
        return this.http.get<PromptTemplate>(this.apiConfig.endpoints.prompt.specific(category, action))
            .pipe(catchError(this.handleError));
    }

    updateTemplate(category: string, action: string, update: PromptTemplateUpdate): Observable<PromptTemplate> {
        return this.http.put<PromptTemplate>(
            this.apiConfig.endpoints.prompt.update(category, action),
            update
        ).pipe(
            tap(() => {
                // Auto-refresh PromptConfigService cache after successful template update
                this.promptConfig.refreshCache().subscribe({
                    next: () => console.log("PromptConfigService cache refreshed successfully"),
                    error: (error) => console.error("Failed to refresh PromptConfigService cache:", error)
                });
            }),
            catchError(this.handleError)
        );
    }

    async updateTemplateAsync(category: string, action: string, update: PromptTemplateUpdate): Promise<PromptTemplate> {
        const result = await firstValueFrom(
            this.http.put<PromptTemplate>(this.apiConfig.endpoints.prompt.update(category, action), update)
                .pipe(catchError(this.handleError))
        );

        // Auto-refresh PromptConfigService cache after successful template update
        try {
            await firstValueFrom(this.promptConfig.refreshCache());
        } catch (error) {
            console.error("Failed to refresh PromptConfigService cache:", error);
        }

        return result;
    }

    private handleError(error: HttpErrorResponse): Observable<never> {
        console.error("PromptTemplateService Error:", error);
        let errorMessage = "An unknown error occurred";

        if (error.error instanceof ErrorEvent) {
            errorMessage = `Client Error: ${error.error.message}`;
        } else {
            errorMessage = `Server Error: ${error.status} - ${error.message}`;
        }

        return throwError(() => new Error(errorMessage));
    }
}