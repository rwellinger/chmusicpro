import {Component, DestroyRef, ElementRef, inject, OnInit, ViewChild, ViewEncapsulation} from "@angular/core";
import {CommonModule} from "@angular/common";
import {FormBuilder, FormGroup, ReactiveFormsModule, Validators} from "@angular/forms";
import {HttpClient} from "@angular/common/http";
import {TranslateModule, TranslateService} from "@ngx-translate/core";
import {MatCardModule} from "@angular/material/card";
import {MatFormFieldModule} from "@angular/material/form-field";
import {MatInputModule} from "@angular/material/input";
import {MatSelectModule} from "@angular/material/select";
import {MatButtonModule} from "@angular/material/button";
import {MatProgressSpinnerModule} from "@angular/material/progress-spinner";
import {MatDividerModule} from "@angular/material/divider";
import {MatSliderModule} from "@angular/material/slider";
import {MatExpansionModule} from "@angular/material/expansion";
import {MatCheckboxModule} from "@angular/material/checkbox";
import {MatRadioModule} from "@angular/material/radio";
import {MatTooltipModule} from "@angular/material/tooltip";
import {MatTabsModule} from "@angular/material/tabs";
import {takeUntilDestroyed} from "@angular/core/rxjs-interop";
import {debounceTime} from "rxjs";

import {ApiConfigService} from "../../services/config/api-config.service";
import {NotificationService} from "../../services/ui/notification.service";

interface GeneratedImage {
    id: string;
    prompt: string;
    filename: string;
    created_at: string;
    title?: string;
    composition?: string;
    display_url?: string;  // Backend proxy URL for S3 images
    url?: string;          // Alternative URL field
}

interface UserProfile {
    artist_name?: string;
}

@Component({
    selector: "app-text-overlay-editor",
    standalone: true,
    imports: [
        CommonModule,
        ReactiveFormsModule,
        TranslateModule,
        MatCardModule,
        MatFormFieldModule,
        MatInputModule,
        MatSelectModule,
        MatButtonModule,
        MatProgressSpinnerModule,
        MatDividerModule,
        MatSliderModule,
        MatExpansionModule,
        MatCheckboxModule,
        MatRadioModule,
        MatTooltipModule,
        MatTabsModule
    ],
    templateUrl: "./text-overlay-editor.component.html",
    styleUrl: "./text-overlay-editor.component.scss",
    encapsulation: ViewEncapsulation.None
})
export class TextOverlayEditorComponent implements OnInit {
    @ViewChild("canvas", {static: false}) canvasRef!: ElementRef<HTMLCanvasElement>;

    form!: FormGroup;
    images: GeneratedImage[] = [];
    selectedImage: GeneratedImage | null = null;
    isProcessing = false;
    resultImageFilePath: string | null = null;
    userProfile: UserProfile | null = null;

    // Canvas click mode for positioning
    isCanvasClickMode = false;
    currentClickTarget: "title" | "artist" | null = null;

    fontStyles = [
        // Original fonts
        {value: "bold", label: "Bold (Anton)", icon: "fas fa-bold"},
        {value: "elegant", label: "Elegant (Playfair)", icon: "fas fa-signature"},
        {value: "light", label: "Light (Roboto)", icon: "fas fa-feather"},
        // Comic styles
        {value: "bangers", label: "Bangers (Comic Bold)", icon: "fas fa-explosion"},
        {value: "comic", label: "Comic Neue (Modern)", icon: "fas fa-comment"},
        {value: "bubblegum", label: "Bubblegum (Playful)", icon: "fas fa-circle"},
        {value: "righteous", label: "Righteous (Retro)", icon: "fas fa-glasses"},
        // Display fonts
        {value: "bebas", label: "Bebas Neue (Condensed)", icon: "fas fa-compress"},
        {value: "bungee", label: "Bungee (Urban)", icon: "fas fa-cube"},
        {value: "montserrat", label: "Montserrat (Geometric)", icon: "fas fa-shapes"},
        {value: "oswald", label: "Oswald (Gothic)", icon: "fas fa-skull"}
    ];

    private fb = inject(FormBuilder);
    private http = inject(HttpClient);
    private apiConfig = inject(ApiConfigService);
    private notificationService = inject(NotificationService);
    private translate = inject(TranslateService);
    private destroyRef = inject(DestroyRef);

