import {inject, Injectable} from "@angular/core";
import {ActivatedRouteSnapshot, CanActivate, CanActivateChild, Router, RouterStateSnapshot} from "@angular/router";
import {Observable, of} from "rxjs";
import {catchError, map} from "rxjs/operators";
import {AuthService} from "../services/business/auth.service";

@Injectable({
    providedIn: "root"
})
export class AuthGuard implements CanActivate, CanActivateChild {
    private authService = inject(AuthService);
    private router = inject(Router);

    canActivate(
        route: ActivatedRouteSnapshot,
        state: RouterStateSnapshot
    ): Observable<boolean> {
        return this.checkAuthentication(state.url);
    }

    canActivateChild(
        childRoute: ActivatedRouteSnapshot,
        state: RouterStateSnapshot
    ): Observable<boolean> {
        return this.checkAuthentication(state.url);
    }

    private checkAuthentication(url: string): Observable<boolean> {
        // If user is already authenticated locally, allow access
        if (this.authService.isAuthenticated()) {
            // Validate token (uses cache, so minimal overhead)
            // forceBackendCheck=false uses local validation + 5-minute cache
            return this.authService.validateToken(false).pipe(
                map(isValid => {
                    if (!isValid) {
                        this.redirectToLogin(url);
                        return false;
                    }
                    return true;
                }),
                catchError(() => {
                    this.redirectToLogin(url);
                    return of(false);
                })
            );
        }

        // Not authenticated, redirect to login
        this.redirectToLogin(url);
        return of(false);
    }

    private redirectToLogin(returnUrl?: string): void {
        const navigationExtras = returnUrl ? {queryParams: {returnUrl}} : {};
        this.router.navigate(["/login"], navigationExtras);
    }
}