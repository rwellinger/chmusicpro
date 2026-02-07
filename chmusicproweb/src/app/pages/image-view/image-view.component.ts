import {
    AfterViewInit,
    Component,
    ElementRef,
    inject,
    OnDestroy,
    OnInit,
    ViewChild,
    ViewEncapsulation
} from "@angular/core";
import {CommonModule} from "@angular/common";
import {FormsModule} from "@angular/forms";
import {HttpClient} from "@angular/common/http";
import {Router} from "@angular/router";
import {TranslateModule, TranslateService} from "@ngx-translate/core";
import {ResourceBlobService} from "../../services/ui/resource-blob.service";
import {ImageService} from "../../services/business/image.service";
import {ApiConfigService} from "../../services/config/api-config.service";
import {NotificationService} from "../../services/ui/notification.service";
import {UserSettingsService} from "../../services/user-settings.service";
import {MatSnackBarModule} from "@angular/material/snack-bar";
import {MatDialog} from "@angular/material/dialog";
import {
    AssignToProjectDialogComponent
} from "../../dialogs/assign-to-project-dialog/assign-to-project-dialog.component";
import {MatCardModule} from "@angular/material/card";
import {MatButtonModule} from "@angular/material/button";
import {DisplayNamePipe} from "../../pipes/display-name.pipe";
import {ImageDetailPanelComponent} from "../../components/image-detail-panel/image-detail-panel.component";
import {debounceTime, distinctUntilChanged, firstValueFrom, Subject, takeUntil} from "rxjs";

interface ImageData {
    id: string;
    filename: string;
    model_used: string;
    prompt: string | null;
    user_prompt?: string | null;
    enhanced_prompt?: string | null;
    prompt_hash: string;
    size: string;
    url: string;
    title?: string;
    tags?: string;
    text_overlay_metadata?: any;
    composition?: string;
    created_at: string;
    updated_at?: string;
    projects_count?: number; // Number of projects this image is assigned to
}

interface PaginationInfo {
    has_more: boolean;
    limit: number;
    offset: number;
    total: number;
}

@Component({
    selector: "app-image-view",
    standalone: true,
    imports: [CommonModule, FormsModule, TranslateModule, MatSnackBarModule, MatCardModule, MatButtonModule, DisplayNamePipe, ImageDetailPanelComponent],
    templateUrl: "./image-view.component.html",
    styleUrl: "./image-view.component.scss",
    encapsulation: ViewEncapsulation.None
})
export class ImageViewComponent implements OnInit, AfterViewInit, OnDestroy {
    images: ImageData[] = [];
    selectedImage: ImageData | null = null;
    selectedImageBlobUrl: string = "";
    isLoading = false;
    loadingMessage = "";
    currentPage = 0;
    pagination: PaginationInfo = {
        has_more: false,
        limit: 10, // Will be overridden by user settings
        offset: 0,
        total: 0
    };

    // Search and sort (server-based)
    searchTerm: string = "";
    sortBy: string = "created_at";
    sortDirection: "asc" | "desc" = "desc";

    // RxJS subjects for debouncing
    private searchSubject = new Subject<string>();
    private destroy$ = new Subject<void>();

    // Navigation state
    private navigationState: any;

    // Modal state
    showImageModal = false;

    // Selection mode state
    isSelectionMode = false;
    selectedImageIds = new Set<string>();

    // Inline editing state
    editingTitle = false;
    editTitleValue = "";

    // Image placeholder and dimensions analysis
    @ViewChild("imagePlaceholder") imagePlaceholder!: ElementRef;
    placeholderDimensions = {
        width: 0,
        height: 0,
        aspectRatio: "0:0",
        viewportWidth: 0,
        viewportHeight: 0
    };

    @ViewChild("titleInput") titleInput!: ElementRef;
    @ViewChild("searchInput") searchInput!: ElementRef;

    private http = inject(HttpClient);
    private resourceBlobService = inject(ResourceBlobService);
    private imageService = inject(ImageService);
    private apiConfig = inject(ApiConfigService);
    private notificationService = inject(NotificationService);
    private settingsService = inject(UserSettingsService);
    private translate = inject(TranslateService);
    private router = inject(Router);
    private dialog = inject(MatDialog);

    // Make Math available in template
    Math = Math;

    constructor() {
        // Capture navigation state for filter preservation
        this.navigationState = this.router.getCurrentNavigation()?.extras?.state;

        // Setup search debouncing
        this.searchSubject.pipe(
            debounceTime(300),
            distinctUntilChanged(),
            takeUntil(this.destroy$)
        ).subscribe(searchTerm => {
            const hadFocus = document.activeElement === this.searchInput?.nativeElement;
            this.searchTerm = searchTerm;
            this.loadImages(0).then(() => {
                // Restore focus if it was in search field
                if (hadFocus && this.searchInput) {
                    setTimeout(() => this.searchInput.nativeElement.focus(), 0);
                }
            });
        });
    }

