# Database Implementation & Migration Guide

## Overview

This guide covers the workflow for database schema changes using SQLAlchemy and Alembic in the aiproxysrv backend.

## Architecture

### Core Components

**Database Stack**
- **PostgreSQL**: Primary database (Docker in development, native or Docker in production)
- **SQLAlchemy**: ORM for database operations
- **Alembic**: Database migration management
- **Pydantic**: Schema validation and serialization

**Directory Structure**
```
aiproxysrv/src/
├── db/
│   ├── database.py          # DB connection & session management
│   ├── models.py            # SQLAlchemy ORM models
│   └── base.py              # Base model class
├── alembic/
│   ├── versions/            # Migration files
│   ├── env.py               # Alembic environment config
│   └── alembic.ini          # Alembic configuration
└── schemas/
    └── *.py                 # Pydantic schemas (API layer)
```

## Workflow: Database Schema Changes

### 1. Update SQLAlchemy Model

**Location**: `src/db/models.py`

```python
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean
from sqlalchemy.sql import func
from .database import Base

class Song(Base):
    __tablename__ = "songs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    lyrics = Column(Text)
    model = Column(String(100))
    status = Column(String(50), default="processing")

    # Add new column
    genre = Column(String(100), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

**Common Column Types**
- `Integer`: Numeric IDs, counters
- `String(length)`: Fixed-length text (titles, names, enums)
- `Text`: Unlimited text (lyrics, prompts, descriptions)
- `Boolean`: True/False flags
- `DateTime(timezone=True)`: Timestamps
- `JSON`: Structured data (tags, metadata)
- `ARRAY(String)`: Lists of strings (PostgreSQL specific)

### 2. Generate Migration

```bash
cd src
alembic revision --autogenerate -m "add genre column to songs"
```

**Alembic will**:
- Compare current DB schema with SQLAlchemy models
- Generate migration file in `alembic/versions/`
- Create `upgrade()` and `downgrade()` functions

**Example Generated Migration**:
```python
# alembic/versions/abc123_add_genre_column_to_songs.py

def upgrade():
    op.add_column('songs', sa.Column('genre', sa.String(length=100), nullable=True))

def downgrade():
    op.drop_column('songs', 'genre')
```

### 3. Review Migration File

**IMPORTANT**: Always review auto-generated migrations before applying!

**Check for**:
- Correct table names
- Proper nullable constraints
- Default values
- Index creation if needed
- Data migrations (if renaming/transforming)

**Manual adjustments example**:
```python
def upgrade():
    # Add column with default value
    op.add_column('songs', sa.Column('genre', sa.String(length=100),
                                     nullable=False,
                                     server_default='unknown'))

    # Create index for performance
    op.create_index('idx_songs_genre', 'songs', ['genre'])

def downgrade():
    op.drop_index('idx_songs_genre', 'songs')
    op.drop_column('songs', 'genre')
```

### 4. Apply Migration

```bash
cd src
alembic upgrade head
```

**Verify**:
```bash
# Check current migration version
alembic current

# View migration history
alembic history

# Connect to DB and verify schema
docker exec -it mac_ki_service-postgres-1 psql -U aiuser -d aiproxy
\d songs
```

### 5. Update Pydantic Schemas

**Location**: `src/schemas/song_schemas.py`

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class SongBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    lyrics: Optional[str] = None
    model: Optional[str] = None
    genre: Optional[str] = Field(None, max_length=100)  # Add new field

class SongCreate(SongBase):
    pass

class SongResponse(SongBase):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True  # Enable ORM mode
```

### 6. Update Business Logic

**Location**: `src/api/*.py` or `src/business/*.py`

```python
# Example: Update song creation
def create_song(db: Session, song_data: SongCreate):
    song = Song(
        title=song_data.title,
        lyrics=song_data.lyrics,
        model=song_data.model,
        genre=song_data.genre,  # Use new field
        status="processing"
    )
    db.add(song)
    db.commit()
    db.refresh(song)
    return song
```

### 7. Test Changes

```bash
# Start PostgreSQL
docker compose up postgres -d

# Start development server
python src/server.py

# Test API endpoint
curl -X POST http://localhost:8000/api/v1/song/generate \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Song",
    "lyrics": "Test lyrics",
    "genre": "rock"
  }'
```

## Common Migration Scenarios

### Add Column with Default Value

```python
def upgrade():
    op.add_column('songs',
        sa.Column('rating', sa.Integer(), nullable=False, server_default='0'))

def downgrade():
    op.drop_column('songs', 'rating')
```

### Rename Column

