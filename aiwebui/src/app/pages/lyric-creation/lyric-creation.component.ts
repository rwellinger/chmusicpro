import {Component, HostListener, inject, OnInit, ViewEncapsulation} from "@angular/core";
import {FormBuilder, FormGroup, FormsModule, ReactiveFormsModule} from "@angular/forms";
import {CommonModule} from "@angular/common";
import {MatDialog} from "@angular/material/dialog";
import {TranslateModule, TranslateService} from "@ngx-translate/core";
import {ActivatedRoute, Router} from "@angular/router";
import {FormDataContext, SongService} from "../../services/business/song.service";
import {NotificationService} from "../../services/ui/notification.service";
import {ChatService} from "../../services/config/chat.service";
import {MatSnackBarModule} from "@angular/material/snack-bar";
import {MatCardModule} from "@angular/material/card";
import {ProgressService} from "../../services/ui/progress.service";
import {LyricArchitectModalComponent} from "../../components/lyric-architect-modal/lyric-architect-modal.component";
import {LyricArchitectureService} from "../../services/lyric-architecture.service";
import {SongSection, SongSectionItem} from "../../models/lyric-architecture.model";
import {LyricParsingRuleService} from "../../services/config/lyric-parsing-rule.service";

interface LyricSection {
    id: string;
    label: string;
    content: string;
    order: number;
    aiInstructions?: string;
}

@Component({
    selector: "app-lyric-creation",
    standalone: true,
    imports: [CommonModule, ReactiveFormsModule, FormsModule, MatSnackBarModule, MatCardModule, TranslateModule],
    templateUrl: "./lyric-creation.component.html",
    styleUrl: "./lyric-creation.component.scss",
    encapsulation: ViewEncapsulation.None
})
export class LyricCreationComponent implements OnInit {
    lyricForm!: FormGroup;
    isGeneratingLyrics = false;
    isTranslatingLyrics = false;
    isOptimizingPhrasing = false;
    showEditDropdown = false;
    showToolsDropdown = false;
    lastCleanupState: string | null = null;
    lastStructureState: string | null = null;
    lastSearchReplaceState: string | null = null;

    // Section Editor State
    sectionEditorMode = false;
    sections: LyricSection[] = [];
    activeSection: LyricSection | null = null;
    lastSectionState: string | null = null;
    isImprovingSection = false;
    isRewritingSection = false;
    isCondensingSection = false;
    isOptimizingSection = false;

    // Section Detection Rules (loaded from API)
    private sectionDetectionPattern: RegExp | null = null;

    // Non-structural Suno tags - kept in lyrics but ignored by Rebuild Architecture
    private readonly NON_STRUCTURAL_TAGS = [
        /^guitar\s*solo$/i,
        /^instrumental$/i,
        /^solo$/i,
        /^\d+\s*beats?\s*break$/i,
        /^break$/i,
        /^interlude$/i,
        /^ad[- ]?lib$/i,
        /^fade\s*(out|in)$/i,
        /^hook$/i,
        /^drop$/i,
        /^buildup$/i
    ];

    // Context for form data storage (song-generator or sketch-creator)
    private context: FormDataContext = "song-generator";

    // State from navigation (when called from sketch editor)
    private isFromSketch = false;
    private isEditMode = false;
    private currentSketchId: string | null = null;
    private sketchFormData: any = null;
    private navigationState: any = null;

    private fb = inject(FormBuilder);
    private songService = inject(SongService);
    private notificationService = inject(NotificationService);
    private chatService = inject(ChatService);
    private progressService = inject(ProgressService);
    private dialog = inject(MatDialog);
    private architectureService = inject(LyricArchitectureService);
    private translate = inject(TranslateService);
    private lyricParsingRuleService = inject(LyricParsingRuleService);
    private route = inject(ActivatedRoute);
    private router = inject(Router);

    constructor() {
        // IMPORTANT: getCurrentNavigation() must be called in constructor!
        const navigation = this.router.getCurrentNavigation();
        this.navigationState = navigation?.extras?.state;
    }

    get isAnyLyricOperationInProgress(): boolean {
        return this.isGeneratingLyrics || this.isTranslatingLyrics || this.isOptimizingPhrasing;
    }

    get isAnySectionOperationInProgress(): boolean {
        return this.isImprovingSection || this.isRewritingSection || this.isCondensingSection || this.isOptimizingSection;
    }

    get isFromSketchCreator(): boolean {
        return this.isFromSketch;
    }

