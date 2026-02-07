# Makefile for aiwebui development tasks

.PHONY: help check-node lint-ts lint-scss lint-arch lint-all lint-fix test test-watch test-coverage build-dev build-prod install dev clean validate deploy-check

# Default target
help:
	@echo "Available targets:"
	@echo ""
	@echo "Code Quality:"
	@echo "  check-node     - Verify Node.js and npm versions"
	@echo "  lint-ts        - Run ESLint (TypeScript only)"
	@echo "  lint-scss      - Run Stylelint (SCSS only)"
	@echo "  lint-arch      - Run dependency-cruiser (architecture validation)"
	@echo "  lint-all       - Run all linters (TypeScript + SCSS + Architecture)"
	@echo "  lint-fix       - Auto-fix all linter issues (TypeScript + SCSS)"
	@echo "  install        - Install npm dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  test           - Run all unit tests (single run)"
	@echo "  test-watch     - Run tests in watch mode (development)"
	@echo "  test-coverage  - Run tests with coverage report"
	@echo ""
	@echo "Development:"
	@echo "  dev            - Start development server (ng serve)"
	@echo "  watch          - Watch mode for development builds"
	@echo "  clean          - Clean Angular cache and node_modules"
	@echo ""
	@echo "Build & Deployment:"
	@echo "  build-dev      - Development build"
	@echo "  build-prod     - Production build (with pre-check: lint-all)"
	@echo "  validate       - Pre-deployment validation (lint-all only)"
	@echo "  deploy-check   - Verify production build output"

# Check Node.js and npm versions
check-node:
	@echo "Checking Node.js environment..."
	@node --version || (echo "ERROR: Node.js not found! Install Node.js first."; exit 1)
	@npm --version || (echo "ERROR: npm not found! Install npm first."; exit 1)
	@echo "Node.js environment OK"

# TypeScript linting only
lint-ts: check-node
	@echo "Running ESLint (TypeScript)..."
	npm run lint

# SCSS linting only
lint-scss: check-node
	@echo "Running Stylelint (SCSS)..."
	npm run lint:scss

# Architecture validation
lint-arch: check-node
	@echo "Running dependency-cruiser (architecture validation)..."
	npm run lint:arch

# Run all linters (CRITICAL: TypeScript + SCSS + Architecture)
lint-all: check-node
	@echo "Running all linters (TypeScript + SCSS + Architecture)..."
	npm run lint:all
	@echo "All linters passed!"

# Auto-fix linter issues
lint-fix: check-node
	@echo "Auto-fixing TypeScript issues..."
	npm run lint:fix
	@echo "Auto-fixing SCSS issues..."
	npm run lint:scss:fix
	@echo "All auto-fixes applied!"

# Install npm dependencies
install: check-node
	@echo "Installing npm dependencies..."
	npm install

# Development server
dev: check-node
	@echo "Starting development server..."
	npm run start

# Watch mode
watch: check-node
	@echo "Starting watch mode..."
	npm run watch

# Clean cache and dependencies
clean:
	@echo "Cleaning Angular cache and node_modules..."
	rm -rf .angular
	rm -rf node_modules
	@echo "Clean complete. Run 'make install' to reinstall dependencies."

# Development build
build-dev: check-node
	@echo "Running development build..."
	@npm run build || (echo ""; echo "❌ BUILD FAILED! Fix TypeScript compilation errors above."; exit 1)

# Production build (CRITICAL: with all pre-checks!)
build-prod: check-node lint-all
	@echo "Running production build..."
	@npm run build:prod || (echo ""; echo "❌ BUILD FAILED! Fix TypeScript compilation errors above."; exit 1)
	@echo ""
	@echo "✅ Production build complete!"
	@echo "Output location: dist/aiwebui/"
	@echo "Deployment target: ../forwardproxy/html/aiwebui/"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Run 'make deploy-check' to verify output"
	@echo "  2. Copy to deployment: cp -r dist/aiwebui/* ../forwardproxy/html/aiwebui/"

# Pre-deployment validation (lint only)
validate: lint-all
	@echo "Pre-deployment validation passed!"

# Verify production build output
deploy-check:
	@echo "Checking production build output..."
	@if [ ! -d "dist/aiwebui" ]; then \
		echo "ERROR: Build output not found at dist/aiwebui/"; \
		echo "Run 'make build-prod' first!"; \
		exit 1; \
	fi
	@if [ ! -f "dist/aiwebui/index.html" ]; then \
		echo "ERROR: index.html not found in build output!"; \
		exit 1; \
	fi
	@echo "Build output OK: dist/aiwebui/"
	@ls -lh dist/aiwebui/ | head -10
	@echo ""
	@echo "Deployment target check..."
	@if [ -d "../forwardproxy/html/aiwebui" ]; then \
		echo "Deployment directory exists: ../forwardproxy/html/aiwebui/"; \
	else \
		echo "WARNING: Deployment directory not found: ../forwardproxy/html/aiwebui/"; \
		echo "Create it first or adjust deployment target."; \
	fi

# Run unit tests (single run)
test: check-node
	@echo "Running unit tests..."
	@if [ -f "/Applications/Chromium.app/Contents/MacOS/Chromium" ]; then \
		CHROME_BIN="/Applications/Chromium.app/Contents/MacOS/Chromium" npm run test -- --watch=false --browsers=ChromeHeadless; \
	elif [ -f "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]; then \
		CHROME_BIN="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" npm run test -- --watch=false --browsers=ChromeHeadless; \
	else \
		echo "ERROR: Neither Chromium nor Chrome found!"; \
		echo "Install with: brew install --cask chromium"; \
		exit 1; \
	fi

# Run tests in watch mode (development)
test-watch: check-node
	@echo "Running tests in watch mode..."
	@if [ -f "/Applications/Chromium.app/Contents/MacOS/Chromium" ]; then \
		CHROME_BIN="/Applications/Chromium.app/Contents/MacOS/Chromium" npm run test; \
	elif [ -f "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]; then \
		CHROME_BIN="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" npm run test; \
	else \
		echo "ERROR: Neither Chromium nor Chrome found!"; \
		echo "Install with: brew install --cask chromium"; \
		exit 1; \
	fi

# Run tests with coverage report
test-coverage: check-node
	@echo "Running tests with coverage..."
	@if [ -f "/Applications/Chromium.app/Contents/MacOS/Chromium" ]; then \
		CHROME_BIN="/Applications/Chromium.app/Contents/MacOS/Chromium" npm run test -- --watch=false --browsers=ChromeHeadless --code-coverage; \
	elif [ -f "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]; then \
		CHROME_BIN="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" npm run test -- --watch=false --browsers=ChromeHeadless --code-coverage; \
	else \
		echo "ERROR: Neither Chromium nor Chrome found!"; \
		echo "Install with: brew install --cask chromium"; \
		exit 1; \
	fi
	@echo ""
	@echo "Coverage report generated at: coverage/"
