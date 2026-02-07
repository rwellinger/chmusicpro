import {Component, ElementRef, inject, OnDestroy, OnInit, ViewChild} from "@angular/core";
import {CommonModule} from "@angular/common";
import {FormsModule} from "@angular/forms";
import {Subject, takeUntil} from "rxjs";
import {MatSnackBarModule} from "@angular/material/snack-bar";
import {MatCardModule} from "@angular/material/card";
import {MatButtonModule} from "@angular/material/button";
import {MatSelectModule} from "@angular/material/select";
import {MatFormFieldModule} from "@angular/material/form-field";
import {MatInputModule} from "@angular/material/input";
import {MatIconModule} from "@angular/material/icon";
import {MatProgressSpinnerModule} from "@angular/material/progress-spinner";
import {MatExpansionModule} from "@angular/material/expansion";
import {MatProgressBarModule} from "@angular/material/progress-bar";
import {MatMenuModule} from "@angular/material/menu";
import {TranslateModule, TranslateService} from "@ngx-translate/core";

import {ConversationService} from "../../services/business/conversation.service";
import {NotificationService} from "../../services/ui/notification.service";
import {ChatExportService} from "../../services/business/chat-export.service";
import {Conversation, ConversationDetailResponse, Message, OllamaChatModel} from "../../models/conversation.model";
import {MessageContentPipe} from "../../pipes/message-content.pipe";

@Component({
    selector: "app-ai-chat",
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        MatSnackBarModule,
        MatCardModule,
        MatButtonModule,
        MatSelectModule,
        MatFormFieldModule,
        MatInputModule,
        MatIconModule,
        MatProgressSpinnerModule,
        MatExpansionModule,
        MatProgressBarModule,
        MatMenuModule,
        TranslateModule,
        MessageContentPipe
    ],
    templateUrl: "./ai-chat.component.html",
    styleUrl: "./ai-chat.component.scss"
})
export class AiChatComponent implements OnInit, OnDestroy {
    // Services
    private conversationService = inject(ConversationService);
    private notificationService = inject(NotificationService);
    private chatExportService = inject(ChatExportService);
    private translate = inject(TranslateService);
    private messageContentPipe = new MessageContentPipe();
    private destroy$ = new Subject<void>();

    // Data
    conversations: Conversation[] = [];
    currentConversation: Conversation | null = null;
    messages: Message[] = [];
    models: OllamaChatModel[] = [];

    // UI State
    isLoading = false;
    isSending = false;
    isLoadingModels = false;
    isCompressing = false;

    // Form State
    newChatTitle = "";
    selectedModel = "";
    systemContext = "";
    messageInput = "";

    // View State
    showNewChatForm = false;
    isEditingTitle = false;
    editTitleValue = "";
    showArchived = false;

    // Computed properties to avoid method calls in template
    formattedTokenCount = "";
    tokenPercentage = 0;

    @ViewChild("messagesContainer") private messagesContainer!: ElementRef;
    @ViewChild("messageInputField") private messageInputField!: ElementRef;

    ngOnInit(): void {
        this.loadConversations();

        // Load saved system context from localStorage
        this.systemContext = this.conversationService.loadSystemContext();
    }

    ngOnDestroy(): void {
        this.destroy$.next();
        this.destroy$.complete();
    }