    ngOnInit(): void {
        this.form = this.fb.group({
            imageId: ["", Validators.required],
            // Title controls
            title: ["", Validators.required],
            titlePositionCustomX: [10],  // Custom X (0-100) - default bottom-left
            titlePositionCustomY: [90],  // Custom Y (0-100) - default bottom-left
            titleFontSize: [80],  // 80px default
            titleColor: ["#FFFFFF", Validators.required],
            titleOutlineColor: ["#000000", Validators.required],
            // Artist controls
            artist: [""],
            artistPositionCustomX: [10],  // Custom X (0-100) - default bottom-left
            artistPositionCustomY: [95],  // Custom Y (0-100) - slightly below title
            artistFontSize: [40],  // 40px default
            artistColor: [null],  // null = same as title
            artistOutlineColor: [null],  // null = same as title
            useCustomArtistFont: [false],  // Toggle for custom artist font
            artistFontStyle: [null],  // null = same as title font
            // Common
            fontStyle: ["bold", Validators.required]
        });

        this.loadImages();
        this.loadUserProfile();

        // Update canvas preview on form changes (debounced)
        this.form.valueChanges
            .pipe(
                debounceTime(300),
                takeUntilDestroyed(this.destroyRef)
            )
            .subscribe(() => {
                if (this.selectedImage) {
                    this.updateCanvasPreview();
                }
            });
    }

    loadImages(): void {
        // Use specialized endpoint that returns only images with title, sorted by album-cover first
        this.http.get<{ images: GeneratedImage[] }>(this.apiConfig.endpoints.image.listForTextOverlay)
            .pipe(takeUntilDestroyed(this.destroyRef))
            .subscribe({
                next: (response) => {
                    this.images = response.images || [];
                },
                error: (error) => {
                    console.error("Failed to load images:", error);
                    this.notificationService.error(this.translate.instant("textOverlayEditor.errors.loadImagesFailed"));
                }
            });
    }

    loadUserProfile(): void {
        this.http.get<UserProfile>(this.apiConfig.endpoints.user.profile)
            .pipe(takeUntilDestroyed(this.destroyRef))
            .subscribe({
                next: (profile) => {
                    this.userProfile = profile;
                    // Auto-fill artist if available and field is empty
                    if (profile.artist_name && !this.form.get("artist")?.value) {
                        this.form.patchValue({
                            artist: profile.artist_name
                        });
                    }
                },
                error: (error) => {
                    console.error("Failed to load user profile:", error);
                    // Don't show error notification, it's optional
                }
            });
    }

    onImageSelect(imageId: string): void {
        this.selectedImage = this.images.find(img => img.id === imageId) || null;
        if (this.selectedImage) {
            // Automatically fill title field with image title
            if (this.selectedImage.title) {
                this.form.patchValue({
                    title: this.selectedImage.title
                });
            }
            this.loadImageOnCanvas();
        }
    }

    private cachedImageBlob: Blob | null = null;

    loadImageOnCanvas(): void {
        if (!this.selectedImage || !this.canvasRef) return;

        const canvas = this.canvasRef.nativeElement;
        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        // Fetch image as blob with JWT token (via HttpClient)
        // Use display_url for S3 images, fallback to filename-based URL for legacy filesystem images
        const imageUrl = this.selectedImage.display_url || this.selectedImage.url || `/api/v1/image/${this.selectedImage.filename}`;
        this.http.get(`${this.apiConfig.getBaseUrl()}${imageUrl}`, {
            responseType: "blob"
        })
            .pipe(takeUntilDestroyed(this.destroyRef))
            .subscribe({
                next: (blob) => {
                    this.cachedImageBlob = blob;
                    this.renderCanvasWithImage(blob, false);
                },
                error: (error) => {
                    console.error("Failed to load image:", error);
                    this.notificationService.error(this.translate.instant("textOverlayEditor.errors.loadImagesFailed"));
                }
            });
    }

    updateCanvasPreview(): void {
        if (!this.cachedImageBlob) return;
        this.renderCanvasWithImage(this.cachedImageBlob, true);
    }

    private renderCanvasWithImage(blob: Blob, withText: boolean): void {
        if (!this.canvasRef) return;

        const canvas = this.canvasRef.nativeElement;
        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        const objectUrl = URL.createObjectURL(blob);
        const img = new Image();
        img.onload = () => {
            canvas.width = img.width;
            canvas.height = img.height;
            ctx.drawImage(img, 0, 0);

            if (withText) {
                this.drawTextOverlay(ctx, canvas);
            }

            URL.revokeObjectURL(objectUrl);
        };
        img.src = objectUrl;
    }

