"""
Song Project API Routes - HTTP endpoints for song project management.

CRITICAL:
- ALL endpoints require JWT authentication (@jwt_required)
- User ID from JWT token (get_current_user_id), NOT from URL params
- Input validation with Pydantic schemas
- Parameter validation (limit, offset)

Endpoints:
- POST   /api/v1/song-projects              Create project
- GET    /api/v1/song-projects              List projects (paginated)
- GET    /api/v1/song-projects/{id}         Get project by ID (with folders and files)
- PUT    /api/v1/song-projects/{id}         Update project
- DELETE /api/v1/song-projects/{id}         Delete project (with S3 cleanup)
- POST   /api/v1/song-projects/{id}/files   Upload file to project folder
"""

from uuid import UUID

from flask import Blueprint, jsonify, request
from pydantic import ValidationError
from sqlalchemy.orm import Session

from api.auth_middleware import get_current_user_id, jwt_required
from api.controllers.song_project_controller import song_project_controller
from db.database import get_db
from schemas.song_project_schemas import BatchDeleteRequest, MirrorRequest, ProjectCreateRequest, ProjectUpdateRequest
from utils.logger import logger


# Blueprint definition
api_song_projects_v1 = Blueprint("api_song_projects_v1", __name__, url_prefix="/api/v1/song-projects")


@api_song_projects_v1.route("", methods=["POST"])
@jwt_required
def create_project():
    """
    Create new project with default folder structure.

    Request Body:
        ProjectCreateRequest (JSON)

    Response:
        201: {'data': {'id': '...'}, 'message': 'Project created successfully'}
        401: {'error': 'Unauthorized'}
        500: {'error': 'Failed to create project: ...'}

    Example:
        POST /api/v1/song-projects
        Headers: Authorization: Bearer <JWT_TOKEN>
        Body: {
            "project_name": "My Awesome Song",
            "tags": ["rock", "demo"],
            "description": "A new project for my rock song"
        }
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        project_data = ProjectCreateRequest.model_validate(request.json)
    except ValidationError as e:
        return jsonify({"error": f"Validation error: {e}"}), 400

    db: Session = next(get_db())
    try:
        result, status_code = song_project_controller.create_project(db, UUID(user_id), project_data)
        return jsonify(result), status_code
    finally:
        db.close()


@api_song_projects_v1.route("", methods=["GET"])
@jwt_required
def list_projects():
    """
    Get list of projects for user (paginated, searchable).

    Query Parameters:
        - limit (int): Items per page (1-100, default: 20)
        - offset (int): Offset for pagination (default: 0)
        - search (str): Search term (project_name, description)
        - tags (str): Comma-separated tags filter
        - project_status (str): Status filter ('new', 'progress', 'archived', or None for all non-archived)

    Response:
        200: {'data': [...], 'pagination': {...}}
        401: {'error': 'Unauthorized'}

    Example:
        GET /api/v1/song-projects?limit=10&offset=0&search=rock&tags=demo,wip&project_status=new
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    # Parse query parameters
    try:
        limit = int(request.args.get("limit", 20))
        offset = int(request.args.get("offset", 0))

        # Validate parameters
        if limit <= 0 or limit > 100:
            return jsonify({"error": "Limit must be between 1 and 100"}), 400
        if offset < 0:
            return jsonify({"error": "Offset must be >= 0"}), 400

    except ValueError:
        return jsonify({"error": "Invalid limit or offset parameter"}), 400

    # Parse search and filter parameters
    search = request.args.get("search", "").strip()
    tags = request.args.get("tags", None)
    project_status = request.args.get("project_status", None)

    db: Session = next(get_db())
    try:
        result, status_code = song_project_controller.get_projects(
            db=db,
            user_id=UUID(user_id),
            limit=limit,
            offset=offset,
            search=search,
            tags=tags,
            project_status=project_status,
        )
        return jsonify(result), status_code
    finally:
        db.close()


