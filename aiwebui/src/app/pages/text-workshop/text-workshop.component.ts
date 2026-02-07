import {Component, inject, OnDestroy, OnInit, SecurityContext, ViewEncapsulation} from "@angular/core";
import {FormBuilder, FormGroup, FormsModule, ReactiveFormsModule, Validators} from "@angular/forms";
import {CommonModule} from "@angular/common";
import {ActivatedRoute, Router} from "@angular/router";
import {DomSanitizer} from "@angular/platform-browser";
import {TranslateModule, TranslateService} from "@ngx-translate/core";
import {MatCardModule} from "@angular/material/card";
import {MatExpansionModule} from "@angular/material/expansion";
import {debounceTime, firstValueFrom, Subject, takeUntil} from "rxjs";
import {marked} from "marked";

import {MatDialog, MatDialogModule} from "@angular/material/dialog";
import {WorkshopService} from "../../services/business/workshop.service";
import {NotificationService} from "../../services/ui/notification.service";
import {ChatService} from "../../services/config/chat.service";
import {LyricArchitectModalComponent} from "../../components/lyric-architect-modal/lyric-architect-modal.component";
import {LyricArchitectureService} from "../../services/lyric-architecture.service";
import {Workshop, WorkshopPhase} from "../../models/workshop.model";

interface SelectableItem {
    id: number;
    heading: string;
    content: string;
    selected: boolean;
}

@Component({
    selector: "app-text-workshop",
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        ReactiveFormsModule,
        MatCardModule,
        MatDialogModule,
        MatExpansionModule,
        TranslateModule
    ],
    templateUrl: "./text-workshop.component.html",
    styleUrl: "./text-workshop.component.scss",
    encapsulation: ViewEncapsulation.None
})
export class TextWorkshopComponent implements OnInit, OnDestroy {
    // Mode
    isEditorMode = false;
    currentWorkshopId: string | null = null;

    // Editor form
    workshopForm!: FormGroup;
    currentPhase: WorkshopPhase = "connect";
    saveStatus: "idle" | "saving" | "saved" = "idle";
    private saveStatusTimer: ReturnType<typeof setTimeout> | null = null;

    // Draft language
    draftLanguage = "EN";
    draftLanguages = ["EN", "DE", "FR", "IT", "ES"];

    // AI loading states
    isGeneratingTitle = false;
    isGeneratingInspirations = false;
    isGeneratingMindmap = false;
    isGeneratingStories = false;
    isGeneratingWords = false;
    isGeneratingRhymes = false;
    isGeneratingDraft = false;
    isExporting = false;

    // Preview mode
    isPreviewMode = false;

    // Selection mode
    isSelectingInspirations = false;
    inspirationItems: SelectableItem[] = [];
    isSelectingStories = false;
    storyItems: SelectableItem[] = [];

    // Library
    workshops: Workshop[] = [];
    totalWorkshops = 0;
    currentPage = 0;
    pageSize = 20;
    searchTerm = "";
    isLoading = false;

    private destroy$ = new Subject<void>();
    private fb = inject(FormBuilder);
    private router = inject(Router);
    private route = inject(ActivatedRoute);
    private workshopService = inject(WorkshopService);
    private notificationService = inject(NotificationService);
    private translate = inject(TranslateService);
    private chatService = inject(ChatService);
    private dialog = inject(MatDialog);
    private architectureService = inject(LyricArchitectureService);
    private sanitizer = inject(DomSanitizer);

    ngOnInit(): void {
        this.initForm();

        this.route.params.pipe(takeUntil(this.destroy$)).subscribe(params => {
            if (params["id"]) {
                this.currentWorkshopId = params["id"];
                this.isEditorMode = true;
                this.loadWorkshop(params["id"]);
            } else {
                this.isEditorMode = false;
                this.loadWorkshops();
            }
        });
    }

    ngOnDestroy(): void {
        this.destroy$.next();
        this.destroy$.complete();
    }

    private initForm(): void {
        this.workshopForm = this.fb.group({
            title: ["", [Validators.required, Validators.maxLength(200)]],
            connect_topic: [""],
            connect_inspirations: [""],
            collect_mindmap: [""],
            collect_stories: [""],
            collect_words: [""],
            shape_structure: [""],
            shape_rhymes: [""],
            shape_draft: [""]
        });
    }

