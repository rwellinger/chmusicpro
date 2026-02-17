import {inject, Injectable} from "@angular/core";
import {HttpClient} from "@angular/common/http";
import {Observable, throwError} from "rxjs";
import {catchError, map} from "rxjs/operators";
import {environment} from "../../../environments/environment";
import {
    ApiKeyStatusResponse,
    ApiKeyUpdateRequest,
    PasswordChangeRequest,
    PasswordChangeResponse,
    User,
    UserUpdateRequest,
    UserUpdateResponse
} from "../../models/user.model";
import {AuthService} from "./auth.service";

@Injectable({
    providedIn: "root"
})
export class UserService {
    private readonly baseUrl = environment.apiUrl;

    private http = inject(HttpClient);
    private authService = inject(AuthService);

    /**
     * Get user profile (uses JWT token, no userId required)
     */
    public getUserProfile(): Observable<User> {
        return this.http.get<User>(`${this.baseUrl}/api/v1/user/profile`)
            .pipe(
                map(response => response),
                catchError(this.handleError)
            );
    }

    /**
     * Update user profile (uses JWT token, no userId required)
     */
    public updateUserProfile(userData: UserUpdateRequest): Observable<User> {
        return this.http.put<UserUpdateResponse>(`${this.baseUrl}/api/v1/user/edit`, userData)
            .pipe(
                map(response => {
                    if (response.success && response.user) {
                        // Update the user in auth service
                        const currentUser = this.authService.getCurrentUser();
                        if (currentUser) {
                            const updatedUser = {...currentUser, ...userData};
                            this.authService.updateUser(updatedUser);
                        }
                        return response.user;
                    }
                    throw new Error(response.message || "Failed to update user profile");
                }),
                catchError(this.handleError)
            );
    }

    /**
     * Change user password (uses JWT token, no userId required)
     */
    public changePassword(passwordData: PasswordChangeRequest): Observable<PasswordChangeResponse> {
        return this.http.put<PasswordChangeResponse>(`${this.baseUrl}/api/v1/user/password`, passwordData)
            .pipe(
                map(response => {
                    if (response.success) {
                        return response;
                    }
                    throw new Error(response.message || "Failed to change password");
                }),
                catchError(this.handleError)
            );
    }

    /**
     * Get current user profile (alias for getUserProfile, kept for compatibility)
     */
    public getCurrentUserProfile(): Observable<User> {
        return this.getUserProfile();
    }

    /**
     * Update current user profile (alias for updateUserProfile, kept for compatibility)
     */
    public updateCurrentUserProfile(userData: UserUpdateRequest): Observable<User> {
        return this.updateUserProfile(userData);
    }

    /**
     * Change current user password (alias for changePassword, kept for compatibility)
     */
    public changeCurrentUserPassword(passwordData: PasswordChangeRequest): Observable<PasswordChangeResponse> {
        return this.changePassword(passwordData);
    }

    /**
     * Get API key configuration status
     */
    public getApiKeyStatus(): Observable<ApiKeyStatusResponse> {
        return this.http.get<ApiKeyStatusResponse>(`${this.baseUrl}/api/v1/user/api-keys/status`)
            .pipe(catchError(this.handleError));
    }

    /**
     * Update API keys (encrypted on server)
     */
    public updateApiKeys(keys: ApiKeyUpdateRequest): Observable<ApiKeyStatusResponse> {
        return this.http.put<ApiKeyStatusResponse>(`${this.baseUrl}/api/v1/user/api-keys`, keys)
            .pipe(catchError(this.handleError));
    }

    /**
     * Delete all API keys
     */
    public deleteApiKeys(): Observable<{success: boolean; message: string}> {
        return this.http.delete<{success: boolean; message: string}>(`${this.baseUrl}/api/v1/user/api-keys`)
            .pipe(catchError(this.handleError));
    }

    /**
     * Handle HTTP errors
     */
    private handleError(error: any): Observable<never> {
        console.error("UserService error:", error);

        let errorMessage = "An error occurred";

        if (error.error) {
            if (typeof error.error === "string") {
                errorMessage = error.error;
            } else if (error.error.error) {
                errorMessage = error.error.error;
            } else if (error.error.message) {
                errorMessage = error.error.message;
            }
        } else if (error.message) {
            errorMessage = error.message;
        }

        return throwError(() => new Error(errorMessage));
    }
}