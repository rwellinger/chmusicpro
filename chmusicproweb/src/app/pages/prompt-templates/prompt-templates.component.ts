import {Component, ElementRef, inject, OnDestroy, OnInit, ViewChild} from "@angular/core";
import {CommonModule} from "@angular/common";
import {FormsModule} from "@angular/forms";
import {Router} from "@angular/router";
import {debounceTime, distinctUntilChanged, Subject, takeUntil} from "rxjs";
import {PromptTemplate} from "../../models/prompt-template.model";
import {PromptTemplateService} from "../../services/config/prompt-template.service";
import {NotificationService} from "../../services/ui/notification.service";
import {UserSettingsService} from "../../services/user-settings.service";
import {TemperatureOptionsService} from "../../services/config/temperature-options.service";
import {MatSnackBarModule} from "@angular/material/snack-bar";
import {MatCardModule} from "@angular/material/card";
import {MatButtonModule} from "@angular/material/button";
import {TranslateModule, TranslateService} from "@ngx-translate/core";

@Component({
    selector: "app-prompt-templates",
    standalone: true,
    imports: [CommonModule, FormsModule, MatSnackBarModule, MatCardModule, MatButtonModule, TranslateModule],
    templateUrl: "./prompt-templates.component.html",
    styleUrl: "./prompt-templates.component.scss"
})
export class PromptTemplatesComponent implements OnInit, OnDestroy {
    // Template data
    templates: PromptTemplate[] = [];
    filteredTemplates: PromptTemplate[] = [];
    paginatedTemplates: PromptTemplate[] = [];
    selectedTemplate: PromptTemplate | null = null;

    // Pagination
    pagination = {
        total: 0,
        limit: 8, // Will be overridden by user settings
        offset: 0
    };

    // UI state
    isLoading = false;
    loadingMessage = "";

    // Search functionality
    searchTerm: string = "";
    private searchSubject = new Subject<string>();
    private destroy$ = new Subject<void>();

    // Category filter
    currentCategory: "all" | "lyrics" | "image" | "music" | "titel" | "description" | "other" = "all";
    private knownCategories = ["lyrics", "image", "music", "titel", "description"];

    // Navigation state (must be captured in constructor)
    private navigationState: any = null;

    // Make Math available in template
    Math = Math;

    @ViewChild("searchInput") searchInput!: ElementRef;

    private promptService = inject(PromptTemplateService);
    private notificationService = inject(NotificationService);
    private settingsService = inject(UserSettingsService);
    private translate = inject(TranslateService);
    private router = inject(Router);
    private temperatureOptionsService = inject(TemperatureOptionsService);

    constructor() {
        // IMPORTANT: getCurrentNavigation() must be called in constructor!
        const navigation = this.router.getCurrentNavigation();
        this.navigationState = navigation?.extras?.state;

        // Setup search debouncing
        this.searchSubject.pipe(
            debounceTime(300),
            distinctUntilChanged(),
            takeUntil(this.destroy$)
        ).subscribe(searchTerm => {
            this.searchTerm = searchTerm;
            this.applyFilter();
            // Maintain focus on search input
            if (document.activeElement === this.searchInput?.nativeElement) {
                setTimeout(() => this.searchInput.nativeElement.focus(), 0);
            }
        });
    }

    ngOnInit(): void {
        this.loadUserSettings();
    }

    private loadUserSettings(): void {
        this.settingsService.getSettings()
            .pipe(takeUntil(this.destroy$))
            .subscribe(settings => {
                this.pagination.limit = settings.promptListLimit;
                this.loadTemplates();
            });
    }

    ngOnDestroy(): void {
        this.destroy$.next();
        this.destroy$.complete();
    }

