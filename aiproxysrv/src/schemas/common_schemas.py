"""Common Pydantic schemas for OpenAPI integration"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BaseResponse(BaseModel):
    """Base response schema for all API endpoints"""

    success: bool = Field(True, description="Request success status")
    message: str | None = Field(None, description="Optional success message")


class ErrorResponse(BaseModel):
    """Error response schema for API endpoints"""

    success: bool = Field(False, description="Request success status")
    error: str = Field(..., description="Error message")
    details: dict[str, Any] | None = Field(None, description="Additional error details")


class ValidationErrorResponse(BaseModel):
    """Validation error response for invalid requests"""

    success: bool = Field(False, description="Request success status")
    error: str = Field("Validation error", description="Error type")
    validation_errors: list[dict[str, Any]] = Field(..., description="List of validation errors")


class PaginationMeta(BaseModel):
    """Pagination metadata"""

    total: int = Field(..., ge=0, description="Total number of items")
    offset: int = Field(..., ge=0, description="Current offset")
    limit: int = Field(..., ge=1, le=100, description="Items per page")
    has_more: bool = Field(..., description="Whether more items are available")


class PaginationResponse(BaseResponse):
    """Base paginated response schema"""

    pagination: PaginationMeta = Field(..., description="Pagination metadata")


class HealthResponse(BaseModel):
    """Health check response"""

    status: str = Field("ok", description="Service status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Health check timestamp")
    version: str = Field("1.3.0", description="API version")


class StatusEnum(str):
    """Common status values"""

    PENDING = "pending"
    PROCESSING = "processing"
    PROGRESS = "progress"
    SUCCESS = "success"
    COMPLETED = "completed"
    FAILED = "failed"
    ERROR = "error"


class BulkDeleteRequest(BaseModel):
    """Schema for bulk deletion requests"""

    model_config = ConfigDict(json_schema_extra={"example": {"ids": ["item_1", "item_2", "item_3"]}})

    ids: list[str] = Field(..., min_length=1, description="List of IDs to delete")


class BulkDeleteResponse(BaseResponse):
    """Schema for bulk deletion response"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "data": {
                    "deleted_count": 3,
                    "failed_count": 0,
                    "deleted_ids": ["item_1", "item_2", "item_3"],
                    "failed_ids": [],
                },
            }
        }
    )

    data: dict[str, Any] = Field(..., description="Bulk deletion results")
