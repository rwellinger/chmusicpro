/**
 * Song Project Service - Business logic for song project management.
 *
 * CRITICAL:
 * - Uses inject() NOT constructor injection
 * - Uses ApiConfigService for all endpoints (NO hardcoded URLs!)
 * - Returns RxJS Observables (lazy evaluation)
 */

import {inject, Injectable} from "@angular/core";
import {HttpClient} from "@angular/common/http";
import {Observable} from "rxjs";
import {ApiConfigService} from "../config/api-config.service";
import {
    SongProjectCreateRequest,
    SongProjectDetailResponse,
    SongProjectListResponse,
    SongProjectUpdateRequest
} from "../../models/song-project.model";

@Injectable({
    providedIn: "root"
})
export class SongProjectService {
    private http = inject(HttpClient);
    private apiConfig = inject(ApiConfigService);

    /**
     * Create new song project.
     *
     * @param data Project data (project_name, optional tags)
     * @returns Observable of SongProjectDetailResponse
     *
     * @example
     * this.songProjectService.createProject({
     *   project_name: 'Summer Vibes 2024',
     *   tags: ['pop', 'summer']
     * }).subscribe({
     *   next: (response) => console.log('Created:', response.data.id),
     *   error: (error) => console.error('Failed:', error)
     * });
     */
    createProject(data: SongProjectCreateRequest): Observable<SongProjectDetailResponse> {
        return this.http.post<SongProjectDetailResponse>(
            this.apiConfig.endpoints.songProject.create,
            data
        );
    }

    /**
     * Get paginated song projects list with filters.
     *
     * @param limit Items per page (default 20)
     * @param offset Pagination offset (default 0)
     * @param search Search term for project_name (optional)
     * @param tags Comma-separated tags filter (optional)
     * @param projectStatus Status filter ('new', 'progress', 'archived', or undefined for all non-archived)
     * @returns Observable of SongProjectListResponse
     *
     * @example
     * this.songProjectService.getProjects(20, 0, 'Summer', 'pop,rock', 'new')
     *   .subscribe(response => {
     *     console.log('Total:', response.pagination.total);
     *     console.log('Items:', response.data);
     *   });
     */
    getProjects(
        limit: number = 20,
        offset: number = 0,
        search?: string,
        tags?: string,
        projectStatus?: string
    ): Observable<SongProjectListResponse> {
        return this.http.get<SongProjectListResponse>(
            this.apiConfig.endpoints.songProject.list(limit, offset, search, tags, projectStatus)
        );
    }

    /**
     * Get song project by ID (with folders and files).
     *
     * @param id Project UUID
     * @returns Observable of SongProjectDetailResponse (with folders and files)
     *
     * @example
     * this.songProjectService.getProjectById('123e4567-e89b-12d3-a456-426614174000')
     *   .subscribe(response => {
     *     console.log('Project:', response.data);
     *     console.log('Folders:', response.data.folders);
     *   });
     */
    getProjectById(id: string): Observable<SongProjectDetailResponse> {
        return this.http.get<SongProjectDetailResponse>(
            this.apiConfig.endpoints.songProject.detail(id)
        );
    }

    /**
     * Update song project (partial update).
     *
     * @param id Project UUID
     * @param data Fields to update (project_name, tags, sync_status)
     * @returns Observable of SongProjectDetailResponse
     *
     * @example
     * this.songProjectService.updateProject(id, {
     *   project_name: 'Summer Vibes 2024 (Final)',
     *   tags: ['pop', 'summer', 'released']
     * }).subscribe({
     *   next: () => console.log('Updated'),
     *   error: (error) => console.error('Failed:', error)
     * });
     */
    updateProject(id: string, data: SongProjectUpdateRequest): Observable<SongProjectDetailResponse> {
        return this.http.put<SongProjectDetailResponse>(
            this.apiConfig.endpoints.songProject.update(id),
            data
        );
    }

    /**
     * Delete song project (including S3 files).
     *
     * @param id Project UUID
     * @returns Observable of { message: string }
     *
     * @example
     * this.songProjectService.deleteProject(id).subscribe({
     *   next: (response) => console.log(response.message),
     *   error: (error) => console.error('Failed:', error)
     * });
     */
    deleteProject(id: string): Observable<{ message: string }> {
        return this.http.delete<{ message: string }>(
            this.apiConfig.endpoints.songProject.delete(id)
        );
    }

    /**
     * Upload file to song project folder.
     *
     * @param projectId Project UUID
     * @param file File to upload
     * @param folderId Folder UUID
     * @returns Observable of upload response
     *
     * @example
     * const formData = new FormData();
     * formData.append('file', file);
     * formData.append('folder_id', folderId);
     *
     * this.songProjectService.uploadFile(projectId, formData).subscribe({
     *   next: (response) => console.log('Uploaded:', response),
     *   error: (error) => console.error('Failed:', error)
     * });
     */
    uploadFile(projectId: string, formData: FormData): Observable<{ message: string; file_id: string }> {
        return this.http.post<{ message: string; file_id: string }>(
            this.apiConfig.endpoints.songProject.uploadFile(projectId),
            formData
        );
    }

    /**
     * Clear all files in a folder (Bereinigung).
     *
     * @param projectId Project UUID
     * @param folderId Folder UUID
     * @returns Observable of clear result
     *
     * @example
     * this.songProjectService.clearFolder(projectId, folderId).subscribe({
     *   next: (result) => console.log(`${result.deleted} files deleted`),
     *   error: (error) => console.error('Failed:', error)
     * });
     */
    clearFolder(projectId: string, folderId: string): Observable<{ data: { deleted: number; errors: unknown[] } }> {
        return this.http.delete<{ data: { deleted: number; errors: unknown[] } }>(
            this.apiConfig.endpoints.songProject.clearFolder(projectId, folderId)
        );
    }
}
