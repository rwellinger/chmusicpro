# AiProxy Service - Main Makefile

.PHONY: help install-cli install-cli-dev install-cli-prod setup-cli-config-dev setup-cli-config-prod

help:
	@echo "AiProxy Service - Available commands:"
	@echo ""
	@echo "  make install-cli           Install CLI tool (no config)"
	@echo "  make install-cli-dev       Install CLI + DEV config (localhost:5050)"
	@echo "  make install-cli-prod      Install CLI + PROD config (macstudio)"
	@echo "  make setup-cli-config-dev  Create DEV config only"
	@echo "  make setup-cli-config-prod Create PROD config only"
	@echo ""

install-cli:
	@echo "Installing aiproxy-cli..."
	@mkdir -p ~/bin
	@cp scripts/cli/aiproxy-cli.py ~/bin/aiproxy-cli
	@chmod +x ~/bin/aiproxy-cli
	@echo "✓ Installed to ~/bin/aiproxy-cli"
	@echo ""
	@echo "Installing Python dependencies..."
	@pip install -r scripts/cli/requirements.txt
	@echo ""
	@echo "✓ Installation complete!"
	@echo ""
	@echo "Make sure ~/bin is in your PATH:"
	@echo "  export PATH=\"\$$HOME/bin:\$$PATH\""
	@echo ""
	@echo "⚠ No config created. Run one of:"
	@echo "  make setup-cli-config-dev   (for localhost development)"
	@echo "  make setup-cli-config-prod  (for production macstudio)"
	@echo "  aiproxy-cli login           (interactive setup)"

install-cli-dev: install-cli setup-cli-config-dev

install-cli-prod: install-cli setup-cli-config-prod

setup-cli-config-dev:
	@echo "Creating DEV config (~/.aiproxy/config.json)..."
	@mkdir -p ~/.aiproxy
	@chmod 700 ~/.aiproxy
	@echo '{\n  "api_url": "http://localhost:5050",\n  "jwt_token": "",\n  "email": "",\n  "expires_at": "",\n  "ssl_verify": true\n}' > ~/.aiproxy/config.json
	@chmod 600 ~/.aiproxy/config.json
	@if [ ! -f ~/.aiproxy/.aiproxyignore ]; then \
		cp scripts/cli/.aiproxyignore.default ~/.aiproxy/.aiproxyignore; \
		chmod 600 ~/.aiproxy/.aiproxyignore; \
		echo "✓ Created default .aiproxyignore"; \
	fi
	@echo "✓ DEV config created: ~/.aiproxy/config.json"
	@echo ""
	@echo "⚠ JWT token is empty. Run to login:"
	@echo "  aiproxy-cli login --api-url http://localhost:5050"

setup-cli-config-prod:
	@echo "Creating PROD config (~/.aiproxy/config.json)..."
	@mkdir -p ~/.aiproxy
	@chmod 700 ~/.aiproxy
	@echo '{\n  "api_url": "https://macstudio/aiproxysrv",\n  "jwt_token": "",\n  "email": "",\n  "expires_at": "",\n  "ssl_verify": false\n}' > ~/.aiproxy/config.json
	@chmod 600 ~/.aiproxy/config.json
	@echo "✓ PROD config created: ~/.aiproxy/config.json"
	@echo ""
	@echo "⚠ JWT token is empty. Run to login:"
	@echo "  aiproxy-cli login"
