import {Component, inject, OnDestroy, OnInit} from "@angular/core";
import {CommonModule} from "@angular/common";
import {FormsModule} from "@angular/forms";
import {Router} from "@angular/router";
import {debounceTime, distinctUntilChanged, firstValueFrom, Subject, takeUntil} from "rxjs";
import {TranslateModule, TranslateService} from "@ngx-translate/core";
import {MatCardModule} from "@angular/material/card";
import {MatButtonModule} from "@angular/material/button";
import {MatIconModule} from "@angular/material/icon";
import {MatChipsModule} from "@angular/material/chips";
import {MatProgressSpinnerModule} from "@angular/material/progress-spinner";
import {MatExpansionModule} from "@angular/material/expansion";
import {MatDialog, MatDialogModule} from "@angular/material/dialog";
import {MatTooltipModule} from "@angular/material/tooltip";
import {MatMenuModule} from "@angular/material/menu";
import {MatTabsModule} from "@angular/material/tabs";

import {SongProjectService} from "../../services/business/song-project.service";
import {NotificationService} from "../../services/ui/notification.service";
import {UserSettingsService} from "../../services/user-settings.service";
import {ApiConfigService} from "../../services/config/api-config.service";
import {ResourceBlobService} from "../../services/ui/resource-blob.service";
import {CreateProjectDialogComponent} from "../../dialogs/create-project-dialog/create-project-dialog.component";
import {AssignedSketch, AssignedSong, SongProjectDetail, SongProjectListItem} from "../../models/song-project.model";
import {getColorFromString, getInitials} from "../../services/utils/cover-utils";

@Component({
    selector: "app-song-projects",
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        TranslateModule,
        MatCardModule,
        MatButtonModule,
        MatIconModule,
        MatChipsModule,
        MatProgressSpinnerModule,
        MatExpansionModule,
        MatDialogModule,
        MatTooltipModule,
        MatMenuModule,
        MatTabsModule
    ],
    templateUrl: "./song-projects.component.html",
    styleUrl: "./song-projects.component.scss"
})
export class SongProjectsComponent implements OnInit, OnDestroy {
    // Project list and pagination
    projectList: SongProjectListItem[] = [];
    selectedProject: SongProjectDetail | null = null;
    selectedProjectCoverBlobUrl: string = "";
    listItemCoverBlobUrls = new Map<string, string>(); // Map: project.id -> blob URL
    totalProjects = 0;
    pagination = {
        total: 0,
        limit: 20,
        offset: 0,
        has_more: false
    };

    // Search and filter
    searchTerm = "";
    currentStatus: "all" | "new" | "progress" | "archived" = "all";

    // UI state
    isLoading = false;
    isLoadingDetail = false;
    selectedTabIndex = 0;

    // Math for template
    Math = Math;

    // RxJS subjects
    private searchSubject = new Subject<string>();
    private destroy$ = new Subject<void>();

    private projectService = inject(SongProjectService);
    private notificationService = inject(NotificationService);
    private translate = inject(TranslateService);
    private router = inject(Router);
    private dialog = inject(MatDialog);
    private settingsService = inject(UserSettingsService);
    private apiConfig = inject(ApiConfigService);
    private resourceBlobService = inject(ResourceBlobService);

    // Navigation state (must be captured in constructor)
    private navigationState: any = null;

    constructor() {
        // IMPORTANT: getCurrentNavigation() must be called in constructor!
        const navigation = this.router.getCurrentNavigation();
        this.navigationState = navigation?.extras?.state;

        // Load user settings for page size
        const settings = this.settingsService.getCurrentSettings();
        this.pagination.limit = settings.projectListLimit;
    }

    ngOnInit(): void {
        // Setup search debounce
        this.searchSubject
            .pipe(
                debounceTime(300),
                distinctUntilChanged(),
                takeUntil(this.destroy$)
            )
            .subscribe(searchTerm => {
                this.searchTerm = searchTerm;
                this.pagination.offset = 0;
                this.loadProjects();
            });

        // Check navigation state for status filter (e.g., for archived projects from Song Release links)
        const targetStatus = this.navigationState?.["targetStatus"];
        if (targetStatus && ["all", "new", "progress", "archived"].includes(targetStatus)) {
            this.currentStatus = targetStatus as "all" | "new" | "progress" | "archived";
        }

        // Load initial data and auto-select project if provided via state
        this.loadProjects().then(() => {
            const selectedProjectId = this.navigationState?.["selectedProjectId"];
            if (selectedProjectId) {
                this.selectProjectById(selectedProjectId);
            } else if (this.projectList.length > 0 && !this.selectedProject) {
                // Auto-select first project if no navigation state
                this.selectProject(this.projectList[0]);
            }
        });
    }

