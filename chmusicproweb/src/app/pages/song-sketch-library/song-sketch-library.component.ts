import {Component, inject, OnDestroy, OnInit, ViewEncapsulation} from "@angular/core";
import {CommonModule} from "@angular/common";
import {FormsModule} from "@angular/forms";
import {Router} from "@angular/router";
import {debounceTime, distinctUntilChanged, firstValueFrom, Subject, takeUntil} from "rxjs";
import {TranslateModule, TranslateService} from "@ngx-translate/core";
import {MatCardModule} from "@angular/material/card";
import {MatSnackBarModule} from "@angular/material/snack-bar";
import {MatTabsModule} from "@angular/material/tabs";
import {MatDialog} from "@angular/material/dialog";

import {Sketch, SketchService} from "../../services/business/sketch.service";
import {NotificationService} from "../../services/ui/notification.service";
import {UserSettingsService} from "../../services/user-settings.service";
import {
    AssignToProjectDialogComponent
} from "../../dialogs/assign-to-project-dialog/assign-to-project-dialog.component";

@Component({
    selector: "app-song-sketch-library",
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        TranslateModule,
        MatCardModule,
        MatSnackBarModule,
        MatTabsModule
    ],
    templateUrl: "./song-sketch-library.component.html",
    styleUrl: "./song-sketch-library.component.scss",
    encapsulation: ViewEncapsulation.None
})
export class SongSketchLibraryComponent implements OnInit, OnDestroy {
    // Sketches list and pagination
    sketches: Sketch[] = [];
    selectedSketch: Sketch | null = null;
    pagination = {
        total: 0,
        limit: 8,
        offset: 0,
        has_more: false
    };

    // Search and filter
    searchTerm = "";
    currentWorkflow: "all" | "draft" | "used" | "archived" = "all";
    sortBy = "created_at";
    sortDirection: "asc" | "desc" = "desc";

    // UI state
    isLoading = false;
    showDeleteConfirm = false;
    deleteSketchId: string | null = null;

    // Navigation state (must be captured in constructor)
    private navigationState: any = null;

    // RxJS subjects
    private searchSubject = new Subject<string>();
    private destroy$ = new Subject<void>();

    private sketchService = inject(SketchService);
    private notificationService = inject(NotificationService);
    private translate = inject(TranslateService);
    private router = inject(Router);
    private settingsService = inject(UserSettingsService);
    private dialog = inject(MatDialog);

    constructor() {
        // IMPORTANT: getCurrentNavigation() must be called in constructor!
        const navigation = this.router.getCurrentNavigation();
        this.navigationState = navigation?.extras?.state;

        // Load user settings for page size
        const settings = this.settingsService.getCurrentSettings();
        this.pagination.limit = settings.sketchListLimit;

        // Setup search debouncing
        this.searchSubject.pipe(
            debounceTime(300),
            distinctUntilChanged(),
            takeUntil(this.destroy$)
        ).subscribe(searchTerm => {
            this.searchTerm = searchTerm;
            this.loadSketches();
        });
    }

    ngOnInit(): void {
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

        // Check if returning from save/edit with a selected sketch ID
        const selectedSketchId = this.navigationState?.["selectedSketchId"];
        const targetWorkflow = this.navigationState?.["targetWorkflow"];
        const returnPage = this.navigationState?.["returnPage"] || 0;

        // Set workflow filter BEFORE loading sketches (e.g., for archived sketches from Song Project links)
        if (targetWorkflow && ["all", "draft", "used", "archived"].includes(targetWorkflow)) {
            this.currentWorkflow = targetWorkflow as "all" | "draft" | "used" | "archived";
        }

        this.loadSketches(returnPage).then(() => {
            // Re-select the sketch after save if ID was provided
            if (selectedSketchId) {
                const sketch = this.sketches.find(s => s.id === selectedSketchId);
                if (sketch) {
                    this.selectSketch(sketch);
                } else {
                    // Fallback: Sketch not on this page (e.g., filters changed)
                    this.notificationService.info(
                        this.translate.instant("songSketch.library.messages.sketchSaved")
                    );
                }
            }
        });
    }

    ngOnDestroy(): void {
        this.destroy$.next();
        this.destroy$.complete();
    }

    async loadSketches(page = 0): Promise<void> {
        this.isLoading = true;
        try {
            const offset = page * this.pagination.limit;
            const workflowParam = this.currentWorkflow === "all" ? undefined : this.currentWorkflow;

            const response = await firstValueFrom(
                this.sketchService.getSketches(
                    this.pagination.limit,
                    offset,
                    workflowParam
                )
            );

            this.sketches = response.data || [];
            this.pagination = response.pagination || this.pagination;
            this.pagination.offset = offset;

            // Select first sketch if nothing selected
            if (this.sketches.length > 0 && !this.selectedSketch) {
                this.selectSketch(this.sketches[0]);
            } else if (this.sketches.length === 0) {
                this.selectedSketch = null;
            }
        } catch (error: any) {
            this.notificationService.error(
                this.translate.instant("songSketch.library.messages.loadingError") + ": " + error.message
            );
        } finally {
            this.isLoading = false;
        }
    }

