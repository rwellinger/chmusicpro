import {Component, inject, OnDestroy, OnInit, ViewEncapsulation} from "@angular/core";
import {CommonModule} from "@angular/common";
import {FormBuilder, FormGroup, FormsModule, ReactiveFormsModule, Validators} from "@angular/forms";
import {MatTableModule} from "@angular/material/table";
import {MatButtonModule} from "@angular/material/button";
import {MatIconModule} from "@angular/material/icon";
import {MatCardModule} from "@angular/material/card";
import {MatFormFieldModule} from "@angular/material/form-field";
import {MatInputModule} from "@angular/material/input";
import {MatSelectModule} from "@angular/material/select";
import {MatSlideToggleModule} from "@angular/material/slide-toggle";
import {MatTooltipModule} from "@angular/material/tooltip";
import {CdkDragDrop, DragDropModule, moveItemInArray} from "@angular/cdk/drag-drop";
import {TranslateModule, TranslateService} from "@ngx-translate/core";
import {Subject} from "rxjs";
import {takeUntil} from "rxjs/operators";

import {
    LyricParsingRule,
    LyricParsingRuleCreate,
    LyricParsingRuleUpdate,
    RuleType
} from "../../models/lyric-parsing-rule.model";
import {LyricParsingRuleService} from "../../services/config/lyric-parsing-rule.service";
import {NotificationService} from "../../services/ui/notification.service";

@Component({
    selector: "app-lyric-parsing-rules",
    standalone: true,
    imports: [
        CommonModule,
        ReactiveFormsModule,
        FormsModule,
        MatTableModule,
        MatButtonModule,
        MatIconModule,
        MatCardModule,
        MatFormFieldModule,
        MatInputModule,
        MatSelectModule,
        MatSlideToggleModule,
        MatTooltipModule,
        DragDropModule,
        TranslateModule
    ],
    templateUrl: "./lyric-parsing-rules.component.html",
    styleUrl: "./lyric-parsing-rules.component.scss",
    encapsulation: ViewEncapsulation.None
})
export class LyricParsingRulesComponent implements OnInit, OnDestroy {
    rules: LyricParsingRule[] = [];
    displayedColumns: string[] = ["order", "name", "type", "pattern", "replacement", "active", "actions"];

    ruleForm: FormGroup;
    isEditing = false;
    editingRuleId: number | null = null;
    isLoading = false;
    showDialog = false;

    // Live preview
    previewInput = "";
    previewOutput = "";
    previewDiffHtml = "";

    private destroy$ = new Subject<void>();
    private fb = inject(FormBuilder);
    private ruleService = inject(LyricParsingRuleService);
    private notificationService = inject(NotificationService);
    private translate = inject(TranslateService);

    constructor() {
        this.ruleForm = this.fb.group({
            name: ["", [Validators.required, Validators.maxLength(100)]],
            description: [""],
            pattern: ["", [Validators.required]],
            replacement: ["", [Validators.required]],
            rule_type: ["cleanup" as RuleType, [Validators.required]],
            active: [true],
            order: [0, [Validators.required, Validators.min(0)]]
        });
    }

    ngOnInit(): void {
        this.loadRules();
        this.setupPreviewListener();
    }

    ngOnDestroy(): void {
        this.destroy$.next();
        this.destroy$.complete();
    }

