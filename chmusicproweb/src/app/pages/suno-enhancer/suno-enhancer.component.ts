import {Component, ElementRef, inject, OnDestroy, OnInit, ViewChild, ViewEncapsulation} from "@angular/core";
import {MusicStyleChooserConfig} from "../../models/music-style-chooser.model";
import {FormBuilder, FormGroup, FormsModule, ReactiveFormsModule} from "@angular/forms";
import {CommonModule} from "@angular/common";
import {ActivatedRoute, Router} from "@angular/router";
import {TranslateModule, TranslateService} from "@ngx-translate/core";
import {MatCardModule} from "@angular/material/card";
import {MatButtonModule} from "@angular/material/button";
import {MatChipsModule} from "@angular/material/chips";
import {MatFormFieldModule} from "@angular/material/form-field";
import {MatInputModule} from "@angular/material/input";
import {MatSelectModule} from "@angular/material/select";
import {MatSlideToggleModule} from "@angular/material/slide-toggle";
import {debounceTime, Subject, takeUntil} from "rxjs";

import {SunoTemplateService} from "../../services/business/suno-template.service";
import {NotificationService} from "../../services/ui/notification.service";
import {ChatService} from "../../services/config/chat.service";
import {ProgressService} from "../../services/ui/progress.service";
import {SunoTemplate} from "../../models/suno-template.model";
import {MusicStyleChooserInlineComponent} from "../../components/music-style-chooser-inline/music-style-chooser-inline.component";
import {MusicStyleChooserService} from "../../services/music-style-chooser.service";
import {
    SUNO_LYRICS_CHAR_LIMIT,
    SUNO_LYRICS_WARNING_LIMIT,
    SUNO_MODIFIERS,
    SUNO_STYLE_CHAR_LIMIT,
    SUNO_STYLE_WARNING_LIMIT,
    SUNO_TAG_CATEGORIES,
    SunoTag,
    SunoTagCategory,
} from "./suno-tag-config";

@Component({
    selector: "app-suno-enhancer",
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        ReactiveFormsModule,
        MatCardModule,
        MatButtonModule,
        MatChipsModule,
        MatFormFieldModule,
        MatInputModule,
        MatSelectModule,
        MatSlideToggleModule,
        TranslateModule,
        MusicStyleChooserInlineComponent,
    ],
    templateUrl: "./suno-enhancer.component.html",
    styleUrl: "./suno-enhancer.component.scss",
    encapsulation: ViewEncapsulation.None,
})
export class SunoEnhancerComponent implements OnInit, OnDestroy {
    // View mode
    isEditorMode = false;
    currentTemplateId: string | null = null;

    // Editor
    templateForm!: FormGroup;
    styleForm!: FormGroup;
    saveStatus: "idle" | "saving" | "saved" = "idle";
    private saveStatusTimer: ReturnType<typeof setTimeout> | null = null;

    // Tag palette
    tagCategories = SUNO_TAG_CATEGORIES;
    modifiers = SUNO_MODIFIERS;
    activeCategory: string | null = null;
    showModifiers = false;
    lastInsertedTag: SunoTag | null = null;

    // Preview mode
    isPreviewMode = false;
    previewHtml = '';

    // Style prompt mode
    currentMode: "auto" | "manual" = "auto";

    @ViewChild(MusicStyleChooserInlineComponent) styleChooser!: MusicStyleChooserInlineComponent;

    // Library
    templates: SunoTemplate[] = [];
    totalTemplates = 0;
    currentPage = 0;
    pageSize = 10;
    searchTerm = "";
    filterType: string | null = null;
    isLoading = false;

    // Detail panel
    selectedTemplate: SunoTemplate | null = null;
    isLoadingDetail = false;

    // Char limits
    readonly LYRICS_LIMIT = SUNO_LYRICS_CHAR_LIMIT;
    readonly LYRICS_WARNING = SUNO_LYRICS_WARNING_LIMIT;
    readonly STYLE_LIMIT = SUNO_STYLE_CHAR_LIMIT;
    readonly STYLE_WARNING = SUNO_STYLE_WARNING_LIMIT;

