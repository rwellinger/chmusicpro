import {Component, inject, OnDestroy, OnInit} from "@angular/core";
import {CommonModule} from "@angular/common";
import {MAT_DIALOG_DATA, MatDialogModule, MatDialogRef} from "@angular/material/dialog";
import {MatButtonModule} from "@angular/material/button";
import {MatIconModule} from "@angular/material/icon";
import {TranslateModule, TranslateService} from "@ngx-translate/core";
import {Subject} from "rxjs";

import {MUSIC_STYLE_CATEGORIES, MusicStyleChooserConfig} from "../../models/music-style-chooser.model";
import {MusicStyleChooserService} from "../../services/music-style-chooser.service";
import {NotificationService} from "../../services/ui/notification.service";

@Component({
    selector: "app-music-style-chooser-modal",
    standalone: true,
    imports: [
        CommonModule,
        TranslateModule,
        MatDialogModule,
        MatButtonModule,
        MatIconModule
    ],
    templateUrl: "./music-style-chooser-modal.component.html",
    styleUrl: "./music-style-chooser-modal.component.scss"
})
export class MusicStyleChooserModalComponent implements OnInit, OnDestroy {
    config: MusicStyleChooserConfig = {
        selectedStyles: [],
        selectedThemes: [],
        selectedInstruments: [],
        lastModified: new Date()
    };
    availableStyles: string[] = MUSIC_STYLE_CATEGORIES.style;
    availableThemes: string[] = MUSIC_STYLE_CATEGORIES.theme;
    availableInstruments: string[] = MUSIC_STYLE_CATEGORIES.instruments;
    isInstrumental = false;

    private destroy$ = new Subject<void>();

    private styleChooserService = inject(MusicStyleChooserService);
    private notificationService = inject(NotificationService);
    private translateService = inject(TranslateService);
    private dialogRef = inject(MatDialogRef<MusicStyleChooserModalComponent>);
    private data = inject<{ isInstrumental?: boolean }>(MAT_DIALOG_DATA);

    constructor() {
        this.isInstrumental = this.data?.isInstrumental || false;
    }

    ngOnInit(): void {
        this.loadConfig();
        this.filterInstrumentsForMode();
    }

    ngOnDestroy(): void {
        this.destroy$.next();
        this.destroy$.complete();
    }

    loadConfig(): void {
        this.config = this.styleChooserService.getConfig();
    }

    filterInstrumentsForMode(): void {
        // Clean up legacy 'vocals' from saved config
        this.config.selectedInstruments = this.config.selectedInstruments.filter(
            instrument => instrument !== "vocals"
        );

        if (this.isInstrumental) {
            // Remove male-voice and female-voice for instrumental mode
            this.availableInstruments = MUSIC_STYLE_CATEGORIES.instruments.filter(
                instrument => instrument !== "male-voice" && instrument !== "female-voice"
            );
            // Also remove them from selected instruments if they were previously selected
            this.config.selectedInstruments = this.config.selectedInstruments.filter(
                instrument => instrument !== "male-voice" && instrument !== "female-voice"
            );
        } else {
            // Show all instruments for normal mode
            this.availableInstruments = [...MUSIC_STYLE_CATEGORIES.instruments];

            // Note: Auto-select male-voice removed - Mureka ignores voice selection anyway
        }
    }

    toggleStyle(style: string): void {
        try {
            this.config = this.styleChooserService.toggleStyle(style);
        } catch (error: any) {
            console.error("Error toggling style:", error);
            this.notificationService.error(error.message);
        }
    }

    toggleTheme(theme: string): void {
        try {
            this.config = this.styleChooserService.toggleTheme(theme);
        } catch (error: any) {
            console.error("Error toggling theme:", error);
            this.notificationService.error(error.message);
        }
    }

    toggleInstrument(instrument: string): void {
        try {
            // Handle voice selection for non-instrumental mode
            if (!this.isInstrumental && (instrument === "male-voice" || instrument === "female-voice")) {
                const isCurrentlySelected = this.isInstrumentSelected(instrument);

                if (!isCurrentlySelected) {
                    // Deselect the other voice first
                    const otherVoice = instrument === "male-voice" ? "female-voice" : "male-voice";
                    if (this.isInstrumentSelected(otherVoice)) {
                        this.config = this.styleChooserService.toggleInstrument(otherVoice);
                    }
                }
            }

            this.config = this.styleChooserService.toggleInstrument(instrument);
        } catch (error: any) {
            console.error("Error toggling instrument:", error);
            this.notificationService.error(error.message);
        }
    }

    isStyleSelected(style: string): boolean {
        return this.styleChooserService.isStyleSelected(style, this.config);
    }

    isThemeSelected(theme: string): boolean {
        return this.styleChooserService.isThemeSelected(theme, this.config);
    }

    isInstrumentSelected(instrument: string): boolean {
        return this.styleChooserService.isInstrumentSelected(instrument, this.config);
    }

    reset(): void {
        this.config = this.styleChooserService.resetToDefault();
        this.notificationService.success(this.translateService.instant("musicStyleChooser.messages.resetSuccess"));
    }

    save(): void {
        try {
            // Note: Voice validation removed - Mureka ignores "no vocals" setting anyway
            // and randomly selects voices regardless of the prompt instruction.
            // Keeping this for future reference if Mureka fixes this behavior.

            this.styleChooserService.saveConfig(this.config);
            const stylePrompt = this.styleChooserService.generateStylePrompt(this.config, this.isInstrumental);

            this.dialogRef.close({
                config: this.config,
                stylePrompt: stylePrompt
            });
        } catch (error: any) {
            this.notificationService.error(this.translateService.instant("musicStyleChooser.messages.saveError", {message: error.message}));
        }
    }

    cancel(): void {
        this.dialogRef.close();
    }

    getPreviewText(): string {
        const prompt = this.styleChooserService.generateStylePrompt(this.config, this.isInstrumental);
        return prompt || this.translateService.instant("musicStyleChooser.preview.empty");
    }

    getSelectionSummary(): string {
        const stylesCount = this.config.selectedStyles.length;
        const themesCount = this.config.selectedThemes.length;
        const instrumentsCount = this.config.selectedInstruments.length;

        if (stylesCount === 0 && themesCount === 0 && instrumentsCount === 0) {
            return this.translateService.instant("musicStyleChooser.summary.empty");
        }

        const parts = [];
        if (stylesCount > 0) {
            const styleKey = stylesCount > 1 ? "musicStyleChooser.summary.styles" : "musicStyleChooser.summary.style";
            parts.push(`${stylesCount} ${this.translateService.instant(styleKey)}`);
        }
        if (instrumentsCount > 0) {
            const instrumentKey = instrumentsCount > 1 ? "musicStyleChooser.summary.instruments" : "musicStyleChooser.summary.instrument";
            parts.push(`${instrumentsCount} ${this.translateService.instant(instrumentKey)}`);
        }
        if (themesCount > 0) {
            const themeKey = themesCount > 1 ? "musicStyleChooser.summary.themes" : "musicStyleChooser.summary.theme";
            parts.push(`${themesCount} ${this.translateService.instant(themeKey)}`);
        }

        return parts.join(", ") + " " + this.translateService.instant("musicStyleChooser.summary.selected");
    }
}