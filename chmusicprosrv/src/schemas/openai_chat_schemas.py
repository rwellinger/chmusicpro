"""OpenAI Chat API schemas for request/response validation."""

from pydantic import BaseModel, Field


class OpenAIChatMessage(BaseModel):
    """Schema for a single message in OpenAI Chat format."""

    role: str = Field(..., pattern="^(system|user|assistant)$", description="Message role")
    content: str = Field(..., min_length=1, description="Message content")


class OpenAIChatRequest(BaseModel):
    """Schema for OpenAI Chat API request."""

    model: str = Field(..., min_length=1, description="OpenAI model name (e.g., gpt-4o)")
    messages: list[OpenAIChatMessage] = Field(..., min_length=1, description="Conversation messages")
    temperature: float | None = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int | None = Field(None, ge=1, description="Maximum tokens to generate")
    top_p: float | None = Field(1.0, ge=0.0, le=1.0, description="Nucleus sampling")
    frequency_penalty: float | None = Field(0.0, ge=-2.0, le=2.0, description="Frequency penalty")
    presence_penalty: float | None = Field(0.0, ge=-2.0, le=2.0, description="Presence penalty")


class OpenAIChatChoice(BaseModel):
    """Schema for a single choice in OpenAI response."""

    index: int
    message: OpenAIChatMessage
    finish_reason: str | None = None


class OpenAIChatUsage(BaseModel):
    """Schema for token usage in OpenAI response."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class OpenAIChatResponse(BaseModel):
    """Schema for OpenAI Chat API response."""

    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[OpenAIChatChoice]
    usage: OpenAIChatUsage


class OpenAIModelInfo(BaseModel):
    """Schema for OpenAI model information."""

    name: str = Field(..., description="Model name")
    context_window: int = Field(..., description="Maximum context window size in tokens")


class OpenAIModelsListResponse(BaseModel):
    """Schema for list of available OpenAI models."""

    models: list[OpenAIModelInfo]