    @ViewChild('lyricsTextarea') lyricsTextarea!: ElementRef<HTMLTextAreaElement>;

    private destroy$ = new Subject<void>();
    private fb = inject(FormBuilder);
    private router = inject(Router);
    private route = inject(ActivatedRoute);
    private templateService = inject(SunoTemplateService);
    private notificationService = inject(NotificationService);
    private translate = inject(TranslateService);
    private styleChooserService = inject(MusicStyleChooserService);
    private chatService = inject(ChatService);
    private progressService = inject(ProgressService);

    isEnhancingPrompt = false;
    isTranslatingPrompt = false;

    get isAnyAiOperationInProgress(): boolean {
        return this.isEnhancingPrompt || this.isTranslatingPrompt;
    }

    ngOnInit(): void {
        this.initForms();

        const routeId = this.route.snapshot.paramMap.get("id");
        if (routeId) {
            this.isEditorMode = true;
            this.currentTemplateId = routeId;
            this.loadTemplate(routeId);
        } else {
            // Check for fromSketch navigation state
            const nav = this.router.getCurrentNavigation();
            const state = nav?.extras?.state || history.state;
            if (state?.['fromSketch'] && state?.['sketchId']) {
                this.createFromSketch(state['sketchId']);
            } else {
                this.loadTemplates();
            }
        }
    }

    ngOnDestroy(): void {
        this.destroy$.next();
        this.destroy$.complete();
        if (this.saveStatusTimer) clearTimeout(this.saveStatusTimer);
    }

    // ===== Forms =====

    private initForms(): void {
        this.templateForm = this.fb.group({
            title: [''],
            template_type: ['song'],
            enhanced_lyrics: [''],
            is_instrumental: [false],
        });

        this.styleForm = this.fb.group({
            genre: [''],
            bpm: [null],
            vocal_type: [''],
            instruments: [''],
            mood: [''],
            mix_character: [''],
            style_prompt: [''],
        });

        // Auto-save on form changes (editor mode)
        this.templateForm.valueChanges.pipe(
            debounceTime(2000),
            takeUntil(this.destroy$),
        ).subscribe(() => {
            if (this.isEditorMode && this.currentTemplateId) {
                this.autoSave();
            }
        });

        this.styleForm.valueChanges.pipe(
            debounceTime(2000),
            takeUntil(this.destroy$),
        ).subscribe(() => {
            if (this.isEditorMode && this.currentTemplateId) {
                if (this.currentMode === 'auto') {
                    this.regenerateStylePrompt();
                }
                this.autoSave();
            }
        });

        // Regenerate style prompt when instrumental toggle changes
        this.templateForm.get('is_instrumental')!.valueChanges.pipe(
            takeUntil(this.destroy$),
        ).subscribe(() => {
            if (this.styleChooser) {
                this.styleChooser.isInstrumental = this.templateForm.get('is_instrumental')?.value || false;
                this.styleChooser.filterInstrumentsForMode();
            }
            this.regenerateStylePrompt();
        });
    }

    // ===== Library Mode =====

    loadTemplates(): void {
        this.isLoading = true;
        this.templateService.getTemplates(
            this.pageSize,
            this.currentPage * this.pageSize,
            this.searchTerm || undefined,
            this.filterType || undefined,
        ).pipe(takeUntil(this.destroy$)).subscribe({
            next: (response) => {
                this.templates = response.data;
                this.totalTemplates = response.pagination.total;
                this.isLoading = false;
                if (!this.selectedTemplate && this.templates.length > 0) {
                    this.selectTemplate(this.templates[0]);
                }
            },
            error: () => {
                this.notificationService.error(this.translate.instant('sunoEnhancer.errors.loadFailed'));
                this.isLoading = false;
            },
        });
    }

