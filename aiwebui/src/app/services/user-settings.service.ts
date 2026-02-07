import {Injectable} from "@angular/core";
import {BehaviorSubject, Observable} from "rxjs";
import {DEFAULT_USER_SETTINGS, Language, UserSettings} from "../models/user-settings.model";

@Injectable({
    providedIn: "root"
})
export class UserSettingsService {
    private readonly STORAGE_KEY = "user-settings";
    private settingsSubject = new BehaviorSubject<UserSettings>(this.loadSettings());

    constructor() {
    }

    getSettings(): Observable<UserSettings> {
        return this.settingsSubject.asObservable();
    }

    getCurrentSettings(): UserSettings {
        return this.settingsSubject.value;
    }

    updateSettings(settings: Partial<UserSettings>): void {
        const currentSettings = this.settingsSubject.value;
        const newSettings = {...currentSettings, ...settings};
        this.settingsSubject.next(newSettings);
        this.saveSettings(newSettings);
    }

    updateSongListLimit(limit: number): void {
        this.updateSettings({songListLimit: limit});
    }

    updateImageListLimit(limit: number): void {
        this.updateSettings({imageListLimit: limit});
    }

    updatePromptListLimit(limit: number): void {
        this.updateSettings({promptListLimit: limit});
    }

    updateSketchListLimit(limit: number): void {
        this.updateSettings({sketchListLimit: limit});
    }

    updateEquipmentListLimit(limit: number): void {
        this.updateSettings({equipmentListLimit: limit});
    }

    updateLanguage(language: Language): void {
        this.updateSettings({language});
    }

    resetToDefaults(): void {
        this.settingsSubject.next(DEFAULT_USER_SETTINGS);
        this.saveSettings(DEFAULT_USER_SETTINGS);
    }

    private loadSettings(): UserSettings {
        try {
            const stored = localStorage.getItem(this.STORAGE_KEY);
            if (stored) {
                const parsed = JSON.parse(stored);
                return {...DEFAULT_USER_SETTINGS, ...parsed};
            }
        } catch (error) {
            console.warn("Error loading user settings from localStorage:", error);
        }
        return DEFAULT_USER_SETTINGS;
    }

    private saveSettings(settings: UserSettings): void {
        try {
            localStorage.setItem(this.STORAGE_KEY, JSON.stringify(settings));
        } catch (error) {
            console.error("Error saving user settings to localStorage:", error);
        }
    }
}