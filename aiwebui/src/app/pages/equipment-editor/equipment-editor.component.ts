import {Component, inject, OnDestroy, OnInit} from "@angular/core";
import {FormBuilder, FormGroup, ReactiveFormsModule, Validators} from "@angular/forms";
import {CommonModule} from "@angular/common";
import {ActivatedRoute, Router} from "@angular/router";
import {TranslateModule, TranslateService} from "@ngx-translate/core";
import {MatCardModule} from "@angular/material/card";
import {MatButtonModule} from "@angular/material/button";
import {MatIconModule} from "@angular/material/icon";
import {MatFormFieldModule} from "@angular/material/form-field";
import {MatInputModule} from "@angular/material/input";
import {MatSelectModule} from "@angular/material/select";
import {MatDatepickerModule} from "@angular/material/datepicker";
import {MatNativeDateModule} from "@angular/material/core";
import {MatExpansionModule} from "@angular/material/expansion";
import {firstValueFrom, Subject, takeUntil} from "rxjs";

import {EquipmentService} from "../../services/business/equipment.service";
import {NotificationService} from "../../services/ui/notification.service";
import {
    EquipmentAttachment,
    EquipmentCreateRequest,
    EquipmentStatus,
    EquipmentType,
    EquipmentUpdateRequest,
    LicenseManagement
} from "../../models/equipment.model";
import {InfoTooltipComponent} from "../../components/info-tooltip/info-tooltip.component";

@Component({
    selector: "app-equipment-editor",
    standalone: true,
    imports: [
        CommonModule,
        ReactiveFormsModule,
        TranslateModule,
        MatCardModule,
        MatButtonModule,
        MatIconModule,
        MatFormFieldModule,
        MatInputModule,
        MatSelectModule,
        MatDatepickerModule,
        MatNativeDateModule,
        MatExpansionModule,
        InfoTooltipComponent
    ],
    templateUrl: "./equipment-editor.component.html",
    styleUrl: "./equipment-editor.component.scss"
})
export class EquipmentEditorComponent implements OnInit, OnDestroy {
    equipmentForm!: FormGroup;
    isSaving = false;
    isLoading = false;

    // Edit mode
    isEditMode = false;
    equipmentId: string | null = null;

    // Password/License Key visibility
    showPassword = false;
    showLicenseKey = false;

    // Attachments
    attachments: EquipmentAttachment[] = [];
    isUploadingFile = false;

    // Enums for template
    EquipmentType = EquipmentType;
    LicenseManagement = LicenseManagement;
    EquipmentStatus = EquipmentStatus;

    // Enum arrays for dropdowns
    equipmentTypes = Object.values(EquipmentType);
    licenseManagementTypes = Object.values(LicenseManagement);
    equipmentStatuses = Object.values(EquipmentStatus);

    // Navigation state (must be captured in constructor)
    private navigationState: any = null;

    private destroy$ = new Subject<void>();
    private fb = inject(FormBuilder);
    private router = inject(Router);
    private route = inject(ActivatedRoute);
    private equipmentService = inject(EquipmentService);
    private notificationService = inject(NotificationService);
    private translate = inject(TranslateService);

    constructor() {
        // IMPORTANT: getCurrentNavigation() must be called in constructor!
        const navigation = this.router.getCurrentNavigation();
        this.navigationState = navigation?.extras?.state;
    }

    ngOnInit(): void {
        this.initForm();
        this.loadEquipmentIfEditMode();
        this.loadEquipmentIfDuplicateMode();
        this.setupConditionalValidation();
    }

    ngOnDestroy(): void {
        this.destroy$.next();
        this.destroy$.complete();
    }

    /**
     * Initialize reactive form.
     */
    private initForm(): void {
        this.equipmentForm = this.fb.group({
            type: [EquipmentType.SOFTWARE, Validators.required],
            name: ["", [Validators.required, Validators.maxLength(200)]],
            version: ["", Validators.maxLength(100)],
            description: [""],
            software_tags: [""],
            plugin_tags: [""],
            manufacturer: ["", Validators.maxLength(200)],
            url: ["", Validators.maxLength(500)],
            username: ["", Validators.maxLength(200)],
            password: [""],
            license_management: [""],
            license_key: [""],
            license_description: [""],
            purchase_date: [""],
            price: [""],
            system_requirements: [""],
            status: [EquipmentStatus.ACTIVE, Validators.required]
        });
    }

    /**
     * Setup conditional validation based on license_management.
     */
    private setupConditionalValidation(): void {
        this.equipmentForm.get("license_management")?.valueChanges
            .pipe(takeUntil(this.destroy$))
            .subscribe(value => {
                const licenseKeyControl = this.equipmentForm.get("license_key");
                const licenseDescControl = this.equipmentForm.get("license_description");

                if (value === LicenseManagement.LICENSE_KEY) {
                    licenseKeyControl?.setValidators(Validators.required);
                } else {
                    licenseKeyControl?.clearValidators();
                }

                if (value === LicenseManagement.OTHER) {
                    licenseDescControl?.setValidators(Validators.required);
                } else {
                    licenseDescControl?.clearValidators();
                }

                licenseKeyControl?.updateValueAndValidity();
                licenseDescControl?.updateValueAndValidity();
            });
    }

