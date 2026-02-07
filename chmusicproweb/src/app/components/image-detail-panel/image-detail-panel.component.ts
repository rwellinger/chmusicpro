import {
    Component,
    ElementRef,
    EventEmitter,
    HostListener,
    inject,
    Input,
    OnChanges,
    OnInit,
    Output,
    SimpleChanges,
    ViewChild
} from "@angular/core";
import {CommonModule} from "@angular/common";
import {FormsModule} from "@angular/forms";
import {HttpClient} from "@angular/common/http";
import {firstValueFrom} from "rxjs";
import {TranslateModule, TranslateService} from "@ngx-translate/core";
import {ResourceBlobService} from "../../services/ui/resource-blob.service";
import {NotificationService} from "../../services/ui/notification.service";
import {ApiConfigService} from "../../services/config/api-config.service";
import {ChatService} from "../../services/config/chat.service";
import {ProgressService} from "../../services/ui/progress.service";

@Component({
    selector: "app-image-detail-panel",
    standalone: true,
    imports: [CommonModule, FormsModule, TranslateModule],
    templateUrl: "./image-detail-panel.component.html",
    styleUrl: "./image-detail-panel.component.scss"
})
export class ImageDetailPanelComponent implements OnInit, OnChanges {
    private resourceBlobService = inject(ResourceBlobService);
    private notificationService = inject(NotificationService);
    private apiConfigService = inject(ApiConfigService);
    private http = inject(HttpClient);
    private translate = inject(TranslateService);
    private chatService = inject(ChatService);
    private progressService = inject(ProgressService);

    imageBlobUrl: string = "";
    @Input() image: any = null;
    @Input() imageId: string | null = null;
    @Input() showEditTitle: boolean = true;
    @Input() title: string = "";
    @Input() showMetaInfo: string[] = ["model", "size", "created"];
    @Input() placeholderText: string = "";
    @Input() placeholderIcon: string = "fas fa-image";
    @Input() isGenerating: boolean = false;
    @Input() showActionButtons: boolean = true;

    // Component state
    isLoading = false;
    loadingError: string | null = null;

    @Output() titleChanged = new EventEmitter<string>();
    @Output() downloadOriginal = new EventEmitter<void>();
    @Output() previewImage = new EventEmitter<void>();

    @ViewChild("titleInput") titleInput!: ElementRef;

    editingTitle = false;
    editTitleValue = "";
    showTitleDropdown = false;
    isGeneratingTitle = false;

    startEditTitle() {
        if (!this.showEditTitle || !this.image) return;
        this.editingTitle = true;
        this.editTitleValue = this.getDisplayTitle(this.image);
        setTimeout(() => {
            this.titleInput?.nativeElement?.focus();
        });
    }

    async saveTitle() {
        if (!this.image || !this.imageId) return;

        try {
            await firstValueFrom(
                this.http.put<any>(this.apiConfigService.endpoints.image.update(this.imageId), {
                    title: this.editTitleValue.trim()
                })
            );

            this.editingTitle = false;
            this.titleChanged.emit(this.editTitleValue);

            // Auto-refresh to show updated data
            await this.reloadImage();

        } catch (error: any) {
            this.notificationService.error(this.translate.instant("imageDetailPanel.errors.updateTitle"));
        }
    }

    cancelEditTitle() {
        this.editingTitle = false;
        this.editTitleValue = "";
        this.showTitleDropdown = false;
    }

