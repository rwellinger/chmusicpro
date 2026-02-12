import {inject, Injectable} from "@angular/core";
import {HttpClient} from "@angular/common/http";
import {Observable} from "rxjs";
import {ApiConfigService} from "../config/api-config.service";
import {
    DomainCreateRequest,
    DomainDetailResponse,
    DomainListResponse,
    DomainMemberAddRequest,
    DomainMemberListResponse,
    DomainMemberUpdateRequest,
    DomainSwitchRequest,
    DomainSwitchResponse,
    DomainUpdateRequest
} from "../../models/domain.model";

@Injectable({
    providedIn: "root"
})
export class DomainService {
    private http = inject(HttpClient);
    private apiConfig = inject(ApiConfigService);

    getUserDomains(): Observable<DomainListResponse> {
        return this.http.get<DomainListResponse>(this.apiConfig.endpoints.domain.list);
    }

    getDomainDetail(domainId: string): Observable<DomainDetailResponse> {
        return this.http.get<DomainDetailResponse>(this.apiConfig.endpoints.domain.detail(domainId));
    }

    switchDomain(request: DomainSwitchRequest): Observable<DomainSwitchResponse> {
        return this.http.post<DomainSwitchResponse>(this.apiConfig.endpoints.domain.switch, request);
    }

    createDomain(data: DomainCreateRequest): Observable<any> {
        return this.http.post(this.apiConfig.endpoints.domain.create, data);
    }

    updateDomain(domainId: string, data: DomainUpdateRequest): Observable<any> {
        return this.http.put(this.apiConfig.endpoints.domain.update(domainId), data);
    }

    deactivateDomain(domainId: string): Observable<any> {
        return this.http.delete(this.apiConfig.endpoints.domain.deactivate(domainId));
    }

    getDomainMembers(domainId: string): Observable<DomainMemberListResponse> {
        return this.http.get<DomainMemberListResponse>(this.apiConfig.endpoints.domain.members(domainId));
    }

    addMember(domainId: string, data: DomainMemberAddRequest): Observable<any> {
        return this.http.post(this.apiConfig.endpoints.domain.members(domainId), data);
    }

    updateMemberRole(domainId: string, userId: string, data: DomainMemberUpdateRequest): Observable<any> {
        return this.http.put(this.apiConfig.endpoints.domain.memberDetail(domainId, userId), data);
    }

    removeMember(domainId: string, userId: string): Observable<any> {
        return this.http.delete(this.apiConfig.endpoints.domain.memberDetail(domainId, userId));
    }
}
