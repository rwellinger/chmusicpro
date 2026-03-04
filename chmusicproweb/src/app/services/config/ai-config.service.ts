import {inject, Injectable} from "@angular/core";
import {HttpClient} from "@angular/common/http";
import {map, Observable, of, shareReplay, tap} from "rxjs";

import {AIConfig, AIProvider, ApplicationMode} from "../../models/ai-config.model";
import {ApiConfigService} from "./api-config.service";

@Injectable({
    providedIn: "root"
})
export class AIConfigService {
    private http = inject(HttpClient);
    private apiConfig = inject(ApiConfigService);

    private cachedConfig: AIConfig | null = null;
    private config$: Observable<AIConfig> | null = null;

    getConfig(): Observable<AIConfig> {
        if (this.cachedConfig) {
            return of(this.cachedConfig);
        }

        if (!this.config$) {
            this.config$ = this.http.get<AIConfig>(this.apiConfig.endpoints.aiConfig).pipe(
                tap(config => this.cachedConfig = config),
                shareReplay(1)
            );
        }

        return this.config$;
    }

    isOllamaEnabled(): Observable<boolean> {
        return this.getConfig().pipe(map(c => c.ollama_enabled));
    }

    isExternalEnabled(): Observable<boolean> {
        return this.getConfig().pipe(map(c => c.external_enabled));
    }

    getAvailableProviders(): Observable<AIProvider[]> {
        return this.getConfig().pipe(map(c => c.available_providers));
    }

    getApplicationMode(): Observable<ApplicationMode> {
        return this.getConfig().pipe(map(c => c.application_mode));
    }

    clearCache(): void {
        this.cachedConfig = null;
        this.config$ = null;
    }
}
