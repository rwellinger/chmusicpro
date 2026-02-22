import {Component, inject, OnDestroy, OnInit} from "@angular/core";
import {CommonModule} from "@angular/common";
import {FormsModule} from "@angular/forms";
import {ActivatedRoute, Router} from "@angular/router";
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
import {MatTabsModule} from "@angular/material/tabs";
import {MatProgressBarModule} from "@angular/material/progress-bar";
import {HttpEventType} from "@angular/common/http";

import {SongProjectService} from "../../services/business/song-project.service";
import {NotificationService} from "../../services/ui/notification.service";
import {UserSettingsService} from "../../services/user-settings.service";
import {FileIgnoreService} from "../../services/utils/file-ignore.service";
import {FileHashService} from "../../services/utils/file-hash.service";
import {CreateProjectDialogComponent} from "../../dialogs/create-project-dialog/create-project-dialog.component";
import {MirrorPreviewDialogComponent} from "../../dialogs/mirror-preview-dialog/mirror-preview-dialog.component";
import {AssignedSketch, AssignedWorkshop, BatchUploadResponse, ChunkedUploadProgress, MirrorFileEntry, SongProjectDetail, SongProjectListItem} from "../../models/song-project.model";
import {ChunkedUploadService} from "../../services/business/chunked-upload.service";
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
        MatTabsModule,
        MatProgressBarModule
    ],
    templateUrl: "./song-projects.component.html",
    styleUrl: "./song-projects.component.scss"
})
export class SongProjectsComponent implements OnInit, OnDestroy {
    // Project list and pagination
    projectList: SongProjectListItem[] = [];
    selectedProject: SongProjectDetail | null = null;
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

    // Upload state
    uploadingFolderId: string | null = null;
    uploadProgress = 0;
    uploadedFileCount = 0;
    uploadTotalFileCount = 0;
    uploadErrors: { filename?: string; error: string }[] = [];
    isUploadComplete = false;
    isDragOver: string | null = null;

    // Chunked upload state
    currentChunkedFile: string | null = null;
    chunkedProgress: ChunkedUploadProgress | null = null;

    // Mirror sync state
    mirrorPhase: "idle" | "filtering" | "hashing" | "comparing" | "uploading" | "moving" | "deleting" = "idle";
    mirrorHashProgress = {current: 0, total: 0};

    // Folder download state
    folderDownloadProgress: { folderId: string; current: number; total: number; filename: string } | null = null;

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
    private route = inject(ActivatedRoute);
    private fileIgnoreService = inject(FileIgnoreService);
    private fileHashService = inject(FileHashService);
    private chunkedUploadService = inject(ChunkedUploadService);

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

