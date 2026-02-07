#!/usr/bin/env python3
"""
AiProxy CLI Tool - Song Project Upload

Command-line tool for uploading files to Song Projects.
"""

# ============================================================
# Environment Validation (MUST be FIRST - before any imports!)
# ============================================================

import os
import sys

REQUIRED_CONDA_ENV = "mac_ki_service_py312"


def check_conda_environment():
    """
    Verify that the required Conda environment is active.

    Exits with error if wrong environment or no Conda environment is active.
    """
    conda_env = os.environ.get("CONDA_DEFAULT_ENV")

    if not conda_env:
        print("\033[91m✗ No Conda environment active!\033[0m")
        print("\033[93mPlease activate the required environment:\033[0m")
        print(f"  conda activate {REQUIRED_CONDA_ENV}")
        sys.exit(1)

    if conda_env != REQUIRED_CONDA_ENV:
        print(f"\033[91m✗ Wrong Conda environment active: {conda_env}\033[0m")
        print(f"\033[93mRequired environment:\033[0m {REQUIRED_CONDA_ENV}")
        print("\033[93mPlease switch to the correct environment:\033[0m")
        print(f"  conda activate {REQUIRED_CONDA_ENV}")
        sys.exit(1)


# Check environment BEFORE importing any third-party packages!
check_conda_environment()


# ============================================================
# Imports (AFTER environment validation)
# ============================================================
# ruff: noqa: E402
# E402 (imports not at top) is intentional: environment check must run BEFORE importing third-party packages

import click
import requests
import json
import hashlib
from pathlib import Path
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeRemainingColumn,
)
from datetime import datetime, UTC
import urllib3
import fnmatch

# Disable SSL warnings for self-signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

console = Console()
CONFIG_DIR = Path.home() / ".aiproxy"
CONFIG_FILE = CONFIG_DIR / "config.json"
GLOBAL_IGNORE_FILE = CONFIG_DIR / ".aiproxyignore"


# ============================================================
# Config Management (with 0600 permissions!)
# ============================================================


def load_config():
    """Load config from ~/.aiproxy/config.json"""
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except Exception as e:
            console.print(f"[red]✗ Error reading config file: {e}[/red]")
            return None
    return None


def save_config(config):
    """Save config with strict file permissions (0600)"""
    try:
        CONFIG_DIR.mkdir(exist_ok=True, mode=0o700)
        CONFIG_FILE.write_text(json.dumps(config, indent=2))
        os.chmod(CONFIG_FILE, 0o600)
        console.print(
            "[green]✓ Config saved to ~/.aiproxy/config.json (permissions: 0600)[/green]"
        )
    except Exception as e:
        console.print(f"[red]✗ Error saving config: {e}[/red]")
        sys.exit(1)


def load_ignore_patterns(upload_dir):
    """
    Load ignore patterns from .aiproxyignore files

    Checks two locations:
    1. ~/.aiproxy/.aiproxyignore (global)
    2. {upload_dir}/.aiproxyignore (local, higher priority)

    Returns list of patterns (glob-style like .gitignore)
    """
    patterns = []

    # Load global ignore file
    if GLOBAL_IGNORE_FILE.exists():
        try:
            for line in GLOBAL_IGNORE_FILE.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.append(line)
        except Exception as e:
            console.print(
                f"[dim yellow]Warning: Could not read global .aiproxyignore: {e}[/dim yellow]"
            )

    # Load local ignore file (in upload directory)
    local_ignore = Path(upload_dir) / ".aiproxyignore"
    if local_ignore.exists():
        try:
            for line in local_ignore.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.append(line)
        except Exception as e:
            console.print(
                f"[dim yellow]Warning: Could not read local .aiproxyignore: {e}[/dim yellow]"
            )

    return patterns


def should_ignore(file_path, upload_dir, patterns):
    """
    Check if file should be ignored based on patterns

    Supports:
    - Exact match: .DS_Store
    - Wildcards: Icon*, *.tmp
    - Directories: node_modules/, .git/
    """
    if not patterns:
        return False

    # Get relative path from upload_dir
    try:
        rel_path = file_path.relative_to(upload_dir)
    except ValueError:
        # File is not relative to upload_dir
        return False

    # Check each pattern
    for pattern in patterns:
        # Directory pattern (ends with /)
        if pattern.endswith("/"):
            # Check if any parent directory matches
            for parent in rel_path.parents:
                if fnmatch.fnmatch(parent.name, pattern.rstrip("/")):
                    return True
        else:
            # File pattern - check filename and full relative path
            if fnmatch.fnmatch(file_path.name, pattern) or fnmatch.fnmatch(
                str(rel_path), pattern
            ):
                return True

    return False


def check_token_expiry(config):
    """Check if JWT token is expired"""
    if "expires_at" not in config:
        return False

    try:
        expires_at_str = config["expires_at"]

        # Try ISO format first (e.g., "2024-11-03T10:30:00Z")
        try:
            expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
        except ValueError:
            # Try RFC 2822 format (e.g., "Mon, 03 Nov 2025 12:18:39 GMT")
            from email.utils import parsedate_to_datetime

            expires_at = parsedate_to_datetime(expires_at_str)

        if datetime.now(UTC) >= expires_at:
            console.print("[yellow]⚠ Token expired. Please login again.[/yellow]")
            return False
        return True
    except Exception as e:
        # If we can't parse the date, assume token is still valid
        # (better to let the backend reject it than block the user)
        console.print(f"[dim]Warning: Could not parse token expiry date: {e}[/dim]")
        return True


