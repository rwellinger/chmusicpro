/**
 * Song Release Service - Business logic for song release management.
 *
 * CRITICAL:
 * - Uses inject() NOT constructor injection
 * - Uses ApiConfigService for all endpoints (NO hardcoded URLs!)
 * - Returns RxJS Observables (lazy evaluation)
 * - Supports cover image upload (200x200 px, FormData multipart/form-data)
 */

import {inject, Injectable} from "@angular/core";
import {HttpClient} from "@angular/common/http";
import {Observable} from "rxjs";
import {ApiConfigService} from "../config/api-config.service";
import {
    SongReleaseCreateRequest,
    SongReleaseDetailResponse,
    SongReleaseListResponse,
    SongReleaseUpdateRequest
} from "../../models/song-release.model";

@Injectable({
    providedIn: "root"
})
export class SongReleaseService {
    private http = inject(HttpClient);
    private apiConfig = inject(ApiConfigService);

    /**
     * Create new song release with optional cover upload.
     *
     * @param data Release data (required fields based on status)
     * @param coverFile Optional cover image file (200x200 px)
     * @returns Observable of SongReleaseDetailResponse
     *
     * @example
     * const request: SongReleaseCreateRequest = {
     *   type: ReleaseType.SINGLE,
     *   name: 'My First Single',
     *   status: ReleaseStatus.DRAFT,
     *   genre: 'Rock',
     *   project_ids: ['project-uuid-1']
     * };
     * this.songReleaseService.createRelease(request, coverImageFile).subscribe({
     *   next: (response) => console.log('Created:', response.data.id),
     *   error: (error) => console.error('Failed:', error)
     * });
     */
    createRelease(data: SongReleaseCreateRequest, coverFile?: File): Observable<SongReleaseDetailResponse> {
        const formData = new FormData();
        formData.append("data", JSON.stringify(data));

        if (coverFile) {
            formData.append("cover", coverFile);
        }

        return this.http.post<SongReleaseDetailResponse>(
            this.apiConfig.endpoints.songRelease.create,
            formData
        );
    }

    /**
     * Get paginated release list with filters.
     *
     * @param limit Items per page (default 20)
     * @param offset Pagination offset (default 0)
     * @param statusFilter Filter by status group ('all', 'progress', 'uploaded', 'released', 'archive')
     * @param search Search term for name/genre (optional)
     * @returns Observable of SongReleaseListResponse
     *
     * @example
     * this.songReleaseService.getReleases(20, 0, 'progress', 'rock').subscribe({
     *   next: (response) => {
     *     console.log('Total:', response.total);
     *     console.log('Items:', response.items);
     *   }
     * });
     */
    getReleases(
        limit: number = 20,
        offset: number = 0,
        statusFilter?: string,
        search?: string
    ): Observable<SongReleaseListResponse> {
        return this.http.get<SongReleaseListResponse>(
            this.apiConfig.endpoints.songRelease.list(limit, offset, statusFilter, search)
        );
    }

    /**
     * Get release by ID with all details and assigned projects.
     *
     * @param id Release UUID
     * @returns Observable of SongReleaseDetailResponse (includes presigned cover URL)
     *
     * @example
     * this.songReleaseService.getReleaseById('release-uuid').subscribe({
     *   next: (response) => {
     *     console.log('Release:', response.data);
     *     console.log('Cover URL:', response.data.cover_url); // Presigned S3 URL
     *     console.log('Projects:', response.data.assigned_projects);
     *   }
     * });
     */
    getReleaseById(id: string): Observable<SongReleaseDetailResponse> {
        return this.http.get<SongReleaseDetailResponse>(
            this.apiConfig.endpoints.songRelease.detail(id)
        );
    }

    /**
     * Update release with optional cover upload and project reassignment.
     *
     * @param id Release UUID
     * @param data Fields to update (partial update)
     * @param coverFile Optional new cover image file (200x200 px, replaces existing)
     * @returns Observable of SongReleaseDetailResponse
     *
     * @example
     * this.songReleaseService.updateRelease(id, {
     *   status: ReleaseStatus.UPLOADED,
     *   upload_date: '2024-01-15'
     * }, newCoverFile).subscribe({
     *   next: () => console.log('Updated'),
     *   error: (error) => console.error('Failed:', error)
     * });
     */
    updateRelease(id: string, data: SongReleaseUpdateRequest, coverFile?: File): Observable<SongReleaseDetailResponse> {
        const formData = new FormData();
        formData.append("data", JSON.stringify(data));

        if (coverFile) {
            formData.append("cover", coverFile);
        }

        return this.http.put<SongReleaseDetailResponse>(
            this.apiConfig.endpoints.songRelease.update(id),
            formData
        );
    }

    /**
     * Delete release (cascades to project references, deletes S3 cover).
     *
     * @param id Release UUID
     * @returns Observable of { message: string }
     *
     * @example
     * this.songReleaseService.deleteRelease(id).subscribe({
     *   next: (response) => console.log(response.message),
     *   error: (error) => console.error('Failed:', error)
     * });
     */
    deleteRelease(id: string): Observable<{ message: string }> {
        return this.http.delete<{ message: string }>(
            this.apiConfig.endpoints.songRelease.delete(id)
        );
    }

    /**
     * Validate cover image dimensions (must be 200x200 px).
     *
     * @param file Image file to validate
     * @returns Promise<{ valid: boolean, error?: string }>
     *
     * @example
     * const validation = await this.songReleaseService.validateCoverImage(file);
     * if (!validation.valid) {
     *   this.notificationService.error(validation.error);
     *   return;
     * }
     */
    validateCoverImage(file: File): Promise<{ valid: boolean; error?: string }> {
        return new Promise((resolve) => {
            if (!file.type.startsWith("image/")) {
                resolve({valid: false, error: "File must be an image"});
                return;
            }

            const img = new Image();
            img.onload = () => {
                if (img.width !== 200 || img.height !== 200) {
                    resolve({
                        valid: false,
                        error: `Cover image must be 200x200 pixels, got ${img.width}x${img.height}`
                    });
                } else {
                    resolve({valid: true});
                }
            };
            img.onerror = () => {
                resolve({valid: false, error: "Failed to load image"});
            };
            img.src = URL.createObjectURL(file);
        });
    }
}
