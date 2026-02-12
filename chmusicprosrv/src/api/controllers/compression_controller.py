"""Compression Controller - HTTP request/response handling for conversation compression (Controller layer)."""

import uuid
from typing import Any

from sqlalchemy.orm import Session

from business.compression_orchestrator import CompressionOrchestrator


class CompressionController:
    """Controller for compressing conversations (HTTP handling only, delegates to orchestrator)."""

    def __init__(self):
        self.orchestrator = CompressionOrchestrator()

    def compress_conversation(
        self, db: Session, conversation_id: uuid.UUID, domain_id: uuid.UUID, keep_recent: int = 2
    ) -> tuple[dict[str, Any], int]:
        """
        Compress a conversation by archiving old messages and creating an AI summary.

        Args:
            db: Database session
            conversation_id: Conversation UUID
            domain_id: Domain UUID
            keep_recent: Number of recent messages to keep (default: 2)

        Returns:
            Tuple of (response_data, status_code)
        """
        return self.orchestrator.compress_conversation(db, conversation_id, domain_id, keep_recent)

    def restore_archive(
        self, db: Session, conversation_id: uuid.UUID, domain_id: uuid.UUID
    ) -> tuple[dict[str, Any], int]:
        """
        Restore archived messages for a conversation.

        Args:
            db: Database session
            conversation_id: Conversation UUID
            domain_id: Domain UUID

        Returns:
            Tuple of (response_data, status_code)
        """
        return self.orchestrator.restore_archive(db, conversation_id, domain_id)
