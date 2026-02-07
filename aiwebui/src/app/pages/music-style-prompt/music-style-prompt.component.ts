import {Component, HostListener, inject, OnInit, ViewChild, ViewEncapsulation} from "@angular/core";
import {FormBuilder, FormGroup, ReactiveFormsModule} from "@angular/forms";
import {CommonModule} from "@angular/common";
import {MatDialog} from "@angular/material/dialog";
import {TranslateModule, TranslateService} from "@ngx-translate/core";
import {ActivatedRoute, Router} from "@angular/router";
import {FormDataContext, SongService} from "../../services/business/song.service";
import {NotificationService} from "../../services/ui/notification.service";
import {ChatService} from "../../services/config/chat.service";
import {MatSnackBarModule} from "@angular/material/snack-bar";
import {MatCardModule} from "@angular/material/card";
import {ProgressService} from "../../services/ui/progress.service";
import {
    MusicStyleChooserInlineComponent
} from "../../components/music-style-chooser-inline/music-style-chooser-inline.component";
import {MusicStyleChooserService} from "../../services/music-style-chooser.service";

@Component({
    selector: "app-music-style-prompt",
    standalone: true,
    imports: [CommonModule, ReactiveFormsModule, MatSnackBarModule, MatCardModule, TranslateModule, MusicStyleChooserInlineComponent],
    templateUrl: "./music-style-prompt.component.html",
    styleUrl: "./music-style-prompt.component.scss",
    encapsulation: ViewEncapsulation.None
})
export class MusicStylePromptComponent implements OnInit {
    promptForm!: FormGroup;
    isEnhancingPrompt = false;
    isTranslatingPrompt = false;
    showEditDropdown = false;
    showEnhancerDropdown = false;
    lastSearchReplaceState: string | null = null;
    currentMode: "auto" | "manual" = "auto";
    isStyleChooserCollapsed = false;

    // Context for form data storage (song-generator or sketch-creator)
    private context: FormDataContext = "song-generator";

    // State from navigation (when called from sketch editor)
    private isFromSketch = false;
    private isEditMode = false;
    private currentSketchId: string | null = null;
    private sketchFormData: any = null;
    private navigationState: any = null;

    @ViewChild(MusicStyleChooserInlineComponent) styleChooser!: MusicStyleChooserInlineComponent;

    private fb = inject(FormBuilder);
    private songService = inject(SongService);
    private musicStyleService = inject(MusicStyleChooserService);
    private notificationService = inject(NotificationService);
    private chatService = inject(ChatService);
    private progressService = inject(ProgressService);
    private dialog = inject(MatDialog);
    private translate = inject(TranslateService);
    private route = inject(ActivatedRoute);
    private router = inject(Router);

    constructor() {
        // IMPORTANT: getCurrentNavigation() must be called in constructor!
        const navigation = this.router.getCurrentNavigation();
        this.navigationState = navigation?.extras?.state;
    }

    get isAnyOperationInProgress(): boolean {
        return this.isEnhancingPrompt || this.isTranslatingPrompt;
    }

    get characterCount(): number {
        return this.promptForm.get("prompt")?.value?.length || 0;
    }

    get canUndo(): boolean {
        return this.lastSearchReplaceState !== null;
    }

    get isFromSketchCreator(): boolean {
        return this.isFromSketch;
    }

    applyChanges(): void {
        // Update prompt in form data and navigate back
        const updatedFormData = {
            ...this.sketchFormData,
            prompt: this.promptForm.get("prompt")?.value || ""
        };

        this.navigateBackToSketchCreator(updatedFormData);

        this.notificationService.success(
            this.translate.instant("musicStylePrompt.changesApplied")
        );
    }

    cancelChanges(): void {
        // Discard changes and navigate back with original data
        this.navigateBackToSketchCreator(this.sketchFormData);

        this.notificationService.info(
            this.translate.instant("musicStylePrompt.changesCancelled")
        );
    }

    private navigateBackToSketchCreator(formData: any): void {
        // Navigate back with form data
        if (this.isEditMode && this.currentSketchId) {
            this.router.navigate(["/song-sketch-creator"], {
                state: {
                    editMode: true,
                    sketchId: this.currentSketchId,
                    formData: formData
                }
            });
        } else {
            this.router.navigate(["/song-sketch-creator"], {
                state: {
                    formData: formData
                }
            });
        }
    }

