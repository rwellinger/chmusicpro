import {Component, HostListener, inject, OnInit} from "@angular/core";
import {FormBuilder, FormControl, FormGroup, ReactiveFormsModule, Validators} from "@angular/forms";
import {CommonModule} from "@angular/common";
import {HttpClient} from "@angular/common/http";
import {firstValueFrom} from "rxjs";
import {TranslateModule, TranslateService} from "@ngx-translate/core";
import {ResourceBlobService} from "../../services/ui/resource-blob.service";
import {ApiConfigService} from "../../services/config/api-config.service";
import {HealthService} from "../../services/config/health.service";
import {NotificationService} from "../../services/ui/notification.service";
import {ImageService} from "../../services/business/image.service";
import {ChatService} from "../../services/config/chat.service";
import {UserService} from "../../services/business/user.service";
import {MatSnackBarModule} from "@angular/material/snack-bar";
import {MatCardModule} from "@angular/material/card";
import {MatButtonModule} from "@angular/material/button";
import {MatSelectModule} from "@angular/material/select";
import {MatFormFieldModule} from "@angular/material/form-field";
import {ImageDetailPanelComponent} from "../../components/image-detail-panel/image-detail-panel.component";
import {InfoTooltipComponent} from "../../components/info-tooltip/info-tooltip.component";
import {ProgressService} from "../../services/ui/progress.service";
import {
    ArtisticStyle,
    ColorPaletteStyle,
    CompositionStyle,
    DetailLevel,
    EnhanceQuality,
    LightingStyle,
    SelectOption
} from "../../models/image-generation.model";

@Component({
    selector: "app-image-generator",
    standalone: true,
    imports: [CommonModule, ReactiveFormsModule, MatSnackBarModule, MatCardModule, MatButtonModule, MatSelectModule, MatFormFieldModule, ImageDetailPanelComponent, InfoTooltipComponent, TranslateModule],
    templateUrl: "./image-generator.component.html",
    styleUrl: "./image-generator.component.scss"
})
export class ImageGeneratorComponent implements OnInit {
    promptForm!: FormGroup;
    isLoading = false;
    isImprovingPrompt = false;
    isTranslatingPrompt = false;
    isInterpretingLyric = false;
    showPromptDropdown = false;
    isGeneratingTitle = false;
    showTitleDropdown = false;
    result = "";
    generatedImageUrl = "";
    generatedImageBlobUrl = "";
    showImageModal = false;

    // Storage health state (preventive UX)
    isStorageHealthy = true;
    isCheckingStorage = true;
    generatedImageId: string | null = null;
    generatedImageData: any = null;

    // Style-related FormControls (managed separately for cleaner code)
    // Note: Initial values will be overridden in ngOnInit() from LocalStorage
    artisticStyle = new FormControl<ArtisticStyle>("auto");
    composition = new FormControl<CompositionStyle>("auto");
    lighting = new FormControl<LightingStyle>("auto");
    colorPalette = new FormControl<ColorPaletteStyle>("auto");
    detailLevel = new FormControl<DetailLevel>("auto");
    enhanceQuality = new FormControl<EnhanceQuality>("auto", {nonNullable: true});

    // Dropdown options (i18n keys)
    artisticStyleOptions: SelectOption<ArtisticStyle>[] = [
        {value: "auto", labelKey: "imageGenerator.styles.artisticStyle.options.auto"},
        {value: "photorealistic", labelKey: "imageGenerator.styles.artisticStyle.options.photorealistic"},
        {value: "digital-art", labelKey: "imageGenerator.styles.artisticStyle.options.digital-art"},
        {value: "oil-painting", labelKey: "imageGenerator.styles.artisticStyle.options.oil-painting"},
        {value: "watercolor", labelKey: "imageGenerator.styles.artisticStyle.options.watercolor"},
        {value: "cartoon", labelKey: "imageGenerator.styles.artisticStyle.options.cartoon"},
        {value: "anime", labelKey: "imageGenerator.styles.artisticStyle.options.anime"},
        {value: "sketch", labelKey: "imageGenerator.styles.artisticStyle.options.sketch"},
        {value: "3d-render", labelKey: "imageGenerator.styles.artisticStyle.options.3d-render"}
    ];

