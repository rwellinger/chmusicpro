# Code Patterns & Examples

**Project:** Multi-AI Creative Platform
**Last Updated:** 2025-10-22

---

## Angular Patterns

### Component (Modern inject() style)

```typescript
import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TranslateModule } from '@ngx-translate/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { ExampleService } from '@services/business/example.service';
import { Item } from '@models/item.model';

@Component({
  selector: 'app-example',
  standalone: true,
  imports: [CommonModule, TranslateModule, MaterialModules],
  templateUrl: './example.component.html',
  styleUrls: ['./example.component.scss']
})
export class ExampleComponent implements OnInit, OnDestroy {
  // Properties
  public items: Item[] = [];
  public loading = false;

  // Modern DI with inject()
  private destroy$ = new Subject<void>();
  private service = inject(ExampleService);
  private snackBar = inject(MatSnackBar);

  ngOnInit(): void {
    this.loadData();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadData(): void {
    this.loading = true;
    this.service.getData()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.items = data;
          this.loading = false;
        },
        error: (error) => {
          this.handleError(error);
          this.loading = false;
        }
      });
  }

  private handleError(error: any): void {
    console.error('Error loading data:', error);
    this.snackBar.open(
      'Failed to load data',
      'Close',
      { duration: 5000 }
    );
  }
}
```

### Service (Modern inject() style)

```typescript
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { map, catchError } from 'rxjs/operators';

import { ApiConfigService } from '@services/config/api-config.service';
import { Item } from '@models/item.model';
import { ApiResponse } from '@models/api-response.model';

@Injectable({ providedIn: 'root' })
export class ExampleService {
  private http = inject(HttpClient);
  private apiConfig = inject(ApiConfigService);

  public getData(): Observable<Item[]> {
    return this.http.get<ApiResponse<Item[]>>(
      this.apiConfig.endpoints.category.list()
    ).pipe(
      map(response => response.data),
      catchError(error => {
        console.error('API Error:', error);
        return throwError(() => error);
      })
    );
  }

  public getById(id: string): Observable<Item> {
    return this.http.get<ApiResponse<Item>>(
      this.apiConfig.endpoints.category.getById(id)
    ).pipe(
      map(response => response.data),
      catchError(error => throwError(() => error))
    );
  }

  public create(item: Partial<Item>): Observable<Item> {
    return this.http.post<ApiResponse<Item>>(
      this.apiConfig.endpoints.category.create(),
      item
    ).pipe(
      map(response => response.data),
      catchError(error => throwError(() => error))
    );
  }

  public update(id: string, item: Partial<Item>): Observable<Item> {
    return this.http.put<ApiResponse<Item>>(
      this.apiConfig.endpoints.category.update(id),
      item
    ).pipe(
      map(response => response.data),
      catchError(error => throwError(() => error))
    );
  }

  public delete(id: string): Observable<void> {
    return this.http.delete<void>(
      this.apiConfig.endpoints.category.delete(id)
    ).pipe(
      catchError(error => throwError(() => error))
    );
  }
}
```

### Component Template (i18n)

```html
<div class="example-container">
  <h2>{{ 'example.title' | translate }}</h2>

  <!-- Loading State -->
  <div *ngIf="loading" class="loading-spinner">
    <mat-spinner></mat-spinner>
    <p>{{ 'common.loading' | translate }}</p>
  </div>

  <!-- Data List -->
  <div *ngIf="!loading && items.length > 0" class="items-list">
    <mat-card *ngFor="let item of items" class="item-card">
      <mat-card-header>
        <mat-card-title>{{ item.title }}</mat-card-title>
        <mat-card-subtitle>
          {{ 'example.createdAt' | translate:{date: item.createdAt | date} }}
        </mat-card-subtitle>
      </mat-card-header>
      <mat-card-content>
        <p>{{ item.description }}</p>
      </mat-card-content>
      <mat-card-actions>
        <button mat-button (click)="onEdit(item.id)">
          {{ 'common.edit' | translate }}
        </button>
        <button mat-button color="warn" (click)="onDelete(item.id)">
          {{ 'common.delete' | translate }}
        </button>
      </mat-card-actions>
    </mat-card>
  </div>

  <!-- Empty State -->
  <div *ngIf="!loading && items.length === 0" class="empty-state">
    <p>{{ 'example.noItems' | translate }}</p>
    <button mat-raised-button color="primary" (click)="onCreate()">
      {{ 'example.createFirst' | translate }}
    </button>
  </div>
</div>
```