    selectSketch(sketch: Sketch): void {
        this.selectedSketch = sketch;
    }

    onSearchChange(searchTerm: string): void {
        this.searchSubject.next(searchTerm);
    }

    clearSearch(): void {
        this.searchTerm = "";
        this.searchSubject.next("");
    }

    onWorkflowChange(workflow: "all" | "draft" | "used" | "archived"): void {
        this.currentWorkflow = workflow;
        this.pagination.offset = 0;
        this.loadSketches(0);
    }

    async changePage(page: number): Promise<void> {
        await this.loadSketches(page);
    }

    get currentPage(): number {
        return Math.floor(this.pagination.offset / this.pagination.limit);
    }

    get totalPages(): number {
        return Math.ceil(this.pagination.total / this.pagination.limit);
    }

    editSketch(): void {
        if (!this.selectedSketch) return;

        // Navigate to sketch creator with Router State (no ID in URL)
        this.router.navigate(["/song-sketch-creator"], {
            state: {
                editMode: true,
                sketchId: this.selectedSketch.id,
                searchTerm: this.searchTerm,
                targetWorkflow: this.currentWorkflow,
                sortBy: this.sortBy,
                sortDirection: this.sortDirection,
                returnPage: this.currentPage
            }
        });
    }

    confirmDeleteSketch(sketchId: string): void {
        this.deleteSketchId = sketchId;
        this.showDeleteConfirm = true;
    }

    cancelDelete(): void {
        this.showDeleteConfirm = false;
        this.deleteSketchId = null;
    }

    async deleteSketch(): Promise<void> {
        if (!this.deleteSketchId) return;

        try {
            await firstValueFrom(
                this.sketchService.deleteSketch(this.deleteSketchId)
            );

            this.notificationService.success(
                this.translate.instant("songSketch.library.messages.deleted")
            );

            // Clear selection if deleted sketch was selected
            if (this.selectedSketch?.id === this.deleteSketchId) {
                this.selectedSketch = null;
            }

            // Reload list
            await this.loadSketches(this.currentPage);
        } catch (error: any) {
            this.notificationService.error(
                this.translate.instant("songSketch.library.messages.deleteError") + ": " + error.message
            );
        } finally {
            this.cancelDelete();
        }
    }

    async archiveSketch(sketch: Sketch): Promise<void> {
        try {
            await firstValueFrom(
                this.sketchService.updateSketch(sketch.id, {
                    workflow: "archived"
                })
            );

            this.notificationService.success(
                this.translate.instant("songSketch.library.messages.archived")
            );

            // Reload list
            await this.loadSketches(this.currentPage);

            // Update selected sketch to reflect new workflow
            if (this.selectedSketch?.id === sketch.id) {
                const updatedSketch = this.sketches.find(s => s.id === sketch.id);
                if (updatedSketch) {
                    this.selectedSketch = updatedSketch;
                }
            }
        } catch (error: any) {
            this.notificationService.error(
                this.translate.instant("songSketch.library.messages.archiveError") + ": " + error.message
            );
        }
    }

    async markAsUsed(sketch: Sketch): Promise<void> {
        try {
            await firstValueFrom(
                this.sketchService.updateSketch(sketch.id, {
                    workflow: "used"
                })
            );

            this.notificationService.success(
                this.translate.instant("songSketch.library.messages.markedAsUsed")
            );

            // Reload list
            await this.loadSketches(this.currentPage);

            // Update selected sketch to reflect new workflow
            if (this.selectedSketch?.id === sketch.id) {
                const updatedSketch = this.sketches.find(s => s.id === sketch.id);
                if (updatedSketch) {
                    this.selectedSketch = updatedSketch;
                }
            }
        } catch (error: any) {
            this.notificationService.error(
                this.translate.instant("songSketch.library.messages.markAsUsedError") + ": " + error.message
            );
        }
    }

    async markAsDraft(sketch: Sketch): Promise<void> {
        try {
            await firstValueFrom(
                this.sketchService.updateSketch(sketch.id, {
                    workflow: "draft"
                })
            );

            this.notificationService.success(
                this.translate.instant("songSketch.library.messages.markedAsDraft")
            );

            // Reload list
            await this.loadSketches(this.currentPage);

            // Update selected sketch to reflect new workflow
            if (this.selectedSketch?.id === sketch.id) {
                const updatedSketch = this.sketches.find(s => s.id === sketch.id);
                if (updatedSketch) {
                    this.selectedSketch = updatedSketch;
                }
            }
        } catch (error: any) {
            this.notificationService.error(
                this.translate.instant("songSketch.library.messages.markAsDraftError") + ": " + error.message
            );
        }
    }

