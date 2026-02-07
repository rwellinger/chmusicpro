import {ChangeDetectorRef, Component, HostListener, inject, OnDestroy, OnInit, ViewEncapsulation} from "@angular/core";
import {FormBuilder, FormGroup, ReactiveFormsModule, Validators} from "@angular/forms";
import {CommonModule} from "@angular/common";
import {NavigationEnd, Router} from "@angular/router";
import {TranslateModule, TranslateService} from "@ngx-translate/core";
import {MatCardModule} from "@angular/material/card";
import {MatSnackBarModule} from "@angular/material/snack-bar";
import {MatTabsModule} from "@angular/material/tabs";
import {filter, firstValueFrom, Subject, takeUntil} from "rxjs";

import {SongService} from "../../services/business/song.service";
import {SketchService} from "../../services/business/sketch.service";
import {NotificationService} from "../../services/ui/notification.service";
import {ChatService} from "../../services/config/chat.service";
import {ProgressService} from "../../services/ui/progress.service";
import {MUSIC_STYLE_CATEGORIES} from "../../models/music-style-chooser.model";

@Component({
    selector: "app-song-sketch-creator",
    standalone: true,
    imports: [
        CommonModule,
        ReactiveFormsModule,
        MatCardModule,
        MatSnackBarModule,
        MatTabsModule,
        TranslateModule
    ],
    templateUrl: "./song-sketch-creator.component.html",
    styleUrl: "./song-sketch-creator.component.scss",
    encapsulation: ViewEncapsulation.None
})
export class SongSketchCreatorComponent implements OnInit, OnDestroy {
    sketchForm!: FormGroup;
    isSaving = false;
    isGeneratingTitle = false;
    showTitleDropdown = false;
    selectedTags: string[] = [];

    // Edit mode state
    isEditMode = false;
    currentSketchId: string | null = null;
    private navigationState: any = null;

    // Tab state (only visible in edit mode)
    selectedTabIndex = 0;

    // AI generation states
    isGeneratingDescriptionLong = false;
    isGeneratingDescriptionShort = false;
    isGeneratingTags = false;

    // Tag categories from shared constants
    tagCategories = MUSIC_STYLE_CATEGORIES;

    // Expanded tag category (only one at a time)
    expandedCategory: "style" | "theme" | "useCase" | null = null;

    private destroy$ = new Subject<void>();
    private fb = inject(FormBuilder);
    private router = inject(Router);
    private songService = inject(SongService);
    private sketchService = inject(SketchService);
    private notificationService = inject(NotificationService);
    private translate = inject(TranslateService);
    private chatService = inject(ChatService);
    private progressService = inject(ProgressService);
    private cdr = inject(ChangeDetectorRef);

    constructor() {
        // IMPORTANT: getCurrentNavigation() must be called in constructor!
        // It returns null if called in ngOnInit
        const navigation = this.router.getCurrentNavigation();
        this.navigationState = navigation?.extras?.state;
    }

    async ngOnInit(): Promise<void> {
        // Initialize form (workflow will be added later)
        this.sketchForm = this.fb.group({
            title: ["", [Validators.required, Validators.maxLength(500)]],
            lyrics: ["", [Validators.required, Validators.maxLength(10000)]],
            prompt: ["", [Validators.required, Validators.maxLength(1024)]],
            sketch_type: ["song", Validators.required],
            workflow: ["draft"],
            // Release description fields (optional)
            description_long: [""],
            description_short: ["", Validators.maxLength(150)],
            description_tags: [""],
            info: [""]
        });

        // Handle initial navigation state
        await this.handleNavigationState(this.navigationState);

        // Listen to router events for subsequent navigations (when component is reused)
        this.router.events.pipe(
            filter(event => event instanceof NavigationEnd),
            takeUntil(this.destroy$)
        ).subscribe(async () => {
            // Use history.state to get navigation state after navigation completed
            const state = history.state;
            if (state && (state.formData || state.editMode)) {
                await this.handleNavigationState(state);
            }
        });
    }

    ngOnDestroy(): void {
        this.destroy$.next();
        this.destroy$.complete();
    }

    private async handleNavigationState(state: any): Promise<void> {
        if (!state) {
            return;
        }

        if (state["editMode"] && state["sketchId"]) {
            // EDIT MODE: Load sketch for editing
            this.isEditMode = true;
            this.currentSketchId = state["sketchId"];

            // Check if we have updated formData (coming back from child editor)
            if (state["formData"]) {
                this.updateFormWithData(state["formData"]);
            } else {
                await this.loadSketchForEdit(state["sketchId"]);
            }
        } else if (state["formData"]) {
            // CREATE MODE: Restore form data from navigation state (coming back from child editors)
            this.isEditMode = false;
            this.currentSketchId = null;
            this.updateFormWithData(state["formData"]);
        }
    }