    ngOnInit() {
        // Restore filter state from navigation
        if (this.navigationState?.["searchTerm"] !== undefined) {
            this.searchTerm = this.navigationState["searchTerm"];
        }
        if (this.navigationState?.["sortBy"]) {
            this.sortBy = this.navigationState["sortBy"];
        }
        if (this.navigationState?.["sortDirection"]) {
            this.sortDirection = this.navigationState["sortDirection"];
        }
        if (this.navigationState?.["returnPage"] !== undefined) {
            this.currentPage = this.navigationState["returnPage"];
        }

        this.loadUserSettings();
    }

    ngOnDestroy() {
        this.destroy$.next();
        this.destroy$.complete();
    }

    private loadUserSettings() {
        this.settingsService.getSettings()
            .pipe(takeUntil(this.destroy$))
            .subscribe(settings => {
                this.pagination.limit = settings.imageListLimit;
                this.loadImages(this.currentPage);
            });
    }

    ngAfterViewInit() {
        // Initial dimension measurement
        this.measureDimensions();

        // Update dimensions on window resize
        window.addEventListener("resize", () => {
            setTimeout(() => this.measureDimensions(), 100);
        });
    }

    private measureDimensions() {
        if (this.imagePlaceholder) {
            const element = this.imagePlaceholder.nativeElement;
            const rect = element.getBoundingClientRect();

            this.placeholderDimensions = {
                width: Math.round(rect.width),
                height: Math.round(rect.height),
                aspectRatio: this.calculateAspectRatio(rect.width, rect.height),
                viewportWidth: window.innerWidth,
                viewportHeight: window.innerHeight
            };
        }
    }

    private calculateAspectRatio(width: number, height: number): string {
        if (height === 0) return "0:0";
        const gcd = this.gcd(Math.round(width), Math.round(height));
        return `${Math.round(width / gcd)}:${Math.round(height / gcd)}`;
    }

    private gcd(a: number, b: number): number {
        return b === 0 ? a : this.gcd(b, a % b);
    }

    async loadImages(page: number = 0) {
        this.isLoading = true;
        this.loadingMessage = this.translate.instant("imageView.messages.loadingImages");

        try {
            const offset = page * this.pagination.limit;

            // Build URL with search and sort parameters
            const params = new URLSearchParams({
                limit: this.pagination.limit.toString(),
                offset: offset.toString(),
                sort_by: this.sortBy,
                sort_direction: this.sortDirection
            });

            if (this.searchTerm.trim()) {
                params.append("search", this.searchTerm.trim());
            }

            const url = `${this.apiConfig.endpoints.image.list(this.pagination.limit, offset).split("?")[0]}?${params.toString()}`;

            const data = await firstValueFrom(
                this.http.get<any>(url)
            );

            if (data.images && Array.isArray(data.images)) {
                this.images = data.images;
                this.pagination = data.pagination;
                this.currentPage = page;

                // Auto-select first image if available and none selected
                if (this.images.length > 0 && !this.selectedImage) {
                    this.selectImage(this.images[0]);
                }
            } else {
                this.images = [];
            }
        } catch (error: any) {
            this.notificationService.error(this.translate.instant("imageView.errors.loadingImages", {error: error.message}));
            this.images = [];
        } finally {
            this.isLoading = false;
        }
    }


    selectImage(image: ImageData) {
        this.selectedImage = image;

        // Load blob URL for modal display
        if (image?.url) {
            this.resourceBlobService.getResourceBlobUrl(image.url).subscribe({
                next: (blobUrl) => {
                    this.selectedImageBlobUrl = blobUrl;
                },
                error: (error) => {
                    console.error("Failed to load image blob for modal:", error);
                    this.selectedImageBlobUrl = "";
                }
            });
        } else {
            this.selectedImageBlobUrl = "";
        }

        // Measure dimensions when image changes
        setTimeout(() => this.measureDimensions(), 100);
    }


    nextPage() {
        if (this.pagination.has_more) {
            this.loadImages(this.currentPage + 1);
        }
    }

    previousPage() {
        if (this.currentPage > 0) {
            this.loadImages(this.currentPage - 1);
        }
    }

