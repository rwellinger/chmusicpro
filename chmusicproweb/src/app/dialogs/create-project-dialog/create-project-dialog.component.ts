import {Component, inject, OnInit} from "@angular/core";
import {CommonModule} from "@angular/common";
import {FormBuilder, FormGroup, ReactiveFormsModule, Validators} from "@angular/forms";
import {MAT_DIALOG_DATA, MatDialogModule, MatDialogRef} from "@angular/material/dialog";
import {MatFormFieldModule} from "@angular/material/form-field";
import {MatInputModule} from "@angular/material/input";
import {MatButtonModule} from "@angular/material/button";
import {TranslateModule, TranslateService} from "@ngx-translate/core";
import {AssignedImage, AssignedSketch, AssignedSong} from "../../models/song-project.model";
import {SongService} from "../../services/business/song.service";
import {SketchService} from "../../services/business/sketch.service";
import {ImageService} from "../../services/business/image.service";
import {NotificationService} from "../../services/ui/notification.service";

export interface ProjectDialogData {
    project_id?: string;
    project_name?: string;
    description?: string;
    tags?: string[];
    // Assigned elements (only for edit mode)
    all_assigned_songs?: AssignedSong[];
    all_assigned_sketches?: AssignedSketch[];
    all_assigned_images?: AssignedImage[];
}

@Component({
    selector: "app-create-project-dialog",
    standalone: true,
    imports: [
        CommonModule,
        ReactiveFormsModule,
        MatDialogModule,
        MatFormFieldModule,
        MatInputModule,
        MatButtonModule,
        TranslateModule
    ],
    templateUrl: "./create-project-dialog.component.html",
    styleUrl: "./create-project-dialog.component.scss"
})
export class CreateProjectDialogComponent implements OnInit {
    projectForm!: FormGroup;
    isEditMode: boolean = false;
    showAdvanced: boolean = false;

    // Assigned elements (copy to allow local modifications)
    assignedSongs: AssignedSong[] = [];
    assignedSketches: AssignedSketch[] = [];
    assignedImages: AssignedImage[] = [];

    // Track unassigned items (for reporting back to parent)
    unassignedItems: { type: "song" | "sketch" | "image"; id: string }[] = [];

    private fb = inject(FormBuilder);
    private dialogRef = inject(MatDialogRef<CreateProjectDialogComponent>);
    public data = inject<ProjectDialogData | null>(MAT_DIALOG_DATA);
    private songService = inject(SongService);
    private sketchService = inject(SketchService);
    private imageService = inject(ImageService);
    private translate = inject(TranslateService);
    private notificationService = inject(NotificationService);

    constructor() {
        this.isEditMode = !!this.data;
    }

    get hasAssignments(): boolean {
        return this.assignedSongs.length > 0 ||
            this.assignedSketches.length > 0 ||
            this.assignedImages.length > 0;
    }

    get hasUnassignedItems(): boolean {
        return this.unassignedItems.length > 0;
    }

    get totalAssignments(): number {
        return this.assignedSongs.length +
            this.assignedSketches.length +
            this.assignedImages.length;
    }

    ngOnInit(): void {
        this.projectForm = this.fb.group({
            project_name: [this.data?.project_name || "", [Validators.required, Validators.maxLength(100)]],
            description: [this.data?.description || "", [Validators.maxLength(2000)]],
            tags: [this.data?.tags?.join(", ") || ""]
        });

        // Initialize assigned elements (copy to allow local modifications)
        if (this.isEditMode && this.data) {
            this.assignedSongs = [...(this.data.all_assigned_songs || [])];
            this.assignedSketches = [...(this.data.all_assigned_sketches || [])];
            this.assignedImages = [...(this.data.all_assigned_images || [])];
        }
    }

    /**
     * Get form field error message.
     */
    getFieldError(fieldName: string): string {
        const field = this.projectForm.get(fieldName);
        if (!field || !field.errors || !field.touched) {
            return "";
        }

        if (field.errors["required"]) {
            return "songProjects.validation.required";
        }
        if (field.errors["maxLength"]) {
            return `songProjects.validation.maxLength`;
        }
        return "";
    }

