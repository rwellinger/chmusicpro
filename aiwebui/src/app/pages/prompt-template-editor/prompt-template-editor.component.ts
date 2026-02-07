import {Component, inject, OnDestroy, OnInit} from "@angular/core";
import {CommonModule} from "@angular/common";
import {FormBuilder, FormGroup, FormsModule, ReactiveFormsModule, Validators} from "@angular/forms";
import {Router} from "@angular/router";
import {Subject, takeUntil} from "rxjs";
import {TranslateModule, TranslateService} from "@ngx-translate/core";
import {MatCardModule} from "@angular/material/card";
import {MatSnackBarModule} from "@angular/material/snack-bar";
import {MatSelectModule} from "@angular/material/select";
import {MatFormFieldModule} from "@angular/material/form-field";

import {PromptTemplate, PromptTemplateUpdate} from "../../models/prompt-template.model";
import {PromptTemplateService} from "../../services/config/prompt-template.service";
import {NotificationService} from "../../services/ui/notification.service";
import {ChatService} from "../../services/config/chat.service";
import {ConversationService} from "../../services/business/conversation.service";
import {OllamaChatModel} from "../../models/conversation.model";
import {TemperatureOption, TemperatureOptionsService} from "../../services/config/temperature-options.service";

@Component({
    selector: "app-prompt-template-editor",
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        ReactiveFormsModule,
        TranslateModule,
        MatCardModule,
        MatSnackBarModule,
        MatSelectModule,
        MatFormFieldModule
    ],
    templateUrl: "./prompt-template-editor.component.html",
    styleUrl: "./prompt-template-editor.component.scss"
})
export class PromptTemplateEditorComponent implements OnInit, OnDestroy {
    // Form
    editorForm: FormGroup;

    // Template data
    originalTemplate: PromptTemplate | null = null;
    category: string = "";
    action: string = "";

    // Model data
    models: OllamaChatModel[] = [];

    // Temperature options
    temperatureOptions: TemperatureOption[] = [];

    // UI state
    isLoading = false;
    isSaving = false;
    isImprovingPre = false;
    isImprovingPost = false;
    isLoadingModels = false;

    // Navigation state (must be captured in constructor)
    private navigationState: any = null;

    // RxJS cleanup
    private destroy$ = new Subject<void>();

    private fb = inject(FormBuilder);
    private router = inject(Router);
    private promptService = inject(PromptTemplateService);
    private notificationService = inject(NotificationService);
    private translate = inject(TranslateService);
    private chatService = inject(ChatService);
    private conversationService = inject(ConversationService);
    private temperatureOptionsService = inject(TemperatureOptionsService);

    constructor() {
        // IMPORTANT: getCurrentNavigation() must be called in constructor!
        const navigation = this.router.getCurrentNavigation();
        this.navigationState = navigation?.extras?.state;

        // Initialize form
        this.editorForm = this.fb.group({
            pre_condition: ["", Validators.required],
            post_condition: ["", Validators.required],
            description: [""],
            model: [""],
            temperature: [null],
            max_tokens: [null]
        });
    }

    ngOnInit(): void {
        // Load temperature options
        this.temperatureOptions = this.temperatureOptionsService.getOptions();

        // Load models
        this.loadModels();

        // Load template from navigation state
        if (this.navigationState?.["template"]) {
            this.loadTemplate(this.navigationState["template"]);
        } else {
            // No template provided - redirect back
            this.notificationService.error(
                this.translate.instant("promptTemplateEditor.errors.noTemplate")
            );
            this.cancel();
        }
    }

    ngOnDestroy(): void {
        this.destroy$.next();
        this.destroy$.complete();
    }

