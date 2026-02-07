import {inject, Injectable} from "@angular/core";
import {HttpClient, HttpErrorResponse} from "@angular/common/http";
import {BehaviorSubject, Observable, throwError} from "rxjs";
import {catchError, map, tap} from "rxjs/operators";
import {
    LyricParsingRule,
    LyricParsingRuleCreate,
    LyricParsingRuleListResponse,
    LyricParsingRuleReorderRequest,
    LyricParsingRuleUpdate,
    RuleType
} from "../../models/lyric-parsing-rule.model";
import {ApiConfigService} from "./api-config.service";

@Injectable({
    providedIn: "root"
})
export class LyricParsingRuleService {
    private http = inject(HttpClient);
    private apiConfig = inject(ApiConfigService);

    private rulesCache$ = new BehaviorSubject<LyricParsingRule[] | null>(null);
    public rules$ = this.rulesCache$.asObservable();

    getAllRules(ruleType?: RuleType, activeOnly?: boolean, forceRefresh = false): Observable<LyricParsingRule[]> {
        if (!forceRefresh && this.rulesCache$.value && !ruleType && !activeOnly) {
            return this.rules$.pipe(map(rules => rules || []));
        }

        return this.http.get<LyricParsingRuleListResponse>(
            this.apiConfig.endpoints.lyricParsingRule.list(ruleType, activeOnly)
        ).pipe(
            map(response => response.rules),
            tap(rules => {
                if (!ruleType && !activeOnly) {
                    this.rulesCache$.next(rules);
                }
            }),
            catchError(this.handleError)
        );
    }

    getRuleById(id: number): Observable<LyricParsingRule> {
        return this.http.get<LyricParsingRule>(
            this.apiConfig.endpoints.lyricParsingRule.detail(id)
        ).pipe(catchError(this.handleError));
    }

    createRule(rule: LyricParsingRuleCreate): Observable<LyricParsingRule> {
        return this.http.post<LyricParsingRule>(
            this.apiConfig.endpoints.lyricParsingRule.create,
            rule
        ).pipe(
            tap(() => this.refreshCache()),
            catchError(this.handleError)
        );
    }

    updateRule(id: number, update: LyricParsingRuleUpdate): Observable<LyricParsingRule> {
        return this.http.put<LyricParsingRule>(
            this.apiConfig.endpoints.lyricParsingRule.update(id),
            update
        ).pipe(
            tap(() => this.refreshCache()),
            catchError(this.handleError)
        );
    }

    deleteRule(id: number): Observable<void> {
        return this.http.delete<void>(
            this.apiConfig.endpoints.lyricParsingRule.delete(id)
        ).pipe(
            tap(() => this.refreshCache()),
            catchError(this.handleError)
        );
    }

    reorderRules(ruleIds: number[]): Observable<LyricParsingRule[]> {
        const request: LyricParsingRuleReorderRequest = {rule_ids: ruleIds};
        return this.http.patch<LyricParsingRuleListResponse>(
            this.apiConfig.endpoints.lyricParsingRule.reorder,
            request
        ).pipe(
            map(response => response.rules),
            tap(rules => this.rulesCache$.next(rules)),
            catchError(this.handleError)
        );
    }

    refreshCache(): void {
        this.getAllRules(undefined, undefined, true).subscribe({
            next: () => console.log("LyricParsingRuleService cache refreshed"),
            error: (error) => console.error("Failed to refresh cache:", error)
        });
    }

    clearCache(): void {
        this.rulesCache$.next(null);
    }

    private handleError(error: HttpErrorResponse): Observable<never> {
        console.error("LyricParsingRuleService Error:", error);
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