    ngOnInit() {
        // Check if coming from sketch creator via router state
        if (this.navigationState?.["context"] === "sketch") {
            this.isFromSketch = true;
            this.isEditMode = this.navigationState["editMode"] || false;
            this.currentSketchId = this.navigationState["sketchId"] || null;
            this.sketchFormData = this.navigationState["formData"] || {};
            this.context = "sketch-creator";
        } else {
            // Song generator mode
            this.context = "song-generator";
        }

        this.promptForm = this.fb.group({
            prompt: [""]
        });

        // Load prompt based on context
        if (this.isFromSketch && this.sketchFormData?.prompt) {
            // From sketch: load prompt from router state
            this.promptForm.patchValue({prompt: this.sketchFormData.prompt});

            // Try to parse the prompt to detect auto-mode pattern
            const parsed = this.musicStyleService.parsePromptToSelections(this.sketchFormData.prompt);

            if (parsed?.isAutoMode) {
                // Pattern recognized - switch to auto mode and restore selections
                this.currentMode = "auto";
                this.musicStyleService.saveConfig(parsed.config);
            } else {
                // No pattern match - default to manual mode and clear selections
                this.switchToManualMode();
                // Reset config to avoid old buttons staying active
                this.musicStyleService.saveConfig({
                    selectedStyles: [],
                    selectedInstruments: [],
                    selectedThemes: [],
                    lastModified: new Date()
                });
            }
        } else if (!this.isFromSketch) {
            // Song generator mode: load from localStorage
            const savedData = this.songService.loadFormData(this.context);
            if (savedData.prompt) {
                this.promptForm.patchValue({prompt: savedData.prompt});
            }

            // Auto-save prompt on changes (only for song generator)
            this.promptForm.valueChanges.subscribe(value => {
                this.savePrompt(value.prompt);
            });
        }
    }

    @HostListener("document:click", ["$event"])
    onDocumentClick(event: MouseEvent): void {
        const target = event.target as HTMLElement;
        const clickedInEditDropdown = target.closest(".edit-dropdown-container");
        const clickedInEnhancerDropdown = target.closest(".enhancer-dropdown-container");

        if (!clickedInEditDropdown && this.showEditDropdown) {
            this.showEditDropdown = false;
        }

        if (!clickedInEnhancerDropdown && this.showEnhancerDropdown) {
            this.showEnhancerDropdown = false;
        }
    }

    private savePrompt(prompt: string): void {
        // Load existing data from context-aware storage and update only prompt
        const existingData = this.songService.loadFormData(this.context);
        this.songService.saveFormData({
            ...existingData,
            prompt: prompt
        }, this.context);
    }

    clearPrompt(): void {
        this.promptForm.patchValue({prompt: ""});
        // Reset Style Chooser as well
        if (this.styleChooser) {
            this.styleChooser.reset();
        }
        // Switch back to auto-mode
        this.switchToAutoMode();
        this.notificationService.success(this.translate.instant("musicStylePrompt.cleared"));
    }

    async enhancePrompt() {
        const currentPrompt = this.promptForm.get("prompt")?.value?.trim();
        if (!currentPrompt) {
            this.notificationService.error(this.translate.instant("musicStylePrompt.errors.promptRequired"));
            return;
        }

        this.switchToManualMode();
        this.isEnhancingPrompt = true;
        this.promptForm.get("prompt")?.disable();
        try {
            const enhancedPrompt = await this.progressService.executeWithProgress(
                () => this.chatService.improveMusicStylePrompt(currentPrompt),
                this.translate.instant("musicStylePrompt.progress.enhancing"),
                this.translate.instant("musicStylePrompt.progress.enhancingHint")
            );
            this.promptForm.patchValue({prompt: this.removeQuotes(enhancedPrompt)});
            this.notificationService.success(this.translate.instant("musicStylePrompt.success.promptEnhanced"));
        } catch (error: any) {
            this.notificationService.error(`Error enhancing prompt: ${error.message}`);
        } finally {
            this.isEnhancingPrompt = false;
            this.promptForm.get("prompt")?.enable();
        }
    }

    async enhanceSunoPrompt() {
        const currentPrompt = this.promptForm.get("prompt")?.value?.trim();
        if (!currentPrompt) {
            this.notificationService.error(this.translate.instant("musicStylePrompt.errors.promptRequired"));
            return;
        }

        // Detect gender from prompt text (from style chooser selections)
        let gender: "male" | "female" | undefined;
        if (currentPrompt.toLowerCase().includes("male-voice") || currentPrompt.toLowerCase().includes("male voice")) {
            gender = "male";
        } else if (currentPrompt.toLowerCase().includes("female-voice") || currentPrompt.toLowerCase().includes("female voice")) {
            gender = "female";
        }

        this.switchToManualMode();
        this.isEnhancingPrompt = true;
        this.promptForm.get("prompt")?.disable();
        try {
            const enhancedPrompt = await this.progressService.executeWithProgress(
                () => this.chatService.improveMusicStylePromptForSuno(currentPrompt, gender),
                this.translate.instant("musicStylePrompt.progress.enhancingSuno"),
                this.translate.instant("musicStylePrompt.progress.enhancingSunoHint")
            );
            this.promptForm.patchValue({prompt: this.removeQuotes(enhancedPrompt)});
            this.notificationService.success(this.translate.instant("musicStylePrompt.success.promptEnhancedSuno"));
        } catch (error: any) {
            this.notificationService.error(`Error enhancing prompt for Suno: ${error.message}`);
        } finally {
            this.isEnhancingPrompt = false;
            this.promptForm.get("prompt")?.enable();
        }
    }