@api_song_projects_v1.route("/<project_id>", methods=["GET"])
@jwt_required
def get_project(project_id: str):
    """
    Get a specific project by ID (with all folders and files).

    Path Parameters:
        - project_id (UUID): Project ID

    Response:
        200: {'data': {'folders': [...], ...}}
        404: {'error': 'Project not found with ID: ...'}
        401: {'error': 'Unauthorized'}

    Example:
        GET /api/v1/song-projects/550e8400-e29b-41d4-a716-446655440000
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    db: Session = next(get_db())
    try:
        # Always return project with details (folders and files)
        result, status_code = song_project_controller.get_project_with_details(db, UUID(user_id), project_id)
        return jsonify(result), status_code
    finally:
        db.close()


@api_song_projects_v1.route("/<project_id>", methods=["PUT"])
@jwt_required
def update_project(project_id: str):
    """
    Update an existing project.

    Path Parameters:
        - project_id (UUID): Project ID

    Request Body:
        ProjectUpdateRequest (JSON)

    Response:
        200: {'data': {...}, 'message': 'Project updated successfully'}
        404: {'error': 'Project not found'}
        401: {'error': 'Unauthorized'}

    Example:
        PUT /api/v1/song-projects/550e8400-e29b-41d4-a716-446655440000
        Body: {
            "project_name": "Updated Project Name",
            "tags": ["rock", "mastered"]
        }
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        update_data = ProjectUpdateRequest.model_validate(request.json)
    except ValidationError as e:
        return jsonify({"error": f"Validation error: {e}"}), 400

    db: Session = next(get_db())
    try:
        result, status_code = song_project_controller.update_project(db, UUID(user_id), project_id, update_data)
        return jsonify(result), status_code
    finally:
        db.close()


@api_song_projects_v1.route("/<project_id>", methods=["DELETE"])
@jwt_required
def delete_project(project_id: str):
    """
    Delete a project (with S3 cleanup).

    Path Parameters:
        - project_id (UUID): Project ID

    Response:
        200: {'message': 'Project deleted successfully'}
        404: {'error': 'Project not found'}
        401: {'error': 'Unauthorized'}

    Example:
        DELETE /api/v1/song-projects/550e8400-e29b-41d4-a716-446655440000
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    db: Session = next(get_db())
    try:
        result, status_code = song_project_controller.delete_project(db, UUID(user_id), project_id)
        return jsonify(result), status_code
    finally:
        db.close()


@api_song_projects_v1.route("/<project_id>/files", methods=["POST"])
@jwt_required
def upload_file(project_id: str):
    """
    Upload file to project folder.

    Path Parameters:
        - project_id (UUID): Project ID

    Form Data:
        - file: File to upload (multipart/form-data)
        - folder_id (UUID): Target folder ID

    Response:
        201: {'data': {...}, 'message': 'File uploaded successfully'}
        400: {'error': 'No file provided' | 'folder_id required' | 'Invalid ID format'}
        404: {'error': 'Project not found or unauthorized' | 'Folder not found with ID: ...'}
        401: {'error': 'Unauthorized'}
        500: {'error': 'Failed to upload file: ...'}

    Example:
        POST /api/v1/song-projects/550e8400-e29b-41d4-a716-446655440000/files
        Headers: Authorization: Bearer <JWT_TOKEN>
        Form Data:
            file: test.wav (binary)
            folder_id: 123e4567-e89b-12d3-a456-426614174000
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    folder_id = request.form.get("folder_id")

    if not folder_id:
        return jsonify({"error": "folder_id required"}), 400

    # Read file data
    file_data = file.read()
    filename = file.filename

    db: Session = next(get_db())
    try:
        result, status_code = song_project_controller.upload_file(
            db, UUID(user_id), project_id, folder_id, filename, file_data
        )
        return jsonify(result), status_code
    finally:
        db.close()