    private updateFormWithData(formData: any): void {
        this.sketchForm.patchValue({
            title: formData.title || "",
            lyrics: formData.lyrics || "",
            prompt: formData.prompt || "",
            sketch_type: formData.sketch_type || "song",
            workflow: formData.workflow || "draft",
            description_long: formData.description_long || "",
            description_short: formData.description_short || "",
            description_tags: formData.description_tags || "",
            info: formData.info || ""
        });

        // Load tags separately
        if (formData.tags) {
            this.selectedTags = this.parseTagsFromString(formData.tags);
        } else {
            this.selectedTags = [];
        }

        // Force change detection
        this.cdr.detectChanges();
    }

    async loadSketchForEdit(sketchId: string): Promise<void> {
        try {
            const response = await firstValueFrom(
                this.sketchService.getSketchById(sketchId)
            );

            const sketch = response.data;

            // Populate form with sketch data
            this.sketchForm.patchValue({
                title: sketch.title || "",
                lyrics: sketch.lyrics || "",
                prompt: sketch.prompt,
                sketch_type: sketch.sketch_type || "song",
                workflow: sketch.workflow || "draft",
                description_long: sketch.description_long || "",
                description_short: sketch.description_short || "",
                description_tags: sketch.description_tags || "",
                info: sketch.info || ""
            });

            // Load tags - parse and select them
            if (sketch.tags) {
                const parsedTags = this.parseTagsFromString(sketch.tags);
                this.selectedTags = parsedTags;

                // Force change detection to update UI
                this.cdr.detectChanges();
            } else {
                this.selectedTags = [];
            }
        } catch (error: any) {
            this.notificationService.error(
                this.translate.instant("songSketch.creator.messages.loadError") + ": " + error.message
            );
            // Navigate back to library on error
            this.router.navigate(["/song-sketch-library"]);
        }
    }

    async saveSketch(): Promise<void> {
        if (!this.sketchForm.valid) {
            this.notificationService.error(
                this.translate.instant("songSketch.creator.messages.validationError")
            );
            return;
        }

        const formValue = this.sketchForm.value;
        this.isSaving = true;

        try {
            // Convert selectedTags array to comma-separated string
            const tagsString = this.selectedTags.length > 0
                ? this.selectedTags.join(", ")
                : undefined;

            const sketchData = {
                title: formValue.title?.trim() || undefined,
                lyrics: formValue.lyrics?.trim() || undefined,
                prompt: formValue.prompt.trim(),
                tags: tagsString,
                sketch_type: formValue.sketch_type || "song",
                workflow: formValue.workflow || "draft",
                description_long: formValue.description_long?.trim() || null,
                description_short: formValue.description_short?.trim() || null,
                description_tags: formValue.description_tags?.trim() || null,
                info: formValue.info?.trim() || null
            };

            let savedSketchId: string;

            if (this.isEditMode && this.currentSketchId) {
                // UPDATE existing sketch
                const response = await firstValueFrom(
                    this.sketchService.updateSketch(this.currentSketchId, sketchData)
                );
                savedSketchId = response.data.id;

                this.notificationService.success(
                    this.translate.instant("songSketch.creator.messages.updated")
                );
            } else {
                // CREATE new sketch
                const response = await firstValueFrom(
                    this.sketchService.createSketch(sketchData)
                );
                savedSketchId = response.data.id;

                this.notificationService.success(
                    this.translate.instant("songSketch.creator.messages.saved")
                );
            }

            // Reset form and tags
            this.sketchForm.reset();
            this.selectedTags = [];

            // Navigate to sketch library with saved sketch ID
            this.router.navigate(["/song-sketch-library"], {
                state: {
                    selectedSketchId: savedSketchId,
                    returnPage: this.navigationState?.["returnPage"] || 0
                }
            });
        } catch (error: any) {
            const errorMessage = error?.error?.detail || error?.message ||
                this.translate.instant("songSketch.creator.messages.error");
            this.notificationService.error(errorMessage);
        } finally {
            this.isSaving = false;
        }
    }

    resetForm(): void {
        this.sketchForm.reset({workflow: "draft"});
        this.selectedTags = [];
        this.notificationService.success(
            this.translate.instant("songSketch.creator.messages.resetSuccess")
        );
    }

    cancelEdit(): void {
        // Navigate back to library with current sketch ID (if in edit mode)
        const returnPage = this.navigationState?.["returnPage"] || 0;

        if (this.isEditMode && this.currentSketchId) {
            this.router.navigate(["/song-sketch-library"], {
                state: {
                    selectedSketchId: this.currentSketchId,
                    returnPage: returnPage
                }
            });
        } else {
            this.router.navigate(["/song-sketch-library"], {
                state: {returnPage: returnPage}
            });
        }
    }

