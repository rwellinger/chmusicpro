"""Pydantic schemas for Project Asset Assignment"""

from pydantic import BaseModel, ConfigDict, Field
from pydantic.types import UUID4

from schemas.common_schemas import BaseResponse


class AssignToProjectRequest(BaseModel):
    """Schema for assigning an asset (image/song/sketch) to a project"""

    project_id: UUID4 = Field(..., description="Project ID to assign the asset to")
    folder_id: UUID4 | None = Field(None, description="Folder ID within the project (optional)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "project_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "folder_id": "f1f2f3f4-e5e6-7890-abcd-ef1234567890",
            }
        }
    )


class AssignToProjectResponse(BaseResponse):
    """Schema for assign to project response"""

    data: dict = Field(..., description="Assignment result")


class ImageProjectReferenceResponse(BaseModel):
    """Schema for single image-project reference"""

    id: UUID4 = Field(..., description="Reference ID")
    project_id: UUID4 = Field(..., description="Project ID")
    image_id: UUID4 = Field(..., description="Image ID")
    folder_id: UUID4 | None = Field(None, description="Folder ID")
    display_order: int = Field(..., description="Display order")
    project_name: str | None = Field(None, description="Project name (optional)")
    folder_name: str | None = Field(None, description="Folder name (optional)")

    model_config = ConfigDict(from_attributes=True)