    async duplicateSketch(sketch: Sketch): Promise<void> {
        const confirmMessage = this.translate.instant("songSketch.library.messages.duplicateConfirm", {
            title: sketch.title || "Untitled"
        });

        if (!confirm(confirmMessage)) {
            return;
        }

        try {
            const response = await firstValueFrom(
                this.sketchService.duplicateSketch(sketch.id)
            );

            this.notificationService.success(
                this.translate.instant("songSketch.library.messages.duplicated")
            );

            // Reload list and select new sketch
            await this.loadSketches(this.currentPage);
            if (response.data?.id) {
                this.selectedSketch = this.sketches.find(s => s.id === response.data.id) || null;
            }

        } catch (error: any) {
            this.notificationService.error(
                this.translate.instant("songSketch.library.messages.duplicateError") + ": " + error.message
            );
        }
    }

    navigateToSketchCreator(): void {
        this.router.navigate(["/song-sketch-creator"], {
            state: {
                searchTerm: this.searchTerm,
                targetWorkflow: this.currentWorkflow,
                sortBy: this.sortBy,
                sortDirection: this.sortDirection,
                returnPage: this.currentPage
            }
        });
    }

    formatDate(dateString: string): string {
        const date = new Date(dateString);
        return date.toLocaleDateString() + " " + date.toLocaleTimeString([], {hour: "2-digit", minute: "2-digit"});
    }

    formatDateDetailed(dateString: string): string {
        if (!dateString) return "";
        return new Date(dateString).toLocaleDateString("de-DE", {
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit"
        });
    }

    getWorkflowLabel(workflow: string): string {
        return this.translate.instant(`songSketch.workflow.${workflow}`);
    }

    getWorkflowClass(workflow: string): string {
        const classMap: Record<string, string> = {
            draft: "badge-draft",
            used: "badge-used",
            archived: "badge-archived"
        };
        return classMap[workflow] || "badge-draft";
    }

    async copyToClipboard(text: string, fieldName: string): Promise<void> {
        if (!text || !text.trim()) {
            return;
        }

        try {
            await navigator.clipboard.writeText(text);
            this.notificationService.success(
                this.translate.instant(`songSketch.library.actions.copy${fieldName}`)
            );
        } catch (error) {
            console.error("Failed to copy to clipboard:", error);
            this.notificationService.error(
                this.translate.instant("songSketch.library.messages.copyError")
            );
        }
    }

    /**
     * Open dialog to assign sketch to a project
     */
    openAssignToProjectDialog() {
        if (!this.selectedSketch) {
            return;
        }

        const dialogRef = this.dialog.open(AssignToProjectDialogComponent, {
            width: "600px",
            maxHeight: "90vh",
            data: {
                assetType: "sketch",
                assetId: this.selectedSketch.id
            }
        });

        dialogRef.afterClosed().subscribe(async (result) => {
            if (result?.success) {
                this.notificationService.success(
                    this.translate.instant("assignToProject.success")
                );
                // Reload sketches to reflect updated project assignment
                const currentPage = Math.floor(this.pagination.offset / this.pagination.limit);
                await this.loadSketches(currentPage);
            }
        });
    }

    /**
     * Navigate to project overview with auto-selection
     */
    navigateToProject(projectId: string, event: Event): void {
        event.stopPropagation();
        this.router.navigate(["/song-projects"], {
            state: {selectedProjectId: projectId}
        });
    }

    /**
     * Unassign sketch from its project (link only, sketch remains)
     */
    async unassignFromProject(): Promise<void> {
        if (!this.selectedSketch || !this.selectedSketch.project_id) {
            return;
        }

        const confirmation = confirm(
            this.translate.instant("songSketch.library.confirmations.unassignFromProject", {
                sketch: this.selectedSketch.title || this.translate.instant("songSketch.library.untitled"),
                project: this.selectedSketch.project_name || ""
            })
        );

        if (!confirmation) {
            return;
        }

        this.isLoading = true;
        try {
            await this.sketchService.unassignFromProject(this.selectedSketch.id);

            this.notificationService.success(
                this.translate.instant("songSketch.library.messages.unassignedFromProject")
            );

            // Reload sketches to reflect updated project assignment
            await this.loadSketches(this.currentPage);

        } catch (error: any) {
            this.notificationService.error(
                this.translate.instant("songSketch.library.messages.unassignFromProjectError") + ": " + error.message
            );
        } finally {
            this.isLoading = false;
        }
    }
}
