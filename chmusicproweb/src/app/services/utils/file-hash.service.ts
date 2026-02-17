import {Injectable} from "@angular/core";

/**
 * FileHashService - SHA-256 hashing of files using Web Crypto API.
 */
@Injectable({
    providedIn: "root"
})
export class FileHashService {
    /**
     * Hash a single file using SHA-256.
     * @returns hex string of the hash
     */
    async hashFile(file: File): Promise<string> {
        const buffer = await file.arrayBuffer();
        const hashBuffer = await crypto.subtle.digest("SHA-256", buffer);
        const hashArray = new Uint8Array(hashBuffer);
        return Array.from(hashArray).map(b => b.toString(16).padStart(2, "0")).join("");
    }

    /**
     * Hash multiple files with progress callback.
     * @returns Map of relativePath -> hash
     */
    async hashFiles(
        files: { file: File; relativePath: string }[],
        onProgress?: (current: number, total: number) => void
    ): Promise<Map<string, string>> {
        const result = new Map<string, string>();

        for (let i = 0; i < files.length; i++) {
            const {file, relativePath} = files[i];
            const hash = await this.hashFile(file);
            result.set(relativePath, hash);

            if (onProgress) {
                onProgress(i + 1, files.length);
            }
        }

        return result;
    }
}
