import {inject, Injectable} from "@angular/core";
import {HttpClient} from "@angular/common/http";
import {Observable} from "rxjs";
import {ApiConfigService} from "../config/api-config.service";
import {Workshop, WorkshopDetailResponse, WorkshopListResponse} from "../../models/workshop.model";

@Injectable({
    providedIn: "root"
})
export class WorkshopService {
    private http = inject(HttpClient);
    private apiConfig = inject(ApiConfigService);

    createWorkshop(data: Partial<Workshop>): Observable<WorkshopDetailResponse> {
        return this.http.post<WorkshopDetailResponse>(
            this.apiConfig.endpoints.workshop.create(),
            data
        );
    }

    getWorkshops(
        limit = 20,
        offset = 0,
        search?: string,
        phase?: string
    ): Observable<WorkshopListResponse> {
        return this.http.get<WorkshopListResponse>(
            this.apiConfig.endpoints.workshop.list(limit, offset, search, phase)
        );
    }

    getWorkshopById(id: string): Observable<WorkshopDetailResponse> {
        return this.http.get<WorkshopDetailResponse>(
            this.apiConfig.endpoints.workshop.detail(id)
        );
    }

    updateWorkshop(id: string, data: Partial<Workshop>): Observable<WorkshopDetailResponse> {
        return this.http.put<WorkshopDetailResponse>(
            this.apiConfig.endpoints.workshop.update(id),
            data
        );
    }

    deleteWorkshop(id: string): Observable<{ success: boolean; message?: string }> {
        return this.http.delete<{ success: boolean; message?: string }>(
            this.apiConfig.endpoints.workshop.delete(id)
        );
    }

    exportToSketch(id: string): Observable<any> {
        return this.http.post(
            this.apiConfig.endpoints.workshop.exportToSketch(id),
            {}
        );
    }
}