    navigateToLyricCreator(): void {
        // Prepare current form data
        const formData = {
            title: this.sketchForm.get("title")?.value || "",
            lyrics: this.sketchForm.get("lyrics")?.value || "",
            prompt: this.sketchForm.get("prompt")?.value || "",
            tags: this.selectedTags.join(", "),
            workflow: this.sketchForm.get("workflow")?.value || "draft"
        };

        // Navigate with form data in state
        this.router.navigate(["/lyriccreation"], {
            state: {
                context: "sketch",
                editMode: this.isEditMode,
                sketchId: this.currentSketchId,
                formData: formData
            }
        });
    }

    navigateToMusicStylePrompt(): void {
        // Prepare current form data
        const formData: any = {
            title: this.sketchForm.get("title")?.value || "",
            lyrics: this.sketchForm.get("lyrics")?.value || "",
            prompt: this.sketchForm.get("prompt")?.value || "",
            tags: this.selectedTags.join(", "),
            workflow: this.sketchForm.get("workflow")?.value || "draft"
        };

        // Navigate with form data in state
        this.router.navigate(["/music-style-prompt"], {
            state: {
                context: "sketch",
                editMode: this.isEditMode,
                sketchId: this.currentSketchId,
                formData: formData
            }
        });
    }

    navigateToSketchLibrary(): void {
        this.router.navigate(["/song-sketch-library"]);
    }

    get charCountLyrics(): number {
        return this.sketchForm.get("lyrics")?.value?.length || 0;
    }

    get charCountPrompt(): number {
        return this.sketchForm.get("prompt")?.value?.length || 0;
    }

    get charCountDescriptionLong(): number {
        return this.sketchForm.get("description_long")?.value?.length || 0;
    }

    get charCountDescriptionShort(): number {
        return this.sketchForm.get("description_short")?.value?.length || 0;
    }

    // Title generation methods
    toggleTitleDropdown(): void {
        this.showTitleDropdown = !this.showTitleDropdown;
    }

    closeTitleDropdown(): void {
        this.showTitleDropdown = false;
    }

    @HostListener("document:click", ["$event"])
    onDocumentClick(): void {
        this.closeTitleDropdown();
    }

    selectTitleAction(action: "generate"): void {
        this.closeTitleDropdown();
        if (action === "generate") {
            this.generateTitle();
        }
    }

    async generateTitle(): Promise<void> {
        let inputText = "";

        // Priority logic: Title > Lyrics > Fallback
        const currentTitle = this.sketchForm.get("title")?.value?.trim();
        const currentLyrics = this.sketchForm.get("lyrics")?.value?.trim();

        if (currentTitle) {
            inputText = currentTitle;
        } else if (currentLyrics) {
            inputText = currentLyrics;
        } else {
            // Fallback constant
            inputText = this.translate.instant("songSketch.creator.messages.generateTitleFallback");
        }

        this.isGeneratingTitle = true;
        try {
            const generatedTitle = await this.progressService.executeWithProgress(
                () => this.chatService.generateTitle(inputText),
                this.translate.instant("songSketch.creator.messages.generatingTitle"),
                this.translate.instant("songSketch.creator.messages.generatingTitleHint")
            );
            this.sketchForm.patchValue({title: this.removeQuotes(generatedTitle as string)});
        } catch (error: any) {
            this.notificationService.error(
                this.translate.instant("songSketch.creator.messages.titleGenerationError") + ": " + error.message
            );
        } finally {
            this.isGeneratingTitle = false;
        }
    }

