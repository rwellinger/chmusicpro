"""Orchestrator for model context windows with in-memory cache"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from utils.logger import logger


if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class ModelContextWindowOrchestrator:
    """Manages model context window lookups with cached DB access.

    Cache strategy:
    - All entries loaded from DB on first access
    - Cache refreshed after TTL (5 minutes)
    - Cache invalidated immediately on CRUD operations
    - Falls back to DEFAULT_CONTEXT_WINDOWS if DB unavailable
    """

    CACHE_TTL: int = 300  # 5 minutes

    def __init__(self) -> None:
        self._cache: dict[str, int] = {}
        self._cache_loaded_at: float = 0.0

    # ---- Cached lookup (main use case) ----

    def get_context_window(self, model_name: str) -> int:
        """Get context window size for a model (cached DB lookup).

        Lookup order: exact match -> base model match -> family match -> default 2048
        """
        self._ensure_cache()

        # Exact match
        if model_name in self._cache:
            return self._cache[model_name]

        # Base model match (e.g., "llama3:8b-instruct" -> "llama3:8b")
        base_model = model_name.split("-")[0]
        if base_model in self._cache:
            return self._cache[base_model]

        # Family match (e.g., "llama3" from "llama3:custom")
        model_family = model_name.split(":")[0]
        for key in self._cache:
            if key.startswith(model_family):
                return self._cache[key]

        return self._cache.get("default", 2048)

    def invalidate_cache(self) -> None:
        """Force cache reload on next access."""
        self._cache_loaded_at = 0.0

    # ---- Admin CRUD ----

    def list_all(self, db: Session) -> list[Any]:
        """Get all model context window entries (for admin UI)."""
        from db.models import ModelContextWindow

        return db.query(ModelContextWindow).order_by(ModelContextWindow.model_name).all()

    def create_entry(
        self, db: Session, model_name: str, context_window: int, provider: str, description: str | None
    ) -> Any:
        """Create a new entry and invalidate cache."""
        from db.models import ModelContextWindow

        entry = ModelContextWindow(
            model_name=model_name,
            context_window=context_window,
            provider=provider,
            description=description,
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        self.invalidate_cache()
        logger.info("model_context_window_created", model_name=model_name, context_window=context_window)
        return entry

    def update_entry(self, db: Session, entry_id: int, update_data: dict[str, Any]) -> Any | None:
        """Update an entry and invalidate cache."""
        from db.models import ModelContextWindow

        entry = db.query(ModelContextWindow).filter(ModelContextWindow.id == entry_id).first()
        if not entry:
            return None

        for field, value in update_data.items():
            setattr(entry, field, value)

        db.commit()
        db.refresh(entry)
        self.invalidate_cache()
        logger.info("model_context_window_updated", id=entry_id, fields=list(update_data.keys()))
        return entry

    def delete_entry(self, db: Session, entry_id: int) -> bool:
        """Delete an entry and invalidate cache."""
        from db.models import ModelContextWindow

        entry = db.query(ModelContextWindow).filter(ModelContextWindow.id == entry_id).first()
        if not entry:
            return False

        model_name = entry.model_name
        db.delete(entry)
        db.commit()
        self.invalidate_cache()
        logger.info("model_context_window_deleted", id=entry_id, model_name=model_name)
        return True

    # ---- Internal cache management ----

    def _ensure_cache(self) -> None:
        """Load cache from DB if expired or empty."""
        if time.time() - self._cache_loaded_at < self.CACHE_TTL and self._cache:
            return
        self._load_cache()

    def _load_cache(self) -> None:
        """Load all entries from DB into cache, merging with defaults."""
        from db.database import get_db

        db = next(get_db())
        try:
            from db.models import ModelContextWindow

            entries = db.query(ModelContextWindow).all()
            self._cache = {e.model_name: e.context_window for e in entries}

            # Merge defaults for entries not yet in DB
            from config.model_context_windows import DEFAULT_CONTEXT_WINDOWS

            for name, size in DEFAULT_CONTEXT_WINDOWS.items():
                if name not in self._cache:
                    self._cache[name] = size

            self._cache_loaded_at = time.time()
            logger.debug("model_context_window_cache_loaded", db_entries=len(entries), total=len(self._cache))
        except Exception as e:
            logger.warning("model_context_window_cache_load_failed", error=str(e))
            # Fallback to hardcoded defaults
            from config.model_context_windows import DEFAULT_CONTEXT_WINDOWS

            self._cache = dict(DEFAULT_CONTEXT_WINDOWS)
            self._cache_loaded_at = time.time()
        finally:
            db.close()


# Singleton instance
model_context_window_orchestrator = ModelContextWindowOrchestrator()
