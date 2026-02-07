import {Component, inject} from "@angular/core";
import {CommonModule} from "@angular/common";
import {MAT_DIALOG_DATA, MatDialogModule, MatDialogRef} from "@angular/material/dialog";
import {MatButtonModule} from "@angular/material/button";
import {MatListModule} from "@angular/material/list";
import {TranslateModule} from "@ngx-translate/core";

export interface ProjectSelectionData {
    imageId: string;
    projects: {
        project_id: string;
        project_name: string;
    }[];
}

@Component({
    selector: "app-select-project-dialog",
    standalone: true,
    imports: [
        CommonModule,
        MatDialogModule,
        MatButtonModule,
        MatListModule,
        TranslateModule
    ],
    templateUrl: "./select-project-dialog.component.html",
    styleUrl: "./select-project-dialog.component.scss"
})
export class SelectProjectDialogComponent {
    dialogRef = inject(MatDialogRef<SelectProjectDialogComponent>);
    data: ProjectSelectionData = inject(MAT_DIALOG_DATA);

    selectProject(projectId: string): void {
        this.dialogRef.close({selectedProjectId: projectId});
    }

    cancel(): void {
        this.dialogRef.close();
    }
}
