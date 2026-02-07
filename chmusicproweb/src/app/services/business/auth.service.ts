import {inject, Injectable} from "@angular/core";
import {HttpClient, HttpHeaders} from "@angular/common/http";
import {BehaviorSubject, Observable, throwError} from "rxjs";
import {catchError, map, tap} from "rxjs/operators";
import {CookieService} from "ngx-cookie-service";
import {environment} from "../../../environments/environment";
import {
    AuthState,
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    User,
    UserCreateRequest,
    UserCreateResponse
} from "../../models/user.model";

@Injectable({
    providedIn: "root"
})
export class AuthService {
    private readonly baseUrl = environment.apiUrl;
    private readonly tokenKey = "auth_token";
    private readonly userKey = "auth_user";

    private authStateSubject = new BehaviorSubject<AuthState>({
        isAuthenticated: false,
        user: null,
        token: null,
        loading: false,
        error: null,
        lastValidated: null
    });

    // Token validation cache duration (5 minutes)
    private readonly TOKEN_VALIDATION_CACHE_MS = 5 * 60 * 1000;

    public authState$ = this.authStateSubject.asObservable();

    private http = inject(HttpClient);
    private cookieService = inject(CookieService);

    constructor() {
        this.initializeAuthState();
    }

    /**
     * Initialize auth state from stored cookies
     */
    private initializeAuthState(): void {
        const token = this.cookieService.get(this.tokenKey);
        const userJson = this.cookieService.get(this.userKey);

        if (token && userJson) {
            try {
                const user = JSON.parse(userJson);
                this.updateAuthState({
                    isAuthenticated: true,
                    user,
                    token,
                    loading: false,
                    error: null
                });
            } catch (error) {
                this.clearAuthData();
            }
        }
    }

    /**
     * Update the auth state
     */
    private updateAuthState(newState: Partial<AuthState>): void {
        const currentState = this.authStateSubject.value;
        this.authStateSubject.next({...currentState, ...newState});
    }

    /**
     * Get current user
     */
    public getCurrentUser(): User | null {
        return this.authStateSubject.value.user;
    }

    /**
     * Get current token
     */
    public getToken(): string | null {
        return this.authStateSubject.value.token;
    }

    /**
     * Check if user is authenticated
     */
    public isAuthenticated(): boolean {
        return this.authStateSubject.value.isAuthenticated;
    }

    /**
     * Login user
     */
    public login(credentials: LoginRequest): Observable<LoginResponse> {
        this.updateAuthState({loading: true, error: null});

        return this.http.post<LoginResponse>(`${this.baseUrl}/api/v1/user/login`, credentials)
            .pipe(
                tap(response => {
                    if (response.success && response.token && response.user) {
                        this.storeAuthData(response.token, response.user);
                        this.updateAuthState({
                            isAuthenticated: true,
                            user: response.user,
                            token: response.token,
                            loading: false,
                            error: null,
                            lastValidated: Date.now()
                        });
                    }
                }),
                catchError(error => {
                    this.updateAuthState({
                        loading: false,
                        error: error.error?.error || "Login failed"
                    });
                    return throwError(() => error);
                })
            );
    }

    /**
     * Logout user
     */
    public logout(): Observable<LogoutResponse> {
        this.updateAuthState({loading: true});

        return this.http.post<LogoutResponse>(`${this.baseUrl}/api/v1/user/logout`, {})
            .pipe(
                tap(() => {
                    this.clearAuthData();
                    this.updateAuthState({
                        isAuthenticated: false,
                        user: null,
                        token: null,
                        loading: false,
                        error: null,
                        lastValidated: null
                    });
                }),
                catchError(error => {
                    // Clear auth data even if logout fails
                    this.clearAuthData();
                    this.updateAuthState({
                        isAuthenticated: false,
                        user: null,
                        token: null,
                        loading: false,
                        error: null,
                        lastValidated: null
                    });
                    return throwError(() => error);
                })
            );
    }

    /**
     * Register new user
     */
    public register(userData: UserCreateRequest): Observable<UserCreateResponse> {
        this.updateAuthState({loading: true, error: null});

        return this.http.post<UserCreateResponse>(`${this.baseUrl}/api/v1/user/create`, userData)
            .pipe(
                tap(() => {
                    this.updateAuthState({
                        loading: false,
                        error: null
                    });
                }),
                catchError(error => {
                    this.updateAuthState({
                        loading: false,
                        error: error.error?.error || "Registration failed"
                    });
                    return throwError(() => error);
                })
            );
    }

