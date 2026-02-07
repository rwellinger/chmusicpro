"""
Zentrale Konfiguration für alle Module
"""

import os
import sys

from dotenv import load_dotenv


# Load correct .env file based on environment
# Priority:
# 1. DOTENV_FILE environment variable (e.g., DOTENV_FILE=.env_mock python src/server.py)
# 2. pytest detected → .env_pytest (unit tests only, no DB)
# 3. Default → .env (development/production)
dotenv_file = os.getenv("DOTENV_FILE")
if not dotenv_file:
    dotenv_file = ".env_pytest" if "pytest" in sys.modules else ".env"

load_dotenv(dotenv_file)

# --------------------------------------------------
# OpenAI Config (Images + Chat + Admin API)
# --------------------------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ADMIN_API_KEY = os.getenv("OPENAI_ADMIN_API_KEY")
OPENAI_ADMIN_BASE_URL = os.getenv("OPENAI_ADMIN_BASE_URL", "https://api.openai.com/v1")
OPENAI_IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "dall-e-3")
OPENAI_CHAT_MODELS = os.getenv(
    "OPENAI_CHAT_MODELS", "gpt-5,gpt-5-mini,gpt-5-nano,gpt-4o,gpt-4o-mini,gpt-4.1,gpt-4.1-mini"
)
OPENAI_TIMEOUT = int(os.getenv("OPENAI_TIMEOUT", "120"))
OPENAI_ADMIN_TIMEOUT = int(os.getenv("OPENAI_ADMIN_TIMEOUT", "30"))
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "4096"))

# Backwards compatibility (deprecated - use OPENAI_ADMIN_BASE_URL + endpoints)
OPENAI_URL = os.getenv("OPENAI_URL", f"{OPENAI_ADMIN_BASE_URL}/images")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", OPENAI_IMAGE_MODEL)

# --------------------------------------------------
# Claude Config (Anthropic Claude API)
# --------------------------------------------------
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
CLAUDE_BASE_URL = os.getenv("CLAUDE_BASE_URL", "https://api.anthropic.com/v1")
CLAUDE_API_VERSION = os.getenv("CLAUDE_API_VERSION", "2023-06-01")
CLAUDE_CHAT_MODELS = os.getenv(
    "CLAUDE_CHAT_MODELS", "claude-sonnet-4-5-20250929,claude-haiku-4-5-20250929,claude-opus-4-5-20251101"
)
CLAUDE_TIMEOUT = int(os.getenv("CLAUDE_TIMEOUT", "120"))
CLAUDE_MAX_TOKENS = int(os.getenv("CLAUDE_MAX_TOKENS", "4096"))

# --------------------------------------------------
# Image URL Config
# --------------------------------------------------
IMAGE_BASE_URL = os.getenv("IMAGE_BASE_URL", "http://localhost:8000/api/v1/image")

# --------------------------------------------------
# Flask Server Config
# --------------------------------------------------
FLASK_SERVER_PORT = int(os.getenv("FLASK_SERVER_PORT", "5050"))
FLASK_SERVER_HOST = os.getenv("FLASK_SERVER_HOST", "0.0.0.0")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# --------------------------------------------------
# loguru
# --------------------------------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG" if DEBUG else "WARNING")


# --------------------------------------------------
# Chat Debug Config
# --------------------------------------------------
CHAT_DEBUG_LOGGING = os.getenv("CHAT_DEBUG_LOGGING", "false").lower() == "true"


# --------------------------------------------------
# Image Storage Config
# --------------------------------------------------
IMAGES_DIR = os.getenv("IMAGES_DIR", "./images" if DEBUG else "/images")
# Control if physical files should be deleted (defaults to true if not set)
# Only set to false in special cases where you want to keep files but delete DB records
DELETE_PHYSICAL_FILES = os.getenv("DELETE_PHYSICAL_FILES", "true").lower() == "true"

# --------------------------------------------------
# S3 Storage Config (MinIO / AWS / Backblaze / Wasabi)
# --------------------------------------------------
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "s3")  # 's3' or 'filesystem'
S3_PROVIDER = os.getenv("S3_PROVIDER", "minio")  # 'minio', 'aws', 'backblaze', 'wasabi'
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://localhost:9000")
S3_BUCKET = os.getenv("S3_BUCKET", "aiproxy-media")  # Default bucket for songs, etc.
S3_SONG_PROJECTS_BUCKET = os.getenv("S3_SONG_PROJECTS_BUCKET", "song-projects")  # Dedicated bucket for song projects
S3_SONG_RELEASES_BUCKET = os.getenv("S3_SONG_RELEASES_BUCKET", "song-releases")  # Dedicated bucket for song releases
S3_SONGS_BUCKET = os.getenv("S3_SONGS_BUCKET", "songs")  # Dedicated bucket for songs (MP3/FLAC/stems)
S3_IMAGES_BUCKET = os.getenv("S3_IMAGES_BUCKET", "ai-generated-images")  # Dedicated bucket for AI-generated images
S3_EQUIPMENT_DATA_BUCKET = os.getenv("S3_EQUIPMENT_DATA_BUCKET", "equipment-data")  # Equipment file attachments
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "minioadmin")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "minioadmin")
S3_REGION = os.getenv("S3_REGION", "us-east-1")

# --------------------------------------------------
# Ollama Config
# --------------------------------------------------
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "60"))
OLLAMA_CHAT_MODELS = os.getenv("OLLAMA_CHAT_MODELS", "")
OLLAMA_DEFAULT_MODEL = os.getenv("OLLAMA_DEFAULT_MODEL", "llama3.2:3b")
OLLAMA_ALLOWED_MODELS = os.getenv("OLLAMA_ALLOWED_MODELS", "llama3.2:3b,gpt-oss:20b,deepseek-r1:8b,gemma3:4b")
OLLAMA_SUMMARY_MODEL = os.getenv("OLLAMA_SUMMARY_MODEL", "")  # Empty = use conversation model

# --------------------------------------------------
# JWT Authentication Config
# --------------------------------------------------
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "240"))

# --------------------------------------------------
# Encryption Config (Fernet symmetric encryption)
# --------------------------------------------------
# Generate key with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_SECRET_KEY = os.getenv("ENCRYPTION_SECRET_KEY", "")

# --------------------------------------------------
# Database Config
# --------------------------------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://aiproxy:aiproxy123@localhost:5432/aiproxysrv"
    if DEBUG
    else "postgresql://aiproxy:aiproxy123@postgres:5432/aiproxysrv",
)
DATABASE_ECHO = os.getenv("DATABASE_ECHO", "false").lower() == "true"

# Database Connection Pool Settings
# pool_size: Number of permanent connections in the pool
# max_overflow: Additional connections when pool is exhausted
# pool_pre_ping: Test connections before using (prevents stale connections)
# pool_recycle: Recycle connections after N seconds (prevents stale connections)
DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "10"))
DATABASE_MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
DATABASE_POOL_PRE_PING = os.getenv("DATABASE_POOL_PRE_PING", "true").lower() == "true"
DATABASE_POOL_RECYCLE = int(os.getenv("DATABASE_POOL_RECYCLE", "3600"))  # 1 hour default
