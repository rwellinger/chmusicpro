import {Component, inject, OnDestroy, OnInit} from "@angular/core";
import {CommonModule} from "@angular/common";
import {FormBuilder, FormGroup, ReactiveFormsModule, Validators} from "@angular/forms";
import {ActivatedRoute, Router} from "@angular/router";
import {firstValueFrom, Subject, takeUntil} from "rxjs";
import {TranslateModule, TranslateService} from "@ngx-translate/core";
import {MatCardModule} from "@angular/material/card";
import {MatFormFieldModule} from "@angular/material/form-field";
import {MatInputModule} from "@angular/material/input";
import {MatSelectModule} from "@angular/material/select";
import {MatDatepickerModule} from "@angular/material/datepicker";
import {MatNativeDateModule} from "@angular/material/core";
import {MatDialog} from "@angular/material/dialog";

import {SongReleaseService} from "../../services/business/song-release.service";
import {SongProjectService} from "../../services/business/song-project.service";
import {NotificationService} from "../../services/ui/notification.service";
import {ResourceBlobService} from "../../services/ui/resource-blob.service";
import {
    AssignToProjectDialogComponent
} from "../../dialogs/assign-to-project-dialog/assign-to-project-dialog.component";
import {ReleaseStatus, ReleaseType, SongRelease} from "../../models/song-release.model";

@Component({
    selector: "app-song-release-editor",
    standalone: true,
    imports: [
        CommonModule,
        ReactiveFormsModule,
        TranslateModule,
        MatCardModule,
        MatFormFieldModule,
        MatInputModule,
        MatSelectModule,
        MatDatepickerModule,
        MatNativeDateModule
    ],
    templateUrl: "./song-release-editor.component.html",
    styleUrl: "./song-release-editor.component.scss"
})
export class SongReleaseEditorComponent implements OnInit, OnDestroy {
    releaseForm!: FormGroup;
    isEditMode = false;
    isLoading = false;
    isSaving = false;
    releaseId: string | null = null;
    selectedRelease: SongRelease | null = null;

    // Cover Image
    selectedCoverFile: File | null = null;
    coverPreviewUrl: string | null = null;

    // Project Assignment
    assignedProjectIds: string[] = [];
    assignedProjectNames: string[] = [];

    // Enums for template
    ReleaseType = ReleaseType;
    ReleaseStatus = ReleaseStatus;

    // Available enum values
    releaseTypes = Object.values(ReleaseType);
    releaseStatuses = Object.values(ReleaseStatus);

    // Navigation state
    private navigationState: any = null;

    private destroy$ = new Subject<void>();

    private fb = inject(FormBuilder);
    private route = inject(ActivatedRoute);
    private router = inject(Router);
    private releaseService = inject(SongReleaseService);
    private projectService = inject(SongProjectService);
    private notificationService = inject(NotificationService);
    private resourceBlobService = inject(ResourceBlobService);
    private translate = inject(TranslateService);
    private dialog = inject(MatDialog);

    constructor() {
        // Capture navigation state in constructor
        const navigation = this.router.getCurrentNavigation();
        this.navigationState = navigation?.extras?.state;
    }

    ngOnInit(): void {
        this.initializeForm();

        // Check if edit mode
        this.route.paramMap.pipe(takeUntil(this.destroy$)).subscribe(params => {
            this.releaseId = params.get("id");
            this.isEditMode = !!this.releaseId;

            if (this.isEditMode && this.releaseId) {
                this.loadRelease(this.releaseId);
            }
        });

        // Subscribe to status changes for conditional validators
        this.releaseForm.get("status")?.valueChanges
            .pipe(takeUntil(this.destroy$))
            .subscribe(() => this.updateStatusValidators());
    }

    ngOnDestroy(): void {
        this.destroy$.next();
        this.destroy$.complete();
    }

    /**
     * Initialize reactive form with validators
     */
    private initializeForm(): void {
        this.releaseForm = this.fb.group({
            type: [ReleaseType.SINGLE, Validators.required],
            name: ["", [Validators.required, Validators.maxLength(200)]],
            genre: ["", [Validators.required, Validators.maxLength(100)]],
            status: [ReleaseStatus.DRAFT, Validators.required],
            description: ["", Validators.maxLength(2000)],
            tags: ["", Validators.maxLength(500)],
            upload_date: [null],
            release_date: [null],
            downtaken_date: [null],
            downtaken_reason: ["", Validators.maxLength(500)],
            rejected_reason: ["", Validators.maxLength(500)],
            upc: ["", Validators.maxLength(50)],
            isrc: ["", Validators.maxLength(50)],
            copyright_info: ["", Validators.maxLength(500)],
            smart_link: ["", Validators.maxLength(1000)]
        });
    }

