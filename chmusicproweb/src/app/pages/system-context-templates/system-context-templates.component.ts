import {Component, inject, OnDestroy, OnInit, ViewEncapsulation} from "@angular/core";
import {FormBuilder, FormGroup, ReactiveFormsModule, Validators} from "@angular/forms";
import {MatTableModule} from "@angular/material/table";
import {MatButtonModule} from "@angular/material/button";
import {MatIconModule} from "@angular/material/icon";
import {MatCardModule} from "@angular/material/card";
import {MatFormFieldModule} from "@angular/material/form-field";
import {MatInputModule} from "@angular/material/input";
import {MatSlideToggleModule} from "@angular/material/slide-toggle";
import {MatTooltipModule} from "@angular/material/tooltip";
import {TranslateModule, TranslateService} from "@ngx-translate/core";
import {Subject} from "rxjs";
import {takeUntil} from "rxjs/operators";

import {
    SystemContextTemplate,
    SystemContextTemplateCreate,
    SystemContextTemplateUpdate
} from "../../models/system-context-template.model";
import {SystemContextTemplateService} from "../../services/config/system-context-template.service";
import {NotificationService} from "../../services/ui/notification.service";

@Component({
    selector: "app-system-context-templates",
    standalone: true,
    imports: [
        ReactiveFormsModule,
        MatTableModule,
        MatButtonModule,
        MatIconModule,
        MatCardModule,
        MatFormFieldModule,
        MatInputModule,
        MatSlideToggleModule,
        MatTooltipModule,
        TranslateModule
    ],
    templateUrl: "./system-context-templates.component.html",
    styleUrl: "./system-context-templates.component.scss",
    encapsulation: ViewEncapsulation.None
})
export class SystemContextTemplatesComponent implements OnInit, OnDestroy {
    templates: SystemContextTemplate[] = [];
    displayedColumns: string[] = ["sort_order", "name", "description", "active", "actions"];

    templateForm: FormGroup;
    isEditing = false;
    editingTemplateId: string | null = null;
    isLoading = false;
    showDialog = false;

    private destroy$ = new Subject<void>();
    private fb = inject(FormBuilder);
    private templateService = inject(SystemContextTemplateService);
    private notificationService = inject(NotificationService);
    private translate = inject(TranslateService);

    constructor() {
        this.templateForm = this.fb.group({
            name: ["", [Validators.required, Validators.maxLength(100)]],
            description: [""],
            content: ["", [Validators.required]],
            sort_order: [0, [Validators.required, Validators.min(0)]],
            active: [true]
        });
    }

    ngOnInit(): void {
        this.loadTemplates();
    }

    ngOnDestroy(): void {
        this.destroy$.next();
        this.destroy$.complete();
    }

    loadTemplates(): void {
        this.isLoading = true;
        this.templateService.getAll(true)
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: (templates) => {
                    this.templates = templates.sort((a, b) => a.sort_order - b.sort_order);
                    this.isLoading = false;
                },
                error: (error) => {
                    this.notificationService.error(
                        this.translate.instant("systemContextTemplates.notifications.loadError", {message: error.message})
                    );
                    this.isLoading = false;
                }
            });
    }

    openCreateDialog(): void {
        this.isEditing = false;
        this.editingTemplateId = null;
        this.templateForm.reset({
            name: "",
            description: "",
            content: "",
            sort_order: this.templates.length,
            active: true
        });
        this.showDialog = true;
    }

    openEditDialog(template: SystemContextTemplate): void {
        this.isEditing = true;
        this.editingTemplateId = template.id;
        this.templateForm.patchValue({
            name: template.name,
            description: template.description || "",
            content: template.content,
            sort_order: template.sort_order,
            active: template.active
        });
        this.showDialog = true;
    }

    closeDialog(): void {
        this.showDialog = false;
        this.templateForm.reset();
    }

    saveTemplate(): void {
        if (this.templateForm.invalid) return;

        this.isLoading = true;
        const formValue = this.templateForm.value;

        if (this.isEditing && this.editingTemplateId !== null) {
            const update: SystemContextTemplateUpdate = {
                name: formValue.name,
                description: formValue.description,
                content: formValue.content,
                sort_order: formValue.sort_order,
                active: formValue.active
            };

            this.templateService.update(this.editingTemplateId, update)
                .pipe(takeUntil(this.destroy$))
                .subscribe({
                    next: () => {
                        this.loadTemplates();
                        this.closeDialog();
                        this.isLoading = false;
                    },
                    error: (error) => {
                        this.notificationService.error(
                            this.translate.instant("systemContextTemplates.notifications.saveError", {message: error.message})
                        );
                        this.isLoading = false;
                    }
                });
        } else {
            const newTemplate: SystemContextTemplateCreate = {
                name: formValue.name,
                description: formValue.description,
                content: formValue.content,
                sort_order: formValue.sort_order,
                active: formValue.active
            };

            this.templateService.create(newTemplate)
                .pipe(takeUntil(this.destroy$))
                .subscribe({
                    next: () => {
                        this.loadTemplates();
                        this.closeDialog();
                        this.isLoading = false;
                    },
                    error: (error) => {
                        this.notificationService.error(
                            this.translate.instant("systemContextTemplates.notifications.saveError", {message: error.message})
                        );
                        this.isLoading = false;
                    }
                });
        }
    }

    deleteTemplate(template: SystemContextTemplate): void {
        const confirmed = confirm(
            this.translate.instant("systemContextTemplates.dialog.deleteConfirm")
        );

        if (!confirmed) return;

        this.isLoading = true;
        this.templateService.delete(template.id)
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: () => {
                    this.loadTemplates();
                    this.isLoading = false;
                },
                error: (error) => {
                    this.notificationService.error(
                        this.translate.instant("systemContextTemplates.notifications.deleteError", {message: error.message})
                    );
                    this.isLoading = false;
                }
            });
    }

    toggleActive(template: SystemContextTemplate): void {
        const update: SystemContextTemplateUpdate = {
            active: !template.active
        };

        this.templateService.update(template.id, update)
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: () => {
                    template.active = !template.active;
                },
                error: (error) => {
                    this.notificationService.error(
                        this.translate.instant("systemContextTemplates.notifications.saveError", {message: error.message})
                    );
                }
            });
    }
}
