"""Pydantic schemas for Suno Template API validation"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from schemas.common_schemas import BaseResponse, PaginationResponse


class SunoTemplateCreateRequest(BaseModel):
    """Schema for suno template creation requests"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "My Song Template",
                "template_type": "song",
                "genre": "Indie Pop",
                "bpm": 120,
            }
        }
    )

    title: str = Field(..., min_length=1, max_length=500, description="Template title")
    template_type: str = Field("song", description="Template type: song or instrumental")
    enhanced_lyrics: str | None = Field(None, max_length=5000, description="Enhanced lyrics with Suno tags")
    genre: str | None = Field(None, max_length=200, description="Genre")
    bpm: int | None = Field(None, ge=40, le=300, description="BPM (40-300)")
    vocal_type: str | None = Field(None, max_length=100, description="Vocal type")
    instruments: str | None = Field(None, description="Instruments (comma-separated)")
    mood: str | None = Field(None, max_length=500, description="Mood description")
    mix_character: str | None = Field(None, max_length=200, description="Mix character")
    style_prompt: str | None = Field(None, max_length=500, description="Style prompt (auto-generated or manual)")
    is_instrumental: bool = Field(False, description="Whether template is instrumental-only")

    @field_validator("template_type")
    @classmethod
    def validate_template_type(cls, v):
        if v not in ["song", "instrumental"]:
            raise ValueError("template_type must be one of: song, instrumental")
        return v


class SunoTemplateUpdateRequest(BaseModel):
    """Schema for suno template update requests"""

    title: str | None = Field(None, min_length=1, max_length=500, description="Template title")
    template_type: str | None = Field(None, description="Template type")
    enhanced_lyrics: str | None = Field(None, max_length=5000, description="Enhanced lyrics with Suno tags")
    genre: str | None = Field(None, max_length=200, description="Genre")
    bpm: int | None = Field(None, ge=40, le=300, description="BPM (40-300)")
    vocal_type: str | None = Field(None, max_length=100, description="Vocal type")
    instruments: str | None = Field(None, description="Instruments (comma-separated)")
    mood: str | None = Field(None, max_length=500, description="Mood description")
    mix_character: str | None = Field(None, max_length=200, description="Mix character")
    style_prompt: str | None = Field(None, max_length=500, description="Style prompt")
    is_instrumental: bool | None = Field(None, description="Whether template is instrumental-only")
    original_lyrics: str | None = Field(None, description="Original lyrics")

    @field_validator("template_type")
    @classmethod
    def validate_template_type(cls, v):
        if v is not None and v not in ["song", "instrumental"]:
            raise ValueError("template_type must be one of: song, instrumental")
        return v


class SunoTemplateResponse(BaseModel):
    """Schema for single suno template response"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Unique template ID")
    title: str = Field(..., description="Template title")
    template_type: str = Field(..., description="Template type (song/instrumental)")
    source_sketch_id: UUID | None = Field(None, description="Source sketch ID")
    original_lyrics: str | None = Field(None, description="Original lyrics from sketch")
    enhanced_lyrics: str | None = Field(None, description="Enhanced lyrics with Suno tags")
    genre: str | None = Field(None, description="Genre")
    bpm: int | None = Field(None, description="BPM")
    vocal_type: str | None = Field(None, description="Vocal type")
    instruments: str | None = Field(None, description="Instruments")
    mood: str | None = Field(None, description="Mood description")
    mix_character: str | None = Field(None, description="Mix character")
    style_prompt: str | None = Field(None, description="Generated style prompt")
    is_instrumental: bool = Field(..., description="Instrumental flag")
    project_id: UUID | None = Field(None, description="Assigned project ID")
    project_folder_id: UUID | None = Field(None, description="Assigned project folder ID")
    project_name: str | None = Field(None, description="Assigned project name")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")

    @field_serializer("id", "source_sketch_id", "project_id", "project_folder_id")
    def serialize_uuid(self, value: UUID | None) -> str | None:
        """Convert UUID to string for JSON serialization"""
        return str(value) if value else None


class SunoTemplateListResponse(PaginationResponse):
    """Schema for suno template list response"""

    data: list[SunoTemplateResponse] = Field(..., description="List of suno templates")


class SunoTemplateDetailResponse(BaseResponse):
    """Schema for single suno template detail response"""

    data: SunoTemplateResponse = Field(..., description="Suno template details")
