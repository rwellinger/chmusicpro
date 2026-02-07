import {Component, EventEmitter, inject, Input, OnDestroy, OnInit, Output} from "@angular/core";
import {CommonModule} from "@angular/common";
import {MatButtonModule} from "@angular/material/button";
import {MatIconModule} from "@angular/material/icon";
import {TranslateModule, TranslateService} from "@ngx-translate/core";
import {Subject} from "rxjs";

import {MUSIC_STYLE_CATEGORIES, MusicStyleChooserConfig} from "../../models/music-style-chooser.model";
import {MusicStyleChooserService} from "../../services/music-style-chooser.service";
import {NotificationService} from "../../services/ui/notification.service";

@Component({
    selector: "app-music-style-chooser-inline",
    standalone: true,
    imports: [
        CommonModule,
        TranslateModule,
        MatButtonModule,
        MatIconModule
    ],
    templateUrl: "./music-style-chooser-inline.component.html",
    styleUrl: "./music-style-chooser-inline.component.scss"
})
export class MusicStyleChooserInlineComponent implements OnInit, OnDestroy {
    @Input() mode: "auto" | "manual" = "auto";
    @Input() isInstrumental = false;
    @Input() isCollapsed = false;
    @Output() styleChanged = new EventEmitter<string>();
    @Output() applyStyles = new EventEmitter<string>();
    @Output() collapseToggled = new EventEmitter<boolean>();

    config: MusicStyleChooserConfig = {
        selectedStyles: [],
        selectedThemes: [],
        selectedInstruments: [],
        lastModified: new Date()
    };
    availableStyles: string[] = MUSIC_STYLE_CATEGORIES.style;
    availableThemes: string[] = MUSIC_STYLE_CATEGORIES.theme;
    availableInstruments: string[] = MUSIC_STYLE_CATEGORIES.instruments;
    expandedCategory: "styles" | "instruments" | "themes" | null = "styles";

    private destroy$ = new Subject<void>();

    private styleChooserService = inject(MusicStyleChooserService);
    private notificationService = inject(NotificationService);
    private translateService = inject(TranslateService);

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
        }
    }

    toggleStyle(style: string): void {
        try {
            this.config = this.styleChooserService.toggleStyle(style);
            this.emitChange();
        } catch (error: any) {
            console.error("Error toggling style:", error);
            this.notificationService.error(error.message);
        }
    }

    toggleTheme(theme: string): void {
        try {
            this.config = this.styleChooserService.toggleTheme(theme);
            this.emitChange();
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
            this.emitChange();
        } catch (error: any) {
            console.error("Error toggling instrument:", error);
            this.notificationService.error(error.message);
        }
    }

    private emitChange(): void {
        const stylePrompt = this.styleChooserService.generateStylePrompt(this.config, this.isInstrumental);

        if (this.mode === "auto") {
            // Auto-mode: Emit immediately
            this.styleChanged.emit(stylePrompt);
        }
        // Manual-mode: Don't emit, just update preview
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
        this.emitChange();
    }

    applyStylesClick(): void {
        const stylePrompt = this.styleChooserService.generateStylePrompt(this.config, this.isInstrumental);
        this.applyStyles.emit(stylePrompt);
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

    toggleCollapse(): void {
        this.isCollapsed = !this.isCollapsed;
        this.collapseToggled.emit(this.isCollapsed);
    }

    toggleCategory(category: "styles" | "instruments" | "themes"): void {
        if (this.expandedCategory === category) {
            this.expandedCategory = null;
        } else {
            this.expandedCategory = category;
        }
    }

    isCategoryExpanded(category: "styles" | "instruments" | "themes"): boolean {
        return this.expandedCategory === category;
    }

    getSelectedCount(category: "styles" | "instruments" | "themes"): number {
        switch (category) {
            case "styles":
                return this.config.selectedStyles.length;
            case "instruments":
                return this.config.selectedInstruments.length;
            case "themes":
                return this.config.selectedThemes.length;
        }
    }
}
