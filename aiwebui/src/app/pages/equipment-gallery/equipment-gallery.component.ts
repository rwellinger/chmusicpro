import {Component, inject, OnDestroy, OnInit} from "@angular/core";
import {CommonModule} from "@angular/common";
import {FormsModule} from "@angular/forms";
import {Router} from "@angular/router";
import {debounceTime, distinctUntilChanged, firstValueFrom, Subject, takeUntil} from "rxjs";
import {TranslateModule, TranslateService} from "@ngx-translate/core";
import {MatCardModule} from "@angular/material/card";
import {MatButtonModule} from "@angular/material/button";
import {MatIconModule} from "@angular/material/icon";
import {MatChipsModule} from "@angular/material/chips";
import {MatFormFieldModule} from "@angular/material/form-field";
import {MatInputModule} from "@angular/material/input";
import {MatSelectModule} from "@angular/material/select";
import {MatProgressSpinnerModule} from "@angular/material/progress-spinner";
import {MatDialog, MatDialogModule} from "@angular/material/dialog";
import {MatExpansionModule} from "@angular/material/expansion";

import {EquipmentService} from "../../services/business/equipment.service";
import {NotificationService} from "../../services/ui/notification.service";
import {UserSettingsService} from "../../services/user-settings.service";
import {Equipment, EquipmentAttachment, EquipmentStatus, EquipmentType, LicenseManagement} from "../../models/equipment.model";

@Component({
    selector: "app-equipment-gallery",
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        TranslateModule,
        MatCardModule,
        MatButtonModule,
        MatIconModule,
        MatChipsModule,
        MatFormFieldModule,
        MatInputModule,
        MatSelectModule,
        MatProgressSpinnerModule,
        MatDialogModule,
        MatExpansionModule
    ],
    templateUrl: "./equipment-gallery.component.html",
    styleUrl: "./equipment-gallery.component.scss"
})
export class EquipmentGalleryComponent implements OnInit, OnDestroy {
    // Equipment list and pagination
    equipmentList: Equipment[] = [];
    selectedEquipment: Equipment | null = null;
    currentPage = 0;
    pagination = {
        total: 0,
        limit: 8,
        offset: 0,
        has_more: false
    };

    // Search and filter
    searchTerm = "";
    selectedType: EquipmentType | "all" = "all";
    selectedStatus: EquipmentStatus | "all" = "all";

    // UI state
    isLoading = false;
    showDeleteConfirm = false;
    deleteEquipmentId: string | null = null;

    // Visibility toggles for sensitive fields
    showPassword = false;
    showLicenseKey = false;

    // Attachments for selected equipment
    attachments: EquipmentAttachment[] = [];

    // Enums for template
    EquipmentType = EquipmentType;
    EquipmentStatus = EquipmentStatus;
    LicenseManagement = LicenseManagement;

    // Math for template
    Math = Math;

    // RxJS subjects
    private searchSubject = new Subject<string>();
    private destroy$ = new Subject<void>();

    private equipmentService = inject(EquipmentService);
    private notificationService = inject(NotificationService);
    private settingsService = inject(UserSettingsService);
    private translate = inject(TranslateService);
    private router = inject(Router);
    private dialog = inject(MatDialog);

    // Navigation state (must be captured in constructor)
    private navigationState: any = null;

    // Track initial load for proper returnPage handling
    private isInitialLoad = true;
    private initialReturnPage = 0;
    private initialSelectedId: string | null = null;

    constructor() {
        // IMPORTANT: getCurrentNavigation() must be called in constructor!
        const navigation = this.router.getCurrentNavigation();
        this.navigationState = navigation?.extras?.state;

        // Setup search debouncing
        this.searchSubject.pipe(
            debounceTime(300),
            distinctUntilChanged(),
            takeUntil(this.destroy$)
        ).subscribe(searchTerm => {
            this.searchTerm = searchTerm;
            this.loadEquipment(0);
        });
    }

    ngOnInit(): void {
        // Check if returning from editor with a selected equipment ID
        this.initialReturnPage = this.navigationState?.["returnPage"] || 0;
        this.initialSelectedId = this.navigationState?.["selectedId"];

        // Restore filter state from navigation
        const savedSearchTerm = this.navigationState?.["searchTerm"];
        const savedType = this.navigationState?.["selectedType"];
        const savedStatus = this.navigationState?.["selectedStatus"];

        if (savedSearchTerm !== undefined) {
            this.searchTerm = savedSearchTerm;
        }
        if (savedType !== undefined && (savedType === "all" || Object.values(EquipmentType).includes(savedType))) {
            this.selectedType = savedType;
        }
        if (savedStatus !== undefined && (savedStatus === "all" || Object.values(EquipmentStatus).includes(savedStatus))) {
            this.selectedStatus = savedStatus;
        }

        // Load user settings (will trigger initial load with returnPage)
        this.loadUserSettings();
    }

