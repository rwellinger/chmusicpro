import {inject, Injectable} from "@angular/core";
import {BreakpointObserver, Breakpoints} from "@angular/cdk/layout";
import {map, shareReplay} from "rxjs/operators";

export enum DeviceType {
    DESKTOP = "desktop",
    TABLET = "tablet",
    MOBILE = "mobile"
}

@Injectable({providedIn: "root"})
export class DeviceService {
    private breakpoints = inject(BreakpointObserver);

    // Observable breakpoint matchers
    isHandset$ = this.breakpoints.observe([Breakpoints.Handset])
        .pipe(map(result => result.matches), shareReplay(1));

    isTablet$ = this.breakpoints.observe([Breakpoints.Tablet])
        .pipe(map(result => result.matches), shareReplay(1));

    isDesktop$ = this.breakpoints.observe([Breakpoints.Web, Breakpoints.WebLandscape])
        .pipe(map(result => result.matches), shareReplay(1));

    // Touch device detection
    isTouchDevice = "ontouchstart" in window || navigator.maxTouchPoints > 0;

    // Hover capability (false for touch-only devices)
    hasHoverCapability = window.matchMedia("(hover: hover)").matches;

    // Current device type (synchronous)
    getCurrentDeviceType(): DeviceType {
        const width = window.innerWidth;
        if (width < 768) return DeviceType.MOBILE;
        if (width < 1024) return DeviceType.TABLET;
        return DeviceType.DESKTOP;
    }

    // Check if mobile (for blocking)
    isMobileDevice(): boolean {
        return this.getCurrentDeviceType() === DeviceType.MOBILE;
    }

    // Check if iPad/Tablet
    isTabletDevice(): boolean {
        return this.getCurrentDeviceType() === DeviceType.TABLET;
    }
}
