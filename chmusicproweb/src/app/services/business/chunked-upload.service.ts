/**
 * Chunked Upload Service - Handles large file uploads via S3 multipart upload.
 *
 * Files >= 20MB are split into 10MB chunks and uploaded sequentially.
 * Supports resume via status endpoint (re-checks already uploaded parts).
 */

import {inject, Injectable} from "@angular/core";
import {HttpClient} from "@angular/common/http";
import {firstValueFrom} from "rxjs";
import {ApiConfigService} from "../config/api-config.service";
import {ChunkedUploadInit, ChunkedUploadProgress, ChunkedUploadResult} from "../../models/song-project.model";

const CHUNK_SIZE = 10 * 1024 * 1024; // 10MB
const CHUNKED_THRESHOLD = 20 * 1024 * 1024; // 20MB

interface UploadedPartInfo {
    part_number: number;
    etag: string;
}

@Injectable({
    providedIn: "root"
})
export class ChunkedUploadService {
    private http = inject(HttpClient);
    private apiConfig = inject(ApiConfigService);

    /**
     * Check if a file should use chunked upload.
     */
    shouldUseChunkedUpload(file: File): boolean {
        return file.size >= CHUNKED_THRESHOLD;
    }

    /**
     * Upload a large file using chunked upload with S3 multipart.
     *
     * @param projectId Project UUID
     * @param folderId Folder UUID
     * @param file File to upload
     * @param relativePath Relative path (e.g., "Drums/kick.wav")
     * @param fileHash SHA256 hash of the complete file
     * @param onProgress Progress callback
     * @param abortSignal Optional AbortSignal for cancellation
     * @returns ChunkedUploadResult with file_id
     */
    async uploadFileChunked(
        projectId: string,
        folderId: string,
        file: File,
        relativePath: string,
        fileHash: string,
        onProgress?: (progress: ChunkedUploadProgress) => void,
        abortSignal?: AbortSignal
    ): Promise<ChunkedUploadResult> {
        const totalChunks = Math.ceil(file.size / CHUNK_SIZE);

        // Step 1: Init - get upload_id and s3_key
        const initResponse = await firstValueFrom(
            this.http.post<{ data: ChunkedUploadInit }>(
                this.apiConfig.endpoints.songProject.chunkedUploadInit(projectId, folderId),
                {
                    filename: relativePath,
                    file_size_bytes: file.size,
                    file_hash: fileHash,
                    mime_type: file.type || null,
                    chunk_size_bytes: CHUNK_SIZE,
                    total_chunks: totalChunks
                }
            )
        );

        const {upload_id, s3_key} = initResponse.data;

        try {
            // Step 2: Check for already uploaded parts (resume scenario)
            const existingParts = new Map<number, string>(); // part_number -> etag
            try {
                const statusResponse = await firstValueFrom(
                    this.http.get<{ data: { uploaded_parts: UploadedPartInfo[] } }>(
                        this.apiConfig.endpoints.songProject.chunkedUploadStatus(upload_id, s3_key)
                    )
                );
                for (const part of statusResponse.data.uploaded_parts) {
                    existingParts.set(part.part_number, part.etag);
                }
            } catch {
                // No parts uploaded yet - start fresh
            }

            // Step 3: Upload chunks sequentially, skipping already uploaded parts
            const parts: UploadedPartInfo[] = [];

            for (let i = 0; i < totalChunks; i++) {
                if (abortSignal?.aborted) {
                    await this.abortUpload(upload_id, s3_key);
                    throw new Error("Upload aborted");
                }

                const partNumber = i + 1;

                // Skip already uploaded parts (use existing etag)
                const existingEtag = existingParts.get(partNumber);
                if (existingEtag) {
                    parts.push({part_number: partNumber, etag: existingEtag});
                } else {
                    // Upload this chunk
                    const start = i * CHUNK_SIZE;
                    const end = Math.min(start + CHUNK_SIZE, file.size);
                    const chunk = file.slice(start, end);
                    const chunkBytes = await chunk.arrayBuffer();

                    const partResponse = await firstValueFrom(
                        this.http.put<{ data: UploadedPartInfo }>(
                            this.apiConfig.endpoints.songProject.chunkedUploadPart(upload_id, partNumber, s3_key),
                            chunkBytes,
                            {headers: {"Content-Type": "application/octet-stream"}}
                        )
                    );

                    parts.push(partResponse.data);
                }

                // Report progress
                const end = Math.min((i + 1) * CHUNK_SIZE, file.size);
                if (onProgress) {
                    onProgress({
                        chunksUploaded: partNumber,
                        totalChunks,
                        bytesUploaded: end,
                        totalBytes: file.size,
                        percentComplete: Math.round((partNumber / totalChunks) * 100)
                    });
                }
            }

            // Step 4: Complete - assemble parts and create DB record
            const completeResponse = await firstValueFrom(
                this.http.post<{ data: ChunkedUploadResult }>(
                    this.apiConfig.endpoints.songProject.chunkedUploadComplete(projectId, upload_id),
                    {
                        s3_key: s3_key,
                        filename: relativePath,
                        folder_id: folderId,
                        file_size_bytes: file.size,
                        file_hash: fileHash,
                        parts: parts
                    }
                )
            );

            return completeResponse.data;

        } catch (error) {
            // On error (except abort), try to clean up
            if (!(error instanceof Error && error.message === "Upload aborted")) {
                try {
                    await this.abortUpload(upload_id, s3_key);
                } catch {
                    // Best-effort cleanup
                }
            }
            throw error;
        }
    }

    /**
     * Abort an in-progress chunked upload.
     */
    async abortUpload(uploadId: string, s3Key: string): Promise<void> {
        await firstValueFrom(
            this.http.post(
                this.apiConfig.endpoints.songProject.chunkedUploadAbort(uploadId, s3Key),
                {}
            )
        );
    }
}