    drawTextOverlay(ctx: CanvasRenderingContext2D, canvas: HTMLCanvasElement): void {
        const formValues = this.form.value;
        const title = formValues.title || "";
        const artist = formValues.artist || "";
        const fontStyle = formValues.fontStyle || "bold";

        // V2 parameters - use getTitlePosition/getArtistPosition to support custom coordinates
        const titlePosition = this.getTitlePosition(formValues);
        const titleFontSize = formValues.titleFontSize || 80;  // Pixels
        const titleColor = formValues.titleColor || "#FFFFFF";
        const titleOutlineColor = formValues.titleOutlineColor || "#000000";
        const artistPosition = this.getArtistPosition(formValues);
        const artistFontSize = formValues.artistFontSize || 40;  // Pixels
        const artistColor = formValues.artistColor || titleColor;
        const artistOutlineColor = formValues.artistOutlineColor || titleOutlineColor;
        const artistFontStyle = formValues.useCustomArtistFont ? (formValues.artistFontStyle || fontStyle) : fontStyle;

        if (!title) return;

        // Map fontStyle to CSS font family (matching backend TTF fonts)
        const getFontFamily = (style: string): string => {
            switch (style) {
                // Original fonts
                case "bold":
                    return "Anton, Arial Black, sans-serif";
                case "elegant":
                    return "\"Playfair Display\", Georgia, serif";
                case "light":
                    return "\"Roboto Light\", Arial, sans-serif";
                // Comic styles
                case "bangers":
                    return "Bangers, Impact, sans-serif";
                case "comic":
                    return "\"Comic Neue\", \"Comic Sans MS\", sans-serif";
                case "bubblegum":
                    return "\"Bubblegum Sans\", cursive, sans-serif";
                case "righteous":
                    return "Righteous, Impact, sans-serif";
                // Display fonts
                case "bebas":
                    return "\"Bebas Neue\", Impact, sans-serif";
                case "bungee":
                    return "Bungee, Impact, sans-serif";
                case "montserrat":
                    return "Montserrat, Helvetica, sans-serif";
                case "oswald":
                    return "Oswald, Arial Narrow, sans-serif";
                default:
                    return "sans-serif";
            }
        };

        const titleFontFamily = getFontFamily(fontStyle);

        // Draw title
        const titleText = title.toUpperCase();
        const titleFontSizePx = titleFontSize;  // Already in pixels
        ctx.font = `bold ${titleFontSizePx}px ${titleFontFamily}`;

        this.drawText(ctx, canvas, {
            text: titleText,
            position: titlePosition,
            fontSizePct: titleFontSize,  // Actually pixels now
            color: titleColor,
            outlineColor: titleOutlineColor,
            fontFamily: titleFontFamily,
            offsetY: 0
        });

        // Draw artist if provided
        if (artist) {
            const artistText = `BY ${artist.toUpperCase()}`;
            const artistFontFamily = getFontFamily(artistFontStyle);

            this.drawText(ctx, canvas, {
                text: artistText,
                position: artistPosition,
                fontSizePct: artistFontSize,  // Already in pixels
                color: artistColor,
                outlineColor: artistOutlineColor,
                fontFamily: artistFontFamily,
                offsetY: 0,
                textAlignOverride: undefined,
                xOffsetPx: 0
            });
        }

        // Draw visual markers for positions (showing top-left anchor point)
        this.drawPositionMarker(ctx, canvas, titlePosition.x * 100, titlePosition.y * 100);

        if (artist && artistPosition) {
            this.drawPositionMarker(ctx, canvas, artistPosition.x * 100, artistPosition.y * 100);
        }
    }

    private drawPositionMarker(
        ctx: CanvasRenderingContext2D,
        canvas: HTMLCanvasElement,
        xPct: number,
        yPct: number
    ): void {
        // The marker shows the top-left corner of the text (matches Pillow default anchor)
        // This is where the text rendering starts
        const x = (xPct / 100) * canvas.width;
        const y = (yPct / 100) * canvas.height;

        // Save context
        ctx.save();

        // Draw marker at text start position (top-left)
        ctx.strokeStyle = "#FF0000";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(x - 10, y);
        ctx.lineTo(x + 10, y);
        ctx.moveTo(x, y - 10);
        ctx.lineTo(x, y + 10);
        ctx.stroke();

        // Circle
        ctx.beginPath();
        ctx.arc(x, y, 5, 0, 2 * Math.PI);
        ctx.stroke();

        // Restore context
        ctx.restore();
    }