### SCSS (BEM Pattern)

```scss
.example-container {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
}

.items-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.item-card {
  height: 100%;
}

.empty-state {
  text-align: center;
  padding: 48px;
}

// ❌ BAD: Deep nesting
.player-bar {
  .player-content {
    .song-info {
      .title { } // 4 levels!
    }
  }
}

// ✅ GOOD: Flattened with BEM
.player-bar { }
.player-bar__content { }
.player-bar__song-info { }
.player-bar__title { }
```

---

## Python (FastAPI) Patterns

### Route Handler

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ..db.database import get_db
from ..schemas.song import SongCreate, SongUpdate, SongResponse, SongListResponse
from ..controllers.song_controller import SongController
from ..api.auth_middleware import jwt_required, get_current_user_id

router = APIRouter(prefix="/api/v1/songs", tags=["songs"])

@router.get("/", response_model=SongListResponse)
@jwt_required
async def list_songs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List songs with pagination and optional search.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        search: Optional search term for title/lyrics
        db: Database session

    Returns:
        SongListResponse with songs and pagination info
    """
    user_id = get_current_user_id()
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    controller = SongController(db)
    songs = controller.list_songs(
        user_id=user_id,
        skip=skip,
        limit=limit,
        search=search
    )

    return SongListResponse(
        data=songs,
        total=len(songs),
        skip=skip,
        limit=limit
    )

@router.get("/{song_id}", response_model=SongResponse)
@jwt_required
async def get_song(
    song_id: UUID,
    db: Session = Depends(get_db)
):
    """Get song by ID."""
    user_id = get_current_user_id()
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    controller = SongController(db)
    song = controller.get_song(song_id=song_id, user_id=user_id)

    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    return SongResponse(data=song)

@router.post("/", response_model=SongResponse, status_code=201)
@jwt_required
async def create_song(
    song_data: SongCreate,
    db: Session = Depends(get_db)
):
    """Create new song."""
    user_id = get_current_user_id()
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    controller = SongController(db)
    song = controller.create_song(user_id=user_id, song_data=song_data)

    return SongResponse(data=song)

@router.put("/{song_id}", response_model=SongResponse)
@jwt_required
async def update_song(
    song_id: UUID,
    song_data: SongUpdate,
    db: Session = Depends(get_db)
):
    """Update existing song."""
    user_id = get_current_user_id()
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    controller = SongController(db)
    song = controller.update_song(
        song_id=song_id,
        user_id=user_id,
        song_data=song_data
    )

    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    return SongResponse(data=song)

@router.delete("/{song_id}", status_code=204)
@jwt_required
async def delete_song(
    song_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete song."""
    user_id = get_current_user_id()
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    controller = SongController(db)
    success = controller.delete_song(song_id=song_id, user_id=user_id)

    if not success:
        raise HTTPException(status_code=404, detail="Song not found")

    return None
```

### Controller

```python
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ..db.models import Song
from ..schemas.song import SongCreate, SongUpdate

