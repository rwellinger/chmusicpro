import {inject, Injectable} from "@angular/core";
import {HttpClient} from "@angular/common/http";
import {firstValueFrom, Observable} from "rxjs";
import {ApiConfigService} from "../config/api-config.service";
import {SunoTemplate, SunoTemplateDetailResponse, SunoTemplateListResponse} from "../../models/suno-template.model";

@Injectable({
    providedIn: "root"
})
export class SunoTemplateService {
    private http = inject(HttpClient);
    private apiConfig = inject(ApiConfigService);

    createTemplate(data: Partial<SunoTemplate>): Observable<SunoTemplateDetailResponse> {
        return this.http.post<SunoTemplateDetailResponse>(
            this.apiConfig.endpoints.sunoTemplate.create(),
            data
        );
    }

    getTemplates(
        limit = 20,
        offset = 0,
        search?: string,
        templateType?: string
    ): Observable<SunoTemplateListResponse> {
        return this.http.get<SunoTemplateListResponse>(
            this.apiConfig.endpoints.sunoTemplate.list(limit, offset, search, templateType)
        );
    }

    getTemplateById(id: string): Observable<SunoTemplateDetailResponse> {
        return this.http.get<SunoTemplateDetailResponse>(
            this.apiConfig.endpoints.sunoTemplate.detail(id)
        );
    }

    updateTemplate(id: string, data: Partial<SunoTemplate>): Observable<SunoTemplateDetailResponse> {
        return this.http.put<SunoTemplateDetailResponse>(
            this.apiConfig.endpoints.sunoTemplate.update(id),
            data
        );
    }

    deleteTemplate(id: string): Observable<{ success: boolean; message?: string }> {
        return this.http.delete<{ success: boolean; message?: string }>(
            this.apiConfig.endpoints.sunoTemplate.delete(id)
        );
    }

    createFromSketch(sketchId: string): Observable<SunoTemplateDetailResponse> {
        return this.http.post<SunoTemplateDetailResponse>(
            this.apiConfig.endpoints.sunoTemplate.createFromSketch(sketchId),
            {}
        );
    }

    async assignToProject(templateId: string, projectId: string): Promise<any> {
        const body: any = {
            project_id: projectId
        };
        return firstValueFrom(
            this.http.post(this.apiConfig.endpoints.sunoTemplate.assignToProject(templateId), body)
        );
    }

    async unassignFromProject(templateId: string): Promise<any> {
        return firstValueFrom(
            this.http.delete(this.apiConfig.endpoints.sunoTemplate.unassignFromProject(templateId))
        );
    }
}
