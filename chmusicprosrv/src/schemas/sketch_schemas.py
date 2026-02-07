"""Pydantic schemas for Sketch API validation"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from schemas.common_schemas import BaseResponse, PaginationResponse


class SketchCreateRequest(BaseModel):
    """Schema for sketch creation requests"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Summer Vibes Idea",
                "lyrics": "[Verse 1]\nSummer days are here...",
                "prompt": "upbeat pop, sunny, feel-good",
                "tags": "pop, summer, upbeat",
            }
        }
    )

    title: str | None = Field(None, max_length=500, description="Sketch title")
    lyrics: str | None = Field(None, max_length=10000, description="Song lyrics (optional)")
    prompt: str = Field(..., min_length=1, max_length=1024, description="Music style prompt")
    tags: str | None = Field(None, max_length=1000, description="Comma-separated tags")
    sketch_type: str = Field(
        default="song", pattern="^(inspiration|song)$", description="Sketch type: inspiration or song"
    )
    description_long: str | None = Field(None, description="Long description for release platforms")
    description_short: str | None = Field(None, max_length=150, description="Short description (max 150 chars)")
    description_tags: str | None = Field(None, max_length=1000, description="Release tags (comma-separated)")
    info: str | None = Field(None, description="Working notes (key, tempo, bars, length)")


class SketchResponse(BaseModel):
    """Schema for single sketch response"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Unique sketch ID")
    title: str | None = Field(None, description="Sketch title")
    lyrics: str | None = Field(None, description="Song lyrics")
    prompt: str = Field(..., description="Music style prompt")
    tags: str | None = Field(None, description="Comma-separated tags")
    sketch_type: str = Field(..., description="Sketch type: inspiration or song")
    description_long: str | None = Field(None, description="Long description for release platforms")
    description_short: str | None = Field(None, description="Short description (max 150 chars)")
    description_tags: str | None = Field(None, description="Release tags (comma-separated)")
    info: str | None = Field(None, description="Working notes (key, tempo, bars, length)")
    workflow: str = Field(..., description="Workflow status")
    project_id: UUID | None = Field(None, description="Project ID (if assigned)")
    project_name: str | None = Field(None, description="Project name (if assigned)")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")

    @field_serializer("id", "project_id")
    def serialize_uuid(self, value: UUID | None) -> str | None:
        """Convert UUID to string for JSON serialization"""
        return str(value) if value else None

    @field_validator("workflow")
    @classmethod
    def validate_workflow(cls, v):
        """Validate workflow field"""
        if v not in ["draft", "used", "archived"]:
            raise ValueError("workflow must be one of: draft, used, archived")
        return v


class SketchUpdateRequest(BaseModel):
    """Schema for sketch update requests"""

    title: str | None = Field(None, max_length=500, description="New sketch title")
    lyrics: str | None = Field(None, max_length=10000, description="New lyrics")
    prompt: str | None = Field(None, min_length=1, max_length=1024, description="New music style")
    tags: str | None = Field(None, max_length=1000, description="New tags")
    sketch_type: str | None = Field(None, pattern="^(inspiration|song)$", description="New sketch type")
    description_long: str | None = Field(None, description="New long description")
    description_short: str | None = Field(None, max_length=150, description="New short description")
    description_tags: str | None = Field(None, max_length=1000, description="New release tags")
    info: str | None = Field(None, description="New working notes")
    workflow: str | None = Field(None, description="New workflow status")
    project_id: str | None = Field(None, description="Song project ID to assign this sketch to")
    project_folder_id: str | None = Field(None, description="Folder ID within the project")

    @field_validator("workflow")
    @classmethod
    def validate_workflow(cls, v):
        """Validate workflow field"""
        if v and v not in ["draft", "used", "archived"]:
            raise ValueError("workflow must be one of: draft, used, archived")
        return v


class SketchListRequest(BaseModel):
    """Schema for sketch list request parameters"""

    limit: int | None = Field(20, ge=1, le=100, description="Number of items to return")
    offset: int | None = Field(0, ge=0, description="Number of items to skip")
    search: str | None = Field(None, max_length=100, description="Search query")
    workflow: str | None = Field(None, description="Filter by workflow")
    sort: str | None = Field("created_at", description="Sort field")
    order: str | None = Field("desc", description="Sort order")

    @field_validator("workflow")
    @classmethod
    def validate_workflow(cls, v):
        """Validate workflow field"""
        if v and v not in ["draft", "used", "archived"]:
            raise ValueError("workflow must be one of: draft, used, archived")
        return v

    @field_validator("sort")
    @classmethod
    def validate_sort(cls, v):
        """Validate sort field"""
        if v and v not in ["created_at", "updated_at", "title"]:
            raise ValueError("sort must be one of: created_at, updated_at, title")
        return v


class SketchListResponse(PaginationResponse):
    """Schema for sketch list response"""

    data: list[SketchResponse] = Field(..., description="List of sketches")


class SketchDetailResponse(BaseResponse):
    """Schema for single sketch detail response"""

    data: SketchResponse = Field(..., description="Sketch details")


class SketchDeleteResponse(BaseResponse):
    """Schema for sketch deletion response"""

    data: dict = Field(default={"deleted": True}, description="Deletion confirmation")


class SketchDuplicateRequest(BaseModel):
    """Schema for sketch duplication requests"""

    new_title_suffix: str | None = Field(
        default=None, max_length=100, description="Suffix for new title (default: ' (Copy)')"
    )
