"""Pydantic schemas for Workshop API validation"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from schemas.common_schemas import BaseResponse, PaginationResponse


class WorkshopCreateRequest(BaseModel):
    """Schema for workshop creation requests"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Love Song Workshop",
                "connect_topic": "First love in summer",
            }
        }
    )

    title: str = Field(..., min_length=1, max_length=200, description="Workshop title")
    connect_topic: str | None = Field(None, max_length=5000, description="Initial topic/theme for connect phase")
    draft_language: str | None = Field("EN", max_length=5, description="Draft generation language code")

    @field_validator("draft_language")
    @classmethod
    def validate_draft_language(cls, v):
        """Validate draft_language field"""
        if v and v not in ["EN", "DE", "FR", "IT", "ES"]:
            raise ValueError("draft_language must be one of: EN, DE, FR, IT, ES")
        return v


class WorkshopUpdateRequest(BaseModel):
    """Schema for workshop update requests"""

    title: str | None = Field(None, min_length=1, max_length=200, description="Workshop title")
    connect_topic: str | None = Field(None, max_length=5000, description="Topic/theme")
    connect_inspirations: str | None = Field(None, description="Inspirations (JSON string)")
    collect_mindmap: str | None = Field(None, description="Mindmap data (JSON string)")
    collect_stories: str | None = Field(None, description="Story ideas (JSON string)")
    collect_words: str | None = Field(None, description="Word library (JSON string)")
    shape_structure: str | None = Field(None, description="Song structure (JSON string)")
    shape_rhymes: str | None = Field(None, description="Rhyme suggestions (JSON string)")
    shape_draft: str | None = Field(None, description="Draft text")
    current_phase: str | None = Field(None, description="Current workshop phase")
    draft_language: str | None = Field(None, max_length=5, description="Draft generation language code")

    @field_validator("current_phase")
    @classmethod
    def validate_phase(cls, v):
        """Validate current_phase field"""
        if v and v not in ["connect", "collect", "shape", "completed"]:
            raise ValueError("current_phase must be one of: connect, collect, shape, completed")
        return v

    @field_validator("draft_language")
    @classmethod
    def validate_draft_language(cls, v):
        """Validate draft_language field"""
        if v is not None and v not in ["EN", "DE", "FR", "IT", "ES"]:
            raise ValueError("draft_language must be one of: EN, DE, FR, IT, ES")
        return v


class WorkshopResponse(BaseModel):
    """Schema for single workshop response"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Unique workshop ID")
    title: str = Field(..., description="Workshop title")
    connect_topic: str | None = Field(None, description="Topic/theme")
    connect_inspirations: str | None = Field(None, description="Inspirations (JSON string)")
    collect_mindmap: str | None = Field(None, description="Mindmap data (JSON string)")
    collect_stories: str | None = Field(None, description="Story ideas (JSON string)")
    collect_words: str | None = Field(None, description="Word library (JSON string)")
    shape_structure: str | None = Field(None, description="Song structure (JSON string)")
    shape_rhymes: str | None = Field(None, description="Rhyme suggestions (JSON string)")
    shape_draft: str | None = Field(None, description="Draft text")
    current_phase: str = Field(..., description="Current workshop phase")
    draft_language: str | None = Field(None, description="Draft generation language code")
    exported_sketch_id: UUID | None = Field(None, description="Exported sketch ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")

    @field_serializer("id", "exported_sketch_id")
    def serialize_uuid(self, value: UUID | None) -> str | None:
        """Convert UUID to string for JSON serialization"""
        return str(value) if value else None

    @field_validator("current_phase")
    @classmethod
    def validate_phase(cls, v):
        """Validate current_phase field"""
        if v not in ["connect", "collect", "shape", "completed"]:
            raise ValueError("current_phase must be one of: connect, collect, shape, completed")
        return v


class WorkshopListResponse(PaginationResponse):
    """Schema for workshop list response"""

    data: list[WorkshopResponse] = Field(..., description="List of workshops")


class WorkshopDetailResponse(BaseResponse):
    """Schema for single workshop detail response"""

    data: WorkshopResponse = Field(..., description="Workshop details")
