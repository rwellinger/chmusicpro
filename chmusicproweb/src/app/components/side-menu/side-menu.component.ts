import {Component, EventEmitter, inject, OnDestroy, OnInit, Output} from "@angular/core";

import {Router, RouterModule} from "@angular/router";
import {MatTooltipModule} from "@angular/material/tooltip";
import {TranslateModule} from "@ngx-translate/core";
import {Subject} from "rxjs";
import {takeUntil} from "rxjs/operators";
import {AuthService} from "../../services/business/auth.service";
import {AIConfigService} from "../../services/config/ai-config.service";
import {ApplicationMode} from "../../models/ai-config.model";
import {AuthState, User} from "../../models/user.model";
import appVersion from "../../../assets/app-version.json";

@Component({
    selector: "app-side-menu",
    standalone: true,
    imports: [RouterModule, TranslateModule, MatTooltipModule],
    templateUrl: "./side-menu.component.html",
    styleUrl: "./side-menu.component.scss",
    host: {"[class.collapsed]": "isCollapsed"}
})
export class SideMenuComponent implements OnInit, OnDestroy {
    version = appVersion.version;
    authState: AuthState | null = null;
    currentUser: User | null = null;
    firstName = "Guest";
    activeDomainName = "";
    isAdmin = false;
    showInternalChat = true;
    showExternalChat = true;
    applicationMode: ApplicationMode = "PROFI";
    isCollapsed = false;

    @Output() collapsedChange = new EventEmitter<boolean>();

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
                    this.applicationMode = config.application_mode;
                    this.setDefaultCollapsed();
                },
                error: () => {
                    this.showInternalChat = true;
                    this.showExternalChat = true;
                    this.applicationMode = "PROFI";
                    this.setDefaultCollapsed();
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

    toggleCollapse(): void {
        this.isCollapsed = !this.isCollapsed;
        this.collapsedChange.emit(this.isCollapsed);
    }

    private setDefaultCollapsed(): void {
        this.isCollapsed = this.applicationMode === "PRJCT";
        this.collapsedChange.emit(this.isCollapsed);
    }

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
