import {inject, Injectable} from "@angular/core";
import {HttpClient} from "@angular/common/http";
import {Observable} from "rxjs";
import {ApiConfigService} from "../config/api-config.service";
import {
    ModelContextWindow,
    ModelContextWindowCreate,
    ModelContextWindowUpdate
} from "../../models/model-context-window.model";

interface ModelContextWindowListResponse {
    items: ModelContextWindow[];
    total: number;
}

@Injectable({
    providedIn: "root"
})
export class ModelContextWindowService {
    private http = inject(HttpClient);
    private apiConfig = inject(ApiConfigService);

    list(): Observable<ModelContextWindowListResponse> {
        return this.http.get<ModelContextWindowListResponse>(this.apiConfig.endpoints.modelContextWindow.list);
    }

    create(data: ModelContextWindowCreate): Observable<ModelContextWindow> {
        return this.http.post<ModelContextWindow>(this.apiConfig.endpoints.modelContextWindow.create, data);
    }

    update(id: number, data: ModelContextWindowUpdate): Observable<ModelContextWindow> {
        return this.http.put<ModelContextWindow>(this.apiConfig.endpoints.modelContextWindow.update(id), data);
    }

    delete(id: number): Observable<void> {
        return this.http.delete<void>(this.apiConfig.endpoints.modelContextWindow.delete(id));
    }
}
