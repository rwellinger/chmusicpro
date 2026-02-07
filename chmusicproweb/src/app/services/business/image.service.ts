import {inject, Injectable} from "@angular/core";
import {HttpClient} from "@angular/common/http";
import {DEFAULT_STYLE_PREFERENCES, StylePreferences} from "../../models/image-generation.model";
import {ApiConfigService} from "../config/api-config.service";
import {firstValueFrom} from "rxjs";

interface ImageFormData extends Record<string, unknown> {
    prompt?: string;
    size?: string;
}

@Injectable({
    providedIn: "root",
})
export class ImageService {
    private http = inject(HttpClient);
    private apiConfig = inject(ApiConfigService);

    private readonly STORAGE_KEY = "imageFormData";
    private readonly STYLE_PREFERENCES_KEY = "imageStylePreferences";

    loadFormData(): ImageFormData {
        const raw = localStorage.getItem(this.STORAGE_KEY);
        return raw ? JSON.parse(raw) : {};
    }

    saveFormData(data: ImageFormData): void {
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(data));
    }

    clearFormData(): void {
        localStorage.removeItem(this.STORAGE_KEY);
    }

    /**
     * Load style preferences from LocalStorage
     * Returns default values if not found
     */
    loadStylePreferences(): StylePreferences {
        const raw = localStorage.getItem(this.STYLE_PREFERENCES_KEY);
        if (!raw) {
            return {...DEFAULT_STYLE_PREFERENCES};
        }

        try {
            return JSON.parse(raw);
        } catch {
            return {...DEFAULT_STYLE_PREFERENCES};
        }
    }

    /**
     * Save style preferences to LocalStorage
     */
    saveStylePreferences(preferences: StylePreferences): void {
        localStorage.setItem(this.STYLE_PREFERENCES_KEY, JSON.stringify(preferences));
    }

    /**
     * Clear style preferences from LocalStorage
     * Returns to default values
     */
    clearStylePreferences(): void {
        localStorage.removeItem(this.STYLE_PREFERENCES_KEY);
    }

    /**
     * Assign an image to a project (with optional folder)
     */
    async assignToProject(imageId: string, projectId: string, projectFolderId?: string): Promise<any> {
        const body: any = {
            project_id: projectId,
            folder_id: projectFolderId || null
        };
        return firstValueFrom(
            this.http.post(this.apiConfig.endpoints.image.assignToProject(imageId), body)
        );
    }

    async getProjectsForImage(imageId: string): Promise<{ project_id: string; project_name: string }[]> {
        interface ProjectResponse {
            projects: { project_id: string; project_name: string }[];
        }

        const response = await firstValueFrom(
            this.http.get<ProjectResponse>(
                this.apiConfig.endpoints.image.getProjects(imageId)
            )
        );
        return response.projects;
    }

    /**
     * Unassign an image from a project (link only, image remains)
     */
    async unassignFromProject(imageId: string, projectId: string): Promise<any> {
        return firstValueFrom(
            this.http.delete(this.apiConfig.endpoints.image.unassignFromProject(imageId, projectId))
        );
    }
}