@api_song_projects_v1.route("/<project_id>/folders/<folder_id>/files", methods=["GET"])
@jwt_required
def get_folder_files(project_id: str, folder_id: str):
    """
    Get all files in a project folder with download URLs (CLI download endpoint).

    Path Parameters:
        - project_id (UUID): Project ID
        - folder_id (UUID): Folder ID

    Response:
        200: {'data': [{'id': '...', 'filename': '...', 'relative_path': '...', 'download_url': '...', 'file_size_bytes': 123}]}
        404: {'error': 'Project not found or unauthorized' | 'Folder not found'}
        401: {'error': 'Unauthorized'}

    Example:
        GET /api/v1/song-projects/550e8400-e29b-41d4-a716-446655440000/folders/123e4567-e89b-12d3-a456-426614174000/files
        Headers: Authorization: Bearer <JWT_TOKEN>
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    db: Session = next(get_db())
    try:
        result, status_code = song_project_controller.get_folder_files(db, UUID(user_id), project_id, folder_id)
        return jsonify(result), status_code
    finally:
        db.close()


@api_song_projects_v1.route("/<project_id>/folders/<folder_id>/batch-upload", methods=["POST"])
@jwt_required
def batch_upload_files(project_id: str, folder_id: str):
    """
    Upload multiple files to project folder (CLI endpoint).

    Path Parameters:
        - project_id (UUID): Project ID
        - folder_id (UUID): Target folder ID

    Form Data:
        - files: Multiple files (multipart/form-data)

    Response:
        200: {'data': {'uploaded': 5, 'failed': 2, 'errors': [...]}, 'message': 'Batch upload completed'}
        400: {'error': 'No files provided' | 'Invalid ID format'}
        404: {'error': 'Project not found or unauthorized' | 'Folder not found: ...'}
        401: {'error': 'Unauthorized'}
        500: {'error': 'Batch upload failed: ...'}

    Example:
        POST /api/v1/song-projects/550e8400-e29b-41d4-a716-446655440000/folders/123e4567-e89b-12d3-a456-426614174000/batch-upload
        Headers: Authorization: Bearer <JWT_TOKEN>
        Form Data:
            files: test1.wav, test2.mp3, test3.flac (multiple files)
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    if "files" not in request.files:
        return jsonify({"error": "No files provided"}), 400

    files = request.files.getlist("files")

    if not files:
        return jsonify({"error": "No files provided"}), 400

    db: Session = next(get_db())
    try:
        result, status_code = song_project_controller.batch_upload_files(
            db, UUID(user_id), project_id, folder_id, files
        )
        return jsonify(result), status_code
    finally:
        db.close()


@api_song_projects_v1.route("/<project_id>/folders/<folder_id>/mirror", methods=["POST"])
@jwt_required
def mirror_compare(project_id: str, folder_id: str):
    """
    Compare local files vs remote files (for Mirror sync).

    Request Body:
        MirrorRequest (JSON): {files: [{relative_path, file_hash, file_size_bytes}]}

    Response:
        200: {
            'data': {
                'to_upload': ['file1.wav', ...],
                'to_update': ['file2.wav', ...],
                'to_delete': [{'file_id': '...', 'relative_path': '...'}],
                'unchanged': ['file3.wav', ...]
            }
        }
        401: {'error': 'Unauthorized'}
        400: {'error': 'Validation error: ...'}
        500: {'error': 'Mirror compare failed: ...'}

    Example:
        POST /api/v1/song-projects/{id}/folders/{folder_id}/mirror
        Headers: Authorization: Bearer <JWT_TOKEN>
        Body: {
            "files": [
                {"relative_path": "01 Arrangement/drums.flac", "file_hash": "abc123...", "file_size_bytes": 123456},
                {"relative_path": "01 Arrangement/bass.flac", "file_hash": "def456...", "file_size_bytes": 234567}
            ]
        }
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        mirror_data = MirrorRequest.model_validate(request.json)
    except ValidationError as e:
        return jsonify({"error": f"Validation error: {e}"}), 400

    db: Session = next(get_db())
    try:
        result, status_code = song_project_controller.mirror_compare(
            db, UUID(user_id), project_id, folder_id, mirror_data
        )
        return jsonify(result), status_code
    finally:
        db.close()


@api_song_projects_v1.route("/<project_id>/files/batch-delete", methods=["DELETE"])
@jwt_required
def batch_delete_files(project_id: str):
    """
    Delete multiple files from project (S3 + DB).

    Request Body:
        BatchDeleteRequest (JSON): {file_ids: ["uuid1", "uuid2", ...]}

    Response:
        200: {
            'data': {
                'deleted': 3,
                'failed': 1,
                'errors': [{'file_id': '...', 'error': '...'}]
            }
        }
        401: {'error': 'Unauthorized'}
        400: {'error': 'Validation error: ...'}
        500: {'error': 'Batch delete failed: ...'}

    Example:
        DELETE /api/v1/song-projects/{id}/files/batch-delete
        Headers: Authorization: Bearer <JWT_TOKEN>
        Body: {
            "file_ids": [
                "550e8400-e29b-41d4-a716-446655440000",
                "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
            ]
        }
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        delete_data = BatchDeleteRequest.model_validate(request.json)
    except ValidationError as e:
        return jsonify({"error": f"Validation error: {e}"}), 400

    db: Session = next(get_db())
    try:
        result, status_code = song_project_controller.batch_delete_files(db, UUID(user_id), project_id, delete_data)
        return jsonify(result), status_code
    finally:
        db.close()