class SongController:
    def __init__(self, db: Session):
        self.db = db

    def list_songs(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None
    ) -> List[Song]:
        """List songs with pagination and search."""
        query = self.db.query(Song).filter(Song.user_id == user_id)

        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                (Song.title.ilike(search_filter)) |
                (Song.lyrics.ilike(search_filter))
            )

        return query.order_by(Song.created_at.desc()).offset(skip).limit(limit).all()

    def get_song(self, song_id: UUID, user_id: UUID) -> Optional[Song]:
        """Get song by ID."""
        return self.db.query(Song).filter(
            Song.id == song_id,
            Song.user_id == user_id
        ).first()

    def create_song(self, user_id: UUID, song_data: SongCreate) -> Song:
        """Create new song."""
        song = Song(
            user_id=user_id,
            title=song_data.title,
            lyrics=song_data.lyrics,
            style_description=song_data.style_description,
            instrumental_only=song_data.instrumental_only,
            status="pending"
        )

        self.db.add(song)
        self.db.commit()
        self.db.refresh(song)

        return song

    def update_song(
        self,
        song_id: UUID,
        user_id: UUID,
        song_data: SongUpdate
    ) -> Optional[Song]:
        """Update existing song."""
        song = self.get_song(song_id=song_id, user_id=user_id)

        if not song:
            return None

        for field, value in song_data.dict(exclude_unset=True).items():
            setattr(song, field, value)

        self.db.commit()
        self.db.refresh(song)

        return song

    def delete_song(self, song_id: UUID, user_id: UUID) -> bool:
        """Delete song."""
        song = self.get_song(song_id=song_id, user_id=user_id)

        if not song:
            return False

        self.db.delete(song)
        self.db.commit()

        return True
```

### Pydantic Schemas (V2)

```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from uuid import UUID
from datetime import datetime

class SongBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    lyrics: Optional[str] = None
    style_description: Optional[str] = None
    instrumental_only: bool = False

class SongCreate(SongBase):
    """Schema for creating a song."""
    model: str = Field("auto", description="Model to use for generation")

    @field_validator("model")
    @classmethod
    def validate_model(cls, v):
        """Validate model field (Pydantic V2 pattern)."""
        allowed_models = ["auto", "mureka-7.5", "mureka-7", "mureka-6"]
        if v not in allowed_models:
            raise ValueError(f"model must be one of: {', '.join(allowed_models)}")
        return v

