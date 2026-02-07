"""Conversation and Message schemas for AI chat functionality."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MessageCreate(BaseModel):
    """Schema for creating a new message."""

    content: str = Field(..., min_length=1, description="Message content")
    role: str = Field(..., pattern="^(user|assistant|system)$", description="Message role")


class MessageResponse(BaseModel):
    """Schema for message response."""

    id: UUID
    conversation_id: UUID
    role: str
    content: str
    token_count: int | None = None
    is_summary: bool | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationCreate(BaseModel):
    """Schema for creating a new conversation."""

    title: str = Field(..., min_length=1, max_length=255, description="Conversation title")
    model: str = Field(..., min_length=1, max_length=100, description="AI model name")
    provider: str | None = Field(
        "internal",
        pattern="^(internal|external)$",
        description="Provider type: internal (Ollama) or external (OpenAI, Claude)",
    )
    external_provider: str | None = Field(
        None,
        pattern="^(openai|claude)$",
        description="External provider name: 'openai' or 'claude' (only for provider='external')",
    )
    system_context: str | None = Field(None, description="System context/prompt")


class ConversationResponse(BaseModel):
    """Schema for conversation response without messages."""

    id: UUID
    user_id: UUID
    title: str
    model: str
    provider: str = "internal"
    external_provider: str | None = None
    system_context: str | None
    archived: bool = False
    context_window_size: int = 2048
    current_token_count: int = 0
    has_archived_messages: bool = False
    created_at: datetime
    updated_at: datetime | None
    message_count: int | None = None

    model_config = ConfigDict(from_attributes=True)


class ConversationListResponse(BaseModel):
    """Schema for list of conversations."""

    conversations: list[ConversationResponse]
    total: int
    skip: int
    limit: int


class ConversationDetailResponse(BaseModel):
    """Schema for conversation detail with messages."""

    conversation: ConversationResponse
    messages: list[MessageResponse]


class SendMessageRequest(BaseModel):
    """Schema for sending a message in a conversation."""

    content: str = Field(..., min_length=1, description="Message content")


class SendMessageResponse(BaseModel):
    """Schema for send message response with both user and assistant messages."""

    user_message: MessageResponse
    assistant_message: MessageResponse


class ConversationUpdate(BaseModel):
    """Schema for updating a conversation."""

    title: str | None = Field(None, min_length=1, max_length=255)
    model: str | None = Field(None, min_length=1, max_length=100)
    system_context: str | None = None
    archived: bool | None = None