@api_song_projects_v1.route("/<project_id>/files/batch-move", methods=["POST"])
@jwt_required
def batch_move_files(project_id: str):
    """
    Move multiple files within project (S3 server-side copy + DB update).

    Request Body:
        {
            "move_actions": [
                {
                    "file_id": "uuid",
                    "old_path": "Media/file.flac",
                    "new_path": "Audio/file.flac",
                    "s3_key_old": "projects/.../Media/file.flac",
                    "s3_key_new": "projects/.../Audio/file.flac",
                    "file_hash": "sha256..."
                }
            ]
        }

    Response:
        200: {
            'data': {
                'moved': 3,
                'failed': 1,
                'errors': [{'file_id': '...', 'error': '...'}]
            }
        }
        401: {'error': 'Unauthorized'}
        400: {'error': 'Missing move_actions'}
        500: {'error': 'Batch move failed: ...'}

    Example:
        POST /api/v1/song-projects/{id}/files/batch-move
        Headers: Authorization: Bearer <JWT_TOKEN>
        Body: {
            "move_actions": [
                {
                    "file_id": "550e8400-e29b-41d4-a716-446655440000",
                    "old_path": "Media/drums.flac",
                    "new_path": "Audio/drums.flac",
                    "s3_key_old": "projects/.../01 Arrangement/Media/drums.flac",
                    "s3_key_new": "projects/.../01 Arrangement/Audio/drums.flac",
                    "file_hash": "abc123..."
                }
            ]
        }
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    db: Session = next(get_db())
    try:
        # Parse request body
        data = request.get_json()
        if not data or "move_actions" not in data:
            return jsonify({"error": "Missing move_actions in request body"}), 400

        # Call controller
        result, status_code = song_project_controller.batch_move_files(
            db=db, user_id=UUID(user_id), project_id=project_id, move_actions=data["move_actions"]
        )

        return jsonify(result), status_code
    finally:
        db.close()


@api_song_projects_v1.route("/<project_id>/files/fix-mime", methods=["POST"])
@jwt_required
def fix_mime_types(project_id: str):
    """
    Fix missing/wrong MIME types for all files in project.

    Scans all files with NULL or 'application/octet-stream' MIME types
    and updates them based on filename extension.

    Query Parameters:
        - folder_id (optional): Only fix files in specific folder
        - dry_run (optional): Preview changes without updating (true/false)

    Response:
        200: {
            'data': {
                'scanned': 150,
                'updated': 42,
                'unchanged': 108,
                'files': [
                    {
                        'file_id': 'uuid',
                        'filename': 'track.flac',
                        'old_mime': null,
                        'new_mime': 'audio/flac'
                    }
                ]
            }
        }
        401: {'error': 'Unauthorized'}
        500: {'error': 'Failed to fix MIME types: ...'}

    Example:
        POST /api/v1/song-projects/{id}/files/fix-mime
        POST /api/v1/song-projects/{id}/files/fix-mime?folder_id={folder_id}
        POST /api/v1/song-projects/{id}/files/fix-mime?dry_run=true
        Headers: Authorization: Bearer <JWT_TOKEN>
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    folder_id = request.args.get("folder_id")
    dry_run = request.args.get("dry_run", "").lower() == "true"

    db: Session = next(get_db())
    try:
        result, status_code = song_project_controller.fix_mime_types(db, UUID(user_id), project_id, folder_id, dry_run)
        return jsonify(result), status_code
    finally:
        db.close()


