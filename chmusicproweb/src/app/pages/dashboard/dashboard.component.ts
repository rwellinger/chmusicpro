import {Component, inject, OnDestroy, OnInit} from "@angular/core";
import {CommonModule} from "@angular/common";
import {Router, RouterModule} from "@angular/router";
import {TranslateModule, TranslateService} from "@ngx-translate/core";
import {catchError, firstValueFrom, forkJoin, of, Subject, takeUntil} from "rxjs";
import {MatTooltipModule} from "@angular/material/tooltip";
import {HttpClient} from "@angular/common/http";
import {WorkshopService} from "../../services/business/workshop.service";
import {SongProjectService} from "../../services/business/song-project.service";
import {SongReleaseService} from "../../services/business/song-release.service";
import {ApiConfigService} from "../../services/config/api-config.service";
import {NotificationService} from "../../services/ui/notification.service";
import {Workshop, WorkshopListResponse} from "../../models/workshop.model";
import {SongProjectListItem, SongProjectListResponse} from "../../models/song-project.model";
import {SongReleaseListItem, SongReleaseListResponse} from "../../models/song-release.model";

interface DashboardTile {
    titleKey: string;
    descriptionKey: string;
    icon: string;
    iconColor: string;
    enabled: boolean;
    action: () => void;
}

interface RecentItem {
    id: string;
    title: string;
    subtitle: string;
    icon: string;
    iconColor: string;
    updatedAt: string;
    route: string[];
}

interface RecentCategory {
    titleKey: string;
    icon: string;
    items: RecentItem[];
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
    recentCategories: RecentCategory[] = [];
    isCreatingWorkshop = false;
    isLoadingRecent = true;

    private router = inject(Router);
    private http = inject(HttpClient);
    private translate = inject(TranslateService);
    private workshopService = inject(WorkshopService);
    private songProjectService = inject(SongProjectService);
    private songReleaseService = inject(SongReleaseService);
    private apiConfig = inject(ApiConfigService);
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

        this.loadRecentWork();
    }

    ngOnDestroy(): void {
        this.destroy$.next();
        this.destroy$.complete();
    }

    onTileClick(tile: DashboardTile): void {
        if (!tile.enabled) return;
        tile.action();
    }

    onRecentItemClick(item: RecentItem): void {
        this.router.navigate(item.route);
    }

    formatRelativeDate(isoDate: string): string {
        const date = new Date(isoDate);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

        if (diffDays === 0) {
            return this.translate.instant("dashboard.recentWork.today");
        } else if (diffDays === 1) {
            return this.translate.instant("dashboard.recentWork.yesterday");
        } else if (diffDays < 30) {
            return this.translate.instant("dashboard.recentWork.daysAgo", {days: diffDays});
        }
        return date.toLocaleDateString();
    }

    private loadRecentWork(): void {
        this.isLoadingRecent = true;

        forkJoin({
            workshops: this.workshopService.getWorkshops(4, 0).pipe(
                catchError(() => of({data: [], pagination: {total: 0, limit: 4, offset: 0, has_more: false}} as WorkshopListResponse))
            ),
            images: this.http.get<{images: {id: string; title: string | null; user_prompt: string | null; composition: string | null; created_at: string}[]; pagination: any}>(
                this.apiConfig.endpoints.image.list(4, 0)
            ).pipe(
                catchError(() => of({images: [], pagination: {total: 0}}))
            ),
            projects: this.songProjectService.getProjects(4, 0).pipe(
                catchError(() => of({data: [], pagination: {total: 0, limit: 4, offset: 0, has_more: false}} as SongProjectListResponse))
            ),
            releases: this.songReleaseService.getReleases(4, 0).pipe(
                catchError(() => of({items: [], total: 0, limit: 4, offset: 0} as SongReleaseListResponse))
            )
        }).pipe(takeUntil(this.destroy$)).subscribe(results => {
            this.recentCategories = this.buildRecentCategories(results);
            this.isLoadingRecent = false;
        });
    }

    private buildRecentCategories(results: {
        workshops: WorkshopListResponse;
        images: {images: {id: string; title: string | null; user_prompt: string | null; composition: string | null; created_at: string}[]};
        projects: SongProjectListResponse;
        releases: SongReleaseListResponse;
    }): RecentCategory[] {
        const categories: RecentCategory[] = [];

        if (results.workshops.data.length > 0) {
            categories.push({
                titleKey: "dashboard.recentWork.categories.workshops",
                icon: "fa-pen-fancy",
                items: results.workshops.data.map((w: Workshop) => ({
                    id: w.id,
                    title: w.title,
                    subtitle: w.current_phase,
                    icon: "fa-pen-fancy",
                    iconColor: "#7354af",
                    updatedAt: w.updated_at || w.created_at,
                    route: ["/text-workshop", w.id]
                }))
            });
        }

        if (results.images.images.length > 0) {
            categories.push({
                titleKey: "dashboard.recentWork.categories.coverArts",
                icon: "fa-image",
                items: results.images.images.map(img => ({
                    id: img.id,
                    title: img.title || img.user_prompt || "Untitled",
                    subtitle: img.composition || "image",
                    icon: "fa-image",
                    iconColor: "#28a745",
                    updatedAt: img.created_at,
                    route: ["/imageview"]
                }))
            });
        }

        if (results.projects.data.length > 0) {
            categories.push({
                titleKey: "dashboard.recentWork.categories.projects",
                icon: "fa-folder-open",
                items: results.projects.data.map((p: SongProjectListItem) => ({
                    id: p.id,
                    title: p.project_name,
                    subtitle: p.project_status,
                    icon: "fa-folder-open",
                    iconColor: "#007bff",
                    updatedAt: p.updated_at || p.created_at,
                    route: ["/song-projects"]
                }))
            });
        }

        if (results.releases.items.length > 0) {
            categories.push({
                titleKey: "dashboard.recentWork.categories.distribution",
                icon: "fa-share-alt",
                items: results.releases.items.map((r: SongReleaseListItem) => ({
                    id: r.id,
                    title: r.name,
                    subtitle: `${r.type} - ${r.status}`,
                    icon: "fa-share-alt",
                    iconColor: "#ff9800",
                    updatedAt: r.release_date || "",
                    route: ["/song-releases/edit", r.id]
                }))
            });
        }

        return categories;
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
