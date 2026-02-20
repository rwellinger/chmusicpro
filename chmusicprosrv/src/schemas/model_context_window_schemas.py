"""Pydantic schemas for model context window validation"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ModelContextWindowCreate(BaseModel):
    """Schema for creating a new model context window entry"""

    model_name: str = Field(..., min_length=1, max_length=100, description="Model name (e.g., 'qwen3:30b', 'gpt-4o')")
    context_window: int = Field(..., gt=0, description="Context window size in tokens")
    provider: str = Field("ollama", max_length=50, description="Provider: 'ollama', 'openai', 'claude'")
    description: str | None = Field(None, max_length=255, description="Optional description")

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        valid_providers = ["ollama", "openai", "claude"]
        if v not in valid_providers:
            raise ValueError(f"provider must be one of: {', '.join(valid_providers)}")
        return v


class ModelContextWindowUpdate(BaseModel):
    """Schema for updating an existing model context window entry"""

    model_name: str | None = Field(None, min_length=1, max_length=100, description="Model name")
    context_window: int | None = Field(None, gt=0, description="Context window size in tokens")
    provider: str | None = Field(None, max_length=50, description="Provider")
    description: str | None = Field(None, max_length=255, description="Optional description")

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str | None) -> str | None:
        if v is None:
            return v
        valid_providers = ["ollama", "openai", "claude"]
        if v not in valid_providers:
            raise ValueError(f"provider must be one of: {', '.join(valid_providers)}")
        return v


class ModelContextWindowResponse(BaseModel):
    """Schema for model context window responses"""

    id: int = Field(..., description="Unique ID")
    model_name: str = Field(..., description="Model name")
    context_window: int = Field(..., description="Context window size in tokens")
    provider: str = Field(..., description="Provider")
    description: str | None = Field(None, description="Optional description")
    created_at: datetime | None = Field(None, description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class ModelContextWindowListResponse(BaseModel):
    """Schema for listing model context window entries"""

    items: list[ModelContextWindowResponse] = Field(..., description="List of model context window entries")
    total: int = Field(..., description="Total number of entries")
