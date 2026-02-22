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

    // Drag mode for positioning markers
    isDragging = false;
    isHoveringMarker = false;
    private dragTarget: "title" | "artist" | "extra1" | "extra2" | null = null;
    private dragPositionPct: { x: number; y: number } | null = null;
    private cachedImage: HTMLImageElement | null = null;
    private animFrameId: number | null = null;
    private boundOnDocMouseMove = this.onDocMouseMove.bind(this);
    private boundOnDocMouseUp = this.onDocMouseUp.bind(this);

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
            // Extra Text 1 (optional freetext, rendered as-is)
            extraText1: [""],
            extraText1PositionCustomX: [50],
            extraText1PositionCustomY: [80],
            extraText1FontSize: [30],
            extraText1Color: [null],  // null = same as title
            extraText1OutlineColor: [null],
            useCustomExtraText1Font: [false],
            extraText1FontStyle: [null],
            // Extra Text 2 (optional freetext, rendered as-is)
            extraText2: [""],
            extraText2PositionCustomX: [50],
            extraText2PositionCustomY: [85],
            extraText2FontSize: [30],
            extraText2Color: [null],
            extraText2OutlineColor: [null],
            useCustomExtraText2Font: [false],
            extraText2FontStyle: [null],
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
            this.cachedImage = img;

            if (withText) {
                this.drawTextOverlay(ctx, canvas);
            }

            URL.revokeObjectURL(objectUrl);
        };
        img.src = objectUrl;
    }

    drawTextOverlay(ctx: CanvasRenderingContext2D, canvas: HTMLCanvasElement): void {
        this.drawTextOverlayWithValues(ctx, canvas, this.form.value);
    }

    private drawTextOverlayWithValues(
        ctx: CanvasRenderingContext2D,
        canvas: HTMLCanvasElement,
        formValues: any,
        dragOverride?: { target: "title" | "artist" | "extra1" | "extra2"; position: { x: number; y: number } }
    ): void {
        const title = formValues.title || "";
        const artist = formValues.artist || "";
        const fontStyle = formValues.fontStyle || "bold";

        // V2 parameters - use getTitlePosition/getArtistPosition to support custom coordinates
        let titlePosition = this.getTitlePosition(formValues);
        const titleFontSize = formValues.titleFontSize || 80;
        const titleColor = formValues.titleColor || "#FFFFFF";
        const titleOutlineColor = formValues.titleOutlineColor || "#000000";
        let artistPosition = this.getArtistPosition(formValues);
        const artistFontSize = formValues.artistFontSize || 40;
        const artistColor = formValues.artistColor || titleColor;
        const artistOutlineColor = formValues.artistOutlineColor || titleOutlineColor;
        const artistFontStyle = formValues.useCustomArtistFont ? (formValues.artistFontStyle || fontStyle) : fontStyle;

        // Extra text fields
        const extraText1 = formValues.extraText1 || "";
        let extraText1Position = this.getExtraText1Position(formValues);
        const extraText1FontSize = formValues.extraText1FontSize || 30;
        const extraText1Color = formValues.extraText1Color || titleColor;
        const extraText1OutlineColor = formValues.extraText1OutlineColor || titleOutlineColor;
        const extraText1FontStyle = formValues.useCustomExtraText1Font ? (formValues.extraText1FontStyle || fontStyle) : fontStyle;

        const extraText2 = formValues.extraText2 || "";
        let extraText2Position = this.getExtraText2Position(formValues);
        const extraText2FontSize = formValues.extraText2FontSize || 30;
        const extraText2Color = formValues.extraText2Color || titleColor;
        const extraText2OutlineColor = formValues.extraText2OutlineColor || titleOutlineColor;
        const extraText2FontStyle = formValues.useCustomExtraText2Font ? (formValues.extraText2FontStyle || fontStyle) : fontStyle;

        // Apply drag override
        if (dragOverride) {
            if (dragOverride.target === "title") {
                titlePosition = dragOverride.position;
            } else if (dragOverride.target === "artist") {
                artistPosition = dragOverride.position;
            } else if (dragOverride.target === "extra1") {
                extraText1Position = dragOverride.position;
            } else if (dragOverride.target === "extra2") {
                extraText2Position = dragOverride.position;
            }
        }

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
        const titleFontSizePx = titleFontSize;
        ctx.font = `bold ${titleFontSizePx}px ${titleFontFamily}`;

        this.drawText(ctx, canvas, {
            text: titleText,
            position: titlePosition,
            fontSizePct: titleFontSize,
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
                fontSizePct: artistFontSize,
                color: artistColor,
                outlineColor: artistOutlineColor,
                fontFamily: artistFontFamily,
                offsetY: 0,
                textAlignOverride: undefined,
                xOffsetPx: 0
            });
        }

        // Draw visual markers for positions (showing top-left anchor point)
        this.drawPositionMarker(ctx, canvas, titlePosition.x * 100, titlePosition.y * 100, "T");

        if (artist && artistPosition) {
            this.drawPositionMarker(ctx, canvas, artistPosition.x * 100, artistPosition.y * 100, "A");
        }

        // Draw extra text 1 if provided (rendered as-is, no uppercase)
        if (extraText1) {
            const et1FontFamily = getFontFamily(extraText1FontStyle);
            this.drawText(ctx, canvas, {
                text: extraText1,
                position: extraText1Position,
                fontSizePct: extraText1FontSize,
                color: extraText1Color,
                outlineColor: extraText1OutlineColor,
                fontFamily: et1FontFamily,
                offsetY: 0
            });
            this.drawPositionMarker(ctx, canvas, extraText1Position.x * 100, extraText1Position.y * 100, "1");
        }

        // Draw extra text 2 if provided (rendered as-is, no uppercase)
        if (extraText2) {
            const et2FontFamily = getFontFamily(extraText2FontStyle);
            this.drawText(ctx, canvas, {
                text: extraText2,
                position: extraText2Position,
                fontSizePct: extraText2FontSize,
                color: extraText2Color,
                outlineColor: extraText2OutlineColor,
                fontFamily: et2FontFamily,
                offsetY: 0
            });
            this.drawPositionMarker(ctx, canvas, extraText2Position.x * 100, extraText2Position.y * 100, "2");
        }
    }

    private drawPositionMarker(
        ctx: CanvasRenderingContext2D,
        canvas: HTMLCanvasElement,
        xPct: number,
        yPct: number,
        label: string = ""
    ): void {
        const x = (xPct / 100) * canvas.width;
        const y = (yPct / 100) * canvas.height;

        ctx.save();

        // Semi-transparent red fill circle
        ctx.fillStyle = "rgba(255, 0, 0, 0.25)";
        ctx.beginPath();
        ctx.arc(x, y, 12, 0, 2 * Math.PI);
        ctx.fill();

        // Crosshair arms (14px)
        ctx.strokeStyle = "#FF0000";
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        ctx.moveTo(x - 14, y);
        ctx.lineTo(x + 14, y);
        ctx.moveTo(x, y - 14);
        ctx.lineTo(x, y + 14);
        ctx.stroke();

        // Outer circle
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(x, y, 12, 0, 2 * Math.PI);
        ctx.stroke();

        // Label (T/A)
        if (label) {
            ctx.font = "bold 14px sans-serif";
            ctx.fillStyle = "#FF0000";
            ctx.textAlign = "left";
            ctx.textBaseline = "bottom";
            ctx.fillText(label, x + 15, y - 5);
        }

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

    onCanvasMouseDown(event: MouseEvent): void {
        if (!this.canvasRef) return;

        const canvas = this.canvasRef.nativeElement;
        const pct = this.eventToCanvasPct(event, canvas);
        const formValues = this.form.value;
        const hitThreshold = 20;

        // Collect all active markers with distances
        const markers: { target: "title" | "artist" | "extra1" | "extra2"; dist: number }[] = [];

        markers.push({target: "title", dist: this.markerDistanceInDisplayPx(pct, this.getTitlePosition(formValues), canvas)});

        if (formValues.artist) {
            markers.push({target: "artist", dist: this.markerDistanceInDisplayPx(pct, this.getArtistPosition(formValues), canvas)});
        }
        if (formValues.extraText1) {
            markers.push({target: "extra1", dist: this.markerDistanceInDisplayPx(pct, this.getExtraText1Position(formValues), canvas)});
        }
        if (formValues.extraText2) {
            markers.push({target: "extra2", dist: this.markerDistanceInDisplayPx(pct, this.getExtraText2Position(formValues), canvas)});
        }

        const nearest = markers.reduce((a, b) => a.dist < b.dist ? a : b);
        if (nearest.dist < hitThreshold) {
            this.dragTarget = nearest.target;
            this.isDragging = true;
            this.dragPositionPct = pct;

            document.addEventListener("mousemove", this.boundOnDocMouseMove);
            document.addEventListener("mouseup", this.boundOnDocMouseUp);
            event.preventDefault();
        }
    }

    onCanvasMouseMove(event: MouseEvent): void {
        if (this.isDragging) return;
        if (!this.canvasRef) return;

        const canvas = this.canvasRef.nativeElement;
        const pct = this.eventToCanvasPct(event, canvas);
        const formValues = this.form.value;

        const distances: number[] = [
            this.markerDistanceInDisplayPx(pct, this.getTitlePosition(formValues), canvas)
        ];
        if (formValues.artist) {
            distances.push(this.markerDistanceInDisplayPx(pct, this.getArtistPosition(formValues), canvas));
        }
        if (formValues.extraText1) {
            distances.push(this.markerDistanceInDisplayPx(pct, this.getExtraText1Position(formValues), canvas));
        }
        if (formValues.extraText2) {
            distances.push(this.markerDistanceInDisplayPx(pct, this.getExtraText2Position(formValues), canvas));
        }

        this.isHoveringMarker = Math.min(...distances) < 20;
    }

    private onDocMouseMove(event: MouseEvent): void {
        if (!this.isDragging || !this.canvasRef) return;

        const canvas = this.canvasRef.nativeElement;
        const pct = this.eventToCanvasPct(event, canvas);
        this.dragPositionPct = {
            x: Math.max(0, Math.min(1, pct.x)),
            y: Math.max(0, Math.min(1, pct.y))
        };

        if (this.animFrameId === null) {
            this.animFrameId = requestAnimationFrame(() => {
                this.renderDragPreview();
                this.animFrameId = null;
            });
        }
    }

    private onDocMouseUp(): void {
        if (!this.isDragging || !this.dragPositionPct || !this.dragTarget) return;

        const xClamped = Math.round(Math.max(0, Math.min(100, this.dragPositionPct.x * 100)));
        const yClamped = Math.round(Math.max(0, Math.min(100, this.dragPositionPct.y * 100)));

        if (this.dragTarget === "title") {
            this.form.patchValue({titlePositionCustomX: xClamped, titlePositionCustomY: yClamped});
        } else if (this.dragTarget === "artist") {
            this.form.patchValue({artistPositionCustomX: xClamped, artistPositionCustomY: yClamped});
        } else if (this.dragTarget === "extra1") {
            this.form.patchValue({extraText1PositionCustomX: xClamped, extraText1PositionCustomY: yClamped});
        } else if (this.dragTarget === "extra2") {
            this.form.patchValue({extraText2PositionCustomX: xClamped, extraText2PositionCustomY: yClamped});
        }

        document.removeEventListener("mousemove", this.boundOnDocMouseMove);
        document.removeEventListener("mouseup", this.boundOnDocMouseUp);
        this.isDragging = false;
        this.isHoveringMarker = false;
        this.dragTarget = null;
        this.dragPositionPct = null;

        if (this.animFrameId !== null) {
            cancelAnimationFrame(this.animFrameId);
            this.animFrameId = null;
        }
    }

    private renderDragPreview(): void {
        if (!this.canvasRef || !this.cachedImage || !this.dragTarget || !this.dragPositionPct) return;

        const canvas = this.canvasRef.nativeElement;
        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        ctx.drawImage(this.cachedImage, 0, 0);
        this.drawTextOverlayWithValues(ctx, canvas, this.form.value, {
            target: this.dragTarget,
            position: this.dragPositionPct
        });
    }

    private eventToCanvasPct(event: MouseEvent, canvas: HTMLCanvasElement): { x: number; y: number } {
        const rect = canvas.getBoundingClientRect();
        const clickX = event.clientX - rect.left;
        const clickY = event.clientY - rect.top;
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;
        return {
            x: (clickX * scaleX) / canvas.width,
            y: (clickY * scaleY) / canvas.height
        };
    }

    private markerDistanceInDisplayPx(
        pct: { x: number; y: number },
        markerPos: { x: number; y: number },
        canvas: HTMLCanvasElement
    ): number {
        const rect = canvas.getBoundingClientRect();
        const dx = (pct.x - markerPos.x) * rect.width;
        const dy = (pct.y - markerPos.y) * rect.height;
        return Math.sqrt(dx * dx + dy * dy);
    }

    private getTitlePosition(formValues: any): { x: number; y: number } {
        // Always custom position
        return {
            x: formValues.titlePositionCustomX / 100,  // 50 → 0.50
            y: formValues.titlePositionCustomY / 100
        };
    }

    private getArtistPosition(formValues: any): { x: number; y: number } {
        return {
            x: formValues.artistPositionCustomX / 100,
            y: formValues.artistPositionCustomY / 100
        };
    }

    private getExtraText1Position(formValues: any): { x: number; y: number } {
        return {
            x: formValues.extraText1PositionCustomX / 100,
            y: formValues.extraText1PositionCustomY / 100
        };
    }

    private getExtraText2Position(formValues: any): { x: number; y: number } {
        return {
            x: formValues.extraText2PositionCustomX / 100,
            y: formValues.extraText2PositionCustomY / 100
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
        const extraText1FontSizePct = formValues.extraText1FontSize / 1024;
        const extraText2FontSizePct = formValues.extraText2FontSize / 1024;

        const payload: Record<string, any> = {
            image_id: formValues.imageId,
            title: formValues.title,
            artist: formValues.artist || null,
            font_style: formValues.fontStyle,
            title_position: this.getTitlePosition(formValues),
            title_font_size: titleFontSizePct,
            title_color: formValues.titleColor,
            title_outline_color: formValues.titleOutlineColor,
            artist_position: this.getArtistPosition(formValues),
            artist_font_size: artistFontSizePct,
            artist_color: formValues.artistColor,
            artist_outline_color: formValues.artistOutlineColor,
            artist_font_style: formValues.useCustomArtistFont ? formValues.artistFontStyle : null,
            extra_text_1: formValues.extraText1 || null,
            extra_text_1_position: formValues.extraText1 ? this.getExtraText1Position(formValues) : null,
            extra_text_1_font_size: extraText1FontSizePct,
            extra_text_1_color: formValues.extraText1Color,
            extra_text_1_outline_color: formValues.extraText1OutlineColor,
            extra_text_1_font_style: formValues.useCustomExtraText1Font ? formValues.extraText1FontStyle : null,
            extra_text_2: formValues.extraText2 || null,
            extra_text_2_position: formValues.extraText2 ? this.getExtraText2Position(formValues) : null,
            extra_text_2_font_size: extraText2FontSizePct,
            extra_text_2_color: formValues.extraText2Color,
            extra_text_2_outline_color: formValues.extraText2OutlineColor,
            extra_text_2_font_style: formValues.useCustomExtraText2Font ? formValues.extraText2FontStyle : null,
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