    compositionOptions: SelectOption<CompositionStyle>[] = [
        {value: "auto", labelKey: "imageGenerator.styles.composition.options.auto"},
        {value: "portrait", labelKey: "imageGenerator.styles.composition.options.portrait"},
        {value: "landscape", labelKey: "imageGenerator.styles.composition.options.landscape"},
        {value: "wide-angle", labelKey: "imageGenerator.styles.composition.options.wide-angle"},
        {value: "close-up", labelKey: "imageGenerator.styles.composition.options.close-up"},
        {value: "rule-of-thirds", labelKey: "imageGenerator.styles.composition.options.rule-of-thirds"},
        {value: "centered", labelKey: "imageGenerator.styles.composition.options.centered"},
        {value: "album-cover", labelKey: "imageGenerator.styles.composition.options.album-cover"}
    ];

    lightingOptions: SelectOption<LightingStyle>[] = [
        {value: "auto", labelKey: "imageGenerator.styles.lighting.options.auto"},
        {value: "natural", labelKey: "imageGenerator.styles.lighting.options.natural"},
        {value: "studio", labelKey: "imageGenerator.styles.lighting.options.studio"},
        {value: "dramatic", labelKey: "imageGenerator.styles.lighting.options.dramatic"},
        {value: "golden-hour", labelKey: "imageGenerator.styles.lighting.options.golden-hour"},
        {value: "night", labelKey: "imageGenerator.styles.lighting.options.night"}
    ];

    colorPaletteOptions: SelectOption<ColorPaletteStyle>[] = [
        {value: "auto", labelKey: "imageGenerator.styles.colorPalette.options.auto"},
        {value: "vibrant", labelKey: "imageGenerator.styles.colorPalette.options.vibrant"},
        {value: "muted", labelKey: "imageGenerator.styles.colorPalette.options.muted"},
        {value: "monochrome", labelKey: "imageGenerator.styles.colorPalette.options.monochrome"},
        {value: "high-contrast", labelKey: "imageGenerator.styles.colorPalette.options.high-contrast"},
        {value: "warm", labelKey: "imageGenerator.styles.colorPalette.options.warm"},
        {value: "cool", labelKey: "imageGenerator.styles.colorPalette.options.cool"},
        {value: "pastel", labelKey: "imageGenerator.styles.colorPalette.options.pastel"}
    ];

    detailLevelOptions: SelectOption<DetailLevel>[] = [
        {value: "auto", labelKey: "imageGenerator.styles.detailLevel.options.auto"},
        {value: "minimal", labelKey: "imageGenerator.styles.detailLevel.options.minimal"},
        {value: "moderate", labelKey: "imageGenerator.styles.detailLevel.options.moderate"},
        {value: "highly-detailed", labelKey: "imageGenerator.styles.detailLevel.options.highly-detailed"}
    ];

    enhanceQualityOptions: SelectOption<EnhanceQuality>[] = [
        {value: "auto", labelKey: "imageGenerator.enhanceQuality.options.auto"},
        {value: "quality", labelKey: "imageGenerator.enhanceQuality.options.quality"},
        {value: "fast", labelKey: "imageGenerator.enhanceQuality.options.fast"},
        {value: "off", labelKey: "imageGenerator.enhanceQuality.options.off"}
    ];

    private fb = inject(FormBuilder);
    private http = inject(HttpClient);
    private apiConfig = inject(ApiConfigService);
    private healthService = inject(HealthService);
    private notificationService = inject(NotificationService);
    private imageService = inject(ImageService);
    private chatService = inject(ChatService);
    private progressService = inject(ProgressService);
    private resourceBlobService = inject(ResourceBlobService);
    private translate = inject(TranslateService);
    private userService = inject(UserService);

