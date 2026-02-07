"""Pydantic schemas for Song Release API validation"""

from datetime import date

from pydantic import BaseModel, Field


class ReleaseCreateRequest(BaseModel):
    """Request schema for creating a new release"""

    type: str = Field(..., description="Release type: 'single' or 'album'")
    name: str = Field(..., min_length=1, max_length=255, description="Release name")
    status: str = Field(default="draft", description="Release status")
    genre: str = Field(..., min_length=1, max_length=100, description="Music genre")
    project_ids: list[str] = Field(..., description="List of project UUIDs to assign")

    description: str | None = Field(default=None, description="Release description")
    tags: str | None = Field(default=None, max_length=500, description="Comma-separated tags")

    upload_date: date | None = Field(default=None, description="Upload date to platforms")
    release_date: date | None = Field(default=None, description="Public release date")
    downtaken_date: date | None = Field(default=None, description="Downtaken date")

    downtaken_reason: str | None = Field(default=None, description="Reason for downtake")
    rejected_reason: str | None = Field(default=None, description="Reason for rejection")

    upc: str | None = Field(default=None, max_length=50, description="Universal Product Code")
    isrc: str | None = Field(default=None, max_length=50, description="International Standard Recording Code")
    copyright_info: str | None = Field(default=None, description="Copyright information")
    smart_link: str | None = Field(
        default=None, max_length=1000, description="Smart link URL (DistroKid, ToneDen, etc.)"
    )


class ReleaseUpdateRequest(BaseModel):
    """Request schema for updating a release"""

    type: str | None = Field(default=None, description="Release type: 'single' or 'album'")
    name: str | None = Field(default=None, min_length=1, max_length=255, description="Release name")
    status: str | None = Field(default=None, description="Release status")
    genre: str | None = Field(default=None, min_length=1, max_length=100, description="Music genre")
    project_ids: list[str] | None = Field(
        default=None, description="List of project UUIDs to assign (replaces existing)"
    )

    description: str | None = Field(default=None, description="Release description")
    tags: str | None = Field(default=None, max_length=500, description="Comma-separated tags")

    upload_date: date | None = Field(default=None, description="Upload date to platforms")
    release_date: date | None = Field(default=None, description="Public release date")
    downtaken_date: date | None = Field(default=None, description="Downtaken date")

    downtaken_reason: str | None = Field(default=None, description="Reason for downtake")
    rejected_reason: str | None = Field(default=None, description="Reason for rejection")

    upc: str | None = Field(default=None, max_length=50, description="Universal Product Code")
    isrc: str | None = Field(default=None, max_length=50, description="International Standard Recording Code")
    copyright_info: str | None = Field(default=None, description="Copyright information")
    smart_link: str | None = Field(
        default=None, max_length=1000, description="Smart link URL (DistroKid, ToneDen, etc.)"
    )


class ReleaseFilterRequest(BaseModel):
    """Request schema for filtering releases"""

    limit: int = Field(default=20, ge=1, le=100, description="Max results per page")
    offset: int = Field(default=0, ge=0, description="Skip first N results")
    status_filter: str | None = Field(
        default=None, description="Filter by status group: 'all', 'progress', 'uploaded', 'released', 'archive'"
    )
    search: str | None = Field(default=None, max_length=255, description="Search in name/genre")


class AssignedProjectResponse(BaseModel):
    """Response schema for an assigned project"""

    id: str
    project_name: str
    s3_prefix: str | None
    project_status: str

    class Config:
        from_attributes = True


class ReleaseResponse(BaseModel):
    """Response schema for a song release (full details)"""

    id: str
    user_id: str
    type: str
    name: str
    status: str
    genre: str

    description: str | None
    tags: str | None

    upload_date: str | None
    release_date: str | None
    downtaken_date: str | None

    downtaken_reason: str | None
    rejected_reason: str | None

    upc: str | None
    isrc: str | None
    copyright_info: str | None
    smart_link: str | None

    cover_url: str | None

    created_at: str | None
    updated_at: str | None

    assigned_projects: list[AssignedProjectResponse] | None = None

    class Config:
        from_attributes = True


class ReleaseListItemResponse(BaseModel):
    """Response schema for a release list item (minimal fields)"""

    id: str
    name: str
    type: str
    status: str
    genre: str
    release_date: str | None
    cover_url: str | None

    class Config:
        from_attributes = True


class ReleaseListResponse(BaseModel):
    """Response schema for paginated release list"""

    items: list[ReleaseListItemResponse]
    total: int
    limit: int
    offset: int
