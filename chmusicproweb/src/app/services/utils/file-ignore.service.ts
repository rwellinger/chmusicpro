import {Injectable} from "@angular/core";

/**
 * FileIgnoreService - Filters files based on .chmusicproignore patterns.
 * Hardcoded default patterns from .chmusicproignore.default.
 */
@Injectable({
    providedIn: "root"
})
export class FileIgnoreService {
    private readonly defaultPatterns: string[] = [
        // macOS system files
        ".DS_Store", ".AppleDouble", ".LSOverride", "Icon*", "._*",
        // Windows
        "Thumbs.db", "desktop.ini",
        // Temporary files
        "*.tmp", "*.temp", "*.swp", "*.swo", "*~", "*.bak",
        // Version control
        ".git/", ".svn/", ".hg/", ".gitignore", ".gitattributes",
        // IDE / Editor
        ".vscode/", ".idea/", "*.sublime-*", "*.code-workspace",
        // Build artifacts
        "node_modules/", "dist/", "build/", "*.pyc", "__pycache__/", ".cache/",
        // Logs
        "*.log", "logs/",
        // Environment files
        ".env", ".env.local", "*.secret"
    ];

    shouldIgnore(relativePath: string): boolean {
        const segments = relativePath.split("/");
        const filename = segments[segments.length - 1];

        for (const pattern of this.defaultPatterns) {
            // Directory pattern (ending with /)
            if (pattern.endsWith("/")) {
                const dirName = pattern.slice(0, -1);
                if (segments.some(seg => this.matchGlob(seg, dirName))) {
                    return true;
                }
                continue;
            }

            // File pattern: match against filename
            if (this.matchGlob(filename, pattern)) {
                return true;
            }
        }

        return false;
    }

    filterFiles(files: { file: File; relativePath: string }[]): {
        accepted: { file: File; relativePath: string }[];
        ignored: { file: File; relativePath: string }[];
    } {
        const accepted: { file: File; relativePath: string }[] = [];
        const ignored: { file: File; relativePath: string }[] = [];

        for (const entry of files) {
            if (this.shouldIgnore(entry.relativePath)) {
                ignored.push(entry);
            } else {
                accepted.push(entry);
            }
        }

        return {accepted, ignored};
    }

    /**
     * Simple glob matching: supports * (any chars except /) and ? (single char).
     */
    private matchGlob(text: string, pattern: string): boolean {
        let regexStr = "^";
        for (const char of pattern) {
            if (char === "*") {
                regexStr += "[^/]*";
            } else if (char === "?") {
                regexStr += "[^/]";
            } else if (".+^${}()|[]\\".includes(char)) {
                regexStr += "\\" + char;
            } else {
                regexStr += char;
            }
        }
        regexStr += "$";

        return new RegExp(regexStr).test(text);
    }
}