    /**
     * Load equipment data if in edit mode.
     */
    private async loadEquipmentIfEditMode(): Promise<void> {
        this.equipmentId = this.route.snapshot.paramMap.get("id");

        if (this.equipmentId) {
            this.isEditMode = true;
            this.isLoading = true;

            try {
                const response = await firstValueFrom(
                    this.equipmentService.getEquipmentById(this.equipmentId)
                );

                // Patch form with equipment data
                this.equipmentForm.patchValue({
                    type: response.data.type,
                    name: response.data.name,
                    version: response.data.version,
                    description: response.data.description,
                    software_tags: response.data.software_tags,
                    plugin_tags: response.data.plugin_tags,
                    manufacturer: response.data.manufacturer,
                    url: response.data.url,
                    username: response.data.username,
                    password: response.data.password,
                    license_management: response.data.license_management,
                    license_key: response.data.license_key,
                    license_description: response.data.license_description,
                    purchase_date: response.data.purchase_date,
                    price: response.data.price,
                    system_requirements: response.data.system_requirements,
                    status: response.data.status
                });

                // Load attachments
                this.loadAttachments();
            } catch (error) {
                console.error("Failed to load equipment:", error);
                this.notificationService.error(
                    this.translate.instant("equipment.messages.loadError")
                );
                this.router.navigate(["/equipment-gallery"]);
            } finally {
                this.isLoading = false;
            }
        }
    }

