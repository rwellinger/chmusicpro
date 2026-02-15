import {Component, inject, OnDestroy, OnInit} from "@angular/core";

import {Router, RouterModule} from "@angular/router";
import {TranslateModule} from "@ngx-translate/core";
import {Subject} from "rxjs";
import {takeUntil} from "rxjs/operators";
import {AuthService} from "../../services/business/auth.service";
import {AIConfigService} from "../../services/config/ai-config.service";
import {AuthState, User} from "../../models/user.model";
import appVersion from "../../../assets/app-version.json";

@Component({
    selector: "app-side-menu",
    standalone: true,
    imports: [RouterModule, TranslateModule],
    templateUrl: "./side-menu.component.html",
    styleUrl: "./side-menu.component.scss"
})
export class SideMenuComponent implements OnInit, OnDestroy {
    version = appVersion.version;
    authState: AuthState | null = null;
    currentUser: User | null = null;
    firstName = "Guest"; // Computed property to avoid method calls in template
    activeDomainName = ""; // Active domain name from JWT
    isAdmin = false;
    showInternalChat = true;
    showExternalChat = true;

    private destroy$ = new Subject<void>();
    private authService = inject(AuthService);
    private aiConfigService = inject(AIConfigService);
    private router = inject(Router);

    ngOnInit(): void {
        // Subscribe to auth state changes
        this.authService.authState$
            .pipe(takeUntil(this.destroy$))
            .subscribe(authState => {
                this.authState = authState;
                this.currentUser = authState.user;
                this.isAdmin = authState.isSystemAdmin;
                const rawName = authState.activeDomainName || "";
                const cleanName = rawName.includes(":") ? rawName.split(":").slice(1).join(":") : rawName;
                this.activeDomainName = cleanName.toLowerCase();
                this.updateFirstName(); // Update computed property
            });

        // Load AI config for chat menu visibility
        this.aiConfigService.getConfig()
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: (config) => {
                    this.showInternalChat = config.ollama_enabled;
                    this.showExternalChat = config.external_enabled;
                },
                error: () => {
                    // Fallback: show both
                    this.showInternalChat = true;
                    this.showExternalChat = true;
                }
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
