import {inject, Injectable} from "@angular/core";
import {HttpClient} from "@angular/common/http";
import {Observable, of} from "rxjs";
import {catchError, map, timeout} from "rxjs/operators";
import {ApiConfigService} from "./api-config.service";

export interface HealthCheckResponse {
    status: "healthy" | "unhealthy";
    message: string;
}

/**
 * Health Service - System health monitoring
 *
 * CRITICAL: Pre-flight checks for expensive operations (Song/Image generation)
 * Prevents:
 * - Lost API credits when storage is unavailable
 * - User frustration (content generated but not saved)
 * - Data loss when MinIO is down (e.g., NAS auto-shutdown at 23:30)
 */
@Injectable({
    providedIn: "root"
})
export class HealthService {
    private http = inject(HttpClient);
    private apiConfig = inject(ApiConfigService);

    /**
     * Check if S3 storage backend (MinIO) is reachable
     *
     * Use BEFORE expensive operations:
     * - Song generation (Mureka AI credits)
     * - Image generation (OpenAI/DALL-E credits)
     * - Large file uploads
     *
     * @param timeoutMs Request timeout in milliseconds (default: 5000ms)
     * @returns Observable<boolean> - true if storage is healthy, false otherwise
     *
     * @example
     * ```typescript
     * this.healthService.checkStorage().subscribe({
     *   next: (isHealthy) => {
     *     if (!isHealthy) {
     *       this.snackBar.open('⚠️ Storage unavailable. Try again later.', 'OK');
     *       return;
     *     }
     *     // Proceed with generation
     *     this.generateSong();
     *   }
     * });
     * ```
     */
    checkStorage(timeoutMs: number = 5000): Observable<boolean> {
        const url = `${this.apiConfig["baseUrl"]}/api/v1/health/storage`;

        return this.http.get<HealthCheckResponse>(url).pipe(
            timeout(timeoutMs),
            map(response => response.status === "healthy"),
            catchError(error => {
                // Backend returned 503 or network error
                console.warn("[HealthService] Storage health check failed:", error);
                return of(false);
            })
        );
    }

    /**
     * Check storage health and return detailed response
     *
     * @param timeoutMs Request timeout in milliseconds (default: 5000ms)
     * @returns Observable with detailed health status
     */
    checkStorageDetailed(timeoutMs: number = 5000): Observable<HealthCheckResponse | null> {
        const url = `${this.apiConfig["baseUrl"]}/api/v1/health/storage`;

        return this.http.get<HealthCheckResponse>(url).pipe(
            timeout(timeoutMs),
            catchError(error => {
                console.warn("[HealthService] Storage health check failed:", error);
                // Return unhealthy status on error
                return of({
                    status: "unhealthy" as const,
                    message: error.status === 503
                        ? error.error?.message || "Storage backend unavailable"
                        : "Health check failed: Network error"
                });
            })
        );
    }
}
