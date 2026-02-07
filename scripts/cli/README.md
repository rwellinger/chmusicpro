# AiProxy CLI Tool

Command-line tool for uploading files to Song Projects.

## Installation

### From Repository

```bash
cd mac_ki_service
make install-cli
```

This will:
1. Copy the script to `~/bin/aiproxy-cli`
2. Make it executable
3. Install Python dependencies

**Important:** Make sure `~/bin` is in your `PATH`. Add to your `~/.zshrc` or `~/.bashrc`:

```bash
export PATH="$HOME/bin:$PATH"
```

### Manual Installation

```bash
# Create bin directory
mkdir -p ~/bin

# Copy script
cp scripts/cli/aiproxy-cli.py ~/bin/aiproxy-cli

# Make executable
chmod +x ~/bin/aiproxy-cli

# Install dependencies
pip install -r scripts/cli/requirements.txt
```

---

## Usage

### 1. Login

First, you need to login to get a JWT token:

```bash
aiproxy-cli login
```

**Interactive prompts:**
```
API URL [https://macstudio/aiproxysrv]: <Enter>
Email: your@email.com
Password: ***

✓ Login successful!
Token expires: 2024-11-03T10:30:00Z
```

**Token is stored in:** `~/.aiproxy/config.json` (permissions: `0600`)

---

### 2. Upload Files

Use the "Copy Upload Command" button in the Song Project UI to get the correct command, then:

```bash
# Navigate to your local directory
cd ~/Music/my-project/ai-files

# Paste and execute the copied command
aiproxy-cli upload <project-id> <folder-id> .
```

**Example:**
```bash
aiproxy-cli upload 003ec827-e412-4bb0-9434-2abce08973de abc-123-folder ~/Music/songs/
```

**What happens:**
1. Scans directory recursively for all files
2. Shows file count and total size
3. Uploads files in batches (50 files per request)
4. Shows progress bar with upload status
5. Displays summary (uploaded vs failed)

**Output Example:**
```
Scanning directory: /Users/rob/Music/ai-files
Found 127 files (total size: 2.3 GB)

Uploading files... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% • 127/127 • 0:00:00

Upload Summary
✓ Uploaded: 125 files
✗ Failed:   2 files
  - vocals.mp3: File already exists
  - test.wav: Invalid file format

Done in 45s.
```

---

## Configuration

Config file: `~/.aiproxy/config.json`

```json
{
  "api_url": "https://macstudio/aiproxysrv",
  "jwt_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "email": "user@example.com",
  "expires_at": "2024-11-03T10:30:00Z",
  "ssl_verify": false
}
```

**Security:**
- File permissions: `0600` (owner read/write only)
- Directory permissions: `0700` (owner access only)
- JWT token expires after 24 hours

---

## Security Notice

**JWT tokens are stored in plaintext** (protected by file permissions).

**DO NOT:**
- Share the config file
- Commit to git repositories
- Sync to cloud storage (Dropbox, iCloud)
- Use on shared/multi-user systems

**Token Expiry:**
Tokens expire after 24 hours. Re-run `aiproxy-cli login` if authentication fails.

---

## Troubleshooting

### "Not logged in" error

```bash
aiproxy-cli login
```

### "Token expired" error

```bash
aiproxy-cli login  # Re-login to get new token
```

### "Connection error"

Check if:
1. API URL is correct (`https://macstudio/aiproxysrv`)
2. You can reach the server (try `curl https://macstudio/aiproxysrv/api/v1/health`)
3. VPN/Network is connected

### SSL Certificate error

The config file has `ssl_verify: false` for self-signed certificates. This is normal for `macstudio`.

---

## Commands Reference

| Command | Description |
|---------|-------------|
| `aiproxy-cli login [--api-url URL]` | Login and save JWT token |
| `aiproxy-cli upload PROJECT_ID FOLDER_ID PATH` | Upload files recursively |

---

## Technical Details

**Upload Process:**
1. Scans local directory recursively
2. Groups files into batches (50 files per request)
3. Uploads each batch via `/api/v1/song-projects/{id}/folders/{folder_id}/batch-upload`
4. Shows real-time progress with `rich` library
5. Reports success/failure per file

**Authentication:**
- JWT token from `/api/v1/user/login`
- Sent as `Authorization: Bearer <token>` header
- Token valid for 24 hours

**File Upload:**
- Uses `multipart/form-data`
- Batch size: 50 files per request
- Timeout: 10 minutes per batch
- No file size limit (server-side upload, not browser)

---

## Future Features (Phase 6)

Planned for later:
- `aiproxy-cli list` - List all projects
- `aiproxy-cli sync` - Two-way sync (download + upload)
- `aiproxy-cli watch` - Auto-sync with file watcher
- Keychain integration for token encryption

---

## Development

**Test the CLI:**
```bash
# Make script executable
chmod +x scripts/cli/aiproxy-cli.py

# Run directly
./scripts/cli/aiproxy-cli.py login
./scripts/cli/aiproxy-cli.py upload <project-id> <folder-id> /path
```

**Dependencies:**
- Python 3.8+
- click (CLI framework)
- requests (HTTP client)
- rich (Pretty terminal output)
- urllib3 (SSL warnings suppression)