    async translatePrompt() {
        const currentPrompt = this.promptForm.get("prompt")?.value?.trim();
        if (!currentPrompt) {
            this.notificationService.error(this.translate.instant("musicStylePrompt.errors.promptRequired"));
            return;
        }

        this.switchToManualMode();
        this.isTranslatingPrompt = true;
        this.promptForm.get("prompt")?.disable();
        try {
            const translatedPrompt = await this.progressService.executeWithProgress(
                () => this.chatService.translateMusicStylePrompt(currentPrompt),
                this.translate.instant("musicStylePrompt.progress.translating"),
                this.translate.instant("musicStylePrompt.progress.translatingHint")
            );
            this.promptForm.patchValue({prompt: this.removeQuotes(translatedPrompt)});
            this.notificationService.success(this.translate.instant("musicStylePrompt.success.promptTranslated"));
        } catch (error: any) {
            this.notificationService.error(`Error translating prompt: ${error.message}`);
        } finally {
            this.isTranslatingPrompt = false;
            this.promptForm.get("prompt")?.enable();
        }
    }

    private removeQuotes(text: string): string {
        if (!text) return text;
        return text.replace(/^["']|["']$/g, "").trim();
    }

    toggleEditDropdown(): void {
        this.showEditDropdown = !this.showEditDropdown;
    }

    toggleEnhancerDropdown(): void {
        this.showEnhancerDropdown = !this.showEnhancerDropdown;
    }

    selectEditAction(action: string): void {
        this.showEditDropdown = false;

        switch (action) {
            case "searchReplace":
                this.openSearchReplaceDialog();
                break;
            case "undo":
                this.undoLastChange();
                break;
        }
    }

    selectEnhancerAction(action: "standard" | "suno"): void {
        this.showEnhancerDropdown = false;

        if (action === "standard") {
            this.enhancePrompt();
        } else {
            this.enhanceSunoPrompt();
        }
    }

    openSearchReplaceDialog(): void {
        const SearchReplaceDialogComponent = import("../../components/search-replace-dialog/search-replace-dialog.component")
            .then(m => m.SearchReplaceDialogComponent);

        SearchReplaceDialogComponent.then(component => {
            const dialogRef = this.dialog.open(component, {
                width: "500px",
                maxWidth: "90vw",
                disableClose: false,
                autoFocus: true
            });

            dialogRef.afterClosed().subscribe(result => {
                if (result && result.searchText) {
                    this.performSearchReplace(result.searchText, result.replaceText);
                }
            });
        });
    }

    private performSearchReplace(searchText: string, replaceText: string): void {
        const currentPrompt = this.promptForm.get("prompt")?.value || "";
        if (!currentPrompt.trim()) {
            return;
        }

        this.switchToManualMode();

        // Save state for undo
        this.lastSearchReplaceState = currentPrompt;

        // Perform replacement
        const updatedPrompt = currentPrompt.replaceAll(searchText, replaceText);

        // Calculate number of replacements
        const occurrences = (currentPrompt.match(new RegExp(this.escapeRegExp(searchText), "g")) || []).length;

        // Update form
        this.promptForm.patchValue({prompt: updatedPrompt});

        // Show success notification
        this.notificationService.success(
            this.translate.instant("musicStylePrompt.searchReplaceDialog.applied", {count: occurrences})
        );
    }

    private escapeRegExp(text: string): string {
        return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    }

    undoLastChange(): void {
        if (this.lastSearchReplaceState !== null) {
            this.promptForm.patchValue({prompt: this.lastSearchReplaceState});
            this.lastSearchReplaceState = null;
            this.notificationService.success(this.translate.instant("musicStylePrompt.undoApplied"));
        }
    }

    async copyPromptToClipboard(): Promise<void> {
        const prompt = this.promptForm.get("prompt")?.value || "";
        if (!prompt.trim()) {
            return;
        }

        try {
            await navigator.clipboard.writeText(prompt);
            this.notificationService.success(this.translate.instant("musicStylePrompt.copiedToClipboard"));
        } catch (error) {
            console.error("Failed to copy to clipboard:", error);
            this.notificationService.error(this.translate.instant("musicStylePrompt.errors.copyFailed"));
        }
    }

    onStyleChanged(stylePrompt: string): void {
        // Auto-mode: Update prompt immediately
        if (this.currentMode === "auto") {
            this.promptForm.patchValue({prompt: stylePrompt});
        }
    }

    onApplyStyles(stylePrompt: string): void {
        // Manual-mode: Apply styles and switch to auto-mode
        const currentPrompt = this.promptForm.get("prompt")?.value?.trim();

        if (currentPrompt && currentPrompt !== stylePrompt) {
            const confirmOverwrite = confirm(this.translate.instant("musicStylePrompt.mode.applyConfirm"));
            if (!confirmOverwrite) {
                return;
            }
        }

        this.promptForm.patchValue({prompt: stylePrompt});
        this.switchToAutoMode();
        this.notificationService.success(this.translate.instant("musicStylePrompt.mode.stylesApplied"));
    }

    switchToManualMode(): void {
        if (this.currentMode === "manual") {
            return;
        }
        this.currentMode = "manual";
    }

    switchToAutoMode(): void {
        this.currentMode = "auto";
    }

    onCollapseToggled(isCollapsed: boolean): void {
        this.isStyleChooserCollapsed = isCollapsed;
    }
}