    /**
     * Submit form and close dialog with data.
     */
    onSubmit(): void {
        if (this.projectForm.invalid) {
            this.projectForm.markAllAsTouched();
            return;
        }

        const formValue = this.projectForm.value;

        // Convert comma-separated tags to array
        const tags = formValue.tags
            ? formValue.tags.split(",").map((tag: string) => tag.trim()).filter((tag: string) => tag.length > 0)
            : [];

        this.dialogRef.close({
            project_name: formValue.project_name.trim(),
            description: formValue.description?.trim() || undefined,
            tags: tags
        });
    }

    /**
     * Close dialog without saving.
     */
    onCancel(): void {
        this.dialogRef.close();
    }

    /**
     * Toggle Advanced panel visibility and resize dialog
     */
    toggleAdvanced(): void {
        this.showAdvanced = !this.showAdvanced;
        // Resize dialog when toggling
        this.dialogRef.updateSize(this.showAdvanced ? "850px" : "450px");
    }

    /**
     * Unassign a song from this project
     */
    async unassignSong(song: AssignedSong): Promise<void> {
        const confirmation = confirm(
            this.translate.instant("createProjectDialog.advanced.confirmUnassign", {
                type: this.translate.instant("createProjectDialog.advanced.typeSong"),
                name: song.title || "Untitled"
            })
        );

        if (!confirmation) return;

        try {
            await this.songService.unassignFromProject(song.id);
            this.assignedSongs = this.assignedSongs.filter(s => s.id !== song.id);
            this.unassignedItems.push({type: "song", id: song.id});
            this.notificationService.success(
                this.translate.instant("createProjectDialog.advanced.unassignSuccess")
            );
        } catch (error: any) {
            this.notificationService.error(
                this.translate.instant("createProjectDialog.advanced.unassignError") + ": " + error.message
            );
        }
    }

    /**
     * Unassign a sketch from this project
     */
    async unassignSketch(sketch: AssignedSketch): Promise<void> {
        const confirmation = confirm(
            this.translate.instant("createProjectDialog.advanced.confirmUnassign", {
                type: this.translate.instant("createProjectDialog.advanced.typeSketch"),
                name: sketch.title || sketch.prompt?.substring(0, 30) || "Untitled"
            })
        );

        if (!confirmation) return;

        try {
            await this.sketchService.unassignFromProject(sketch.id);
            this.assignedSketches = this.assignedSketches.filter(s => s.id !== sketch.id);
            this.unassignedItems.push({type: "sketch", id: sketch.id});
            this.notificationService.success(
                this.translate.instant("createProjectDialog.advanced.unassignSuccess")
            );
        } catch (error: any) {
            this.notificationService.error(
                this.translate.instant("createProjectDialog.advanced.unassignError") + ": " + error.message
            );
        }
    }

    /**
     * Unassign an image from this project
     */
    async unassignImage(image: AssignedImage): Promise<void> {
        if (!this.data?.project_id) return;

        const confirmation = confirm(
            this.translate.instant("createProjectDialog.advanced.confirmUnassign", {
                type: this.translate.instant("createProjectDialog.advanced.typeImage"),
                name: image.title || image.prompt?.substring(0, 30) || "Untitled"
            })
        );

        if (!confirmation) return;

        try {
            await this.imageService.unassignFromProject(image.id, this.data.project_id);
            this.assignedImages = this.assignedImages.filter(i => i.id !== image.id);
            this.unassignedItems.push({type: "image", id: image.id});
            this.notificationService.success(
                this.translate.instant("createProjectDialog.advanced.unassignSuccess")
            );
        } catch (error: any) {
            this.notificationService.error(
                this.translate.instant("createProjectDialog.advanced.unassignError") + ": " + error.message
            );
        }
    }

    /**
     * Get display title for an element
     */
    getDisplayTitle(item: AssignedSong | AssignedSketch | AssignedImage, fallbackField?: string): string {
        if (item.title && item.title.trim()) {
            return item.title.trim();
        }
        if (fallbackField && (item as any)[fallbackField]) {
            const fallback = (item as any)[fallbackField];
            return fallback.length > 40 ? fallback.substring(0, 37) + "..." : fallback;
        }
        return "Untitled";
    }
}
