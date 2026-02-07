# 3-Layer Architecture Patterns (Current Implementation)

**Last Updated:** 2025-10-28
**Pattern:** Orchestrator → Transformer + Repository

---

## Overview

```
Controller (HTTP)
  └─> Orchestrator (coordinates services, NOT testable)
       ├─> Transformer/Normalizer (pure functions, 100% testable)
       └─> Repository (CRUD only, NO tests)
```

## Naming Convention

| File Pattern | Purpose | Testable? | Example |
|--------------|---------|-----------|---------|
| `*_orchestrator.py` | Coordinates services, NO business logic | ❌ No | `SketchOrchestrator`, `SongOrchestrator` |
| `*_transformer.py` | Pure functions: transformations, mappings | ✅ Yes (100%) | `SongMurekaTransformer` |
| `*_normalizer.py` | Pure functions: string normalization | ✅ Yes (100%) | `SketchNormalizer` |
| `*_auth_service.py` | Pure functions: authentication logic | ✅ Yes (100%) | `UserAuthService` |
| `*_service.py` (in `db/`) | CRUD operations only | ❌ No | `SketchService`, `SongService` |

---

## Pattern 1: Orchestrator (Coordination)

**Purpose:** Coordinates multiple services, handles orchestration logic
**Testable:** ❌ No (requires DB mocks, not worth testing)
**Location:** `src/business/*_orchestrator.py`

### Example: SketchOrchestrator

```python
from sqlalchemy.orm import Session
from business.sketch_normalizer import SketchNormalizer
from db.sketch_service import sketch_service

class SketchOrchestratorError(Exception):
    """Base exception for sketch orchestration errors"""
    pass

class SketchOrchestrator:
    """Orchestrates sketch operations (calls normalizer + repository)"""

    def create_sketch(
        self,
        db: Session,
        title: str | None,
        lyrics: str | None,
        prompt: str,
        tags: str | None = None,
    ):
        """
        Create sketch with data normalization

        Orchestration Flow:
        1. Normalize data (Transformer)
        2. Create in DB (Repository)
        3. Handle errors
        """
        try:
            # Step 1: Business logic (Transformer)
            normalized_data = SketchNormalizer.normalize_sketch_data({
                "title": title,
                "lyrics": lyrics,
                "prompt": prompt,
                "tags": tags,
            })

            # Step 2: Repository (CRUD)
            sketch = sketch_service.create_sketch(db=db, **normalized_data)

            if not sketch:
                raise SketchOrchestratorError("Failed to create sketch")

            return sketch

        except Exception as e:
            logger.error("Sketch creation failed", error=str(e))
            raise SketchOrchestratorError(f"Failed to create sketch: {e}") from e
```

