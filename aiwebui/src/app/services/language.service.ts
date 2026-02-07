import {inject, Injectable} from "@angular/core";
import {TranslateService} from "@ngx-translate/core";
import {UserSettingsService} from "./user-settings.service";
import {Language} from "../models/user-settings.model";
import {firstValueFrom} from "rxjs";

@Injectable({
    providedIn: "root"
})
export class LanguageService {
    private translateService = inject(TranslateService);
    private settingsService = inject(UserSettingsService);

    /**
     * Initialize language from user settings
     * Used by APP_INITIALIZER to ensure translations are loaded before app starts
     */
    public async initialize(): Promise<void> {
        try {
            const settings = this.settingsService.getCurrentSettings();
            const currentLang = settings.language || "en";

            // Wait for translation loading to complete before app starts
            await firstValueFrom(this.translateService.use(currentLang));
        } catch (error) {
            console.error("Error loading translations:", error);
            // Fallback to default language
            await firstValueFrom(this.translateService.use("en"));
        }
    }

    /**
     * Change the current language
     */
    public changeLanguage(language: Language): void {
        this.translateService.use(language).subscribe({
            next: () => this.settingsService.updateLanguage(language),
            error: (error) => console.error("Error changing language:", error)
        });
    }

    /**
     * Get the current language
     */
    public getCurrentLanguage(): Language {
        return this.settingsService.getCurrentSettings().language;
    }

    /**
     * Get available languages
     */
    public getAvailableLanguages(): { code: Language, name: string }[] {
        return [
            {code: "en", name: "English"},
            {code: "de", name: "Deutsch"}
        ];
    }
}
