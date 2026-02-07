import {inject} from "@angular/core";
import {HttpErrorResponse, HttpHandlerFn, HttpInterceptorFn, HttpRequest} from "@angular/common/http";
import {BehaviorSubject, Observable, throwError, timeout} from "rxjs";
import {catchError, filter, finalize, switchMap, take} from "rxjs/operators";
import {AuthService} from "../services/business/auth.service";
import {Router} from "@angular/router";
import {MatSnackBar} from "@angular/material/snack-bar";
import {TranslateService} from "@ngx-translate/core";

let isRefreshing = false;
const refreshTokenSubject: BehaviorSubject<any> = new BehaviorSubject<any>(null);
const TOKEN_REFRESH_TIMEOUT_MS = 5000; // 5 seconds timeout for token validation

export const authInterceptor: HttpInterceptorFn = (req, next) => {
    const authService = inject(AuthService);
    const router = inject(Router);
    const snackBar = inject(MatSnackBar);
    const translate = inject(TranslateService);

    // Skip authentication for auth-related endpoints
    if (isAuthEndpoint(req.url)) {
        return next(req);
    }

    // Add authentication token to request
    const authToken = authService.getToken();
    if (authToken) {
        req = addTokenToRequest(req, authToken);
    }

    return next(req).pipe(
        catchError((error: HttpErrorResponse) => {
            // Handle 401 Unauthorized errors
            if (error.status === 401 && authToken) {
                return handle401Error(req, next, authService, router, snackBar, translate);
            }

            // Handle other errors
            if (error.status === 403) {
                // Forbidden - user doesn't have permission
                authService.forceLogout();
                router.navigate(["/login"]);
            }

            return throwError(() => error);
        })
    );
};

function isAuthEndpoint(url: string): boolean {
    const authEndpoints = [
        "/api/v1/user/login",
        "/api/v1/user/create",
        "/api/v1/user/validate-token",
        "/aiproxysrv/api/v1/user/login",
        "/aiproxysrv/api/v1/user/create",
        "/aiproxysrv/api/v1/user/validate-token"
    ];
    return authEndpoints.some(endpoint => url.includes(endpoint));
}

function addTokenToRequest(request: HttpRequest<any>, token: string): HttpRequest<any> {
    return request.clone({
        setHeaders: {
            "Authorization": `Bearer ${token}`
        }
    });
}

function handle401Error(request: HttpRequest<any>, next: HttpHandlerFn, authService: AuthService, router: Router, snackBar: MatSnackBar, translate: TranslateService): Observable<any> {
    if (!isRefreshing) {
        isRefreshing = true;
        refreshTokenSubject.next(null);

        // Validate current token with timeout and force backend check
        return authService.validateToken(true).pipe(
            timeout(TOKEN_REFRESH_TIMEOUT_MS),
            switchMap((isValid: boolean) => {
                if (isValid) {
                    // Token is still valid, retry original request
                    const token = authService.getToken();
                    if (token) {
                        refreshTokenSubject.next(token);
                        return next(addTokenToRequest(request, token));
                    }
                }

                // Token is invalid, logout user
                snackBar.open(
                    translate.instant("authInterceptor.sessionExpired"),
                    translate.instant("common.close"),
                    {
                        duration: 5000,
                        horizontalPosition: "center",
                        verticalPosition: "top"
                    }
                );
                authService.forceLogout();
                router.navigate(["/login"]);
                return throwError(() => new Error("Authentication failed"));
            }),
            catchError((error) => {
                // Handle both validation errors and timeouts
                const errorMessage = error.name === "TimeoutError"
                    ? translate.instant("authInterceptor.sessionTimeout")
                    : translate.instant("authInterceptor.sessionExpired");

                snackBar.open(errorMessage, translate.instant("common.close"), {
                    duration: 5000,
                    horizontalPosition: "center",
                    verticalPosition: "top"
                });
                authService.forceLogout();
                router.navigate(["/login"]);
                return throwError(() => error);
            }),
            finalize(() => {
                // Always reset refreshing state, even on error
                isRefreshing = false;
            })
        );
    } else {
        // Wait for token refresh to complete with timeout
        return refreshTokenSubject.pipe(
            filter(token => token != null),
            take(1),
            timeout(TOKEN_REFRESH_TIMEOUT_MS),
            switchMap(token => {
                return next(addTokenToRequest(request, token));
            }),
            catchError((error) => {
                // Timeout while waiting for other request's validation
                if (error.name === "TimeoutError") {
                    snackBar.open(
                        translate.instant("authInterceptor.sessionTimeout"),
                        translate.instant("common.close"),
                        {
                            duration: 5000,
                            horizontalPosition: "center",
                            verticalPosition: "top"
                        }
                    );
                    authService.forceLogout();
                    router.navigate(["/login"]);
                }
                return throwError(() => error);
            })
        );
    }
}