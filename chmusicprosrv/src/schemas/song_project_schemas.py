"""Pydantic schemas for Song Project API validation"""

from pydantic import BaseModel, Field

from schemas.common_schemas import PaginationMeta


class CoverInfo(BaseModel):
    """Cover display info for Song Project"""

    source: str = Field(..., description="Cover source: 'release' or 'placeholder'")
    release_id: str | None = Field(default=None, description="Release UUID if source='release'")
    release_name: str | None = Field(default=None, description="Release name if source='release'")

    class Config:
        from_attributes = True


class ProjectCreateRequest(BaseModel):
    """Request schema for creating a new project"""

    project_name: str = Field(..., min_length=1, max_length=255, description="Project name")
    tags: list[str] | None = Field(default=None, description="Optional tags list")
    description: str | None = Field(default=None, max_length=5000, description="Optional project description")


class ProjectUpdateRequest(BaseModel):
    """Request schema for updating a project"""

    project_name: str | None = Field(default=None, min_length=1, max_length=255, description="New project name")
    tags: list[str] | None = Field(default=None, description="New tags list")
    description: str | None = Field(default=None, max_length=5000, description="New description")
    cover_image_id: str | None = Field(default=None, description="Cover image UUID")
    project_status: str | None = Field(default=None, description="Project status: 'new', 'progress', 'archived'")


class ProjectResponse(BaseModel):
    """Response schema for a song project"""

    id: str
    project_name: str
    s3_prefix: str | None
    cover_image_id: str | None
    tags: list[str]
    description: str | None
    project_status: str
    cover_info: CoverInfo | None = Field(default=None, description="Cover display information")
    created_at: str | None
    updated_at: str | None

    class Config:
        from_attributes = True


class FolderResponse(BaseModel):
    """Response schema for a project folder"""

    id: str
    folder_name: str
    folder_type: str | None
    s3_prefix: str | None
    custom_icon: str | None
    created_at: str | None
    files: list["FileResponse"] | None = None
    assigned_songs: list["AssignedSongResponse"] | None = None
    assigned_sketches: list["AssignedSketchResponse"] | None = None
    assigned_images: list["AssignedImageResponse"] | None = None

    class Config:
        from_attributes = True


class FileResponse(BaseModel):
    """Response schema for a project file"""

    id: str
    filename: str
    relative_path: str
    file_type: str | None
    mime_type: str | None
    file_size_bytes: int | None
    is_synced: bool
    download_url: str | None
    created_at: str | None
    updated_at: str | None

    class Config:
        from_attributes = True


class AssignedSongResponse(BaseModel):
    """Response schema for an assigned song"""

    id: str
    title: str | None
    workflow: str | None
    file_type: str | None
    file_size_bytes: int | None
    created_at: str | None

    class Config:
        from_attributes = True


class AssignedSketchResponse(BaseModel):
    """Response schema for an assigned sketch"""

    id: str
    title: str | None
    prompt: str
    sketch_type: str
    workflow: str | None
    created_at: str | None

    class Config:
        from_attributes = True


class AssignedImageResponse(BaseModel):
    """Response schema for an assigned image"""

    id: str
    title: str | None
    prompt: str | None
    composition: str | None
    width: int | None
    height: int | None
    created_at: str | None

    class Config:
        from_attributes = True


class AssignedReleaseResponse(BaseModel):
    """Response schema for an assigned release"""

    id: str
    name: str | None
    type: str | None
    status: str | None
    genre: str | None
    release_date: str | None
    created_at: str | None

    class Config:
        from_attributes = True


