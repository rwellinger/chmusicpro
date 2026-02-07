"""Pydantic schemas for Chat API validation"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from config.allowed_models import OLLAMA_ALLOWED_MODELS

from .common_schemas import BaseResponse


class ChatOptions(BaseModel):
    """Schema for chat generation options"""

    temperature: float | None = Field(0.3, description="Temperature for text generation (validated by frontend)")
    max_tokens: int | None = Field(
        30, description="Maximum tokens to generate (None or <=0 means no limit, let model decide)"
    )
    top_p: float | None = Field(0.9, ge=0.0, le=1.0, description="Top-p sampling parameter")
    repeat_penalty: float | None = Field(1.1, ge=0.0, le=2.0, description="Repeat penalty")

    model_config = ConfigDict(
        json_schema_extra={"example": {"temperature": 0.7, "max_tokens": 100, "top_p": 0.9, "repeat_penalty": 1.1}}
    )


class ChatRequest(BaseModel):
    """Schema for chat generation requests"""

    model: str = Field(..., description="AI model to use for generation")
    prompt: str = Field(..., min_length=1, max_length=10000, description="Input prompt for generation")
    pre_condition: str | None = Field("", description="Text before user input")
    post_condition: str | None = Field("", description="Text after user input")
    options: ChatOptions | None = Field(default_factory=ChatOptions, description="Generation options")

    @field_validator("model")
    @classmethod
    def validate_model(cls, v):
        if v not in OLLAMA_ALLOWED_MODELS:
            raise ValueError(f"model must be one of: {', '.join(OLLAMA_ALLOWED_MODELS)}")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "model": "llama3.2:3b",
                "prompt": "Explain quantum computing in simple terms",
                "pre_condition": "You are a helpful AI assistant. Please provide a clear explanation.",
                "post_condition": "Keep your answer concise and educational.",
                "options": {"temperature": 0.7, "max_tokens": 150, "top_p": 0.9, "repeat_penalty": 1.1},
            }
        }
    )


class ChatResponse(BaseResponse):
    """Schema for chat generation response"""

    data: dict[str, Any] = Field(..., description="Generated response data")
    model: str = Field(..., description="Model used for generation")
    usage: dict[str, Any] | None = Field(None, description="Token usage statistics")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "data": {
                    "response": "Quantum computing is a revolutionary computing paradigm...",
                    "prompt_tokens": 25,
                    "completion_tokens": 147,
                    "total_tokens": 172,
                },
                "model": "llama3.2:3b",
                "usage": {"prompt_tokens": 25, "completion_tokens": 147, "total_tokens": 172},
                "timestamp": "2024-01-01T12:00:00Z",
            }
        }
    )


class UnifiedChatRequest(BaseModel):
    """Schema for unified chat generation requests"""

    pre_condition: str = Field("", description="Text before user input")
    post_condition: str = Field("", description="Text after user input")
    input_text: str = Field(..., min_length=1, max_length=50000, description="Input text for generation")
    user_instructions: str = Field(
        "", description="Optional user-specific instructions (placed between input and post_condition)"
    )
    temperature: float | None = Field(
        None, description="Temperature for text generation (overrides template, validated by frontend)"
    )
    max_tokens: int | None = Field(
        None,
        description="Maximum tokens to generate (None or <=0 means no limit, let model decide, overrides template)",
    )
    model: str | None = Field(None, description="AI model to use (overrides template)")
    category: str | None = Field(None, description="Template category (for logging/tracking)")
    action: str | None = Field(None, description="Template action (for logging/tracking)")

    @field_validator("model")
    @classmethod
    def validate_model(cls, v):
        if v is not None and v not in OLLAMA_ALLOWED_MODELS:
            raise ValueError(f"model must be one of: {', '.join(OLLAMA_ALLOWED_MODELS)}")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "pre_condition": "You are a helpful AI assistant.",
                "post_condition": "Keep your answer concise.",
                "input_text": "Explain quantum computing",
                "user_instructions": "Make it shorter and use simple language.",
                "temperature": 0.7,
                "max_tokens": 150,
                "model": "llama3.2:3b",
            }
        }
    )


class ChatErrorResponse(BaseResponse):
    """Schema for chat error responses"""

    success: bool = Field(False, description="Request success status")
    error: str = Field(..., description="Error message")
    model: str | None = Field(None, description="Model that was attempted")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "error": "Model not available or invalid parameters",
                "model": "llama3.2:3b",
                "timestamp": "2024-01-01T12:00:00Z",
            }
        }
    )
