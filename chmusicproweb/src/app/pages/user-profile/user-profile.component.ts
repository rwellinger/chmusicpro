import {Component, inject, OnDestroy, OnInit} from "@angular/core";
import {CommonModule} from "@angular/common";
import {FormBuilder, FormGroup, ReactiveFormsModule, Validators} from "@angular/forms";
import {MatDialog} from "@angular/material/dialog";
import {MatButtonModule} from "@angular/material/button";
import {MatFormFieldModule} from "@angular/material/form-field";
import {MatInputModule} from "@angular/material/input";
import {MatCardModule} from "@angular/material/card";
import {MatIconModule} from "@angular/material/icon";
import {MatSnackBarModule} from "@angular/material/snack-bar";
import {MatSelectModule} from "@angular/material/select";
import {TranslateModule, TranslateService} from "@ngx-translate/core";
import {Subject} from "rxjs";
import {takeUntil} from "rxjs/operators";

import {PasswordChangeModalComponent} from "../../components/password-change-modal/password-change-modal.component";

import {UserService} from "../../services/business/user.service";
import {AuthService} from "../../services/business/auth.service";
import {NotificationService} from "../../services/ui/notification.service";
import {UserSettingsService} from "../../services/user-settings.service";
import {LanguageService} from "../../services/language.service";
import {CostService, MonthlyCosts} from "../../services/config/cost.service";
import {User} from "../../models/user.model";
import {Language, UserSettings} from "../../models/user-settings.model";

@Component({
    selector: "app-user-profile",
    standalone: true,
    imports: [
        CommonModule,
        ReactiveFormsModule,
        MatButtonModule,
        MatFormFieldModule,
        MatInputModule,
        MatCardModule,
        MatIconModule,
        MatSnackBarModule,
        MatSelectModule,
        TranslateModule
    ],
    templateUrl: "./user-profile.component.html",
    styleUrl: "./user-profile.component.scss"
})
export class UserProfileComponent implements OnInit, OnDestroy {
    userForm: FormGroup;
    settingsForm: FormGroup;
    currentUser: User | null = null;
    currentSettings: UserSettings | null = null;
    openaiCosts: MonthlyCosts | null = null;
    openaiAllTimeCosts: MonthlyCosts | null = null;
    isLoading = false;
    isLoadingCosts = false;
    isEditing = false;
    userDisplayName = "Unknown User"; // Computed property to avoid method calls in template
    availableLanguages: { code: Language, name: string }[] = []; // Computed property to avoid method calls in template

    private destroy$ = new Subject<void>();
    private fb = inject(FormBuilder);
    private dialog = inject(MatDialog);
    private userService = inject(UserService);
    private authService = inject(AuthService);
    private notificationService = inject(NotificationService);
    private settingsService = inject(UserSettingsService);
    private languageService = inject(LanguageService);
    private costService = inject(CostService);
    private translate = inject(TranslateService);

    constructor() {
        this.userForm = this.fb.group({
            first_name: ["", [Validators.required, Validators.minLength(2)]],
            last_name: ["", [Validators.required, Validators.minLength(2)]],
            artist_name: [""]
        });

        this.settingsForm = this.fb.group({
            songListLimit: [10, [Validators.required, Validators.min(5), Validators.max(100)]],
            imageListLimit: [10, [Validators.required, Validators.min(5), Validators.max(100)]],
            promptListLimit: [10, [Validators.required, Validators.min(5), Validators.max(100)]],
            sketchListLimit: [8, [Validators.required, Validators.min(5), Validators.max(100)]],
            equipmentListLimit: [7, [Validators.required, Validators.min(5), Validators.max(100)]],
            language: ["en", [Validators.required]]
        });
    }

    ngOnInit(): void {
        this.availableLanguages = this.languageService.getAvailableLanguages(); // Initialize once
        this.loadUserProfile();
        this.subscribeToAuthState();
        this.loadUserSettings();
        this.loadOpenAICosts();
        this.loadOpenAIAllTimeCosts();
    }

    ngOnDestroy(): void {
        this.destroy$.next();
        this.destroy$.complete();
    }