def check_storage_health(config):
    """
    Check if S3 storage backend (MinIO) is reachable

    CRITICAL Pre-Flight Check:
    - Prevents 600s timeout per batch when MinIO is down (e.g., NAS auto-shutdown at 23:30)
    - Prevents user confusion (seeing "success" but nothing uploaded)
    - Prevents inconsistent state (DB records without S3 files)

    Returns:
        True if storage is healthy, False otherwise
    """
    try:
        url = f"{config['api_url']}/api/v1/health/storage"
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {config['jwt_token']}"},
            verify=config.get("ssl_verify", False),
            timeout=5,  # 5s total timeout (backend has 2s, plus network overhead)
        )

        if response.status_code == 200:
            return True
        elif response.status_code == 503:
            # Storage backend is down
            data = response.json()
            message = data.get("message", "Storage backend unavailable")
            console.print(f"[red]✗ Storage backend check failed:[/red] {message}")
            console.print(
                "[yellow]→ Is the NAS running? (auto-shutdown at 23:30)[/yellow]"
            )
            return False
        else:
            console.print(
                f"[red]✗ Unexpected health check response: HTTP {response.status_code}[/red]"
            )
            return False

    except requests.exceptions.Timeout:
        console.print("[red]✗ Storage health check timeout[/red]")
        console.print("[yellow]→ Backend or MinIO may be down[/yellow]")
        return False
    except requests.exceptions.ConnectionError:
        console.print(f"[red]✗ Cannot reach backend: {config['api_url']}[/red]")
        return False
    except Exception as e:
        console.print(f"[red]✗ Storage health check error: {str(e)}[/red]")
        return False


# ============================================================
# CLI Commands
# ============================================================


@click.group()
def cli():
    """AiProxy CLI Tool - Song Project Management"""
    # Environment already checked at import time
    pass


