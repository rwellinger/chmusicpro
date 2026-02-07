import {Component, inject, OnInit} from "@angular/core";
import {CommonModule} from "@angular/common";
import {FormsModule} from "@angular/forms";
import {MAT_DIALOG_DATA, MatDialogModule, MatDialogRef} from "@angular/material/dialog";
import {MatFormFieldModule} from "@angular/material/form-field";
import {MatSelectModule} from "@angular/material/select";
import {MatButtonModule} from "@angular/material/button";
import {TranslateModule} from "@ngx-translate/core";
import {firstValueFrom} from "rxjs";

import {SongProjectService} from "../../services/business/song-project.service";
import {SongService} from "../../services/business/song.service";
import {ImageService} from "../../services/business/image.service";
import {SketchService} from "../../services/business/sketch.service";
import {SongReleaseService} from "../../services/business/song-release.service";
import {ReleaseType} from "../../models/song-release.model";

export interface AssignToProjectDialogData {
    assetType: "image" | "song" | "sketch" | "release";
    assetId: string;
    releaseType?: ReleaseType; // For release: SINGLE or ALBUM
    currentProjectIds?: string[]; // For release: already assigned projects
}

interface ProjectListItem {
    id: string;
    project_name: string;
}

interface ProjectFolder {
    id: string;
    folder_name: string;
}

@Component({
    selector: "app-assign-to-project-dialog",
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        MatDialogModule,
        MatFormFieldModule,
        MatSelectModule,
        MatButtonModule,
        TranslateModule
    ],
    templateUrl: "./assign-to-project-dialog.component.html",
    styleUrl: "./assign-to-project-dialog.component.scss"
})
export class AssignToProjectDialogComponent implements OnInit {
    projects: ProjectListItem[] = [];
    folders: ProjectFolder[] = [];
    selectedProjectId: string | null = null;
    selectedProjectIds: string[] = []; // For release multi-select (Album)
    selectedFolderId: string | null = null;
    loading = false;
    errorMessage = "";

    // Release-specific properties
    ReleaseType = ReleaseType;
    isMultiSelect = false;

    private dialogRef = inject(MatDialogRef<AssignToProjectDialogComponent>);
    protected data = inject<AssignToProjectDialogData>(MAT_DIALOG_DATA);
    private projectService = inject(SongProjectService);
    private songService = inject(SongService);
    private imageService = inject(ImageService);
    private sketchService = inject(SketchService);
    private releaseService = inject(SongReleaseService);

    async ngOnInit(): Promise<void> {
        // Determine if multi-select is needed (Album releases)
        if (this.data.assetType === "release" && this.data.releaseType === ReleaseType.ALBUM) {
            this.isMultiSelect = true;
            // Load current project assignments for Album
            if (this.data.currentProjectIds) {
                this.selectedProjectIds = [...this.data.currentProjectIds];
            }
        }

        await this.loadProjects();
    }

    /**
     * Load all projects from backend
     */
    async loadProjects(): Promise<void> {
        this.loading = true;
        this.errorMessage = "";
        try {
            const response = await firstValueFrom(
                this.projectService.getProjects(100, 0)
            );
            this.projects = response.data || [];
        } catch (error) {
            console.error("Failed to load projects", error);
            this.errorMessage = "assignToProject.errors.loadProjectsFailed";
        } finally {
            this.loading = false;
        }
    }

    /**
     * Load folders when a project is selected
     */
    async onProjectChange(): Promise<void> {
        this.folders = [];
        this.selectedFolderId = null;

        if (!this.selectedProjectId) {
            return;
        }

        this.loading = true;
        this.errorMessage = "";
        try {
            const response = await firstValueFrom(
                this.projectService.getProjectById(this.selectedProjectId)
            );
            this.folders = response.data?.folders || [];

            // Sort folders numerically by folder_name (e.g., "01 Arrangement", "02 AI", ...)
            this.folders.sort((a, b) =>
                a.folder_name.localeCompare(b.folder_name, undefined, {numeric: true})
            );
        } catch (error) {
            console.error("Failed to load folders", error);
            this.errorMessage = "assignToProject.errors.loadFoldersFailed";
        } finally {
            this.loading = false;
        }
    }

    /**
     * Check if save button should be disabled
     */
    getSaveButtonDisabled(): boolean {
        if (this.loading) {
            return true;
        }

        // For release assets, no folder is required
        if (this.data.assetType === "release") {
            // Multi-select (Album): need at least one project
            if (this.isMultiSelect) {
                return this.selectedProjectIds.length === 0;
            }
            // Single-select: need exactly one project
            return !this.selectedProjectId;
        }

        // For non-release assets (song, image, sketch): only project is required, folder is optional
        return !this.selectedProjectId;
    }

    /**
     * Save assignment and close dialog
     */
    async save(): Promise<void> {
        // Validation for release
        if (this.data.assetType === "release") {
            // Validate project selection for release
            if (this.isMultiSelect && this.selectedProjectIds.length === 0) {
                this.errorMessage = "assignToProject.errors.noProjectSelected";
                return;
            }

            if (!this.isMultiSelect && !this.selectedProjectId) {
                this.errorMessage = "assignToProject.errors.noProjectSelected";
                return;
            }

            // Validation: Single releases can only have 1 project
            if (this.data.releaseType === ReleaseType.SINGLE && this.selectedProjectIds.length > 1) {
                this.errorMessage = "assignToProject.errors.singleOneProject";
                return;
            }
        } else {
            // For non-release assets
            if (!this.selectedProjectId) {
                return;
            }
        }

        this.loading = true;
        this.errorMessage = "";

        try {
            // Call the appropriate service based on asset type
            switch (this.data.assetType) {
                case "song":
                    await this.songService.assignToProject(
                        this.data.assetId,
                        this.selectedProjectId!,
                        this.selectedFolderId || undefined
                    );
                    break;
                case "image":
                    await this.imageService.assignToProject(
                        this.data.assetId,
                        this.selectedProjectId!,
                        this.selectedFolderId || undefined
                    );
                    break;
                case "sketch":
                    await this.sketchService.assignToProject(
                        this.data.assetId,
                        this.selectedProjectId!,
                        this.selectedFolderId || undefined
                    );
                    break;
                case "release": {
                    // For release, return selected project IDs to editor
                    const projectIds = this.isMultiSelect ? this.selectedProjectIds : [this.selectedProjectId!];
                    const projectNames = projectIds.map(id => {
                        const project = this.projects.find(p => p.id === id);
                        return project?.project_name || "";
                    }).filter(name => name);

                    this.dialogRef.close({
                        success: true,
                        projectIds: projectIds,
                        projectNames: projectNames
                    });
                    return;
                }
            }

            // Close dialog with success flag for non-release assets
            this.dialogRef.close({success: true});
        } catch (error) {
            console.error("Failed to assign asset to project", error);
            this.errorMessage = "assignToProject.errors.assignFailed";
        } finally {
            this.loading = false;
        }
    }

    /**
     * Cancel and close dialog
     */
    cancel(): void {
        this.dialogRef.close();
    }
}