    ngOnDestroy(): void {
        this.destroy$.next();
        this.destroy$.complete();
    }

    /**
     * Load projects list from API.
     */
    async loadProjects(page = 0): Promise<void> {
        this.isLoading = true;

        try {
            const offset = page * this.pagination.limit;
            const statusParam = this.currentStatus === "all" ? undefined : this.currentStatus;

            const response = await firstValueFrom(
                this.projectService.getProjects(
                    this.pagination.limit,
                    offset,
                    this.searchTerm || undefined,
                    undefined, // tags
                    statusParam
                )
            );

            this.projectList = response.data;
            this.pagination = response.pagination;
            this.pagination.offset = offset;
            this.totalProjects = response.pagination.total;

            // Load cover images as blobs (with JWT authentication)
            this.projectList.forEach(project => {
                if (project.cover_info?.source === "release" && project.cover_info.release_id) {
                    const coverUrl = `${this.apiConfig.endpoints.songRelease.detail(project.cover_info.release_id)}/cover`;
                    this.resourceBlobService.getResourceBlobUrl(coverUrl)
                        .pipe(takeUntil(this.destroy$))
                        .subscribe({
                            next: (blobUrl) => {
                                if (blobUrl) {
                                    this.listItemCoverBlobUrls.set(project.id, blobUrl);
                                }
                            },
                            error: () => {
                                // Silently fail - placeholder will be shown
                            }
                        });
                }
            });
        } catch (error) {
            console.error("Failed to load projects:", error);
            this.notificationService.error(
                this.translate.instant("songProjects.messages.loadError")
            );
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * Select a project and load details.
     */
    async selectProject(project: SongProjectListItem): Promise<void> {
        this.isLoadingDetail = true;

        try {
            const response = await firstValueFrom(
                this.projectService.getProjectById(project.id)
            );

            this.selectedProject = response.data;

            // Sort folders numerically by folder_name (e.g., "01 Arrangement", "02 AI", ...")
            if (this.selectedProject?.folders) {
                this.selectedProject.folders.sort((a, b) =>
                    a.folder_name.localeCompare(b.folder_name, undefined, {numeric: true})
                );
            }

            // Load cover image as blob (with JWT authentication)
            if (this.selectedProject?.cover_info?.source === "release" && this.selectedProject.cover_info.release_id) {
                const coverUrl = `${this.apiConfig.endpoints.songRelease.detail(this.selectedProject.cover_info.release_id)}/cover`;
                this.resourceBlobService.getResourceBlobUrl(coverUrl)
                    .pipe(takeUntil(this.destroy$))
                    .subscribe({
                        next: (blobUrl) => {
                            if (blobUrl) {
                                this.selectedProjectCoverBlobUrl = blobUrl;
                            }
                        },
                        error: () => {
                            // Silently fail - placeholder will be shown
                            this.selectedProjectCoverBlobUrl = "";
                        }
                    });
            } else {
                this.selectedProjectCoverBlobUrl = "";
            }
        } catch (error) {
            console.error("Failed to load project details:", error);
            this.notificationService.error(
                this.translate.instant("songProjects.messages.loadError")
            );
        } finally {
            this.isLoadingDetail = false;
        }
    }

    /**
     * Select a project by ID (for auto-selection from router state).
     */
    async selectProjectById(projectId: string): Promise<void> {
        this.isLoadingDetail = true;

        try {
            const response = await firstValueFrom(
                this.projectService.getProjectById(projectId)
            );

            this.selectedProject = response.data;

            // Sort folders numerically by folder_name (e.g., "01 Arrangement", "02 AI", ...)
            if (this.selectedProject?.folders) {
                this.selectedProject.folders.sort((a, b) =>
                    a.folder_name.localeCompare(b.folder_name, undefined, {numeric: true})
                );
            }
        } catch (error) {
            console.error("Failed to load project details:", error);
            this.notificationService.error(
                this.translate.instant("songProjects.messages.loadError")
            );
        } finally {
            this.isLoadingDetail = false;
        }
    }

    /**
     * Refresh current project details.
     */
    async refreshProject(): Promise<void> {
        if (!this.selectedProject) return;

        try {
            this.isLoadingDetail = true;
            await this.selectProject(this.selectedProject);
            this.notificationService.success(
                this.translate.instant("common.refreshSuccess")
            );
        } catch (error) {
            console.error("Failed to refresh project:", error);
            this.notificationService.error(
                this.translate.instant("songProjects.messages.loadError")
            );
        }
    }

    /**
     * Delete project with confirmation.
     */
    async deleteProject(): Promise<void> {
        if (!this.selectedProject) return;

        const confirmed = confirm(
            this.translate.instant("songProjects.messages.deleteConfirm")
        );

        if (!confirmed) return;

        try {
            await firstValueFrom(
                this.projectService.deleteProject(this.selectedProject.id)
            );

            this.notificationService.success(
                this.translate.instant("songProjects.messages.deleteSuccess")
            );

            // Reset selection and reload list
            this.selectedProject = null;
            await this.loadProjects();
        } catch (error) {
            console.error("Failed to delete project:", error);
            this.notificationService.error(
                this.translate.instant("songProjects.messages.deleteError")
            );
        }
    }

    /**
     * Handle search input.
     */
    onSearchChange(searchTerm: string): void {
        this.searchSubject.next(searchTerm);
    }

    /**
     * Clear search input.
     */
    clearSearch(): void {
        this.searchTerm = "";
        this.searchSubject.next("");
    }

    /**
     * Handle status filter change.
     */
    onStatusChange(status: "all" | "new" | "progress" | "archived"): void {
        this.currentStatus = status;
        this.pagination.offset = 0;
        this.loadProjects();
    }

    /**
     * Change page (pagination).
     */
    async changePage(page: number): Promise<void> {
        await this.loadProjects(page);
    }

    /**
     * Get current page number (0-indexed).
     */
    get currentPage(): number {
        return Math.floor(this.pagination.offset / this.pagination.limit);
    }

    /**
     * Get total number of pages.
     */
    get totalPages(): number {
        return Math.ceil(this.pagination.total / this.pagination.limit);
    }

    /**
     * Format file size to human-readable string.
     */
    formatFileSize(bytes: number): string {
        if (bytes === 0) return "0 Bytes";

        const k = 1024;
        const sizes = ["Bytes", "KB", "MB", "GB", "TB"];
        const i = Math.floor(Math.log(bytes) / Math.log(k));

        return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
    }

    /**
     * Get file path relative to folder (strips folder name prefix).
     * Example: "01 Arrangement/Media/drums.wav" → "Media/drums.wav"
     *
     * @param relativePath Full relative path (e.g., "01 Arrangement/Media/drums.wav")
     * @param folderName Folder name (e.g., "01 Arrangement")
     * @returns Path within folder (e.g., "Media/drums.wav")
     */
    getFilePathInFolder(relativePath: string, folderName: string): string {
        // Remove folder name prefix if present
        const prefix = folderName + "/";
        if (relativePath.startsWith(prefix)) {
            return relativePath.substring(prefix.length);
        }
        // Fallback: return full path if prefix doesn't match
        return relativePath;
    }

    /**
     * Download file (opens pre-signed URL).
     */
    downloadFile(downloadUrl: string): void {
        if (downloadUrl) {
            window.open(downloadUrl, "_blank");
        }
    }

    /**
     * Upload file to project folder.
     */
    async uploadFile(folder: any): Promise<void> {
        // Check if uploads are allowed
        if (!this.canUploadFiles()) {
            this.notificationService.error(
                this.translate.instant("songProjects.warnings.uploadBlocked")
            );
            return;
        }

        // Create hidden file input
        const input = document.createElement("input");
        input.type = "file";
        input.accept = "*";

        input.onchange = async (e: any) => {
            const file = e.target.files[0];
            if (!file) return;

            // Validate file size (500MB max)
            const maxSizeBytes = 500 * 1024 * 1024; // 500MB
            if (file.size > maxSizeBytes) {
                this.notificationService.error(
                    this.translate.instant("songProjects.messages.fileTooLarge", {size: "500MB"})
                );
                return;
            }

            // Create FormData
            const formData = new FormData();
            formData.append("file", file);
            formData.append("folder_id", folder.id);

            try {
                await firstValueFrom(
                    this.projectService.uploadFile(this.selectedProject!.id, formData)
                );

                this.notificationService.success(
                    this.translate.instant("songProjects.messages.uploadSuccess")
                );

                // Reload project details to show new file
                if (this.selectedProject) {
                    await this.selectProject(this.selectedProject);
                }
            } catch (error) {
                console.error("Upload failed:", error);
                this.notificationService.error(
                    this.translate.instant("songProjects.messages.uploadError")
                );
            }
        };

        // Trigger file selection dialog
        input.click();
    }

    /**
     * Copy CLI upload command to clipboard.
     */
    async copyCLICommand(folder: any): Promise<void> {
        if (!this.selectedProject) return;

        const command = `aiproxy-cli upload ${this.selectedProject.id} ${folder.id}`;

        try {
            await navigator.clipboard.writeText(command);
            this.notificationService.success(
                this.translate.instant("songProjects.messages.cliUploadCommandCopied")
            );
        } catch (error) {
            console.error("Failed to copy to clipboard:", error);
            this.notificationService.error(
                this.translate.instant("songProjects.messages.clipboardError")
            );
        }
    }

    /**
     * Copy CLI download command to clipboard.
     */
    async copyCLIDownloadCommand(folder: any): Promise<void> {
        if (!this.selectedProject) return;

        const command = `aiproxy-cli download ${this.selectedProject.id} ${folder.id}`;

        try {
            await navigator.clipboard.writeText(command);
            this.notificationService.success(
                this.translate.instant("songProjects.messages.cliDownloadCommandCopied")
            );
        } catch (error) {
            console.error("Clipboard copy failed:", error);
            this.notificationService.error(
                this.translate.instant("songProjects.messages.cliCommandCopyFailed")
            );
        }
    }

    /**
     * Copy CLI mirror command to clipboard.
     */
    async copyCLIMirrorCommand(folder: any): Promise<void> {
        if (!this.selectedProject) return;

        const command = `aiproxy-cli mirror ${this.selectedProject.id} ${folder.id} . --dry-run`;

        try {
            await navigator.clipboard.writeText(command);
            this.notificationService.success(
                this.translate.instant("songProjects.messages.cliMirrorCommandCopied")
            );
        } catch (error) {
            console.error("Clipboard copy failed:", error);
            this.notificationService.error(
                this.translate.instant("songProjects.messages.cliCommandCopyFailed")
            );
        }
    }

    /**
     * Copy CLI clone command to clipboard (complete clone).
     */
    async copyCLICompleteCloneCommand(): Promise<void> {
        if (!this.selectedProject) return;

        const command = `aiproxy-cli clone ${this.selectedProject.id} .`;

        try {
            await navigator.clipboard.writeText(command);
            this.notificationService.success(
                this.translate.instant("songProjects.messages.cliCompleteCloneCommandCopied")
            );
        } catch (error) {
            console.error("Clipboard copy failed:", error);
            this.notificationService.error(
                this.translate.instant("songProjects.messages.cliCommandCopyFailed")
            );
        }
    }


    /**
     * Open dialog to create new project.
     */
    createNewProject(): void {
        const dialogRef = this.dialog.open(CreateProjectDialogComponent, {
            width: "600px",
            minHeight: "400px",
            disableClose: false
        });

        dialogRef.afterClosed().subscribe(async (result) => {
            if (!result) {
                return; // User cancelled
            }

            try {
                await firstValueFrom(
                    this.projectService.createProject(result)
                );

                this.notificationService.success(
                    this.translate.instant("songProjects.messages.createSuccess")
                );

                // Reload projects list
                await this.loadProjects();
            } catch (error) {
                console.error("Failed to create project:", error);
                this.notificationService.error(
                    this.translate.instant("songProjects.messages.saveError")
                );
            }
        });
    }

    /**
     * Navigate to Song View with song ID in state.
     * Passes targetWorkflow to switch to archived tab if song is archived.
     */
    openSong(song: AssignedSong): void {
        this.router.navigate(["/songview"], {
            state: {
                selectedSongId: song.id,
                targetWorkflow: song.workflow === "archived" ? "archived" : "all"
            }
        });
    }

    /**
     * Navigate to Sketch Library with sketch ID in state.
     * Passes targetWorkflow to switch to archived tab if sketch is archived.
     */
    openSketch(sketch: AssignedSketch): void {
        this.router.navigate(["/song-sketch-library"], {
            state: {
                selectedSketchId: sketch.id,
                targetWorkflow: sketch.workflow === "archived" ? "archived" : "all"
            }
        });
    }

    /**
     * Navigate to Image View with image ID in state.
     */
    openImage(imageId: string): void {
        this.router.navigate(["/imageview"], {
            state: {selectedImageId: imageId}
        });
    }

    /**
     * Get smart folder content label (e.g., "2 images", "3 assets, 1 file").
     */
    getFolderContentLabel(folder: any): string {
        const fileCount = folder.files?.length || 0;
        const songCount = folder.assigned_songs?.length || 0;
        const sketchCount = folder.assigned_sketches?.length || 0;
        const imageCount = folder.assigned_images?.length || 0;
        const totalAssets = songCount + sketchCount + imageCount;

        // Only images (specific type)
        if (totalAssets > 0 && fileCount === 0 && songCount === 0 && sketchCount === 0 && imageCount > 0) {
            return this.translate.instant("songProjects.detail.folderContent.images", {count: imageCount});
        }

        // Only songs (specific type)
        if (totalAssets > 0 && fileCount === 0 && songCount > 0 && sketchCount === 0 && imageCount === 0) {
            return this.translate.instant("songProjects.detail.folderContent.songs", {count: songCount});
        }

        // Only sketches (specific type)
        if (totalAssets > 0 && fileCount === 0 && songCount === 0 && sketchCount > 0 && imageCount === 0) {
            return this.translate.instant("songProjects.detail.folderContent.sketches", {count: sketchCount});
        }

        // Mixed assets only
        if (totalAssets > 0 && fileCount === 0) {
            return this.translate.instant("songProjects.detail.folderContent.assets", {count: totalAssets});
        }

        // Assets + files
        if (totalAssets > 0 && fileCount > 0) {
            return this.translate.instant("songProjects.detail.folderContent.assetsAndFiles", {
                assetCount: totalAssets,
                fileCount: fileCount
            });
        }

        // Only files
        if (fileCount > 0) {
            return this.translate.instant("songProjects.detail.folderContent.files", {count: fileCount});
        }

        // Empty
        return this.translate.instant("songProjects.detail.folderContent.empty");
    }

    /**
     * Open edit project dialog (using create dialog in edit mode)
     */
    openEditDialog(): void {
        if (!this.selectedProject) return;

        const dialogRef = this.dialog.open(CreateProjectDialogComponent, {
            width: "600px",
            maxHeight: "90vh",
            data: {
                project_id: this.selectedProject.id,
                project_name: this.selectedProject.project_name,
                description: this.selectedProject.description,
                tags: this.selectedProject.tags,
                // Pass assigned elements for Advanced section
                all_assigned_songs: this.selectedProject.all_assigned_songs,
                all_assigned_sketches: this.selectedProject.all_assigned_sketches,
                all_assigned_images: this.selectedProject.all_assigned_images
            }
        });

        dialogRef.afterClosed().subscribe(async (result) => {
            // If dialog was closed without result but unassignments were made, reload project
            if (!result && this.selectedProject) {
                // Reload to reflect any unassignments made in Advanced section
                const projectInList = this.projectList.find(p => p.id === this.selectedProject!.id);
                if (projectInList) {
                    await this.selectProject(projectInList);
                }
                return;
            }

            if (!result || !this.selectedProject) return;

            try {
                await firstValueFrom(
                    this.projectService.updateProject(this.selectedProject.id, {
                        project_name: result.project_name,
                        description: result.description,
                        tags: result.tags
                    })
                );

                // Update local state
                this.selectedProject.project_name = result.project_name;
                this.selectedProject.description = result.description;
                this.selectedProject.tags = result.tags;

                // Update in list
                const projectInList = this.projectList.find(p => p.id === this.selectedProject!.id);
                if (projectInList) {
                    projectInList.project_name = result.project_name;
                    projectInList.tags = result.tags;
                    // Reload project to reflect any unassignments made in Advanced section
                    await this.selectProject(projectInList);
                }

                this.notificationService.success(
                    this.translate.instant("songProjects.messages.projectUpdated")
                );
            } catch (error) {
                console.error("Failed to update project:", error);
                this.notificationService.error(
                    this.translate.instant("common.error")
                );
            }
        });
    }

    /**
     * Toggle project archive status
     */
    async toggleProjectStatus(): Promise<void> {
        if (!this.selectedProject) return;

        const newStatus = this.selectedProject.project_status === "archived" ? "progress" : "archived";

        try {
            await firstValueFrom(
                this.projectService.updateProject(this.selectedProject.id, {
                    project_status: newStatus
                })
            );

            this.selectedProject.project_status = newStatus;

            // Update item in list and reload to respect filters
            const projectInList = this.projectList.find(p => p.id === this.selectedProject!.id);
            if (projectInList) {
                projectInList.project_status = newStatus;
            }
            await this.loadProjects();

            this.notificationService.success(
                this.translate.instant("songProjects.messages.statusUpdated")
            );
        } catch (error) {
            console.error("Failed to update project status:", error);
            this.notificationService.error(
                this.translate.instant("common.error")
            );
        }
    }

    /**
     * Clear all files in a folder
     */
    async clearFolder(folderId: string): Promise<void> {
        if (!this.selectedProject) return;

        const folder = this.selectedProject.folders.find(f => f.id === folderId);
        if (!folder) return;

        // Confirmation dialog
        const message = this.translate.instant("songProjects.dialogs.clearFolder.message", {folderName: folder.folder_name});
        const confirmed = window.confirm(message);

        if (!confirmed) return;

        try {
            const response = await firstValueFrom(
                this.projectService.clearFolder(this.selectedProject.id, folderId)
            );

            // Refresh project to show updated file list
            await this.selectProject(this.selectedProject);

            this.notificationService.success(
                this.translate.instant("songProjects.messages.filesDeleted", {count: response.data.deleted})
            );
        } catch (error) {
            console.error("Failed to clear folder:", error);
            this.notificationService.error(
                this.translate.instant("common.error")
            );
        }
    }

    /**
     * Check if uploads are allowed (not archived)
     */
    canUploadFiles(): boolean {
        return this.selectedProject?.project_status !== "archived";
    }

    /**
     * Get CSS class for release status badge
     */
    getStatusBadgeClass(status: string | null): string {
        if (!status) return "release-status-draft";

        const statusMap: Record<string, string> = {
            "draft": "release-status-draft",
            "arranging": "release-status-progress",
            "mixing": "release-status-progress",
            "mastering": "release-status-progress",
            "uploaded": "release-status-uploaded",
            "released": "release-status-released",
            "rejected": "release-status-rejected",
            "downtaken": "release-status-rejected",
            "archived": "release-status-archived"
        };

        return statusMap[status] || "release-status-draft";
    }

    /**
     * Open release details
     */
    openRelease(releaseId: string): void {
        this.router.navigate(["/song-releases", releaseId]);
    }

    /**
     * Get cover URL for project list item (returns blob URL if loaded)
     */
    getProjectCoverUrl(project: SongProjectListItem): string | null {
        return this.listItemCoverBlobUrls.get(project.id) || null;
    }

    /**
     * Get cover URL for selected project detail (returns blob URL if loaded)
     */
    getSelectedProjectCoverUrl(): string | null {
        return this.selectedProjectCoverBlobUrl || null;
    }

    /**
     * Get initials from project name (for placeholder cover)
     */
    getInitials(name: string): string {
        return getInitials(name);
    }

    /**
     * Get color from project name (for placeholder cover background)
     */
    getColorFromString(name: string): string {
        return getColorFromString(name);
    }

    /**
     * Copy text to clipboard
     */
    async copyToClipboard(text: string): Promise<void> {
        try {
            await navigator.clipboard.writeText(text);
            this.notificationService.success(
                this.translate.instant("common.copiedToClipboard")
            );
        } catch (error) {
            console.error("Failed to copy to clipboard:", error);
            this.notificationService.error(
                this.translate.instant("songProjects.messages.clipboardError")
            );
        }
    }
}
