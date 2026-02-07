import {inject, Injectable} from "@angular/core";
import {Conversation, Message} from "../../models/conversation.model";
import {ConversationService} from "./conversation.service";
import {firstValueFrom} from "rxjs";

@Injectable({
    providedIn: "root"
})
export class ChatExportService {
    private conversationService = inject(ConversationService);

    /**
     * Export conversation to Markdown format
     */
    public exportToMarkdown(conversation: Conversation, messages: Message[]): void {
        const content = this.generateMarkdownContent(conversation, messages);
        const filename = this.generateFilename(conversation.title, "md");
        this.downloadFile(content, filename, "text/markdown");
    }

    /**
     * Export conversation with full history (including archived messages, excluding summaries)
     */
    public async exportFullToMarkdown(conversationId: string, conversationTitle: string): Promise<void> {
        try {
            // Fetch full conversation including archived messages
            const response = await firstValueFrom(
                this.conversationService.getConversationForExport(conversationId)
            );

            // Filter out summary messages (we only want original messages)
            const messages = response.messages.filter((msg: any) => !msg.is_summary);

            const content = this.generateMarkdownContent(response.conversation, messages);
            const filename = this.generateFilename(conversationTitle, "md");
            this.downloadFile(content, filename, "text/markdown");
        } catch (error) {
            console.error("Error exporting full conversation:", error);
            throw error;
        }
    }

    /**
     * Generate markdown content from conversation
     */
    private generateMarkdownContent(conversation: Conversation, messages: Message[]): string {
        let content = "";

        // Header
        content += `# ${conversation.title}\n\n`;

        // Metadata
        content += `**Model:** ${conversation.model}\n\n`;
        content += `**Provider:** ${conversation.provider || "internal"}\n\n`;
        content += `**Created:** ${new Date(conversation.created_at).toLocaleString("de-DE")}\n\n`;

        if (conversation.current_token_count && conversation.context_window_size) {
            content += `**Tokens:** ${conversation.current_token_count} / ${conversation.context_window_size}\n\n`;
        }

        // System Context
        if (conversation.system_context) {
            content += `## System Context\n\n`;
            content += `${conversation.system_context}\n\n`;
        }

        // Separator
        content += `---\n\n`;

        // Messages
        content += `## Messages\n\n`;

        for (const message of messages) {
            // Skip system messages
            if (message.role === "system") continue;

            const roleLabel = message.role === "user" ? "**USER**" : "**ASSISTANT**";
            const timestamp = new Date(message.created_at).toLocaleString("de-DE");

            content += `### ${roleLabel} _(${timestamp})_\n\n`;
            content += `${message.content}\n\n`;
            content += `---\n\n`;
        }

        return content;
    }

    /**
     * Generate filename with sanitized title
     */
    private generateFilename(title: string, extension: string): string {
        const sanitizedTitle = title
            .replace(/[^a-zA-Z0-9äöüÄÖÜß\s-]/g, "")
            .replace(/\s+/g, "-")
            .substring(0, 50);

        const date = new Date().toISOString().split("T")[0];
        return `chat-${sanitizedTitle}-${date}.${extension}`;
    }

    /**
     * Download file with given content
     */
    private downloadFile(content: string, filename: string, mimeType: string): void {
        const blob = new Blob([content], {type: mimeType});
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = filename;
        link.click();
        window.URL.revokeObjectURL(url);
    }
}
