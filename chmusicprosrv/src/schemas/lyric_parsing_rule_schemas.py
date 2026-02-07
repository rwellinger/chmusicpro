"""Pydantic schemas for lyric parsing rule validation"""

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LyricParsingRuleBase(BaseModel):
    """Base schema for lyric parsing rules"""

    name: str = Field(..., min_length=1, max_length=100, description="Rule name (e.g., 'Line Break After Comma')")
    description: str | None = Field(None, description="Human-readable description of what this rule does")
    pattern: str = Field(..., min_length=1, description="Regex pattern to match (JSON-escaped)")
    replacement: str = Field(..., description="Replacement string (can be empty)")
    rule_type: str = Field(..., description="Rule type: 'cleanup' or 'section'")
    active: bool = Field(True, description="Whether the rule is active")
    order: int = Field(0, ge=0, description="Execution order (0-based, lower executes first)")

    @field_validator("pattern")
    @classmethod
    def validate_pattern(cls, v: str) -> str:
        """Validate that pattern is a valid regex"""
        if not v or not v.strip():
            raise ValueError("Pattern cannot be empty")
        try:
            re.compile(v)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")
        return v

    @field_validator("rule_type")
    @classmethod
    def validate_rule_type(cls, v: str) -> str:
        """Validate rule_type is valid"""
        valid_types = ["cleanup", "section"]
        if v not in valid_types:
            raise ValueError(f"rule_type must be one of: {', '.join(valid_types)}")
        return v


class LyricParsingRuleCreate(LyricParsingRuleBase):
    """Schema for creating a new lyric parsing rule"""

    pass


class LyricParsingRuleUpdate(BaseModel):
    """Schema for updating an existing lyric parsing rule"""

    name: str | None = Field(None, min_length=1, max_length=100, description="Rule name")
    description: str | None = Field(None, description="Description")
    pattern: str | None = Field(None, min_length=1, description="Regex pattern (JSON-escaped)")
    replacement: str | None = Field(None, description="Replacement string")
    rule_type: str | None = Field(None, description="Rule type: 'cleanup' or 'section'")
    active: bool | None = Field(None, description="Whether the rule is active")
    order: int | None = Field(None, ge=0, description="Execution order")

    @field_validator("pattern")
    @classmethod
    def validate_pattern(cls, v: str | None) -> str | None:
        """Validate regex pattern if provided"""
        if v is None:
            return v
        if not v.strip():
            raise ValueError("Pattern cannot be empty")
        try:
            re.compile(v)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")
        return v

    @field_validator("rule_type")
    @classmethod
    def validate_rule_type(cls, v: str | None) -> str | None:
        """Validate rule_type if provided"""
        if v is None:
            return v
        valid_types = ["cleanup", "section"]
        if v not in valid_types:
            raise ValueError(f"rule_type must be one of: {', '.join(valid_types)}")
        return v


class LyricParsingRuleResponse(LyricParsingRuleBase):
    """Schema for lyric parsing rule responses"""

    id: int = Field(..., description="Unique rule ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class LyricParsingRuleListResponse(BaseModel):
    """Schema for listing multiple lyric parsing rules"""

    rules: list[LyricParsingRuleResponse] = Field(..., description="List of lyric parsing rules")
    total: int = Field(..., description="Total number of rules")


class LyricParsingRuleReorderRequest(BaseModel):
    """Schema for reordering rules"""

    rule_ids: list[int] = Field(..., min_length=1, description="Ordered list of rule IDs (new order)")

    @field_validator("rule_ids")
    @classmethod
    def validate_unique_ids(cls, v: list[int]) -> list[int]:
        """Ensure all IDs are unique"""
        if len(v) != len(set(v)):
            raise ValueError("rule_ids must contain unique values")
        return v
