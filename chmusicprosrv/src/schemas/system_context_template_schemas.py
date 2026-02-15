"""Pydantic schemas for system context template validation"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SystemContextTemplateBase(BaseModel):
    """Base schema for system context templates"""

    name: str = Field(..., min_length=1, max_length=100, description="Template name")
    description: str | None = Field(None, description="Human-readable description")
    content: str = Field(..., min_length=1, description="System prompt content")
    sort_order: int = Field(0, ge=0, description="Display order (lower first)")
    active: bool = Field(True, description="Whether the template is active")


class SystemContextTemplateCreate(SystemContextTemplateBase):
    """Schema for creating a new system context template"""

    pass


class SystemContextTemplateUpdate(BaseModel):
    """Schema for updating an existing system context template"""

    name: str | None = Field(None, min_length=1, max_length=100, description="Template name")
    description: str | None = Field(None, description="Human-readable description")
    content: str | None = Field(None, min_length=1, description="System prompt content")
    sort_order: int | None = Field(None, ge=0, description="Display order")
    active: bool | None = Field(None, description="Whether the template is active")


class SystemContextTemplateResponse(SystemContextTemplateBase):
    """Schema for system context template responses"""

    id: UUID = Field(..., description="Unique template ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class SystemContextTemplateListResponse(BaseModel):
    """Schema for listing multiple system context templates"""

    templates: list[SystemContextTemplateResponse] = Field(..., description="List of templates")
    total: int = Field(..., description="Total number of templates")
