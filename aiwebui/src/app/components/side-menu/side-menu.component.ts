import {Component, inject, OnDestroy, OnInit} from "@angular/core";
import {CommonModule} from "@angular/common";
import {Router, RouterModule} from "@angular/router";
import {TranslateModule, TranslateService} from "@ngx-translate/core";
import {Subject} from "rxjs";
import {takeUntil} from "rxjs/operators";
import {AuthService} from "../../services/business/auth.service";
import {AuthState, User} from "../../models/user.model";
import appVersion from "../../../assets/app-version.json";

@Component({
    selector: "app-side-menu",
    standalone: true,
    imports: [RouterModule, CommonModule, TranslateModule],
    templateUrl: "./side-menu.component.html",
    styleUrl: "./side-menu.component.scss"
})
export class SideMenuComponent implements OnInit, OnDestroy {
    version = appVersion.version;
    authState: AuthState | null = null;
    currentUser: User | null = null;
    firstName = "Guest"; // Computed property to avoid method calls in template
    currentLang = "EN"; // Current language code

    private destroy$ = new Subject<void>();
    private authService = inject(AuthService);
    private router = inject(Router);
    private translate = inject(TranslateService);

    ngOnInit(): void {
        // Subscribe to auth state changes
        this.authService.authState$
            .pipe(takeUntil(this.destroy$))
            .subscribe(authState => {
                this.authState = authState;
                this.currentUser = authState.user;
                this.updateFirstName(); // Update computed property
            });

        // Subscribe to language changes
        this.currentLang = this.translate.currentLang?.toUpperCase() || "EN";
        this.translate.onLangChange
            .pipe(takeUntil(this.destroy$))
            .subscribe(event => {
                this.currentLang = event.lang?.toUpperCase() || "EN";
            });
    }

    ngOnDestroy(): void {
        this.destroy$.next();
        this.destroy$.complete();
    }

    public onLogout(): void {
        this.authService.logout()
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: () => {
                    this.router.navigate(["/login"]);
                },
                error: (error) => {
                    console.error("Logout error:", error);
                    this.authService.forceLogout();
                    this.router.navigate(["/login"]);
                }
            });
    }

    /**
     * Update firstName property based on current user
     * Called when user changes to avoid method calls in template
     */
    private updateFirstName(): void {
        if (!this.currentUser) {
            this.firstName = "Guest";
            return;
        }

        if (this.currentUser.first_name) {
            this.firstName = this.currentUser.first_name;
            return;
        }

        this.firstName = this.currentUser.email.split("@")[0];
    }

    public getUserDisplayName(): string {
        if (!this.currentUser) return "Guest";

        if (this.currentUser.first_name && this.currentUser.last_name) {
            return `${this.currentUser.first_name} ${this.currentUser.last_name}`;
        }

        if (this.currentUser.first_name) {
            return this.currentUser.first_name;
        }

        return this.currentUser.email.split("@")[0];
    }
}
