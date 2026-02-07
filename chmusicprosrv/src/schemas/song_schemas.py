"""Pydantic schemas for Song API validation"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .common_schemas import BaseResponse, PaginationResponse


class SongResponse(BaseModel):
    """Schema for single song response"""

    id: str = Field(..., description="Unique song ID")
    title: str | None = Field(None, description="Song title")
    prompt: str = Field(..., description="Generation prompt used")
    lyrics: str | None = Field(None, description="Song lyrics")
    style: str | None = Field(None, description="Music style/genre")
    status: str = Field(..., description="Generation status")
    job_id: str | None = Field(None, description="External API job ID")
    audio_url: str | None = Field(None, description="Audio file URL")
    flac_url: str | None = Field(None, description="FLAC file URL")
    mp3_url: str | None = Field(None, description="MP3 file URL")
    stems_url: str | None = Field(None, description="Stems ZIP file URL")
    workflow: str | None = Field("notUsed", description="Workflow status (inUse, onWork, notUsed, fail)")
    rating: int | None = Field(None, ge=1, le=5, description="User rating")
    is_instrumental: bool | None = Field(False, description="True if this is an instrumental song")
    created_at: datetime = Field(..., description="Creation timestamp")
    completed_at: datetime | None = Field(None, description="Completion timestamp")
    tags: list[str] | None = Field(None, description="Song tags")

    @field_validator("workflow")
    @classmethod
    def validate_workflow(cls, v):
        if v and v not in ["inUse", "onWork", "notUsed", "fail"]:
            raise ValueError("workflow must be one of: inUse, onWork, notUsed, fail")
        return v

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "song_abc123",
                "title": "Summer Vibes",
                "prompt": "Upbeat pop song about summer",
                "lyrics": "[Verse 1]\nSummer days are here...",
                "style": "pop",
                "status": "completed",
                "workflow": "notUsed",
                "rating": 4,
                "created_at": "2024-01-01T12:00:00Z",
                "completed_at": "2024-01-01T12:02:30Z",
                "tags": ["pop", "summer", "upbeat"],
            }
        },
    )


class SongListRequest(BaseModel):
    """Schema for song list request parameters"""

    limit: int | None = Field(20, ge=1, le=100, description="Number of items to return")
    offset: int | None = Field(0, ge=0, description="Number of items to skip")
    search: str | None = Field(None, max_length=100, description="Search query for title/prompt/lyrics")
    status: str | None = Field(None, description="Filter by status")
    workflow: str | None = Field(None, description="Filter by workflow")
    sort: str | None = Field("created_at", description="Sort field")
    order: str | None = Field("desc", description="Sort order")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v and v not in ["pending", "processing", "progress", "completed", "failed"]:
            raise ValueError("status must be one of: pending, processing, progress, completed, failed")
        return v

    @field_validator("workflow")
    @classmethod
    def validate_workflow(cls, v):
        if v and v not in ["inUse", "onWork", "notUsed", "fail"]:
            raise ValueError("workflow must be one of: inUse, onWork, notUsed, fail")
        return v

    @field_validator("sort")
    @classmethod
    def validate_sort(cls, v):
        if v and v not in ["created_at", "completed_at", "title", "rating"]:
            raise ValueError("sort must be one of: created_at, completed_at, title, rating")
        return v

    @field_validator("order")
    @classmethod
    def validate_order(cls, v):
        if v and v not in ["asc", "desc"]:
            raise ValueError("order must be either asc or desc")
        return v


class SongListResponse(PaginationResponse):
    """Schema for song list response"""

    data: list[SongResponse] = Field(..., description="List of songs")


class SongUpdateRequest(BaseModel):
    """Schema for song update requests"""

    title: str | None = Field(None, max_length=255, description="New song title")
    workflow: str | None = Field(None, description="Workflow status")
    rating: int | None = Field(None, ge=1, le=5, description="User rating")
    tags: list[str] | None = Field(None, description="Song tags")
    project_id: str | None = Field(None, description="Song project ID to assign this song to")
    project_folder_id: str | None = Field(None, description="Folder ID within the project")

    @field_validator("workflow")
    @classmethod
    def validate_workflow(cls, v):
        if v and v not in ["inUse", "onWork", "notUsed", "fail"]:
            raise ValueError("workflow must be one of: inUse, onWork, notUsed, fail")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Amazing Summer Song",
                "workflow": "inUse",
                "rating": 5,
                "tags": ["pop", "summer", "upbeat", "vacation"],
                "project_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "project_folder_id": "f1f2f3f4-e5e6-7890-abcd-ef1234567890",
            }
        }
    )


class SongUpdateResponse(BaseResponse):
    """Schema for song update response"""

    data: SongResponse = Field(..., description="Updated song data")


class SongDeleteResponse(BaseResponse):
    """Schema for song deletion response"""

    data: dict = Field({"deleted": True}, description="Deletion confirmation")


class ChoiceRatingUpdateRequest(BaseModel):
    """Schema for updating song choice rating"""

    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")

    model_config = ConfigDict(json_schema_extra={"example": {"rating": 4}})


class ChoiceRatingUpdateResponse(BaseResponse):
    """Schema for choice rating update response"""

    data: dict[str, Any] = Field(..., description="Updated choice data")