    /**
     * Load user settings and apply equipment list limit.
     * On initial load: uses returnPage from navigation state.
     * On subsequent updates: reloads current page.
     */
    private loadUserSettings(): void {
        this.settingsService.getSettings()
            .pipe(takeUntil(this.destroy$))
            .subscribe(settings => {
                this.pagination.limit = settings.equipmentListLimit;

                if (this.isInitialLoad) {
                    // First load: use returnPage from navigation state
                    this.isInitialLoad = false;
                    this.loadEquipment(this.initialReturnPage).then(() => {
                        // Re-select the equipment after save if ID was provided
                        if (this.initialSelectedId) {
                            const equipment = this.equipmentList.find(e => e.id === this.initialSelectedId);
                            if (equipment) {
                                this.selectEquipment(equipment);
                            } else {
                                // Fallback: Equipment not on this page (e.g., filters changed)
                                this.notificationService.info(
                                    this.translate.instant("equipment.messages.equipmentSaved")
                                );
                            }
                        }
                    });
                } else {
                    // Subsequent loads: reload current page (when user changes settings)
                    this.loadEquipment(this.currentPage);
                }
            });
    }

    ngOnDestroy(): void {
        this.destroy$.next();
        this.destroy$.complete();
    }

    /**
     * Load equipment list with current filters and pagination.
     */
    async loadEquipment(page: number = 0): Promise<void> {
        this.isLoading = true;

        try {
            const offset = page * this.pagination.limit;
            const typeFilter = this.selectedType === "all" ? undefined : this.selectedType;
            const statusFilter = this.selectedStatus === "all" ? undefined : this.selectedStatus;
            const searchQuery = this.searchTerm.trim() || undefined;

            const response = await firstValueFrom(
                this.equipmentService.getEquipments(
                    this.pagination.limit,
                    offset,
                    typeFilter,
                    statusFilter,
                    searchQuery
                )
            );

            this.equipmentList = response.data as Equipment[];
            this.pagination = response.pagination;
            this.currentPage = page;

            // Auto-select first equipment if list is not empty and nothing is selected
            if (this.equipmentList.length > 0 && !this.selectedEquipment) {
                this.selectEquipment(this.equipmentList[0]);
            }
        } catch (error) {
            console.error("Failed to load equipment:", error);
            this.notificationService.error(
                this.translate.instant("equipment.messages.loadError")
            );
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * Handle search input change.
     */
    onSearchChange(searchTerm: string): void {
        this.searchSubject.next(searchTerm);
    }

    /**
     * Clear search input.
     */
    clearSearch(): void {
        this.searchTerm = "";
        this.searchSubject.next("");
    }

    /**
     * Handle type filter change.
     */
    onTypeFilterChange(): void {
        this.loadEquipment(0);
    }

    /**
     * Handle status filter change.
     */
    onStatusFilterChange(): void {
        this.loadEquipment(0);
    }

    /**
     * Select equipment to show details (loads full data with decrypted fields).
     */
    async selectEquipment(equipment: Equipment): Promise<void> {
        try {
            // Load full equipment details (includes decrypted password, license_key, price)
            const response = await firstValueFrom(
                this.equipmentService.getEquipmentById(equipment.id)
            );

            this.selectedEquipment = response.data;

            // Reset visibility toggles when selecting new equipment
            this.showPassword = false;
            this.showLicenseKey = false;

            // Load attachments for this equipment
            this.loadAttachments(equipment.id);
        } catch (error) {
            console.error("Failed to load equipment details:", error);
            this.notificationService.error(
                this.translate.instant("equipment.messages.loadError")
            );
            // Fallback to list data if detail load fails
            this.selectedEquipment = equipment;
        }
    }

    /**
     * Navigate to equipment editor (edit mode).
     */
    editEquipment(id: string): void {
        this.router.navigate(["/equipment-editor", id], {
            state: {
                returnPage: this.currentPage,
                searchTerm: this.searchTerm,
                selectedType: this.selectedType,
                selectedStatus: this.selectedStatus
            }
        });
    }

    /**
     * Navigate to equipment editor (duplicate mode).
     */
    duplicateEquipment(id: string): void {
        this.router.navigate(["/equipment-editor"], {
            queryParams: {duplicate: id},
            state: {
                returnPage: this.currentPage,
                searchTerm: this.searchTerm,
                selectedType: this.selectedType,
                selectedStatus: this.selectedStatus
            }
        });
    }

    /**
     * Navigate to equipment editor (create mode).
     */
    createNew(): void {
        this.router.navigate(["/equipment-editor"], {
            state: {
                returnPage: this.currentPage,
                searchTerm: this.searchTerm,
                selectedType: this.selectedType,
                selectedStatus: this.selectedStatus
            }
        });
    }

    /**
     * Show delete confirmation dialog.
     */
    confirmDelete(id: string, event: Event): void {
        event.stopPropagation();
        this.showDeleteConfirm = true;
        this.deleteEquipmentId = id;
    }

    /**
     * Delete equipment after confirmation.
     */
    async deleteEquipment(): Promise<void> {
        if (!this.deleteEquipmentId) return;

        try {
            await firstValueFrom(
                this.equipmentService.deleteEquipment(this.deleteEquipmentId)
            );

            this.notificationService.success(
                this.translate.instant("equipment.messages.deleteSuccess")
            );

            // Reload list
            await this.loadEquipment();

            // Clear selection if deleted
            if (this.selectedEquipment?.id === this.deleteEquipmentId) {
                this.selectedEquipment = null;
            }
        } catch (error) {
            console.error("Failed to delete equipment:", error);
            this.notificationService.error(
                this.translate.instant("equipment.messages.deleteError")
            );
        } finally {
            this.showDeleteConfirm = false;
            this.deleteEquipmentId = null;
        }
    }

    /**
     * Cancel delete operation.
     */
    cancelDelete(): void {
        this.showDeleteConfirm = false;
        this.deleteEquipmentId = null;
    }

    /**
     * Navigate to next page.
     */
    nextPage(): void {
        if (this.pagination.has_more && !this.isLoading) {
            this.loadEquipment(this.currentPage + 1);
        }
    }

    /**
     * Navigate to previous page.
     */
    previousPage(): void {
        if (this.currentPage > 0 && !this.isLoading) {
            this.loadEquipment(this.currentPage - 1);
        }
    }

    /**
     * Get icon for equipment type.
     */
    getTypeIcon(type: EquipmentType): string {
        switch (type) {
            case EquipmentType.SOFTWARE:
                return "desktop_windows";
            case EquipmentType.PLUGIN:
                return "extension";
            default:
                return "device_unknown";
        }
    }

    /**
     * Format date for display in list.
     */
    formatDate(dateString: string): string {
        const date = new Date(dateString);
        return date.toLocaleDateString() + " " + date.toLocaleTimeString([], {hour: "2-digit", minute: "2-digit"});
    }

    /**
     * Get color for status chip.
     */
    getStatusColor(status: EquipmentStatus): string {
        switch (status) {
            case EquipmentStatus.ACTIVE:
                return "primary";
            case EquipmentStatus.TRIAL:
                return "accent";
            case EquipmentStatus.EXPIRED:
                return "warn";
            case EquipmentStatus.ARCHIVED:
                return "";
            default:
                return "";
        }
    }

    /**
     * Toggle password visibility.
     */
    togglePasswordVisibility(): void {
        this.showPassword = !this.showPassword;
    }

    /**
     * Toggle license key visibility.
     */
    toggleLicenseKeyVisibility(): void {
        this.showLicenseKey = !this.showLicenseKey;
    }

    /**
     * Copy text to clipboard.
     */
    async copyToClipboard(text: string | undefined, fieldName: string): Promise<void> {
        if (!text || !text.trim()) {
            return;
        }

        try {
            await navigator.clipboard.writeText(text);
            this.notificationService.success(
                this.translate.instant(`equipment.gallery.actions.copy${fieldName}`)
            );
        } catch (error) {
            console.error("Failed to copy to clipboard:", error);
            this.notificationService.error(
                this.translate.instant("equipment.messages.copyError")
            );
        }
    }

    /**
     * Check if equipment has credential data.
     */
    hasCredentials(): boolean {
        if (!this.selectedEquipment) return false;
        return !!(
            this.selectedEquipment.manufacturer ||
            this.selectedEquipment.url ||
            this.selectedEquipment.username ||
            this.selectedEquipment.password
        );
    }

    /**
     * Check if equipment has license information.
     */
    hasLicenseInfo(): boolean {
        if (!this.selectedEquipment) return false;
        return !!this.selectedEquipment.license_management;
    }

    /**
     * Check if both credentials and license sections should be shown as accordion.
     */
    shouldUseAccordion(): boolean {
        return this.hasCredentials() && this.hasLicenseInfo();
    }

    // ============================================================
    // Attachment Methods
    // ============================================================

    /**
     * Load attachments for selected equipment.
     */
    loadAttachments(equipmentId: string): void {
        this.equipmentService.getAttachments(equipmentId).subscribe({
            next: (response) => {
                this.attachments = response.data;
            },
            error: (error) => {
                console.error("Failed to load attachments:", error);
                this.attachments = [];
            }
        });
    }

    /**
     * Download an attachment.
     */
    downloadAttachment(attachment: EquipmentAttachment): void {
        if (!this.selectedEquipment) return;

        this.equipmentService.downloadAttachment(this.selectedEquipment.id, attachment.id).subscribe({
            next: (blob) => {
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement("a");
                link.href = url;
                link.download = attachment.filename;
                link.click();
                window.URL.revokeObjectURL(url);
            },
            error: (error) => {
                console.error("Download failed:", error);
                this.notificationService.error(
                    this.translate.instant("equipment.attachments.downloadError")
                );
            }
        });
    }

    /**
     * Format file size for display.
     */
    formatFileSize(bytes: number): string {
        if (bytes < 1024) return bytes + " B";
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
        return (bytes / (1024 * 1024)).toFixed(1) + " MB";
    }
}
