import {inject, Injectable} from "@angular/core";
import {HttpClient, HttpErrorResponse} from "@angular/common/http";
import {BehaviorSubject, Observable, throwError} from "rxjs";
import {catchError, map, tap} from "rxjs/operators";
import {
    SystemContextTemplate,
    SystemContextTemplateCreate,
    SystemContextTemplateListResponse,
    SystemContextTemplateUpdate
} from "../../models/system-context-template.model";
import {ApiConfigService} from "./api-config.service";

@Injectable({
    providedIn: "root"
})
export class SystemContextTemplateService {
    private http = inject(HttpClient);
    private apiConfig = inject(ApiConfigService);

    private templatesCache$ = new BehaviorSubject<SystemContextTemplate[] | null>(null);
    public templates$ = this.templatesCache$.asObservable();

    getAll(forceRefresh = false): Observable<SystemContextTemplate[]> {
        if (!forceRefresh && this.templatesCache$.value) {
            return this.templates$.pipe(map(templates => templates || []));
        }

        return this.http.get<SystemContextTemplateListResponse>(
            this.apiConfig.endpoints.systemContextTemplate.list
        ).pipe(
            map(response => response.templates),
            tap(templates => this.templatesCache$.next(templates)),
            catchError(this.handleError)
        );
    }

    getActive(): Observable<SystemContextTemplate[]> {
        return this.http.get<SystemContextTemplateListResponse>(
            this.apiConfig.endpoints.systemContextTemplate.active
        ).pipe(
            map(response => response.templates),
            catchError(this.handleError)
        );
    }

    getById(id: string): Observable<SystemContextTemplate> {
        return this.http.get<SystemContextTemplate>(
            this.apiConfig.endpoints.systemContextTemplate.detail(id)
        ).pipe(catchError(this.handleError));
    }

    create(template: SystemContextTemplateCreate): Observable<SystemContextTemplate> {
        return this.http.post<SystemContextTemplate>(
            this.apiConfig.endpoints.systemContextTemplate.create,
            template
        ).pipe(
            tap(() => this.refreshCache()),
            catchError(this.handleError)
        );
    }

    update(id: string, update: SystemContextTemplateUpdate): Observable<SystemContextTemplate> {
        return this.http.put<SystemContextTemplate>(
            this.apiConfig.endpoints.systemContextTemplate.update(id),
            update
        ).pipe(
            tap(() => this.refreshCache()),
            catchError(this.handleError)
        );
    }

    delete(id: string): Observable<void> {
        return this.http.delete<void>(
            this.apiConfig.endpoints.systemContextTemplate.delete(id)
        ).pipe(
            tap(() => this.refreshCache()),
            catchError(this.handleError)
        );
    }

    refreshCache(): void {
        this.getAll(true).subscribe({
            next: () => console.log("SystemContextTemplateService cache refreshed"),
            error: (error) => console.error("Failed to refresh cache:", error)
        });
    }

    clearCache(): void {
        this.templatesCache$.next(null);
    }

    private handleError(error: HttpErrorResponse): Observable<never> {
        console.error("SystemContextTemplateService Error:", error);
        let errorMessage = "An unknown error occurred";

        if (error.error instanceof ErrorEvent) {
            errorMessage = `Client Error: ${error.error.message}`;
        } else {
            errorMessage = `Server Error: ${error.status} - ${error.message}`;
            if (error.error?.detail) {
                errorMessage += ` - ${error.error.detail}`;
            }
        }

        return throwError(() => new Error(errorMessage));
    }
}
