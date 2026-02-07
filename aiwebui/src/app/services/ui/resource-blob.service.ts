import {inject, Injectable} from "@angular/core";
import {HttpClient} from "@angular/common/http";
import {catchError, map, Observable, of, shareReplay} from "rxjs";
import {ApiConfigService} from "../config/api-config.service";

/**
 * Generic service for loading resources (images, audio, etc.) with JWT authentication.
 *
 * Browser elements like <img>, <audio>, and window.open() cannot send JWT headers.
 * This service downloads resources via HttpClient (with auth headers) and creates
 * blob URLs that the browser can use.
 */
@Injectable({
    providedIn: "root"
})
export class ResourceBlobService {
    private http = inject(HttpClient);
    private apiConfig = inject(ApiConfigService);
    private blobCache = new Map<string, Observable<string>>();

    /**
     * Get blob URL for any resource with authentication headers.
     * Use this for <img> src, <audio> src, etc.
     */
    getResourceBlobUrl(resourceUrl: string): Observable<string> {
        if (!resourceUrl) {
            return of("");
        }

        // Check cache first
        if (this.blobCache.has(resourceUrl)) {
            return this.blobCache.get(resourceUrl)!;
        }

        // Build absolute URL if resourceUrl is relative
        const absoluteUrl = resourceUrl.startsWith("http")
            ? resourceUrl
            : `${this.apiConfig.getBaseUrl()}${resourceUrl}`;

        // Create observable for authenticated resource fetch
        const blobUrl$ = this.http.get(absoluteUrl, {
            responseType: "blob",
            // HttpClient will automatically add auth headers via interceptor
        }).pipe(
            map((blob: Blob) => {
                // Create blob URL for display/playback
                return URL.createObjectURL(blob);
            }),
            catchError(error => {
                console.error("Failed to load resource:", resourceUrl, error);
                // Return empty string on error
                return of("");
            }),
            shareReplay(1) // Cache the result
        );

        // Cache the observable
        this.blobCache.set(resourceUrl, blobUrl$);
        return blobUrl$;
    }

    /**
     * Download resource with authentication.
     * Triggers browser download dialog.
     */
    downloadResource(resourceUrl: string, filename?: string): void {
        if (!resourceUrl) return;

        // Build absolute URL if resourceUrl is relative
        const absoluteUrl = resourceUrl.startsWith("http")
            ? resourceUrl
            : `${this.apiConfig.getBaseUrl()}${resourceUrl}`;

        this.http.get(absoluteUrl, {
            responseType: "blob"
        }).subscribe({
            next: (blob: Blob) => {
                // Create download link
                const url = URL.createObjectURL(blob);
                const link = document.createElement("a");
                link.href = url;
                link.download = filename || this.extractFilename(resourceUrl);

                // Trigger download
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);

                // Cleanup
                URL.revokeObjectURL(url);
            },
            error: (error) => {
                console.error("Failed to download resource:", error);
            }
        });
    }

    /**
     * Clear blob cache for memory management
     */
    clearCache(): void {
        // Revoke all blob URLs to free memory
        this.blobCache.forEach(obs => {
            obs.subscribe(url => {
                if (url) {
                    URL.revokeObjectURL(url);
                }
            });
        });
        this.blobCache.clear();
    }

    /**
     * Remove specific resource from cache
     */
    clearResourceFromCache(resourceUrl: string): void {
        const obs = this.blobCache.get(resourceUrl);
        if (obs) {
            obs.subscribe(url => {
                if (url) {
                    URL.revokeObjectURL(url);
                }
            });
            this.blobCache.delete(resourceUrl);
        }
    }

    private extractFilename(url: string): string {
        try {
            const pathname = new URL(url).pathname;
            return pathname.split("/").pop() || "download";
        } catch {
            return "download";
        }
    }
}