@cli.command()
@click.option(
    "--api-url",
    default=None,
    help="API base URL (overrides config file)",
)
def login(api_url):
    """Login and save JWT token"""
    console.print("[bold]AiProxy CLI Login[/bold]")

    # Load existing config to get API URL if not provided via --api-url
    if api_url is None:
        existing_config = load_config()
        if existing_config and "api_url" in existing_config:
            api_url = existing_config["api_url"]
            console.print(f"[dim]Using API URL from config: {api_url}[/dim]")
        else:
            api_url = "https://macstudio/aiproxysrv"
            console.print(f"[dim]No config found, using default: {api_url}[/dim]")

    console.print(f"API URL: [bold]{api_url}[/bold]\n")

    email = console.input("Email: ")
    password = console.input("Password: ", password=True)

    # Call login endpoint
    url = f"{api_url}/api/v1/user/login"

    try:
        with console.status("[bold green]Logging in...[/bold green]"):
            response = requests.post(
                url,
                json={"email": email, "password": password},
                verify=False,  # Self-signed cert
                timeout=30,
            )

        if response.status_code == 200:
            data = response.json()

            # Save config
            config = {
                "api_url": api_url,
                "jwt_token": data["token"],
                "email": email,
                "expires_at": data["expires_at"],
                "ssl_verify": False,
            }
            save_config(config)

            console.print("[green]✓ Login successful![/green]")
            console.print(f"[dim]Token expires: {data['expires_at']}[/dim]")

        else:
            error = response.json().get("error", "Unknown error")
            console.print(f"[red]✗ Login failed: {error}[/red]")
            sys.exit(1)

    except requests.exceptions.Timeout:
        console.print("[red]✗ Connection timeout[/red]")
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        console.print(f"[red]✗ Connection error: Cannot reach {api_url}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗ Error: {str(e)}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("project_id")
@click.argument("folder_id")
@click.argument("local_path", type=click.Path(exists=True), default=".")
@click.option(
    "--debug", is_flag=True, help="Show debug output (request/response details)"
)
def upload(project_id, folder_id, local_path, debug):
    """Upload files recursively to song project folder

    If local_path is omitted, uses current directory (.)

    Examples:
        aiproxy-cli upload <project-id> <folder-id> ~/Music/
        aiproxy-cli upload <project-id> <folder-id> .
        aiproxy-cli upload <project-id> <folder-id>  (uses current dir)
    """

    # Load config
    config = load_config()
    if not config:
        console.print("[red]✗ Not logged in. Run: aiproxy-cli login[/red]")
        sys.exit(1)

    # Check token expiry
    if not check_token_expiry(config):
        console.print("[yellow]Run: aiproxy-cli login[/yellow]")
        sys.exit(1)

    # CRITICAL: Check storage backend health BEFORE scanning files
    # Prevents 600s timeout per batch when MinIO is down (e.g., NAS auto-shutdown at 23:30)
    console.print("[bold]Checking storage backend...[/bold]")
    if not check_storage_health(config):
        console.print("[red]✗ Upload aborted: Storage backend not reachable[/red]")
        sys.exit(1)
    console.print("[green]✓ Storage backend OK[/green]\n")

    # Check if project is archived
    try:
        url = f"{config['api_url']}/api/v1/song-projects/{project_id}"
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {config['jwt_token']}"},
            verify=config.get("ssl_verify", False),
            timeout=30,
        )
        if response.status_code == 200:
            project_data = response.json().get("data", {})
            project_name = project_data.get("project_name", "Unknown")
            if project_data.get("project_status") == "archived":
                console.print(
                    f"[red]✗ Upload denied: Project '{project_name}' is archived.[/red]"
                )
                console.print(
                    "[yellow]  → Unarchive the project first to enable uploads.[/yellow]"
                )
                sys.exit(1)
    except Exception as e:
        console.print(
            f"[yellow]Warning: Could not check project status: {str(e)}[/yellow]"
        )

    # Scan directory recursively
    local_path = Path(local_path)
    files = []
    ignored_files = []

    console.print(f"[bold]Scanning directory:[/bold] {local_path}")

    # Load ignore patterns
    ignore_patterns = load_ignore_patterns(local_path)
    if ignore_patterns:
        console.print(
            f"[dim]Loaded {len(ignore_patterns)} ignore patterns from .aiproxyignore[/dim]"
        )

    for file_path in local_path.rglob("*"):
        if file_path.is_file():
            # Check if file should be ignored
            if should_ignore(file_path, local_path, ignore_patterns):
                ignored_files.append(file_path)
            else:
                files.append(file_path)

    if not files:
        console.print("[yellow]✗ No files found (or all files ignored)[/yellow]")
        if ignored_files:
            console.print(
                f"[dim]Ignored {len(ignored_files)} files based on .aiproxyignore[/dim]"
            )
        sys.exit(0)

    total_size = sum(f.stat().st_size for f in files)
    console.print(
        f"Found [bold]{len(files)}[/bold] files "
        f"(total size: [bold]{total_size / (1024 * 1024):.1f} MB[/bold])"
    )
    if ignored_files:
        console.print(
            f"[dim]Ignored {len(ignored_files)} files based on .aiproxyignore[/dim]"
        )
    console.print()

    # Upload files in batches (3 files per request to avoid 413 errors with large FLAC files)
    # CRITICAL: 10 × 100MB FLAC = 1GB exceeds Nginx limit!
    # Conservative batch size: 3 × 150MB = 450MB (under 500MB Nginx limit)
    BATCH_SIZE = 3
    uploaded = 0
    failed = 0
    errors = []

    url = f"{config['api_url']}/api/v1/song-projects/{project_id}/folders/{folder_id}/batch-upload"
    headers = {"Authorization": f"Bearer {config['jwt_token']}"}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("•"),
        TextColumn("[bold blue]{task.completed}/{task.total}[/bold blue]"),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Uploading files...", total=len(files))

        for i in range(0, len(files), BATCH_SIZE):
            batch = files[i : i + BATCH_SIZE]

            # Prepare multipart form data with relative paths
            file_objects = []
            relative_paths = []
            for f in batch:
                try:
                    # Calculate relative path from upload directory (preserves subdirectories)
                    rel_path = f.relative_to(local_path)
                    # Use forward slashes for cross-platform compatibility
                    rel_path_str = str(rel_path).replace("\\", "/")

                    file_objects.append(("files", (rel_path_str, open(f, "rb"))))
                    relative_paths.append(rel_path_str)
                except Exception as e:
                    failed += 1
                    errors.append(
                        {"filename": f.name, "error": f"Cannot read file: {str(e)}"}
                    )
                    progress.update(task, advance=1)
                    continue

            if not file_objects:
                continue

            try:
                # Show intermediate progress while uploading
                progress.update(
                    task,
                    description=f"Uploading batch {i // BATCH_SIZE + 1}/{(len(files) + BATCH_SIZE - 1) // BATCH_SIZE}...",
                )

                if debug:
                    console.print(f"[dim]DEBUG: POST {url}[/dim]")
                    console.print(
                        f"[dim]DEBUG: Files in batch: {len(file_objects)}[/dim]"
                    )

                response = requests.post(
                    url,
                    files=file_objects,
                    headers=headers,
                    verify=config.get("ssl_verify", False),
                    timeout=600,  # 10min timeout for large uploads
                )

                if debug:
                    console.print(f"[dim]DEBUG: HTTP {response.status_code}[/dim]")
                    console.print(
                        f"[dim]DEBUG: Content-Type: {response.headers.get('Content-Type', 'N/A')}[/dim]"
                    )
                    console.print(
                        f"[dim]DEBUG: Response preview: {response.text[:300]}[/dim]"
                    )

                # Close file handles
                for _, (_, fh) in file_objects:
                    try:
                        fh.close()
                    except Exception:
                        pass

                # Parse response with proper error handling
                try:
                    response_data = response.json()
                except json.JSONDecodeError:
                    # Server returned HTML instead of JSON (likely Nginx error page)
                    failed += len(batch)
                    error_preview = response.text[:200].replace("\n", " ")
                    errors.append(
                        {
                            "error": f"Server error (HTTP {response.status_code}): Response is not JSON. Preview: {error_preview}"
                        }
                    )
                    progress.update(
                        task, advance=len(batch), description="Uploading files..."
                    )
                    continue

                if response.status_code == 200:
                    result = response_data["data"]
                    uploaded += result["uploaded"]
                    failed += result["failed"]
                    errors.extend(result["errors"])
                else:
                    # Batch upload failed
                    failed += len(batch)
                    error_msg = response_data.get(
                        "error", f"HTTP {response.status_code}"
                    )
                    errors.append({"error": f"Batch upload failed: {error_msg}"})

            except requests.exceptions.Timeout:
                failed += len(batch)
                errors.append({"error": "Request timeout (10min)"})
            except Exception as e:
                failed += len(batch)
                errors.append({"error": str(e)})

            # Advance progress by number of files in batch
            progress.update(task, advance=len(batch), description="Uploading files...")

    # Summary
    console.print("\n[bold]Upload Summary[/bold]")
    console.print(f"[green]✓ Uploaded:[/green] {uploaded} files")

    if failed > 0:
        console.print(f"[red]✗ Failed:[/red]   {failed} files")
        for error in errors[:10]:  # Show max 10 errors
            filename = error.get("filename", "Unknown")
            error_msg = error.get("error", "Unknown error")
            console.print(f"  [dim red]- {filename}: {error_msg}[/dim red]")

        if len(errors) > 10:
            console.print(f"  [dim]... and {len(errors) - 10} more errors[/dim]")