    private drawText(
        ctx: CanvasRenderingContext2D,
        canvas: HTMLCanvasElement,
        options: {
            text: string;
            position: string | { x: number; y: number };
            fontSizePct: number;
            color: string;
            outlineColor: string;
            fontFamily: string;
            offsetY: number;
            textAlignOverride?: "left" | "center" | "right";
            xOffsetPx?: number;
        }
    ): void {
        const {
            text,
            position,
            fontSizePct,
            color,
            outlineColor,
            fontFamily,
            offsetY,
            textAlignOverride,
            xOffsetPx
        } = options;

        // Check if position is custom (object) or grid (string)
        let gridXPct: number;
        let gridYPct: number;
        const isCustomPosition = typeof position === "object";

        if (isCustomPosition) {
            // Custom position (x, y as 0.0-1.0)
            gridXPct = position.x;
            gridYPct = position.y;
        } else {
            // Grid position mappings (3x3 grid) - matches backend V2 service
            const gridPositions: Record<string, [number, number]> = {
                "top-left": [0.10, 0.10],
                "top-center": [0.50, 0.10],
                "top-right": [0.90, 0.10],
                "middle-left": [0.10, 0.50],
                "center": [0.50, 0.50],
                "middle-right": [0.90, 0.50],
                "bottom-left": [0.10, 0.90],
                "bottom-center": [0.50, 0.90],
                "bottom-right": [0.90, 0.90]
            };

            [gridXPct, gridYPct] = gridPositions[position] || [0.50, 0.50];
        }

        // Font size is already in pixels
        const fontSize = fontSizePct;
        ctx.font = `bold ${fontSize}px ${fontFamily}`;

        // For CUSTOM positions: always use left-align and top baseline (matches Pillow default)
        // For GRID positions: use the old alignment logic
        if (isCustomPosition) {
            ctx.textAlign = "left";
            ctx.textBaseline = "top";
            const x = canvas.width * gridXPct;
            const y = canvas.height * gridYPct;

            // Draw outline (stroke)
            ctx.strokeStyle = outlineColor;
            ctx.lineWidth = 3;
            ctx.strokeText(text, x, y);

            // Draw fill
            ctx.fillStyle = color;
            ctx.fillText(text, x, y);
        } else {
            // GRID POSITION: Use old alignment logic
            const textHeight = fontSize;
            let x = canvas.width * gridXPct;

            if (xOffsetPx) {
                x += xOffsetPx;
            }

            if (textAlignOverride) {
                ctx.textAlign = textAlignOverride;
            } else if (gridXPct === 0.10) {
                ctx.textAlign = "left";
            } else if (gridXPct === 0.90) {
                ctx.textAlign = "right";
            } else {
                ctx.textAlign = "center";
            }

            let y = 0;
            if (gridYPct === 0.10) {
                y = canvas.height * gridYPct + textHeight / 2;
                ctx.textBaseline = "top";
            } else if (gridYPct === 0.90) {
                y = canvas.height * gridYPct - textHeight / 2;
                ctx.textBaseline = "bottom";
            } else {
                y = canvas.height * gridYPct;
                ctx.textBaseline = "middle";
            }

            y += offsetY;

            // Draw outline (stroke)
            ctx.strokeStyle = outlineColor;
            ctx.lineWidth = 3;
            ctx.strokeText(text, x, y);

            // Draw fill
            ctx.fillStyle = color;
            ctx.fillText(text, x, y);
        }
    }

    activateCanvasClick(target: "title" | "artist"): void {
        this.isCanvasClickMode = true;
        this.currentClickTarget = target;
    }

