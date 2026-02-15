import {Component, inject, OnDestroy, OnInit} from "@angular/core";

import {Router, RouterModule} from "@angular/router";
import {TranslateModule, TranslateService} from "@ngx-translate/core";
import {catchError, forkJoin, of, Subject, takeUntil} from "rxjs";
import {MatTooltipModule} from "@angular/material/tooltip";
import {HttpClient} from "@angular/common/http";
import {WorkshopService} from "../../services/business/workshop.service";
import {SongProjectService} from "../../services/business/song-project.service";
import {SongReleaseService} from "../../services/business/song-release.service";
import {ApiConfigService} from "../../services/config/api-config.service";
import {PIPELINE_STEPS} from "../../services/config/pipeline.config";
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
    isLoadingRecent = true;

    private router = inject(Router);
    private http = inject(HttpClient);
    private translate = inject(TranslateService);
    private workshopService = inject(WorkshopService);
    private songProjectService = inject(SongProjectService);
    private songReleaseService = inject(SongReleaseService);
    private apiConfig = inject(ApiConfigService);
    private destroy$ = new Subject<void>();

    ngOnInit(): void {
        this.tiles = PIPELINE_STEPS.map(step => ({
            titleKey: step.titleKey,
            descriptionKey: step.descriptionKey,
            icon: step.icon,
            iconColor: step.iconColor,
            enabled: step.enabled,
            action: step.primaryRoute ? () => this.router.navigate([step.primaryRoute]) : () => {}
        }));

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
                    iconColor: "#AD1457",
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
                    iconColor: "#D32F2F",
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

}