class SongUpdate(BaseModel):
    """Schema for updating a song."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    lyrics: Optional[str] = None
    style_description: Optional[str] = None
    instrumental_only: Optional[bool] = None

class SongDB(SongBase):
    """Song model from database."""
    id: UUID
    user_id: UUID
    status: str
    job_id: Optional[str] = None
    flac_url: Optional[str] = None
    mp3_url: Optional[str] = None
    audio_file_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SongResponse(BaseModel):
    """API response with single song."""
    data: SongDB

class SongListResponse(BaseModel):
    """API response with song list."""
    data: list[SongDB]
    total: int
    skip: int
    limit: int
```

**Important Pydantic V2 Changes:**

- **Validators**: Use `@field_validator("field")` instead of `@validator("field")`
- **Class Method**: Always add `@classmethod` decorator
- **Import**: `from pydantic import field_validator` (not `validator`)

**Migration Example:**

```python
# ❌ V1 (OLD - deprecated)
from pydantic import validator

@validator("model")
def validate_model(cls, v):
    if v not in ["auto", "mureka-7.5"]:
        raise ValueError("Invalid model")
    return v

# ✅ V2 (NEW - current)
from pydantic import field_validator

@field_validator("model")
@classmethod
def validate_model(cls, v):
    if v not in ["auto", "mureka-7.5"]:
        raise ValueError("Invalid model")
    return v
```

### SQLAlchemy Model

```python
from sqlalchemy import Column, String, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .base import Base

class Song(Base):
    __tablename__ = "songs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    lyrics = Column(Text, nullable=True)
    style_description = Column(Text, nullable=True)
    instrumental_only = Column(Boolean, default=False)
    status = Column(String(50), default="pending")
    job_id = Column(String(100), nullable=True)
    flac_url = Column(String(500), nullable=True)
    mp3_url = Column(String(500), nullable=True)
    stems_url = Column(String(500), nullable=True)
    audio_file_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="songs")
    choices = relationship("SongChoice", back_populates="song", cascade="all, delete-orphan")
```

---

## Testing Patterns

### Angular Unit Test

```typescript
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { TranslateModule } from '@ngx-translate/core';
import { of, throwError } from 'rxjs';

import { ExampleComponent } from './example.component';
import { ExampleService } from '@services/business/example.service';

describe('ExampleComponent', () => {
  let component: ExampleComponent;
  let fixture: ComponentFixture<ExampleComponent>;
  let service: jasmine.SpyObj<ExampleService>;

  beforeEach(async () => {
    const serviceSpy = jasmine.createSpyObj('ExampleService', ['getData']);

    await TestBed.configureTestingModule({
      imports: [
        ExampleComponent,
        HttpClientTestingModule,
        TranslateModule.forRoot()
      ],
      providers: [
        { provide: ExampleService, useValue: serviceSpy }
      ]
    }).compileComponents();

    service = TestBed.inject(ExampleService) as jasmine.SpyObj<ExampleService>;
    fixture = TestBed.createComponent(ExampleComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load data on init', () => {
    const mockData = [{ id: '1', title: 'Test' }];
    service.getData.and.returnValue(of(mockData));

    component.ngOnInit();

    expect(service.getData).toHaveBeenCalled();
    expect(component.items).toEqual(mockData);
    expect(component.loading).toBe(false);
  });

  it('should handle error', () => {
    const error = new Error('Test error');
    service.getData.and.returnValue(throwError(() => error));

    component.ngOnInit();

    expect(component.items).toEqual([]);
    expect(component.loading).toBe(false);
  });
});
```

### Python Unit Test (pytest)

```python
import pytest
from uuid import uuid4
from fastapi.testclient import TestClient

from src.server import app
from src.db.models import Song, User
from src.db.database import get_db, Base, engine

@pytest.fixture
def client():
    """Test client."""
    return TestClient(app)

@pytest.fixture
def test_db():
    """Test database."""
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_user(test_db):
    """Test user."""
    user = User(
        email="test@example.com",
        password_hash="hashed_password",
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user

@pytest.fixture
def test_song(test_db, test_user):
    """Test song."""
    song = Song(
        user_id=test_user.id,
        title="Test Song",
        lyrics="Test lyrics",
        status="completed"
    )
    test_db.add(song)
    test_db.commit()
    test_db.refresh(song)
    return song

def test_list_songs(client, test_song):
    """Test listing songs."""
    response = client.get(
        "/api/v1/songs",
        headers={"Authorization": f"Bearer {get_test_token()}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) > 0
    assert data["data"][0]["title"] == "Test Song"

def test_get_song(client, test_song):
    """Test getting song by ID."""
    response = client.get(
        f"/api/v1/songs/{test_song.id}",
        headers={"Authorization": f"Bearer {get_test_token()}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["data"]["id"] == str(test_song.id)
    assert data["data"]["title"] == "Test Song"

def test_create_song(client):
    """Test creating song."""
    song_data = {
        "title": "New Song",
        "lyrics": "New lyrics",
        "instrumental_only": False
    }

    response = client.post(
        "/api/v1/songs",
        json=song_data,
        headers={"Authorization": f"Bearer {get_test_token()}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["data"]["title"] == "New Song"
    assert data["data"]["status"] == "pending"
```

---

## 3-Layer Architecture (Current Implementation)

**NEW:** For modern 3-Layer Architecture patterns with Orchestrators, Transformers, and Repositories,
see **[CODE_PATTERNS_3LAYER.md](CODE_PATTERNS_3LAYER.md)**.

This document contains:
- ✅ Orchestrator Pattern (coordination)
- ✅ Transformer Pattern (pure functions, 100% testable)
- ✅ Normalizer Pattern (string transformations)
- ✅ Repository Pattern (CRUD only)
- ✅ Complete flow examples
- ✅ Testing strategy
- ✅ Anti-patterns (what NOT to do)

