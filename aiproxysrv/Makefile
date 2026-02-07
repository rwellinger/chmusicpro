# Makefile for aiproxysrv development tasks

.PHONY: help check-conda lint lint-ruff lint-imports lint-all format format-check test install-dev security-check db-current db-upgrade db-downgrade db-revision db-history db-heads

# Default target
help:
	@echo "Available targets:"
	@echo ""
	@echo "Code Quality:"
	@echo "  check-conda    - Verify correct Conda environment is activated"
	@echo "  lint-ruff      - Run Ruff linter (code quality)"
	@echo "  lint-imports   - Run import-linter (architecture validation)"
	@echo "  format-check   - Check code formatting (no auto-fix)"
	@echo "  lint-all       - Run all linters (Ruff + import-linter + format-check)"
	@echo "  format         - Format code with Ruff"
	@echo "  test           - Run pytest"
	@echo "  security-check - Check dependencies for known vulnerabilities (warn only)"
	@echo "  install-dev    - Install development dependencies"
	@echo ""
	@echo "Database Migrations (Alembic):"
	@echo "  db-current     - Show current migration version"
	@echo "  db-upgrade     - Upgrade database to latest version"
	@echo "  db-downgrade   - Downgrade database by 1 revision"
	@echo "  db-revision    - Create new migration (prompts for message)"
	@echo "  db-history     - Show migration history"
	@echo "  db-heads       - Show head revisions"

# Check if correct Conda environment is activated
check-conda:
	@if [ "$$CONDA_DEFAULT_ENV" != "mac_ki_service_py312" ]; then \
		echo "ERROR: Wrong Conda environment!"; \
		echo "Current: $$CONDA_DEFAULT_ENV"; \
		echo "Required: mac_ki_service_py312"; \
		echo ""; \
		echo "Activate with: conda activate mac_ki_service_py312"; \
		exit 1; \
	else \
		echo "Conda environment OK: mac_ki_service_py312"; \
	fi

# Ruff linting
lint-ruff: check-conda
	@echo "Running Ruff linter..."
	ruff check .

# Architecture validation
lint-imports: check-conda
	@echo "Running import-linter (architecture validation)..."
	lint-imports

# Format check (no auto-fix)
format-check: check-conda
	@echo "Checking code formatting with Ruff..."
	ruff format --check .

# Run all linters
lint-all: check-conda lint-ruff lint-imports format-check
	@echo "All linters passed!"

# Format code
format: check-conda
	@echo "Formatting code with Ruff..."
	ruff check . --fix
	ruff format .

# Run tests
test: check-conda
	@echo "Running pytest..."
	pytest -v

# Security: Check dependencies for known vulnerabilities (warn only, never fails)
security-check: check-conda
	@echo "Checking Python dependencies for known vulnerabilities..."
	@pip-audit --desc 2>/dev/null || echo "pip-audit not installed. Run: pip install pip-audit"
	@echo ""
	@echo "Done. This check is informational only - no build was blocked."

# Install development dependencies
install-dev: check-conda
	@echo "Installing development dependencies..."
	pip install -e ".[dev,test]"

# ============================================================================
# Database Migrations (Alembic)
# ============================================================================

# Show current migration version
db-current: check-conda
	@echo "Showing current migration version..."
	alembic current

# Upgrade database to latest version
db-upgrade: check-conda
	@echo "Upgrading database to latest version..."
	alembic upgrade head

# Downgrade database by 1 revision
db-downgrade: check-conda
	@echo "Downgrading database by 1 revision..."
	alembic downgrade -1

# Create new migration (prompts for message)
db-revision: check-conda
	@echo "Creating new migration..."
	@read -p "Migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

# Show migration history
db-history: check-conda
	@echo "Showing migration history..."
	alembic history --verbose

# Show head revisions
db-heads: check-conda
	@echo "Showing head revisions..."
	alembic heads
