"""add_model_context_windows

Revision ID: b4c7d8e9f0a1
Revises: f3a1b2c4d5e6
Create Date: 2026-02-20 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b4c7d8e9f0a1"
down_revision: str | Sequence[str] | None = "f3a1b2c4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create model_context_windows table
    op.create_table(
        "model_context_windows",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("context_window", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=50), server_default="ollama", nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("model_name", name="uq_model_context_windows_model_name"),
    )

    # Seed with default data
    model_context_windows = sa.table(
        "model_context_windows",
        sa.column("model_name", sa.String),
        sa.column("context_window", sa.Integer),
        sa.column("provider", sa.String),
        sa.column("description", sa.String),
    )

    op.bulk_insert(
        model_context_windows,
        [
            # OpenAI Models - GPT-5 Series
            {"model_name": "gpt-5.1", "context_window": 200000, "provider": "openai", "description": "GPT-5.1"},
            {
                "model_name": "gpt-5.1-codex-mini",
                "context_window": 200000,
                "provider": "openai",
                "description": "GPT-5.1 Codex Mini",
            },
            {"model_name": "gpt-5", "context_window": 200000, "provider": "openai", "description": "GPT-5 base"},
            {"model_name": "gpt-5-pro", "context_window": 200000, "provider": "openai", "description": "GPT-5 Pro"},
            {"model_name": "gpt-5-mini", "context_window": 200000, "provider": "openai", "description": "GPT-5 Mini"},
            {"model_name": "gpt-5-nano", "context_window": 200000, "provider": "openai", "description": "GPT-5 Nano"},
            {"model_name": "gpt-5-codex", "context_window": 200000, "provider": "openai", "description": "GPT-5 Codex"},
            {
                "model_name": "gpt-5-chat-latest",
                "context_window": 200000,
                "provider": "openai",
                "description": "GPT-5 Chat Latest",
            },
            # OpenAI Models - GPT-4.1 Series
            {"model_name": "gpt-4.1", "context_window": 128000, "provider": "openai", "description": "GPT-4.1 base"},
            {
                "model_name": "gpt-4.1-mini",
                "context_window": 128000,
                "provider": "openai",
                "description": "GPT-4.1 Mini",
            },
            {
                "model_name": "gpt-4.1-nano",
                "context_window": 128000,
                "provider": "openai",
                "description": "GPT-4.1 Nano",
            },
            # OpenAI Models - GPT-4o Series
            {"model_name": "gpt-4o", "context_window": 128000, "provider": "openai", "description": "GPT-4o"},
            {"model_name": "gpt-4o-mini", "context_window": 128000, "provider": "openai", "description": "GPT-4o Mini"},
            # OpenAI Models - GPT-4 Series
            {"model_name": "gpt-4-turbo", "context_window": 128000, "provider": "openai", "description": "GPT-4 Turbo"},
            {"model_name": "gpt-4", "context_window": 8192, "provider": "openai", "description": "GPT-4"},
            # OpenAI Models - GPT-3.5 Series
            {
                "model_name": "gpt-3.5-turbo",
                "context_window": 16385,
                "provider": "openai",
                "description": "GPT-3.5 Turbo",
            },
            {
                "model_name": "gpt-3.5-turbo-16k",
                "context_window": 16385,
                "provider": "openai",
                "description": "GPT-3.5 Turbo 16k",
            },
            # Ollama Models - GPT-OSS
            {"model_name": "gpt-oss:20b", "context_window": 8192, "provider": "ollama", "description": "GPT-OSS 20B"},
            # DeepSeek Models
            {
                "model_name": "deepseek-r1:8b",
                "context_window": 131072,
                "provider": "ollama",
                "description": "DeepSeek R1 8B (128k)",
            },
            # Apertus Models
            {
                "model_name": "MichelRosselli/apertus:latest",
                "context_window": 65536,
                "provider": "ollama",
                "description": "Apertus (64k)",
            },
            # LLaMA Models
            {"model_name": "llama2:7b", "context_window": 4096, "provider": "ollama", "description": "LLaMA 2 7B"},
            {"model_name": "llama2:13b", "context_window": 4096, "provider": "ollama", "description": "LLaMA 2 13B"},
            {"model_name": "llama2:70b", "context_window": 4096, "provider": "ollama", "description": "LLaMA 2 70B"},
            {"model_name": "llama3:8b", "context_window": 8192, "provider": "ollama", "description": "LLaMA 3 8B"},
            {"model_name": "llama3:70b", "context_window": 8192, "provider": "ollama", "description": "LLaMA 3 70B"},
            {
                "model_name": "llama3.1:8b",
                "context_window": 131072,
                "provider": "ollama",
                "description": "LLaMA 3.1 8B (128k)",
            },
            {
                "model_name": "llama3.1:70b",
                "context_window": 131072,
                "provider": "ollama",
                "description": "LLaMA 3.1 70B (128k)",
            },
            {
                "model_name": "llama3.2:1b",
                "context_window": 131072,
                "provider": "ollama",
                "description": "LLaMA 3.2 1B (128k)",
            },
            {
                "model_name": "llama3.2:3b",
                "context_window": 131072,
                "provider": "ollama",
                "description": "LLaMA 3.2 3B (128k)",
            },
            # Mistral Models
            {"model_name": "mistral:7b", "context_window": 8192, "provider": "ollama", "description": "Mistral 7B"},
            {
                "model_name": "mistral:instruct",
                "context_window": 8192,
                "provider": "ollama",
                "description": "Mistral Instruct",
            },
            {
                "model_name": "mixtral:8x7b",
                "context_window": 32768,
                "provider": "ollama",
                "description": "Mixtral 8x7B (32k)",
            },
            # Gemma Models
            {"model_name": "gemma:2b", "context_window": 8192, "provider": "ollama", "description": "Gemma 2B"},
            {"model_name": "gemma:7b", "context_window": 8192, "provider": "ollama", "description": "Gemma 7B"},
            {"model_name": "gemma2:9b", "context_window": 8192, "provider": "ollama", "description": "Gemma 2 9B"},
            {"model_name": "gemma2:27b", "context_window": 8192, "provider": "ollama", "description": "Gemma 2 27B"},
            {
                "model_name": "gemma3:4b",
                "context_window": 131072,
                "provider": "ollama",
                "description": "Gemma 3 4B (128k)",
            },
            # CodeLlama Models
            {
                "model_name": "codellama:7b",
                "context_window": 16384,
                "provider": "ollama",
                "description": "CodeLlama 7B (16k)",
            },
            {
                "model_name": "codellama:13b",
                "context_window": 16384,
                "provider": "ollama",
                "description": "CodeLlama 13B (16k)",
            },
            {
                "model_name": "codellama:34b",
                "context_window": 16384,
                "provider": "ollama",
                "description": "CodeLlama 34B (16k)",
            },
            # Phi Models
            {"model_name": "phi3:mini", "context_window": 4096, "provider": "ollama", "description": "Phi-3 Mini"},
            {"model_name": "phi3:medium", "context_window": 4096, "provider": "ollama", "description": "Phi-3 Medium"},
            # Qwen Models
            {"model_name": "qwen:7b", "context_window": 8192, "provider": "ollama", "description": "Qwen 7B"},
            {"model_name": "qwen:14b", "context_window": 8192, "provider": "ollama", "description": "Qwen 14B"},
            {"model_name": "qwen2:7b", "context_window": 32768, "provider": "ollama", "description": "Qwen 2 7B (32k)"},
            {"model_name": "qwen3:8b", "context_window": 32768, "provider": "ollama", "description": "Qwen 3 8B (32k)"},
            {
                "model_name": "qwen3:30b",
                "context_window": 32768,
                "provider": "ollama",
                "description": "Qwen 3 30B (32k)",
            },
        ],
    )


def downgrade() -> None:
    op.drop_table("model_context_windows")
