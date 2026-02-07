import {inject, Injectable} from "@angular/core";
import {HttpClient} from "@angular/common/http";
import {Observable} from "rxjs";
import {ApiConfigService} from "./api-config.service";

export interface MonthlyCosts {
    year: number;
    month: number;
    total: number;
    image: number;
    chat: number;
    currency: string;
    organization_id?: string;
    breakdown?: Record<string, number>;
    bucket_count?: number;
}

export interface CostResponse {
    status: string;
    costs: MonthlyCosts;
    cached?: boolean;
}

@Injectable({
    providedIn: "root"
})
export class CostService {
    private http = inject(HttpClient);
    private apiConfig = inject(ApiConfigService);

    getCurrentMonthCosts(): Observable<CostResponse> {
        return this.http.get<CostResponse>(
            this.apiConfig.endpoints.costs.openaiCurrent
        );
    }

    getMonthCosts(year: number, month: number): Observable<CostResponse> {
        return this.http.get<CostResponse>(
            this.apiConfig.endpoints.costs.openaiMonth(year, month)
        );
    }

    getAllTimeCosts(): Observable<CostResponse> {
        return this.http.get<CostResponse>(
            this.apiConfig.endpoints.costs.openaiAllTime
        );
    }
}
