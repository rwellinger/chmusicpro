"""Pydantic schemas for Image API validation"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .common_schemas import BaseResponse, PaginationResponse


class ImageGenerateRequest(BaseModel):
    """Schema for image generation requests"""

    prompt: str = Field(..., min_length=1, max_length=4000, description="Image generation prompt (AI-enhanced)")
    user_prompt: str | None = Field(
        None, min_length=1, max_length=2500, description="Original user input (before AI enhancement)"
    )
    size: str | None = Field("1024x1024", description="Image size")
    title: str | None = Field(None, max_length=255, description="Image title")

    # Style preferences (guided mode)
    artistic_style: str | None = Field(None, description="Artistic style (auto, photorealistic, digital-art, etc.)")
    composition: str | None = Field(None, description="Composition style (auto, portrait, landscape, etc.)")
    lighting: str | None = Field(None, description="Lighting style (auto, natural, studio, dramatic, etc.)")
    color_palette: str | None = Field(None, description="Color palette (auto, vibrant, muted, monochrome, etc.)")
    detail_level: str | None = Field(None, description="Detail level (auto, minimal, moderate, highly-detailed)")

    @field_validator("size")
    @classmethod
    def validate_size(cls, v):
        if v and v not in ["512x512", "1024x1024", "1024x1792", "1792x1024"]:
            raise ValueError("size must be one of: 512x512, 1024x1024, 1024x1792, 1792x1024")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "prompt": "A beautiful sunset over the ocean with sailing boats",
                "size": "1024x1024",
                "title": "Ocean Sunset",
                "artistic_style": "photorealistic",
                "composition": "landscape",
                "lighting": "golden-hour",
                "color_palette": "warm",
                "detail_level": "highly-detailed",
            }
        }
    )


class ImageResponse(BaseModel):
    """Schema for single image response"""

    id: str = Field(..., description="Unique image ID")
    title: str | None = Field(None, description="Image title")
    user_prompt: str | None = Field(None, description="Original user input (before AI enhancement)")
    prompt: str = Field(..., description="AI-enhanced prompt (Ollama)")
    enhanced_prompt: str | None = Field(None, description="Final prompt sent to DALL-E (Ollama + Styles)")
    size: str | None = Field(None, description="Image dimensions")
    status: str = Field(..., description="Generation status")
    url: str | None = Field(None, description="Image URL if completed")
    created_at: datetime = Field(..., description="Creation timestamp")
    completed_at: datetime | None = Field(None, description="Completion timestamp")
    tags: list[str] | None = Field(None, description="Image tags")

    # Style preferences (guided mode)
    artistic_style: str | None = Field(None, description="Artistic style used")
    composition: str | None = Field(None, description="Composition style used")
    lighting: str | None = Field(None, description="Lighting style used")
    color_palette: str | None = Field(None, description="Color palette used")
    detail_level: str | None = Field(None, description="Detail level used")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "img_abc123",
                "title": "Ocean Sunset",
                "user_prompt": "A beautiful sunset",
                "prompt": "A beautiful sunset over the ocean with sailing boats",
                "enhanced_prompt": "A beautiful sunset over the ocean with sailing boats, photorealistic style, landscape composition, golden hour lighting, warm color palette, highly detailed",
                "size": "1024x1024",
                "status": "completed",
                "url": "http://localhost:8000/api/v1/image/download/img_abc123",
                "created_at": "2024-01-01T12:00:00Z",
                "completed_at": "2024-01-01T12:01:30Z",
                "tags": ["sunset", "ocean", "nature"],
                "artistic_style": "photorealistic",
                "composition": "landscape",
                "lighting": "golden-hour",
                "color_palette": "warm",
                "detail_level": "highly-detailed",
            }
        },
    )


class ImageGenerateResponse(BaseResponse):
    """Schema for image generation response"""

    data: ImageResponse = Field(..., description="Generated image data")


class ImageListRequest(BaseModel):
    """Schema for image list request parameters"""

    limit: int | None = Field(20, ge=1, le=100, description="Number of items to return")
    offset: int | None = Field(0, ge=0, description="Number of items to skip")
    search: str | None = Field(None, max_length=100, description="Search query for title/prompt")
    sort: str | None = Field("created_at", description="Sort field")
    order: str | None = Field("desc", description="Sort order")

    @field_validator("sort")
    @classmethod
    def validate_sort(cls, v):
        if v and v not in ["created_at", "completed_at", "title"]:
            raise ValueError("sort must be one of: created_at, completed_at, title")
        return v

    @field_validator("order")
    @classmethod
    def validate_order(cls, v):
        if v and v not in ["asc", "desc"]:
            raise ValueError("order must be either asc or desc")
        return v


class ImageListResponse(PaginationResponse):
    """Schema for image list response"""

    data: list[ImageResponse] = Field(..., description="List of images")


class ImageUpdateRequest(BaseModel):
    """Schema for image update requests"""

    title: str | None = Field(None, max_length=255, description="New image title")
    tags: list[str] | None = Field(None, description="Image tags")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"title": "Beautiful Ocean Sunset", "tags": ["sunset", "ocean", "peaceful", "nature"]}
        }
    )


class ImageUpdateResponse(BaseResponse):
    """Schema for image update response"""

    data: ImageResponse = Field(..., description="Updated image data")


class ImageDeleteResponse(BaseResponse):
    """Schema for image deletion response"""

    data: dict = Field({"deleted": True}, description="Deletion confirmation")