    // --- Library Mode ---

    loadWorkshops(): void {
        this.isLoading = true;
        this.workshopService.getWorkshops(this.pageSize, this.currentPage * this.pageSize, this.searchTerm)
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: (response) => {
                    this.workshops = response.data;
                    this.totalWorkshops = response.pagination.total;
                    this.isLoading = false;
                },
                error: () => {
                    this.notificationService.error(this.translate.instant("workshop.errors.loadFailed"));
                    this.isLoading = false;
                }
            });
    }

    onSearch(event: Event): void {
        this.searchTerm = (event.target as HTMLInputElement).value;
        this.currentPage = 0;
        this.loadWorkshops();
    }

    onPageChange(direction: number): void {
        this.currentPage += direction;
        this.loadWorkshops();
    }

    get hasNextPage(): boolean {
        return (this.currentPage + 1) * this.pageSize < this.totalWorkshops;
    }

    get hasPreviousPage(): boolean {
        return this.currentPage > 0;
    }

    openWorkshop(workshop: Workshop): void {
        this.router.navigate(["/text-workshop", workshop.id]);
    }

    async createNewWorkshop(): Promise<void> {
        try {
            const response = await firstValueFrom(
                this.workshopService.createWorkshop({title: this.translate.instant("workshop.newWorkshopTitle")})
            );
            this.router.navigate(["/text-workshop", response.data.id]);
        } catch {
            this.notificationService.error(this.translate.instant("workshop.errors.createFailed"));
        }
    }

    async deleteWorkshop(event: Event, workshop: Workshop): Promise<void> {
        event.stopPropagation();
        const confirmed = confirm(this.translate.instant("workshop.confirmDelete"));
        if (!confirmed) return;

        try {
            await firstValueFrom(this.workshopService.deleteWorkshop(workshop.id));
            this.notificationService.success(this.translate.instant("workshop.deleteSuccess"));
            this.loadWorkshops();
        } catch {
            this.notificationService.error(this.translate.instant("workshop.errors.deleteFailed"));
        }
    }

    // --- Editor Mode ---

    private async loadWorkshop(id: string): Promise<void> {
        try {
            const response = await firstValueFrom(this.workshopService.getWorkshopById(id));
            const workshop = response.data;
            this.currentPhase = workshop.current_phase;
            this.draftLanguage = workshop.draft_language || "EN";
            this.workshopForm.patchValue({
                title: workshop.title,
                connect_topic: workshop.connect_topic || "",
                connect_inspirations: workshop.connect_inspirations || "",
                collect_mindmap: workshop.collect_mindmap || "",
                collect_stories: workshop.collect_stories || "",
                collect_words: workshop.collect_words || "",
                shape_structure: workshop.shape_structure || "",
                shape_rhymes: workshop.shape_rhymes || "",
                shape_draft: workshop.shape_draft || ""
            }, {emitEvent: false});
            this.setupAutoSave();
        } catch {
            this.notificationService.error(this.translate.instant("workshop.errors.loadFailed"));
            this.router.navigate(["/text-workshop"]);
        }
    }

    private setupAutoSave(): void {
        this.workshopForm.valueChanges.pipe(
            debounceTime(2000),
            takeUntil(this.destroy$)
        ).subscribe(() => this.autoSave());
    }

    private async autoSave(): Promise<void> {
        if (!this.currentWorkshopId || this.saveStatus === "saving") return;
        const title = this.workshopForm.get("title")?.value;
        if (!title?.trim()) return;
        this.saveStatus = "saving";

        try {
            const formData = this.workshopForm.value;
            formData.current_phase = this.currentPhase;
            formData.draft_language = this.draftLanguage;
            await firstValueFrom(this.workshopService.updateWorkshop(this.currentWorkshopId, formData));
            this.saveStatus = "saved";
            if (this.saveStatusTimer) clearTimeout(this.saveStatusTimer);
            this.saveStatusTimer = setTimeout(() => this.saveStatus = "idle", 3000);
        } catch {
            this.saveStatus = "idle";
            this.notificationService.error(this.translate.instant("workshop.errors.saveFailed"));
        }
    }

    async saveWorkshop(): Promise<void> {
        if (!this.currentWorkshopId || this.saveStatus === "saving") return;
        await this.autoSave();
    }

    backToLibrary(): void {
        this.router.navigate(["/text-workshop"]);
    }

    getPhaseLabel(phase: WorkshopPhase): string {
        return this.translate.instant(`workshop.phases.${phase}`);
    }

    // --- AI Generation Methods ---

    async generateTitle(): Promise<void> {
        const inspirations = this.workshopForm.get("connect_inspirations")?.value;
        const existingTitle = this.workshopForm.get("title")?.value;
        const input = inspirations?.trim() || existingTitle?.trim();

        if (!input) {
            this.notificationService.error(this.translate.instant("workshop.errors.inspirationsRequired"));
            return;
        }

        this.isGeneratingTitle = true;
        try {
            const result = await this.chatService.generateTitle(input);
            this.workshopForm.patchValue({title: result.trim()});
            await this.autoSave();
            this.notificationService.success(this.translate.instant("workshop.aiSuccess"));
        } catch {
            this.notificationService.error(this.translate.instant("workshop.errors.aiFailed"));
        } finally {
            this.isGeneratingTitle = false;
        }
    }

    async generateInspirations(): Promise<void> {
        const topic = this.workshopForm.get("connect_topic")?.value;
        if (!topic?.trim()) {
            this.notificationService.error(this.translate.instant("workshop.errors.topicRequired"));
            return;
        }

        this.isGeneratingInspirations = true;
        try {
            const result = await this.chatService.generateInspirations(topic);
            const items = this.parseMarkdownItems(result);
            if (items.length > 0) {
                this.inspirationItems = items;
                this.isSelectingInspirations = true;
            } else {
                this.workshopForm.patchValue({connect_inspirations: result});
                this.currentPhase = "connect";
                await this.autoSave();
            }
            this.notificationService.success(this.translate.instant("workshop.aiSuccess"));
        } catch {
            this.notificationService.error(this.translate.instant("workshop.errors.aiFailed"));
        } finally {
            this.isGeneratingInspirations = false;
        }
    }

    async generateMindmap(): Promise<void> {
        const topic = this.workshopForm.get("connect_topic")?.value;
        if (!topic?.trim()) {
            this.notificationService.error(this.translate.instant("workshop.errors.topicRequired"));
            return;
        }

        this.isGeneratingMindmap = true;
        try {
            const inspirations = this.workshopForm.get("connect_inspirations")?.value;
            const result = await this.chatService.generateMindmap(topic, inspirations);
            this.workshopForm.patchValue({collect_mindmap: result});
            this.currentPhase = "collect";
            await this.autoSave();
            this.notificationService.success(this.translate.instant("workshop.aiSuccess"));
        } catch {
            this.notificationService.error(this.translate.instant("workshop.errors.aiFailed"));
        } finally {
            this.isGeneratingMindmap = false;
        }
    }

    async generateStories(): Promise<void> {
        const topic = this.workshopForm.get("connect_topic")?.value;
        if (!topic?.trim()) {
            this.notificationService.error(this.translate.instant("workshop.errors.topicRequired"));
            return;
        }

        this.isGeneratingStories = true;
        try {
            const context = [
                this.workshopForm.get("connect_inspirations")?.value,
                this.workshopForm.get("collect_mindmap")?.value
            ].filter(Boolean).join("\n\n");
            const result = await this.chatService.generateStories(topic, context || undefined);
            const items = this.parseMarkdownItems(result);
            if (items.length > 0) {
                this.storyItems = items;
                this.isSelectingStories = true;
            } else {
                this.workshopForm.patchValue({collect_stories: result});
                this.currentPhase = "collect";
                await this.autoSave();
            }
            this.notificationService.success(this.translate.instant("workshop.aiSuccess"));
        } catch {
            this.notificationService.error(this.translate.instant("workshop.errors.aiFailed"));
        } finally {
            this.isGeneratingStories = false;
        }
    }

    async generateWords(): Promise<void> {
        const topic = this.workshopForm.get("connect_topic")?.value;
        if (!topic?.trim()) {
            this.notificationService.error(this.translate.instant("workshop.errors.topicRequired"));
            return;
        }

        this.isGeneratingWords = true;
        try {
            const result = await this.chatService.generateWordLibrary(topic);
            this.workshopForm.patchValue({collect_words: result});
            this.currentPhase = "collect";
            await this.autoSave();
            this.notificationService.success(this.translate.instant("workshop.aiSuccess"));
        } catch {
            this.notificationService.error(this.translate.instant("workshop.errors.aiFailed"));
        } finally {
            this.isGeneratingWords = false;
        }
    }

    async generateRhymes(): Promise<void> {
        const words = this.workshopForm.get("collect_words")?.value || this.workshopForm.get("connect_topic")?.value;
        if (!words?.trim()) {
            this.notificationService.error(this.translate.instant("workshop.errors.wordsRequired"));
            return;
        }

        this.isGeneratingRhymes = true;
        try {
            const result = await this.chatService.generateRhymes(words);
            this.workshopForm.patchValue({shape_rhymes: result});
            this.currentPhase = "shape";
            await this.autoSave();
            this.notificationService.success(this.translate.instant("workshop.aiSuccess"));
        } catch {
            this.notificationService.error(this.translate.instant("workshop.errors.aiFailed"));
        } finally {
            this.isGeneratingRhymes = false;
        }
    }

    async generateDraft(): Promise<void> {
        const collectedMaterial = [
            this.workshopForm.get("connect_topic")?.value,
            this.workshopForm.get("connect_inspirations")?.value,
            this.workshopForm.get("collect_mindmap")?.value,
            this.workshopForm.get("collect_stories")?.value,
            this.workshopForm.get("collect_words")?.value,
            this.workshopForm.get("shape_rhymes")?.value
        ].filter(Boolean).join("\n\n---\n\n");

        if (!collectedMaterial.trim()) {
            this.notificationService.error(this.translate.instant("workshop.errors.materialRequired"));
            return;
        }

        const structure = this.workshopForm.get("shape_structure")?.value;
        const structureInstruction = structure?.trim()
            ? `\n\nMANDATORY SONG STRUCTURE (follow exactly, no extra sections): ${structure}`
            : "";

        const languageInstruction = `MANDATORY: Write the entire draft in ${this.getLanguageName(this.draftLanguage)}.`;

        this.isGeneratingDraft = true;
        try {
            const result = await this.chatService.generateDraft(collectedMaterial + structureInstruction, languageInstruction);
            this.workshopForm.patchValue({shape_draft: result});
            this.currentPhase = "shape";
            await this.autoSave();
            this.notificationService.success(this.translate.instant("workshop.aiSuccess"));
        } catch {
            this.notificationService.error(this.translate.instant("workshop.errors.aiFailed"));
        } finally {
            this.isGeneratingDraft = false;
        }
    }

    getLanguageName(code: string): string {
        const map: Record<string, string> = {
            EN: "English",
            DE: "German",
            FR: "French",
            IT: "Italian",
            ES: "Spanish"
        };
        return map[code] || "English";
    }

    openStructureModal(): void {
        const dialogRef = this.dialog.open(LyricArchitectModalComponent, {
            width: "800px",
            maxWidth: "90vw",
            maxHeight: "90vh"
        });

        dialogRef.afterClosed().subscribe(result => {
            if (result?.architectureString) {
                this.workshopForm.patchValue({shape_structure: result.architectureString});
            }
        });
    }

    async exportToSketch(): Promise<void> {
        if (!this.currentWorkshopId || this.isExporting) return;

        // Save current state first
        await this.saveWorkshop();

        this.isExporting = true;
        try {
            await firstValueFrom(this.workshopService.exportToSketch(this.currentWorkshopId));
            this.currentPhase = "completed";
            this.notificationService.success(this.translate.instant("workshop.exportSuccess"));
        } catch {
            this.notificationService.error(this.translate.instant("workshop.errors.exportFailed"));
        } finally {
            this.isExporting = false;
        }
    }

    // --- Item Selection ---

    parseMarkdownItems(text: string): SelectableItem[] {
        const items: SelectableItem[] = [];
        // Split by numbered items with bold headings: "1. **heading**" or "**heading**"
        const pattern = /(?:^|\n)(?:\d+\.\s*)?\*\*(.+?)\*\*/g;
        const matches = [...text.matchAll(pattern)];

        if (matches.length < 2) return [];

        for (let i = 0; i < matches.length; i++) {
            const heading = matches[i][1].trim();
            const startIndex = matches[i].index! + matches[i][0].length;
            const endIndex = i < matches.length - 1 ? matches[i + 1].index! : text.length;
            const content = text.substring(startIndex, endIndex).trim();
            items.push({id: i, heading, content, selected: true});
        }

        return items;
    }

    compileSelectedItems(items: SelectableItem[]): string {
        return items
            .filter(item => item.selected)
            .map((item, index) => `${index + 1}. **${item.heading}**\n${item.content}`)
            .join("\n\n");
    }

    toggleInspirationItem(item: SelectableItem): void {
        item.selected = !item.selected;
    }

    toggleStoryItem(item: SelectableItem): void {
        item.selected = !item.selected;
    }

    get hasSelectedInspirations(): boolean {
        return this.inspirationItems.some(item => item.selected);
    }

    get hasSelectedStories(): boolean {
        return this.storyItems.some(item => item.selected);
    }

    async applyInspirationSelection(): Promise<void> {
        const compiled = this.compileSelectedItems(this.inspirationItems);
        this.workshopForm.patchValue({connect_inspirations: compiled});
        this.isSelectingInspirations = false;
        this.inspirationItems = [];
        this.currentPhase = "connect";
        await this.autoSave();
    }

    cancelInspirationSelection(): void {
        this.isSelectingInspirations = false;
        this.inspirationItems = [];
    }

    async applyStorySelection(): Promise<void> {
        const compiled = this.compileSelectedItems(this.storyItems);
        this.workshopForm.patchValue({collect_stories: compiled});
        this.isSelectingStories = false;
        this.storyItems = [];
        this.currentPhase = "collect";
        await this.autoSave();
    }

    cancelStorySelection(): void {
        this.isSelectingStories = false;
        this.storyItems = [];
    }

    // --- Markdown Export ---

    exportToMarkdown(): void {
        const title = this.workshopForm.get("title")?.value || "Untitled Workshop";
        const date = new Date().toISOString().split("T")[0];

        const sections: {label: string; key: string}[] = [
            {label: "Topic", key: "connect_topic"},
            {label: "Inspirations", key: "connect_inspirations"},
            {label: "Mindmap", key: "collect_mindmap"},
            {label: "Stories", key: "collect_stories"},
            {label: "Words", key: "collect_words"},
            {label: "Structure", key: "shape_structure"},
            {label: "Rhymes", key: "shape_rhymes"},
            {label: "Draft", key: "shape_draft"}
        ];

        let md = `# ${title}\n\n`;
        md += `**Phase:** ${this.getPhaseLabel(this.currentPhase)} | **Language:** ${this.draftLanguage} | **Date:** ${date}\n\n---\n`;

        for (const section of sections) {
            const value = this.workshopForm.get(section.key)?.value?.trim();
            if (value) {
                md += `\n## ${section.label}\n\n${value}\n`;
            }
        }

        const sanitizedTitle = title.replace(/[^a-zA-Z0-9-_ ]/g, "").replace(/\s+/g, "-").toLowerCase();
        const filename = `workshop-${sanitizedTitle}-${date}.md`;

        const blob = new Blob([md], {type: "text/markdown;charset=utf-8"});
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement("a");
        anchor.href = url;
        anchor.download = filename;
        anchor.click();
        URL.revokeObjectURL(url);
    }

    // --- Markdown Preview ---

    togglePreviewMode(): void {
        this.isPreviewMode = !this.isPreviewMode;
    }

    renderMarkdown(text: string): string {
        if (!text) return "";
        try {
            const html = marked.parse(text) as string;
            return this.sanitizer.sanitize(SecurityContext.HTML, html) || "";
        } catch {
            return text;
        }
    }
}