    ngOnInit() {
        this.promptForm = this.fb.group({
            title: [""],
            prompt: ["", Validators.required],
            size: ["1024x1024", Validators.required]
        });

        // Load saved form data
        const savedData = this.imageService.loadFormData();
        if (savedData.prompt || savedData["title"]) this.promptForm.patchValue(savedData);

        // Save form data on changes
        this.promptForm.valueChanges.subscribe(value => {
            this.imageService.saveFormData(value);
        });

        // Load style preferences from LocalStorage
        const savedStyles = this.imageService.loadStylePreferences();
        this.artisticStyle.setValue(savedStyles.artisticStyle);
        this.composition.setValue(savedStyles.composition);
        this.lighting.setValue(savedStyles.lighting);
        this.colorPalette.setValue(savedStyles.colorPalette);
        this.detailLevel.setValue(savedStyles.detailLevel);
        this.enhanceQuality.setValue(savedStyles.enhanceQuality);

        // If Album Cover is already selected, force enhanceQuality to 'auto' and size to square
        if (savedStyles.composition === "album-cover") {
            this.enhanceQuality.setValue("auto");
            this.enhanceQuality.disable();
            this.promptForm.patchValue({size: "1024x1024"}, {emitEvent: false});
            this.promptForm.get("size")?.disable({emitEvent: false});
            this.saveStylePreferences();
        }

        // Save style preferences on changes
        this.artisticStyle.valueChanges.subscribe(() => this.saveStylePreferences());
        this.composition.valueChanges.subscribe(value => {
            // Auto-set enhancement quality, size, and disable when Album Cover is selected
            if (value === "album-cover") {
                this.enhanceQuality.setValue("auto", {emitEvent: false});
                this.enhanceQuality.disable();
                this.promptForm.patchValue({size: "1024x1024"}, {emitEvent: false});
                // Disable size dropdown to prevent format changes
                this.promptForm.get("size")?.disable({emitEvent: false});
                // Reset incompatible styles to 'auto' when switching to Album Cover
                this.resetIncompatibleStylesForAlbumCover();
            } else {
                // Re-enable when switching away from Album Cover
                this.enhanceQuality.enable();
                this.promptForm.get("size")?.enable({emitEvent: false});
            }
            this.saveStylePreferences();
        });
        this.lighting.valueChanges.subscribe(() => this.saveStylePreferences());
        this.colorPalette.valueChanges.subscribe(() => this.saveStylePreferences());
        this.detailLevel.valueChanges.subscribe(() => this.saveStylePreferences());
        this.enhanceQuality.valueChanges.subscribe(() => this.saveStylePreferences());

        // CRITICAL: Check storage health on page load (preventive UX)
        // Disables generate button if MinIO is down (prevents wasted API credits)
        this.checkStorageHealth();

        // Watch title changes → Reset composition if album-cover but no title
        this.promptForm.get("title")?.valueChanges.subscribe(title => {
            if (!title?.trim() && this.composition.value === "album-cover") {
                this.composition.setValue("auto");
                this.notificationService.info(this.translate.instant("imageGenerator.albumCoverRequiresTitle"));
            }
        });
    }

    /**
     * Check storage health on component init
     * Prevents users from wasting API credits when storage is unavailable
     */
    private async checkStorageHealth() {
        this.isCheckingStorage = true;
        try {
            this.isStorageHealthy = await firstValueFrom(this.healthService.checkStorage());
        } catch (error) {
            console.warn("[ImageGenerator] Storage health check failed:", error);
            this.isStorageHealthy = false;
        } finally {
            this.isCheckingStorage = false;
        }
    }

