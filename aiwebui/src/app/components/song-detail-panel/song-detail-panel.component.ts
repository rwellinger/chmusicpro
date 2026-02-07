import {
    Component,
    ElementRef,
    EventEmitter,
    inject,
    Input,
    OnChanges,
    OnInit,
    Output,
    SimpleChanges,
    ViewChild
} from "@angular/core";
import {CommonModule} from "@angular/common";
import {FormsModule} from "@angular/forms";
import {HttpClient} from "@angular/common/http";
import {firstValueFrom} from "rxjs";
import {TranslateModule, TranslateService} from "@ngx-translate/core";
import {SongService} from "../../services/business/song.service";
import {NotificationService} from "../../services/ui/notification.service";
import {ApiConfigService} from "../../services/config/api-config.service";
import {ResourceBlobService} from "../../services/ui/resource-blob.service";
import {MUSIC_STYLE_CATEGORIES} from "../../models/music-style-chooser.model";

@Component({
    selector: "app-song-detail-panel",
    standalone: true,
    imports: [CommonModule, FormsModule, TranslateModule],
    templateUrl: "./song-detail-panel.component.html",
    styleUrl: "./song-detail-panel.component.scss"
})
export class SongDetailPanelComponent implements OnInit, OnChanges {
    @Input() song: any = null;
    @Input() songId: string | null = null;
    @Input() showEditTitle: boolean = true;
    @Input() showEditTags: boolean = true;
    @Input() showEditWorkflow: boolean = true;
    @Input() showRating: boolean = true;
    @Input() title: string = "Song Details";
    @Input() showMetaInfo: string[] = ["job_id", "model", "status", "created", "completed"];
    @Input() placeholderText: string = "Select a song from the list to view details";
    @Input() placeholderIcon: string = "fas fa-music";
    @Input() currentlyPlayingId: string | null = null;
    @Input() isGenerating: boolean = false;

    // Component state
    isLoading = false;
    loadingError: string | null = null;


    @Output() titleChanged = new EventEmitter<string>();
    @Output() tagsChanged = new EventEmitter<string[]>();
    @Output() workflowChanged = new EventEmitter<string>();
    @Output() downloadFlac = new EventEmitter<string>();
    @Output() playAudio = new EventEmitter<{ url: string, id: string, choiceNumber: number }>();
    @Input() currentlyPlaying: string | null = null;
    @Output() downloadStems = new EventEmitter<string>();
    @Output() copyLyrics = new EventEmitter<void>();
    @Output() updateRating = new EventEmitter<{ choiceId: string, rating: number | null }>();

    @ViewChild("titleInput") titleInput!: ElementRef;
    @ViewChild("lyricsTextarea") lyricsTextarea!: ElementRef;

    // Services
    private songService = inject(SongService);
    private notificationService = inject(NotificationService);
    private apiConfigService = inject(ApiConfigService);
    private resourceBlobService = inject(ResourceBlobService);
    private http = inject(HttpClient);
    private translate = inject(TranslateService);

    // Component state
    editingTitle = false;
    editTitleValue = "";
    editingTags = false;
    selectedTags: string[] = [];
    editingWorkflow = false;
    selectedWorkflow = "";
    showLyricsDialog = false;

    // Tag categories from shared constants
    tagCategories = MUSIC_STYLE_CATEGORIES;

    // Workflow options - will be initialized in ngOnInit with translated labels
    workflowOptions: { value: string; label: string }[] = [];

    // Title editing methods
    startEditTitle() {
        if (!this.showEditTitle || !this.song) return;
        this.editingTitle = true;
        this.editTitleValue = this.getDisplayTitle(this.song);
        setTimeout(() => {
            this.titleInput?.nativeElement?.focus();
        });
    }

    async saveTitle() {
        if (!this.song || !this.songId) return;

        try {
            await firstValueFrom(
                this.http.put<any>(this.apiConfigService.endpoints.song.update(this.songId), {
                    title: this.editTitleValue.trim()
                })
            );

            this.editingTitle = false;
            this.titleChanged.emit(this.editTitleValue);

            // Auto-refresh to show updated data
            await this.reloadSong();

        } catch (error: any) {
            this.notificationService.error(`${this.translate.instant("songDetailPanel.errors.updateTitle")}: ${error.message}`);
        }
    }

    cancelEditTitle() {
        this.editingTitle = false;
        this.editTitleValue = "";
    }