    /**
     * Subscribe to auth state changes
     */
    private subscribeToAuthState(): void {
        this.authService.authState$
            .pipe(takeUntil(this.destroy$))
            .subscribe(authState => {
                this.currentUser = authState.user;
                if (this.currentUser) {
                    this.updateFormValues();
                    this.updateUserDisplayName();
                }
            });
    }

    /**
     * Load user profile data
     */
    private loadUserProfile(): void {
        this.isLoading = true;

        this.userService.getCurrentUserProfile()
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: (user) => {
                    this.currentUser = user;
                    this.updateFormValues();
                    this.updateUserDisplayName();
                    this.isLoading = false;
                },
                error: (error) => {
                    console.error("Error loading user profile:", error);
                    this.notificationService.error(this.translate.instant("userProfile.errors.errorLoadingProfile"));
                    this.isLoading = false;
                }
            });
    }

    /**
     * Update form values from current user data
     */
    private updateFormValues(): void {
        if (this.currentUser) {
            this.userForm.patchValue({
                first_name: this.currentUser.first_name || "",
                last_name: this.currentUser.last_name || "",
                artist_name: this.currentUser.artist_name || ""
            });
        }
    }

    /**
     * Get error message for form fields
     */
    public getErrorMessage(fieldName: string): string {
        const field = this.userForm.get(fieldName);
        const fieldDisplayName = this.getFieldDisplayName(fieldName);

        if (field?.hasError("required")) {
            return this.translate.instant("userProfile.errors.required", {field: fieldDisplayName});
        }

        if (field?.hasError("minlength")) {
            const requiredLength = field.errors?.["minlength"]?.requiredLength;
            return this.translate.instant("userProfile.errors.minLength", {
                field: fieldDisplayName,
                length: requiredLength
            });
        }

        return "";
    }

    /**
     * Get display name for form fields
     */
    private getFieldDisplayName(fieldName: string): string {
        switch (fieldName) {
            case "first_name":
                return this.translate.instant("userProfile.fieldNames.firstName");
            case "last_name":
                return this.translate.instant("userProfile.fieldNames.lastName");
            case "artist_name":
                return this.translate.instant("userProfile.fieldNames.artistName");
            default:
                return fieldName;
        }
    }

    /**
     * Check if field has error
     */
    public hasFieldError(fieldName: string): boolean {
        const field = this.userForm.get(fieldName);
        return !!(field && field.invalid && (field.dirty || field.touched));
    }

    /**
     * Start editing mode
     */
    public startEditing(): void {
        this.isEditing = true;
    }

    /**
     * Cancel editing and reset form
     */
    public cancelEditing(): void {
        this.isEditing = false;
        this.updateFormValues();
    }

    /**
     * Save user profile changes
     */
    public saveProfile(): void {
        if (this.userForm.valid && !this.isLoading) {
            this.isLoading = true;

            const formData = this.userForm.value;

            this.userService.updateCurrentUserProfile(formData)
                .pipe(takeUntil(this.destroy$))
                .subscribe({
                    next: (updatedUser) => {
                        this.currentUser = updatedUser;
                        this.updateUserDisplayName(); // Update display name after save
                        this.isEditing = false;
                        this.isLoading = false;
                    },
                    error: (error) => {
                        console.error("Error updating profile:", error);
                        this.notificationService.error(error.message || this.translate.instant("userProfile.errors.errorUpdatingProfile"));
                        this.isLoading = false;
                    }
                });
        }
    }

    /**
     * Open password change modal
     */
    public openPasswordChangeModal(): void {
        const dialogRef = this.dialog.open(PasswordChangeModalComponent, {
            width: "450px",
            maxWidth: "90vw",
            disableClose: true,
            panelClass: "password-modal-panel"
        });

        dialogRef.afterClosed()
            .pipe(takeUntil(this.destroy$))
            .subscribe(() => {
            });
    }

    /**
     * Update userDisplayName property based on current user
     * Called when user changes to avoid method calls in template
     */
    private updateUserDisplayName(): void {
        if (!this.currentUser) {
            this.userDisplayName = this.translate.instant("userProfile.unknownUser");
            return;
        }

        if (this.currentUser.first_name && this.currentUser.last_name) {
            this.userDisplayName = `${this.currentUser.first_name} ${this.currentUser.last_name}`;
            return;
        }

        if (this.currentUser.first_name) {
            this.userDisplayName = this.currentUser.first_name;
            return;
        }

        this.userDisplayName = this.currentUser.email.split("@")[0];
    }

    /**
     * Format date for display
     */
    public formatDate(dateString: string): string {
        if (!dateString) return this.translate.instant("userProfile.unknown");

        const date = new Date(dateString);
        return date.toLocaleDateString("en-US", {
            year: "numeric",
            month: "long",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit"
        });
    }

    /**
     * Load user settings from the service
     */
    private loadUserSettings(): void {
        this.settingsService.getSettings()
            .pipe(takeUntil(this.destroy$))
            .subscribe(settings => {
                this.currentSettings = settings;
                this.settingsForm.patchValue(settings);
            });
    }

    /**
     * Update song list limit setting
     */
    public updateSongListLimit(): void {
        const value = this.settingsForm.get("songListLimit")?.value;
        if (value && value >= 5 && value <= 100) {
            this.settingsService.updateSongListLimit(value);
            this.notificationService.success(this.translate.instant("userProfile.notifications.songListLimitUpdated"));
        }
    }

    /**
     * Update image list limit setting
     */
    public updateImageListLimit(): void {
        const value = this.settingsForm.get("imageListLimit")?.value;
        if (value && value >= 5 && value <= 100) {
            this.settingsService.updateImageListLimit(value);
            this.notificationService.success(this.translate.instant("userProfile.notifications.imageListLimitUpdated"));
        }
    }

    /**
     * Update prompt list limit setting
     */
    public updatePromptListLimit(): void {
        const value = this.settingsForm.get("promptListLimit")?.value;
        if (value && value >= 5 && value <= 100) {
            this.settingsService.updatePromptListLimit(value);
            this.notificationService.success(this.translate.instant("userProfile.notifications.promptListLimitUpdated"));
        }
    }

    /**
     * Update sketch list limit setting
     */
    public updateSketchListLimit(): void {
        const value = this.settingsForm.get("sketchListLimit")?.value;
        if (value && value >= 5 && value <= 100) {
            this.settingsService.updateSketchListLimit(value);
            this.notificationService.success(this.translate.instant("userProfile.notifications.sketchListLimitUpdated"));
        }
    }

    /**
     * Update equipment list limit setting
     */
    public updateEquipmentListLimit(): void {
        const value = this.settingsForm.get("equipmentListLimit")?.value;
        if (value && value >= 5 && value <= 100) {
            this.settingsService.updateEquipmentListLimit(value);
            this.notificationService.success(this.translate.instant("userProfile.notifications.equipmentListLimitUpdated"));
        }
    }

    /**
     * Reset settings to defaults
     */
    public resetSettingsToDefaults(): void {
        this.settingsService.resetToDefaults();
        this.notificationService.success(this.translate.instant("userProfile.notifications.settingsReset"));
    }

    /**
     * Update language setting
     */
    public updateLanguage(): void {
        const value = this.settingsForm.get("language")?.value as Language;
        if (value) {
            this.languageService.changeLanguage(value);
            this.notificationService.success(this.translate.instant("userProfile.notifications.languageUpdated"));
        }
    }

    /**
     * Get available languages
     */
    public getAvailableLanguages(): { code: Language, name: string }[] {
        return this.languageService.getAvailableLanguages();
    }

    /**
     * Get current language
     */
    public getCurrentLanguage(): Language {
        return this.languageService.getCurrentLanguage();
    }

    /**
     * Load OpenAI costs for current month
     */
    private loadOpenAICosts(): void {
        this.isLoadingCosts = true;
        this.costService.getCurrentMonthCosts()
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: (data) => {
                    this.openaiCosts = data.costs;
                    this.isLoadingCosts = false;
                },
                error: (error) => {
                    console.error("Failed to load OpenAI costs:", error);
                    this.isLoadingCosts = false;
                }
            });
    }

    /**
     * Load OpenAI all-time costs
     */
    private loadOpenAIAllTimeCosts(): void {
        this.costService.getAllTimeCosts()
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: (data) => {
                    this.openaiAllTimeCosts = data.costs;
                },
                error: (error) => {
                    console.error("Failed to load OpenAI all-time costs:", error);
                }
            });
    }
}