    private loadModels(): void {
        this.isLoadingModels = true;
        this.conversationService
            .getChatModels()
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: (models) => {
                    this.models = models || [];
                },
                error: (error) => {
                    console.error("Error loading models:", error);
                    this.notificationService.error(
                        this.translate.instant("promptTemplateEditor.errors.modelsFailed")
                    );
                },
                complete: () => {
                    this.isLoadingModels = false;
                }
            });
    }

    private loadTemplate(template: PromptTemplate): void {
        this.originalTemplate = template;
        this.category = template.category;
        this.action = template.action;

        // Populate form
        this.editorForm.patchValue({
            pre_condition: template.pre_condition || "",
            post_condition: template.post_condition || "",
            description: template.description || "",
            model: template.model || "",
            temperature: template.temperature,
            max_tokens: template.max_tokens
        });
    }

    async save(): Promise<void> {
        if (this.editorForm.invalid || !this.originalTemplate) {
            return;
        }

        this.isSaving = true;

        try {
            // Get max_tokens value - preserve 0 and null (they mean "no limit")
            const maxTokensValue = this.editorForm.get("max_tokens")?.value;
            const maxTokens = (maxTokensValue === null || maxTokensValue === undefined || maxTokensValue === "")
                ? null
                : maxTokensValue;

            const update: PromptTemplateUpdate = {
                pre_condition: this.editorForm.get("pre_condition")?.value.trim(),
                post_condition: this.editorForm.get("post_condition")?.value.trim(),
                description: this.editorForm.get("description")?.value?.trim() || undefined,
                model: this.editorForm.get("model")?.value || undefined,
                temperature: this.editorForm.get("temperature")?.value || undefined,
                max_tokens: maxTokens
            };

            const updatedTemplate = await this.promptService.updateTemplateAsync(
                this.category,
                this.action,
                update
            );

            this.notificationService.success(
                this.translate.instant("promptTemplateEditor.notifications.saved")
            );

            // Navigate back with updated template
            this.navigateBackToPromptTemplates(updatedTemplate);
        } catch (error: any) {
            this.notificationService.error(
                this.translate.instant("promptTemplateEditor.notifications.saveError", {message: error.message})
            );
        } finally {
            this.isSaving = false;
        }
    }

    cancel(): void {
        // Navigate back without changes, re-select original template
        this.router.navigate(["/prompt-templates"], {
            state: {
                returnPage: this.navigationState?.["returnPage"] || 0,
                selectTemplate: {
                    category: this.category,
                    action: this.action
                },
                targetCategory: this.navigationState?.["targetCategory"] || "all"
            }
        });
    }

    private navigateBackToPromptTemplates(updatedTemplate: PromptTemplate): void {
        this.router.navigate(["/prompt-templates"], {
            state: {
                updatedTemplate: updatedTemplate,
                selectTemplate: {
                    category: updatedTemplate.category,
                    action: updatedTemplate.action
                },
                returnPage: this.navigationState?.["returnPage"] || 0,
                targetCategory: this.navigationState?.["targetCategory"] || "all"
            }
        });
    }

    get characterCountPre(): number {
        return this.editorForm.get("pre_condition")?.value?.length || 0;
    }

    get characterCountPost(): number {
        return this.editorForm.get("post_condition")?.value?.length || 0;
    }

    async improvePreCondition(): Promise<void> {
        const currentValue = this.editorForm.get("pre_condition")?.value;
        if (!currentValue || !currentValue.trim()) {
            return;
        }

        this.isImprovingPre = true;

        try {
            // Use ChatService with prompt_engineering/improve_condition template
            const improved = await this.chatService.validateAndCallUnified(
                "prompt_engineering",
                "improve_condition",
                currentValue
            );

            // Update form with improved prompt
            this.editorForm.patchValue({
                pre_condition: improved
            });

            this.notificationService.success(
                this.translate.instant("promptTemplateEditor.notifications.improved")
            );
        } catch (error: any) {
            this.notificationService.error(
                this.translate.instant("promptTemplateEditor.notifications.improveError", {message: error.message})
            );
        } finally {
            this.isImprovingPre = false;
        }
    }

    async improvePostCondition(): Promise<void> {
        const currentValue = this.editorForm.get("post_condition")?.value;
        if (!currentValue || !currentValue.trim()) {
            return;
        }

        this.isImprovingPost = true;

        try {
            // Use ChatService with prompt_engineering/improve_condition template
            const improved = await this.chatService.validateAndCallUnified(
                "prompt_engineering",
                "improve_condition",
                currentValue
            );

            // Update form with improved prompt
            this.editorForm.patchValue({
                post_condition: improved
            });

            this.notificationService.success(
                this.translate.instant("promptTemplateEditor.notifications.improved")
            );
        } catch (error: any) {
            this.notificationService.error(
                this.translate.instant("promptTemplateEditor.notifications.improveError", {message: error.message})
            );
        } finally {
            this.isImprovingPost = false;
        }
    }
}
