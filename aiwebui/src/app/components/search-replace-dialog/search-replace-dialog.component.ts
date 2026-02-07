import {Component, inject, OnInit} from "@angular/core";
import {CommonModule} from "@angular/common";
import {FormBuilder, FormGroup, ReactiveFormsModule, Validators} from "@angular/forms";
import {MatDialogModule, MatDialogRef} from "@angular/material/dialog";
import {MatButtonModule} from "@angular/material/button";
import {MatFormFieldModule} from "@angular/material/form-field";
import {MatInputModule} from "@angular/material/input";
import {TranslateModule} from "@ngx-translate/core";

export interface SearchReplaceDialogData {
    searchText: string;
    replaceText: string;
}

@Component({
    selector: "app-search-replace-dialog",
    standalone: true,
    imports: [
        CommonModule,
        ReactiveFormsModule,
        TranslateModule,
        MatDialogModule,
        MatButtonModule,
        MatFormFieldModule,
        MatInputModule
    ],
    templateUrl: "./search-replace-dialog.component.html",
    styleUrl: "./search-replace-dialog.component.scss"
})
export class SearchReplaceDialogComponent implements OnInit {
    searchReplaceForm!: FormGroup;
    matchCount = 0;

    private fb = inject(FormBuilder);
    private dialogRef = inject(MatDialogRef<SearchReplaceDialogComponent>);

    ngOnInit(): void {
        this.searchReplaceForm = this.fb.group({
            searchText: ["", [Validators.required]],
            replaceText: [""]
        });

        // Live preview: Update match count when search text changes
        this.searchReplaceForm.get("searchText")?.valueChanges.subscribe(() => {
            this.updateMatchCount();
        });
    }

    private updateMatchCount(): void {
        const searchText = this.searchReplaceForm.get("searchText")?.value || "";
        if (!searchText.trim()) {
            this.matchCount = 0;
            return;
        }

        // Get lyrics from dialog data if available
        // For now, we just show 0 - the actual count will be calculated in the parent component
        this.matchCount = 0;
    }

    apply(): void {
        if (this.searchReplaceForm.valid) {
            const result: SearchReplaceDialogData = {
                searchText: this.searchReplaceForm.get("searchText")?.value || "",
                replaceText: this.searchReplaceForm.get("replaceText")?.value || ""
            };
            this.dialogRef.close(result);
        }
    }

    cancel(): void {
        this.dialogRef.close();
    }
}