    formatDate(dateString: string): string {
        try {
            return new Date(dateString).toLocaleDateString("de-DE", {
                day: "2-digit",
                month: "2-digit",
                year: "numeric",
                hour: "2-digit",
                minute: "2-digit"
            });
        } catch {
            return dateString;
        }
    }

    getImageOrientation(size: string): string {
        // Map image size to orientation type
        switch (size) {
            case "1024x1024":
                return "square";
            case "1792x1024":
                return "landscape";
            case "1024x1792":
                return "portrait";
            default:
                // Fallback for unknown sizes
                return "square";
        }
    }

    downloadImage(imageUrl: string) {
        // Use authenticated download via ResourceBlobService
        const filename = this.getImageFilename();
        this.resourceBlobService.downloadResource(imageUrl, filename);
    }

    private getImageFilename(): string {
        const title = this.selectedImage?.title || (this.selectedImage ? this.getDisplayTitle(this.selectedImage) : "") || "image";
        const sanitized = title.replace(/[^a-zA-Z0-9]/g, "_").substring(0, 50);
        return `${sanitized}.png`;
    }

    onImageError(event: Event): void {
        const target = event.target as HTMLImageElement;
        if (target) {
            target.style.display = "none";
        }
    }

    formatDateShort(dateString: string): string {
        try {
            return new Date(dateString).toLocaleDateString("de-CH", {
                day: "2-digit",
                month: "2-digit",
                year: "numeric"
            });
        } catch {
            return dateString;
        }
    }

    // Modern pagination methods
    getVisiblePages(): (number | string)[] {
        const totalPages = Math.ceil(this.pagination.total / this.pagination.limit);
        const current = this.currentPage + 1;
        const pages: (number | string)[] = [];

        if (totalPages <= 7) {
            // Show all pages if 7 or less
            for (let i = 1; i <= totalPages; i++) {
                pages.push(i);
            }
        } else {
            // Smart pagination with ellipsis
            if (current <= 4) {
                // Show: 1 2 3 4 5 ... last
                for (let i = 1; i <= 5; i++) pages.push(i);
                pages.push("...");
                pages.push(totalPages);
            } else if (current >= totalPages - 3) {
                // Show: 1 ... n-4 n-3 n-2 n-1 n
                pages.push(1);
                pages.push("...");
                for (let i = totalPages - 4; i <= totalPages; i++) pages.push(i);
            } else {
                // Show: 1 ... current-1 current current+1 ... last
                pages.push(1);
                pages.push("...");
                for (let i = current - 1; i <= current + 1; i++) pages.push(i);
                pages.push("...");
                pages.push(totalPages);
            }
        }

        return pages;
    }

    goToPage(pageIndex: number) {
        if (pageIndex >= 0 && pageIndex < Math.ceil(this.pagination.total / this.pagination.limit) && !this.isLoading) {
            this.loadImages(pageIndex);
        }
    }

    trackByPage(index: number, page: number | string): number | string {
        return page;
    }

    trackByImage(index: number, image: ImageData): string {
        return image.id;
    }

    onSearchChange(searchTerm: string) {
        this.searchSubject.next(searchTerm);
    }

    clearSearch() {
        this.searchTerm = "";
        this.searchSubject.next("");
    }

    toggleSort() {
        this.sortDirection = this.sortDirection === "desc" ? "asc" : "desc";
        this.loadImages(0); // Reset to first page and reload with new sort
    }

    openImageModal() {
        this.showImageModal = true;
    }

    closeImageModal() {
        this.showImageModal = false;
    }

    // Selection mode methods
    toggleSelectionMode() {
        this.isSelectionMode = !this.isSelectionMode;
        if (!this.isSelectionMode) {
            this.selectedImageIds.clear();
        }
    }

    // Check if an image can be deleted (not assigned to any project)
    canDeleteImage(image: ImageData): boolean {
        return !image.projects_count || image.projects_count === 0;
    }

    toggleImageSelection(imageId: string) {
        if (this.selectedImageIds.has(imageId)) {
            this.selectedImageIds.delete(imageId);
        } else {
            this.selectedImageIds.add(imageId);
        }
    }

    selectAllImages() {
        this.images.forEach(image => {
            if (this.canDeleteImage(image)) {
                this.selectedImageIds.add(image.id);
            }
        });
    }

    deselectAllImages() {
        this.selectedImageIds.clear();
    }

    onSelectAllChange(event: Event) {
        const checkbox = event.target as HTMLInputElement;
        if (checkbox.checked) {
            this.selectAllImages();
        } else {
            this.deselectAllImages();
        }
    }

