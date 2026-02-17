import {inject, Injectable} from "@angular/core";
import {HttpClient} from "@angular/common/http";
import {firstValueFrom} from "rxjs";
import {ApiConfigService} from "../config/api-config.service";

/**
 * FileIgnoreService - Filters files based on .chmusicproignore patterns.
 * Loads patterns from backend API, falls back to hardcoded defaults.
 */
@Injectable({
    providedIn: "root"
})
export class FileIgnoreService {
    private readonly http = inject(HttpClient);
    private readonly apiConfig = inject(ApiConfigService);

    private patterns: string[] | null = null;

    private readonly fallbackPatterns: string[] = [
        ".DS_Store", ".AppleDouble", ".LSOverride", "Icon*", "._*",
        "Thumbs.db",
        "*.tmp", "*.temp", "*.swp", "*.swo", "*~",
        ".git/", ".svn/", ".hg/",
        ".vscode/", ".idea/", "*.sublime-*",
        "node_modules/", "dist/", "build/", "*.pyc", "__pycache__/",
        "Cache/", "*.csh", "autosave/"
    ];

    async loadPatterns(): Promise<void> {
        if (this.patterns !== null) return;

        try {
            const response = await firstValueFrom(
                this.http.get<{ data: { patterns: string[] } }>(this.apiConfig.endpoints.config.ignorePatterns)
            );
            const loaded = response?.data?.patterns;
            this.patterns = loaded && loaded.length > 0 ? loaded : this.fallbackPatterns;
        } catch {
            this.patterns = this.fallbackPatterns;
        }
    }

    private getPatterns(): string[] {
        return this.patterns ?? this.fallbackPatterns;
    }

    shouldIgnore(relativePath: string): boolean {
        const segments = relativePath.split("/");
        const filename = segments[segments.length - 1];

        for (const pattern of this.getPatterns()) {
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