        // Auto-open create dialog if requested via query param (e.g., from dashboard)
        this.route.queryParams.pipe(takeUntil(this.destroy$)).subscribe(params => {
            if (params["action"] === "create") {
                this.createNewProject();
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
     * Delete a single file from the project.
     */
    async deleteFile(file: any): Promise<void> {
        if (!this.selectedProject) return;

        const filename = file.filename || file.relative_path || "file";
        const confirmed = confirm(
            this.translate.instant("songProjects.messages.deleteFileConfirm", {filename})
        );
        if (!confirmed) return;

        try {
            await firstValueFrom(
                this.projectService.deleteFiles(this.selectedProject.id, [file.id])
            );

            // Refresh project to show updated file list
            await this.selectProject(this.selectedProject);
        } catch (error) {
            console.error("Failed to delete file:", error);
            this.notificationService.error(
                this.translate.instant("songProjects.messages.deleteFileError")
            );
        }
    }

    /**
     * Upload multiple files to project folder.
     */
    uploadFiles(folder: any): void {
        if (!this.canUploadFiles()) {
            this.notificationService.error(
                this.translate.instant("songProjects.warnings.uploadBlocked")
            );
            return;
        }

        const input = document.createElement("input");
        input.type = "file";
        input.multiple = true;
        input.accept = "*";

        input.onchange = async (e: any) => {
            const files: File[] = Array.from(e.target.files || []);
            if (files.length === 0) return;
            await this.processMirrorSync(folder, files);
        };

        input.click();
    }

    /**
     * Upload an entire folder to project folder.
     */
    uploadFolder(folder: any): void {
        if (!this.canUploadFiles()) {
            this.notificationService.error(
                this.translate.instant("songProjects.warnings.uploadBlocked")
            );
            return;
        }

        const input = document.createElement("input");
        input.type = "file";
        input.setAttribute("webkitdirectory", "");
        input.multiple = true;

        input.onchange = async (e: any) => {
            const files: File[] = Array.from(e.target.files || []);
            if (files.length === 0) return;
            await this.processMirrorSync(folder, files);
        };

        input.click();
    }

    /**
     * Core batch upload engine. Splits files into small (<20MB, batch upload)
     * and large (>=20MB, chunked upload) groups.
     */
    async processBatchUpload(folder: any, files: File[]): Promise<void> {
        const maxSizeBytes = 500 * 1024 * 1024; // 500MB
        const validFiles: File[] = [];
        const sizeErrors: { filename?: string; error: string }[] = [];

        // Validate file sizes
        for (const file of files) {
            if (file.size > maxSizeBytes) {
                sizeErrors.push({
                    filename: (file as any).webkitRelativePath || file.name,
                    error: this.translate.instant("songProjects.messages.fileTooLarge", {size: "500MB"})
                });
            } else {
                validFiles.push(file);
            }
        }

        if (validFiles.length === 0 && sizeErrors.length > 0) {
            this.uploadErrors = sizeErrors;
            this.isUploadComplete = true;
            this.uploadingFolderId = folder.id;
            return;
        }

        // Split into small files (batch) and large files (chunked)
        const smallFiles = validFiles.filter(f => !this.chunkedUploadService.shouldUseChunkedUpload(f));
        const largeFiles = validFiles.filter(f => this.chunkedUploadService.shouldUseChunkedUpload(f));

        // Initialize upload state
        this.uploadingFolderId = folder.id;
        this.uploadProgress = 0;
        this.uploadedFileCount = 0;
        this.uploadTotalFileCount = validFiles.length;
        this.uploadErrors = [...sizeErrors];
        this.isUploadComplete = false;
        this.currentChunkedFile = null;
        this.chunkedProgress = null;

        let totalUploaded = 0;
        let totalFailed = 0;

        // Calculate weight for progress: small files as one group, each large file as individual
        const totalWeight = (smallFiles.length > 0 ? 1 : 0) + largeFiles.length;
        let completedWeight = 0;

        // Upload small files via batch upload (existing logic)
        if (smallFiles.length > 0) {
            const batchSize = 3;
            const batches: File[][] = [];
            for (let i = 0; i < smallFiles.length; i += batchSize) {
                batches.push(smallFiles.slice(i, i + batchSize));
            }

            for (let batchIndex = 0; batchIndex < batches.length; batchIndex++) {
                const batch = batches[batchIndex];
                const formData = new FormData();

                for (const file of batch) {
                    const filename = (file as any).webkitRelativePath || file.name;
                    formData.append("files", file, filename);
                }

                try {
                    const result = await new Promise<BatchUploadResponse>((resolve, reject) => {
                        this.projectService.batchUploadFiles(
                            this.selectedProject!.id,
                            folder.id,
                            formData
                        ).subscribe({
                            next: (event) => {
                                if (event.type === HttpEventType.UploadProgress && event.total) {
                                    const batchProgress = event.loaded / event.total;
                                    const smallProgress = (batchIndex + batchProgress) / batches.length;
                                    this.uploadProgress = Math.round(((completedWeight + smallProgress) / totalWeight) * 100);
                                } else if (event.type === HttpEventType.Response) {
                                    resolve(event.body!);
                                }
                            },
                            error: (error) => reject(error)
                        });
                    });

                    totalUploaded += result.data.uploaded;
                    totalFailed += result.data.failed;
                    this.uploadedFileCount = totalUploaded;

                    if (result.data.errors?.length) {
                        this.uploadErrors.push(...result.data.errors);
                    }
                } catch (error: any) {
                    console.error(`Batch ${batchIndex + 1} failed:`, error);
                    totalFailed += batch.length;
                    this.uploadErrors.push({
                        error: `Batch ${batchIndex + 1} failed: ${error?.message || "Unknown error"}`
                    });
                }
            }
            completedWeight += 1;
        }

        // Upload large files via chunked upload (one at a time)
        for (const largeFile of largeFiles) {
            const filename = (largeFile as any).webkitRelativePath || largeFile.name;
            this.currentChunkedFile = filename;

            try {
                // Hash the file first
                const fileHash = await this.fileHashService.hashFile(largeFile);

                await this.chunkedUploadService.uploadFileChunked(
                    this.selectedProject!.id,
                    folder.id,
                    largeFile,
                    filename,
                    fileHash,
                    (progress) => {
                        this.chunkedProgress = progress;
                        const chunkedFraction = progress.percentComplete / 100;
                        this.uploadProgress = Math.round(((completedWeight + chunkedFraction) / totalWeight) * 100);
                    }
                );

                totalUploaded += 1;
                this.uploadedFileCount = totalUploaded;
            } catch (error: any) {
                console.error(`Chunked upload failed for ${filename}:`, error);
                totalFailed += 1;
                this.uploadErrors.push({
                    filename,
                    error: error?.message || "Chunked upload failed"
                });
            }

            completedWeight += 1;
        }

        // Complete
        this.uploadProgress = 100;
        this.isUploadComplete = true;
        this.currentChunkedFile = null;
        this.chunkedProgress = null;

        if (totalFailed === 0) {
            // Upload successful
        } else if (totalUploaded > 0) {
            this.notificationService.info(
                this.translate.instant("songProjects.upload.batchUploadPartial", {
                    uploaded: totalUploaded,
                    failed: totalFailed
                })
            );
        } else {
            this.notificationService.error(
                this.translate.instant("songProjects.upload.batchUploadError")
            );
        }

        // Refresh project to show new files
        if (this.selectedProject) {
            await this.selectProject(this.selectedProject);
        }
    }

    /**
     * Drag-and-drop: dragover handler.
     */
    onDragOver(event: DragEvent, folderId: string): void {
        event.preventDefault();
        event.stopPropagation();
        if (this.canUploadFiles()) {
            this.isDragOver = folderId;
        }
    }

    /**
     * Drag-and-drop: dragleave handler.
     */
    onDragLeave(event: DragEvent, folderId: string): void {
        event.preventDefault();
        event.stopPropagation();
        // Only clear if leaving the drop zone (not entering a child element)
        const relatedTarget = event.relatedTarget as HTMLElement;
        const currentTarget = event.currentTarget as HTMLElement;
        if (!currentTarget.contains(relatedTarget)) {
            if (this.isDragOver === folderId) {
                this.isDragOver = null;
            }
        }
    }

    /**
     * Drag-and-drop: drop handler. Supports files and directories.
     */
    async onDrop(event: DragEvent, folder: any): Promise<void> {
        event.preventDefault();
        event.stopPropagation();
        this.isDragOver = null;

        if (!this.canUploadFiles()) {
            this.notificationService.error(
                this.translate.instant("songProjects.warnings.uploadBlocked")
            );
            return;
        }

        const items = event.dataTransfer?.items;
        if (items) {
            const files: File[] = [];
            const promises: Promise<void>[] = [];

            for (const item of Array.from(items)) {
                const entry = item.webkitGetAsEntry?.();
                if (entry) {
                    promises.push(this.readEntry(entry, "", files));
                }
            }

            await Promise.all(promises);

            if (files.length > 0) {
                await this.processMirrorSync(folder, files);
            }
            return;
        }

        // Fallback: plain file list
        const fileList = event.dataTransfer?.files;
        if (fileList && fileList.length > 0) {
            const files: File[] = Array.from(fileList);
            await this.processMirrorSync(folder, files);
        }
    }

    /**
     * Recursively read a FileSystemEntry (file or directory).
     */
    private readEntry(entry: FileSystemEntry, path: string, files: File[]): Promise<void> {
        return new Promise((resolve) => {
            if (entry.isFile) {
                (entry as FileSystemFileEntry).file((file) => {
                    // Create a new file with the relative path as name
                    const relativePath = path ? `${path}/${file.name}` : file.name;
                    const renamedFile = new File([file], relativePath, {type: file.type, lastModified: file.lastModified});
                    files.push(renamedFile);
                    resolve();
                }, () => resolve());
            } else if (entry.isDirectory) {
                const reader = (entry as FileSystemDirectoryEntry).createReader();
                const dirPath = path ? `${path}/${entry.name}` : entry.name;
                const readAllEntries = (allEntries: FileSystemEntry[]) => {
                    reader.readEntries((entries) => {
                        if (entries.length === 0) {
                            // Done reading - process all entries
                            Promise.all(allEntries.map(e => this.readEntry(e, dirPath, files)))
                                .then(() => resolve());
                        } else {
                            // readEntries may return partial results, keep reading
                            readAllEntries([...allEntries, ...entries]);
                        }
                    }, () => resolve());
                };
                readAllEntries([]);
            } else {
                resolve();
            }
        });
    }

    /**
     * Dismiss the upload status section.
     */
    dismissUploadStatus(): void {
        this.uploadingFolderId = null;
        this.uploadProgress = 0;
        this.uploadedFileCount = 0;
        this.uploadTotalFileCount = 0;
        this.uploadErrors = [];
        this.isUploadComplete = false;
    }

    /**
     * Mirror sync: filter, hash, compare, preview, execute.
     * Replaces direct batch upload with intelligent sync.
     */
    async processMirrorSync(folder: any, rawFiles: File[]): Promise<void> {
        if (!this.selectedProject) return;

        const projectId = this.selectedProject.id;
        const folderId = folder.id;

        // Build file entries with relative paths
        const fileEntries = rawFiles.map(file => ({
            file,
            relativePath: (file as any).webkitRelativePath || file.name
        }));

        // Phase 1: Filter
        this.mirrorPhase = "filtering";
        this.uploadingFolderId = folderId;
        this.isUploadComplete = false;
        this.uploadErrors = [];

        await this.fileIgnoreService.loadPatterns();
        const {accepted, ignored} = this.fileIgnoreService.filterFiles(fileEntries);

        if (accepted.length === 0) {
            this.mirrorPhase = "idle";
            this.uploadingFolderId = null;
            this.notificationService.info(
                this.translate.instant("songProjects.mirror.noFilesAfterFilter")
            );
            return;
        }

        // Phase 2: Hash
        this.mirrorPhase = "hashing";
        this.mirrorHashProgress = {current: 0, total: accepted.length};

        const hashes = await this.fileHashService.hashFiles(accepted, (current, total) => {
            this.mirrorHashProgress = {current, total};
        });

        // Build MirrorFileEntry[]
        const mirrorEntries: MirrorFileEntry[] = accepted.map(entry => ({
            relative_path: entry.relativePath,
            file_hash: hashes.get(entry.relativePath)!,
            file_size_bytes: entry.file.size
        }));

        // Phase 3: Compare
        this.mirrorPhase = "comparing";

        let compareResult;
        try {
            const response = await firstValueFrom(
                this.projectService.mirrorCompare(projectId, folderId, mirrorEntries)
            );
            compareResult = response.data;
        } catch (error) {
            console.error("Mirror compare failed:", error);
            this.mirrorPhase = "idle";
            this.uploadingFolderId = null;
            this.notificationService.error(
                this.translate.instant("songProjects.messages.syncError")
            );
            return;
        }

        // Check if already up to date
        const totalChanges = compareResult.to_upload.length + compareResult.to_update.length +
            compareResult.to_move.length + compareResult.to_delete.length;

        if (totalChanges === 0) {
            this.mirrorPhase = "idle";
            this.uploadingFolderId = null;
            return;
        }

        // Phase 4: Preview Dialog
        this.mirrorPhase = "idle";

        // Calculate total upload size for new + updated files
        const uploadPaths = new Set([...compareResult.to_upload, ...compareResult.to_update]);
        const totalUploadSize = accepted
            .filter(e => uploadPaths.has(e.relativePath))
            .reduce((sum, e) => sum + e.file.size, 0);

        const dialogRef = this.dialog.open(MirrorPreviewDialogComponent, {
            width: "700px",
            maxHeight: "80vh",
            data: {
                folderName: folder.folder_name,
                toUpload: compareResult.to_upload,
                toUpdate: compareResult.to_update,
                toMove: compareResult.to_move,
                toDelete: compareResult.to_delete,
                unchanged: compareResult.unchanged,
                totalUploadSize,
                ignoredCount: ignored.length
            }
        });

        const confirmed = await firstValueFrom(dialogRef.afterClosed());
        if (!confirmed) {
            this.uploadingFolderId = null;
            return;
        }

        // Phase 5: Execute sync
        const filesToUpload = accepted.filter(e =>
            compareResult.to_upload.includes(e.relativePath) ||
            compareResult.to_update.includes(e.relativePath)
        );

        // 5a: Upload new + updated files
        if (filesToUpload.length > 0) {
            this.mirrorPhase = "uploading";
            const uploadFiles = filesToUpload.map(e => {
                // Create file with relativePath as name for batch upload
                return new File([e.file], e.relativePath, {
                    type: e.file.type,
                    lastModified: e.file.lastModified
                });
            });
            await this.processBatchUpload(folder, uploadFiles);
        }

        // 5b: Move files
        if (compareResult.to_move.length > 0) {
            this.mirrorPhase = "moving";
            try {
                await firstValueFrom(
                    this.projectService.batchMoveFiles(projectId, compareResult.to_move)
                );
            } catch (error) {
                console.error("Batch move failed:", error);
                this.uploadErrors.push({error: "Move operation failed"});
            }
        }

        // 5c: Delete files
        if (compareResult.to_delete.length > 0) {
            this.mirrorPhase = "deleting";
            const deleteIds = compareResult.to_delete.map(f => f.file_id);
            try {
                await firstValueFrom(
                    this.projectService.deleteFiles(projectId, deleteIds)
                );
            } catch (error) {
                console.error("Batch delete failed:", error);
                this.uploadErrors.push({error: "Delete operation failed"});
            }
        }

        // Phase 6: Complete
        this.mirrorPhase = "idle";

        // Refresh project
        if (this.selectedProject) {
            await this.selectProject(this.selectedProject);
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
     * Navigate to Text Workshop with workshop ID in state.
     */
    openWorkshop(workshop: AssignedWorkshop): void {
        this.router.navigate(["/text-workshop"], {
            state: {selectedWorkshopId: workshop.id}
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
        const sketchCount = folder.assigned_sketches?.length || 0;
        const imageCount = folder.assigned_images?.length || 0;
        const workshopCount = folder.assigned_workshops?.length || 0;
        const totalAssets = sketchCount + imageCount + workshopCount;

        // Only images (specific type)
        if (totalAssets > 0 && fileCount === 0 && sketchCount === 0 && imageCount > 0) {
            return this.translate.instant("songProjects.detail.folderContent.images", {count: imageCount});
        }

        // Only sketches (specific type)
        if (totalAssets > 0 && fileCount === 0 && sketchCount > 0 && imageCount === 0) {
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
                all_assigned_sketches: this.selectedProject.all_assigned_sketches,
                all_assigned_images: this.selectedProject.all_assigned_images,
                all_assigned_workshops: this.selectedProject.all_assigned_workshops
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
            await firstValueFrom(
                this.projectService.clearFolder(this.selectedProject.id, folderId)
            );

            // Refresh project to show updated file list
            await this.selectProject(this.selectedProject);
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
        } catch (error) {
            console.error("Failed to copy to clipboard:", error);
            this.notificationService.error(
                this.translate.instant("songProjects.messages.clipboardError")
            );
        }
    }

    async downloadTemplateZip(): Promise<void> {
        if (!this.selectedProject) return;

        try {
            const blob = await firstValueFrom(
                this.projectService.downloadTemplateZip(this.selectedProject.id)
            );
            await this.saveBlob(blob, `${this.selectedProject.project_name}-template.zip`);
        } catch (error) {
            console.error("Failed to download template ZIP:", error);
            this.notificationService.error(
                this.translate.instant("songProjects.download.zipDownloadError")
            );
        }
    }

    async downloadFolderZip(folder: any): Promise<void> {
        if (!this.selectedProject) return;
        const projectId = this.selectedProject.id;
        const files = folder.files || [];

        // Strategy 1: Direct to directory (Chromium) - try first
        if ("showDirectoryPicker" in window) {
            try {
                const dirHandle = await (window as any).showDirectoryPicker({mode: "readwrite"});

                this.folderDownloadProgress = {folderId: folder.id, current: 0, total: files.length, filename: ""};

                for (let i = 0; i < files.length; i++) {
                    const file = files[i];
                    this.folderDownloadProgress = {
                        folderId: folder.id,
                        current: i + 1,
                        total: files.length,
                        filename: file.filename
                    };

                    const blob = await firstValueFrom(
                        this.projectService.downloadFile(projectId, file.id)
                    );

                    // Recreate subdirectories from relative_path, stripping folder name prefix
                    let targetDir = dirHandle;
                    let pathParts = (file.relative_path || file.filename).split("/");
                    const fileName = pathParts.pop()!;
                    // Strip folder name if relative_path starts with it (user already picked the folder)
                    if (pathParts.length > 0 && pathParts[0] === folder.folder_name) {
                        pathParts = pathParts.slice(1);
                    }
                    for (const part of pathParts) {
                        targetDir = await targetDir.getDirectoryHandle(part, {create: true});
                    }

                    const fileHandle = await targetDir.getFileHandle(fileName, {create: true});
                    const writable = await fileHandle.createWritable();
                    await writable.write(blob);
                    await writable.close();
                }

                this.folderDownloadProgress = null;
                return;
            } catch (err: any) {
                this.folderDownloadProgress = null;
                // User cancelled picker → fall through to ZIP
                if (err?.name === "AbortError") {
                    return;
                }
                // Other error (e.g. permission denied) → fall through to ZIP
            }
        }

        // Strategy 2: ZIP fallback with "Save As" or direct download
        this.folderDownloadProgress = {folderId: folder.id, current: 0, total: 0, filename: ""};

        try {
            const blob = await firstValueFrom(
                this.projectService.downloadFolderZip(this.selectedProject.id, folder.id)
            );

            await this.saveBlob(blob, `${folder.folder_name}.zip`);
        } catch (error) {
            console.error("Failed to download folder ZIP:", error);
            this.notificationService.error(
                this.translate.instant("songProjects.download.zipDownloadError")
            );
        } finally {
            this.folderDownloadProgress = null;
        }
    }

    private async saveBlob(blob: Blob, filename: string): Promise<void> {
        if ("showSaveFilePicker" in window) {
            try {
                const handle = await (window as any).showSaveFilePicker({
                    suggestedName: filename,
                    types: [{description: "ZIP Archive", accept: {"application/zip": [".zip"]}}]
                });
                const writable = await handle.createWritable();
                await writable.write(blob);
                await writable.close();
                return;
            } catch (err: any) {
                if (err?.name === "AbortError") {
                    return;
                }
                // Other errors (Brave SecurityError etc.) → fall through to <a> download
            }
        }

        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    }
}
