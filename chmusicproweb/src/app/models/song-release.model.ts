/**
 * Song Release Models - TypeScript interfaces and enums for song release management.
 */

export enum ReleaseType {
    SINGLE = "single",
    ALBUM = "album"
}

export enum ReleaseStatus {
    DRAFT = "draft",
    ARRANGING = "arranging",
    MIXING = "mixing",
    MASTERING = "mastering",
    PRE_RELEASE = "pre_release",
    REJECTED = "rejected",
    UPLOADED = "uploaded",
    RELEASED = "released",
    DOWNTAKEN = "downtaken",
    ARCHIVED = "archived"
}

export interface AssignedProject {
    id: string;
    project_name: string;
    s3_prefix?: string;
    project_status: string;
}

export interface SongRelease {
    id: string;
    user_id: string;
    type: ReleaseType;
    name: string;
    status: ReleaseStatus;
    genre: string;
    description?: string;
    tags?: string;
    upload_date?: string; // ISO format (YYYY-MM-DD)
    release_date?: string; // ISO format (YYYY-MM-DD)
    downtaken_date?: string; // ISO format (YYYY-MM-DD)
    downtaken_reason?: string;
    rejected_reason?: string;
    upc?: string;
    isrc?: string;
    copyright_info?: string;
    smart_link?: string;
    cover_url?: string; // Presigned S3 URL
    created_at?: string; // ISO format
    updated_at?: string; // ISO format
    assigned_projects?: AssignedProject[];
}

export interface SongReleaseListItem {
    id: string;
    name: string;
    type: ReleaseType;
    status: ReleaseStatus;
    genre: string;
    release_date?: string;
    cover_url?: string;
}

export interface SongReleaseListResponse {
    items: SongReleaseListItem[];
    total: number;
    limit: number;
    offset: number;
}

export interface SongReleaseDetailResponse {
    data: SongRelease;
    message?: string;
}

export interface SongReleaseCreateRequest {
    type: ReleaseType;
    name: string;
    status: ReleaseStatus;
    genre: string;
    project_ids: string[];
    description?: string;
    tags?: string;
    upload_date?: string;
    release_date?: string;
    downtaken_date?: string;
    downtaken_reason?: string;
    rejected_reason?: string;
    upc?: string;
    isrc?: string;
    copyright_info?: string;
    smart_link?: string;
}

export interface SongReleaseUpdateRequest {
    type?: ReleaseType;
    name?: string;
    status?: ReleaseStatus;
    genre?: string;
    project_ids?: string[];
    description?: string;
    tags?: string;
    upload_date?: string;
    release_date?: string;
    downtaken_date?: string;
    downtaken_reason?: string;
    rejected_reason?: string;
    upc?: string;
    isrc?: string;
    copyright_info?: string;
    smart_link?: string;
}
