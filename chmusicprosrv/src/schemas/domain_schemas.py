"""
Domain management Pydantic schemas for multi-tenancy
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from schemas.common_schemas import BaseResponse


class DomainResponse(BaseModel):
    """Domain information response schema"""

    id: UUID = Field(..., description="Domain ID")
    type: int = Field(..., description="Domain type (0=System, 1=KI Templates, 2=User, 3=Company, 4=Producer)")
    name: str = Field(..., description="Domain name")
    description: str | None = Field(None, description="Domain description")
    is_active: bool = Field(..., description="Domain active status")
    created_at: datetime = Field(..., description="Domain creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class DomainMembershipResponse(BaseModel):
    """Domain membership response schema"""

    id: UUID = Field(..., description="Membership ID")
    domain_id: UUID = Field(..., description="Domain ID")
    user_id: UUID = Field(..., description="User ID")
    role: str = Field(..., description="Role in domain (owner, admin, member, viewer)")
    is_default: bool = Field(..., description="Whether this is the user's default domain")
    created_at: datetime = Field(..., description="Membership creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class DomainWithRoleResponse(BaseModel):
    """Domain with the current user's role in it"""

    domain: DomainResponse = Field(..., description="Domain information")
    role: str = Field(..., description="Current user's role in this domain")
    is_default: bool = Field(..., description="Whether this is the user's default domain")

    model_config = ConfigDict(from_attributes=True)


class DomainCreateRequest(BaseModel):
    """Schema for creating a new domain"""

    type: int = Field(..., ge=2, description="Domain type (2=User, 3=Company, 4=Producer)")
    name: str = Field(..., min_length=1, max_length=200, description="Domain name")
    description: str | None = Field(None, description="Domain description")


class DomainUpdateRequest(BaseModel):
    """Schema for updating a domain"""

    name: str | None = Field(None, min_length=1, max_length=200, description="Domain name")
    description: str | None = Field(None, description="Domain description")


class DomainSwitchRequest(BaseModel):
    """Schema for switching active domain"""

    domain_id: str = Field(..., description="Target domain ID to switch to")


class DomainMemberAddRequest(BaseModel):
    """Schema for adding a member to a domain"""

    email: str = Field(..., description="Email of the user to add")
    role: str = Field("member", description="Role to assign (owner, admin, member, viewer)")


class DomainMemberUpdateRequest(BaseModel):
    """Schema for updating a member's role"""

    role: str = Field(..., description="New role (owner, admin, member, viewer)")


class DomainSwitchResponse(BaseResponse):
    """Response for domain switch"""

    token: str = Field(..., description="New JWT token with updated domain claims")
    domain: DomainWithRoleResponse = Field(..., description="The newly active domain")
    expires_at: str = Field(..., description="Token expiration timestamp")


class DomainMemberResponse(BaseModel):
    """Response for a domain member"""

    membership_id: str = Field(..., description="Membership ID")
    user_id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    first_name: str | None = Field(None, description="User first name")
    last_name: str | None = Field(None, description="User last name")
    role: str = Field(..., description="Role in domain")
    is_default: bool = Field(..., description="Whether this domain is the user's default")
    created_at: datetime = Field(..., description="Membership creation timestamp")


class DomainMemberListResponse(BaseResponse):
    """Response for domain member list"""

    members: list[DomainMemberResponse] = Field(..., description="List of domain members")


class DomainListResponse(BaseResponse):
    """Response for domain list"""

    domains: list[DomainWithRoleResponse] = Field(..., description="List of domains with user roles")