    loadRules(): void {
        this.isLoading = true;
        this.ruleService.getAllRules(undefined, undefined, true)
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: (rules) => {
                    this.rules = rules.sort((a, b) => a.order - b.order);
                    this.isLoading = false;
                },
                error: (error) => {
                    this.notificationService.error(
                        this.translate.instant("lyricParsingRules.notifications.loadError", {message: error.message})
                    );
                    this.isLoading = false;
                }
            });
    }

    openCreateDialog(): void {
        this.isEditing = false;
        this.editingRuleId = null;
        this.ruleForm.reset({
            name: "",
            description: "",
            pattern: "",
            replacement: "",
            rule_type: "cleanup",
            active: true,
            order: this.rules.length
        });
        this.showDialog = true;
    }

    openEditDialog(rule: LyricParsingRule): void {
        this.isEditing = true;
        this.editingRuleId = rule.id;
        this.ruleForm.patchValue({
            name: rule.name,
            description: rule.description || "",
            pattern: rule.pattern,
            replacement: rule.replacement,
            rule_type: rule.rule_type,
            active: rule.active,
            order: rule.order
        });
        this.showDialog = true;
    }

    closeDialog(): void {
        this.showDialog = false;
        this.ruleForm.reset();
        this.previewInput = "";
        this.previewOutput = "";
    }

    saveRule(): void {
        if (this.ruleForm.invalid) return;

        this.isLoading = true;
        const formValue = this.ruleForm.value;

        if (this.isEditing && this.editingRuleId !== null) {
            const update: LyricParsingRuleUpdate = {
                name: formValue.name,
                description: formValue.description,
                pattern: formValue.pattern,
                replacement: formValue.replacement,
                rule_type: formValue.rule_type,
                active: formValue.active,
                order: formValue.order
            };

            this.ruleService.updateRule(this.editingRuleId, update)
                .pipe(takeUntil(this.destroy$))
                .subscribe({
                    next: () => {
                        this.notificationService.success(
                            this.translate.instant("lyricParsingRules.notifications.updated")
                        );
                        this.loadRules();
                        this.closeDialog();
                        this.isLoading = false;
                    },
                    error: (error) => {
                        this.notificationService.error(
                            this.translate.instant("lyricParsingRules.notifications.saveError", {message: error.message})
                        );
                        this.isLoading = false;
                    }
                });
        } else {
            const newRule: LyricParsingRuleCreate = {
                name: formValue.name,
                description: formValue.description,
                pattern: formValue.pattern,
                replacement: formValue.replacement,
                rule_type: formValue.rule_type,
                active: formValue.active,
                order: formValue.order
            };

            this.ruleService.createRule(newRule)
                .pipe(takeUntil(this.destroy$))
                .subscribe({
                    next: () => {
                        this.notificationService.success(
                            this.translate.instant("lyricParsingRules.notifications.created")
                        );
                        this.loadRules();
                        this.closeDialog();
                        this.isLoading = false;
                    },
                    error: (error) => {
                        this.notificationService.error(
                            this.translate.instant("lyricParsingRules.notifications.saveError", {message: error.message})
                        );
                        this.isLoading = false;
                    }
                });
        }
    }

    deleteRule(rule: LyricParsingRule): void {
        const confirmed = confirm(
            this.translate.instant("lyricParsingRules.dialog.deleteConfirm")
        );

        if (!confirmed) return;

        this.isLoading = true;
        this.ruleService.deleteRule(rule.id)
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: () => {
                    this.notificationService.success(
                        this.translate.instant("lyricParsingRules.notifications.deleted")
                    );
                    this.loadRules();
                    this.isLoading = false;
                },
                error: (error) => {
                    this.notificationService.error(
                        this.translate.instant("lyricParsingRules.notifications.deleteError", {message: error.message})
                    );
                    this.isLoading = false;
                }
            });
    }

    toggleActive(rule: LyricParsingRule): void {
        const update: LyricParsingRuleUpdate = {
            active: !rule.active
        };

        this.ruleService.updateRule(rule.id, update)
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: () => {
                    rule.active = !rule.active;
                    this.notificationService.success(
                        this.translate.instant("lyricParsingRules.notifications.updated")
                    );
                },
                error: (error) => {
                    this.notificationService.error(
                        this.translate.instant("lyricParsingRules.notifications.saveError", {message: error.message})
                    );
                }
            });
    }

    onRuleDrop(event: CdkDragDrop<LyricParsingRule[]>): void {
        if (this.isLoading) return;

        // Store original order for rollback on error
        const originalRules = [...this.rules];

        moveItemInArray(this.rules, event.previousIndex, event.currentIndex);
        const ruleIds = this.rules.map(r => r.id);
        this.reorderRules(ruleIds, originalRules);
    }

    private reorderRules(ruleIds: number[], originalRules: LyricParsingRule[]): void {
        if (this.isLoading) return;

        this.isLoading = true;
        this.ruleService.reorderRules(ruleIds)
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: (reorderedRules) => {
                    this.rules = reorderedRules.sort((a, b) => a.order - b.order);
                    this.notificationService.success(
                        this.translate.instant("lyricParsingRules.notifications.reordered")
                    );
                },
                error: (error) => {
                    // Rollback to original order on error
                    this.rules = originalRules;
                    this.notificationService.error(
                        this.translate.instant("lyricParsingRules.notifications.reorderError", {message: error.message})
                    );
                },
                complete: () => {
                    this.isLoading = false;
                }
            });
    }

    setupPreviewListener(): void {
        this.ruleForm.get("pattern")?.valueChanges
            .pipe(takeUntil(this.destroy$))
            .subscribe(() => this.updatePreview());

        this.ruleForm.get("replacement")?.valueChanges
            .pipe(takeUntil(this.destroy$))
            .subscribe(() => this.updatePreview());

        this.ruleForm.get("rule_type")?.valueChanges
            .pipe(takeUntil(this.destroy$))
            .subscribe(() => this.updatePreview());
    }

    updatePreview(): void {
        if (!this.previewInput) {
            this.previewOutput = "";
            this.previewDiffHtml = "";
            return;
        }

        const pattern = this.ruleForm.get("pattern")?.value;
        const replacement = this.ruleForm.get("replacement")?.value;
        const ruleType = this.ruleForm.get("rule_type")?.value;

        if (!pattern) {
            this.previewOutput = this.previewInput;
            this.previewDiffHtml = this.makeWhitespaceVisible(this.previewInput);
            return;
        }

        try {
            const regex = new RegExp(pattern, "g");
            this.previewOutput = this.previewInput.replace(regex, replacement || "");

            // Different visualization based on rule type
            if (ruleType === "section") {
                this.previewDiffHtml = this.generateHighlight(this.previewInput, pattern);
            } else {
                this.previewDiffHtml = this.generateDiff(this.previewInput);
            }
        } catch (error) {
            const errorMsg = this.translate.instant("lyricParsingRules.errors.invalidPattern");
            this.previewOutput = errorMsg;
            this.previewDiffHtml = `<span class="diff-error">${errorMsg}</span>`;
        }
    }

    private generateHighlight(text: string, pattern: string): string {
        // Highlight matched sections (for section detection rules)
        try {
            const regex = new RegExp(pattern, "g");
            let result = "";
            let lastIndex = 0;
            let match;
            let matchCount = 0;

            // Find all matches and highlight them
            while ((match = regex.exec(text)) !== null) {
                matchCount++;
                // Add text before match (unchanged)
                if (match.index > lastIndex) {
                    result += this.makeWhitespaceVisible(text.substring(lastIndex, match.index));
                }

                // Add highlighted match
                const matchedText = match[0];
                result += `<mark class="section-highlight">${this.makeWhitespaceVisible(matchedText)}</mark>`;

                lastIndex = regex.lastIndex;
            }

            // Add remaining text
            if (lastIndex < text.length) {
                result += this.makeWhitespaceVisible(text.substring(lastIndex));
            }

            // Add match count info
            if (matchCount > 0) {
                const countMsg = matchCount === 1
                    ? `1 ${this.translate.instant("lyricParsingRules.preview.matchFound")}`
                    : `${matchCount} ${this.translate.instant("lyricParsingRules.preview.matchesFound")}`;
                result = `<div class="match-count">${countMsg}</div>` + result;
            } else {
                result = `<div class="match-count no-matches">${this.translate.instant("lyricParsingRules.preview.noMatches")}</div>` + result;
            }

            return result || this.makeWhitespaceVisible(text);
        } catch {
            return this.makeWhitespaceVisible(text);
        }
    }

    private generateDiff(original: string): string {
        // Simple character-level diff with regex match highlighting
        const pattern = this.ruleForm.get("pattern")?.value;
        const replacement = this.ruleForm.get("replacement")?.value || "";

        if (!pattern) {
            return this.makeWhitespaceVisible(original);
        }

        try {
            const regex = new RegExp(pattern, "g");
            let result = "";
            let lastIndex = 0;
            let match;

            // Find all matches and highlight them
            while ((match = regex.exec(original)) !== null) {
                // Add text before match (unchanged)
                if (match.index > lastIndex) {
                    result += this.makeWhitespaceVisible(original.substring(lastIndex, match.index));
                }

                // Add deleted text (matched part)
                const deletedText = match[0];
                if (deletedText) {
                    result += `<del class="diff-deleted">${this.makeWhitespaceVisible(deletedText)}</del>`;
                }

                // Add inserted text (replacement)
                if (replacement) {
                    result += `<ins class="diff-inserted">${this.makeWhitespaceVisible(replacement)}</ins>`;
                }

                lastIndex = regex.lastIndex;
            }

            // Add remaining text
            if (lastIndex < original.length) {
                result += this.makeWhitespaceVisible(original.substring(lastIndex));
            }

            return result || this.makeWhitespaceVisible(original);
        } catch {
            return this.makeWhitespaceVisible(original);
        }
    }

    private makeWhitespaceVisible(text: string): string {
        return text
            .replace(/ /g, "<span class=\"whitespace-dot\">·</span>")
            .replace(/\n/g, "<span class=\"whitespace-newline\">↵</span>\n")
            .replace(/\t/g, "<span class=\"whitespace-tab\">→</span>");
    }

    onPreviewInputChange(): void {
        this.updatePreview();
    }
}