    // Tags editing methods
    startEditTags() {
        if (!this.showEditTags || !this.song) return;
        this.editingTags = true;
        this.selectedTags = this.song.tags ? this.song.tags.split(",").map((tag: string) => tag.trim()) : [];
    }

    async saveTags() {
        if (!this.song || !this.songId) return;

        try {
            await firstValueFrom(
                this.http.put<any>(this.apiConfigService.endpoints.song.update(this.songId), {
                    tags: this.selectedTags
                })
            );

            this.editingTags = false;
            this.tagsChanged.emit(this.selectedTags);

            // Auto-refresh to show updated data
            await this.reloadSong();

        } catch (error: any) {
            this.notificationService.error(`${this.translate.instant("songDetailPanel.errors.updateTags")}: ${error.message}`);
        }
    }

    cancelEditTags() {
        this.editingTags = false;
        this.selectedTags = [];
    }

    toggleTag(tag: string) {
        const index = this.selectedTags.indexOf(tag);
        if (index > -1) {
            this.selectedTags.splice(index, 1);
        } else {
            this.selectedTags.push(tag);
        }
    }

    isTagSelected(tag: string): boolean {
        return this.selectedTags.includes(tag);
    }

    getSelectedTagsDisplay(): string {
        if (!this.song?.tags) return this.translate.instant("songDetailPanel.tags.noTags");
        return this.song.tags;
    }

    // Workflow editing methods
    startEditWorkflow() {
        if (!this.showEditWorkflow || !this.song) return;
        this.editingWorkflow = true;
        this.selectedWorkflow = this.song.workflow || "";
    }

    async saveWorkflow() {
        if (!this.song || !this.songId) return;

        try {
            await firstValueFrom(
                this.http.put<any>(this.apiConfigService.endpoints.song.update(this.songId), {
                    workflow: this.selectedWorkflow
                })
            );

            this.editingWorkflow = false;
            this.workflowChanged.emit(this.selectedWorkflow);

            // Auto-refresh to show updated data
            await this.reloadSong();

        } catch (error: any) {
            this.notificationService.error(`${this.translate.instant("songDetailPanel.errors.updateWorkflow")}: ${error.message}`);
        }
    }

    cancelEditWorkflow() {
        this.editingWorkflow = false;
        this.selectedWorkflow = "";
    }

    getWorkflowDisplay(): string {
        if (!this.song?.workflow) return this.translate.instant("songDetailPanel.workflow.noWorkflow");
        const option = this.workflowOptions.find(opt => opt.value === this.song.workflow);
        return option?.label || this.song.workflow;
    }

    // Audio methods - emits events to parent (using authenticated blob URLs)
    onPlayAudio(choiceId: string, id: string, choiceNumber: number) {
        // Use backend proxy endpoint with JWT auth → Convert to blob URL
        const backendUrl = this.apiConfigService.endpoints.song.choiceMp3(choiceId);

        // Load blob URL with authentication and emit to parent
        this.resourceBlobService.getResourceBlobUrl(backendUrl).subscribe({
            next: (blobUrl) => {
                if (blobUrl) {
                    this.playAudio.emit({url: blobUrl, id, choiceNumber});
                }
            },
            error: (error) => {
                console.error("Failed to load audio:", error);
                this.notificationService.error(this.translate.instant("songDetailPanel.errors.loadAudio"));
            }
        });
    }

    onDownloadFlac(choiceId: string) {
        // Use authenticated download via ResourceBlobService
        const backendUrl = this.apiConfigService.endpoints.song.choiceFlac(choiceId);
        this.resourceBlobService.downloadResource(backendUrl, `song-choice-${choiceId}.flac`);
    }

    onDownloadWav(choiceId: string) {
        // Use authenticated download via ResourceBlobService
        const backendUrl = this.apiConfigService.endpoints.song.choiceWav(choiceId);
        this.resourceBlobService.downloadResource(backendUrl, `song-choice-${choiceId}.wav`);
    }

    onDownloadStems(choiceId: string) {
        // Use authenticated download via ResourceBlobService
        const backendUrl = this.apiConfigService.endpoints.song.choiceStems(choiceId);
        this.resourceBlobService.downloadResource(backendUrl, `song-choice-${choiceId}-stems.zip`);
    }

    async onUpdateRating(choiceId: string, rating: number | null) {
        try {
            await this.songService.updateChoiceRating(choiceId, rating);

            this.updateRating.emit({choiceId, rating});

            // Auto-refresh to show updated rating
            await this.reloadSong();

        } catch (error: any) {
            console.error("Rating update error:", error);
            this.notificationService.error(`${this.translate.instant("songDetailPanel.errors.updateRating")}: ${error.message}`);
        }
    }

