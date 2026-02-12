export interface Domain {
    id: string;
    type: number;
    name: string;
    description: string | null;
    is_active: boolean;
    created_at: string;
    updated_at: string | null;
}

export interface DomainWithRole {
    domain: Domain;
    role: string;
    is_default: boolean;
}

export interface DomainListResponse {
    success: boolean;
    domains: DomainWithRole[];
}

export interface DomainDetailResponse {
    data: DomainWithRole;
}

export interface DomainSwitchRequest {
    domain_id: string;
}

export interface DomainSwitchResponse {
    success: boolean;
    token: string;
    domain: DomainWithRole;
    expires_at: string;
}

export interface DomainCreateRequest {
    type: number;
    name: string;
    description?: string;
}

export interface DomainUpdateRequest {
    name?: string;
    description?: string;
}

export interface DomainMember {
    membership_id: string;
    user_id: string;
    email: string;
    first_name: string | null;
    last_name: string | null;
    role: string;
    is_default: boolean;
    created_at: string;
}

export interface DomainMemberListResponse {
    success: boolean;
    members: DomainMember[];
}

export interface DomainMemberAddRequest {
    email: string;
    role: string;
}

export interface DomainMemberUpdateRequest {
    role: string;
}

export enum DomainType {
    SYSTEM = 0,
    KI_TEMPLATES = 1,
    USER = 2,
    COMPANY = 3,
    PRODUCER = 4
}

export const DomainTypeLabels: Record<number, string> = {
    [DomainType.SYSTEM]: "System",
    [DomainType.KI_TEMPLATES]: "KI Templates",
    [DomainType.USER]: "Personal",
    [DomainType.COMPANY]: "Company",
    [DomainType.PRODUCER]: "Producer"
};

export const DomainRoles = ["owner", "admin", "member", "viewer"] as const;
export type DomainRole = typeof DomainRoles[number];