    onSearch(): void {
        this.currentPage = 0;
        this.selectedTemplate = null;
        this.loadTemplates();
    }

    onFilterChange(type: string | null): void {
        this.filterType = type;
        this.currentPage = 0;
        this.selectedTemplate = null;
        this.loadTemplates();
    }

    onPageChange(direction: number): void {
        this.currentPage += direction;
        this.selectedTemplate = null;
        this.loadTemplates();
    }

    createNewTemplate(type: 'song' | 'instrumental'): void {
        const defaultTitle = type === 'song'
            ? this.translate.instant('sunoEnhancer.defaults.songTitle')
            : this.translate.instant('sunoEnhancer.defaults.instrumentalTitle');

        this.templateService.createTemplate({
            title: defaultTitle,
            template_type: type,
            is_instrumental: type === 'instrumental',
        }).pipe(takeUntil(this.destroy$)).subscribe({
            next: (response) => {
                this.router.navigate(['/suno-enhancer', response.data.id]);
            },
            error: () => {
                this.notificationService.error(this.translate.instant('sunoEnhancer.errors.createFailed'));
            },
        });
    }

    openTemplate(template: SunoTemplate): void {
        this.selectTemplate(template);
    }

    selectTemplate(template: SunoTemplate): void {
        this.isLoadingDetail = true;
        this.templateService.getTemplateById(String(template.id))
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: (response) => {
                    this.selectedTemplate = response.data;
                    this.isLoadingDetail = false;
                },
                error: () => {
                    this.notificationService.error(this.translate.instant('sunoEnhancer.errors.loadFailed'));
                    this.isLoadingDetail = false;
                },
            });
    }

    editSelectedTemplate(): void {
        if (!this.selectedTemplate) return;
        this.router.navigate(['/suno-enhancer', this.selectedTemplate.id]);
    }

    deleteSelectedTemplate(): void {
        if (!this.selectedTemplate) return;
        if (!confirm(this.translate.instant('sunoEnhancer.confirmDelete'))) return;

        this.templateService.deleteTemplate(this.selectedTemplate.id).pipe(takeUntil(this.destroy$)).subscribe({
            next: () => {
                this.selectedTemplate = null;
                this.loadTemplates();
            },
            error: () => {
                this.notificationService.error(this.translate.instant('sunoEnhancer.errors.deleteFailed'));
            },
        });
    }

    formatDate(dateString: string | undefined): string {
        if (!dateString) return "-";
        return new Date(dateString).toLocaleDateString();
    }

    truncateText(text: string | undefined, maxLength = 200): string {
        if (!text) return "";
        return text.length > maxLength ? text.substring(0, maxLength) + "..." : text;
    }

    // ===== Editor Mode =====

    private loadTemplate(id: string): void {
        this.templateService.getTemplateById(id).pipe(takeUntil(this.destroy$)).subscribe({
            next: (response) => {
                const t = response.data;
                this.templateForm.patchValue({
                    title: t.title,
                    template_type: t.template_type,
                    enhanced_lyrics: t.enhanced_lyrics || '',
                    is_instrumental: t.is_instrumental,
                }, {emitEvent: false});

                this.styleForm.patchValue({
                    genre: t.genre || '',
                    bpm: t.bpm,
                    vocal_type: t.vocal_type || '',
                    instruments: t.instruments || '',
                    mood: t.mood || '',
                    mix_character: t.mix_character || '',
                    style_prompt: t.style_prompt || '',
                }, {emitEvent: false});

                // Restore style chooser from DB fields
                this.restoreStyleChooserFromFields(t);

                // Detect auto/manual mode by comparing saved prompt with auto-generated one
                const config = this.styleChooserService.getConfig();
                const isInstrumental = t.is_instrumental || false;
                const autoPrompt = this.buildAutoPrompt(config, isInstrumental);

                if (!t.style_prompt || t.style_prompt === autoPrompt) {
                    this.currentMode = 'auto';
                } else {
                    this.currentMode = 'manual';
                }
            },
            error: () => {
                this.notificationService.error(this.translate.instant('sunoEnhancer.errors.loadFailed'));
                this.router.navigate(['/suno-enhancer']);
            },
        });
    }

    private createFromSketch(sketchId: string): void {
        this.templateService.createFromSketch(sketchId).pipe(takeUntil(this.destroy$)).subscribe({
            next: (response) => {
                this.router.navigate(['/suno-enhancer', response.data.id]);
            },
            error: () => {
                this.notificationService.error(this.translate.instant('sunoEnhancer.errors.createFromSketchFailed'));
                this.router.navigate(['/suno-enhancer']);
            },
        });
    }

    private autoSave(): void {
        if (!this.currentTemplateId) return;

        this.saveStatus = "saving";
        const data = {
            ...this.templateForm.value,
            ...this.styleForm.value,
        };

        this.templateService.updateTemplate(this.currentTemplateId, data)
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: () => {
                    this.saveStatus = "saved";
                    if (this.saveStatusTimer) clearTimeout(this.saveStatusTimer);
                    this.saveStatusTimer = setTimeout(() => {
                        this.saveStatus = "idle";
                    }, 2000);
                },
                error: () => {
                    this.saveStatus = "idle";
                },
            });
    }

    backToLibrary(): void {
        this.router.navigate(['/suno-enhancer']);
    }

    // ===== Tag Palette =====

    get filteredCategories(): SunoTagCategory[] {
        const templateType = this.templateForm.get('template_type')?.value;
        const isInstrumental = templateType === 'instrumental';
        return this.tagCategories.filter(cat => {
            if (isInstrumental && cat.mode === 'song') return false;
            if (!isInstrumental && cat.mode === 'edm') return false;
            return true;
        });
    }

    toggleCategory(categoryKey: string): void {
        this.activeCategory = this.activeCategory === categoryKey ? null : categoryKey;
        this.showModifiers = false;
        this.lastInsertedTag = null;
    }

    insertTag(tag: SunoTag): void {
        const textarea = this.lyricsTextarea?.nativeElement;
        if (!textarea) return;

        const tagText = `[${tag.tag}]\n`;
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const current = this.templateForm.get('enhanced_lyrics')?.value || '';

        const newValue = current.substring(0, start) + tagText + current.substring(end);
        const scrollTop = textarea.scrollTop;
        this.templateForm.patchValue({enhanced_lyrics: newValue});

        // Restore cursor position and scroll position after Angular re-render
        setTimeout(() => {
            const newPos = start + tagText.length;
            textarea.focus();
            textarea.setSelectionRange(newPos, newPos);
            textarea.scrollTop = scrollTop;
        });

        if (tag.supportsModifiers) {
            this.showModifiers = true;
            this.lastInsertedTag = tag;
        } else {
            this.showModifiers = false;
            this.lastInsertedTag = null;
        }
    }

    applyModifier(modifier: string): void {
        if (!this.lastInsertedTag) return;

        const current = this.templateForm.get('enhanced_lyrics')?.value || '';
        const plainTag = `[${this.lastInsertedTag.tag}]`;
        const modifiedTag = `[${this.lastInsertedTag.tag} | ${modifier}]`;

        // Replace the last occurrence of the plain tag
        const lastIndex = current.lastIndexOf(plainTag);
        if (lastIndex !== -1) {
            const newValue = current.substring(0, lastIndex) + modifiedTag + current.substring(lastIndex + plainTag.length);
            this.templateForm.patchValue({enhanced_lyrics: newValue});
        }

        this.showModifiers = false;
        this.lastInsertedTag = null;
    }

    // ===== Style Prompt =====

    private regenerateStylePrompt(): void {
        if (this.currentMode === 'manual') return;

        const config = this.styleChooserService.getConfig();
        const isInstrumental = this.templateForm.get('is_instrumental')?.value || false;
        const prompt = this.buildAutoPrompt(config, isInstrumental);

        this.styleForm.patchValue({style_prompt: prompt}, {emitEvent: false});
    }

    private buildAutoPrompt(config: MusicStyleChooserConfig, isInstrumental: boolean): string {
        const basePrompt = this.styleChooserService.generateSunoStylePrompt(config, isInstrumental);

        const parts: string[] = [];
        if (basePrompt) parts.push(basePrompt);
        const bpm = this.styleForm.get('bpm')?.value;
        if (bpm) parts.push(`${bpm} BPM`);
        if (isInstrumental) parts.push('Instrumental');
        const mixChar = this.styleForm.get('mix_character')?.value?.trim();
        if (mixChar) parts.push(mixChar);

        return parts.join(', ');
    }

    onStyleChooserChanged(): void {
        const config = this.styleChooserService.getConfig();
        const isInstrumental = this.templateForm.get('is_instrumental')?.value || false;
        this.mapConfigToStyleForm(config, isInstrumental);
        this.regenerateStylePrompt();
        if (this.isEditorMode && this.currentTemplateId) this.autoSave();
    }

    onApplyStyles(): void {
        const config = this.styleChooserService.getConfig();
        const isInstrumental = this.templateForm.get('is_instrumental')?.value || false;
        this.mapConfigToStyleForm(config, isInstrumental);
        this.currentMode = 'auto';
        this.regenerateStylePrompt();
        if (this.isEditorMode && this.currentTemplateId) this.autoSave();
    }

    toggleMode(): void {
        if (this.currentMode === 'auto') {
            this.currentMode = 'manual';
        } else {
            this.currentMode = 'auto';
            this.regenerateStylePrompt();
        }
    }

    private mapConfigToStyleForm(config: MusicStyleChooserConfig, isInstrumental: boolean): void {
        const genre = (config.selectedStyles || []).join(', ');

        let instruments = config.selectedInstruments || [];
        if (isInstrumental) {
            instruments = instruments.filter(i => i !== 'male-voice' && i !== 'female-voice' && i !== 'vocals');
        }
        const voiceInstruments = instruments.filter(i => i === 'male-voice' || i === 'female-voice');
        const otherInstruments = instruments.filter(i => i !== 'male-voice' && i !== 'female-voice');

        const vocalType = voiceInstruments
            .map(v => v.replace('-voice', '') + ' vocals')
            .join(', ');
        const instrumentsStr = otherInstruments
            .map(i => i.replace(/-/g, ' '))
            .join(', ');

        const mood = (config.selectedThemes || []).join(', ');

        this.styleForm.patchValue({
            genre,
            vocal_type: vocalType,
            instruments: instrumentsStr,
            mood,
        }, {emitEvent: false});
    }

    private restoreStyleChooserFromFields(t: any): void {
        const config: MusicStyleChooserConfig = {
            selectedStyles: t.genre ? t.genre.split(', ').filter((s: string) => s) : [],
            selectedInstruments: [],
            selectedThemes: t.mood ? t.mood.split(', ').filter((s: string) => s) : [],
            lastModified: new Date(),
        };

        // Restore instruments from vocal_type + instruments fields
        if (t.vocal_type) {
            const vocals = t.vocal_type.split(', ');
            for (const v of vocals) {
                if (v.includes('male')) config.selectedInstruments.push('male-voice');
                else if (v.includes('female')) config.selectedInstruments.push('female-voice');
            }
        }
        if (t.instruments) {
            const insts = t.instruments.split(', ').filter((s: string) => s);
            for (const inst of insts) {
                config.selectedInstruments.push(inst.replace(/\s+/g, '-'));
            }
        }

        this.styleChooserService.saveConfig(config);
        if (this.styleChooser) {
            this.styleChooser.loadConfig();
            this.styleChooser.isInstrumental = t.is_instrumental || false;
            this.styleChooser.filterInstrumentsForMode();
        }
    }

    // ===== AI Actions =====

    async enhanceSunoPrompt(): Promise<void> {
        const currentPrompt = this.styleForm.get('style_prompt')?.value?.trim();
        if (!currentPrompt) return;

        let gender: "male" | "female" | undefined;
        const lower = currentPrompt.toLowerCase();
        if (lower.includes('male vocal') || lower.includes('male-voice')) gender = 'male';
        else if (lower.includes('female vocal') || lower.includes('female-voice')) gender = 'female';

        this.currentMode = 'manual';
        this.isEnhancingPrompt = true;
        try {
            const enhanced = await this.progressService.executeWithProgress(
                () => this.chatService.improveMusicStylePromptForSuno(currentPrompt, gender),
                this.translate.instant('sunoEnhancer.progress.enhancing'),
                this.translate.instant('sunoEnhancer.progress.enhancingHint'),
            );
            this.styleForm.patchValue({style_prompt: this.removeQuotes(enhanced)});
        } catch (error: any) {
            this.notificationService.error(error.message);
        } finally {
            this.isEnhancingPrompt = false;
        }
    }

    async translatePrompt(): Promise<void> {
        const currentPrompt = this.styleForm.get('style_prompt')?.value?.trim();
        if (!currentPrompt) return;

        this.currentMode = 'manual';
        this.isTranslatingPrompt = true;
        try {
            const translated = await this.progressService.executeWithProgress(
                () => this.chatService.translateMusicStylePrompt(currentPrompt),
                this.translate.instant('sunoEnhancer.progress.translating'),
                this.translate.instant('sunoEnhancer.progress.translatingHint'),
            );
            this.styleForm.patchValue({style_prompt: this.removeQuotes(translated)});
        } catch (error: any) {
            this.notificationService.error(error.message);
        } finally {
            this.isTranslatingPrompt = false;
        }
    }

    private removeQuotes(text: string): string {
        if (!text) return text;
        return text.replace(/^["']|["']$/g, '').trim();
    }

    // ===== Preview =====

    togglePreview(): void {
        this.isPreviewMode = !this.isPreviewMode;
        if (this.isPreviewMode) {
            this.updatePreview();
        }
    }

    private updatePreview(): void {
        const lyrics = this.templateForm.get('enhanced_lyrics')?.value || '';
        // Highlight tags as colored badges
        this.previewHtml = lyrics
            .replace(/\[([^\]]+)\]/g, '<span class="suno-tag-badge">[$1]</span>')
            .replace(/\n/g, '<br>');
    }

    // ===== Character Counters =====

    get lyricsLength(): number {
        return (this.templateForm.get('enhanced_lyrics')?.value || '').length;
    }

    get stylePromptLength(): number {
        return (this.styleForm.get('style_prompt')?.value || '').length;
    }

    get lyricsStatus(): 'ok' | 'warning' | 'danger' {
        if (this.lyricsLength >= this.LYRICS_LIMIT) return 'danger';
        if (this.lyricsLength >= this.LYRICS_WARNING) return 'warning';
        return 'ok';
    }

    get stylePromptStatus(): 'ok' | 'warning' | 'danger' {
        if (this.stylePromptLength >= this.STYLE_LIMIT) return 'danger';
        if (this.stylePromptLength >= this.STYLE_WARNING) return 'warning';
        return 'ok';
    }

    // ===== Copy to Clipboard =====

    async copyLyrics(): Promise<void> {
        const lyrics = this.templateForm.get('enhanced_lyrics')?.value || '';
        await navigator.clipboard.writeText(lyrics);
    }

    async copyStylePrompt(): Promise<void> {
        const prompt = this.styleForm.get('style_prompt')?.value || '';
        await navigator.clipboard.writeText(prompt);
    }

    async copyAll(): Promise<void> {
        const lyrics = this.templateForm.get('enhanced_lyrics')?.value || '';
        const prompt = this.styleForm.get('style_prompt')?.value || '';
        const combined = `LYRICS:\n${lyrics}\n\nSTYLE PROMPT:\n${prompt}`;
        await navigator.clipboard.writeText(combined);
    }
}