    private removeQuotes(text: string): string {
        return text.replace(/^["']|["']$/g, "").trim();
    }

    // AI Description Generation Methods
    async generateDescriptionLong(): Promise<void> {
        const lyrics = this.sketchForm.get("lyrics")?.value?.trim();
        if (!lyrics) {
            this.notificationService.error(
                this.translate.instant("songSketch.creator.messages.descriptionLongRequired")
            );
            return;
        }

        this.isGeneratingDescriptionLong = true;
        try {
            const descriptionLong = await this.progressService.executeWithProgress(
                () => this.chatService.validateAndCallUnified("description", "generate-long", lyrics),
                this.translate.instant("songSketch.creator.messages.generatingDescriptionLong"),
                this.translate.instant("songSketch.creator.messages.generatingDescriptionLongHint")
            );

            this.sketchForm.patchValue({description_long: descriptionLong});
            this.notificationService.success(
                this.translate.instant("songSketch.creator.messages.descriptionLongGenerated")
            );
        } catch (error: any) {
            this.notificationService.error(
                this.translate.instant("songSketch.creator.messages.descriptionLongError") + ": " + error.message
            );
        } finally {
            this.isGeneratingDescriptionLong = false;
        }
    }

    async generateDescriptionShort(): Promise<void> {
        const descriptionLong = this.sketchForm.get("description_long")?.value?.trim();
        if (!descriptionLong) {
            this.notificationService.error(
                this.translate.instant("songSketch.creator.messages.descriptionShortRequired")
            );
            return;
        }

        this.isGeneratingDescriptionShort = true;
        try {
            const descriptionShort = await this.progressService.executeWithProgress(
                () => this.chatService.validateAndCallUnified("description", "generate-short", descriptionLong),
                this.translate.instant("songSketch.creator.messages.generatingDescriptionShort"),
                this.translate.instant("songSketch.creator.messages.generatingDescriptionShortHint")
            );

            this.sketchForm.patchValue({description_short: descriptionShort});
            this.notificationService.success(
                this.translate.instant("songSketch.creator.messages.descriptionShortGenerated")
            );
        } catch (error: any) {
            this.notificationService.error(
                this.translate.instant("songSketch.creator.messages.descriptionShortError") + ": " + error.message
            );
        } finally {
            this.isGeneratingDescriptionShort = false;
        }
    }

    async generateDescriptionTags(): Promise<void> {
        const descriptionLong = this.sketchForm.get("description_long")?.value?.trim();
        if (!descriptionLong) {
            this.notificationService.error(
                this.translate.instant("songSketch.creator.messages.tagsRequired")
            );
            return;
        }

        this.isGeneratingTags = true;
        try {
            const tags = await this.progressService.executeWithProgress(
                () => this.chatService.validateAndCallUnified("description", "generate-tags", descriptionLong),
                this.translate.instant("songSketch.creator.messages.generatingTags"),
                this.translate.instant("songSketch.creator.messages.generatingTagsHint")
            );

            this.sketchForm.patchValue({description_tags: tags});
            this.notificationService.success(
                this.translate.instant("songSketch.creator.messages.tagsGenerated")
            );
        } catch (error: any) {
            this.notificationService.error(
                this.translate.instant("songSketch.creator.messages.tagsError") + ": " + error.message
            );
        } finally {
            this.isGeneratingTags = false;
        }
    }

    insertInfoTemplate(): void {
        const key = this.translate.instant("songSketch.creator.description.infoTemplateKey");
        const tempo = this.translate.instant("songSketch.creator.description.infoTemplateTempo")
        const timeSignature = this.translate.instant("songSketch.creator.description.infoTemplateTimeSignature");
        const totalBars = this.translate.instant("songSketch.creator.description.infoTemplateTotalBars");
        const songLength = this.translate.instant("songSketch.creator.description.infoTemplateSongLength");
        const template = `${key}
${tempo}
${timeSignature}
${totalBars}
${songLength}`;
        this.sketchForm.patchValue({info: template});
        this.notificationService.success(
            this.translate.instant("songSketch.creator.messages.templateInserted")
        );
    }

    // Tag management methods
    toggleTag(tag: string): void {
        // Find tag index case-insensitive
        const index = this.selectedTags.findIndex(selectedTag =>
            selectedTag.toLowerCase() === tag.toLowerCase()
        );

        if (index > -1) {
            // Tag exists, remove it
            this.selectedTags.splice(index, 1);
        } else {
            // Tag doesn't exist, add it (use the button's case)
            this.selectedTags.push(tag);
        }
    }

    isTagSelected(tag: string): boolean {
        // Case-insensitive comparison to handle lowercase model vs mixed-case saved tags
        const isSelected = this.selectedTags.some(selectedTag =>
            selectedTag.toLowerCase() === tag.toLowerCase()
        );
        return isSelected;
    }

    private parseTagsFromString(tagsString: string): string[] {
        if (!tagsString || !tagsString.trim()) {
            return [];
        }
        return tagsString.split(",")
            .map(tag => tag.trim())
            .filter(tag => tag.length > 0);
    }

    // Toggle tag category expansion (only one at a time)
    toggleCategory(category: "style" | "theme" | "useCase"): void {
        if (this.expandedCategory === category) {
            // Close if already open
            this.expandedCategory = null;
        } else {
            // Open this category (closes others)
            this.expandedCategory = category;
        }
    }

    isCategoryExpanded(category: "style" | "theme" | "useCase"): boolean {
        return this.expandedCategory === category;
    }

    getWorkflowLabel(workflow: string): string {
        return this.translate.instant(`songSketch.workflow.${workflow}`);
    }

    hasDescriptionLong(): boolean {
        const descLong = this.sketchForm.get("description_long")?.value;
        return !!(descLong && descLong.trim().length > 0);
    }
}
