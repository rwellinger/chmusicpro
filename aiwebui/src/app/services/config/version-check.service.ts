import {inject, Injectable} from "@angular/core";
import {HttpClient} from "@angular/common/http";
import {interval, Observable} from "rxjs";
import {catchError, map, startWith, switchMap} from "rxjs/operators";
import {TranslateService} from "@ngx-translate/core";

export interface AppVersion {
    version: string;
    buildDate: string;
}

@Injectable({
    providedIn: "root"
})
export class VersionCheckService {
    private readonly VERSION_KEY = "app_version";
    private readonly VERSION_URL = "/aiwebui/assets/app-version.json";
    private readonly CHECK_INTERVAL = 15 * 60 * 1000; // 15 minutes

    private http = inject(HttpClient);
    private translate = inject(TranslateService);

    /**
     * Initialisiert den Version-Check beim App-Start
     * Prüft sofort und dann alle 15 Minuten
     */
    public initVersionCheck(): void {
        // Sofortiger Check beim Start
        this.checkVersion().subscribe();

        // Periodischer Check alle 15 Minuten
        interval(this.CHECK_INTERVAL)
            .pipe(
                startWith(0),
                switchMap(() => this.checkVersion())
            )
            .subscribe();
    }

    /**
     * Prüft ob eine neue Version verfügbar ist
     * @returns Observable mit Version-Info
     */
    public checkVersion(): Observable<AppVersion> {
        // Cache-Buster mit Timestamp
        const url = `${this.VERSION_URL}?t=${Date.now()}`;

        return this.http.get<AppVersion>(url).pipe(
            map((remoteVersion: AppVersion) => {
                const storedVersion = this.getStoredVersion();

                if (!storedVersion) {
                    // Erste Installation - Version speichern
                    this.setStoredVersion(remoteVersion.version);
                    console.log("[VersionCheck] Erste Installation:", remoteVersion.version);
                } else if (storedVersion !== remoteVersion.version) {
                    // Neue Version gefunden
                    console.log(
                        `[VersionCheck] Neue Version gefunden: ${storedVersion} → ${remoteVersion.version}`
                    );
                    this.handleNewVersion(remoteVersion);
                }

                return remoteVersion;
            }),
            catchError((error) => {
                console.warn("[VersionCheck] Fehler beim Version-Check:", error);
                // Silent fail - App läuft weiter
                return [];
            })
        );
    }

    /**
     * Behandelt den Fall einer neuen Version
     * Zeigt optional eine Warnung und lädt die Seite neu
     */
    private handleNewVersion(newVersion: AppVersion): void {
        // Version im Storage aktualisieren
        this.setStoredVersion(newVersion.version);

        // Optional: User-Warnung mit Countdown (auskommentiert für stillen Reload)
        // const confirmed = confirm(
        //   this.translate.instant('versionCheck.newVersion', { version: newVersion.version })
        // );

        // Automatischer Reload nach kurzer Verzögerung
        setTimeout(() => {
            console.log("[VersionCheck] Lade neue Version...");
            window.location.reload();
        }, 1000);
    }

    /**
     * Holt die gespeicherte Version aus localStorage
     */
    private getStoredVersion(): string | null {
        return localStorage.getItem(this.VERSION_KEY);
    }

    /**
     * Speichert die Version in localStorage
     */
    private setStoredVersion(version: string): void {
        localStorage.setItem(this.VERSION_KEY, version);
    }

    /**
     * Holt die aktuelle App-Version vom Server
     * Wird für manuelle Abfragen verwendet
     */
    public getCurrentVersion(): Observable<AppVersion> {
        const url = `${this.VERSION_URL}?t=${Date.now()}`;
        return this.http.get<AppVersion>(url).pipe(
            catchError((error) => {
                console.warn("[VersionCheck] Fehler beim Abrufen der Version:", error);
                throw error;
            })
        );
    }
}
