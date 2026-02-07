"""
Song Release API Routes - HTTP endpoints for song release management.

CRITICAL:
- ALL endpoints require JWT authentication (@jwt_required)
- User ID from JWT token (get_current_user_id), NOT from URL params
- Input validation with Pydantic schemas
- Cover upload as multipart/form-data (200x200 px validation)

Endpoints:
- POST   /api/v1/song-releases              Create release (with optional cover upload)
- GET    /api/v1/song-releases              List releases (paginated, filtered)
- GET    /api/v1/song-releases/{id}         Get release by ID (with assigned projects)
- PUT    /api/v1/song-releases/{id}         Update release (with optional cover upload)
- DELETE /api/v1/song-releases/{id}         Delete release (with S3 cleanup)
"""

from io import BytesIO
from uuid import UUID

from flask import Blueprint, jsonify, request
from PIL import Image
from pydantic import ValidationError
from sqlalchemy.orm import Session

from api.auth_middleware import get_current_user_id, jwt_required
from api.controllers.song_release_controller import song_release_controller
from db.database import get_db
from schemas.song_release_schemas import ReleaseCreateRequest, ReleaseFilterRequest, ReleaseUpdateRequest
from utils.logger import logger


# Blueprint definition
api_song_releases_v1 = Blueprint("api_song_releases_v1", __name__, url_prefix="/api/v1/song-releases")


@api_song_releases_v1.route("", methods=["POST"])
@jwt_required
def create_release():
    """
    Create new release with project assignments and optional cover upload.

    Request:
        Content-Type: multipart/form-data
        Form Data:
            - data (JSON string): Release data (ReleaseCreateRequest)
            - cover (optional): Cover image file (200x200 px)

    Response:
        201: {'data': {'id': '...'}, 'message': 'Release created successfully'}
        400: {'error': 'Validation error: ...' | 'Invalid cover dimensions: ...'}
        401: {'error': 'Unauthorized'}
        500: {'error': 'Failed to create release: ...'}

    Example:
        POST /api/v1/song-releases
        Headers: Authorization: Bearer <JWT_TOKEN>
        Form Data:
            data: {
                "type": "single",
                "name": "My Awesome Song",
                "status": "draft",
                "genre": "Rock",
                "project_ids": ["550e8400-e29b-41d4-a716-446655440000"],
                "description": "A new single release"
            }
            cover: cover.jpg (binary, 200x200 px)
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        # Parse JSON data from form field
        if "data" not in request.form:
            return jsonify({"error": "Missing 'data' field in form"}), 400

        import json

        release_dict = json.loads(request.form["data"])
        release_data = ReleaseCreateRequest.model_validate(release_dict)
    except json.JSONDecodeError as e:
        return jsonify({"error": f"Invalid JSON in 'data' field: {str(e)}"}), 400
    except ValidationError as e:
        return jsonify({"error": f"Validation error: {e}"}), 400

    # Handle optional cover upload
    cover_file = None
    if "cover" in request.files:
        cover = request.files["cover"]
        if cover.filename:
            try:
                # Read file data
                file_data = cover.read()

                # Get image dimensions using PIL
                image = Image.open(BytesIO(file_data))
                width, height = image.size

                # Prepare cover file tuple (data, filename, width, height)
                cover_file = (file_data, cover.filename, width, height)

            except Exception as e:
                logger.error("Cover image processing error", error=str(e), error_type=type(e).__name__)
                return jsonify({"error": f"Failed to process cover image: {str(e)}"}), 400

    db: Session = next(get_db())
    try:
        result, status_code = song_release_controller.create_release(db, UUID(user_id), release_data, cover_file)
        return jsonify(result), status_code
    finally:
        db.close()


@api_song_releases_v1.route("", methods=["GET"])
@jwt_required
def list_releases():
    """
    Get list of releases for user (paginated, searchable, filterable).

    Query Parameters:
        - limit (int): Items per page (1-100, default: 20)
        - offset (int): Offset for pagination (default: 0)
        - status_filter (str): Filter by status group ('all', 'progress', 'uploaded', 'released', 'archive')
        - search (str): Search term (name, genre)

    Response:
        200: {'data': {'items': [...], 'total': 10, 'limit': 20, 'offset': 0}}
        401: {'error': 'Unauthorized'}

    Example:
        GET /api/v1/song-releases?limit=10&offset=0&status_filter=progress&search=rock
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    # Parse query parameters
    try:
        limit = min(int(request.args.get("limit", 20)), 100)
        offset = max(int(request.args.get("offset", 0)), 0)
    except ValueError:
        return jsonify({"error": "Invalid limit or offset"}), 400

    status_filter = request.args.get("status_filter")
    search = request.args.get("search")

    filters = ReleaseFilterRequest(limit=limit, offset=offset, status_filter=status_filter, search=search)

    db: Session = next(get_db())
    try:
        result, status_code = song_release_controller.get_releases(db, UUID(user_id), filters)
        return jsonify(result), status_code
    finally:
        db.close()


