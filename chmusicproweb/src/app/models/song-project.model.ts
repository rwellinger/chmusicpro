/**
 * Song Project Models - TypeScript interfaces and enums for song project management.
 */

/**
 * Cover info for Song Project - determines which cover to display
 */
export interface CoverInfo {
    source: "release" | "placeholder";
    release_id?: string;  // UUID if source='release'
    release_name?: string;  // Name if source='release'
}

export interface SongProject {
    id: string;
    user_id: string;
    project_name: string;
    s3_prefix: string;
    tags: string[];
    description?: string;
    project_status: "new" | "progress" | "archived";
    cover_info?: CoverInfo;  // Cover display logic
    created_at: string; // ISO format
    updated_at: string; // ISO format
}

export interface ProjectFolder {
    id: string;
    project_id: string;
    folder_name: string;
    folder_type: string;
    s3_prefix: string;
    custom_icon?: string;
    created_at: string; // ISO format
}

export interface ProjectFile {
    id: string;
    project_id: string;
    folder_id: string;
    filename: string;
    relative_path: string; // Full path with subdirectories (e.g., "Audio Files/Drums/Kick.wav")
    s3_key: string;
    file_size_bytes: number;
    file_hash?: string;
    is_synced: boolean;
    download_url?: string;
    created_at: string; // ISO format
    updated_at: string; // ISO format
}

export interface AssignedSketch {
    id: string;
    title: string | null;
    prompt: string;
    sketch_type: "inspiration" | "song";
    workflow: string;
    created_at: string | null;
}

export interface AssignedImage {
    id: string;
    title: string | null;
    prompt: string | null;
    composition: string | null;
    width?: number | null;
    height?: number | null;
    created_at: string | null;
}

export interface AssignedRelease {
    id: string;
    name: string | null;
    type: "single" | "album" | null;
    status: string | null;
    genre: string | null;
    release_date: string | null;
    created_at: string | null;
}

export interface AssignedWorkshop {
    id: string;
    title: string;
    current_phase: string;
    draft_language?: string | null;
    created_at: string | null;
}

export interface AssignedSunoTemplate {
    id: string;
    title: string | null;
    template_type: string;
    style_prompt: string | null;
    created_at: string | null;
}

export interface ProjectFolderWithFiles extends ProjectFolder {
    files: ProjectFile[];
}

export interface ProjectFolderWithAssets extends ProjectFolderWithFiles {
    assigned_sketches?: AssignedSketch[];
    assigned_images?: AssignedImage[];
    assigned_workshops?: AssignedWorkshop[];
    assigned_suno_templates?: AssignedSunoTemplate[];
}

export interface SongProjectDetail extends SongProject {
    total_files: number;  // Live calculated
    total_size_bytes: number;  // Live calculated
    folders: ProjectFolderWithAssets[];
    assigned_releases?: AssignedRelease[];
    // All assigned assets (regardless of folder) - for Metadata tab
    all_assigned_sketches?: AssignedSketch[];
    all_assigned_images?: AssignedImage[];
    all_assigned_workshops?: AssignedWorkshop[];
    all_assigned_suno_templates?: AssignedSunoTemplate[];
}

export interface SongProjectListItem {
    id: string;
    project_name: string;
    tags: string[];
    project_status: "new" | "progress" | "archived";
    total_files: number;
    total_size_bytes: number;
    cover_info?: CoverInfo;  // Cover display logic
    created_at: string;
    updated_at: string;
}

export interface SongProjectListResponse {
    data: SongProjectListItem[];
    pagination: {
        total: number;
        limit: number;
        offset: number;
        has_more: boolean;
    };
}

export interface SongProjectDetailResponse {
    data: SongProjectDetail;
    message?: string;
}

export interface SongProjectCreateRequest {
    project_name: string;
    tags?: string[];
    description?: string;
}

export interface SongProjectUpdateRequest {
    project_name?: string;
    tags?: string[];
    description?: string;
    cover_image_id?: string;
    project_status?: "new" | "progress" | "archived";
}

export interface FileUploadRequest {
    file: File;
    folder_id: string;
}

export interface BatchUploadResponse {
    data: {
        uploaded: number;
        failed: number;
        errors: { filename?: string; error: string }[];
    };
    message: string;
}

export interface MirrorFileEntry {
    relative_path: string;
    file_hash: string;
    file_size_bytes: number;
}

export interface MirrorMoveAction {
    file_id: string;
    old_path: string;
    new_path: string;
    file_hash: string;
    file_size_bytes: number;
    s3_key_old: string;
    s3_key_new: string;
}

export interface MirrorFileAction {
    file_id: string;
    relative_path: string;
    file_size_bytes: number;
}

export interface MirrorCompareResult {
    to_upload: string[];
    to_update: string[];
    to_move: MirrorMoveAction[];
    to_delete: MirrorFileAction[];
    unchanged: string[];
}

export interface BatchMoveResponse {
    data: { moved: number; failed: number; errors: { file_id: string; error: string }[] };
}

export interface ChunkedUploadInit {
    upload_id: string;
    s3_key: string;
    chunk_size_bytes: number;
    total_chunks: number;
}

export interface ChunkedUploadProgress {
    chunksUploaded: number;
    totalChunks: number;
    bytesUploaded: number;
    totalBytes: number;
    percentComplete: number;
}

export interface ChunkedUploadResult {
    file_id: string;
    filename: string;
    relative_path: string;
    file_size_bytes: number;
}
