import {Component, inject} from "@angular/core";
import {CommonModule} from "@angular/common";
import {MAT_DIALOG_DATA, MatDialogModule, MatDialogRef} from "@angular/material/dialog";
import {MatButtonModule} from "@angular/material/button";
import {MatExpansionModule} from "@angular/material/expansion";
import {TranslateModule} from "@ngx-translate/core";
import {MirrorFileAction, MirrorMoveAction} from "../../models/song-project.model";

export interface MirrorPreviewDialogData {
    folderName: string;
    toUpload: string[];
    toUpdate: string[];
    toMove: MirrorMoveAction[];
    toDelete: MirrorFileAction[];
    unchanged: string[];
    totalUploadSize: number;
    ignoredCount: number;
}

@Component({
    selector: "app-mirror-preview-dialog",
    standalone: true,
    imports: [
        CommonModule,
        MatDialogModule,
        MatButtonModule,
        MatExpansionModule,
        TranslateModule
    ],
    templateUrl: "./mirror-preview-dialog.component.html",
    styleUrl: "./mirror-preview-dialog.component.scss"
})
export class MirrorPreviewDialogComponent {
    private dialogRef = inject(MatDialogRef<MirrorPreviewDialogComponent>);
    data = inject<MirrorPreviewDialogData>(MAT_DIALOG_DATA);

    readonly maxVisibleItems = 50;

    get totalChanges(): number {
        return this.data.toUpload.length + this.data.toUpdate.length +
            this.data.toMove.length + this.data.toDelete.length;
    }

    get hasDeletions(): boolean {
        return this.data.toDelete.length > 0;
    }

    formatFileSize(bytes: number): string {
        if (bytes === 0) return "0 Bytes";
        const k = 1024;
        const sizes = ["Bytes", "KB", "MB", "GB"];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
    }

    confirm(): void {
        this.dialogRef.close(true);
    }

    cancel(): void {
        this.dialogRef.close(false);
    }
}
