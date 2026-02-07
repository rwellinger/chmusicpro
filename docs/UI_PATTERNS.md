# UI Patterns & Component Standards

**Project:** Multi-AI Creative Platform
**Last Updated:** 2025-10-29
**Reference Implementation:** Equipment Gallery (`aiwebui/src/app/pages/equipment-gallery/`)

---

## Purpose

**CRITICAL:** All new UI components MUST follow these patterns to ensure consistency across the application.
DO NOT create new button styles, layouts, or patterns without updating this document first.

---

## Table of Contents

1. [Master-Detail Layout](#master-detail-layout)
2. [Button Standards](#button-standards)
3. [Form Layouts](#form-layouts)
4. [Detail View Patterns](#detail-view-patterns)
5. [Icons](#icons)

---

## Master-Detail Layout

### Standard Structure

**ALWAYS use this structure for list/detail pages:**

```html
<div class="[feature]-container master-detail-layout">
  <!-- Left Side: List -->
  <div class="list-section">
    <mat-card class="list-card">
      <!-- List Header -->
      <div class="list-header">...</div>

      <!-- Search/Filters -->
      <div class="filters-section">...</div>

      <!-- List Items -->
      <div class="[feature]-list">...</div>

      <!-- Pagination/Load More -->
      <div class="load-more-section">...</div>
    </mat-card>
  </div>

  <!-- Right Side: Detail -->
  <div class="detail-section">
    <mat-card class="detail-card">
      <!-- Detail Header -->
      <div class="detail-header">...</div>

      <!-- Detail Content -->
      <div class="detail-content">...</div>

      <!-- Detail Actions -->
      <div class="detail-actions">...</div>
    </mat-card>
  </div>
</div>
```

### SCSS Setup

```scss
@import '../../../scss/variables';
@import '../../../scss/mixins';

.[feature]-container {
  display: grid;
  grid-template-columns: 400px 1fr;
  gap: $spacing-lg;
  padding: $spacing-lg;
  min-height: calc(100vh - 100px);
}

.list-section {
  display: flex;
  flex-direction: column;
}

.detail-section {
  display: flex;
  flex-direction: column;
}
```

**Reference:** `equipment-gallery.component.html` (Lines 1-503)

---

## Button Standards

### CRITICAL: Use Standard Mixins Only

**NEVER** create custom button styles. **ALWAYS** use the predefined mixins from `src/scss/_mixins.scss`.

### Available Button Mixins

```scss
@include button-primary('base');    // Blue button (primary actions)
@include button-secondary('base');  // Gray button (secondary actions)
@include button-danger('base');     // Red button (destructive actions)
@include button-success('base');    // Green button (success actions)
@include button-ai('base');         // Purple button (AI actions)
```

### Detail Actions Pattern (MANDATORY)

**ALWAYS use this pattern for action buttons in detail views:**

#### HTML

```html
<div class="detail-actions">
  <button type="button" class="action-button edit-button" (click)="onEdit()">
    <i class="fas fa-edit"></i>
    <span>{{ 'feature.actions.edit' | translate }}</span>
  </button>
  <button type="button" class="action-button duplicate-button" (click)="onDuplicate()">
    <i class="fas fa-copy"></i>
    <span>{{ 'feature.actions.duplicate' | translate }}</span>
  </button>
  <button type="button" class="action-button delete-button" (click)="onDelete()">
    <i class="fas fa-trash"></i>
    <span>{{ 'feature.actions.delete' | translate }}</span>
  </button>
</div>
```

#### SCSS

```scss
.detail-actions {
  display: flex;
  gap: $spacing-sm;
  padding: $spacing-md;
  border-top: 1px solid $border-light;
  justify-content: flex-end;
}

.action-button {
  display: inline-flex;
  align-items: center;
  gap: $spacing-xs;
  font-weight: $font-weight-medium !important;

  i {
    font-size: $font-base;
  }

  span {
    display: inline-block;
  }

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
  }
}

.edit-button {
  @include button-secondary('base');
}

.duplicate-button {
  @include button-secondary('base');
}

.delete-button {
  @include button-secondary('base');
}
```

**Reference:**
- HTML: `equipment-gallery.component.html` (Lines 465-478)
- SCSS: `equipment-gallery.component.scss` (Lines 664-711)
- Original: `song-sketch-library.component.scss` (Lines 666-715)

### Button Rules

✅ **DO:**
- Use Font Awesome icons (`<i class="fas fa-icon">`)
- Wrap text in `<span>` tags
- Use `type="button"` attribute
- Use mixins for styling
- Add `font-weight: $font-weight-medium !important;`

❌ **DON'T:**
- Use Material Icons (`<mat-icon>`)
- Hardcode colors or styles
- Create custom button classes
- Use different hover effects

---

## Form Layouts

### Editor Form Pattern

**Standard form structure for create/edit pages:**

#### Single Full-Width Field

```html
<mat-form-field appearance="outline" class="full-width">
  <mat-label>{{ 'feature.editor.fieldName' | translate }}</mat-label>
  <input matInput formControlName="fieldName">
  <mat-error>{{ getFieldError('fieldName') }}</mat-error>
</mat-form-field>
```

#### Fields in Row (Multiple Columns)

```html
<div class="form-row">
  <mat-form-field appearance="outline" class="form-row__small">
    <mat-label>{{ 'feature.editor.type' | translate }}</mat-label>
    <mat-select formControlName="type">...</mat-select>
  </mat-form-field>

  <mat-form-field appearance="outline" class="form-row__large">
    <mat-label>{{ 'feature.editor.name' | translate }}</mat-label>
    <input matInput formControlName="name">
  </mat-form-field>

  <mat-form-field appearance="outline" class="form-row__medium">
    <mat-label>{{ 'feature.editor.version' | translate }}</mat-label>
    <input matInput formControlName="version">
    <app-info-tooltip matSuffix [text]="'feature.editor.versionInfo'"></app-info-tooltip>
  </mat-form-field>
</div>
```

#### SCSS for Form Rows

```scss
.form-row {
  display: flex;
  gap: $spacing-md;
  align-items: flex-start;
}

.form-row__small {
  flex: 0 0 25%;
}

.form-row__medium {
  flex: 0 0 30%;
}

.form-row__large {
  flex: 1;
}

.form-row__half {
  flex: 1;
}
```

**Reference:** `equipment-editor.component.html` (Lines 27-104)

### Info Tooltip Pattern

Use `app-info-tooltip` for field hints instead of `mat-hint`:

```html
<mat-form-field appearance="outline">
  <mat-label>{{ 'label' | translate }}</mat-label>
  <input matInput formControlName="field">
  <app-info-tooltip matSuffix [text]="'tooltip.key'"></app-info-tooltip>
  <mat-error>{{ getFieldError('field') }}</mat-error>
</mat-form-field>
```

**Reference:** `equipment-editor.component.html` (Line 57)

---

## Detail View Patterns

### Section Blocks

**Standard section structure in detail views:**

```html
<div class="detail-section-block">
  <h3 class="section-title">
    <i class="fas fa-icon"></i>
    {{ 'feature.sections.sectionName' | translate }}
  </h3>

  <div class="detail-field">
    <span class="field-label">{{ 'feature.editor.fieldName' | translate }}</span>
    <div class="readonly-field">{{ item.fieldName }}</div>
  </div>
</div>
```

### 3-Column Field Row

```html
<div class="detail-field-row-3col">
  <div class="detail-field">
    <span class="field-label">{{ 'field1' | translate }}</span>
    <div class="readonly-field">{{ item.field1 }}</div>
  </div>

  <div class="detail-field">
    <span class="field-label">{{ 'field2' | translate }}</span>
    <div class="readonly-field">{{ item.field2 }}</div>
  </div>

  <div class="detail-field">
    <span class="field-label">{{ 'field3' | translate }}</span>
    <div class="readonly-field">{{ item.field3 }}</div>
  </div>
</div>
```

### 2-Column Field Row

```html
<div class="detail-field-row">
  <div class="detail-field">
    <span class="field-label">{{ 'field1' | translate }}</span>
    <div class="readonly-field">{{ item.field1 }}</div>
  </div>

  <div class="detail-field">
    <span class="field-label">{{ 'field2' | translate }}</span>
    <div class="readonly-field">{{ item.field2 }}</div>
  </div>
</div>
```

**Reference:** `equipment-gallery.component.html` (Lines 194-474)

### Sensitive Fields (Password/License Key)

**Pattern for masked/copyable fields:**

```html
<div class="detail-field sensitive-field">
  <div class="field-header">
    <span class="field-label">{{ 'feature.editor.password' | translate }}</span>
    <div class="field-actions">
      <button class="visibility-toggle-btn" (click)="toggleVisibility()">
        <i [class]="showPassword ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
      </button>
      <button class="copy-icon-btn" (click)="copyToClipboard(value, 'Password')">
        <i class="fas fa-copy"></i>
      </button>
    </div>
  </div>
  <div class="readonly-field sensitive-value" [class.masked]="!showPassword">
    {{ showPassword ? item.password : '••••••••' }}
  </div>
</div>
```

**Reference:** `equipment-gallery.component.html` (Lines 306-321)

---

## Icons

### Standard: Font Awesome

**ALWAYS use Font Awesome icons, NEVER Material Icons in new components.**

#### Icon Usage

```html
<!-- ✅ CORRECT -->
<i class="fas fa-edit"></i>
<i class="fas fa-copy"></i>
<i class="fas fa-trash"></i>
<i class="fas fa-check"></i>

<!-- ❌ WRONG -->
<mat-icon>edit</mat-icon>
<mat-icon>content_copy</mat-icon>
```

#### Common Icons

| Action | Icon Class |
|--------|-----------|
| Edit | `fas fa-edit` |
| Copy/Duplicate | `fas fa-copy` |
| Delete | `fas fa-trash` |
| Save | `fas fa-save` |
| Close | `fas fa-times` |
| Info | `fas fa-info-circle` |
| Search | `fas fa-search` |
| Filter | `fas fa-filter` |
| Check/Mark | `fas fa-check` |
| Plus/Add | `fas fa-plus` |

**Reference:** Font Awesome 5 Free (already included in project)

---

## List Item Pattern (NO Actions!)

### CRITICAL: Actions Belong in Detail View Only

**List items should NEVER have inline action buttons (edit/delete).**
All actions belong in the detail view's `detail-actions` section.

#### Correct List Item Pattern

```html
<div class="[feature]-item"
     [class.selected]="selectedItem?.id === item.id"
     (click)="selectItem(item)">
  <div class="[feature]-item-header">
    <div class="icon">...</div>
    <div class="title-group">
      <h4>{{ item.name }}</h4>
    </div>
    <span class="status-badge">{{ item.status | translate }}</span>
  </div>
  <div class="[feature]-item-footer">
    <span class="date">{{ item.created_at | date:'short' }}</span>
  </div>
</div>
```

**Reference:** `equipment-gallery.component.html` (Lines 119-143)

---

## Checklist for New Pages

Before creating a new page, ensure you:

- [ ] Use Master-Detail Layout structure
- [ ] Use standard button mixins (`@include button-*`)
- [ ] Use Font Awesome icons (NOT Material Icons)
- [ ] Use `app-info-tooltip` for field hints
- [ ] Place actions in `detail-actions` section (NOT in list items)
- [ ] Follow form layout patterns (full-width, form-row, etc.)
- [ ] Use `.detail-section-block` for content sections
- [ ] Use `.detail-field-row` or `.detail-field-row-3col` for fields
- [ ] Review Equipment Gallery as reference implementation

---

## Reference Files

**Equipment Gallery (Reference Implementation):**
- `/aiwebui/src/app/pages/equipment-gallery/equipment-gallery.component.html`
- `/aiwebui/src/app/pages/equipment-gallery/equipment-gallery.component.scss`
- `/aiwebui/src/app/pages/equipment-gallery/equipment-gallery.component.ts`

**Equipment Editor:**
- `/aiwebui/src/app/pages/equipment-editor/equipment-editor.component.html`
- `/aiwebui/src/app/pages/equipment-editor/equipment-editor.component.scss`

**Sketch Library (Original Pattern):**
- `/aiwebui/src/app/pages/song-sketch-library/song-sketch-library.component.html`
- `/aiwebui/src/app/pages/song-sketch-library/song-sketch-library.component.scss`

**Button Mixins:**
- `/aiwebui/src/scss/_mixins.scss` (Lines 48-71)

---

## Anti-Patterns (DON'T DO THIS!)

### ❌ Custom Button Styles

```scss
// ❌ WRONG: Custom button styling
.my-button {
  background-color: #5a6268;
  color: white;
  padding: 8px 16px;
  &:hover { background-color: #4a5258; }
}
```

```scss
// ✅ CORRECT: Use mixins
.my-button {
  @include button-secondary('base');
}
```

### ❌ Material Icons in New Components

```html
<!-- ❌ WRONG -->
<button>
  <mat-icon>edit</mat-icon>
  Edit
</button>
```

```html
<!-- ✅ CORRECT -->
<button class="action-button edit-button">
  <i class="fas fa-edit"></i>
  <span>Edit</span>
</button>
```

### ❌ Actions in List Items

```html
<!-- ❌ WRONG: Actions in list -->
<div class="item">
  <span>{{ item.name }}</span>
  <button (click)="edit()">Edit</button>
  <button (click)="delete()">Delete</button>
</div>
```

```html
<!-- ✅ CORRECT: Actions in detail view -->
<div class="item" (click)="selectItem(item)">
  <span>{{ item.name }}</span>
</div>

<!-- Separate detail view with actions -->
<div class="detail-actions">
  <button class="action-button edit-button">...</button>
  <button class="action-button delete-button">...</button>
</div>
```

---

## Questions?

If you're unsure about a pattern:
1. Check Equipment Gallery implementation first
2. Check Sketch Library for original patterns
3. Review `_mixins.scss` for available utilities
4. Update this document if you find a missing pattern

**Last Review:** 2025-10-29
