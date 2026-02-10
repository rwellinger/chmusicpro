import {Component, inject, OnDestroy, OnInit} from "@angular/core";
import {CommonModule} from "@angular/common";
import {Router, RouterModule} from "@angular/router";
import {TranslateModule, TranslateService} from "@ngx-translate/core";
import {firstValueFrom, Subject, takeUntil} from "rxjs";
import {MatTooltipModule} from "@angular/material/tooltip";
import {WorkshopService} from "../../services/business/workshop.service";
import {NotificationService} from "../../services/ui/notification.service";

interface DashboardTile {
    titleKey: string;
    descriptionKey: string;
    icon: string;
    iconColor: string;
    enabled: boolean;
    action: () => void;
}

@Component({
    selector: "app-dashboard",
    standalone: true,
    imports: [
        CommonModule,
        TranslateModule,
        RouterModule,
        MatTooltipModule
    ],
    templateUrl: "./dashboard.component.html",
    styleUrl: "./dashboard.component.scss"
})
export class DashboardComponent implements OnInit, OnDestroy {
    tiles: DashboardTile[] = [];
    isCreatingWorkshop = false;

    private router = inject(Router);
    private translate = inject(TranslateService);
    private workshopService = inject(WorkshopService);
    private notificationService = inject(NotificationService);
    private destroy$ = new Subject<void>();

    ngOnInit(): void {
        this.tiles = [
            {
                titleKey: "dashboard.tiles.workshop.title",
                descriptionKey: "dashboard.tiles.workshop.description",
                icon: "fa-pen-fancy",
                iconColor: "#7354af",
                enabled: true,
                action: () => this.startWorkshop()
            },
            {
                titleKey: "dashboard.tiles.composition.title",
                descriptionKey: "dashboard.tiles.composition.description",
                icon: "fa-sliders-h",
                iconColor: "#6c757d",
                enabled: false,
                action: () => {}
            },
            {
                titleKey: "dashboard.tiles.cover.title",
                descriptionKey: "dashboard.tiles.cover.description",
                icon: "fa-image",
                iconColor: "#28a745",
                enabled: true,
                action: () => this.router.navigate(["/imagegen"], {queryParams: {composition: "album-cover"}})
            },
            {
                titleKey: "dashboard.tiles.mixing.title",
                descriptionKey: "dashboard.tiles.mixing.description",
                icon: "fa-headphones",
                iconColor: "#6c757d",
                enabled: false,
                action: () => {}
            },
            {
                titleKey: "dashboard.tiles.mastering.title",
                descriptionKey: "dashboard.tiles.mastering.description",
                icon: "fa-compact-disc",
                iconColor: "#6c757d",
                enabled: false,
                action: () => {}
            },
            {
                titleKey: "dashboard.tiles.distribute.title",
                descriptionKey: "dashboard.tiles.distribute.description",
                icon: "fa-share-alt",
                iconColor: "#ff9800",
                enabled: true,
                action: () => this.router.navigate(["/song-releases/new"])
            },
            {
                titleKey: "dashboard.tiles.promote.title",
                descriptionKey: "dashboard.tiles.promote.description",
                icon: "fa-bullhorn",
                iconColor: "#6c757d",
                enabled: false,
                action: () => {}
            },
            {
                titleKey: "dashboard.tiles.project.title",
                descriptionKey: "dashboard.tiles.project.description",
                icon: "fa-folder-open",
                iconColor: "#007bff",
                enabled: true,
                action: () => this.router.navigate(["/song-projects"])
            }
        ];
    }

    ngOnDestroy(): void {
        this.destroy$.next();
        this.destroy$.complete();
    }

    onTileClick(tile: DashboardTile): void {
        if (!tile.enabled) return;
        tile.action();
    }

    private async startWorkshop(): Promise<void> {
        if (this.isCreatingWorkshop) return;
        this.isCreatingWorkshop = true;

        try {
            const response = await firstValueFrom(
                this.workshopService.createWorkshop({
                    title: this.translate.instant("workshop.newWorkshopTitle")
                }).pipe(takeUntil(this.destroy$))
            );
            if (response?.data?.id) {
                this.router.navigate(["/text-workshop", response.data.id]);
            }
        } catch (error) {
            console.error("Failed to create workshop:", error);
            this.notificationService.error(
                this.translate.instant("workshop.errors.createFailed")
            );
        } finally {
            this.isCreatingWorkshop = false;
        }
    }
}