    async bulkDeleteImages() {
        if (this.selectedImageIds.size === 0) {
            this.notificationService.error(this.translate.instant("imageView.errors.noImagesSelected"));
            return;
        }

        // Check for protected images that cannot be deleted (assigned to projects)
        const protectedImages = this.images.filter(image =>
            this.selectedImageIds.has(image.id) && !this.canDeleteImage(image)
        );

        if (protectedImages.length > 0) {
            const totalProjects = protectedImages.reduce((sum, img) => sum + (img.projects_count || 0), 0);
            this.notificationService.error(
                this.translate.instant("imageView.errors.cannotDeleteAssignedBulk", {
                    imageCount: protectedImages.length,
                    projectCount: totalProjects
                })
            );
            return;
        }

        const confirmation = confirm(this.translate.instant("imageView.confirmations.bulkDelete", {count: this.selectedImageIds.size}));
        if (!confirmation) {
            return;
        }

        this.isLoading = true;
        try {
            const result = await firstValueFrom(
                this.http.delete<any>(this.apiConfig.endpoints.image.bulkDelete, {
                    body: {
                        ids: Array.from(this.selectedImageIds)
                    }
                })
            );

            // Show detailed result notification
            if (result.summary) {
                const {deleted, not_found, errors} = result.summary;
                let message = this.translate.instant("imageView.bulkDelete.completed", {deleted});
                if (not_found > 0) message += `, ${this.translate.instant("imageView.bulkDelete.notFound", {count: not_found})}`;
                if (errors > 0) message += `, ${this.translate.instant("imageView.bulkDelete.errors", {count: errors})}`;

                if (deleted <= 0) {
                    this.notificationService.error(message);
                }
            }

            // Clear selections and reload
            this.selectedImageIds.clear();
            this.isSelectionMode = false;

            // Clear selected image if it was deleted
            if (this.selectedImage && this.selectedImageIds.has(this.selectedImage.id)) {
                this.selectedImage = null;
            }

            // Reload current page
            await this.loadImages(this.currentPage);

        } catch (error: any) {
            this.notificationService.error(this.translate.instant("imageView.errors.deletingImages", {error: error.message}));
        } finally {
            this.isLoading = false;
        }
    }

    // Title editing methods
    hasTextOverlay(image: ImageData): boolean {
        return image.text_overlay_metadata !== null && image.text_overlay_metadata !== undefined;
    }

    getDisplayTitle(image: ImageData): string {
        if (image.title && image.title.trim()) {
            return image.title.trim();
        }
        // Generate title from user_prompt (original user input)
        const displayPrompt = image.user_prompt || image.prompt || "Untitled";
        return displayPrompt.length > 50 ? displayPrompt.substring(0, 47) + "..." : displayPrompt;
    }

    startEditTitle() {
        if (!this.selectedImage) return;

        this.editingTitle = true;
        // Use current title if exists, otherwise use generated title as template
        this.editTitleValue = this.selectedImage.title || this.getDisplayTitle(this.selectedImage);

        // Focus input after view updates
        setTimeout(() => {
            if (this.titleInput) {
                this.titleInput.nativeElement.focus();
                this.titleInput.nativeElement.select();
            }
        }, 100);
    }

    cancelEditTitle() {
        this.editingTitle = false;
        this.editTitleValue = "";
    }

    async saveTitle() {
        if (!this.selectedImage) return;

        this.isLoading = true;
        try {
            const updatedImage = await firstValueFrom(
                this.http.put<any>(this.apiConfig.endpoints.image.update(this.selectedImage.id), {
                    title: this.editTitleValue.trim()
                })
            );

            // Update selected image with new data (ensure all fields are preserved)
            this.selectedImage = {
                ...this.selectedImage,
                title: updatedImage.title,
                tags: updatedImage.tags,
                updated_at: updatedImage.updated_at
            };

            // Update in images list too
            const imageIndex = this.images.findIndex(img => img.id === this.selectedImage!.id);
            if (imageIndex !== -1) {
                this.images[imageIndex] = {
                    ...this.images[imageIndex],
                    title: updatedImage.title,
                    tags: updatedImage.tags
                };
                // Stay on current page after update
                this.loadImages(this.currentPage);
            }

            this.editingTitle = false;
            this.editTitleValue = "";

        } catch (error: any) {
            this.notificationService.error(this.translate.instant("imageView.errors.updatingTitle", {error: error.message}));
        } finally {
            this.isLoading = false;
        }
    }

    // Handlers for shared image detail panel
    onTitleChanged() {
        // Refresh the list to reflect changes
        this.loadImages(this.currentPage);
    }

    onDownloadImage() {
        if (this.selectedImage?.url) {
            this.downloadImage(this.selectedImage.url);
        }
    }