    /**
     * Check if token needs validation (older than cache duration)
     */
    private needsValidation(): boolean {
        const lastValidated = this.authStateSubject.value.lastValidated;
        if (!lastValidated) {
            return true;
        }
        const now = Date.now();
        return (now - lastValidated) > this.TOKEN_VALIDATION_CACHE_MS;
    }

    /**
     * Decode JWT token locally without API call
     */
    private decodeToken(token: string): any {
        try {
            const base64Url = token.split(".")[1];
            const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
            const jsonPayload = decodeURIComponent(
                atob(base64)
                    .split("")
                    .map(c => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
                    .join("")
            );
            return JSON.parse(jsonPayload);
        } catch (error) {
            return null;
        }
    }

    /**
     * Check if token is expired locally
     */
    private isTokenExpiredLocally(token: string): boolean {
        const decoded = this.decodeToken(token);
        if (!decoded || !decoded.exp) {
            return true;
        }
        const now = Math.floor(Date.now() / 1000);
        return decoded.exp < now;
    }

    /**
     * Validate current token with caching
     * Uses local validation first, then backend validation if needed
     */
    public validateToken(forceBackendCheck: boolean = false): Observable<boolean> {
        const token = this.getToken();
        if (!token) {
            return new Observable(observer => {
                observer.next(false);
                observer.complete();
            });
        }

        // Check if token is expired locally
        if (this.isTokenExpiredLocally(token)) {
            this.clearAuthData();
            this.updateAuthState({
                isAuthenticated: false,
                user: null,
                token: null,
                lastValidated: null
            });
            return new Observable(observer => {
                observer.next(false);
                observer.complete();
            });
        }

        // If recently validated and no force check, return cached result
        if (!forceBackendCheck && !this.needsValidation()) {
            return new Observable(observer => {
                observer.next(true);
                observer.complete();
            });
        }

        // Perform backend validation
        const headers = new HttpHeaders({
            "Authorization": `Bearer ${token}`
        });

        return this.http.post<any>(`${this.baseUrl}/api/v1/user/validate-token`, {}, {headers})
            .pipe(
                map(response => {
                    if (response.valid) {
                        this.updateAuthState({
                            lastValidated: Date.now()
                        });
                        return true;
                    } else {
                        this.clearAuthData();
                        this.updateAuthState({
                            isAuthenticated: false,
                            user: null,
                            token: null,
                            lastValidated: null
                        });
                        return false;
                    }
                }),
                catchError(() => {
                    this.clearAuthData();
                    this.updateAuthState({
                        isAuthenticated: false,
                        user: null,
                        token: null,
                        lastValidated: null
                    });
                    return new Observable<boolean>(observer => {
                        observer.next(false);
                        observer.complete();
                    });
                })
            );
    }

    /**
     * Store authentication data in cookies
     */
    private storeAuthData(token: string, user: User): void {
        // Store token for 24 hours (same as JWT expiration)
        this.cookieService.set(
            this.tokenKey,
            token,
            1, // 1 day
            "/", // path
            undefined, // domain
            true, // secure
            "Lax" // sameSite
        );

        // Store user data
        this.cookieService.set(
            this.userKey,
            JSON.stringify(user),
            1, // 1 day
            "/", // path
            undefined, // domain
            true, // secure
            "Lax" // sameSite
        );
    }

    /**
     * Clear authentication data
     */
    private clearAuthData(): void {
        this.cookieService.delete(this.tokenKey, "/");
        this.cookieService.delete(this.userKey, "/");
    }

    /**
     * Force logout (clear local data)
     */
    public forceLogout(): void {
        this.clearAuthData();
        this.updateAuthState({
            isAuthenticated: false,
            user: null,
            token: null,
            loading: false,
            error: null,
            lastValidated: null
        });
    }

    /**
     * Update user data in auth state
     */
    public updateUser(user: User): void {
        const currentState = this.authStateSubject.value;
        if (currentState.isAuthenticated && currentState.token) {
            this.storeAuthData(currentState.token, user);
            this.updateAuthState({user});
        }
    }
}