@api_song_projects_v1.route("/<project_id>/files/all", methods=["GET"])
@jwt_required
def get_all_project_files(project_id: str):
    """
    Get all files from all folders for complete project download (CLI endpoint).

    Path Parameters:
        - project_id (UUID): Project ID

    Response:
        200: {
            'data': {
                'project_name': 'My Project',
                'folders': [
                    {
                        'folder_name': '01 Arrangement',
                        'files': [
                            {
                                'filename': 'drums.flac',
                                'relative_path': '01 Arrangement/Media/drums.flac',
                                'download_url': 'https://s3...',
                                'size': 1234567
                            }
                        ]
                    },
                    {
                        'folder_name': '02 AI',
                        'files': []
                    }
                ]
            }
        }
        404: {'error': 'Project not found or unauthorized: ...'}
        401: {'error': 'Unauthorized'}
        400: {'error': 'Invalid project ID format'}
        500: {'error': 'Failed to get all project files: ...'}

    Example:
        GET /api/v1/song-projects/550e8400-e29b-41d4-a716-446655440000/files/all
        Headers: Authorization: Bearer <JWT_TOKEN>
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    db: Session = next(get_db())
    try:
        result, status_code = song_project_controller.get_all_project_files_with_urls(db, UUID(user_id), project_id)
        return jsonify(result), status_code
    finally:
        db.close()


@api_song_projects_v1.route("/<project_id>/folders/<folder_id>/clear", methods=["DELETE"])
@jwt_required
def clear_folder_files(project_id: str, folder_id: str):
    """
    Clear all files in a folder (Bereinigung).

    Path Parameters:
        - project_id (UUID): Project ID
        - folder_id (UUID): Folder ID

    Response:
        200: {
            'data': {'deleted': 5, 'errors': []},
            'message': '5 files deleted successfully'
        }
        403: {'error': 'Cannot clear folder in archived project'}
        401: {'error': 'Unauthorized'}
        400: {'error': 'Invalid project or folder ID format'}
        500: {'error': 'Failed to clear folder: ...'}

    Example:
        DELETE /api/v1/song-projects/550e8400-e29b-41d4-a716-446655440000/folders/abc123.../clear
        Headers: Authorization: Bearer <JWT_TOKEN>
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    db: Session = next(get_db())
    try:
        result, status_code = song_project_controller.clear_folder_files(db, UUID(user_id), project_id, folder_id)
        return jsonify(result), status_code
    finally:
        db.close()


@api_song_projects_v1.route("/<project_id>/files/<file_id>/download", methods=["GET"])
@jwt_required
def download_file(project_id: str, file_id: str):
    """
    Download project file via backend proxy (streams from S3).

    CRITICAL: This is a backend proxy route - NEVER return presigned URLs to CLI/frontend!

    Path Parameters:
        - project_id (UUID): Project ID (for security validation)
        - file_id (UUID): File ID

    Response:
        200: Binary file data (application/octet-stream or specific MIME type)
        401: {'error': 'Unauthorized'}
        404: {'error': 'File not found' | 'Project not found'}
        500: {'error': 'Failed to load file from S3'}

    Example:
        GET /api/v1/song-projects/550e8400-e29b-41d4-a716-446655440000/files/abc123.../download
        Headers: Authorization: Bearer <JWT_TOKEN>
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        from adapters.s3.s3_proxy_service import s3_proxy_service
        from config.settings import S3_SONG_PROJECTS_BUCKET
        from db.song_project_service import song_project_service

        project_uuid = UUID(project_id)
        file_uuid = UUID(file_id)

        logger.debug("Serving project file", project_id=project_id, file_id=file_id, user_id=user_id)

        # Get file from DB
        db: Session = next(get_db())
        try:
            file = song_project_service.get_file_by_id(db, file_uuid)
            if not file:
                return jsonify({"error": "File not found"}), 404

            # Security: Verify file belongs to user's project
            if str(file.project_id) != str(project_uuid) or str(file.project.user_id) != str(user_id):
                return jsonify({"error": "File not found"}), 404

            # Verify file has S3 key
            if not file.s3_key:
                return jsonify({"error": "File not available"}), 404

            # Stream from S3 using generic proxy service
            return s3_proxy_service.serve_resource(
                bucket=S3_SONG_PROJECTS_BUCKET, s3_key=file.s3_key, filename=file.filename
            )

        finally:
            db.close()

    except ValueError:
        return jsonify({"error": "Invalid project or file ID format"}), 400
    except Exception as e:
        logger.error(
            "Error serving project file",
            project_id=project_id,
            file_id=file_id,
            error=str(e),
            error_type=type(e).__name__,
        )
        return jsonify({"error": "Failed to load file from S3"}), 500