```python
def upgrade():
    op.alter_column('songs', 'old_name', new_column_name='new_name')

def downgrade():
    op.alter_column('songs', 'new_name', new_column_name='old_name')
```

### Add Index

```python
def upgrade():
    op.create_index('idx_songs_status', 'songs', ['status'])

def downgrade():
    op.drop_index('idx_songs_status', 'songs')
```

### Add Foreign Key

```python
def upgrade():
    op.add_column('songs', sa.Column('user_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_songs_user', 'songs', 'users', ['user_id'], ['id'])

def downgrade():
    op.drop_constraint('fk_songs_user', 'songs', type_='foreignkey')
    op.drop_column('songs', 'user_id')
```

### Data Migration

```python
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add new column
    op.add_column('songs', sa.Column('workflow', sa.String(50), nullable=True))

    # Migrate existing data
    connection = op.get_bind()
    connection.execute(
        sa.text("UPDATE songs SET workflow = 'notUsed' WHERE workflow IS NULL")
    )

    # Make column non-nullable
    op.alter_column('songs', 'workflow', nullable=False)

def downgrade():
    op.drop_column('songs', 'workflow')
```

## Migration Management

### Check Current Version

```bash
cd src
alembic current
```

### View History

```bash
alembic history --verbose
```

### Rollback One Migration

```bash
alembic downgrade -1
```

### Rollback to Specific Version

```bash
alembic downgrade abc123  # Revision ID
```

### Rollback All Migrations

```bash
alembic downgrade base
```

### Show SQL Without Executing

```bash
alembic upgrade head --sql
```

## Troubleshooting

### Migration Fails

```bash
# Check database connection
docker compose ps postgres
docker compose logs postgres

# Verify alembic configuration
cat alembic.ini

# Check database state
docker exec -it mac_ki_service-postgres-1 psql -U aiuser -d aiproxy
SELECT * FROM alembic_version;
```

### Autogenerate Misses Changes

**Common causes**:
- Model not imported in `alembic/env.py`
- Database not up to date
- Naming convention issues

**Fix**:
```python
# alembic/env.py
from db.models import Base, Song, Image  # Import all models
target_metadata = Base.metadata
```

### Conflicting Migrations

```bash
# Check migration branches
alembic branches

# Merge branches if needed
alembic merge -m "merge migrations" <rev1> <rev2>
```

### Reset Database (Development Only)

```bash
# Stop services
docker compose down

# Remove volumes
docker volume rm mac_ki_service_postgres_data

# Restart and recreate
docker compose up postgres -d
cd src
alembic upgrade head
```

## Best Practices

### DO

✅ Always review auto-generated migrations
✅ Test migrations on development database first
✅ Include both `upgrade()` and `downgrade()`
✅ Add comments for complex migrations
✅ Use meaningful migration messages
✅ Commit migrations with code changes
✅ Keep migrations small and focused

### DON'T

❌ Edit applied migrations (create new ones instead)
❌ Skip migration review
❌ Combine unrelated schema changes
❌ Forget to update Pydantic schemas
❌ Apply untested migrations to production
❌ Delete migration files

## Production Deployment

### Pre-Deployment Checklist

- [ ] Test migration on development database
- [ ] Review migration SQL (`alembic upgrade head --sql`)
- [ ] Backup production database
- [ ] Plan rollback strategy
- [ ] Coordinate with frontend deployment if API changes

### Deployment Steps

```bash
# 1. Backup database
docker exec mac_ki_service-postgres-1 pg_dump -U aiuser aiproxy > backup.sql

# 2. Apply migration
docker exec -it mac_ki_service-aiproxysrv-1 bash
cd src
alembic upgrade head

# 3. Verify
alembic current

# 4. Restart services if needed
docker compose restart aiproxysrv
```

### Rollback Procedure

```bash
# Rollback migration
docker exec -it mac_ki_service-aiproxysrv-1 bash
cd src
alembic downgrade -1

# Verify
alembic current

# Restart services
docker compose restart aiproxysrv
```

## Quick Reference

### Common Commands

```bash
# Create migration
cd src && alembic revision --autogenerate -m "description"

# Apply migrations
cd src && alembic upgrade head

# Rollback one
cd src && alembic downgrade -1

# Check version
cd src && alembic current

# Show history
cd src && alembic history
```

### Database Access

```bash
# Connect to PostgreSQL
docker exec -it mac_ki_service-postgres-1 psql -U aiuser -d aiproxy

# Common psql commands
\dt              # List tables
\d table_name    # Describe table
\q               # Quit
```