    // Lyrics methods
    openLyricsDialog() {
        this.showLyricsDialog = true;
    }

    closeLyricsDialog() {
        this.showLyricsDialog = false;
    }

    copyLyricsToClipboard() {
        this.copyLyrics.emit();
    }

    // Utility methods
    getDisplayTitle(song: any): string {
        if (!song) return "";
        return song.title || song.lyrics?.slice(0, 50) + (song.lyrics?.length > 50 ? "..." : "") || this.translate.instant("songDetailPanel.untitled");
    }

    formatDateDetailed(dateString: string): string {
        if (!dateString) return "";
        return new Date(dateString).toLocaleDateString("de-DE", {
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit"
        });
    }

    formatDuration(createdAt: string, completedAt: string): string {
        if (!createdAt || !completedAt) return "";

        const created = new Date(createdAt);
        const completed = new Date(completedAt);
        const diffMs = completed.getTime() - created.getTime();

        if (diffMs < 0) return "";

        const totalMinutes = Math.floor(diffMs / (1000 * 60));
        const hours = Math.floor(totalMinutes / 60);
        const minutes = totalMinutes % 60;

        if (hours > 0) {
            return `${hours.toString().padStart(2, "0")}:${minutes.toString().padStart(2, "0")}h`;
        } else {
            return `${minutes.toString().padStart(2, "0")}:${Math.floor((diffMs % (1000 * 60)) / 1000).toString().padStart(2, "0")}m`;
        }
    }

    formatDateShort(dateString: string): string {
        if (!dateString) return "";
        return new Date(dateString).toLocaleDateString("de-DE");
    }

    shouldShowMetaInfo(type: string): boolean {
        return this.showMetaInfo.includes(type);
    }

    ngOnInit() {
        // Initialize workflow options with translated labels
        this.workflowOptions = [
            {value: "", label: this.translate.instant("songDetailPanel.workflow.noWorkflow")},
            {value: "inUse", label: this.translate.instant("songDetailPanel.workflow.inUse")},
            {value: "onWork", label: this.translate.instant("songDetailPanel.workflow.onWork")},
            {value: "notUsed", label: this.translate.instant("songDetailPanel.workflow.notUsed")},
            {value: "fail", label: this.translate.instant("songDetailPanel.workflow.fail")}
        ];

        if (this.songId) {
            this.loadSongFromDB(this.songId);
        }
    }

    ngOnChanges(changes: SimpleChanges) {
        if (changes["songId"] && this.songId && this.songId !== changes["songId"].previousValue) {
            this.loadSongFromDB(this.songId);
        }
    }

    public async reloadSong() {
        if (this.songId) {
            await this.loadSongFromDB(this.songId);
        }
    }

    private async loadSongFromDB(songId: string) {
        this.isLoading = true;
        this.loadingError = null;

        try {
            const response = await this.songService.getSongById(songId);
            if (response && (response as any).data) {
                this.song = (response as any).data;
            } else {
                this.song = response;
            }
        } catch (error: any) {
            this.loadingError = `${this.translate.instant("songDetailPanel.errors.loadSong")}: ${error.message}`;
            this.notificationService.error(`${this.translate.instant("songDetailPanel.errors.loadSongDetails")}: ${error.message}`);
            this.song = null;
        } finally {
            this.isLoading = false;
        }
    }

    // Check if a song is instrumental
    isInstrumental(song: any): boolean {
        return song?.is_instrumental === true;
    }

    // Get the appropriate icon class for a song
    getSongIcon(song: any): string {
        return this.isInstrumental(song) ? "fa-guitar" : "fa-microphone";
    }

    // Get the song type display text
    getSongTypeText(song: any): string {
        return this.isInstrumental(song)
            ? this.translate.instant("songDetailPanel.type.instrumental")
            : this.translate.instant("songDetailPanel.type.withVocals");
    }

    // === Copy to Clipboard ===

    copyToClipboard(text: string): void {
        if (!text) return;

        navigator.clipboard.writeText(text).then(() => {
            this.notificationService.success(this.translate.instant("songDetailPanel.idCopied"));
        }).catch(err => {
            console.error("Failed to copy to clipboard:", err);
            this.notificationService.error(this.translate.instant("songDetailPanel.errors.copyFailed"));
        });
    }
}
