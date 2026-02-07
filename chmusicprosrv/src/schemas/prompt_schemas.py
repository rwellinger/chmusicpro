"""Pydantic schemas for prompt template validation"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from config.allowed_models import OLLAMA_ALLOWED_MODELS


class PromptTemplateBase(BaseModel):
    """Base schema for prompt templates"""

    category: str = Field(..., max_length=50, description="Template category (e.g., 'image', 'music', 'lyrics')")
    action: str = Field(..., max_length=50, description="Template action (e.g., 'enhance', 'translate')")
    pre_condition: str = Field(..., description="Text before user input")
    post_condition: str = Field(..., description="Text after user input")
    description: str | None = Field(None, description="Human-readable description of the template")
    version: str | None = Field(None, max_length=10, description="Template version")
    model: str | None = Field(None, max_length=50, description="AI model for this template")
    temperature: float | None = Field(None, description="Temperature for text generation (validated by frontend)")
    max_tokens: int | None = Field(
        None, description="Maximum tokens to generate (None or <=0 means no limit, let model decide)"
    )
    active: bool = Field(True, description="Whether the template is active")

    @field_validator("model")
    @classmethod
    def validate_model(cls, v):
        if v is not None and v not in OLLAMA_ALLOWED_MODELS:
            raise ValueError(f"model must be one of: {', '.join(OLLAMA_ALLOWED_MODELS)}")
        return v


class PromptTemplateCreate(PromptTemplateBase):
    """Schema for creating a new prompt template"""

    pass


class PromptTemplateUpdate(BaseModel):
    """Schema for updating an existing prompt template"""

    pre_condition: str | None = Field(None, description="Text before user input")
    post_condition: str | None = Field(None, description="Text after user input")
    description: str | None = Field(None, description="Human-readable description of the template")
    version: str | None = Field(None, max_length=10, description="Template version")
    model: str | None = Field(None, max_length=50, description="AI model for this template")
    temperature: float | None = Field(None, description="Temperature for text generation (validated by frontend)")
    max_tokens: int | None = Field(
        None, description="Maximum tokens to generate (None or <=0 means no limit, let model decide)"
    )
    active: bool | None = Field(None, description="Whether the template is active")

    @field_validator("model")
    @classmethod
    def validate_model(cls, v):
        if v is not None and v not in OLLAMA_ALLOWED_MODELS:
            raise ValueError(f"model must be one of: {', '.join(OLLAMA_ALLOWED_MODELS)}")
        return v


class PromptTemplateResponse(PromptTemplateBase):
    """Schema for prompt template responses"""

    id: int = Field(..., description="Unique template ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class PromptTemplateListResponse(BaseModel):
    """Schema for listing multiple prompt templates"""

    templates: list[PromptTemplateResponse] = Field(..., description="List of prompt templates")
    total: int = Field(..., description="Total number of templates")


class PromptCategoryResponse(BaseModel):
    """Schema for templates grouped by category"""

    category: str = Field(..., description="Category name")
    templates: dict[str, PromptTemplateResponse] = Field(..., description="Templates by action")


class PromptTemplatesGroupedResponse(BaseModel):
    """Schema for all templates grouped by category and action"""

    categories: dict[str, dict[str, PromptTemplateResponse]] = Field(
        ..., description="Templates grouped by category and action"
    )