    async onSubmit() {
        if (this.promptForm.valid) {
            // Validate title is required for Album Cover composition
            if (this.composition.value === "album-cover" && !this.promptForm.get("title")?.value?.trim()) {
                this.notificationService.error(this.translate.instant("imageGenerator.errors.titleRequiredForCover"));
                return;
            }

            this.isLoading = true;
            this.result = "";

            try {
                const formValue = this.promptForm.value;
                let titleValue = formValue.title?.trim();

                // Auto-generate title if empty (obligatory)
                if (!titleValue) {
                    titleValue = await this.progressService.executeWithProgress(
                        () => this.chatService.generateTitleFast(formValue.prompt.trim()),
                        this.translate.instant("imageGenerator.progress.generatingTitle"),
                        this.translate.instant("imageGenerator.progress.generatingTitleHint")
                    );
                    titleValue = this.removeQuotes(titleValue);
                    // Update form with generated title
                    this.promptForm.patchValue({title: titleValue}, {emitEvent: false});
                }

                const effectiveMode = this.getEffectiveEnhanceMode();
                let finalPrompt = formValue.prompt.trim();

                // Step 1: AI Enhancement (if not 'off')
                if (effectiveMode !== "off") {
                    // Album Cover uses special cover enhancement
                    if (this.composition.value === "album-cover") {
                        finalPrompt = await this.progressService.executeWithProgress(
                            () => this.chatService.enhanceCoverPrompt(finalPrompt),
                            this.translate.instant("imageGenerator.progress.enhancingCover"),
                            this.translate.instant("imageGenerator.progress.enhancingCoverHint")
                        );
                    } else {
                        // Regular enhancement (quality or fast)
                        const progressMessage =
                            effectiveMode === "quality"
                                ? this.translate.instant("imageGenerator.progress.enhancingQuality")
                                : this.translate.instant("imageGenerator.progress.enhancingFast");

                        const progressHint =
                            effectiveMode === "quality"
                                ? this.translate.instant("imageGenerator.progress.enhancingQualityHint")
                                : this.translate.instant("imageGenerator.progress.enhancingFastHint");

                        finalPrompt = await this.progressService.executeWithProgress(
                            () =>
                                effectiveMode === "quality"
                                    ? this.chatService.improveImagePrompt(finalPrompt)
                                    : this.chatService.improveImagePromptFast(finalPrompt),
                            progressMessage,
                            progressHint
                        );
                    }

                    finalPrompt = this.removeQuotes(finalPrompt);
                }

                // Step 2: Send generation request with styles
                const requestBody: any = {
                    title: titleValue || null,
                    user_prompt: formValue.prompt.trim(), // Original user input
                    prompt: finalPrompt, // AI-enhanced prompt (Ollama)
                    size: formValue.size
                };

                // Add style parameters if not 'auto'
                if (this.artisticStyle.value !== "auto") {
                    requestBody.artistic_style = this.artisticStyle.value;
                }
                if (this.composition.value !== "auto") {
                    requestBody.composition = this.composition.value;
                }
                if (this.lighting.value !== "auto") {
                    requestBody.lighting = this.lighting.value;
                }
                if (this.colorPalette.value !== "auto") {
                    requestBody.color_palette = this.colorPalette.value;
                }
                if (this.detailLevel.value !== "auto") {
                    requestBody.detail_level = this.detailLevel.value;
                }

                const data = await firstValueFrom(
                    this.http.post<any>(this.apiConfig.endpoints.image.generate, requestBody)
                );

                if (data.url) {
                    // Store the generated image URL and ID
                    this.generatedImageUrl = data.url || "";
                    this.generatedImageId = data.id || null;

                    // Create image object for direct display (use data from backend)
                    this.generatedImageData = {
                        id: data.id || null,
                        url: data.url,
                        user_prompt: data.user_prompt || null,
                        prompt: data.prompt || finalPrompt,
                        enhanced_prompt: data.enhanced_prompt || null,
                        title: titleValue || null,
                        size: formValue.size,
                        model_used: "DALL-E 3",
                        created_at: new Date().toISOString(),
                        artistic_style: data.artistic_style || null,
                        composition: data.composition || null,
                        lighting: data.lighting || null,
                        color_palette: data.color_palette || null,
                        detail_level: data.detail_level || null
                    };

                    // Load blob URL for modal display
                    if (data.url) {
                        this.resourceBlobService.getResourceBlobUrl(data.url).subscribe({
                            next: (blobUrl) => {
                                this.generatedImageBlobUrl = blobUrl;
                            },
                            error: (error) => {
                                console.error("Failed to load image blob:", error);
                                this.generatedImageBlobUrl = "";
                            }
                        });
                    }
                } else {
                    this.notificationService.error("Error generating image.");
                }
            } catch (error: any) {
                this.notificationService.error(`Error: ${error.message}`);
            } finally {
                this.isLoading = false;
            }
        }
    }