@cli.command()
@click.argument("project_id")
@click.argument("folder_id")
@click.argument("local_path", type=click.Path(), default=".")
def download(project_id, folder_id, local_path):
    """Download all files from song project folder (reconstructs directory structure)

    If local_path is omitted, uses current directory (.)

    Examples:
        aiproxy-cli download <project-id> <folder-id> ~/Music/
        aiproxy-cli download <project-id> <folder-id> .
        aiproxy-cli download <project-id> <folder-id>  (uses current dir)
    """

    # Load config
    config = load_config()
    if not config:
        console.print("[red]✗ Not logged in. Run: aiproxy-cli login[/red]")
        sys.exit(1)

    # Check token expiry
    if not check_token_expiry(config):
        console.print("[yellow]Run: aiproxy-cli login[/yellow]")
        sys.exit(1)

    # CRITICAL: Check storage backend health BEFORE fetching file list
    # Prevents 600s timeout per file when MinIO is down
    console.print("[bold]Checking storage backend...[/bold]")
    if not check_storage_health(config):
        console.print("[red]✗ Download aborted: Storage backend not reachable[/red]")
        sys.exit(1)
    console.print("[green]✓ Storage backend OK[/green]\n")

    # Fetch file list from API
    url = f"{config['api_url']}/api/v1/song-projects/{project_id}/folders/{folder_id}/files"
    headers = {"Authorization": f"Bearer {config['jwt_token']}"}

    console.print("[bold]Fetching file list from server...[/bold]")

    try:
        response = requests.get(
            url,
            headers=headers,
            verify=config.get("ssl_verify", False),
            timeout=30,
        )

        if response.status_code != 200:
            error = response.json().get("error", f"HTTP {response.status_code}")
            console.print(f"[red]✗ Failed to fetch file list: {error}[/red]")
            sys.exit(1)

        files = response.json()["data"]

        if not files:
            console.print("[yellow]✗ No files found in folder[/yellow]")
            sys.exit(0)

        total_size = sum(f["file_size_bytes"] for f in files)
        console.print(
            f"Found [bold]{len(files)}[/bold] files "
            f"(total size: [bold]{total_size / (1024 * 1024):.1f} MB[/bold])"
        )
        console.print()

    except requests.exceptions.Timeout:
        console.print("[red]✗ Connection timeout[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗ Error: {str(e)}[/red]")
        sys.exit(1)

    # Download files with progress
    local_path = Path(local_path)
    downloaded = 0
    failed = 0
    errors = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("•"),
        TextColumn("[bold blue]{task.completed}/{task.total}[/bold blue]"),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Downloading files...", total=len(files))

        for file in files:
            try:
                # Get relative path (e.g., "Media/drums.wav")
                relative_path = file["relative_path"]
                download_url = file["download_url"]

                # Build full URL (download_url is now a backend proxy path)
                if download_url and not download_url.startswith("http"):
                    download_url = config["api_url"] + download_url

                # Remove folder name prefix (e.g., "01 Arrangement/Media/drums.wav" → "Media/drums.wav")
                # Folder name is everything before the first "/"
                if "/" in relative_path:
                    # Skip first component (folder name)
                    parts = relative_path.split("/", 1)
                    if len(parts) > 1:
                        relative_path = parts[1]

                # Create target path
                target_file = local_path / relative_path

                # Create subdirectories if needed
                target_file.parent.mkdir(parents=True, exist_ok=True)

                # Download file via backend proxy (with JWT auth)
                file_response = requests.get(
                    download_url,
                    headers=headers,  # JWT authentication required
                    verify=config.get("ssl_verify", False),
                    timeout=600,  # 10min timeout for large files
                    stream=True,
                )

                if file_response.status_code == 200:
                    with open(target_file, "wb") as f:
                        for chunk in file_response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    downloaded += 1
                else:
                    failed += 1
                    errors.append(
                        {
                            "filename": file["filename"],
                            "error": f"HTTP {file_response.status_code}",
                        }
                    )

            except Exception as e:
                failed += 1
                errors.append(
                    {"filename": file.get("filename", "Unknown"), "error": str(e)}
                )

            progress.update(task, advance=1)

    # Summary
    console.print("\n[bold]Download Summary[/bold]")
    console.print(f"[green]✓ Downloaded:[/green] {downloaded} files")

    if failed > 0:
        console.print(f"[red]✗ Failed:[/red]     {failed} files")
        for error in errors[:10]:  # Show max 10 errors
            filename = error.get("filename", "Unknown")
            error_msg = error.get("error", "Unknown error")
            console.print(f"  [dim red]- {filename}: {error_msg}[/dim red]")

        if len(errors) > 10:
            console.print(f"  [dim]... and {len(errors) - 10} more errors[/dim]")

    console.print(f"\n[dim]Files downloaded to: {local_path.absolute()}[/dim]")


