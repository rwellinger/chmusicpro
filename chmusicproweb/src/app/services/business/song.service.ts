import {inject, Injectable} from "@angular/core";
import {HttpClient} from "@angular/common/http";
import {ApiConfigService} from "../config/api-config.service";
import {catchError, firstValueFrom, throwError, timeout} from "rxjs";


interface SongFormData extends Record<string, unknown> {
    lyrics?: string;
    prompt?: string;
    model?: string;
    title?: string;
    isInstrumental?: boolean;
}

/**
 * Context for form data storage
 * - 'sketch-creator': Form data for sketch creation page
 */
export type FormDataContext = "song-generator" | "sketch-creator";

interface SongsResponse {
    songs: unknown[];
    pagination?: {
        total: number;
        limit: number;
        offset: number;
        has_more: boolean;
    };
    total: number;
    limit: number;
    offset: number;
    has_more: boolean;
}

interface SongDetailResponse extends Record<string, unknown> {
    song_id: string;
    lyrics: string;
    prompt: string;
    model: string;
    status: string;
    audio_url?: string;
    created_at: string;
}

@Injectable({
    providedIn: "root"
})
export class SongService {
    private http = inject(HttpClient);
    private apiConfig = inject(ApiConfigService);

    private async httpWithTimeout<T>(method: "GET" | "POST" | "PUT", url: string, body?: any, timeoutMs: number = 30000): Promise<T> {
        const request$ = method === "GET"
            ? this.http.get<T>(url)
            : method === "POST"
                ? this.http.post<T>(url, body)
                : this.http.put<T>(url, body);

        return firstValueFrom(
            request$.pipe(
                timeout(timeoutMs),
                catchError((error: any) => {
                    if (error.name === "TimeoutError") {
                        return throwError(() => new Error("Request timed out"));
                    }
                    return throwError(() => error);
                })
            )
        );
    }

    /**
     * Load form data from localStorage with context-aware key
     * @param context - Context for storage (default: 'song-generator')
     * @returns Form data object or empty object if not found
     */
    loadFormData(context: FormDataContext = "song-generator"): SongFormData {
        const key = `${context}-form-data`;
        const raw = localStorage.getItem(key);
        return raw ? JSON.parse(raw) : {};
    }

    /**
     * Save form data to localStorage with context-aware key
     * @param data - Form data to save
     * @param context - Context for storage (default: 'song-generator')
     */
    saveFormData(data: SongFormData, context: FormDataContext = "song-generator"): void {
        const key = `${context}-form-data`;
        localStorage.setItem(key, JSON.stringify(data));
    }

    /**
     * Clear form data from localStorage with context-aware key
     * @param context - Context for storage (default: 'song-generator')
     */
    clearFormData(context: FormDataContext = "song-generator"): void {
        const key = `${context}-form-data`;
        localStorage.removeItem(key);
    }

    async getSongs(limit: number = 20, offset: number = 0, status?: string, search: string = "",
                   sort_by: string = "created_at", sort_direction: string = "desc", workflow?: string): Promise<SongsResponse> {
        // Build URL with parameters
        const url = new URL(this.apiConfig.endpoints.song.list(limit, offset, status).split("?")[0], window.location.origin);
        url.searchParams.set("limit", limit.toString());
        url.searchParams.set("offset", offset.toString());
        url.searchParams.set("sort_by", sort_by);
        url.searchParams.set("sort_direction", sort_direction);

        if (status) {
            url.searchParams.set("status", status);
        }
        if (search.trim()) {
            url.searchParams.set("search", search.trim());
        }
        if (workflow) {
            url.searchParams.set("workflow", workflow);
        }

        return this.httpWithTimeout<SongsResponse>("GET", url.toString(), undefined, 30000);
    }

    async getSongById(songId: string): Promise<SongDetailResponse> {
        return this.httpWithTimeout<SongDetailResponse>("GET", this.apiConfig.endpoints.song.detail(songId), undefined, 30000);
    }

    async updateChoiceRating(choiceId: string, rating: number | null): Promise<any> {
        return this.httpWithTimeout<any>("PUT", this.apiConfig.endpoints.song.updateChoiceRating(choiceId), {rating}, 30000);
    }

    async assignToProject(songId: string, projectId: string, projectFolderId?: string): Promise<any> {
        const body: any = {
            project_id: projectId,
            folder_id: projectFolderId || null
        };
        return this.httpWithTimeout<any>("POST", this.apiConfig.endpoints.song.assignToProject(songId), body, 30000);
    }

    async unassignFromProject(songId: string): Promise<any> {
        return firstValueFrom(
            this.http.delete(this.apiConfig.endpoints.song.unassignFromProject(songId))
        );
    }
}