@api_song_releases_v1.route("/<release_id>", methods=["GET"])
@jwt_required
def get_release(release_id: str):
    """
    Get release details by ID.

    Path Parameters:
        - release_id (UUID): Release ID

    Response:
        200: {'data': {...}}
        401: {'error': 'Unauthorized'}
        404: {'error': 'Release not found'}
        500: {'error': 'Failed to retrieve release: ...'}

    Example:
        GET /api/v1/song-releases/550e8400-e29b-41d4-a716-446655440000
        Headers: Authorization: Bearer <JWT_TOKEN>
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        release_uuid = UUID(release_id)
    except ValueError:
        return jsonify({"error": "Invalid release ID format"}), 400

    db: Session = next(get_db())
    try:
        result, status_code = song_release_controller.get_release(db, UUID(user_id), release_uuid)
        return jsonify(result), status_code
    finally:
        db.close()


@api_song_releases_v1.route("/<release_id>", methods=["PUT"])
@jwt_required
def update_release(release_id: str):
    """
    Update release with optional cover upload and project reassignment.

    Path Parameters:
        - release_id (UUID): Release ID

    Request:
        Content-Type: multipart/form-data
        Form Data:
            - data (JSON string): Update data (ReleaseUpdateRequest)
            - cover (optional): New cover image file (200x200 px)

    Response:
        200: {'data': {...}, 'message': 'Release updated successfully'}
        400: {'error': 'Validation error: ...' | 'Invalid cover dimensions: ...'}
        401: {'error': 'Unauthorized'}
        404: {'error': 'Release not found or update failed'}
        500: {'error': 'Failed to update release: ...'}

    Example:
        PUT /api/v1/song-releases/550e8400-e29b-41d4-a716-446655440000
        Headers: Authorization: Bearer <JWT_TOKEN>
        Form Data:
            data: {"status": "uploaded", "upload_date": "2024-01-15"}
            cover: new_cover.jpg (binary, 200x200 px)
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        release_uuid = UUID(release_id)
    except ValueError:
        return jsonify({"error": "Invalid release ID format"}), 400

    try:
        # Parse JSON data from form field
        if "data" not in request.form:
            return jsonify({"error": "Missing 'data' field in form"}), 400

        import json

        update_dict = json.loads(request.form["data"])
        update_data = ReleaseUpdateRequest.model_validate(update_dict)
    except json.JSONDecodeError as e:
        return jsonify({"error": f"Invalid JSON in 'data' field: {str(e)}"}), 400
    except ValidationError as e:
        return jsonify({"error": f"Validation error: {e}"}), 400

    # Handle optional cover upload
    cover_file = None
    if "cover" in request.files:
        cover = request.files["cover"]
        if cover.filename:
            try:
                # Read file data
                file_data = cover.read()

                # Get image dimensions using PIL
                image = Image.open(BytesIO(file_data))
                width, height = image.size

                # Prepare cover file tuple (data, filename, width, height)
                cover_file = (file_data, cover.filename, width, height)

            except Exception as e:
                logger.error("Cover image processing error", error=str(e), error_type=type(e).__name__)
                return jsonify({"error": f"Failed to process cover image: {str(e)}"}), 400

    db: Session = next(get_db())
    try:
        result, status_code = song_release_controller.update_release(
            db, UUID(user_id), release_uuid, update_data, cover_file
        )
        return jsonify(result), status_code
    finally:
        db.close()


@api_song_releases_v1.route("/<release_id>", methods=["DELETE"])
@jwt_required
def delete_release(release_id: str):
    """
    Delete release and cleanup S3 cover.

    Path Parameters:
        - release_id (UUID): Release ID

    Response:
        200: {'message': 'Release deleted successfully'}
        401: {'error': 'Unauthorized'}
        404: {'error': 'Release not found or deletion failed'}
        500: {'error': 'Failed to delete release: ...'}

    Example:
        DELETE /api/v1/song-releases/550e8400-e29b-41d4-a716-446655440000
        Headers: Authorization: Bearer <JWT_TOKEN>
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        release_uuid = UUID(release_id)
    except ValueError:
        return jsonify({"error": "Invalid release ID format"}), 400

    db: Session = next(get_db())
    try:
        result, status_code = song_release_controller.delete_release(db, UUID(user_id), release_uuid)
        return jsonify(result), status_code
    finally:
        db.close()


@api_song_releases_v1.route("/<release_id>/cover", methods=["GET"])
@jwt_required
def serve_cover(release_id: str):
    """
    Serve release cover image via backend proxy (streams from S3).

    CRITICAL: This is a backend proxy route - NEVER return presigned URLs to frontend!

    Path Parameters:
        - release_id (UUID): Release ID

    Response:
        200: Binary image data (image/jpeg, image/png, etc.)
        401: {'error': 'Unauthorized'}
        404: {'error': 'Release not found' | 'Cover not found'}
        500: {'error': 'Failed to load cover from S3'}

    Example:
        GET /api/v1/song-releases/550e8400-e29b-41d4-a716-446655440000/cover
        Headers: Authorization: Bearer <JWT_TOKEN>
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        from adapters.s3.s3_proxy_service import s3_proxy_service
        from config.settings import S3_SONG_RELEASES_BUCKET
        from db.song_release_service import song_release_service

        release_uuid = UUID(release_id)

        logger.debug("Serving release cover", release_id=release_id, user_id=user_id)

        # Get release from DB
        db: Session = next(get_db())
        try:
            release = song_release_service.get_release_by_id(db, release_uuid, UUID(user_id))
            if not release:
                return jsonify({"error": "Release not found"}), 404

            # Verify release has cover
            if not release.cover_s3_key:
                return jsonify({"error": "Cover not found"}), 404

            # Stream from S3 using generic proxy service
            return s3_proxy_service.serve_resource(
                bucket=S3_SONG_RELEASES_BUCKET, s3_key=release.cover_s3_key, filename="cover.jpg"
            )

        finally:
            db.close()

    except ValueError:
        return jsonify({"error": "Invalid release ID format"}), 400
    except Exception as e:
        logger.error(
            "Error serving release cover",
            release_id=release_id,
            error=str(e),
            error_type=type(e).__name__,
        )
        return jsonify({"error": "Failed to load cover from S3"}), 500
