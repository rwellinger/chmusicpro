import {Component, inject, OnDestroy, OnInit} from "@angular/core";
import {CommonModule} from "@angular/common";
import {FormsModule} from "@angular/forms";
import {MatCardModule} from "@angular/material/card";
import {MatButtonModule} from "@angular/material/button";
import {MatSelectModule} from "@angular/material/select";
import {MatFormFieldModule} from "@angular/material/form-field";
import {MatInputModule} from "@angular/material/input";
import {MatSnackBarModule} from "@angular/material/snack-bar";
import {TranslateModule, TranslateService} from "@ngx-translate/core";
import {Subject} from "rxjs";
import {takeUntil} from "rxjs/operators";

import {DomainService} from "../../services/business/domain.service";
import {AuthService} from "../../services/business/auth.service";
import {NotificationService} from "../../services/ui/notification.service";
import {
    DomainMember,
    DomainRoles,
    DomainType,
    DomainTypeLabels,
    DomainWithRole
} from "../../models/domain.model";

@Component({
    selector: "app-domain-management",
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        MatCardModule,
        MatButtonModule,
        MatSelectModule,
        MatFormFieldModule,
        MatInputModule,
        MatSnackBarModule,
        TranslateModule
    ],
    templateUrl: "./domain-management.component.html",
    styleUrl: "./domain-management.component.scss"
})
export class DomainManagementComponent implements OnInit, OnDestroy {
    domains: DomainWithRole[] = [];
    selectedDomain: DomainWithRole | null = null;
    members: DomainMember[] = [];

    isLoadingDomains = false;
    isLoadingMembers = false;
    isAddingMember = false;

    newMemberEmail = "";
    newMemberRole = "member";
    domainRoles = DomainRoles;
    domainTypeLabels = DomainTypeLabels;

    // Create domain form
    showCreateForm = false;
    newDomainName = "";
    newDomainDescription = "";
    newDomainType = DomainType.COMPANY;
    creatableDomainTypes = [
        {value: DomainType.COMPANY, label: "Company"},
        {value: DomainType.PRODUCER, label: "Producer"}
    ];
    isCreatingDomain = false;

    private destroy$ = new Subject<void>();
    private domainService = inject(DomainService);
    private authService = inject(AuthService);
    private notificationService = inject(NotificationService);
    private translate = inject(TranslateService);

    currentUserId: string | null = null;

    ngOnInit(): void {
        this.currentUserId = this.authService.getCurrentUser()?.id ?? null;
        this.loadDomains();
    }

    ngOnDestroy(): void {
        this.destroy$.next();
        this.destroy$.complete();
    }