    async loadTemplates(): Promise<void> {
        this.isLoading = true;
        this.loadingMessage = this.translate.instant("promptTemplates.notifications.loading");

        try {
            this.templates = await this.promptService.getAllTemplates().toPromise() || [];

            // Check if returning from editor with navigation state
            const savedSearchTerm = this.navigationState?.["searchTerm"];
            const returnPage = this.navigationState?.["returnPage"];
            const selectTemplate = this.navigationState?.["selectTemplate"];
            const targetCategory = this.navigationState?.["targetCategory"];

            // Restore search term
            if (savedSearchTerm !== undefined) {
                this.searchTerm = savedSearchTerm;
            }

            // Set category filter BEFORE applying filter (for returning from editor)
            if (targetCategory && ["all", "lyrics", "image", "music", "titel", "description", "other"].includes(targetCategory)) {
                this.currentCategory = targetCategory;
            }

            this.applyFilter();

            // Navigate to return page if specified
            if (returnPage !== undefined && returnPage !== null) {
                this.goToPage(returnPage);
            }

            // Try to select template if specified
            if (selectTemplate) {
                const template = this.paginatedTemplates.find(t =>
                    t.category === selectTemplate.category &&
                    t.action === selectTemplate.action
                );
                if (template) {
                    this.selectTemplate(template);
                } else {
                    // Template not on current page, search in filtered list
                    const templateInFiltered = this.filteredTemplates.find(t =>
                        t.category === selectTemplate.category &&
                        t.action === selectTemplate.action
                    );
                    if (templateInFiltered) {
                        // Find page index and navigate there
                        const templateIndex = this.filteredTemplates.indexOf(templateInFiltered);
                        const targetPage = Math.floor(templateIndex / this.pagination.limit);
                        this.goToPage(targetPage);
                        this.selectTemplate(templateInFiltered);
                    } else {
                        // Template not in current filter, notify user
                        this.notificationService.info(
                            this.translate.instant("promptTemplates.notifications.templateSaved")
                        );
                    }
                }
            } else if (this.filteredTemplates.length > 0 && !this.selectedTemplate) {
                // Auto-select first template if available and none selected
                this.selectTemplate(this.filteredTemplates[0]);
            }
        } catch (error: any) {
            this.notificationService.error(this.translate.instant("promptTemplates.notifications.loadError", {message: error.message}));
            this.templates = [];
            this.filteredTemplates = [];
        } finally {
            this.isLoading = false;
        }
    }

    applyFilter(): void {
        // Step 1: Filter by category
        let categoryFiltered: PromptTemplate[];
        if (this.currentCategory === "all") {
            categoryFiltered = [...this.templates];
        } else if (this.currentCategory === "other") {
            // "Other" = categories NOT in knownCategories
            categoryFiltered = this.templates.filter(template =>
                !this.knownCategories.includes(template.category.toLowerCase())
            );
        } else {
            // Specific category filter
            categoryFiltered = this.templates.filter(template =>
                template.category.toLowerCase() === this.currentCategory
            );
        }

        // Step 2: Filter by search term
        if (!this.searchTerm.trim()) {
            this.filteredTemplates = categoryFiltered;
        } else {
            const term = this.searchTerm.toLowerCase();
            this.filteredTemplates = categoryFiltered.filter(template =>
                template.category.toLowerCase().includes(term) ||
                template.action.toLowerCase().includes(term)
            );
        }

        // Update pagination after filtering
        this.pagination.total = this.filteredTemplates.length;
        this.pagination.offset = 0; // Reset to first page
        this.updatePaginatedTemplates();
    }

    onCategoryChange(category: "all" | "lyrics" | "image" | "music" | "titel" | "description" | "other"): void {
        this.currentCategory = category;
        this.selectedTemplate = null; // Clear selection when changing category
        this.applyFilter();
    }

    private updatePaginatedTemplates(): void {
        const start = this.pagination.offset;
        const end = start + this.pagination.limit;
        this.paginatedTemplates = this.filteredTemplates.slice(start, end);

        // Auto-select first template if available and none selected
        if (this.paginatedTemplates.length > 0 && !this.selectedTemplate) {
            this.selectTemplate(this.paginatedTemplates[0]);
        } else if (this.paginatedTemplates.length === 0) {
            this.selectedTemplate = null;
        }
    }

