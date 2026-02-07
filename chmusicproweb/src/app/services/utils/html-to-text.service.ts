import {Injectable} from "@angular/core";

/**
 * Service to convert HTML to plain text while preserving structure
 */
@Injectable({
    providedIn: "root"
})
export class HtmlToTextService {
    /**
     * Convert HTML to plain text with preserved structure
     */
    public convert(html: string): string {
        if (!html) return "";

        const tempDiv = document.createElement("div");
        tempDiv.innerHTML = html;

        return this.processNode(tempDiv).trim();
    }

    /**
     * Recursively process HTML nodes and convert to text
     */
    private processNode(node: Node): string {
        let text = "";

        if (node.nodeType === Node.TEXT_NODE) {
            // Text node - return content
            return node.textContent || "";
        }

        if (node.nodeType !== Node.ELEMENT_NODE) {
            return "";
        }

        const element = node as HTMLElement;
        const tagName = element.tagName.toLowerCase();

        // Process children first
        const childText = Array.from(element.childNodes)
            .map(child => this.processNode(child))
            .join("");

        switch (tagName) {
            case "p":
                text = childText + "\n\n";
                break;

            case "br":
                text = "\n";
                break;

            case "h1":
            case "h2":
            case "h3":
            case "h4":
            case "h5":
            case "h6":
                text = "\n" + childText + "\n\n";
                break;

            case "ul":
            case "ol":
                text = "\n" + childText + "\n";
                break;

            case "li": {
                // Get parent to determine bullet type
                const parent = element.parentElement;
                const isOrdered = parent?.tagName.toLowerCase() === "ol";
                const indent = this.getIndentLevel(element);
                const indentStr = "  ".repeat(indent);

                if (isOrdered) {
                    const index = Array.from(parent?.children || []).indexOf(element) + 1;
                    text = indentStr + index + ". " + childText.trim() + "\n";
                } else {
                    text = indentStr + "• " + childText.trim() + "\n";
                }
                break;
            }

            case "blockquote":
                text = "\n" + childText.split("\n").map(line => "> " + line).join("\n") + "\n";
                break;

            case "code":
                // Inline code
                if (element.parentElement?.tagName.toLowerCase() !== "pre") {
                    text = childText;
                } else {
                    // Code block (handled by pre)
                    text = childText;
                }
                break;

            case "pre":
                text = "\n" + childText + "\n\n";
                break;

            case "table":
                text = "\n" + this.convertTable(element as HTMLTableElement) + "\n";
                break;

            case "hr":
                text = "\n---\n\n";
                break;

            case "strong":
            case "b":
            case "em":
            case "i":
            case "a":
            case "span":
            case "div":
                // Just return text content without formatting
                text = childText;
                break;

            default:
                text = childText;
        }

        return text;
    }

    /**
     * Get indentation level for nested lists
     */
    private getIndentLevel(element: HTMLElement): number {
        let level = 0;
        let parent = element.parentElement;

        while (parent) {
            if (parent.tagName.toLowerCase() === "ul" || parent.tagName.toLowerCase() === "ol") {
                level++;
            }
            parent = parent.parentElement;
        }

        return level - 1; // Subtract 1 because direct parent is already counted
    }

    /**
     * Convert HTML table to plain text
     * Uses simple tab-separated format
     */
    private convertTable(table: HTMLTableElement): string {
        const rows: string[][] = [];

        // Process all rows
        const tableRows = Array.from(table.querySelectorAll("tr"));

        for (const row of tableRows) {
            const cells = Array.from(row.querySelectorAll("th, td"));
            const cellTexts = cells.map(cell => (cell.textContent || "").trim());
            rows.push(cellTexts);
        }

        if (rows.length === 0) return "";

        // Calculate column widths
        const colWidths: number[] = [];
        for (const row of rows) {
            for (let i = 0; i < row.length; i++) {
                colWidths[i] = Math.max(colWidths[i] || 0, row[i].length);
            }
        }

        // Format rows with padding
        const formattedRows = rows.map(row => {
            return row.map((cell, i) => cell.padEnd(colWidths[i], " ")).join("    ");
        });

        // Add separator after header (first row)
        if (formattedRows.length > 1) {
            const separator = colWidths.map(width => "-".repeat(width)).join("    ");
            formattedRows.splice(1, 0, separator);
        }

        return formattedRows.join("\n");
    }
}