    /**
     * Load release data in edit mode
     */
    private async loadRelease(releaseId: string): Promise<void> {
        this.isLoading = true;

        try {
            const response = await firstValueFrom(
                this.releaseService.getReleaseById(releaseId)
            );

            this.selectedRelease = response.data;

            // Patch form with release data
            this.releaseForm.patchValue({
                type: this.selectedRelease.type,
                name: this.selectedRelease.name,
                genre: this.selectedRelease.genre,
                status: this.selectedRelease.status,
                description: this.selectedRelease.description || "",
                tags: this.selectedRelease.tags || "",
                upload_date: this.selectedRelease.upload_date ? new Date(this.selectedRelease.upload_date) : null,
                release_date: this.selectedRelease.release_date ? new Date(this.selectedRelease.release_date) : null,
                downtaken_date: this.selectedRelease.downtaken_date ? new Date(this.selectedRelease.downtaken_date) : null,
                downtaken_reason: this.selectedRelease.downtaken_reason || "",
                rejected_reason: this.selectedRelease.rejected_reason || "",
                upc: this.selectedRelease.upc || "",
                isrc: this.selectedRelease.isrc || "",
                copyright_info: this.selectedRelease.copyright_info || "",
                smart_link: this.selectedRelease.smart_link || ""
            });

            // Load assigned projects
            if (this.selectedRelease.assigned_projects) {
                this.assignedProjectIds = this.selectedRelease.assigned_projects.map(p => p.id);
                this.assignedProjectNames = this.selectedRelease.assigned_projects.map(p => p.project_name);
            }

            // Load cover preview if exists
            // CRITICAL: Use blob URL for authenticated image access
            if (this.selectedRelease.cover_url) {
                this.resourceBlobService.getResourceBlobUrl(this.selectedRelease.cover_url)
                    .pipe(takeUntil(this.destroy$))
                    .subscribe({
                        next: (blobUrl) => {
                            this.coverPreviewUrl = blobUrl;
                        },
                        error: () => {
                            this.coverPreviewUrl = "";
                        }
                    });
            }

            // Update validators based on status
            this.updateStatusValidators();

        } catch (error) {
            console.error("Failed to load release:", error);
            this.notificationService.error(
                this.translate.instant("songRelease.messages.loadError")
            );
            this.goBack();
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * Update form validators based on current status
     * PATTERN from song-generator.component.ts Lines 462-477
     */
    private updateStatusValidators(): void {
        const status = this.releaseForm.get("status")?.value;

        // Clear all optional validators first
        this.clearOptionalValidators();

        // Apply status-specific required fields
        switch (status) {
            case ReleaseStatus.UPLOADED: {
                this.addRequiredValidator("upload_date");
                // release_date is OPTIONAL for uploaded (might not be planned yet)
                // UPC/ISRC are OPTIONAL (not all platforms require them, e.g., SoundCloud)
                this.addRequiredValidator("copyright_info");

                // Auto-fill upload_date with today if empty
                const uploadDateControl = this.releaseForm.get("upload_date");
                if (uploadDateControl && !uploadDateControl.value) {
                    uploadDateControl.setValue(new Date());
                }
                break;
            }

            case ReleaseStatus.RELEASED: {
                this.addRequiredValidator("upload_date");
                this.addRequiredValidator("release_date"); // REQUIRED after release
                // UPC/ISRC are OPTIONAL (not all platforms require them)
                this.addRequiredValidator("copyright_info");

                // Auto-fill release_date with today if empty
                const releaseDateControl = this.releaseForm.get("release_date");
                if (releaseDateControl && !releaseDateControl.value) {
                    releaseDateControl.setValue(new Date());
                }
                break;
            }

            case ReleaseStatus.REJECTED:
                this.addRequiredValidator("rejected_reason");
                break;

            case ReleaseStatus.DOWNTAKEN: {
                this.addRequiredValidator("downtaken_date");
                this.addRequiredValidator("downtaken_reason");

                // Auto-fill downtaken_date with today if empty
                const downtakenDateControl = this.releaseForm.get("downtaken_date");
                if (downtakenDateControl && !downtakenDateControl.value) {
                    downtakenDateControl.setValue(new Date());
                }
                break;
            }
        }
    }

    /**
     * Clear optional validators for status-dependent fields
     */
    private clearOptionalValidators(): void {
        const optionalFields = [
            "upload_date",
            "release_date",
            "downtaken_date",
            "downtaken_reason",
            "rejected_reason",
            "upc",
            "isrc",
            "copyright_info"
        ];

        optionalFields.forEach(field => {
            const control = this.releaseForm.get(field);
            if (control) {
                control.clearValidators();
                // Re-add maxLength validators if applicable
                if (field === "downtaken_reason" || field === "rejected_reason") {
                    control.setValidators(Validators.maxLength(500));
                } else if (field === "copyright_info") {
                    control.setValidators(Validators.maxLength(500));
                } else if (field === "upc" || field === "isrc") {
                    control.setValidators(Validators.maxLength(50));
                }
                control.updateValueAndValidity();
            }
        });
    }

    /**
     * Add required validator to a specific field
     */
    private addRequiredValidator(fieldName: string): void {
        const control = this.releaseForm.get(fieldName);
        if (control) {
            const existingValidators = control.validator ? [control.validator] : [];
            control.setValidators([Validators.required, ...existingValidators]);
            control.updateValueAndValidity();
        }
    }

    /**
     * Open assign to project dialog
     */
    async openAssignToProjectDialog(): Promise<void> {
        const releaseType = this.releaseForm.get("type")?.value;

        if (!releaseType) {
            this.notificationService.error(
                this.translate.instant("songRelease.validation.selectTypeFirst")
            );
            return;
        }

        const dialogRef = this.dialog.open(AssignToProjectDialogComponent, {
            width: "600px",
            data: {
                assetType: "release",
                assetId: this.releaseId || "new",
                releaseType: releaseType,
                currentProjectIds: this.assignedProjectIds
            }
        });

        const result = await firstValueFrom(dialogRef.afterClosed());

        if (result && result.success) {
            this.assignedProjectIds = result.projectIds || [];
            this.assignedProjectNames = result.projectNames || [];

            // If Single and project selected, offer to use project name
            if (releaseType === ReleaseType.SINGLE && this.assignedProjectNames.length === 1) {
                this.offerProjectNameForSingle();
            }

            this.notificationService.success(
                this.translate.instant("songRelease.messages.projectsAssigned")
            );
        }
    }

    /**
     * Offer to use project data (name, description, tags) for Single release
     */
    private async offerProjectNameForSingle(): Promise<void> {
        const currentName = this.releaseForm.get("name")?.value;

        // Always offer if exactly 1 project is assigned (even if name already exists)
        if (this.assignedProjectNames.length === 1 && this.assignedProjectIds.length === 1) {
            const projectName = this.assignedProjectNames[0];

            // Skip if project name is already the release name
            if (currentName === projectName) {
                return;
            }

            const message = this.translate.instant("songRelease.messages.useProjectName", {
                projectName: projectName
            });

            if (confirm(message)) {
                // Fetch full project details to get description and tags
                try {
                    const projectResponse = await firstValueFrom(
                        this.projectService.getProjectById(this.assignedProjectIds[0])
                    );

                    if (projectResponse?.data) {
                        const project = projectResponse.data;

                        // Patch name, description, and tags
                        this.releaseForm.patchValue({
                            name: projectName,
                            description: project.description || "",
                            tags: Array.isArray(project.tags) ? project.tags.join(", ") : ""
                        });
                    }
                } catch (error) {
                    console.error("Failed to load project details:", error);
                    // Fallback: just set the name
                    this.releaseForm.patchValue({name: projectName});
                }
            }
        }
    }

    /**
     * Handle cover file selection
     */
    async onCoverFileSelected(event: Event): Promise<void> {
        const input = event.target as HTMLInputElement;
        const file = input.files?.[0];

        if (!file) return;

        // Validate cover image (must be 200x200)
        const validation = await this.releaseService.validateCoverImage(file);

        if (!validation.valid) {
            this.notificationService.error(validation.error!);
            input.value = ""; // Clear input
            return;
        }

        this.selectedCoverFile = file;

        // Show preview
        const reader = new FileReader();
        reader.onload = (e) => {
            this.coverPreviewUrl = e.target?.result as string;
        };
        reader.readAsDataURL(file);
    }

    /**
     * Remove selected cover image
     */
    removeCoverImage(): void {
        this.selectedCoverFile = null;
        this.coverPreviewUrl = null;
    }

    /**
     * Validate status-specific required fields (frontend validation)
     */
    private validateStatusRequirements(): { valid: boolean; missingFields: string[] } {
        const status = this.releaseForm.get("status")?.value;
        const missingFields: string[] = [];

        // Check status-specific requirements
        switch (status) {
            case ReleaseStatus.UPLOADED:
                if (!this.releaseForm.get("upload_date")?.value) missingFields.push("Upload Date");
                if (!this.releaseForm.get("copyright_info")?.value) missingFields.push("Copyright Info");
                if (!this.coverPreviewUrl && !this.selectedCoverFile) missingFields.push("Cover Image");
                break;

            case ReleaseStatus.RELEASED:
                if (!this.releaseForm.get("upload_date")?.value) missingFields.push("Upload Date");
                if (!this.releaseForm.get("release_date")?.value) missingFields.push("Release Date");
                if (!this.releaseForm.get("copyright_info")?.value) missingFields.push("Copyright Info");
                if (!this.coverPreviewUrl && !this.selectedCoverFile) missingFields.push("Cover Image");
                break;

            case ReleaseStatus.REJECTED:
                if (!this.releaseForm.get("rejected_reason")?.value) missingFields.push("Rejected Reason");
                break;

            case ReleaseStatus.DOWNTAKEN:
                if (!this.releaseForm.get("downtaken_date")?.value) missingFields.push("Downtaken Date");
                if (!this.releaseForm.get("downtaken_reason")?.value) missingFields.push("Downtaken Reason");
                break;
        }

        return {valid: missingFields.length === 0, missingFields};
    }

    /**
     * Save release (create or update)
     */
    async save(): Promise<void> {
        if (this.releaseForm.invalid) {
            this.notificationService.error(
                this.translate.instant("songRelease.validation.invalidForm")
            );
            this.markFormGroupTouched(this.releaseForm);
            return;
        }

        // Validate project assignment
        if (this.assignedProjectIds.length === 0) {
            this.notificationService.error(
                this.translate.instant("songRelease.validation.noProjectAssigned")
            );
            return;
        }

        const releaseType = this.releaseForm.get("type")?.value;
        if (releaseType === ReleaseType.SINGLE && this.assignedProjectIds.length > 1) {
            this.notificationService.error(
                this.translate.instant("songRelease.validation.singleOneProject")
            );
            return;
        }

        // Frontend validation for status-specific requirements
        const validation = this.validateStatusRequirements();
        if (!validation.valid) {
            const status = this.releaseForm.get("status")?.value;
            this.notificationService.error(
                `Missing required fields for status '${status}': ${validation.missingFields.join(", ")}`
            );
            return;
        }

        this.isSaving = true;

        try {
            const formValue = this.releaseForm.value;

            // Format dates to YYYY-MM-DD (using local timezone, not UTC!)
            const formatDate = (date: Date | null): string | undefined => {
                if (!date) return undefined;
                if (!(date instanceof Date)) return undefined;

                // Use local timezone instead of UTC to avoid day-shifting
                const year = date.getFullYear();
                const month = String(date.getMonth() + 1).padStart(2, "0");
                const day = String(date.getDate()).padStart(2, "0");
                return `${year}-${month}-${day}`;
            };

            const releaseData = {
                type: formValue.type,
                name: formValue.name,
                genre: formValue.genre,
                status: formValue.status,
                description: formValue.description || undefined,
                tags: formValue.tags || undefined,
                upload_date: formatDate(formValue.upload_date),
                release_date: formatDate(formValue.release_date),
                downtaken_date: formatDate(formValue.downtaken_date),
                downtaken_reason: formValue.downtaken_reason || undefined,
                rejected_reason: formValue.rejected_reason || undefined,
                upc: formValue.upc || undefined,
                isrc: formValue.isrc || undefined,
                copyright_info: formValue.copyright_info || undefined,
                smart_link: formValue.smart_link || undefined,
                project_ids: this.assignedProjectIds
            };

            if (this.isEditMode && this.releaseId) {
                // Update existing release
                await firstValueFrom(
                    this.releaseService.updateRelease(this.releaseId, releaseData, this.selectedCoverFile || undefined)
                );

                this.notificationService.success(
                    this.translate.instant("songRelease.messages.updateSuccess")
                );
            } else {
                // Create new release
                await firstValueFrom(
                    this.releaseService.createRelease(releaseData, this.selectedCoverFile || undefined)
                );

                this.notificationService.success(
                    this.translate.instant("songRelease.messages.createSuccess")
                );
            }

            this.goBack();

        } catch (error: any) {
            console.error("Failed to save release:", error);

            // Show specific error message from backend if available
            let errorMessage = this.translate.instant("songRelease.messages.saveError");

            if (error?.error?.error) {
                // Backend returned specific error message
                errorMessage = error.error.error;
            } else if (error?.message) {
                // Generic HTTP error message
                errorMessage = error.message;
            }

            this.notificationService.error(errorMessage);
        } finally {
            this.isSaving = false;
        }
    }

    /**
     * Mark all form controls as touched to show validation errors
     */
    private markFormGroupTouched(formGroup: FormGroup): void {
        Object.keys(formGroup.controls).forEach(key => {
            const control = formGroup.get(key);
            control?.markAsTouched();
        });
    }

    /**
     * Cancel and go back to gallery
     */
    cancel(): void {
        if (this.releaseForm.dirty) {
            const confirmed = confirm(
                this.translate.instant("songRelease.messages.unsavedChanges")
            );
            if (!confirmed) return;
        }

        this.goBack();
    }

    /**
     * Navigate back to gallery
     */
    private goBack(): void {
        this.router.navigate(["/song-releases"], {
            state: this.navigationState
        });
    }

    /**
     * Check if a field should be shown based on status
     */
    shouldShowField(fieldName: string): boolean {
        const status = this.releaseForm.get("status")?.value;

        switch (fieldName) {
            case "upload_date":
            case "upc":
            case "copyright_info":
            case "smart_link":
                return [ReleaseStatus.UPLOADED, ReleaseStatus.RELEASED, ReleaseStatus.DOWNTAKEN].includes(status);

            case "release_date":
                // Release date = planned release date (optional for uploaded, required after release)
                return [ReleaseStatus.UPLOADED, ReleaseStatus.RELEASED, ReleaseStatus.DOWNTAKEN].includes(status);

            case "isrc":
                // ISRC only available after actual release
                return [ReleaseStatus.RELEASED, ReleaseStatus.DOWNTAKEN].includes(status);

            case "rejected_reason":
                return status === ReleaseStatus.REJECTED;

            case "downtaken_date":
            case "downtaken_reason":
                return status === ReleaseStatus.DOWNTAKEN;

            default:
                return true;
        }
    }

    /**
     * Get field error message
     */
    getFieldError(fieldName: string): string {
        const control = this.releaseForm.get(fieldName);

        if (control?.hasError("required")) {
            return this.translate.instant("errors.required");
        }

        if (control?.hasError("maxlength")) {
            const maxLength = control.errors?.["maxlength"]?.requiredLength;
            return this.translate.instant("errors.maxLength", {length: maxLength});
        }

        return "";
    }

    /**
     * Get initials from release name (e.g., "My Album" -> "MA")
     */
    getInitials(name: string): string {
        if (!name) return "?";

        const words = name.trim().split(/\s+/);

        if (words.length === 1) {
            // Single word: take first 2 characters
            return words[0].substring(0, 2).toUpperCase();
        }

        // Multiple words: take first letter of first 2 words
        return (words[0][0] + words[1][0]).toUpperCase();
    }

    /**
     * Generate consistent color from string (for cover placeholder)
     */
    getColorFromString(text: string): string {
        if (!text) return "#5a6268"; // Default gray

        // Simple hash function
        let hash = 0;
        for (let i = 0; i < text.length; i++) {
            hash = text.charCodeAt(i) + ((hash << 5) - hash);
        }

        // Generate color (pastel-like colors for better readability)
        const hue = Math.abs(hash % 360);
        const saturation = 60; // Medium saturation for pleasant colors
        const lightness = 55; // Medium lightness for good contrast

        return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
    }
}