    // Title generation methods
    async generateTitle() {
        // Determine input text: current title > user_prompt > prompt > fallback
        let inputText = this.editTitleValue?.trim();
        if (!inputText) {
            inputText = this.image?.user_prompt?.trim() || this.image?.prompt?.trim();
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
            this.editTitleValue = this.removeQuotes(generatedTitle);
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
        const titleDropdown = target.closest(".title-dropdown-container");

        if (!titleDropdown && this.showTitleDropdown) {
            this.closeTitleDropdown();
        }
    }

    private removeQuotes(text: string): string {
        if (!text) return text;
        return text.replace(/^["']|["']$/g, "").trim();
    }

    onDownloadOriginal() {
        this.downloadOriginal.emit();
    }

    onPreview() {
        this.previewImage.emit();
    }

    ngOnInit() {
        // Set default values for inputs if not provided
        if (!this.title) {
            this.title = this.translate.instant("imageDetailPanel.title");
        }
        if (!this.placeholderText) {
            this.placeholderText = this.translate.instant("imageDetailPanel.placeholder");
        }

        if (this.imageId) {
            this.loadImageFromDB(this.imageId);
        }
    }

    ngOnChanges(changes: SimpleChanges): void {
        if (changes["imageId"] && this.imageId && this.imageId !== changes["imageId"].previousValue) {
            this.loadImageFromDB(this.imageId);
        } else if (changes["image"] && this.image?.url) {
            // Load blob URL when image changes
            this.loadImageBlob();
        } else if (!this.image) {
            this.imageBlobUrl = "";
        }
    }

    private loadImageBlob() {
        // Use display_url if available (overlay version), otherwise fallback to url (original)
        const imageUrl = this.image?.display_url || this.image?.url;

        if (imageUrl) {
            this.resourceBlobService.getResourceBlobUrl(imageUrl).subscribe({
                next: (blobUrl) => {
                    this.imageBlobUrl = blobUrl;
                },
                error: (error) => {
                    console.error("Failed to load image blob:", imageUrl, error);
                    this.imageBlobUrl = "";
                }
            });
        } else {
            console.warn("[ImageDetailPanel] No imageUrl to load!", this.image);
        }
    }

    public async reloadImage() {
        if (this.imageId) {
            await this.loadImageFromDB(this.imageId);
        }
    }

    private async loadImageFromDB(imageId: string) {
        this.isLoading = true;
        this.loadingError = null;

        try {
            const response = await firstValueFrom(
                this.http.get<any>(this.apiConfigService.endpoints.image.detail(imageId))
            );

            if (response && response.data) {
                this.image = response.data;
            } else {
                this.image = response;
            }

            // Load the blob URL for the image
            this.loadImageBlob();

        } catch (error: any) {
            this.loadingError = this.translate.instant("imageDetailPanel.errors.failedToLoad");
            this.notificationService.error(this.translate.instant("imageDetailPanel.errors.loadImage"));
            this.image = null;
        } finally {
            this.isLoading = false;
        }
    }

    hasTextOverlay(): boolean {
        return this.image?.text_overlay_metadata !== null && this.image?.text_overlay_metadata !== undefined;
    }

    getDisplayTitle(image: any): string {
        if (!image) return "";
        const displayPrompt = image.user_prompt || image.prompt || "";
        return image.title || (displayPrompt ? displayPrompt.slice(0, 50) + (displayPrompt.length > 50 ? "..." : "") : this.translate.instant("imageDetailPanel.untitled"));
    }

    formatDate(dateString: string): string {
        if (!dateString) return "";
        return new Date(dateString).toLocaleDateString("de-DE", {
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit"
        });
    }

    onImageError(event: Event) {
        const target = event.target as HTMLImageElement;
        if (target && !target.complete) {
            console.error("Image failed to load:", {
                src: target.src,
                alt: target.alt,
                error: event
            });
            this.loadingError = this.translate.instant("imageDetailPanel.errors.failedToLoad");
        }
    }

    shouldShowMetaInfo(type: string): boolean {
        return this.showMetaInfo.includes(type);
    }

    getImageSizeClass(): string {
        if (!this.image?.size) return "";

        const size = this.image.size;

        if (size === "1024x1024") {
            return "square";
        } else if (size === "1792x1024") {
            return "landscape";
        } else if (size === "1024x1792") {
            return "portrait";
        }

        return "";
    }

    // === Prompt Methods ===

    hasUserPrompt(): boolean {
        // Show user prompt if it exists AND is different from enhanced prompt
        if (!this.image?.user_prompt || !this.image.user_prompt.trim()) {
            return false;
        }
        // Only show if we have enhanced prompt AND it's different from user prompt
        if (!this.image.enhanced_prompt) {
            return true; // Show user prompt if no enhancement happened
        }
        return this.image.user_prompt.trim() !== this.image.enhanced_prompt.trim();
    }

    hasEnhancedPrompt(): boolean {
        return !!(this.image?.enhanced_prompt && this.image.enhanced_prompt.trim());
    }

    shouldShowPromptSection(): boolean {
        // Always show if we have at least user_prompt or enhanced_prompt
        return !!(this.hasUserPrompt() || this.hasEnhancedPrompt());
    }

    // === Style Methods ===

    hasManualStyles(): boolean {
        if (!this.image) return false;
        return !!(
            (this.image.artistic_style && this.image.artistic_style !== "auto") ||
            (this.image.composition && this.image.composition !== "auto") ||
            (this.image.lighting && this.image.lighting !== "auto") ||
            (this.image.color_palette && this.image.color_palette !== "auto") ||
            (this.image.detail_level && this.image.detail_level !== "auto")
        );
    }

    getStyleChips(): { label: string, value: string }[] {
        if (!this.image) return [];

        const chips: { label: string, value: string }[] = [];

        if (this.image.artistic_style && this.image.artistic_style !== "auto") {
            chips.push({
                label: this.translate.instant("imageDetailPanel.styles.artistic"),
                value: this.translate.instant(`imageGenerator.styles.artisticStyle.options.${this.image.artistic_style}`)
            });
        }

        if (this.image.composition && this.image.composition !== "auto") {
            chips.push({
                label: this.translate.instant("imageDetailPanel.styles.composition"),
                value: this.translate.instant(`imageGenerator.styles.composition.options.${this.image.composition}`)
            });
        }

        if (this.image.lighting && this.image.lighting !== "auto") {
            chips.push({
                label: this.translate.instant("imageDetailPanel.styles.lighting"),
                value: this.translate.instant(`imageGenerator.styles.lighting.options.${this.image.lighting}`)
            });
        }

        if (this.image.color_palette && this.image.color_palette !== "auto") {
            chips.push({
                label: this.translate.instant("imageDetailPanel.styles.colorPalette"),
                value: this.translate.instant(`imageGenerator.styles.colorPalette.options.${this.image.color_palette}`)
            });
        }

        if (this.image.detail_level && this.image.detail_level !== "auto") {
            chips.push({
                label: this.translate.instant("imageDetailPanel.styles.detailLevel"),
                value: this.translate.instant(`imageGenerator.styles.detailLevel.options.${this.image.detail_level}`)
            });
        }

        return chips;
    }

    // === Copy to Clipboard ===

    copyToClipboard(text: string): void {
        if (!text) return;

        navigator.clipboard.writeText(text).then(() => {
            this.notificationService.success(this.translate.instant("imageDetailPanel.prompts.final.copied"));
        }).catch(err => {
            console.error("Failed to copy to clipboard:", err);
            this.notificationService.error(this.translate.instant("imageDetailPanel.errors.copyFailed"));
        });
    }
}