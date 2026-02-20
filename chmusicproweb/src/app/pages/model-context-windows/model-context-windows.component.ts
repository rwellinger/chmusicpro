import {DecimalPipe, TitleCasePipe} from "@angular/common";
import {Component, inject, OnDestroy, OnInit, ViewEncapsulation} from "@angular/core";
import {FormBuilder, FormGroup, ReactiveFormsModule, Validators} from "@angular/forms";
import {MatTableModule} from "@angular/material/table";
import {MatButtonModule} from "@angular/material/button";
import {MatIconModule} from "@angular/material/icon";
import {MatCardModule} from "@angular/material/card";
import {MatFormFieldModule} from "@angular/material/form-field";
import {MatInputModule} from "@angular/material/input";
import {MatSelectModule} from "@angular/material/select";
import {MatTooltipModule} from "@angular/material/tooltip";
import {TranslateModule, TranslateService} from "@ngx-translate/core";
import {Subject} from "rxjs";
import {takeUntil} from "rxjs/operators";

import {ModelContextWindow, ModelContextWindowCreate, ModelContextWindowUpdate} from "../../models/model-context-window.model";
import {ModelContextWindowService} from "../../services/business/model-context-window.service";
import {NotificationService} from "../../services/ui/notification.service";

@Component({
    selector: "app-model-context-windows",
    standalone: true,
    imports: [
        DecimalPipe,
        TitleCasePipe,
        ReactiveFormsModule,
        MatTableModule,
        MatButtonModule,
        MatIconModule,
        MatCardModule,
        MatFormFieldModule,
        MatInputModule,
        MatSelectModule,
        MatTooltipModule,
        TranslateModule
    ],
    templateUrl: "./model-context-windows.component.html",
    styleUrl: "./model-context-windows.component.scss",
    encapsulation: ViewEncapsulation.None
})
export class ModelContextWindowsComponent implements OnInit, OnDestroy {
    entries: ModelContextWindow[] = [];
    filteredEntries: ModelContextWindow[] = [];
    displayedColumns = ["model_name", "provider", "context_window", "description", "actions"];
    providers = ["ollama", "openai", "claude"];
    activeFilter = "all";

    // Dialog state
    showDialog = false;
    isEditing = false;
    editingId: number | null = null;
    entryForm!: FormGroup;

    // Loading
    isLoading = false;

    private destroy$ = new Subject<void>();
    private service = inject(ModelContextWindowService);
    private notification = inject(NotificationService);
    private translate = inject(TranslateService);
    private fb = inject(FormBuilder);

    ngOnInit(): void {
        this.initForm();
        this.loadEntries();
    }

    ngOnDestroy(): void {
        this.destroy$.next();
        this.destroy$.complete();
    }

    private initForm(): void {
        this.entryForm = this.fb.group({
            model_name: ["", [Validators.required, Validators.maxLength(100)]],
            context_window: [null, [Validators.required, Validators.min(1)]],
            provider: ["ollama", Validators.required],
            description: [""]
        });
    }

    loadEntries(): void {
        this.isLoading = true;
        this.service.list()
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: (response) => {
                    this.entries = response.items;
                    this.applyFilter();
                    this.isLoading = false;
                },
                error: () => {
                    this.notification.error(this.translate.instant("modelContext.loadError"));
                    this.isLoading = false;
                }
            });
    }

    applyFilter(): void {
        if (this.activeFilter === "all") {
            this.filteredEntries = [...this.entries];
        } else {
            this.filteredEntries = this.entries.filter(e => e.provider === this.activeFilter);
        }
    }

    onFilterChange(filter: string): void {
        this.activeFilter = filter;
        this.applyFilter();
    }

    openAddDialog(): void {
        this.isEditing = false;
        this.editingId = null;
        this.entryForm.reset({provider: "ollama"});
        this.showDialog = true;
    }

    openEditDialog(entry: ModelContextWindow): void {
        this.isEditing = true;
        this.editingId = entry.id;
        this.entryForm.patchValue({
            model_name: entry.model_name,
            context_window: entry.context_window,
            provider: entry.provider,
            description: entry.description || ""
        });
        this.showDialog = true;
    }

    closeDialog(): void {
        this.showDialog = false;
        this.entryForm.reset({provider: "ollama"});
    }

    saveEntry(): void {
        if (this.entryForm.invalid) return;

        const formValue = this.entryForm.value;

        if (this.isEditing && this.editingId !== null) {
            const updateData: ModelContextWindowUpdate = {
                model_name: formValue.model_name,
                context_window: formValue.context_window,
                provider: formValue.provider,
                description: formValue.description || undefined
            };
            this.service.update(this.editingId, updateData)
                .pipe(takeUntil(this.destroy$))
                .subscribe({
                    next: () => {
                        this.notification.success(this.translate.instant("modelContext.saved"));
                        this.closeDialog();
                        this.loadEntries();
                    },
                    error: (err) => {
                        const msg = err.error?.error || this.translate.instant("modelContext.saveError");
                        this.notification.error(msg);
                    }
                });
        } else {
            const createData: ModelContextWindowCreate = {
                model_name: formValue.model_name,
                context_window: formValue.context_window,
                provider: formValue.provider,
                description: formValue.description || undefined
            };
            this.service.create(createData)
                .pipe(takeUntil(this.destroy$))
                .subscribe({
                    next: () => {
                        this.notification.success(this.translate.instant("modelContext.saved"));
                        this.closeDialog();
                        this.loadEntries();
                    },
                    error: (err) => {
                        const msg = err.error?.error || this.translate.instant("modelContext.saveError");
                        this.notification.error(msg);
                    }
                });
        }
    }

    deleteEntry(entry: ModelContextWindow): void {
        const confirmed = confirm(this.translate.instant("modelContext.deleteConfirm"));
        if (!confirmed) return;

        this.service.delete(entry.id)
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: () => {
                    this.notification.success(this.translate.instant("modelContext.deleted"));
                    this.loadEntries();
                },
                error: () => {
                    this.notification.error(this.translate.instant("modelContext.deleteError"));
                }
            });
    }

    formatTokens(tokens: number): string {
        if (tokens >= 1000) {
            return `${(tokens / 1000).toFixed(0)}k`;
        }
        return tokens.toString();
    }

    onDialogBackdropClick(event: MouseEvent): void {
        if ((event.target as HTMLElement).classList.contains("dialog-overlay")) {
            this.closeDialog();
        }
    }
}