    private loadDomains(): void {
        this.isLoadingDomains = true;
        this.domainService.getUserDomains()
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: (response) => {
                    this.domains = response.domains || [];
                    if (this.selectedDomain) {
                        const updated = this.domains.find(d => d.domain.id === this.selectedDomain!.domain.id);
                        if (updated) {
                            this.selectedDomain = updated;
                        }
                    }
                    this.isLoadingDomains = false;
                },
                error: (error) => {
                    console.error("Error loading domains:", error);
                    this.isLoadingDomains = false;
                }
            });
    }

    selectDomain(domain: DomainWithRole): void {
        this.selectedDomain = domain;
        this.loadMembers(domain.domain.id);
    }

    private loadMembers(domainId: string): void {
        this.isLoadingMembers = true;
        this.members = [];
        this.domainService.getDomainMembers(domainId)
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: (response) => {
                    this.members = response.members || [];
                    this.isLoadingMembers = false;
                },
                error: (error) => {
                    console.error("Error loading members:", error);
                    this.isLoadingMembers = false;
                    if (error.status === 403) {
                        this.members = [];
                    }
                }
            });
    }

    addMember(): void {
        if (!this.selectedDomain || !this.newMemberEmail.trim()) {
            return;
        }
        this.isAddingMember = true;
        this.domainService.addMember(this.selectedDomain.domain.id, {
            email: this.newMemberEmail.trim(),
            role: this.newMemberRole
        })
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: () => {
                    this.notificationService.success(this.translate.instant("domainManagement.memberAdded"));
                    this.newMemberEmail = "";
                    this.newMemberRole = "member";
                    this.loadMembers(this.selectedDomain!.domain.id);
                    this.isAddingMember = false;
                },
                error: (error) => {
                    this.notificationService.error(
                        error.error?.error || this.translate.instant("domainManagement.memberAddError")
                    );
                    this.isAddingMember = false;
                }
            });
    }

    updateMemberRole(member: DomainMember, newRole: string): void {
        if (!this.selectedDomain) {
            return;
        }
        this.domainService.updateMemberRole(this.selectedDomain.domain.id, member.user_id, {role: newRole})
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: () => {
                    this.notificationService.success(this.translate.instant("domainManagement.roleUpdated"));
                    this.loadMembers(this.selectedDomain!.domain.id);
                },
                error: (error) => {
                    this.notificationService.error(
                        error.error?.error || this.translate.instant("domainManagement.roleUpdateError")
                    );
                }
            });
    }

    removeMember(member: DomainMember): void {
        if (!this.selectedDomain) {
            return;
        }
        const displayName = member.first_name
            ? `${member.first_name} ${member.last_name || ""}`.trim()
            : member.email;
        if (!confirm(this.translate.instant("domainManagement.confirmRemove", {name: displayName}))) {
            return;
        }
        this.domainService.removeMember(this.selectedDomain.domain.id, member.user_id)
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: () => {
                    this.notificationService.success(this.translate.instant("domainManagement.memberRemoved"));
                    this.loadMembers(this.selectedDomain!.domain.id);
                },
                error: (error) => {
                    this.notificationService.error(
                        error.error?.error || this.translate.instant("domainManagement.memberRemoveError")
                    );
                }
            });
    }

    createDomain(): void {
        if (!this.newDomainName.trim()) {
            return;
        }
        this.isCreatingDomain = true;
        this.domainService.createDomain({
            type: this.newDomainType,
            name: this.newDomainName.trim(),
            description: this.newDomainDescription.trim() || undefined
        })
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: () => {
                    this.notificationService.success(this.translate.instant("domainManagement.domainCreated"));
                    this.showCreateForm = false;
                    this.newDomainName = "";
                    this.newDomainDescription = "";
                    this.loadDomains();
                    this.isCreatingDomain = false;
                },
                error: (error) => {
                    this.notificationService.error(
                        error.error?.error || this.translate.instant("domainManagement.domainCreateError")
                    );
                    this.isCreatingDomain = false;
                }
            });
    }

    deactivateDomain(): void {
        if (!this.selectedDomain) {
            return;
        }
        if (!confirm(this.translate.instant("domainManagement.confirmDeactivate", {name: this.selectedDomain.domain.name}))) {
            return;
        }
        this.domainService.deactivateDomain(this.selectedDomain.domain.id)
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: () => {
                    this.notificationService.success(this.translate.instant("domainManagement.domainDeactivated"));
                    this.selectedDomain = null;
                    this.members = [];
                    this.loadDomains();
                },
                error: (error) => {
                    this.notificationService.error(
                        error.error?.error || this.translate.instant("domainManagement.domainDeactivateError")
                    );
                }
            });
    }

    getDomainTypeIcon(type: number): string {
        switch (type) {
            case 0: return "fas fa-shield-alt";
            case 1: return "fas fa-robot";
            case 2: return "fas fa-user";
            case 3: return "fas fa-building";
            case 4: return "fas fa-headphones";
            default: return "fas fa-globe";
        }
    }

    formatDate(dateString: string): string {
        if (!dateString) return "-";
        const date = new Date(dateString);
        return date.toLocaleDateString("en-US", {
            year: "numeric",
            month: "short",
            day: "numeric"
        });
    }

    isSystemAdmin(): boolean {
        return this.authService.isSystemAdmin();
    }
}
