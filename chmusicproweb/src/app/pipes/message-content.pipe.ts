import {inject, Pipe, PipeTransform, SecurityContext} from "@angular/core";
import {DomSanitizer, SafeHtml} from "@angular/platform-browser";
import {marked, Renderer} from "marked";
import hljs from "highlight.js";
import {HtmlToTextService} from "../services/utils/html-to-text.service";

/**
 * Pipe to render markdown content with syntax highlighting
 */
@Pipe({
    name: "messageContent",
    standalone: true
})
export class MessageContentPipe implements PipeTransform {
    private renderer: Renderer;
    private htmlToTextService = inject(HtmlToTextService);
    private sanitizer = inject(DomSanitizer);

    constructor() {
        // Create custom renderer for code blocks
        this.renderer = new Renderer();

        // Override code block rendering with proper token signature
        this.renderer.code = (token: { text: string; lang?: string; escaped?: boolean }): string => {
            const code = token.text;
            const language = token.lang;

            if (language && hljs.getLanguage(language)) {
                try {
                    const highlighted = hljs.highlight(code, {language}).value;
                    return `<pre><code class="hljs language-${language}">${highlighted}</code></pre>`;
                } catch (err) {
                    console.error("Highlight error:", err);
                }
            }

            try {
                const highlighted = hljs.highlightAuto(code).value;
                return `<pre><code class="hljs">${highlighted}</code></pre>`;
            } catch (err) {
                console.error("Auto-highlight error:", err);
                return `<pre><code>${code}</code></pre>`;
            }
        };

        // Configure marked
        marked.setOptions({
            renderer: this.renderer,
            breaks: true, // Convert \n to <br>
            gfm: true // GitHub Flavored Markdown
        });
    }

    transform(value: string): SafeHtml {
        if (!value) return "";

        try {
            // Parse markdown to HTML
            const html = marked.parse(value) as string;

            // Sanitize and return safe HTML
            return this.sanitizer.sanitize(SecurityContext.HTML, html) || "";
        } catch (err) {
            console.error("Markdown parsing error:", err);
            return value; // Return original value on error
        }
    }

    /**
     * Convert markdown to plain text (for clipboard)
     */
    toPlainText(markdown: string): string {
        if (!markdown) return "";

        try {
            // Parse markdown to HTML
            const html = marked.parse(markdown) as string;

            // Convert HTML to plain text
            return this.htmlToTextService.convert(html);
        } catch (err) {
            console.error("Markdown to text conversion error:", err);
            return markdown; // Return original markdown on error
        }
    }
}
