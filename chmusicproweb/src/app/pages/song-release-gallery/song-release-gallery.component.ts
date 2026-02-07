import {Component, inject, OnDestroy, OnInit} from "@angular/core";
import {CommonModule} from "@angular/common";
import {FormsModule} from "@angular/forms";
import {Router} from "@angular/router";
import {debounceTime, distinctUntilChanged, Subject, takeUntil} from "rxjs";
import {TranslateModule, TranslateService} from "@ngx-translate/core";
import {MatCardModule} from "@angular/material/card";

import {SongReleaseService} from "../../services/business/song-release.service";
import {NotificationService} from "../../services/ui/notification.service";
import {ResourceBlobService} from "../../services/ui/resource-blob.service";
import {
    AssignedProject,
    ReleaseStatus,
    ReleaseType,
    SongRelease,
    SongReleaseListItem
} from "../../models/song-release.model";

@Component({
    selector: "app-song-release-gallery",
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        TranslateModule,
        MatCardModule
    ],
    templateUrl: "./song-release-gallery.component.html",
    styleUrl: "./song-release-gallery.component.scss"
})
export class SongReleaseGalleryComponent implements OnInit, OnDestroy {
    // Release list and pagination
    releaseList: SongReleaseListItem[] = [];
    selectedRelease: SongRelease | null = null;
    selectedReleaseCoverBlobUrl: string = "";
    listItemCoverBlobUrls = new Map<string, string>(); // Map: release.id -> blob URL
    currentPage = 0;
    pagination = {
        total: 0,
        limit: 8,
        offset: 0
    };

    // Search and filter
    searchTerm = "";
    selectedStatusFilter: string = "all";

    // UI state
    isLoading = false;
    isLoadingDetail = false;

    // Enums for template
    ReleaseType = ReleaseType;
    ReleaseStatus = ReleaseStatus;

    // Math for template
    Math = Math;

    // RxJS subjects
    private searchSubject = new Subject<string>();
    private destroy$ = new Subject<void>();

    // Navigation state
    private navigationState: any;

    private releaseService = inject(SongReleaseService);
    private notificationService = inject(NotificationService);
    private resourceBlobService = inject(ResourceBlobService);
    private translate = inject(TranslateService);
    private router = inject(Router);

    constructor() {
        // Capture navigation state for filter preservation
        this.navigationState = this.router.getCurrentNavigation()?.extras?.state;

        // Setup search debouncing
        this.searchSubject.pipe(
            debounceTime(300),
            distinctUntilChanged(),
            takeUntil(this.destroy$)
        ).subscribe(searchTerm => {
            this.searchTerm = searchTerm;
            this.loadReleases(0).then(() => {
                // Auto-select first release after search
                if (this.releaseList.length > 0) {
                    this.selectRelease(this.releaseList[0]);
                } else {
                    this.selectedRelease = null;
                }
            });
        });
    }

    ngOnInit(): void {
        // Restore filter state from navigation
        if (this.navigationState?.['searchTerm']) {
            this.searchTerm = this.navigationState['searchTerm'];
        }
        if (this.navigationState?.['selectedStatusFilter']) {
            this.selectedStatusFilter = this.navigationState['selectedStatusFilter'];
        }

        // Restore pagination
        const returnPage = this.navigationState?.['returnPage'] !== undefined
            ? this.navigationState['returnPage']
            : 0;

        this.loadReleases(returnPage).then(() => {
            // Auto-select first release if list is not empty
            if (this.releaseList.length > 0 && !this.selectedRelease) {
                this.selectRelease(this.releaseList[0]);
            }
        });
    }

    ngOnDestroy(): void {
        this.destroy$.next();
        this.destroy$.complete();
    }