    onPreviewImage() {
        this.openImageModal();
    }

    navigateToImageGenerator() {
        this.router.navigate(["/imagegen"], {
            state: {
                searchTerm: this.searchTerm,
                sortBy: this.sortBy,
                sortDirection: this.sortDirection,
                returnPage: this.currentPage
            }
        });
    }

    /**
     * Open dialog to assign image to a project
     */
    openAssignToProjectDialog() {
        if (!this.selectedImage) {
            return;
        }

        const dialogRef = this.dialog.open(AssignToProjectDialogComponent, {
            width: "600px",
            maxHeight: "90vh",
            data: {
                assetType: "image",
                assetId: this.selectedImage.id
            }
        });

        dialogRef.afterClosed().subscribe(async (result) => {
            if (result?.success) {
                this.notificationService.success(
                    this.translate.instant("assignToProject.success")
                );
                // Reload images to reflect updated project assignment
                const currentPage = Math.floor(this.pagination.offset / this.pagination.limit);
                await this.loadImages(currentPage);
            }
        });
    }

    /**
     * Navigate to project(s) containing this image
     * If multiple projects: show selection dialog
     * If single project: navigate directly
     */
    async navigateToFirstProject(image: any, event: Event): Promise<void> {
        event.stopPropagation();

        try {
            // Fetch projects for this image
            const projects = await this.imageService.getProjectsForImage(image.id);

            if (projects.length === 0) {
                this.notificationService.info(this.translate.instant("imageView.messages.noProjects"));
                return;
            }

            if (projects.length === 1) {
                // Single project: navigate directly
                this.router.navigate(["/song-projects"], {
                    state: {selectedProjectId: projects[0].project_id}
                });
            } else {
                // Multiple projects: show selection dialog
                const {SelectProjectDialogComponent} = await import("../../dialogs/select-project-dialog/select-project-dialog.component");
                const dialogRef = this.dialog.open(SelectProjectDialogComponent, {
                    width: "400px",
                    data: {
                        imageId: image.id,
                        projects: projects
                    }
                });

                dialogRef.afterClosed().subscribe(result => {
                    if (result?.selectedProjectId) {
                        this.router.navigate(["/song-projects"], {
                            state: {selectedProjectId: result.selectedProjectId}
                        });
                    }
                });
            }
        } catch (error) {
            console.error("Failed to fetch projects for image:", error);
            this.notificationService.error(this.translate.instant("imageView.messages.projectLoadError"));
        }
    }

    /**
     * Unassign image from a specific project (link only, image remains)
     * Shows project selection dialog if assigned to multiple projects
     */
    async unassignFromProject(): Promise<void> {
        if (!this.selectedImage || !this.selectedImage.projects_count) {
            return;
        }

        try {
            // Fetch projects for this image
            const projects = await this.imageService.getProjectsForImage(this.selectedImage.id);

            if (projects.length === 0) {
                return;
            }

            let targetProjectId: string;
            let targetProjectName: string;

            if (projects.length === 1) {
                // Single project: use directly
                targetProjectId = projects[0].project_id;
                targetProjectName = projects[0].project_name;
            } else {
                // Multiple projects: show selection dialog
                const {SelectProjectDialogComponent} = await import("../../dialogs/select-project-dialog/select-project-dialog.component");
                const dialogRef = this.dialog.open(SelectProjectDialogComponent, {
                    width: "400px",
                    data: {
                        imageId: this.selectedImage.id,
                        projects: projects,
                        title: this.translate.instant("imageView.dialogs.selectProjectToUnassign")
                    }
                });

                const result = await firstValueFrom(dialogRef.afterClosed());
                if (!result?.selectedProjectId) {
                    return;
                }
                targetProjectId = result.selectedProjectId;
                targetProjectName = projects.find(p => p.project_id === targetProjectId)?.project_name || "";
            }

            // Confirm unassignment
            const confirmation = confirm(
                this.translate.instant("imageView.confirmations.unassignFromProject", {
                    image: this.getDisplayTitle(this.selectedImage),
                    project: targetProjectName
                })
            );

            if (!confirmation) {
                return;
            }

            this.isLoading = true;
            await this.imageService.unassignFromProject(this.selectedImage.id, targetProjectId);

            this.notificationService.success(
                this.translate.instant("imageView.messages.unassignedFromProject")
            );

            // Reload images to reflect updated project assignment
            await this.loadImages(this.currentPage);

        } catch (error: any) {
            this.notificationService.error(
                this.translate.instant("imageView.errors.unassigningFromProject", {error: error.message})
            );
        } finally {
            this.isLoading = false;
        }
    }
}
