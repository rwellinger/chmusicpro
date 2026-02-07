import {Component, inject, OnInit} from "@angular/core";
import {RouterOutlet} from "@angular/router";
import {CommonModule} from "@angular/common";
import {TranslateModule} from "@ngx-translate/core";
import {SideMenuComponent} from "./components/side-menu/side-menu.component";
import {AuthService} from "./services/business/auth.service";
import {VersionCheckService} from "./services/config/version-check.service";
import {DeviceService} from "./services/ui/device.service";

@Component({
    selector: "app-root",
    standalone: true,
    imports: [RouterOutlet, SideMenuComponent, CommonModule, TranslateModule],
    templateUrl: "./app.component.html",
    styleUrl: "./app.component.scss"
})
export class AppComponent implements OnInit {
    title = "aiwebui";
    showMobileWarning = false;
    showLandscapeWarning = false;

    private authService = inject(AuthService);
    private versionCheckService = inject(VersionCheckService);
    private deviceService = inject(DeviceService);

    public authState$ = this.authService.authState$;

    ngOnInit(): void {
        // Version-Check beim App-Start initialisieren
        this.versionCheckService.initVersionCheck();

        // Check device warnings
        this.checkDeviceWarnings();
        window.addEventListener("resize", () => this.checkDeviceWarnings());
    }

    private checkDeviceWarnings(): void {
        const width = window.innerWidth;
        const height = window.innerHeight;

        // Mobile warning (< 768px)
        this.showMobileWarning = width < 768;

        // iPad Portrait warning (768-1024px AND height > width AND touch device)
        this.showLandscapeWarning = !this.showMobileWarning &&
            width >= 768 &&
            width <= 1024 &&
            height > width &&
            this.deviceService.isTouchDevice;
    }
}