    applyChanges(): void {
        // Update lyrics in form data and navigate back
        const updatedFormData = {
            ...this.sketchFormData,
            lyrics: this.lyricForm.get("lyrics")?.value || ""
        };

        this.navigateBackToSketchCreator(updatedFormData);

        this.notificationService.success(
            this.translate.instant("lyricCreation.changesApplied")
        );
    }

    cancelChanges(): void {
        // Discard changes and navigate back with original data
        this.navigateBackToSketchCreator(this.sketchFormData);

        this.notificationService.info(
            this.translate.instant("lyricCreation.changesCancelled")
        );
    }

    private navigateBackToSketchCreator(formData: any): void {
        // Navigate back with form data
        if (this.isEditMode && this.currentSketchId) {
            this.router.navigate(["/song-sketch-creator"], {
                state: {
                    editMode: true,
                    sketchId: this.currentSketchId,
                    formData: formData
                }
            });
        } else {
            this.router.navigate(["/song-sketch-creator"], {
                state: {
                    formData: formData
                }
            });
        }
    }

    ngOnInit() {
        // Check if coming from sketch creator via router state
        if (this.navigationState?.["context"] === "sketch") {
            this.isFromSketch = true;
            this.isEditMode = this.navigationState["editMode"] || false;
            this.currentSketchId = this.navigationState["sketchId"] || null;
            this.sketchFormData = this.navigationState["formData"] || {};
            this.context = "sketch-creator";
        } else {
            // Song generator mode
            this.context = "song-generator";
        }

        this.lyricForm = this.fb.group({
            lyrics: [""]
        });

        // Load lyrics based on context
        if (this.isFromSketch && this.sketchFormData?.lyrics) {
            // From sketch: load lyrics from router state
            this.lyricForm.patchValue({lyrics: this.sketchFormData.lyrics});
        } else if (!this.isFromSketch) {
            // Song generator mode: load from localStorage
            const savedData = this.songService.loadFormData(this.context);
            if (savedData.lyrics) {
                this.lyricForm.patchValue({lyrics: savedData.lyrics});
            }

            // Auto-save lyrics on changes (only for song generator)
            this.lyricForm.valueChanges.subscribe(value => {
                this.saveLyrics(value.lyrics);
            });
        }

        // Load section detection rules from API
        this.loadSectionDetectionRules();
    }

    private loadSectionDetectionRules(): void {
        this.lyricParsingRuleService.getAllRules("section", true).subscribe({
            next: (rules) => {
                if (rules.length === 0) {
                    const errorMsg = "No active section detection rules found in database. Please add section rules in Lyric Parsing Rules settings.";
                    console.error(errorMsg);
                    this.notificationService.error(errorMsg);
                    return;
                }

                // Combine all section rule patterns with OR logic
                const patterns = rules.map(rule => `(${rule.pattern})`).join("|");
                try {
                    this.sectionDetectionPattern = new RegExp(patterns, "gmi");
                    console.log("Section detection pattern loaded from", rules.length, "rules");
                } catch (error) {
                    const errorMsg = `Failed to compile section detection patterns: ${error}`;
                    console.error(errorMsg);
                    this.notificationService.error(errorMsg);
                }
            },
            error: (error) => {
                const errorMsg = `Failed to load section detection rules from API: ${error.message}`;
                console.error(errorMsg);
                this.notificationService.error(errorMsg);
            }
        });
    }

    private saveLyrics(lyrics: string): void {
        // Load existing data from context-aware storage and update only lyrics
        const existingData = this.songService.loadFormData(this.context);
        this.songService.saveFormData({
            ...existingData,
            lyrics: lyrics
        }, this.context);
    }

    clearLyrics(): void {
        this.lyricForm.patchValue({lyrics: ""});
        this.notificationService.success(this.translate.instant("lyricCreation.autoSaved"));
    }

    async generateLyrics() {
        const currentText = this.lyricForm.get("lyrics")?.value?.trim();
        if (!currentText) {
            this.notificationService.error(this.translate.instant("lyricCreation.errors.textRequired"));
            return;
        }

        this.isGeneratingLyrics = true;
        this.lyricForm.get("lyrics")?.disable();
        try {
            const generatedLyrics = await this.progressService.executeWithProgress(
                () => this.chatService.generateLyrics(currentText),
                this.translate.instant("songGenerator.progress.generatingLyrics"),
                this.translate.instant("songGenerator.progress.generatingLyricsHint")
            );
            this.lyricForm.patchValue({lyrics: this.removeQuotes(generatedLyrics)});
        } catch (error: any) {
            this.notificationService.error(`Error generating lyrics: ${error.message}`);
        } finally {
            this.isGeneratingLyrics = false;
            this.lyricForm.get("lyrics")?.enable();
        }
    }

