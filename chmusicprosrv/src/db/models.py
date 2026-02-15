"""Database models"""

import uuid
from enum import IntEnum, StrEnum

from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSON, JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from db.database import Base


class RuleType(StrEnum):
    """Enum for lyric parsing rule types"""

    CLEANUP = "cleanup"
    SECTION = "section"


class DomainType(IntEnum):
    """Enum for domain types (multi-tenancy)"""

    SYSTEM = 0
    KI_TEMPLATES = 1
    USER = 2
    COMPANY = 3
    PRODUCER = 4


class DomainRole(StrEnum):
    """Enum for domain membership roles"""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class Domain(Base):
    """Model for multi-tenancy domains (tenants)"""

    __tablename__ = "domains"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    type = Column(Integer, nullable=False, index=True)
    name = Column(String(200), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    memberships = relationship("DomainMembership", back_populates="domain", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Domain(id={self.id}, type={self.type}, name='{self.name}')>"


class DomainMembership(Base):
    """Model for user-domain memberships with per-domain roles"""

    __tablename__ = "domain_memberships"
    __table_args__ = (UniqueConstraint("domain_id", "user_id", name="uq_domain_user"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    domain_id = Column(UUID(as_uuid=True), ForeignKey("domains.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False, default=DomainRole.MEMBER, server_default=DomainRole.MEMBER)
    is_default = Column(Boolean, nullable=False, default=False, server_default="false")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    domain = relationship("Domain", back_populates="memberships")
    user = relationship("User", back_populates="domain_memberships")

    def __repr__(self):
        return f"<DomainMembership(domain_id={self.domain_id}, user_id={self.user_id}, role='{self.role}')>"


class SongSketch(Base):
    """Model for storing song concepts/drafts before generation"""

    __tablename__ = "song_sketches"

    # Primary identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Core song data
    title = Column(String(500), nullable=True)
    lyrics = Column(Text, nullable=True)
    prompt = Column(Text, nullable=False)

    # Metadata
    tags = Column(String(1000), nullable=True)
    sketch_type = Column(String(20), nullable=False, default="song", server_default="song")

    # Release descriptions (for publishing to platforms)
    description_long = Column(Text, nullable=True)
    description_short = Column(String(150), nullable=True)
    description_tags = Column(String(1000), nullable=True)
    info = Column(Text, nullable=True)

    # Workflow status
    workflow = Column(String(50), nullable=False, default="draft", index=True)

    # Domain ownership (multi-tenancy)
    domain_id = Column(UUID(as_uuid=True), ForeignKey("domains.id"), nullable=False, index=True)

    # User reference (created_by / audit trail)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Project relationship (optional)
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("song_projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    project_folder_id = Column(
        UUID(as_uuid=True), ForeignKey("project_folders.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    domain = relationship("Domain")
    user = relationship("User", back_populates="sketches")
    project = relationship("SongProject", back_populates="sketches")
    project_folder = relationship("ProjectFolder", foreign_keys=[project_folder_id])

    def __repr__(self):
        return f"<SongSketch(id={self.id}, title='{self.title}', workflow='{self.workflow}')>"


class LyricWorkshop(Base):
    """Model for storing lyric workshop sessions with 3-phase process (Connect, Collect, Shape)"""

    __tablename__ = "lyric_workshops"

    # Primary identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String(200), nullable=False)

    # Domain ownership (multi-tenancy)
    domain_id = Column(UUID(as_uuid=True), ForeignKey("domains.id"), nullable=False, index=True)

    # User reference (created_by / audit trail)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Phase 1: Connect
    connect_topic = Column(Text, nullable=True)
    connect_inspirations = Column(Text, nullable=True)  # JSON string

    # Phase 2: Collect
    collect_mindmap = Column(Text, nullable=True)  # JSON string
    collect_stories = Column(Text, nullable=True)  # JSON string
    collect_words = Column(Text, nullable=True)  # JSON string

    # Phase 3: Shape
    shape_structure = Column(Text, nullable=True)  # JSON string
    shape_rhymes = Column(Text, nullable=True)  # JSON string
    shape_draft = Column(Text, nullable=True)

    # Meta
    current_phase = Column(String(20), nullable=False, default="connect", server_default="connect")
    draft_language = Column(String(5), nullable=True, server_default="EN", default="EN")
    exported_sketch_id = Column(UUID(as_uuid=True), ForeignKey("song_sketches.id", ondelete="SET NULL"), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    domain = relationship("Domain")
    user = relationship("User", back_populates="workshops")
    exported_sketch = relationship("SongSketch", foreign_keys=[exported_sketch_id])

    def __repr__(self):
        return f"<LyricWorkshop(id={self.id}, title='{self.title}', phase='{self.current_phase}')>"


class GeneratedImage(Base):
    """Model for storing generated image metadata"""

    __tablename__ = "generated_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Domain ownership (multi-tenancy)
    domain_id = Column(UUID(as_uuid=True), ForeignKey("domains.id"), nullable=False, index=True)

    # User reference (created_by / audit trail)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    user_prompt = Column(Text, nullable=True)  # Original user input (before AI enhancement)
    prompt = Column(Text, nullable=False)  # AI-enhanced prompt (Ollama)
    enhanced_prompt = Column(Text, nullable=True)  # Final prompt sent to DALL-E (Ollama + Styles)
    size = Column(String(20), nullable=False)
    filename = Column(String(255), nullable=False, unique=True)
    file_path = Column(String(500), nullable=False)
    local_url = Column(String(500), nullable=False)
    s3_key = Column(String(500), nullable=True)  # S3 object key (for S3 storage)
    storage_backend = Column(String(20), server_default="filesystem", nullable=False)  # 'filesystem' or 's3'
    model_used = Column(String(100), nullable=True)
    prompt_hash = Column(String(32), nullable=True)
    title = Column(String(255), nullable=True)  # Custom user title
    tags = Column(Text, nullable=True)  # Comma-separated tags

    # Style preferences (guided mode)
    artistic_style = Column(String(50), nullable=True)  # photorealistic, digital-art, oil-painting, etc.
    composition = Column(String(50), nullable=True)  # portrait, landscape, wide-angle, etc.
    lighting = Column(String(50), nullable=True)  # natural, studio, dramatic, etc.
    color_palette = Column(String(50), nullable=True)  # vibrant, muted, monochrome, etc.
    detail_level = Column(String(50), nullable=True)  # minimal, moderate, highly-detailed
    text_overlay_metadata = Column(JSON, nullable=True)  # Metadata for text overlays (title, artist, font_style, etc.)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    domain = relationship("Domain")
    user = relationship("User", back_populates="generated_images")
    project_references = relationship("ProjectImageReference", back_populates="image", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<GeneratedImage(id={self.id}, filename='{self.filename}', prompt='{self.prompt[:50]}...')>"


class PromptTemplate(Base):
    """Model for storing AI prompt templates for different categories and actions"""

    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Domain ownership (multi-tenancy: belongs to KI Templates domain)
    domain_id = Column(UUID(as_uuid=True), ForeignKey("domains.id"), nullable=True, index=True)

    category = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)
    pre_condition = Column(Text, nullable=False)
    post_condition = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String(10), nullable=True)
    provider = Column(String(50), nullable=False, server_default="ollama", index=True)
    model = Column(String(50), nullable=True)  # Renamed from model_hint
    temperature = Column(Float, nullable=True)  # For AI Chat API (0.0-2.0)
    max_tokens = Column(Integer, nullable=True)  # Maximum tokens to generate
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    domain = relationship("Domain")

    def __repr__(self):
        return (
            f"<PromptTemplate(id={self.id}, category='{self.category}', action='{self.action}', active={self.active})>"
        )


class User(Base):
    """Model for user authentication and management with OAuth2 preparation"""

    __tablename__ = "users"

    # Primary identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Authentication fields
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=True)  # Nullable for OAuth2 users

    # User profile
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    artist_name = Column(String(100), nullable=True)  # For album cover generation (e.g., "thWelly")

    # User preferences
    preferred_language = Column(String(5), nullable=False, default="en", server_default="en")

    # OAuth2 preparation (for future use)
    oauth_provider = Column(String(50), nullable=True)  # 'google', 'github', etc.
    oauth_id = Column(String(255), nullable=True)  # OAuth provider user ID

    # Status and security
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    domain_memberships = relationship("DomainMembership", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    equipment = relationship("Equipment", back_populates="user", cascade="all, delete-orphan")
    song_projects = relationship("SongProject", back_populates="user", cascade="all, delete-orphan")
    song_releases = relationship("SongRelease", back_populates="user", cascade="all, delete-orphan")
    sketches = relationship("SongSketch", back_populates="user", cascade="all, delete-orphan")
    workshops = relationship("LyricWorkshop", back_populates="user", cascade="all, delete-orphan")
    generated_images = relationship("GeneratedImage", back_populates="user", cascade="all, delete-orphan")
    usage_logs = relationship("UsageLog", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', active={self.is_active})>"


class UsageLog(Base):
    """Model for per-user AI usage tracking"""

    __tablename__ = "usage_logs"

    # Primary identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # User reference
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Request metadata
    endpoint = Column(String(100), nullable=False)  # e.g. "generate-unified"
    category = Column(String(50), nullable=True)  # Template category
    action = Column(String(50), nullable=True)  # Template action
    model = Column(String(100), nullable=False)  # AI model used

    # Ollama metrics
    prompt_tokens = Column(Integer, nullable=True)  # From Ollama prompt_eval_count
    eval_tokens = Column(Integer, nullable=True)  # From Ollama eval_count
    total_duration_ns = Column(BigInteger, nullable=True)  # From Ollama total_duration

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="usage_logs")

    def __repr__(self):
        return f"<UsageLog(id={self.id}, user_id={self.user_id}, endpoint='{self.endpoint}', model='{self.model}')>"


class RegistrationLog(Base):
    """Model for audit logging of user registrations (no passwords stored)"""

    __tablename__ = "registration_log"

    # Primary identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Registration data
    registered_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    email = Column(String(255), nullable=False)
    preferred_language = Column(String(5), nullable=False, server_default="en")

    # Request metadata
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6
    user_agent = Column(String(500), nullable=True)

    def __repr__(self):
        return f"<RegistrationLog(id={self.id}, email='{self.email}', registered_at={self.registered_at})>"


class Conversation(Base):
    """Model for storing AI chat conversations"""

    __tablename__ = "conversations"

    # Primary identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Domain ownership (multi-tenancy)
    domain_id = Column(UUID(as_uuid=True), ForeignKey("domains.id"), nullable=False, index=True)

    # User reference (created_by / audit trail)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # Conversation metadata
    title = Column(String(255), nullable=False)
    model = Column(String(100), nullable=False)  # Model name (Ollama or OpenAI or Claude)
    provider = Column(
        String(50), nullable=False, server_default="internal", index=True
    )  # 'internal' (Ollama) or 'external' (OpenAI, Claude, DeepSeek)
    external_provider = Column(
        String(50), nullable=True, index=True
    )  # For external providers: 'openai', 'claude', etc. NULL for internal (Ollama)
    system_context = Column(Text, nullable=True)  # System prompt/context
    archived = Column(Boolean, nullable=False, server_default="false")  # Archive status

    # Token tracking
    context_window_size = Column(Integer, nullable=False, server_default="2048")  # Max tokens for this model
    current_token_count = Column(Integer, nullable=False, server_default="0")  # Current total tokens used

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    domain = relationship("Domain")
    user = relationship("User", back_populates="conversations")
    messages = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at"
    )

    def __repr__(self):
        return f"<Conversation(id={self.id}, title='{self.title}', model='{self.model}', provider='{self.provider}', messages={len(self.messages) if self.messages else 0})>"


class Message(Base):
    """Model for storing individual messages in a conversation"""

    __tablename__ = "messages"

    # Primary identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)

    # Message content
    role = Column(String(50), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)

    # Compression tracking
    is_summary = Column(Boolean, nullable=True, default=False)  # True if this is a compressed summary

    # Token tracking
    token_count = Column(Integer, nullable=True)  # Token count for this message

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        return f"<Message(id={self.id}, role='{self.role}', conversation_id={self.conversation_id})>"


class MessageArchive(Base):
    """Model for storing archived messages - used for compression without data loss"""

    __tablename__ = "messages_archive"

    # Primary identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Original message reference
    original_message_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)

    # Message content (copied from original)
    role = Column(String(50), nullable=False)  # 'user', 'assistant'
    content = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=True)

    # Original timestamp
    original_created_at = Column(DateTime(timezone=True), nullable=False)

    # Archive metadata
    archived_at = Column(DateTime(timezone=True), server_default=func.now())
    summary_message_id = Column(UUID(as_uuid=True), nullable=True)  # Reference to summary that replaced these messages

    # Relationship
    conversation = relationship("Conversation")

    def __repr__(self):
        return f"<MessageArchive(id={self.id}, original_id={self.original_message_id}, role='{self.role}')>"


class LyricParsingRule(Base):
    """Model for storing configurable lyric parsing rules (cleanup and section detection)"""

    __tablename__ = "lyric_parsing_rules"

    # Primary identifier
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Domain ownership (multi-tenancy: belongs to System domain)
    domain_id = Column(UUID(as_uuid=True), ForeignKey("domains.id"), nullable=True, index=True)

    # Rule metadata
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # Rule logic
    pattern = Column(Text, nullable=False)  # Regex pattern (JSON-escaped)
    replacement = Column(Text, nullable=False)  # Replacement string
    rule_type = Column(String(50), nullable=False, index=True)  # cleanup, section

    # Control
    active = Column(Boolean, default=True, nullable=False, index=True)
    order = Column(Integer, nullable=False, default=0, index=True)  # Execution order

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    domain = relationship("Domain")

    def __repr__(self):
        return f"<LyricParsingRule(id={self.id}, name='{self.name}', type='{self.rule_type}', active={self.active}, order={self.order})>"


class ApiCostMonthly(Base):
    """Model for monthly API cost caching with TTL support"""

    __tablename__ = "api_costs_monthly"

    # Primary identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Provider and organization
    provider = Column(String(50), nullable=False, index=True)  # 'openai'
    organization_id = Column(String(100), nullable=True, index=True)  # User-specific keys (optional)

    # Time period
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False, index=True)  # 1-12

    # Aggregated costs
    total_cost = Column(Numeric(12, 6), nullable=False)
    image_cost = Column(Numeric(12, 6), default=0)  # DALL-E costs
    chat_cost = Column(Numeric(12, 6), default=0)  # GPT costs
    currency = Column(String(3), default="usd")

    # Details
    line_items = Column(JSONB, nullable=True)  # Full breakdown by line_item
    bucket_count = Column(Integer, nullable=True)  # Debug: Number of days/buckets
    project_ids = Column(ARRAY(Text), nullable=True)  # Filtered projects (optional)

    # Caching metadata (for Hybrid-Caching with TTL)
    is_finalized = Column(Boolean, default=False, nullable=False, index=True)  # TRUE = Past month (never reload)
    last_updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)  # Last API update

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<ApiCostMonthly(provider='{self.provider}', year={self.year}, month={self.month}, total={self.total_cost}, finalized={self.is_finalized})>"


class Equipment(Base):
    """Model for storing software and plugin licenses with encrypted sensitive data"""

    __tablename__ = "equipment"

    # Primary identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Core fields
    type = Column(String(50), nullable=False, index=True)  # 'Software' | 'Plugin'
    name = Column(String(200), nullable=False)
    version = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)

    # Tags (comma-separated)
    software_tags = Column(String(1000), nullable=True)
    plugin_tags = Column(String(1000), nullable=True)

    # Manufacturer info
    manufacturer = Column(String(200), nullable=True)
    url = Column(String(500), nullable=True)

    # Credentials (encrypted with Fernet)
    username = Column(String(200), nullable=True)
    password_encrypted = Column(Text, nullable=True)

    # License management
    license_management = Column(String(100), nullable=True)  # 'online' | 'ilok' | 'license_key' | 'other'
    license_key_encrypted = Column(Text, nullable=True)
    license_description = Column(Text, nullable=True)

    # Purchase information
    purchase_date = Column(Date, nullable=True)
    price_encrypted = Column(Text, nullable=True)  # Format: "299.99 EUR" (encrypted)

    # System requirements
    system_requirements = Column(Text, nullable=True)

    # Status (multi-state workflow like Sketch)
    status = Column(
        String(50), nullable=False, default="active", index=True
    )  # 'active' | 'trial' | 'expired' | 'archived'

    # Domain ownership (multi-tenancy)
    domain_id = Column(UUID(as_uuid=True), ForeignKey("domains.id"), nullable=False, index=True)

    # User reference (created_by / audit trail)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    domain = relationship("Domain")
    user = relationship("User", back_populates="equipment")
    attachments = relationship("EquipmentAttachment", back_populates="equipment", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Equipment(id={self.id}, type='{self.type}', name='{self.name}', status='{self.status}')>"


class EquipmentAttachment(Base):
    """Model for equipment file attachments (license files, manuals, etc.)"""

    __tablename__ = "equipment_attachments"

    # Primary identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Foreign keys
    equipment_id = Column(
        UUID(as_uuid=True), ForeignKey("equipment.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Domain ownership (multi-tenancy)
    domain_id = Column(UUID(as_uuid=True), ForeignKey("domains.id"), nullable=False, index=True)

    # User reference (created_by / audit trail)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # File metadata
    filename = Column(String(500), nullable=False)
    s3_key = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    content_type = Column(String(100), nullable=False)

    # Timestamp
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    domain = relationship("Domain")
    equipment = relationship("Equipment", back_populates="attachments")

    def __repr__(self):
        return f"<EquipmentAttachment(id={self.id}, filename='{self.filename}', equipment_id={self.equipment_id})>"


class SongProject(Base):
    """Model for song project management with S3 storage"""

    __tablename__ = "song_projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Domain ownership (multi-tenancy)
    domain_id = Column(UUID(as_uuid=True), ForeignKey("domains.id"), nullable=False, index=True)

    # User reference (created_by / audit trail)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    project_name = Column(String(255), nullable=False)

    # Storage
    s3_prefix = Column(String(255), nullable=True)
    local_path = Column(String(500), nullable=True)

    # Project Status
    project_status = Column(String(20), nullable=False, server_default="progress")  # 'new', 'progress', 'archived'

    # Metadata
    cover_image_id = Column(UUID(as_uuid=True), ForeignKey("generated_images.id", ondelete="SET NULL"), nullable=True)
    tags = Column(ARRAY(String), server_default="{}")
    description = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    domain = relationship("Domain")
    user = relationship("User", back_populates="song_projects")
    folders = relationship(
        "ProjectFolder", back_populates="project", cascade="all, delete-orphan", order_by="ProjectFolder.folder_name"
    )
    files = relationship("ProjectFile", back_populates="project", cascade="all, delete-orphan")
    sketches = relationship("SongSketch", back_populates="project")
    image_references = relationship("ProjectImageReference", back_populates="project", cascade="all, delete-orphan")
    release_references = relationship("ReleaseProjectReference", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SongProject(id={self.id}, name='{self.project_name}', status='{self.project_status}')>"


class ProjectFolder(Base):
    """Model for project folder structure in S3"""

    __tablename__ = "project_folders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("song_projects.id", ondelete="CASCADE"), nullable=False, index=True
    )

    folder_name = Column(String(255), nullable=False)
    folder_type = Column(String(50), nullable=True)
    s3_prefix = Column(String(255), nullable=True)
    custom_icon = Column(String(50), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    project = relationship("SongProject", back_populates="folders")
    files = relationship("ProjectFile", back_populates="folder", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ProjectFolder(id={self.id}, name='{self.folder_name}', type='{self.folder_type}')>"


class ProjectFile(Base):
    """Model for files within song projects"""

    __tablename__ = "project_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("song_projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    folder_id = Column(
        UUID(as_uuid=True), ForeignKey("project_folders.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # File Info
    filename = Column(String(255), nullable=False)
    relative_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=True)
    mime_type = Column(String(100), nullable=True)

    # Storage
    s3_key = Column(String(255), nullable=True, index=True)
    local_path = Column(String(500), nullable=True)
    file_size_bytes = Column(BigInteger, nullable=True)  # BigInteger supports files >2GB
    file_hash = Column(String(64), nullable=True)

    # Sync
    storage_backend = Column(String(20), server_default="s3")
    is_synced = Column(Boolean, server_default="false")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    project = relationship("SongProject", back_populates="files")
    folder = relationship("ProjectFolder", back_populates="files")

    def __repr__(self):
        return f"<ProjectFile(id={self.id}, filename='{self.filename}', synced={self.is_synced}')>"


class ProjectImageReference(Base):
    """Model for N:M relationship between projects and images"""

    __tablename__ = "project_image_references"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("song_projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    image_id = Column(
        UUID(as_uuid=True), ForeignKey("generated_images.id", ondelete="CASCADE"), nullable=False, index=True
    )
    folder_id = Column(UUID(as_uuid=True), ForeignKey("project_folders.id", ondelete="SET NULL"), nullable=True)
    display_order = Column(Integer, server_default="0", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    project = relationship("SongProject", back_populates="image_references")
    image = relationship("GeneratedImage", back_populates="project_references")
    folder = relationship("ProjectFolder")

    def __repr__(self):
        return f"<ProjectImageReference(project_id={self.project_id}, image_id={self.image_id}, folder_id={self.folder_id})>"


class SongRelease(Base):
    """Model for song release tracking (Single/Album)"""

    __tablename__ = "song_releases"

    # Primary identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Domain ownership (multi-tenancy)
    domain_id = Column(UUID(as_uuid=True), ForeignKey("domains.id"), nullable=False, index=True)

    # User reference (created_by / audit trail)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Core fields
    type = Column(String(20), nullable=False, index=True)  # 'single', 'album'
    name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, server_default="draft", index=True)
    # Status: 'draft', 'arranging', 'mixing', 'mastering', 'pre_release', 'rejected', 'uploaded', 'released', 'downtaken', 'archived'

    # Metadata
    description = Column(Text, nullable=True)
    genre = Column(String(100), nullable=False)
    tags = Column(String(500), nullable=True)  # Comma-separated

    # Dates
    upload_date = Column(Date, nullable=True)
    release_date = Column(Date, nullable=True)
    downtaken_date = Column(Date, nullable=True)

    # Reasons
    downtaken_reason = Column(Text, nullable=True)
    rejected_reason = Column(Text, nullable=True)

    # Industry identifiers
    upc = Column(String(50), nullable=True)  # Universal Product Code
    isrc = Column(String(50), nullable=True)  # International Standard Recording Code
    copyright_info = Column(Text, nullable=True)
    smart_link = Column(String(1000), nullable=True)  # Smart link (DistroKid HyperFollow, ToneDen, etc.)

    # Cover image (S3 upload, not generated_images)
    cover_s3_key = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    domain = relationship("Domain")
    user = relationship("User", back_populates="song_releases")
    project_references = relationship("ReleaseProjectReference", back_populates="release", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SongRelease(id={self.id}, name='{self.name}', type='{self.type}', status='{self.status}')>"


class ReleaseProjectReference(Base):
    """Model for N:M relationship between releases and song projects"""

    __tablename__ = "release_project_references"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    release_id = Column(
        UUID(as_uuid=True), ForeignKey("song_releases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("song_projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    release = relationship("SongRelease", back_populates="project_references")
    project = relationship("SongProject", back_populates="release_references")

    def __repr__(self):
        return f"<ReleaseProjectReference(release_id={self.release_id}, project_id={self.project_id})>"