**Key Points:**
- ✅ Calls other services (normalizer, repository)
- ✅ Handles orchestration logic (order of operations)
- ✅ Error handling and logging
- ❌ NO business logic (that's in transformers)
- ❌ NO direct DB queries (that's in repository)
- ❌ NO unit tests (only orchestration, needs mocks)

---

## Pattern 2: Transformer (Pure Functions)

**Purpose:** Transform data, parse responses, apply business rules
**Testable:** ✅ Yes (100% coverage, no mocks)
**Location:** `src/business/*_transformer.py`

### Example: SongMurekaTransformer

```python
from typing import Any

class SongMurekaTransformer:
    """Transform MUREKA API responses (pure functions)"""

    @staticmethod
    def parse_mureka_result(result_data: dict[str, Any]) -> dict[str, Any]:
        """
        Parse MUREKA API response to DB format

        Pure function - NO DB, NO file system, fully unit-testable

        Args:
            result_data: Raw MUREKA response

        Returns:
            Parsed data ready for DB insertion
        """
        choices = result_data.get("choices", [])
        model = result_data.get("model")
        status = result_data.get("status")

        # Parse each choice
        parsed_choices = [
            {
                "mureka_choice_id": choice.get("id"),
                "audio_url": choice.get("url"),
                "duration": SongMurekaTransformer.parse_duration(choice.get("duration")),
                "tags": SongMurekaTransformer.parse_tags_array(choice.get("tags", [])),
            }
            for choice in choices
        ]

        return {
            "choices": parsed_choices,
            "model": model,
            "status": status,
        }

    @staticmethod
    def parse_duration(duration: Any) -> float | None:
        """
        Parse duration from various formats (pure function)

        Handles: int, float, string, None
        """
        if duration is None:
            return None
        try:
            return float(duration)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def parse_tags_array(tags: list) -> str:
        """Convert tags array to comma-separated string (pure function)"""
        if not tags:
            return ""
        return ",".join(str(tag) for tag in tags if tag)
```

**Unit Tests (100% Coverage):**

```python
import pytest
from business.song_mureka_transformer import SongMurekaTransformer

class TestSongMurekaTransformer:
    def test_parse_mureka_result_success(self):
        """Test parsing valid MUREKA response"""
        result_data = {
            "status": "succeeded",
            "model": "mureka-7.5",
            "choices": [
                {
                    "id": "choice-123",
                    "url": "https://example.com/song.mp3",
                    "duration": 30567.89,
                    "tags": ["pop", "upbeat"]
                }
            ]
        }

        parsed = SongMurekaTransformer.parse_mureka_result(result_data)

        assert parsed["status"] == "succeeded"
        assert parsed["model"] == "mureka-7.5"
        assert len(parsed["choices"]) == 1
        assert parsed["choices"][0]["mureka_choice_id"] == "choice-123"
        assert parsed["choices"][0]["duration"] == 30567.89
        assert parsed["choices"][0]["tags"] == "pop,upbeat"

    def test_parse_duration_various_formats(self):
        """Test duration parsing with different input types"""
        assert SongMurekaTransformer.parse_duration(123) == 123.0
        assert SongMurekaTransformer.parse_duration(123.45) == 123.45
        assert SongMurekaTransformer.parse_duration("123.45") == 123.45
        assert SongMurekaTransformer.parse_duration(None) is None
        assert SongMurekaTransformer.parse_duration("invalid") is None

    def test_parse_tags_array(self):
        """Test tags array conversion"""
        assert SongMurekaTransformer.parse_tags_array(["pop", "rock"]) == "pop,rock"
        assert SongMurekaTransformer.parse_tags_array([]) == ""
        assert SongMurekaTransformer.parse_tags_array(["pop", None, "rock"]) == "pop,rock"
```

**Key Points:**
- ✅ Pure functions (@staticmethod)
- ✅ NO database dependencies
- ✅ NO file system operations
- ✅ 100% unit-testable without mocks
- ✅ Easy to verify business logic
- ✅ Fast tests (no infrastructure)

---

## Pattern 3: Normalizer (String Transformations)

**Purpose:** Normalize user input (trim, empty→None, etc.)
**Testable:** ✅ Yes (100% coverage, no mocks)
**Location:** `src/business/*_normalizer.py`

### Example: SketchNormalizer

```python
class SketchNormalizer:
    """Normalize sketch data (pure functions)"""

    @staticmethod
    def normalize_field(value: str | None) -> str | None:
        """
        Normalize string field: trim whitespace, convert empty to None

        Pure function - no dependencies, fully unit-testable

        Examples:
            "  hello  " -> "hello"
            "   " -> None
            "" -> None
            None -> None
        """
        if value is None:
            return None

        normalized = value.strip()
        return normalized if normalized else None

    @staticmethod
    def normalize_sketch_data(data: dict) -> dict:
        """
        Normalize all string fields in sketch data dict

        Pure function - no dependencies, fully unit-testable
        """
        normalizable_fields = [
            "title", "lyrics", "prompt", "tags",
            "description_long", "description_short",
        ]

        normalized = data.copy()
        for field in normalizable_fields:
            if field in normalized:
                normalized[field] = SketchNormalizer.normalize_field(normalized[field])

        return normalized
```

**Unit Tests:**

```python
class TestSketchNormalizer:
    def test_normalize_field_whitespace(self):
        """Test trimming whitespace"""
        assert SketchNormalizer.normalize_field("  hello  ") == "hello"

    def test_normalize_field_empty_to_none(self):
        """Test converting empty string to None"""
        assert SketchNormalizer.normalize_field("") is None
        assert SketchNormalizer.normalize_field("   ") is None

    def test_normalize_sketch_data_all_fields(self):
        """Test normalizing all fields"""
        data = {
            "title": "  My Title  ",
            "lyrics": "   ",
            "prompt": "pop",
        }

        result = SketchNormalizer.normalize_sketch_data(data)

        assert result["title"] == "My Title"
        assert result["lyrics"] is None  # Empty string -> None
        assert result["prompt"] == "pop"
```

---

## Pattern 4: Repository (CRUD Only)

**Purpose:** Database operations only (CRUD, queries)
**Testable:** ❌ No (infrastructure, not worth testing)
**Location:** `src/db/*_service.py`

### Example: SketchService

```python
from sqlalchemy.orm import Session
from db.models import SongSketch
from utils.logger import logger

class SketchService:
    """Service for sketch database operations (CRUD only)"""

    def create_sketch(
        self,
        db: Session,
        title: str | None,
        lyrics: str | None,
        prompt: str,
        tags: str | None = None,
        workflow: str = "draft",
    ) -> SongSketch | None:
        """
        Create new sketch (pure CRUD)

        IMPORTANT: Expects PRE-NORMALIZED data from business layer!
        """
        try:
            sketch = SongSketch(
                title=title,
                lyrics=lyrics,
                prompt=prompt,
                tags=tags,
                workflow=workflow,
            )

            db.add(sketch)
            db.commit()
            db.refresh(sketch)

            logger.info("Sketch created", sketch_id=str(sketch.id))
            return sketch

        except SQLAlchemyError as e:
            db.rollback()
            logger.error("Sketch creation failed", error=str(e))
            return None

    def get_sketch_by_id(self, db: Session, sketch_id: str) -> SongSketch | None:
        """Get sketch by ID (pure CRUD)"""
        try:
            return db.query(SongSketch).filter(SongSketch.id == sketch_id).first()
        except Exception as e:
            logger.error("Error getting sketch", sketch_id=sketch_id, error=str(e))
            return None

    def update_sketch(
        self,
        db: Session,
        sketch_id: str,
        **update_fields
    ) -> SongSketch | None:
        """
        Update sketch (pure CRUD)

        IMPORTANT: Expects PRE-NORMALIZED data from business layer!
        """
        try:
            sketch = db.query(SongSketch).filter(SongSketch.id == sketch_id).first()
            if not sketch:
                return None

            for field, value in update_fields.items():
                setattr(sketch, field, value)

            db.commit()
            db.refresh(sketch)

            logger.info("Sketch updated", sketch_id=sketch_id)
            return sketch

        except SQLAlchemyError as e:
            db.rollback()
            logger.error("Sketch update failed", error=str(e))
            return None
```

**Key Points:**
- ✅ CRUD operations only
- ✅ SQLAlchemy queries
- ✅ Transaction management (commit/rollback)
- ❌ NO business logic (expects pre-transformed data)
- ❌ NO string normalization (done in normalizer)
- ❌ NO unit tests (pure infrastructure, not testable without DB)

---

## Complete Flow Example

### Sketch Creation (End-to-End)

```python
# 1. Route (HTTP Entry Point)
@api_sketch_v1.route("", methods=["POST"])
@jwt_required
def create_sketch_route():
    user_id = get_current_user_id()
    db = next(get_db())
    try:
        data = request.json
        response, status = sketch_controller.create_sketch(db, data)
        return jsonify(response), status
    finally:
        db.close()

# 2. Controller (HTTP Handling)
class SketchController:
    @staticmethod
    def create_sketch(db: Session, sketch_data):
        try:
            orchestrator = SketchOrchestrator()
            sketch = orchestrator.create_sketch(
                db=db,
                title=sketch_data.get("title"),
                lyrics=sketch_data.get("lyrics"),
                prompt=sketch_data.get("prompt"),
            )
            return {"data": sketch.to_dict()}, 201
        except SketchOrchestratorError as e:
            return {"error": str(e)}, 500

# 3. Orchestrator (Coordination)
class SketchOrchestrator:
    def create_sketch(self, db, title, lyrics, prompt):
        # Business logic: Normalize
        normalized = SketchNormalizer.normalize_sketch_data({
            "title": title,
            "lyrics": lyrics,
            "prompt": prompt,
        })

        # Repository: Create
        sketch = sketch_service.create_sketch(db, **normalized)
        return sketch

# 4. Normalizer (Pure Function, TESTED)
class SketchNormalizer:
    @staticmethod
    def normalize_sketch_data(data):
        return {
            "title": normalize_field(data.get("title")),
            "lyrics": normalize_field(data.get("lyrics")),
            "prompt": normalize_field(data.get("prompt")),
        }

# 5. Repository (CRUD)
class SketchService:
    def create_sketch(self, db, title, lyrics, prompt):
        sketch = SongSketch(title=title, lyrics=lyrics, prompt=prompt)
        db.add(sketch)
        db.commit()
        return sketch
```

---

## Anti-Patterns (What NOT to Do)

### ❌ Business Logic in Repository

```python
# ❌ BAD: String normalization in repository
class SketchService:
    def create_sketch(self, db, title, lyrics):
        # ❌ Business logic in DB layer!
        title = title.strip() if title else None
        lyrics = lyrics.strip() if lyrics else None

        sketch = SongSketch(title=title, lyrics=lyrics)
        db.add(sketch)
        db.commit()
        return sketch
```

**Why bad:** Not unit-testable, mixed concerns

### ❌ Direct DB Queries in Orchestrator

```python
# ❌ BAD: Direct DB queries in orchestrator
class SketchOrchestrator:
    def create_sketch(self, db, title):
        # ❌ Direct DB query!
        sketch = db.query(SongSketch).filter(...).first()
        return sketch
```

**Why bad:** Orchestrator should call repository, not query DB directly

### ❌ Business Logic Without Tests

```python
# ❌ BAD: Complex logic without tests
class SomeOrchestrator:
    def complex_calculation(self, data):
        # 50 lines of complex business logic...
        # ❌ If this is in orchestrator, it's NOT tested!
        result = ...
        return result
```

**Why bad:** Extract to transformer for testing

---

## Migration Guide

### Converting Old Code to 3-Layer

**Before (Old Pattern):**
```python
class SketchService:
    def create_sketch(self, db, title, lyrics):
        # Mixed: normalization + DB
        title = title.strip() if title else None
        sketch = SongSketch(title=title)
        db.add(sketch)
        db.commit()
        return sketch
```

**After (3-Layer Pattern):**

**1. Create Normalizer (Pure Functions, TESTABLE):**
```python
# src/business/sketch_normalizer.py
class SketchNormalizer:
    @staticmethod
    def normalize_field(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized if normalized else None
```

**2. Create Orchestrator (Coordination):**
```python
# src/business/sketch_orchestrator.py
class SketchOrchestrator:
    def create_sketch(self, db, title, lyrics):
        normalized = SketchNormalizer.normalize_sketch_data({
            "title": title,
            "lyrics": lyrics,
        })
        return sketch_service.create_sketch(db, **normalized)
```

**3. Refactor Repository (CRUD Only):**
```python
# src/db/sketch_service.py
class SketchService:
    def create_sketch(self, db, title, lyrics):
        # Pure CRUD - expects pre-normalized data
        sketch = SongSketch(title=title, lyrics=lyrics)
        db.add(sketch)
        db.commit()
        return sketch
```

**4. Write Tests (For Normalizer):**
```python
# tests/business/test_sketch_normalizer.py
def test_normalize_field():
    assert SketchNormalizer.normalize_field("  test  ") == "test"
    assert SketchNormalizer.normalize_field("   ") is None
```

---

## Testing Strategy

### What to Test

✅ **DO test:**
- Transformers (100% coverage)
- Normalizers (100% coverage)
- Auth services (100% coverage)
- Pure functions (any business logic)

❌ **DO NOT test:**
- Orchestrators (only orchestration, needs mocks)
- Repositories (pure CRUD, infrastructure)
- File operations (infrastructure)
- External API clients (infrastructure)

### Example: Full Test Coverage

```
src/business/
├── sketch_orchestrator.py        ❌ 0% coverage (orchestration only)
├── sketch_normalizer.py          ✅ 100% coverage (pure functions)
├── song_orchestrator.py          ❌ 0% coverage (orchestration only)
├── song_mureka_transformer.py    ✅ 100% coverage (pure functions)
└── song_transformer.py           ✅ 100% coverage (pure functions)

src/db/
├── sketch_service.py             ❌ 0% coverage (CRUD only)
└── song_service.py               ❌ 0% coverage (CRUD only)

tests/business/
├── test_sketch_normalizer.py     ✅ 13 tests (100% coverage)
├── test_song_mureka_transformer.py ✅ 25 tests (100% coverage)
└── test_song_transformer.py      ✅ 11 tests (100% coverage)
```

---

## Summary

### 3-Layer Architecture Benefits

✅ **Testable:** Pure functions → 100% unit test coverage
✅ **Maintainable:** Clear separation of concerns
✅ **Scalable:** Easy to add new features
✅ **Fast Tests:** No DB, no mocks, instant feedback
✅ **Self-Documenting:** Clear naming convention

### Key Principles

1. **Orchestrators coordinate** - they don't contain logic
2. **Transformers/Normalizers are pure** - fully testable
3. **Repositories are dumb** - CRUD only, no business logic
4. **Tests focus on business logic** - not infrastructure

### Files Reference

**Implemented Examples:**
- `src/business/sketch_orchestrator.py` - Orchestration
- `src/business/sketch_normalizer.py` - Pure functions (tested)
- `src/business/song_orchestrator.py` - Orchestration
- `src/business/song_mureka_transformer.py` - Pure functions (tested)
- `src/business/song_transformer.py` - Pure functions (tested)
- `src/business/user_auth_service.py` - Pure functions (tested)

**See also:**
- `CLAUDE.md` - Architecture principles
- `docs/ARCHITECTURE.md` - System overview
- `.claude/dbsession-refactoring.md` - Migration history