    async translateLyrics() {
        const currentLyrics = this.lyricForm.get("lyrics")?.value?.trim();
        if (!currentLyrics) {
            this.notificationService.error(this.translate.instant("lyricCreation.errors.lyricsRequired"));
            return;
        }

        this.isTranslatingLyrics = true;
        this.lyricForm.get("lyrics")?.disable();
        try {
            const translatedLyrics = await this.progressService.executeWithProgress(
                () => this.chatService.translateLyric(currentLyrics),
                this.translate.instant("songGenerator.progress.translatingLyrics"),
                this.translate.instant("songGenerator.progress.translatingLyricsHint")
            );
            this.lyricForm.patchValue({lyrics: this.removeQuotes(translatedLyrics)});
        } catch (error: any) {
            this.notificationService.error(`Error translating lyrics: ${error.message}`);
        } finally {
            this.isTranslatingLyrics = false;
            this.lyricForm.get("lyrics")?.enable();
        }
    }

    openLyricArchitectModal(): void {
        const dialogRef = this.dialog.open(LyricArchitectModalComponent, {
            width: "800px",
            maxWidth: "90vw",
            maxHeight: "90vh",
            disableClose: false,
            autoFocus: true
        });

        dialogRef.afterClosed().subscribe(result => {
            if (result && result.architectureString) {
                this.notificationService.success(this.translate.instant("songGenerator.success.architectureUpdated"));
            }
        });
    }

