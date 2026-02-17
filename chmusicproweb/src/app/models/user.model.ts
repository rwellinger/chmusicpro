/**
 * User-related interfaces and models for authentication
 */

export interface User {
    id: string;
    email: string;
    first_name?: string;
    last_name?: string;
    artist_name?: string;
    preferred_language?: string;
    is_active: boolean;
    is_verified: boolean;
    created_at: string;
    updated_at?: string;
    last_login?: string;
}

export interface LoginRequest {
    email: string;
    password: string;
}

export interface LoginResponse {
    success: boolean;
    message?: string;
    token: string;
    user: User;
    expires_at: string;
}

export interface UserCreateRequest {
    email: string;
    password: string;
    first_name?: string;
    last_name?: string;
    artist_name?: string;
    preferred_language?: string;
    captcha_token?: string;
    captcha_answer?: string;
    invite_code?: string;
}

export interface UserCreateResponse {
    success: boolean;
    message?: string;
    token: string;
    user: User;
    expires_at: string;
}

export interface UserUpdateRequest {
    first_name?: string;
    last_name?: string;
    artist_name?: string;
}

export interface UserUpdateResponse {
    success: boolean;
    message?: string;
    user: User;
}

export interface PasswordChangeRequest {
    old_password: string;
    new_password: string;
}

export interface PasswordChangeResponse {
    success: boolean;
    message?: string;
}

export interface LogoutResponse {
    success: boolean;
    message?: string;
}

export interface ApiResponse<T> {
    success: boolean;
    message?: string;
    data?: T;
    error?: string;
}

export interface AuthState {
    isAuthenticated: boolean;
    user: User | null;
    token: string | null;
    loading: boolean;
    error: string | null;
    lastValidated: number | null; // Timestamp of last token validation
    activeDomainId: string | null; // From JWT claim
    activeDomainName: string | null; // From JWT claim
    domainRole: string | null; // From JWT claim: "owner" | "admin" | "member" | "viewer"
    isSystemAdmin: boolean; // From JWT claim: admin/owner in System domain
}