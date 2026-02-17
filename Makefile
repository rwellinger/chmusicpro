# CH Music Pro - Main Makefile

.PHONY: help install-cli install-cli-dev install-cli-prod setup-cli-config-dev setup-cli-config-prod

DEPRECATION_MSG = \
	"\n\033[93m======================================================================\n\
WARNING: The CLI tool is DEPRECATED.\n\
All operations (upload, download, mirror sync, etc.) are now\n\
available directly in the Web UI. Please use the web interface.\n\
======================================================================\033[0m\n"

help:
	@echo "CH Music Pro - Available commands:"
	@echo ""
	@echo "  make install-cli           [DEPRECATED] Install CLI tool (no config)"
	@echo "  make install-cli-dev       [DEPRECATED] Install CLI + DEV config (localhost:5050)"
	@echo "  make install-cli-prod      [DEPRECATED] Install CLI + PROD config (macstudio)"
	@echo "  make setup-cli-config-dev  [DEPRECATED] Create DEV config only"
	@echo "  make setup-cli-config-prod [DEPRECATED] Create PROD config only"
	@echo ""
	@echo $(DEPRECATION_MSG)

install-cli:
	@echo $(DEPRECATION_MSG)
	@echo "Installing chmusicpro-cli..."
	@mkdir -p ~/bin
	@cp scripts/cli/chmusicpro-cli.py ~/bin/chmusicpro-cli
	@chmod +x ~/bin/chmusicpro-cli
	@echo "✓ Installed to ~/bin/chmusicpro-cli"
	@echo ""
	@echo "Installing Python dependencies..."
	@pip install -r scripts/cli/requirements.txt
	@echo ""
	@echo "✓ Installation complete!"
	@echo ""
	@echo "Make sure ~/bin is in your PATH:"
	@echo "  export PATH=\"$$HOME/bin:$$PATH\""
	@echo ""
	@echo "⚠ No config created. Run one of:"
	@echo "  make setup-cli-config-dev   (for localhost development)"
	@echo "  make setup-cli-config-prod  (for production macstudio)"
	@echo "  chmusicpro-cli login           (interactive setup)"

install-cli-dev: install-cli setup-cli-config-dev

install-cli-prod: install-cli setup-cli-config-prod

setup-cli-config-dev:
	@echo $(DEPRECATION_MSG)
	@echo "Creating DEV config (~/.chmusicpro/config.json)..."
	@mkdir -p ~/.chmusicpro
	@chmod 700 ~/.chmusicpro
	@echo '{\n  "api_url": "http://localhost:5050",\n  "jwt_token": "",\n  "email": "",\n  "expires_at": "",\n  "ssl_verify": true\n}' > ~/.chmusicpro/config.json
	@chmod 600 ~/.chmusicpro/config.json
	@if [ ! -f ~/.chmusicpro/.chmusicproignore ]; then \
		cp scripts/cli/.chmusicproignore.default ~/.chmusicpro/.chmusicproignore; \
		chmod 600 ~/.chmusicpro/.chmusicproignore; \
		echo "✓ Created default .chmusicproignore"; \
	fi
	@echo "✓ DEV config created: ~/.chmusicpro/config.json"
	@echo ""
	@echo "⚠ JWT token is empty. Run to login:"
	@echo "  chmusicpro-cli login --api-url http://localhost:5050"

setup-cli-config-prod:
	@echo $(DEPRECATION_MSG)
	@echo "Creating PROD config (~/.chmusicpro/config.json)..."
	@mkdir -p ~/.chmusicpro
	@chmod 700 ~/.chmusicpro
	@echo '{\n  "api_url": "https://macstudio/chmusicprosrv",\n  "jwt_token": "",\n  "email": "",\n  "expires_at": "",\n  "ssl_verify": false\n}' > ~/.chmusicpro/config.json
	@chmod 600 ~/.chmusicpro/config.json
	@echo "✓ PROD config created: ~/.chmusicpro/config.json"
	@echo ""
	@echo "⚠ JWT token is empty. Run to login:"
	@echo "  chmusicpro-cli login"