class ProjectDetailResponse(BaseModel):
    """Response schema for project with folders and files"""

    id: str
    project_name: str
    s3_prefix: str | None
    cover_image_id: str | None
    tags: list[str]
    description: str | None
    project_status: str
    total_files: int
    total_size_bytes: int
    cover_info: CoverInfo | None = Field(default=None, description="Cover display information")
    created_at: str | None
    updated_at: str | None
    folders: list[FolderResponse]
    # Assigned releases for this project
    assigned_releases: list[AssignedReleaseResponse] | None = None
    # All assigned assets (regardless of folder) - for Metadata tab
    all_assigned_songs: list[AssignedSongResponse] | None = None
    all_assigned_sketches: list[AssignedSketchResponse] | None = None
    all_assigned_images: list[AssignedImageResponse] | None = None

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """Response schema for list of projects with pagination"""

    data: list[ProjectResponse]
    pagination: PaginationMeta

    class Config:
        from_attributes = True


class FileUploadResponse(BaseModel):
    """Response schema for file upload"""

    file: FileResponse
    message: str

    class Config:
        from_attributes = True


class MirrorFileRequest(BaseModel):
    """Schema for a single file in mirror request"""

    relative_path: str = Field(..., description="File path relative to folder (e.g., 'Media/drums.flac')")
    file_hash: str = Field(..., min_length=64, max_length=64, description="SHA256 hash (64 hex chars)")
    file_size_bytes: int = Field(..., ge=0, description="File size in bytes")

    class Config:
        from_attributes = True


class MirrorRequest(BaseModel):
    """Request schema for mirror endpoint (compare local vs remote)"""

    files: list[MirrorFileRequest] = Field(..., description="List of local files with hashes")

    class Config:
        from_attributes = True


class MirrorFileAction(BaseModel):
    """Schema for a single file action in mirror response"""

    relative_path: str
    file_hash: str | None = None
    file_size_bytes: int | None = None
    file_id: str | None = None  # For deletions

    class Config:
        from_attributes = True


class MirrorMoveAction(BaseModel):
    """Schema for a file move action in mirror response (same hash, different path)"""

    file_id: str = Field(..., description="File UUID to move")
    old_path: str = Field(..., description="Current relative path")
    new_path: str = Field(..., description="New relative path")
    file_hash: str = Field(..., description="SHA256 hash (for verification)")
    file_size_bytes: int = Field(..., description="File size in bytes")
    s3_key_old: str = Field(..., description="Current S3 key")
    s3_key_new: str = Field(..., description="New S3 key")

    class Config:
        from_attributes = True


class MirrorResponse(BaseModel):
    """Response schema for mirror endpoint (diff result)"""

    to_upload: list[str] = Field(default_factory=list, description="Files to upload (not on remote)")
    to_update: list[str] = Field(default_factory=list, description="Files to update (hash mismatch)")
    to_move: list[MirrorMoveAction] = Field(
        default_factory=list, description="Files to move (same hash, different path)"
    )
    to_delete: list[MirrorFileAction] = Field(default_factory=list, description="Files to delete (only on remote)")
    unchanged: list[str] = Field(default_factory=list, description="Files unchanged (hash match)")

    class Config:
        from_attributes = True


class BatchDeleteRequest(BaseModel):
    """Request schema for batch delete endpoint"""

    file_ids: list[str] = Field(..., min_length=1, description="List of file UUIDs to delete")

    class Config:
        from_attributes = True


class BatchDeleteResponse(BaseModel):
    """Response schema for batch delete endpoint"""

    deleted: int = Field(..., description="Number of files successfully deleted")
    failed: int = Field(..., description="Number of files that failed to delete")
    errors: list[dict[str, str]] = Field(default_factory=list, description="List of errors")

    class Config:
        from_attributes = True


class CompleteDownloadFileResponse(BaseModel):
    """Response schema for a single file in complete project download"""

    filename: str
    relative_path: str
    download_url: str
    size: int

    class Config:
        from_attributes = True


class CompleteDownloadFolderResponse(BaseModel):
    """Response schema for a folder in complete project download"""

    folder_name: str
    files: list[CompleteDownloadFileResponse]

    class Config:
        from_attributes = True


class ProjectCompleteDownloadResponse(BaseModel):
    """Response schema for complete project download (all folders and files)"""

    project_name: str
    folders: list[CompleteDownloadFolderResponse]

    class Config:
        from_attributes = True