    /**
     * Load releases with pagination and filters
     */
    async loadReleases(page: number): Promise<void> {
        this.isLoading = true;
        this.currentPage = page;
        this.pagination.offset = page * this.pagination.limit;

        // Clear previous list item cover blob URLs
        this.listItemCoverBlobUrls.clear();

        try {
            const response = await this.releaseService.getReleases(
                this.pagination.limit,
                this.pagination.offset,
                this.selectedStatusFilter || undefined,  // Send 'all' as string, not undefined
                this.searchTerm || undefined
            ).toPromise();

            if (response) {
                this.releaseList = response.items || [];
                this.pagination.total = response.total || 0;

                // Load cover blob URLs for all list items
                this.releaseList.forEach(release => {
                    if (release.cover_url) {
                        this.resourceBlobService.getResourceBlobUrl(release.cover_url)
                            .pipe(takeUntil(this.destroy$))
                            .subscribe({
                                next: (blobUrl) => {
                                    if (blobUrl) {
                                        this.listItemCoverBlobUrls.set(release.id, blobUrl);
                                    }
                                },
                                error: () => {
                                    // Silently fail - placeholder will be shown
                                }
                            });
                    }
                });
            } else {
                this.releaseList = [];
                this.pagination.total = 0;
            }
        } catch (error) {
            console.error("Failed to load releases:", error);
            this.releaseList = [];
            this.pagination.total = 0;
            this.notificationService.error(this.translate.instant("songRelease.messages.loadError"));
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * Select release and load full details
     */
    async selectRelease(release: SongReleaseListItem): Promise<void> {
        this.isLoadingDetail = true;
        this.selectedReleaseCoverBlobUrl = ""; // Reset blob URL

        try {
            const response = await this.releaseService.getReleaseById(release.id).toPromise();
            if (response?.data) {
                this.selectedRelease = response.data;

                // Load cover blob URL for authenticated image access
                if (this.selectedRelease.cover_url) {
                    this.resourceBlobService.getResourceBlobUrl(this.selectedRelease.cover_url)
                        .pipe(takeUntil(this.destroy$))
                        .subscribe({
                            next: (blobUrl) => {
                                this.selectedReleaseCoverBlobUrl = blobUrl;
                            },
                            error: () => {
                                this.selectedReleaseCoverBlobUrl = "";
                            }
                        });
                }
            }
        } catch (error) {
            console.error("Failed to load release details:", error);
            this.notificationService.error(this.translate.instant("songRelease.messages.loadError"));
        } finally {
            this.isLoadingDetail = false;
        }
    }

    /**
     * Handle search input change
     */
    onSearchChange(value: string): void {
        this.searchSubject.next(value);
    }

    /**
     * Handle status filter change
     */
    selectStatusFilter(filter: string): void {
        this.selectedStatusFilter = filter;
        this.loadReleases(0).then(() => {
            // Auto-select first release after filter change
            if (this.releaseList.length > 0) {
                this.selectRelease(this.releaseList[0]);
            } else {
                this.selectedRelease = null;
            }
        });
    }

    /**
     * Navigate to specific page
     */
    changePage(page: number): void {
        if (page >= 0 && page < this.totalPages) {
            this.loadReleases(page).then(() => {
                // Auto-select first release on new page
                if (this.releaseList.length > 0) {
                    this.selectRelease(this.releaseList[0]);
                } else {
                    this.selectedRelease = null;
                }
            });
        }
    }

    /**
     * Get total number of pages
     */
    get totalPages(): number {
        return Math.ceil(this.pagination.total / this.pagination.limit);
    }

    /**
     * Format date for display
     */
    formatDate(dateString?: string): string {
        if (!dateString) return "-";
        const date = new Date(dateString);
        return date.toLocaleDateString();
    }

    /**
     * Get status badge CSS class
     */
    getStatusClass(status: ReleaseStatus): string {
        const classMap: Record<ReleaseStatus, string> = {
            [ReleaseStatus.DRAFT]: "badge-draft",
            [ReleaseStatus.ARRANGING]: "badge-arranging",
            [ReleaseStatus.MIXING]: "badge-mixing",
            [ReleaseStatus.MASTERING]: "badge-mastering",
            [ReleaseStatus.PRE_RELEASE]: "badge-pre-release",
            [ReleaseStatus.REJECTED]: "badge-rejected",
            [ReleaseStatus.UPLOADED]: "badge-uploaded",
            [ReleaseStatus.RELEASED]: "badge-released",
            [ReleaseStatus.DOWNTAKEN]: "badge-downtaken",
            [ReleaseStatus.ARCHIVED]: "badge-archived"
        };
        return classMap[status] || "badge-draft";
    }

    /**
     * Copy text to clipboard
     */
    async copyToClipboard(text: string, messageKey: string): Promise<void> {
        try {
            await navigator.clipboard.writeText(text);
            this.notificationService.success(this.translate.instant(messageKey));
        } catch (error) {
            this.notificationService.error(this.translate.instant("songRelease.messages.copyError"));
        }
    }

    /**
     * Create new release (navigate to editor)
     */
    createNewRelease(): void {
        this.router.navigate(["/song-releases/new"], {
            state: {
                searchTerm: this.searchTerm,
                selectedStatusFilter: this.selectedStatusFilter,
                returnPage: this.currentPage
            }
        });
    }

    /**
     * Edit selected release
     */
    editRelease(): void {
        if (!this.selectedRelease) return;
        this.router.navigate(["/song-releases/edit", this.selectedRelease.id], {
            state: {
                searchTerm: this.searchTerm,
                selectedStatusFilter: this.selectedStatusFilter,
                returnPage: this.currentPage
            }
        });
    }

    /**
     * Delete release
     */
    async deleteRelease(): Promise<void> {
        if (!this.selectedRelease) return;

        const confirmed = confirm(this.translate.instant("songRelease.messages.deleteConfirm"));
        if (!confirmed) return;

        try {
            await this.releaseService.deleteRelease(this.selectedRelease.id).toPromise();
            this.notificationService.success(this.translate.instant("songRelease.messages.deleteSuccess"));
            this.selectedRelease = null;
            this.loadReleases(this.currentPage);
        } catch (error) {
            console.error("Failed to delete release:", error);
            this.notificationService.error(this.translate.instant("songRelease.messages.deleteError"));
        }
    }

    /**
     * Get initials from release name (e.g., "My Album" -> "MA")
     */
    getInitials(name: string): string {
        if (!name) return "?";

        const words = name.trim().split(/\s+/);

        if (words.length === 1) {
            // Single word: take first 2 characters
            return words[0].substring(0, 2).toUpperCase();
        }

        // Multiple words: take first letter of first 2 words
        return (words[0][0] + words[1][0]).toUpperCase();
    }

    /**
     * Generate consistent color from string (for cover placeholder)
     */
    getColorFromString(text: string): string {
        if (!text) return "#5a6268"; // Default gray

        // Simple hash function
        let hash = 0;
        for (let i = 0; i < text.length; i++) {
            hash = text.charCodeAt(i) + ((hash << 5) - hash);
        }

        // Generate color (pastel-like colors for better readability)
        const hue = Math.abs(hash % 360);
        const saturation = 60; // Medium saturation for pleasant colors
        const lightness = 55; // Medium lightness for good contrast

        return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
    }

    /**
     * Navigate to Song Project with project ID in state.
     * Passes targetStatus to switch to archived tab if project is archived.
     */
    openProject(project: AssignedProject): void {
        this.router.navigate(["/song-projects"], {
            state: {
                selectedProjectId: project.id,
                targetStatus: project.project_status === "archived" ? "archived" : "all"
            }
        });
    }

    /**
     * Get cover blob URL for list item
     */
    getListItemCoverUrl(releaseId: string): string {
        return this.listItemCoverBlobUrls.get(releaseId) || "";
    }
}