    /**
     * Load equipment data if in duplicate mode.
     */
    private async loadEquipmentIfDuplicateMode(): Promise<void> {
        const duplicateId = this.route.snapshot.queryParamMap.get("duplicate");

        if (duplicateId) {
            this.isLoading = true;

            try {
                const response = await firstValueFrom(
                    this.equipmentService.getEquipmentById(duplicateId)
                );

                // Patch form with selected fields only (duplicate mode)
                this.equipmentForm.patchValue({
                    type: response.data.type,
                    software_tags: response.data.software_tags,
                    plugin_tags: response.data.plugin_tags,
                    manufacturer: response.data.manufacturer,
                    url: response.data.url,
                    username: response.data.username,
                    password: response.data.password,
                    system_requirements: response.data.system_requirements,
                    status: EquipmentStatus.ACTIVE
                });
                // Fields NOT copied (remain empty): name, version, description,
                // license_management, license_key, license_description, price, purchase_date
            } catch (error) {
                console.error("Failed to load equipment for duplication:", error);
                this.notificationService.error(
                    this.translate.instant("equipment.messages.loadError")
                );
                this.router.navigate(["/equipment-gallery"]);
            } finally {
                this.isLoading = false;
            }
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
     * Check if software tags should be shown.
     */
    shouldShowSoftwareTags(): boolean {
        return this.equipmentForm.get("type")?.value === EquipmentType.SOFTWARE;
    }

    /**
     * Check if plugin tags should be shown.
     */
    shouldShowPluginTags(): boolean {
        return this.equipmentForm.get("type")?.value === EquipmentType.PLUGIN;
    }

    /**
     * Check if license key field should be shown.
     */
    shouldShowLicenseKey(): boolean {
        const licenseManagement = this.equipmentForm.get("license_management")?.value;
        return licenseManagement === LicenseManagement.LICENSE_KEY;
    }

    /**
     * Check if license description field should be shown.
     */
    shouldShowLicenseDescription(): boolean {
        const licenseManagement = this.equipmentForm.get("license_management")?.value;
        return licenseManagement === LicenseManagement.OTHER;
    }

    /**
     * Save equipment (create or update).
     */
    async onSave(): Promise<void> {
        if (this.equipmentForm.invalid) {
            this.equipmentForm.markAllAsTouched();
            this.notificationService.error(
                this.translate.instant("equipment.validation.formInvalid")
            );
            return;
        }

        this.isSaving = true;

        try {
            const formData = this.equipmentForm.value;

            // Clean up empty strings in optional fields (backend expects null or missing field, not empty string)
            Object.keys(formData).forEach(key => {
                if (formData[key] === "" || formData[key] === null) {
                    delete formData[key];
                }
            });

            // Convert date to ISO string if present
            if (formData.purchase_date) {
                formData.purchase_date = new Date(formData.purchase_date).toISOString().split("T")[0];
            }

            if (this.isEditMode && this.equipmentId) {
                await this.updateEquipment(formData);
            } else {
                await this.createEquipment(formData);
            }
        } catch (error) {
            console.error("Failed to save equipment:", error);

            // Parse backend validation errors for better UX
            if (error && typeof error === "object" && "error" in error) {
                const errorObj = error as { error?: { error?: string } };
                if (errorObj.error?.error) {
                    this.notificationService.error(errorObj.error.error);
                    return;
                }
            }

            this.notificationService.error(
                this.translate.instant("equipment.messages.saveError")
            );
        } finally {
            this.isSaving = false;
        }
    }

    /**
     * Create new equipment.
     */
    private async createEquipment(data: EquipmentCreateRequest): Promise<void> {
        const response = await firstValueFrom(this.equipmentService.createEquipment(data));

        this.notificationService.success(
            this.translate.instant("equipment.messages.createSuccess")
        );

        this.router.navigate(["/equipment-gallery"], {
            state: {
                selectedId: response.data.id,
                returnPage: this.navigationState?.["returnPage"] || 0,
                searchTerm: this.navigationState?.["searchTerm"] || "",
                selectedType: this.navigationState?.["selectedType"] || "all",
                selectedStatus: this.navigationState?.["selectedStatus"] || "all"
            }
        });
    }

    /**
     * Update existing equipment.
     */
    private async updateEquipment(data: EquipmentUpdateRequest): Promise<void> {
        if (!this.equipmentId) return;

        await firstValueFrom(
            this.equipmentService.updateEquipment(this.equipmentId, data)
        );

        this.notificationService.success(
            this.translate.instant("equipment.messages.updateSuccess")
        );

        this.router.navigate(["/equipment-gallery"], {
            state: {
                selectedId: this.equipmentId,
                returnPage: this.navigationState?.["returnPage"] || 0,
                searchTerm: this.navigationState?.["searchTerm"] || "",
                selectedType: this.navigationState?.["selectedType"] || "all",
                selectedStatus: this.navigationState?.["selectedStatus"] || "all"
            }
        });
    }

    /**
     * Cancel editing and return to gallery.
     */
    onCancel(): void {
        this.router.navigate(["/equipment-gallery"], {
            state: {
                returnPage: this.navigationState?.["returnPage"] || 0,
                searchTerm: this.navigationState?.["searchTerm"] || "",
                selectedType: this.navigationState?.["selectedType"] || "all",
                selectedStatus: this.navigationState?.["selectedStatus"] || "all"
            }
        });
    }

    /**
     * Get error message for a form field.
     */
    getFieldError(fieldName: string): string {
        const control = this.equipmentForm.get(fieldName);
        if (!control || !control.errors || !control.touched) {
            return "";
        }

        if (control.errors["required"]) {
            return this.translate.instant("equipment.validation.required");
        }
        if (control.errors["maxlength"]) {
            const maxLength = control.errors["maxlength"].requiredLength;
            return this.translate.instant("equipment.validation.maxLength", {max: maxLength});
        }

        return "";
    }

    // ============================================================
    // Attachment Methods
    // ============================================================

    /**
     * Load attachments for current equipment.
     */
    loadAttachments(): void {
        if (!this.equipmentId) return;

        this.equipmentService.getAttachments(this.equipmentId).subscribe({
            next: (response) => {
                this.attachments = response.data;
            },
            error: (error) => {
                console.error("Failed to load attachments:", error);
            }
        });
    }

    /**
     * Handle file selection and upload.
     */
    onFileSelect(event: Event): void {
        const input = event.target as HTMLInputElement;
        if (!input.files || input.files.length === 0 || !this.equipmentId) return;

        const file = input.files[0];
        this.uploadFile(file);

        // Reset input to allow selecting the same file again
        input.value = "";
    }

    /**
     * Upload a single file.
     */
    private uploadFile(file: File): void {
        if (!this.equipmentId) return;

        this.isUploadingFile = true;

        this.equipmentService.uploadAttachment(this.equipmentId, file).subscribe({
            next: () => {
                this.notificationService.success(
                    this.translate.instant("equipment.attachments.uploadSuccess")
                );
                this.loadAttachments();
                this.isUploadingFile = false;
            },
            error: (error) => {
                console.error("Upload failed:", error);
                const errorMsg = error.error?.error || this.translate.instant("equipment.attachments.uploadError");
                this.notificationService.error(errorMsg);
                this.isUploadingFile = false;
            }
        });
    }

    /**
     * Delete an attachment.
     */
    deleteAttachment(attachment: EquipmentAttachment): void {
        if (!this.equipmentId) return;

        // Simple confirmation
        if (!confirm(this.translate.instant("equipment.attachments.deleteConfirm", {filename: attachment.filename}))) {
            return;
        }

        this.equipmentService.deleteAttachment(this.equipmentId, attachment.id).subscribe({
            next: () => {
                this.notificationService.success(
                    this.translate.instant("equipment.attachments.deleteSuccess")
                );
                this.loadAttachments();
            },
            error: (error) => {
                console.error("Delete failed:", error);
                this.notificationService.error(
                    this.translate.instant("equipment.attachments.deleteError")
                );
            }
        });
    }

    /**
     * Download an attachment.
     */
    downloadAttachment(attachment: EquipmentAttachment): void {
        if (!this.equipmentId) return;

        this.equipmentService.downloadAttachment(this.equipmentId, attachment.id).subscribe({
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