    /**
     * Load available Ollama chat models (via cache)
     */
    private loadModels(): void {
        // Skip if models already loaded
        if (this.models.length > 0) {
            return;
        }

        this.isLoadingModels = true;
        this.conversationService
            .getChatModels()
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: (models) => {
                    this.models = models || [];
                    // Set default model if available
                    if (this.models.length > 0 && !this.selectedModel) {
                        // Find default model or use first
                        const defaultModel = this.models.find(m => m.is_default);
                        this.selectedModel = defaultModel ? defaultModel.name : this.models[0].name;
                    }
                },
                error: (error) => {
                    console.error("Error loading models:", error);
                    this.notificationService.error(this.translate.instant("aiChat.notifications.modelsFailed"));
                },
                complete: () => {
                    this.isLoadingModels = false;
                }
            });
    }

    /**
     * Load list of conversations (Ollama provider only)
     */
    public loadConversations(): void {
        this.isLoading = true;
        // archived: undefined = only non-archived, true = only archived
        const archived = this.showArchived ? true : undefined;
        this.conversationService
            .getConversations(0, 50, "internal", archived)
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: (response) => {
                    this.conversations = response.conversations;

                    // Auto-select first conversation if none selected
                    if (!this.currentConversation && this.conversations.length > 0) {
                        this.selectConversation(this.conversations[0]);
                    }
                },
                error: (error) => {
                    console.error("Error loading conversations:", error);
                    this.notificationService.error(this.translate.instant("aiChat.notifications.conversationsFailed"));
                },
                complete: () => {
                    this.isLoading = false;
                }
            });
    }

    /**
     * Select a conversation and load its messages
     */
    public selectConversation(conversation: Conversation): void {
        // Prevent re-loading if conversation is already active
        if (this.currentConversation?.id === conversation.id) {
            return;
        }

        this.isLoading = true;
        this.currentConversation = conversation;

        this.conversationService
            .getConversation(conversation.id)
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: (response: ConversationDetailResponse) => {
                    this.messages = response.messages;
                    this.currentConversation = response.conversation;
                    this.systemContext = response.conversation.system_context || "";
                    this.updateTokenDisplay(); // Update computed properties
                    setTimeout(() => this.scrollToBottom(), 100);
                },
                error: (error) => {
                    console.error("Error loading conversation:", error);
                    this.notificationService.error(this.translate.instant("aiChat.notifications.conversationFailed"));
                },
                complete: () => {
                    this.isLoading = false;
                }
            });
    }

    /**
     * Show new chat form
     */
    public showNewChat(): void {
        this.showNewChatForm = true;
        this.newChatTitle = "";
        // Load persisted system context
        this.systemContext = this.conversationService.loadSystemContext();
        // Lazy load models when needed
        this.loadModels();
    }

    /**
     * Cancel new chat creation
     */
    public cancelNewChat(): void {
        this.showNewChatForm = false;
        this.newChatTitle = "";
        // Keep system context - it persists across sessions
    }

    /**
     * Create new conversation (with provider: 'internal')
     */
    public createConversation(): void {
        if (!this.newChatTitle.trim() || !this.selectedModel) {
            this.notificationService.error(this.translate.instant("aiChat.notifications.titleModelRequired"));
            return;
        }

        this.isLoading = true;
        this.conversationService
            .createConversation({
                title: this.newChatTitle.trim(),
                model: this.selectedModel,
                system_context: this.systemContext.trim() || undefined,
                provider: "internal"
            })
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: (conversation) => {
                    this.conversations.unshift(conversation);
                    this.selectConversation(conversation);
                    this.showNewChatForm = false;
                    this.newChatTitle = "";
                },
                error: (error) => {
                    console.error("Error creating conversation:", error);
                    this.notificationService.error(this.translate.instant("aiChat.notifications.createFailed"));
                },
                complete: () => {
                    this.isLoading = false;
                }
            });
    }

    /**
     * Delete current conversation
     */
    public deleteConversation(): void {
        if (!this.currentConversation) return;

        if (!confirm(this.translate.instant("aiChat.notifications.deleteConfirm", {title: this.currentConversation.title}))) {
            return;
        }

        const conversationId = this.currentConversation.id;

        this.isLoading = true;
        this.conversationService
            .deleteConversation(conversationId)
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: () => {
                    this.conversations = this.conversations.filter(c => c.id !== conversationId);
                    this.currentConversation = null;
                    this.messages = [];

                    // Select first available conversation
                    if (this.conversations.length > 0) {
                        this.selectConversation(this.conversations[0]);
                    }
                },
                error: (error) => {
                    console.error("Error deleting conversation:", error);
                    this.notificationService.error(this.translate.instant("aiChat.notifications.deleteFailed"));
                },
                complete: () => {
                    this.isLoading = false;
                }
            });
    }

    /**
     * Send message in current conversation
     */
    public sendMessage(): void {
        if (!this.currentConversation || !this.messageInput.trim() || this.isSending || this.isCompressing) {
            return;
        }

        const content = this.messageInput.trim();
        this.messageInput = "";

        // Create temporary user message for optimistic UI
        const tempUserMessage: Message = {
            id: "temp-" + Date.now(),
            conversation_id: this.currentConversation.id,
            role: "user",
            content: content,
            token_count: undefined,
            created_at: new Date().toISOString()
        };

        // Add user message immediately (optimistic)
        this.messages.push(tempUserMessage);
        this.isSending = true;
        setTimeout(() => this.scrollToBottom(), 50);

        this.conversationService
            .sendMessage(this.currentConversation.id, content)
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: (response) => {
                    // Replace temporary user message with real one from backend
                    const tempIndex = this.messages.findIndex(m => m.id === tempUserMessage.id);
                    if (tempIndex !== -1) {
                        this.messages[tempIndex] = response.user_message;
                    }

                    // Add assistant message
                    this.messages.push(response.assistant_message);

                    // Update conversation with new token counts
                    this.currentConversation = response.conversation;
                    this.updateTokenDisplay(); // Update computed properties

                    setTimeout(() => this.scrollToBottom(), 100);
                    setTimeout(() => this.focusInput(), 200);
                },
                error: (error) => {
                    console.error("Error sending message:", error);
                    this.notificationService.error(this.translate.instant("aiChat.notifications.sendFailed"));

                    // Remove temporary message on error
                    this.messages = this.messages.filter(m => m.id !== tempUserMessage.id);

                    // Restore message input on error
                    this.messageInput = content;
                },
                complete: () => {
                    this.isSending = false;
                }
            });
    }

    /**
     * Handle Enter key in message input
     */
    public onMessageInputKeydown(event: KeyboardEvent): void {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            this.sendMessage();
        }
    }

    /**
     * Scroll messages to bottom
     */
    private scrollToBottom(): void {
        if (this.messagesContainer) {
            const container = this.messagesContainer.nativeElement;
            container.scrollTop = container.scrollHeight;
        }
    }

    /**
     * Focus message input field
     */
    private focusInput(): void {
        if (this.messageInputField) {
            this.messageInputField.nativeElement.focus();
        }
    }

    /**
     * Format date for display with relative time
     */
    public formatDate(dateString: string): string {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMinutes = Math.floor(diffMs / 60000);
        const diffDays = Math.floor(diffMs / 86400000);

        // < 1 Minute
        if (diffMinutes < 1) {
            return this.translate.instant("aiChat.time.justNow");
        }

        // < 60 Minutes
        if (diffMinutes < 60) {
            return this.translate.instant("aiChat.time.minAgo", {min: diffMinutes});
        }

        // Today
        const today = new Date();
        if (date.toDateString() === today.toDateString()) {
            return date.toLocaleTimeString("en-GB", {
                hour: "2-digit",
                minute: "2-digit"
            });
        }

        // Yesterday
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);
        if (date.toDateString() === yesterday.toDateString()) {
            return `${this.translate.instant("aiChat.time.yesterday")} ${date.toLocaleTimeString("en-GB", {
                hour: "2-digit",
                minute: "2-digit"
            })}`;
        }

        // < 7 Days - Show weekday
        if (diffDays < 7) {
            const weekday = date.toLocaleDateString("en-GB", {weekday: "long"});
            const time = date.toLocaleTimeString("en-GB", {
                hour: "2-digit",
                minute: "2-digit"
            });
            return `${weekday} ${time}`;
        }

        // Older - Show full date
        return date.toLocaleDateString("en-GB", {
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit"
        });
    }

    /**
     * Get message role class for styling
     */
    public getMessageClass(message: Message): string {
        return `message--${message.role}`;
    }

    /**
     * Handle system context changes and save to localStorage
     */
    public onSystemContextChange(): void {
        this.conversationService.saveSystemContext(this.systemContext);
    }

    /**
     * Clear saved system context
     */
    public clearSystemContext(): void {
        this.systemContext = "";
        this.conversationService.clearSystemContext();
    }

    /**
     * Update token display properties
     * Called when conversation changes to avoid method calls in template
     */
    private updateTokenDisplay(): void {
        if (!this.currentConversation?.context_window_size) {
            this.formattedTokenCount = "";
            this.tokenPercentage = 0;
            return;
        }

        // Update percentage
        const currentTokens = this.currentConversation.current_token_count || 0;
        const maxTokens = this.currentConversation.context_window_size;
        this.tokenPercentage = (currentTokens / maxTokens) * 100;

        // Update formatted count
        const format = (num: number): string => {
            if (num >= 1000) return `${(num / 1000).toFixed(1)}k`;
            return num.toString();
        };
        this.formattedTokenCount = `${format(currentTokens)} / ${format(maxTokens)}`;
    }

    /**
     * Get token usage percentage
     * @deprecated Use tokenPercentage property instead
     */
    public getTokenPercentage(): number {
        return this.tokenPercentage;
    }

    /**
     * Get formatted token count (e.g., "1.2k / 8k")
     * @deprecated Use formattedTokenCount property instead
     */
    public getFormattedTokenCount(): string {
        return this.formattedTokenCount;
    }

    /**
     * Get progress bar color based on usage
     */
    public getTokenProgressColor(): string {
        const percentage = this.getTokenPercentage();
        if (percentage >= 90) return "warn";
        if (percentage >= 70) return "accent";
        return "primary";
    }

    /**
     * Check if token warning should be shown
     */
    public shouldShowTokenWarning(): boolean {
        return this.getTokenPercentage() >= 90;
    }

    /**
     * Check if compression warning should be shown (85%+)
     */
    public shouldShowCompressionWarning(): boolean {
        const percentage = this.getTokenPercentage();
        return percentage >= 85 && percentage < 90;
    }

    /**
     * Compress conversation (archive old messages + create summary)
     */
    public compressConversation(): void {
        if (!this.currentConversation || this.isCompressing) return;

        const confirmed = confirm(this.translate.instant("aiChat.compression.confirmMessage"));

        if (!confirmed) return;

        this.isCompressing = true;
        this.conversationService
            .compressConversation(this.currentConversation.id)
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: (response) => {
                    this.notificationService.success(
                        this.translate.instant("aiChat.notifications.compressed", {count: response.archived_messages})
                    );
                    // Reload conversation to see updated token count
                    if (this.currentConversation) {
                        this.selectConversation(this.currentConversation);
                    }
                },
                error: (error) => {
                    console.error("Error compressing conversation:", error);
                    this.notificationService.error(this.translate.instant("aiChat.notifications.compressionFailed"));
                    this.isCompressing = false;
                },
                complete: () => {
                    this.isCompressing = false;
                }
            });
    }

    /**
     * Start editing conversation title
     */
    public startEditTitle(): void {
        if (!this.currentConversation) return;
        this.isEditingTitle = true;
        this.editTitleValue = this.currentConversation.title;
    }

    /**
     * Save edited title
     */
    public saveTitle(): void {
        if (!this.currentConversation || !this.editTitleValue.trim()) {
            this.cancelEditTitle();
            return;
        }

        const newTitle = this.editTitleValue.trim();
        if (newTitle === this.currentConversation.title) {
            this.cancelEditTitle();
            return;
        }

        this.conversationService
            .updateConversation(this.currentConversation.id, {title: newTitle})
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: (updatedConversation) => {
                    // Update current conversation
                    if (this.currentConversation) {
                        this.currentConversation.title = updatedConversation.title;
                    }

                    // Update in list
                    const convIndex = this.conversations.findIndex(c => c.id === updatedConversation.id);
                    if (convIndex !== -1) {
                        this.conversations[convIndex].title = updatedConversation.title;
                    }

                    this.isEditingTitle = false;
                    this.editTitleValue = "";
                },
                error: (error) => {
                    console.error("Error updating title:", error);
                    this.notificationService.error(this.translate.instant("aiChat.notifications.titleUpdateFailed"));
                    this.cancelEditTitle();
                }
            });
    }

    /**
     * Cancel title editing
     */
    public cancelEditTitle(): void {
        this.isEditingTitle = false;
        this.editTitleValue = "";
    }

    /**
     * Handle Enter key in title edit
     */
    public onTitleInputKeydown(event: KeyboardEvent): void {
        if (event.key === "Enter") {
            event.preventDefault();
            this.saveTitle();
        } else if (event.key === "Escape") {
            event.preventDefault();
            this.cancelEditTitle();
        }
    }

    /**
     * Copy message content to clipboard as plain text
     */
    public copyToClipboard(content: string): void {
        if (!content) return;

        // Convert markdown to plain text
        const plainText = this.messageContentPipe.toPlainText(content);

        navigator.clipboard.writeText(plainText)
            .then(() => {
                this.notificationService.success(this.translate.instant("aiChat.notifications.copiedPlainText"));
            })
            .catch((error) => {
                console.error("Error copying to clipboard:", error);
                this.notificationService.error(this.translate.instant("aiChat.notifications.copyFailed"));
            });
    }

    /**
     * Copy message content to clipboard as Markdown
     */
    public copyAsMarkdown(content: string): void {
        if (!content) return;

        navigator.clipboard.writeText(content)
            .then(() => {
                this.notificationService.success(this.translate.instant("aiChat.notifications.copiedMarkdown"));
            })
            .catch((error) => {
                console.error("Error copying to clipboard:", error);
                this.notificationService.error(this.translate.instant("aiChat.notifications.copyFailed"));
            });
    }

    /**
     * Export conversation to Markdown
     */
    public exportToMarkdown(): void {
        if (!this.currentConversation) return;

        try {
            this.chatExportService.exportToMarkdown(this.currentConversation, this.messages);
            this.notificationService.success(this.translate.instant("aiChat.notifications.exported"));
        } catch (error) {
            console.error("Error exporting to Markdown:", error);
            this.notificationService.error(this.translate.instant("aiChat.notifications.exportFailed"));
        }
    }

    /**
     * Export conversation with full history (including archived messages)
     */
    public async exportFullToMarkdown(): Promise<void> {
        if (!this.currentConversation) return;

        this.isLoading = true;
        try {
            await this.chatExportService.exportFullToMarkdown(
                this.currentConversation.id,
                this.currentConversation.title
            );
            this.notificationService.success(this.translate.instant("aiChat.notifications.exportedFull"));
        } catch (error) {
            console.error("Error exporting full chat history:", error);
            this.notificationService.error(this.translate.instant("aiChat.notifications.exportFullFailed"));
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * Toggle between showing archived and non-archived conversations
     */
    public toggleShowArchived(): void {
        this.showArchived = !this.showArchived;
        this.currentConversation = null;
        this.messages = [];
        this.loadConversations();
    }

    /**
     * Archive or unarchive the current conversation
     */
    public toggleArchive(): void {
        if (!this.currentConversation) return;

        const newArchivedState = !this.currentConversation.archived;

        this.conversationService
            .archiveConversation(this.currentConversation.id, newArchivedState)
            .pipe(takeUntil(this.destroy$))
            .subscribe({
                next: () => {
                    // Remove from current list
                    this.conversations = this.conversations.filter(c => c.id !== this.currentConversation?.id);
                    this.currentConversation = null;
                    this.messages = [];

                    // Select first available conversation
                    if (this.conversations.length > 0) {
                        this.selectConversation(this.conversations[0]);
                    }

                    const successKey = newArchivedState ? "aiChat.notifications.archived" : "aiChat.notifications.unarchived";
                    this.notificationService.success(this.translate.instant(successKey));
                },
                error: (error) => {
                    console.error(`Error ${newArchivedState ? "archive" : "unarchive"}:`, error);
                    const errorKey = newArchivedState ? "aiChat.notifications.archiveFailed" : "aiChat.notifications.unarchiveFailed";
                    this.notificationService.error(this.translate.instant(errorKey));
                }
            });
    }
}