@cli.command()
@click.argument("project_id")
@click.argument("local_path", type=click.Path(), default=".")
@click.option(
    "-d", "--create-dir", is_flag=True, help="Create directory with project name"
)
def clone(project_id, local_path, create_dir):
    """Clone complete project (all folders and files, 1:1 S3 structure clone)

    Downloads ALL folders and files from a project, recreating the exact
    S3 directory structure locally (including empty folders).

    Use Case: Create project in web UI → Clone complete structure → Ready to work!

    If local_path is omitted, uses current directory (.)

    Use -d flag to automatically create a subdirectory with the project name.

    Examples:
        aiproxy-cli clone <project-id> ~/Music/MyProject/
        aiproxy-cli clone <project-id> .
        aiproxy-cli clone <project-id>  (uses current dir)
        aiproxy-cli clone <project-id> . -d  (creates ./Project Name/)
    """

    # Load config
    config = load_config()
    if not config:
        console.print("[red]✗ Not logged in. Run: aiproxy-cli login[/red]")
        sys.exit(1)

    # Check token expiry
    if not check_token_expiry(config):
        console.print("[yellow]Run: aiproxy-cli login[/yellow]")
        sys.exit(1)

    # CRITICAL: Check storage backend health BEFORE fetching project structure
    # Clone downloads entire project - prevents timeout-hell when MinIO is down
    console.print("[bold]Checking storage backend...[/bold]")
    if not check_storage_health(config):
        console.print("[red]✗ Clone aborted: Storage backend not reachable[/red]")
        sys.exit(1)
    console.print("[green]✓ Storage backend OK[/green]\n")

    # Fetch complete project structure from API
    url = f"{config['api_url']}/api/v1/song-projects/{project_id}/files/all"
    headers = {"Authorization": f"Bearer {config['jwt_token']}"}

    console.print("[bold]Fetching complete project structure from server...[/bold]")

    try:
        response = requests.get(
            url,
            headers=headers,
            verify=config.get("ssl_verify", False),
            timeout=30,
        )

        if response.status_code != 200:
            error = response.json().get("error", f"HTTP {response.status_code}")
            console.print(f"[red]✗ Failed to fetch project structure: {error}[/red]")
            sys.exit(1)

        data = response.json()["data"]
        project_name = data["project_name"]
        folders = data["folders"]

        # Calculate totals
        total_files = sum(len(folder["files"]) for folder in folders)
        total_folders = len(folders)

        console.print(
            f"[bold]Project:[/bold] {project_name}\n"
            f"[bold]Folders:[/bold] {total_folders}\n"
            f"[bold]Files:[/bold]   {total_files}"
        )
        console.print()

    except requests.exceptions.Timeout:
        console.print("[red]✗ Connection timeout[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗ Error: {str(e)}[/red]")
        sys.exit(1)

    # Determine target directory
    local_path = Path(local_path)

    # If -d flag is set, create subdirectory with project name
    if create_dir:
        local_path = local_path / project_name
        console.print(f"[dim]Creating project directory: {project_name}[/dim]")
        local_path.mkdir(parents=True, exist_ok=True)
    downloaded = 0
    failed = 0
    errors = []
    folders_created = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("•"),
        TextColumn("[bold blue]{task.fields[current_folder]}[/bold blue]"),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(
            "Downloading project...",
            total=total_files + total_folders,
            current_folder="",
        )

        for folder_idx, folder in enumerate(folders, 1):
            folder_name = folder["folder_name"]
            files = folder["files"]

            # Update progress description
            progress.update(
                task, current_folder=f"[{folder_idx}/{total_folders}] {folder_name}"
            )

            # Create folder directory (even if empty)
            folder_path = local_path / folder_name
            folder_path.mkdir(parents=True, exist_ok=True)
            folders_created += 1
            progress.update(task, advance=1)

            # Download files in this folder
            if not files:
                # Empty folder - just log it
                continue

            for file in files:
                try:
                    # Get file info
                    relative_path = file[
                        "relative_path"
                    ]  # e.g., "01 Arrangement/Media/drums.flac"
                    download_url = file["download_url"]

                    # Build full URL (download_url is now a backend proxy path)
                    if download_url and not download_url.startswith("http"):
                        download_url = config["api_url"] + download_url

                    # CRITICAL: Keep complete path structure (do NOT remove folder prefix!)
                    # relative_path already contains full structure: "01 Arrangement/Media/drums.flac"
                    target_file = local_path / relative_path

                    # Create subdirectories if needed
                    target_file.parent.mkdir(parents=True, exist_ok=True)

                    # Download file via backend proxy (with JWT auth)
                    file_response = requests.get(
                        download_url,
                        headers=headers,  # JWT authentication required
                        verify=config.get("ssl_verify", False),
                        timeout=600,  # 10min timeout for large files
                        stream=True,
                    )

                    if file_response.status_code == 200:
                        with open(target_file, "wb") as f:
                            for chunk in file_response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        downloaded += 1
                    else:
                        failed += 1
                        errors.append(
                            {
                                "filename": file["filename"],
                                "folder": folder_name,
                                "error": f"HTTP {file_response.status_code}",
                            }
                        )

                except Exception as e:
                    failed += 1
                    errors.append(
                        {
                            "filename": file.get("filename", "Unknown"),
                            "folder": folder_name,
                            "error": str(e),
                        }
                    )

                progress.update(task, advance=1)

    # Summary
    console.print("\n[bold]Complete Clone Summary[/bold]")
    console.print(f"[green]✓ Folders created:[/green] {folders_created}")
    console.print(f"[green]✓ Files downloaded:[/green] {downloaded}")

    if failed > 0:
        console.print(f"[red]✗ Failed:[/red]          {failed} files")
        for error in errors[:10]:  # Show max 10 errors
            filename = error.get("filename", "Unknown")
            folder = error.get("folder", "Unknown")
            error_msg = error.get("error", "Unknown error")
            console.print(f"  [dim red]- {folder}/{filename}: {error_msg}[/dim red]")

        if len(errors) > 10:
            console.print(f"  [dim]... and {len(errors) - 10} more errors[/dim]")

    console.print(f"\n[dim]Project cloned to: {local_path.absolute()}[/dim]")