    downloadImage() {
        if (this.generatedImageUrl) {
            const link = document.createElement("a");
            link.href = this.generatedImageUrl;
            link.target = "_blank";
            link.download = `generated-image-${Date.now()}.png`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    }

    openImageModal() {
        this.showImageModal = true;
    }

    closeImageModal() {
        this.showImageModal = false;
    }

    // Handlers for shared image detail panel
    onTitleChanged() {
        // Title changes are handled by the detail panel component
        // No action needed here as the component handles its own DB updates
    }

    onDownloadImage() {
        if (this.generatedImageData?.url) {
            // Use authenticated download via ResourceBlobService
            const filename = this.getImageFilename();
            this.resourceBlobService.downloadResource(this.generatedImageData.url, filename);
        }
    }

    private getImageFilename(): string {
        const title = this.generatedImageData?.title || this.generatedImageData?.prompt || "image";
        const sanitized = title.replace(/[^a-zA-Z0-9]/g, "_").substring(0, 50);
        return `${sanitized}.png`;
    }

    onPreviewImage() {
        this.openImageModal();
    }


    async translatePrompt() {
        const currentPrompt = this.promptForm.get("prompt")?.value?.trim();
        if (!currentPrompt) {
            this.notificationService.error(this.translate.instant("imageGenerator.errors.promptRequired"));
            return;
        }

        this.isTranslatingPrompt = true;
        try {
            const translatedPrompt = await this.progressService.executeWithProgress(
                () => this.chatService.translateImagePrompt(currentPrompt),
                this.translate.instant("imageGenerator.progress.translating"),
                this.translate.instant("imageGenerator.progress.translatingHint")
            );
            this.promptForm.patchValue({prompt: this.removeQuotes(translatedPrompt)});
        } catch (error: any) {
            this.notificationService.error(`Error translating prompt: ${error.message}`);
        } finally {
            this.isTranslatingPrompt = false;
        }
    }

    async interpretLyric() {
        const currentPrompt = this.promptForm.get("prompt")?.value?.trim();
        if (!currentPrompt) {
            this.notificationService.error(this.translate.instant("imageGenerator.errors.promptRequired"));
            return;
        }

        this.isInterpretingLyric = true;
        try {
            const interpretedPrompt = await this.progressService.executeWithProgress(
                () => this.chatService.interpretLyricPrompt(currentPrompt),
                this.translate.instant("imageGenerator.progress.interpretingLyric"),
                this.translate.instant("imageGenerator.progress.interpretingLyricHint")
            );
            this.promptForm.patchValue({prompt: this.removeQuotes(interpretedPrompt)});
        } catch (error: any) {
            this.notificationService.error(`Error interpreting lyric: ${error.message}`);
        } finally {
            this.isInterpretingLyric = false;
        }
    }

    togglePromptDropdown() {
        this.showPromptDropdown = !this.showPromptDropdown;
    }

    closePromptDropdown() {
        this.showPromptDropdown = false;
    }

    selectPromptAction(action: "translate" | "interpret-lyric") {
        this.closePromptDropdown();

        if (action === "translate") {
            this.translatePrompt();
        } else if (action === "interpret-lyric") {
            this.interpretLyric();
        }
    }

    // Title generation methods
    async generateTitle() {
        // Determine input text based on priority: title > prompt > default
        let inputText = this.promptForm.get("title")?.value?.trim();
        if (!inputText) {
            inputText = this.promptForm.get("prompt")?.value?.trim();
        }
        if (!inputText) {
            inputText = this.translate.instant("imageGenerator.generateTitleFallback");
        }

        this.isGeneratingTitle = true;
        try {
            const generatedTitle = await this.progressService.executeWithProgress(
                () => this.chatService.generateTitle(inputText),
                this.translate.instant("imageGenerator.progress.generatingTitle"),
                this.translate.instant("imageGenerator.progress.generatingTitleHint")
            );
            this.promptForm.patchValue({title: this.removeQuotes(generatedTitle)});
        } catch (error: any) {
            this.notificationService.error(`Error generating title: ${error.message}`);
        } finally {
            this.isGeneratingTitle = false;
        }
    }

    toggleTitleDropdown() {
        this.showTitleDropdown = !this.showTitleDropdown;
    }

    closeTitleDropdown() {
        this.showTitleDropdown = false;
    }

    selectTitleAction(action: "generate") {
        this.closeTitleDropdown();

        if (action === "generate") {
            this.generateTitle();
        }
    }

    @HostListener("document:click", ["$event"])
    onDocumentClick(event: Event) {
        const target = event.target as HTMLElement;
        const promptDropdown = target.closest(".prompt-dropdown-container");
        const titleDropdown = target.closest(".title-dropdown-container");

        if (!promptDropdown && this.showPromptDropdown) {
            this.closePromptDropdown();
        }
        if (!titleDropdown && this.showTitleDropdown) {
            this.closeTitleDropdown();
        }
    }

    /**
     * Check if user is in Manual Mode (at least one dropdown is not 'auto')
     */
    get isManualMode(): boolean {
        return (
            this.artisticStyle.value !== "auto" ||
            this.composition.value !== "auto" ||
            this.lighting.value !== "auto" ||
            this.colorPalette.value !== "auto" ||
            this.detailLevel.value !== "auto"
        );
    }

    /**
     * Check if Album Cover composition can be used (requires title)
     */
    get canUseAlbumCover(): boolean {
        return !!this.promptForm.get("title")?.value?.trim();
    }

    /**
     * Check if Album Cover composition is currently selected
     */
    get isAlbumCoverMode(): boolean {
        return this.composition.value === "album-cover";
    }

    /**
     * Save current style preferences to LocalStorage
     */
    private saveStylePreferences(): void {
        this.imageService.saveStylePreferences({
            artisticStyle: this.artisticStyle.value || "auto",
            composition: this.composition.value || "auto",
            lighting: this.lighting.value || "auto",
            colorPalette: this.colorPalette.value || "auto",
            detailLevel: this.detailLevel.value || "auto",
            enhanceQuality: this.enhanceQuality.value || "auto"
        });
    }

    /**
     * Determine effective enhancement mode based on 'auto' setting
     * Auto Mode → Quality (creative AI help needed)
     * Manual Mode → Off (user already set precise styles, avoid conflicts)
     * Album Cover → Always Quality (needs title + artist context)
     */
    private getEffectiveEnhanceMode(): "quality" | "fast" | "off" {
        // Album Cover always requires enhancement (for title + artist integration)
        if (this.composition.value === "album-cover") {
            return "quality";
        }

        const selected = this.enhanceQuality.value;

        if (selected === "auto") {
            return this.isManualMode ? "off" : "quality";
        }

        return selected as "quality" | "fast" | "off";
    }

    resetForm() {
        this.promptForm.reset({size: "1024x1024", title: ""});
        this.imageService.clearFormData();
        this.generatedImageUrl = "";
        this.generatedImageBlobUrl = "";
        this.generatedImageId = null;
        this.generatedImageData = null;
    }

    private removeQuotes(text: string): string {
        if (!text) return text;
        return text.replace(/^["']|["']$/g, "").trim();
    }

    /**
     * Reset incompatible styles to 'auto' when Album Cover is selected
     * Album Cover (with Text Overlay) only restricts sketch style.
     * Other styles (oil-painting, watercolor, dramatic, muted, monochrome) are now allowed
     * since text is added separately via Text Overlay Editor.
     */
    private resetIncompatibleStylesForAlbumCover(): void {
        const incompatibleArtisticStyles: ArtisticStyle[] = ["sketch"];

        if (incompatibleArtisticStyles.includes(this.artisticStyle.value as ArtisticStyle)) {
            this.artisticStyle.setValue("auto", {emitEvent: false});
        }
    }

    /**
     * Check if an artistic style option is incompatible with Album Cover composition
     */
    isArtisticStyleIncompatibleWithAlbumCover(style: ArtisticStyle): boolean {
        if (!this.isAlbumCoverMode || style === "auto") return false;
        const incompatibleStyles: ArtisticStyle[] = ["sketch"];
        return incompatibleStyles.includes(style);
    }

    /**
     * Check if a lighting option is incompatible with Album Cover composition
     */
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    isLightingIncompatibleWithAlbumCover(lighting: LightingStyle): boolean {
        // No lighting restrictions for Album Cover (text added via Text Overlay)
        return false;
    }

    /**
     * Check if a color palette option is incompatible with Album Cover composition
     */
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    isColorPaletteIncompatibleWithAlbumCover(palette: ColorPaletteStyle): boolean {
        // No color palette restrictions for Album Cover (text added via Text Overlay)
        return false;
    }
}