    private removeQuotes(text: string): string {
        if (!text) return text;
        return text.replace(/^["']|["']$/g, "").trim();
    }

    private isNonStructuralTag(label: string): boolean {
        return this.NON_STRUCTURAL_TAGS.some(pattern => pattern.test(label));
    }

    private capitalizeLabel(label: string): string {
        // Capitalize first letter and letters after hyphens
        // Examples: PRE-CHORUS -> Pre-Chorus, VERSE1 -> Verse 1, POST_CHORUS -> Post-Chorus
        const normalized = label.replace(/_/g, "-").toLowerCase();
        let result = normalized.replace(/(^|-)(\w)/g, (match, separator, letter) =>
            separator + letter.toUpperCase()
        );
        // Suno format: Add space before number (Verse1 -> Verse 1)
        result = result.replace(/([a-zA-Z])(\d)/g, "$1 $2");
        return result;
    }

    get characterCount(): number {
        return this.lyricForm.get("lyrics")?.value?.length || 0;
    }

    get canUndo(): boolean {
        return this.lastSearchReplaceState !== null || this.lastCleanupState !== null || this.lastStructureState !== null;
    }

    get hasSections(): boolean {
        if (!this.sectionDetectionPattern) {
            return false;
        }

        const lyrics = this.lyricForm.get("lyrics")?.value || "";
        this.sectionDetectionPattern.lastIndex = 0;
        return this.sectionDetectionPattern.test(lyrics);
    }

    toggleEditDropdown() {
        this.showEditDropdown = !this.showEditDropdown;
        if (this.showEditDropdown) {
            this.showToolsDropdown = false;
        }
    }

    closeEditDropdown() {
        this.showEditDropdown = false;
    }

    toggleToolsDropdown() {
        this.showToolsDropdown = !this.showToolsDropdown;
        if (this.showToolsDropdown) {
            this.showEditDropdown = false;
        }
    }

    closeToolsDropdown() {
        this.showToolsDropdown = false;
    }

    selectEditAction(action: "searchReplace" | "undo") {
        this.closeEditDropdown();

        if (action === "searchReplace") {
            this.openSearchReplaceDialog();
        } else if (action === "undo") {
            this.undoLastChange();
        }
    }

    selectToolsAction(action: "sectionEditor" | "structure" | "cleanup" | "optimize-phrasing" | "finalize" | "rebuild") {
        this.closeToolsDropdown();

        if (action === "sectionEditor") {
            this.toggleSectionEditor();
        } else if (action === "structure") {
            this.applyStructure();
        } else if (action === "cleanup") {
            this.cleanupLyrics();
        } else if (action === "optimize-phrasing") {
            this.optimizeLyricsPhrasing();
        } else if (action === "finalize") {
            this.finalizeLyrics();
        } else if (action === "rebuild") {
            this.rebuildFromLyricText();
        }
    }

    cleanupLyrics(): void {
        let lyrics = this.lyricForm.get("lyrics")?.value || "";
        if (!lyrics.trim()) {
            return;
        }

        // Save current state before cleanup
        this.lastCleanupState = lyrics;

        // Load cleanup rules from API and apply them
        this.lyricParsingRuleService.getAllRules("cleanup", true).subscribe({
            next: (rules) => {
                // Apply each rule in order (rules are already sorted by order field from API)
                rules.forEach(rule => {
                    try {
                        const regex = new RegExp(rule.pattern, "gm");
                        lyrics = lyrics.replace(regex, rule.replacement);
                    } catch (error) {
                        console.error(`Failed to apply rule "${rule.name}":`, error);
                    }
                });

                this.lyricForm.patchValue({lyrics: lyrics.trim()});
                this.notificationService.success(this.translate.instant("lyricCreation.cleanupComplete"));
            },
            error: (error) => {
                console.error("Failed to load lyric parsing rules:", error);
                this.notificationService.error("Failed to load cleanup rules");
            }
        });
    }

    async optimizeLyricsPhrasing(): Promise<void> {
        let lyrics = this.lyricForm.get("lyrics")?.value?.trim();
        if (!lyrics) {
            this.notificationService.error(this.translate.instant("lyricCreation.errors.lyricsRequired"));
            return;
        }

        // Save current state for undo
        this.lastCleanupState = lyrics;

        this.isOptimizingPhrasing = true;
        this.lyricForm.get("lyrics")?.disable();
        try {
            // Step 1: AI-Optimize via Ollama
            const optimized = await this.progressService.executeWithProgress(
                () => this.chatService.optimizeLyricPhrasing(lyrics),
                this.translate.instant("lyricCreation.optimizing"),
                this.translate.instant("lyricCreation.optimizingHint")
            );
            lyrics = this.removeQuotes(optimized);

            // Step 2: Apply Cleanup Rules (remove trailing spaces, normalize quotes, etc.)
            const rules = await this.lyricParsingRuleService.getAllRules("cleanup", true).toPromise();
            if (rules) {
                rules.forEach(rule => {
                    try {
                        const regex = new RegExp(rule.pattern, "gm");
                        lyrics = lyrics.replace(regex, rule.replacement);
                    } catch (error) {
                        console.error(`Failed to apply rule "${rule.name}":`, error);
                    }
                });
            }

            // Update form with cleaned lyrics
            this.lyricForm.patchValue({lyrics: lyrics.trim()});

            // Step 3: Apply Structure (normalize section markers)
            this.applyStructure();

            this.notificationService.success(this.translate.instant("lyricCreation.optimizingSuccess"));
        } catch (error: any) {
            this.notificationService.error(
                this.translate.instant("lyricCreation.errors.optimizingPhrasing", {error: error.message})
            );
        } finally {
            this.isOptimizingPhrasing = false;
            this.lyricForm.get("lyrics")?.enable();
        }
    }

    applyStructure(): void {
        let lyrics = this.lyricForm.get("lyrics")?.value || "";
        if (!lyrics.trim()) {
            this.notificationService.error(this.translate.instant("lyricCreation.errors.lyricsRequired"));
            return;
        }

        // Check if labels already exist (various formats: Label:, [Label], **LABEL**, etc.)
        const hasLabels = /^(\w+:|[*[\]]).*$/m.test(lyrics);
        if (hasLabels) {
            const confirmed = confirm(this.translate.instant("lyricCreation.confirmApplyStructure"));
            if (!confirmed) {
                return;
            }
        }

        // Get architecture from service
        const architectureString = this.architectureService.generateArchitectureString();
        if (!architectureString || !architectureString.trim()) {
            this.notificationService.error(this.translate.instant("lyricCreation.errors.noArchitecture"));
            return;
        }

        // Parse architecture: Extract only the elements (INTRO, VERSE1, etc.)
        // Format is: "Song structure: INTRO - VERSE1 - CHORUS - ..."
        const match = architectureString.match(/song structure:\s*(.+)/i);
        if (!match) {
            this.notificationService.error(this.translate.instant("lyricCreation.errors.noArchitecture"));
            return;
        }

        // Split by " - " and clean up
        const sections = match[1].split("-").map((s: string) => s.trim()).filter((s: string) => s);
        if (sections.length === 0) {
            this.notificationService.error(this.translate.instant("lyricCreation.errors.noArchitecture"));
            return;
        }

        // Save current state before applying structure
        this.lastStructureState = lyrics;

        // Remove existing structural section labels only (preserve non-structural Suno tags like [Guitar Solo])
        if (this.sectionDetectionPattern) {
            const stripPattern = new RegExp(this.sectionDetectionPattern.source, "gm");
            lyrics = lyrics.replace(stripPattern, "");
        }
        // Also handle colon format labels (Intro:, Verse 1:, etc.)
        lyrics = lyrics.replace(/^(Intro|Verse\s*\d*|Chorus\s*\d*|Bridge\s*\d*|Outro|Pre[-_\s]?Chorus|Post[-_\s]?Chorus)\s*:\s*$/gmi, "");

        // Split into paragraphs (separated by blank lines)
        const paragraphs = lyrics.split(/\n\s*\n/).filter((p: string) => p.trim());

        if (paragraphs.length === 0) {
            this.notificationService.error(this.translate.instant("lyricCreation.errors.lyricsRequired"));
            return;
        }

        // Apply structure: 1:1 mapping with Suno bracket format "[Label]\nText"
        const structured = paragraphs.map((para: string, i: number) => {
            if (i < sections.length) {
                // Capitalize properly (e.g., VERSE1 -> Verse 1, PRE-CHORUS -> Pre-Chorus)
                const label = this.capitalizeLabel(sections[i]);
                return `[${label}]\n${para.trim()}`;
            }
            return para.trim();
        }).join("\n\n");

        this.lyricForm.patchValue({lyrics: structured});
        this.notificationService.success(this.translate.instant("lyricCreation.structureApplied"));
    }

    undoLastChange(): void {
        // Priority: SearchReplace → Structure → Cleanup
        if (this.lastSearchReplaceState !== null) {
            // Undo search/replace change (highest priority)
            this.lyricForm.patchValue({lyrics: this.lastSearchReplaceState});
            this.lastSearchReplaceState = null;
            this.notificationService.success(this.translate.instant("lyricCreation.undoApplied"));
        } else if (this.lastStructureState !== null) {
            // Undo structure change
            this.lyricForm.patchValue({lyrics: this.lastStructureState});
            this.lastStructureState = null;
            this.notificationService.success(this.translate.instant("lyricCreation.undoApplied"));
        } else if (this.lastCleanupState !== null) {
            // Undo cleanup change
            this.lyricForm.patchValue({lyrics: this.lastCleanupState});
            this.lastCleanupState = null;
            this.notificationService.success(this.translate.instant("lyricCreation.undoApplied"));
        }
    }

    private parseLyrics(text: string): LyricSection[] {
        if (!this.sectionDetectionPattern) {
            const errorMsg = "Section detection pattern not loaded. Cannot parse lyrics.";
            console.error(errorMsg);
            this.notificationService.error(errorMsg);
            return [];
        }

        const sections: LyricSection[] = [];
        const lines = text.split("\n");
        let currentSection: LyricSection | null = null;
        let order = 0;

        // Clone regex to avoid lastIndex issues
        const sectionRegex = new RegExp(this.sectionDetectionPattern.source, this.sectionDetectionPattern.flags);

        for (const line of lines) {
            sectionRegex.lastIndex = 0;
            const match = sectionRegex.exec(line);

            if (match) {
                // Found a section label
                if (currentSection) {
                    sections.push(currentSection);
                }

                // Extract label - try to find the actual label text from match groups
                let rawLabel = "";
                for (let i = 1; i < match.length; i++) {
                    if (match[i] && match[i].trim()) {
                        rawLabel = match[i].trim();
                        break;
                    }
                }

                // Clean up label: remove [] and ** markers and trailing :
                rawLabel = rawLabel.replace(/^\[\s*|\s*\]$|^\*\*\s*|\s*\*\*$|:$/g, "");

                // Keep spaces before numbers for Suno format (Verse 1 stays Verse 1)
                // Only normalize underscores to hyphens (Pre_Chorus -> Pre-Chorus)
                rawLabel = rawLabel.replace(/_/g, "-");

                // Start new section
                const label = this.capitalizeLabel(rawLabel);
                currentSection = {
                    id: `section-${order}-${Date.now()}`,
                    label: label,
                    content: "",
                    order: order++
                };
            } else if (currentSection) {
                // Add line to current section content
                if (currentSection.content) {
                    currentSection.content += "\n" + line;
                } else {
                    currentSection.content = line;
                }
            }
        }

        // Save last section
        if (currentSection) {
            sections.push(currentSection);
        }

        // Clean up content (trim whitespace)
        sections.forEach(section => {
            section.content = section.content.trim();
        });

        return sections;
    }

    private rebuildLyrics(sections: LyricSection[]): string {
        return sections
            .sort((a, b) => a.order - b.order)
            .map(section => `[${section.label}]\n${section.content}`)
            .join("\n\n");
    }

    toggleSectionEditor(): void {
        if (!this.hasSections) {
            const confirmed = confirm(
                this.translate.instant("lyricCreation.sectionEditor.noStructure")
            );
            if (confirmed) {
                this.applyStructure();
                setTimeout(() => this.toggleSectionEditor(), 100);
            }
            return;
        }

        const currentLyrics = this.lyricForm.get("lyrics")?.value || "";
        this.lastSectionState = currentLyrics;
        this.sections = this.parseLyrics(currentLyrics);

        if (this.sections.length === 0) {
            this.notificationService.error(
                this.translate.instant("lyricCreation.sectionEditor.parseFailed")
            );
            return;
        }

        this.sectionEditorMode = true;
        this.activeSection = this.sections[0];
        this.notificationService.info(
            this.translate.instant("lyricCreation.sectionEditor.activated")
        );
    }

    applyAndCloseSectionEditor(): void {
        const updatedLyrics = this.rebuildLyrics(this.sections);
        this.lyricForm.patchValue({lyrics: updatedLyrics});

        this.sectionEditorMode = false;
        this.activeSection = null;

        this.notificationService.success(
            this.translate.instant("lyricCreation.sectionEditor.applied")
        );
    }

    cancelSectionEditor(): void {
        if (this.lastSectionState) {
            this.lyricForm.patchValue({lyrics: this.lastSectionState});
        }

        this.sectionEditorMode = false;
        this.activeSection = null;

        this.notificationService.info(
            this.translate.instant("lyricCreation.sectionEditor.cancelled")
        );
    }

    selectSection(section: LyricSection): void {
        this.activeSection = section;
    }

    async improveSectionAI(): Promise<void> {
        if (!this.activeSection) {
            return;
        }

        this.isImprovingSection = true;
        try {
            const fullContext = this.rebuildLyrics(this.sections);
            const improvedContent = await this.progressService.executeWithProgress(
                () => this.chatService.improveLyricSection(
                    this.activeSection!.label,
                    this.activeSection!.content,
                    fullContext,
                    this.activeSection!.aiInstructions
                ),
                this.translate.instant("lyricCreation.sectionEditor.improving"),
                this.translate.instant("lyricCreation.sectionEditor.improvingHint")
            );
            this.activeSection.content = this.removeQuotes(improvedContent);
        } catch (error: any) {
            this.notificationService.error(`Error improving section: ${error.message}`);
        } finally {
            this.isImprovingSection = false;
        }
    }

    async rewriteSectionAI(): Promise<void> {
        if (!this.activeSection) {
            return;
        }

        this.isRewritingSection = true;
        try {
            const rewrittenContent = await this.progressService.executeWithProgress(
                () => this.chatService.rewriteLyricSection(
                    this.activeSection!.label,
                    this.activeSection!.content,
                    this.activeSection!.aiInstructions
                ),
                this.translate.instant("lyricCreation.sectionEditor.rewriting"),
                this.translate.instant("lyricCreation.sectionEditor.rewritingHint")
            );
            this.activeSection.content = this.removeQuotes(rewrittenContent);
        } catch (error: any) {
            this.notificationService.error(`Error rewriting section: ${error.message}`);
        } finally {
            this.isRewritingSection = false;
        }
    }

    async condenseSectionAI(): Promise<void> {
        if (!this.activeSection) {
            return;
        }

        this.isCondensingSection = true;
        try {
            const condensedContent = await this.progressService.executeWithProgress(
                () => this.chatService.condenseLyricSection(
                    this.activeSection!.label,
                    this.activeSection!.content,
                    this.activeSection!.aiInstructions
                ),
                this.translate.instant("lyricCreation.sectionEditor.condensing"),
                this.translate.instant("lyricCreation.sectionEditor.condensingHint")
            );
            this.activeSection.content = this.removeQuotes(condensedContent);
        } catch (error: any) {
            this.notificationService.error(`Error condensing section: ${error.message}`);
        } finally {
            this.isCondensingSection = false;
        }
    }

    async optimizeSectionAI(): Promise<void> {
        if (!this.activeSection) {
            return;
        }

        this.isOptimizingSection = true;
        try {
            // Step 1: AI-Optimize via Ollama
            const optimizedContent = await this.progressService.executeWithProgress(
                () => this.chatService.optimizeLyricPhrasing(
                    this.activeSection!.content,
                    this.activeSection!.aiInstructions
                ),
                this.translate.instant("lyricCreation.sectionEditor.optimizing"),
                this.translate.instant("lyricCreation.sectionEditor.optimizingHint")
            );
            let cleanedContent = this.removeQuotes(optimizedContent);

            // Step 2: Apply Cleanup Rules (remove trailing spaces, normalize quotes, etc.)
            const rules = await this.lyricParsingRuleService.getAllRules("cleanup", true).toPromise();
            if (rules) {
                rules.forEach(rule => {
                    try {
                        const regex = new RegExp(rule.pattern, "gm");
                        cleanedContent = cleanedContent.replace(regex, rule.replacement);
                    } catch (error) {
                        console.error(`Failed to apply rule "${rule.name}":`, error);
                    }
                });
            }

            this.activeSection.content = cleanedContent.trim();
        } catch (error: any) {
            this.notificationService.error(
                this.translate.instant("lyricCreation.errors.optimizingSection", {error: error.message})
            );
        } finally {
            this.isOptimizingSection = false;
        }
    }

    cleanupSectionContent(): void {
        if (!this.activeSection || !this.activeSection.content.trim()) {
            return;
        }

        let content = this.activeSection.content;

        // Load cleanup rules from API and apply them
        this.lyricParsingRuleService.getAllRules("cleanup", true).subscribe({
            next: (rules) => {
                // Apply each rule in order (rules are already sorted by order field from API)
                rules.forEach(rule => {
                    try {
                        const regex = new RegExp(rule.pattern, "gm");
                        content = content.replace(regex, rule.replacement);
                    } catch (error) {
                        console.error(`Failed to apply rule "${rule.name}":`, error);
                    }
                });

                this.activeSection!.content = content.trim();
                this.notificationService.success(this.translate.instant("lyricCreation.cleanupComplete"));
            },
            error: (error) => {
                console.error("Failed to load lyric parsing rules:", error);
                this.notificationService.error("Failed to load cleanup rules");
            }
        });
    }

    rebuildFromLyricText(): void {
        const lyrics = this.lyricForm.get("lyrics")?.value || "";
        if (!lyrics.trim()) {
            this.notificationService.error(this.translate.instant("lyricCreation.errors.lyricsRequired"));
            return;
        }

        // Parse existing lyrics
        const sections = this.parseLyrics(lyrics);

        if (sections.length === 0) {
            this.notificationService.error(this.translate.instant("lyricCreation.rebuildFailed"));
            return;
        }

        // Confirm before overwriting architecture
        const confirmed = confirm(this.translate.instant("lyricCreation.confirmRebuild"));
        if (!confirmed) {
            return;
        }

        // Map parsed sections to SongSection enum
        const architectureSections: SongSectionItem[] = [];
        let hasWarnings = false;

        for (const section of sections) {
            // Skip non-structural Suno tags (Guitar Solo, 8 beats break, etc.)
            if (this.isNonStructuralTag(section.label)) {
                console.info(`Skipping non-structural tag: ${section.label}`);
                hasWarnings = true;
                continue;
            }

            const mapped = this.mapLabelToSongSection(section.label);

            if (!mapped) {
                // Unknown section type - log warning but continue
                console.warn(`Unknown section label: ${section.label} - skipping`);
                hasWarnings = true;
                continue;
            }

            architectureSections.push(mapped);
        }

        if (architectureSections.length === 0) {
            this.notificationService.error(this.translate.instant("lyricCreation.rebuildFailed"));
            return;
        }

        // Update architecture service
        this.architectureService.saveConfig({
            sections: architectureSections,
            lastModified: new Date()
        });

        // Show success notification
        if (hasWarnings) {
            this.notificationService.success(
                this.translate.instant("lyricCreation.rebuildSuccessWithWarnings", {count: architectureSections.length})
            );
        } else {
            this.notificationService.success(
                this.translate.instant("lyricCreation.rebuildSuccess", {count: architectureSections.length})
            );
        }
    }

    private mapLabelToSongSection(label: string): SongSectionItem | null {
        // Normalize label: lowercase and remove spaces/hyphens/underscores
        const normalized = label.toLowerCase().replace(/[\s_-]/g, "");

        // Extract base type and number (e.g., "verse1" -> "verse", "1")
        const match = normalized.match(/^([a-z]+)(\d*)$/);
        if (!match) {
            return null;
        }

        const [, baseType, number] = match;
        let section: SongSection | null = null;
        let displayName: string;

        // Map to SongSection enum
        switch (baseType) {
            case "intro":
                section = SongSection.INTRO;
                displayName = "INTRO";
                break;
            case "verse":
                section = SongSection.VERSE;
                displayName = number ? `VERSE${number}` : "VERSE1";
                break;
            case "prechorus":
                section = SongSection.PRE_CHORUS;
                displayName = "PRE_CHORUS";
                break;
            case "chorus":
                section = SongSection.CHORUS;
                displayName = number ? `CHORUS${number}` : "CHORUS";
                break;
            case "bridge":
                section = SongSection.BRIDGE;
                displayName = number ? `BRIDGE${number}` : "BRIDGE";
                break;
            case "outro":
                section = SongSection.OUTRO;
                displayName = "OUTRO";
                break;
            case "postchorus":
                // POST_CHORUS is not in the enum - log warning
                console.warn("POST_CHORUS detected but not supported in architecture - skipping");
                return null;
            default:
                return null;
        }

        return {
            id: this.generateSectionId(),
            section,
            displayName
        };
    }

    private generateSectionId(): string {
        return `section_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    @HostListener("document:click", ["$event"])
    onDocumentClick(event: Event) {
        const target = event.target as HTMLElement;
        const editDropdown = target.closest(".edit-dropdown-container");
        const toolsDropdown = target.closest(".tools-dropdown-container");

        if (!editDropdown && this.showEditDropdown) {
            this.closeEditDropdown();
        }
        if (!toolsDropdown && this.showToolsDropdown) {
            this.closeToolsDropdown();
        }
    }

    openSearchReplaceDialog(): void {
        const SearchReplaceDialogComponent = import("../../components/search-replace-dialog/search-replace-dialog.component")
            .then(m => m.SearchReplaceDialogComponent);

        SearchReplaceDialogComponent.then(component => {
            const dialogRef = this.dialog.open(component, {
                width: "500px",
                maxWidth: "90vw",
                disableClose: false,
                autoFocus: true
            });

            dialogRef.afterClosed().subscribe(result => {
                if (result && result.searchText) {
                    this.performSearchReplace(result.searchText, result.replaceText);
                }
            });
        });
    }

    private performSearchReplace(searchText: string, replaceText: string): void {
        const currentLyrics = this.lyricForm.get("lyrics")?.value || "";
        if (!currentLyrics.trim()) {
            return;
        }

        // Save state for undo
        this.lastSearchReplaceState = currentLyrics;

        // Perform replacement
        const updatedLyrics = currentLyrics.replaceAll(searchText, replaceText);

        // Calculate number of replacements
        const occurrences = (currentLyrics.match(new RegExp(this.escapeRegExp(searchText), "g")) || []).length;

        // Update form
        this.lyricForm.patchValue({lyrics: updatedLyrics});

        // Show success notification
        this.notificationService.success(
            this.translate.instant("lyricCreation.searchReplaceDialog.applied", {count: occurrences})
        );
    }

    private escapeRegExp(text: string): string {
        return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    }

    async finalizeLyrics(): Promise<void> {
        let lyrics = this.lyricForm.get("lyrics")?.value || "";
        if (!lyrics.trim()) {
            this.notificationService.error(this.translate.instant("lyricCreation.errors.lyricsRequired"));
            return;
        }

        // Save current state before finalize
        this.lastCleanupState = lyrics;

        try {
            // Step 1: Cleanup
            const rules = await this.lyricParsingRuleService.getAllRules("cleanup", true).toPromise();

            if (rules) {
                // Apply each cleanup rule in order
                rules.forEach(rule => {
                    try {
                        const regex = new RegExp(rule.pattern, "gm");
                        lyrics = lyrics.replace(regex, rule.replacement);
                    } catch (error) {
                        console.error(`Failed to apply rule "${rule.name}":`, error);
                    }
                });

                // Update form with cleaned lyrics
                this.lyricForm.patchValue({lyrics: lyrics.trim()});
            }

            // Step 2: Apply Structure
            this.applyStructure();

            // Success notification
            this.notificationService.success(this.translate.instant("lyricCreation.finalizeComplete"));
        } catch (error) {
            console.error("Failed to finalize lyrics:", error);
            this.notificationService.error("Failed to finalize lyrics");
        }
    }

    async copyLyricsToClipboard(): Promise<void> {
        let lyrics = this.lyricForm.get("lyrics")?.value || "";
        if (!lyrics.trim()) {
            return;
        }

        // Remove Markdown formatting for plain text copy
        // Remove **Label** format
        lyrics = lyrics.replace(/\*\*([^*]+)\*\*/g, "$1");
        // Remove [Label] format
        lyrics = lyrics.replace(/\[([^\]]+)\]/g, "$1");

        try {
            await navigator.clipboard.writeText(lyrics);
            this.notificationService.success(this.translate.instant("lyricCreation.copiedToClipboard"));
        } catch (error) {
            console.error("Failed to copy to clipboard:", error);
            this.notificationService.error(this.translate.instant("lyricCreation.errors.copyFailed"));
        }
    }
}