@cli.command()
@click.argument("project_id")
@click.argument("folder_id")
@click.argument("local_path", type=click.Path(exists=True), default=".")
@click.option(
    "--dry-run", is_flag=True, help="Show preview without executing (no upload/delete)"
)
@click.option("--yes", is_flag=True, help="Skip confirmation prompt")
@click.option(
    "--debug", is_flag=True, help="Show debug output (request/response details)"
)
def mirror(project_id, folder_id, local_path, dry_run, yes, debug):
    """Mirror local directory to remote (One-Way Sync: Local → Remote)

    Syncs local directory with remote storage:
    - Uploads new/changed files (hash comparison)
    - Deletes remote files that don't exist locally (DANGEROUS!)

    Use --dry-run to preview changes before execution.

    Examples:
        aiproxy-cli mirror <project-id> <folder-id> ~/Music/ --dry-run
        aiproxy-cli mirror <project-id> <folder-id> ~/Music/ --yes
        aiproxy-cli mirror <project-id> <folder-id> .
    """

    # Load config
    config = load_config()
    if not config:
        console.print("[red]✗ Not logged in. Run: aiproxy-cli login[/red]")
        sys.exit(1)

    # Check token expiry
    if not check_token_expiry(config):
        console.print("[yellow]Run: aiproxy-cli login[/yellow]")
        sys.exit(1)

    # CRITICAL: Check storage backend health BEFORE scanning files
    # Mirror is ESPECIALLY dangerous when MinIO is down:
    # - Could delete files from DB but not from S3 → Inconsistent state!
    # - Prevents 600s timeout per batch (NAS auto-shutdown at 23:30)
    console.print("[bold]Checking storage backend...[/bold]")
    if not check_storage_health(config):
        console.print("[red]✗ Mirror aborted: Storage backend not reachable[/red]")
        console.print(
            "[yellow]→ Mirror requires storage for upload AND delete operations[/yellow]"
        )
        sys.exit(1)
    console.print("[green]✓ Storage backend OK[/green]\n")

    # Check if project is archived
    try:
        url = f"{config['api_url']}/api/v1/song-projects/{project_id}"
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {config['jwt_token']}"},
            verify=config.get("ssl_verify", False),
            timeout=30,
        )
        if response.status_code == 200:
            project_data = response.json().get("data", {})
            project_name = project_data.get("project_name", "Unknown")
            if project_data.get("project_status") == "archived":
                console.print(
                    f"[red]✗ Mirror denied: Project '{project_name}' is archived.[/red]"
                )
                console.print(
                    "[yellow]  → Unarchive the project first to enable mirroring.[/yellow]"
                )
                sys.exit(1)
    except Exception as e:
        console.print(
            f"[yellow]Warning: Could not check project status: {str(e)}[/yellow]"
        )

    local_path = Path(local_path)

    # Step 1: Scan local directory and calculate hashes
    console.print(f"[bold]📂 Scanning local directory:[/bold] {local_path}")

    ignore_patterns = load_ignore_patterns(local_path)
    if ignore_patterns:
        console.print(
            f"[dim]Loaded {len(ignore_patterns)} ignore patterns from .aiproxyignore[/dim]"
        )

    local_files = []
    ignored_files = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Calculating file hashes...", total=None)

        for file_path in local_path.rglob("*"):
            if file_path.is_file():
                if should_ignore(file_path, local_path, ignore_patterns):
                    ignored_files.append(file_path)
                else:
                    # Calculate SHA256 hash
                    try:
                        rel_path = file_path.relative_to(local_path)
                        rel_path_str = str(rel_path).replace("\\", "/")

                        with open(file_path, "rb") as f:
                            file_hash = hashlib.sha256(f.read()).hexdigest()

                        local_files.append(
                            {
                                "relative_path": rel_path_str,
                                "file_hash": file_hash,
                                "file_size_bytes": file_path.stat().st_size,
                                "local_file_path": file_path,
                            }
                        )
                    except Exception as e:
                        console.print(
                            f"[dim red]Warning: Could not hash {file_path}: {e}[/dim red]"
                        )

        progress.update(task, completed=True)

    if not local_files:
        console.print("[yellow]✗ No files found (or all files ignored)[/yellow]")
        if ignored_files:
            console.print(
                f"[dim]Ignored {len(ignored_files)} files based on .aiproxyignore[/dim]"
            )
        sys.exit(0)

    total_size = sum(f["file_size_bytes"] for f in local_files)
    console.print(
        f"Found [bold]{len(local_files)}[/bold] local files "
        f"(total size: [bold]{total_size / (1024 * 1024):.1f} MB[/bold])"
    )
    if ignored_files:
        console.print(
            f"[dim]Ignored {len(ignored_files)} files based on .aiproxyignore[/dim]"
        )
    console.print()

    # Step 2: Call mirror endpoint (get diff)
    console.print("[bold]🔍 Comparing with remote storage...[/bold]")

    url = f"{config['api_url']}/api/v1/song-projects/{project_id}/folders/{folder_id}/mirror"
    headers = {
        "Authorization": f"Bearer {config['jwt_token']}",
        "Content-Type": "application/json",
    }

    payload = {
        "files": [
            {
                "relative_path": f["relative_path"],
                "file_hash": f["file_hash"],
                "file_size_bytes": f["file_size_bytes"],
            }
            for f in local_files
        ]
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            verify=config.get("ssl_verify", False),
            timeout=30,
        )

        if response.status_code != 200:
            error = response.json().get("error", f"HTTP {response.status_code}")
            console.print(f"[red]✗ Mirror compare failed: {error}[/red]")
            if debug:
                console.print(f"[dim]Response: {response.text}[/dim]")
            sys.exit(1)

        diff = response.json()["data"]

    except requests.exceptions.Timeout:
        console.print("[red]✗ Connection timeout[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗ Error: {str(e)}[/red]")
        sys.exit(1)

    # Step 3: Show preview
    to_upload = diff["to_upload"]
    to_update = diff["to_update"]
    to_move = diff.get("to_move", [])  # Backwards compatible
    to_delete = diff["to_delete"]
    unchanged = diff["unchanged"]

    console.print()
    console.print("[bold cyan]📊 Mirror Preview:[/bold cyan]")
    console.print(f"  [green]✅ Unchanged:[/green] {len(unchanged)} files")
    console.print(f"  [yellow]⬆️  Upload:[/yellow] {len(to_upload)} files (new)")
    console.print(f"  [blue]🔄 Update:[/blue] {len(to_update)} files (hash mismatch)")
    console.print(f"  [magenta]🔀 Move:[/magenta] {len(to_move)} files (relocated)")
    console.print(f"  [red]🗑️  Delete:[/red] {len(to_delete)} files (remote only)")

    # Calculate sizes
    upload_files = [f for f in local_files if f["relative_path"] in to_upload]
    update_files = [f for f in local_files if f["relative_path"] in to_update]
    upload_size = sum(f["file_size_bytes"] for f in upload_files)
    update_size = sum(f["file_size_bytes"] for f in update_files)
    move_size = sum(m["file_size_bytes"] for m in to_move)
    delete_size = sum(d["file_size_bytes"] for d in to_delete)

    if to_upload:
        console.print(f"    [dim]({upload_size / (1024 * 1024):.1f} MB)[/dim]")
    if to_update:
        console.print(f"    [dim]({update_size / (1024 * 1024):.1f} MB)[/dim]")
    if to_move:
        console.print(
            f"    [dim]({move_size / (1024 * 1024):.1f} MB will be moved server-side)[/dim]"
        )
    if to_delete:
        console.print(
            f"    [dim]({delete_size / (1024 * 1024):.1f} MB will be freed)[/dim]"
        )

    console.print()

    # Show files to delete (CRITICAL!)
    if to_delete:
        console.print(
            "[bold red]⚠️  WARNING: The following files will be DELETED from remote storage:[/bold red]"
        )
        for d in to_delete[:10]:
            console.print(f"    [dim red]- {d['relative_path']}[/dim red]")
        if len(to_delete) > 10:
            console.print(f"    [dim]... and {len(to_delete) - 10} more files[/dim]")
        console.print()

    # Check if there's anything to do
    if not to_upload and not to_update and not to_move and not to_delete:
        console.print("[green]✓ Everything in sync! No changes needed.[/green]")
        sys.exit(0)

    # Dry-run mode
    if dry_run:
        console.print(
            "[bold yellow]🔍 DRY-RUN MODE: No changes will be made.[/bold yellow]"
        )
        console.print("[dim]Run without --dry-run to execute.[/dim]")
        sys.exit(0)

    # Confirmation prompt (only if files will be deleted - dangerous operation!)
    if not yes and to_delete:
        console.print(
            "[bold red]⚠️  This will DELETE files from remote storage! ⚠️[/bold red]"
        )
        confirm = click.confirm("Continue with mirror sync?", default=False)
        if not confirm:
            console.print("[yellow]✗ Aborted by user[/yellow]")
            sys.exit(0)

    console.print()

    # Step 4: Execute sync
    uploaded_count = 0
    updated_count = 0
    moved_count = 0
    deleted_count = 0
    errors = []

    # 4a) Upload new/changed files (batch upload like regular upload command)
    files_to_sync = upload_files + update_files
    if files_to_sync:
        console.print("[bold]⬆️  Uploading files...[/bold]")

        BATCH_SIZE = 3
        upload_url = f"{config['api_url']}/api/v1/song-projects/{project_id}/folders/{folder_id}/batch-upload"

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("•"),
            TextColumn("[bold blue]{task.completed}/{task.total}[/bold blue]"),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Uploading...", total=len(files_to_sync))

            for i in range(0, len(files_to_sync), BATCH_SIZE):
                batch = files_to_sync[i : i + BATCH_SIZE]

                file_objects = []
                for f in batch:
                    try:
                        file_objects.append(
                            (
                                "files",
                                (
                                    f["relative_path"],
                                    open(f["local_file_path"], "rb"),
                                    "application/octet-stream",
                                ),
                            )
                        )
                    except Exception as e:
                        errors.append(
                            {
                                "file": f["relative_path"],
                                "error": f"Could not open file: {e}",
                            }
                        )
                        progress.advance(task)
                        continue

                try:
                    response = requests.post(
                        upload_url,
                        headers={"Authorization": f"Bearer {config['jwt_token']}"},
                        files=file_objects,
                        verify=config.get("ssl_verify", False),
                        timeout=300,
                    )

                    # Close file handles
                    for _, file_tuple in file_objects:
                        file_tuple[1].close()

                    if response.status_code == 200:
                        result = response.json()
                        uploaded_count += result.get("uploaded", 0)
                        updated_count += len(batch) - result.get("uploaded", 0)
                        if result.get("errors"):
                            errors.extend(result["errors"])
                    else:
                        error = response.json().get(
                            "error", f"HTTP {response.status_code}"
                        )
                        for f in batch:
                            errors.append({"file": f["relative_path"], "error": error})

                    progress.advance(task, advance=len(batch))

                except requests.exceptions.Timeout:
                    for f in batch:
                        errors.append(
                            {"file": f["relative_path"], "error": "Connection timeout"}
                        )
                    progress.advance(task, advance=len(batch))
                except Exception as e:
                    for f in batch:
                        errors.append({"file": f["relative_path"], "error": str(e)})
                    progress.advance(task, advance=len(batch))

        console.print()

    # 4b) Move files (S3 server-side copy)
    if to_move:
        console.print("[bold]🔀 Moving files...[/bold]")

        move_url = (
            f"{config['api_url']}/api/v1/song-projects/{project_id}/files/batch-move"
        )
        move_payload = {
            "move_actions": [
                {
                    "file_id": m["file_id"],
                    "old_path": m["old_path"],
                    "new_path": m["new_path"],
                    "s3_key_old": m["s3_key_old"],
                    "s3_key_new": m["s3_key_new"],
                    "file_hash": m["file_hash"],
                }
                for m in to_move
            ]
        }

        try:
            response = requests.post(
                move_url,
                headers={
                    "Authorization": f"Bearer {config['jwt_token']}",
                    "Content-Type": "application/json",
                },
                json=move_payload,
                verify=config.get("ssl_verify", False),
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()["data"]
                moved_count = result["moved"]
                if result.get("errors"):
                    errors.extend(
                        [
                            {"file": e["file_id"], "error": e["error"]}
                            for e in result["errors"]
                        ]
                    )
            else:
                error = response.json().get("error", f"HTTP {response.status_code}")
                console.print(f"[red]✗ Batch move failed: {error}[/red]")

        except requests.exceptions.Timeout:
            console.print("[red]✗ Move timeout[/red]")
        except Exception as e:
            console.print(f"[red]✗ Move error: {str(e)}[/red]")

        console.print()

    # 4c) Delete obsolete files (batch delete)
    if to_delete:
        console.print("[bold]🗑️  Deleting obsolete files...[/bold]")

        delete_url = (
            f"{config['api_url']}/api/v1/song-projects/{project_id}/files/batch-delete"
        )
        delete_payload = {"file_ids": [d["file_id"] for d in to_delete]}

        try:
            response = requests.delete(
                delete_url,
                headers={
                    "Authorization": f"Bearer {config['jwt_token']}",
                    "Content-Type": "application/json",
                },
                json=delete_payload,
                verify=config.get("ssl_verify", False),
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()["data"]
                deleted_count = result["deleted"]
                if result.get("errors"):
                    errors.extend(
                        [
                            {"file": e["file_id"], "error": e["error"]}
                            for e in result["errors"]
                        ]
                    )
            else:
                error = response.json().get("error", f"HTTP {response.status_code}")
                console.print(f"[red]✗ Batch delete failed: {error}[/red]")

        except Exception as e:
            console.print(f"[red]✗ Delete error: {str(e)}[/red]")

        console.print()

    # Step 5: Summary
    console.print("[bold green]✓ Mirror sync completed![/bold green]")
    console.print()
    console.print(f"  [green]✅ Unchanged:[/green] {len(unchanged)} files")
    console.print(f"  [yellow]⬆️  Uploaded:[/yellow] {uploaded_count} files")
    console.print(f"  [blue]🔄 Updated:[/blue] {updated_count} files")
    console.print(f"  [magenta]🔀 Moved:[/magenta] {moved_count} files")
    console.print(f"  [red]🗑️  Deleted:[/red] {deleted_count} files")

    if errors:
        console.print()
        console.print(f"[bold red]✗ {len(errors)} errors occurred:[/bold red]")
        for err in errors[:10]:
            filename = err.get("file", "unknown")
            error_msg = err.get("error", "unknown error")
            console.print(f"  [dim red]- {filename}: {error_msg}[/dim red]")
        if len(errors) > 10:
            console.print(f"  [dim]... and {len(errors) - 10} more errors[/dim]")


@cli.command()
@click.argument("project_id")
@click.option(
    "--folder", "folder_id", default=None, help="Only fix files in specific folder"
)
@click.option("--dry-run", is_flag=True, help="Preview changes without updating")
def fix_mime(project_id, folder_id, dry_run):
    """Fix missing/wrong MIME types for project files

    Scans all files in database with NULL or 'application/octet-stream'
    MIME types and updates them based on filename extension.

    No local files needed - works purely on S3 metadata in database.

    Uses the comprehensive MIME type mapping including:
    - Audio formats (FLAC, WAV, MP3, etc.)
    - DAW projects (Cubase, Nuendo, Studio One, etc.)
    - Audio tools (Melodyne, SpectraLayers, etc.)
    - Archives (ZIP, GZIP, 7Z, RAR, etc.)
    - Images and documents

    Examples:
        aiproxy-cli fix-mime <project-id>
        aiproxy-cli fix-mime <project-id> --folder <folder-id>
        aiproxy-cli fix-mime <project-id> --dry-run
    """

    # Load config
    config = load_config()
    if not config:
        console.print("[red]✗ Not logged in. Run: aiproxy-cli login[/red]")
        sys.exit(1)

    # Check token expiry
    if not check_token_expiry(config):
        console.print("[yellow]Run: aiproxy-cli login[/yellow]")
        sys.exit(1)

    # Build URL with query parameters
    url = f"{config['api_url']}/api/v1/song-projects/{project_id}/files/fix-mime"
    params = {}
    if folder_id:
        params["folder_id"] = folder_id
    if dry_run:
        params["dry_run"] = "true"

    # Show header
    console.print("[bold]🔍 Scanning project files for MIME type issues...[/bold]")
    if folder_id:
        console.print(f"[dim]Folder: {folder_id}[/dim]")
    if dry_run:
        console.print("[yellow]DRY-RUN MODE: No changes will be made[/yellow]")
    console.print()

    try:
        with console.status("[bold green]Analyzing MIME types..."):
            response = requests.post(
                url,
                params=params,
                headers={"Authorization": f"Bearer {config['jwt_token']}"},
                verify=config.get("ssl_verify", False),
                timeout=60,
            )

        if response.status_code != 200:
            error = response.json().get("error", f"HTTP {response.status_code}")
            console.print(f"[red]✗ Failed: {error}[/red]")
            sys.exit(1)

        data = response.json()["data"]
        scanned = data["scanned"]
        updated = data["updated"]
        unchanged = data["unchanged"]
        files = data["files"]

        # Summary
        console.print("[bold cyan]📊 MIME Type Fix Summary:[/bold cyan]")
        console.print(f"  [blue]📁 Scanned:[/blue]   {scanned} files")
        console.print(f"  [green]✓ Updated:[/green]   {updated} files")
        console.print(f"  [dim]✓ Unchanged:[/dim] {unchanged} files")
        console.print()

        if files:
            console.print("[bold]📝 Changes:[/bold]")
            for f in files[:20]:  # Show max 20
                old = f["old_mime"] if f["old_mime"] else "[red]NULL[/red]"
                new = f["new_mime"]
                filename = f["filename"]

                # Truncate long filenames
                if len(filename) > 60:
                    filename = filename[:57] + "..."

                console.print(f"  [cyan]{filename}[/cyan]")
                console.print(f"    {old} → [green]{new}[/green]")

            if len(files) > 20:
                console.print(f"  [dim]... and {len(files) - 20} more files[/dim]")

        console.print()

        if dry_run:
            console.print(
                "[yellow]🔍 DRY-RUN: Run without --dry-run to apply changes[/yellow]"
            )
        elif updated > 0:
            console.print("[green]✓ MIME types updated successfully![/green]")
        else:
            console.print("[green]✓ All files already have correct MIME types![/green]")

    except requests.exceptions.Timeout:
        console.print("[red]✗ Connection timeout[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗ Error: {str(e)}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    cli()