    onSearchChange(event: Event): void {
        const value = (event.target as HTMLInputElement).value;
        this.searchSubject.next(value);
    }

    clearSearch(): void {
        this.searchTerm = "";
        this.searchSubject.next("");
    }

    selectTemplate(template: PromptTemplate): void {
        this.selectedTemplate = template;
    }

    getTemplateDisplayName(template: PromptTemplate): string {
        return `${template.category} / ${template.action}`;
    }

    formatDate(dateString: string): string {
        try {
            return new Date(dateString).toLocaleDateString("de-CH", {
                day: "2-digit",
                month: "2-digit",
                year: "numeric",
                hour: "2-digit",
                minute: "2-digit"
            });
        } catch {
            return dateString;
        }
    }

    trackByTemplate(index: number, template: PromptTemplate): string {
        return `${template.category}-${template.action}`;
    }

    getTokensToWordsHint(tokens: number | null | undefined): string {
        if (!tokens || tokens === null || tokens === undefined) return "";
        // Rough estimation: 1 token ≈ 0.75 words
        const words = Math.round(tokens * 0.75);
        return this.translate.instant("promptTemplates.detail.tokensHint", {words});
    }

    getTemperatureLabel(temperature: number | null | undefined): string {
        const label = this.temperatureOptionsService.getLabel(
            temperature,
            (key: string) => this.translate.instant(key)
        );
        return label || (temperature !== null && temperature !== undefined ? temperature.toString() : "");
    }

    // Pagination methods
    getVisiblePages(): (number | string)[] {
        const totalPages = Math.ceil(this.pagination.total / this.pagination.limit);
        const current = Math.floor(this.pagination.offset / this.pagination.limit) + 1;
        const pages: (number | string)[] = [];

        if (totalPages <= 7) {
            // Show all pages if 7 or less
            for (let i = 1; i <= totalPages; i++) {
                pages.push(i);
            }
        } else {
            // Smart pagination with ellipsis
            if (current <= 4) {
                // Show: 1 2 3 4 5 ... last
                for (let i = 1; i <= 5; i++) pages.push(i);
                pages.push("...");
                pages.push(totalPages);
            } else if (current >= totalPages - 3) {
                // Show: 1 ... n-4 n-3 n-2 n-1 n
                pages.push(1);
                pages.push("...");
                for (let i = totalPages - 4; i <= totalPages; i++) pages.push(i);
            } else {
                // Show: 1 ... current-1 current current+1 ... last
                pages.push(1);
                pages.push("...");
                for (let i = current - 1; i <= current + 1; i++) pages.push(i);
                pages.push("...");
                pages.push(totalPages);
            }
        }

        return pages;
    }

    goToPage(pageIndex: number): void {
        const totalPages = Math.ceil(this.pagination.total / this.pagination.limit);
        if (pageIndex >= 0 && pageIndex < totalPages) {
            this.pagination.offset = pageIndex * this.pagination.limit;
            this.updatePaginatedTemplates();
        }
    }

    nextPage(): void {
        const totalPages = Math.ceil(this.pagination.total / this.pagination.limit);
        const currentPage = Math.floor(this.pagination.offset / this.pagination.limit);
        if (currentPage < totalPages - 1) {
            this.goToPage(currentPage + 1);
        }
    }

    previousPage(): void {
        const currentPage = Math.floor(this.pagination.offset / this.pagination.limit);
        if (currentPage > 0) {
            this.goToPage(currentPage - 1);
        }
    }

    trackByPage(index: number, page: number | string): number | string {
        return page;
    }

    openAdvancedEditor(): void {
        if (!this.selectedTemplate) return;

        const currentPage = Math.floor(this.pagination.offset / this.pagination.limit);

        this.router.navigate(["/prompt-template-editor"], {
            state: {
                template: this.selectedTemplate,
                category: this.selectedTemplate.category,
                action: this.selectedTemplate.action,
                searchTerm: this.searchTerm,
                returnPage: currentPage,
                targetCategory: this.currentCategory
            }
        });
    }
}