    onCanvasClick(event: MouseEvent): void {
        if (!this.isCanvasClickMode || !this.canvasRef) return;

        const canvas = this.canvasRef.nativeElement;
        const rect = canvas.getBoundingClientRect();

        // IMPORTANT: Account for CSS scaling
        // rect.width/height = displayed size (e.g., 500x500)
        // canvas.width/height = actual canvas resolution (e.g., 1024x1024)
        // We need percentage of the ACTUAL canvas, not the displayed size

        // Click position relative to displayed canvas
        const clickX = event.clientX - rect.left;
        const clickY = event.clientY - rect.top;

        // Scale factor between display and actual canvas
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;

        // Actual canvas coordinates
        const actualX = clickX * scaleX;
        const actualY = clickY * scaleY;

        // Convert to percentage (0-100) of actual canvas
        const xPct = Math.round((actualX / canvas.width) * 100);
        const yPct = Math.round((actualY / canvas.height) * 100);

        // Clamping
        const xClamped = Math.max(0, Math.min(100, xPct));
        const yClamped = Math.max(0, Math.min(100, yPct));

        // Update form based on target
        if (this.currentClickTarget === "title") {
            this.form.patchValue({
                titlePositionCustomX: xClamped,
                titlePositionCustomY: yClamped
            });
        } else if (this.currentClickTarget === "artist") {
            this.form.patchValue({
                artistPositionCustomX: xClamped,
                artistPositionCustomY: yClamped
            });
        }

        // Deactivate click mode
        this.isCanvasClickMode = false;
        this.currentClickTarget = null;
    }

    private getTitlePosition(formValues: any): { x: number; y: number } {
        // Always custom position
        return {
            x: formValues.titlePositionCustomX / 100,  // 50 → 0.50
            y: formValues.titlePositionCustomY / 100
        };
    }

    private getArtistPosition(formValues: any): { x: number; y: number } {
        // Always custom position
        return {
            x: formValues.artistPositionCustomX / 100,
            y: formValues.artistPositionCustomY / 100
        };
    }

    applyTextOverlay(): void {
        if (!this.form.valid || !this.selectedImage) {
            this.notificationService.error(this.translate.instant("textOverlayEditor.errors.formInvalid"));
            return;
        }

        this.isProcessing = true;
        const formValues = this.form.value;

        // Convert pixel font sizes to percentage (backend expects 0.0-1.0)
        // Assuming 1024px image height as reference, 80px = ~0.078 (7.8%)
        const titleFontSizePct = formValues.titleFontSize / 1024;
        const artistFontSizePct = formValues.artistFontSize / 1024;

        const payload = {
            image_id: formValues.imageId,
            title: formValues.title,
            artist: formValues.artist || null,
            font_style: formValues.fontStyle,
            // V2 parameters with custom position support
            title_position: this.getTitlePosition(formValues),
            title_font_size: titleFontSizePct,
            title_color: formValues.titleColor,
            title_outline_color: formValues.titleOutlineColor,
            artist_position: this.getArtistPosition(formValues),
            artist_font_size: artistFontSizePct,
            artist_color: formValues.artistColor,
            artist_outline_color: formValues.artistOutlineColor,
            artist_font_style: formValues.useCustomArtistFont ? formValues.artistFontStyle : null
        };

        this.http.post<{ image_id: string; image_url: string }>(
            this.apiConfig.endpoints.image.addTextOverlay,
            payload
        )
            .pipe(takeUntilDestroyed(this.destroyRef))
            .subscribe({
                next: (response) => {
                    this.isProcessing = false;
                    this.resultImageFilePath = response.image_url;
                    this.notificationService.success(this.translate.instant("textOverlayEditor.success.applied"));
                    this.loadImages(); // Reload image list
                },
                error: (error) => {
                    this.isProcessing = false;
                    console.error("Failed to apply text overlay:", error);
                    this.notificationService.error(this.translate.instant("textOverlayEditor.errors.applyFailed"));
                }
            });
    }

    downloadResult(): void {
        if (!this.resultImageFilePath) return;

        // Download via HttpClient with JWT token (resultImageFilePath already contains full path like /api/v1/image/filename.png)
        this.http.get(`${this.apiConfig.getBaseUrl()}${this.resultImageFilePath}`, {
            responseType: "blob"
        })
            .pipe(takeUntilDestroyed(this.destroyRef))
            .subscribe({
                next: (blob) => {
                    const url = URL.createObjectURL(blob);
                    const link = document.createElement("a");
                    link.href = url;
                    link.download = `text-overlay-${Date.now()}.png`;
                    link.click();
                    URL.revokeObjectURL(url);
                },
                error: (error) => {
                    console.error("Failed to download image:", error);
                    this.notificationService.error(this.translate.instant("textOverlayEditor.errors.applyFailed"));
                }
            });
    }
}
