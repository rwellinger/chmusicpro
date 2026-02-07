"""
Song Read/Update/Delete Routes
"""

from uuid import UUID

from flask import Blueprint, jsonify, request
from flask_pydantic import validate
from sqlalchemy.orm import Session

from api.auth_middleware import get_current_user_id, jwt_required
from api.controllers.song_controller import SongController
from business.song_orchestrator import SongS3MigrationError
from db.database import get_db
from schemas.common_schemas import ErrorResponse
from schemas.project_asset_schemas import AssignToProjectRequest
from schemas.song_schemas import (
    SongUpdateRequest,
)
from utils.logger import logger


api_song_v1 = Blueprint("api_song_v1", __name__, url_prefix="/api/v1/song")

# Controller instance
song_controller = SongController()


@api_song_v1.route("/list", methods=["GET"])
@jwt_required
def list_songs():
    """Get list of songs with pagination, search and sorting"""
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

    # Parse search and sort parameters
    status = request.args.get("status", None)  # Optional status filter
    search = request.args.get("search", "").strip()
    sort_by = request.args.get("sort_by", "created_at")
    sort_direction = request.args.get("sort_direction", "desc")
    workflow = request.args.get("workflow", None)  # Optional workflow filter

    # Validate sort parameters
    valid_sort_fields = ["created_at", "title", "lyrics"]
    if sort_by not in valid_sort_fields:
        return jsonify({"error": f"Invalid sort_by field. Must be one of: {valid_sort_fields}"}), 400

    if sort_direction not in ["asc", "desc"]:
        return jsonify({"error": "Invalid sort_direction. Must be 'asc' or 'desc'"}), 400

    response_data, status_code = song_controller.get_songs(
        limit=limit,
        offset=offset,
        status=status,
        search=search,
        sort_by=sort_by,
        sort_direction=sort_direction,
        workflow=workflow,
    )

    return jsonify(response_data), status_code


@api_song_v1.route("/<song_id>", methods=["GET"])
@jwt_required
def get_song(song_id):
    """Get single song by ID with all choices"""
    response_data, status_code = song_controller.get_song_by_id(song_id)

    return jsonify(response_data), status_code


@api_song_v1.route("/<song_id>", methods=["DELETE"])
@jwt_required
def delete_song(song_id):
    """Delete song by ID including all choices"""
    response_data, status_code = song_controller.delete_song(song_id)

    return jsonify(response_data), status_code


@api_song_v1.route("/bulk-delete", methods=["DELETE"])
@jwt_required
def bulk_delete_songs():
    """Delete multiple songs by IDs"""
    payload = request.get_json(force=True)

    if not payload:
        return jsonify({"error": "No JSON provided"}), 400

    song_ids = payload.get("ids", [])

    if not isinstance(song_ids, list):
        return jsonify({"error": "ids must be an array"}), 400

    response_data, status_code = song_controller.bulk_delete_songs(song_ids)

    return jsonify(response_data), status_code


@api_song_v1.route("/choice/<choice_id>/rating", methods=["PUT"])
@jwt_required
def update_choice_rating(choice_id):
    """Update rating for a specific song choice"""
    payload = request.get_json(force=True)

    if not payload:
        return jsonify({"error": "No data provided"}), 400

    response_data, status_code = song_controller.update_choice_rating(choice_id, payload)

    return jsonify(response_data), status_code


@api_song_v1.route("/<song_id>", methods=["PUT"])
@jwt_required
@validate()
def update_song(song_id: str, body: SongUpdateRequest):
    """Update song metadata"""
    try:
        response_data, status_code = song_controller.update_song(song_id, body.dict(exclude_none=True))
        return jsonify(response_data), status_code
    except Exception as e:
        error_response = ErrorResponse(error=str(e))
        return jsonify(error_response.dict()), 500


@api_song_v1.route("/<string:song_id>/assign-to-project", methods=["POST"])
@jwt_required
@validate()
def assign_song_to_project(song_id: str, body: AssignToProjectRequest):
    """Assign song to project"""
    try:
        response_data, status_code = song_controller.assign_to_project(
            song_id, str(body.project_id), str(body.folder_id) if body.folder_id else None
        )
        return jsonify(response_data), status_code
    except Exception as e:
        error_response = ErrorResponse(error=str(e))
        return jsonify(error_response.dict()), 500


@api_song_v1.route("/<string:song_id>/unassign-from-project", methods=["DELETE"])
@jwt_required
def unassign_song_from_project(song_id: str):
    """Remove song from its assigned project (link only, song remains)"""
    try:
        response_data, status_code = song_controller.unassign_from_project(song_id)
        return jsonify(response_data), status_code
    except Exception as e:
        error_response = ErrorResponse(error=str(e))
        return jsonify(error_response.dict()), 500


# ============================================================
# S3 Proxy Endpoints (Serves audio from S3)
# ============================================================


@api_song_v1.route("/choice/<choice_id>/mp3", methods=["GET"])
@jwt_required
def serve_choice_mp3(choice_id: str):
    """
    Serve song choice MP3 via backend proxy from S3

    Path Parameters:
        - choice_id (UUID): Choice ID

    Response:
        200: Binary audio data (audio/mpeg)
        401: {'error': 'Unauthorized'}
        404: {'error': 'Choice not found' | 'MP3 not available'}
        500: {'error': 'Failed to load MP3'}

    Example:
        GET /api/v1/song/choice/550e8400-e29b-41d4-a716-446655440000/mp3
        Headers: Authorization: Bearer <JWT_TOKEN>
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        from adapters.s3.s3_proxy_service import s3_proxy_service
        from business.song_orchestrator import song_orchestrator
        from config.settings import S3_SONGS_BUCKET

        choice_uuid = UUID(choice_id)

        logger.debug("Serving choice MP3", choice_id=choice_id, user_id=user_id)

        # Get DB session
        db: Session = next(get_db())
        try:
            s3_key = song_orchestrator.migrate_choice_to_s3(db, str(choice_uuid), "mp3")

            # Stream from S3 using generic proxy service
            return s3_proxy_service.serve_resource(bucket=S3_SONGS_BUCKET, s3_key=s3_key, filename="song.mp3")

        finally:
            db.close()

    except ValueError:
        return jsonify({"error": "Invalid choice ID format"}), 400
    except SongS3MigrationError as e:
        logger.warning("MP3 migration failed", choice_id=choice_id, error=str(e))
        return jsonify({"error": "MP3 not available"}), 404
    except Exception as e:
        logger.error("Error serving choice MP3", choice_id=choice_id, error=str(e), error_type=type(e).__name__)
        return jsonify({"error": "Failed to load MP3"}), 500


@api_song_v1.route("/choice/<choice_id>/flac", methods=["GET"])
@jwt_required
def serve_choice_flac(choice_id: str):
    """
    Serve song choice FLAC via backend proxy from S3

    Path Parameters:
        - choice_id (UUID): Choice ID

    Response:
        200: Binary audio data (audio/flac)
        401: {'error': 'Unauthorized'}
        404: {'error': 'Choice not found' | 'FLAC not available'}
        500: {'error': 'Failed to load FLAC'}

    Example:
        GET /api/v1/song/choice/550e8400-e29b-41d4-a716-446655440000/flac
        Headers: Authorization: Bearer <JWT_TOKEN>
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        from adapters.s3.s3_proxy_service import s3_proxy_service
        from business.song_orchestrator import song_orchestrator
        from config.settings import S3_SONGS_BUCKET

        choice_uuid = UUID(choice_id)

        logger.debug("Serving choice FLAC", choice_id=choice_id, user_id=user_id)

        # Get DB session
        db: Session = next(get_db())
        try:
            s3_key = song_orchestrator.migrate_choice_to_s3(db, str(choice_uuid), "flac")

            # Stream from S3 using generic proxy service
            return s3_proxy_service.serve_resource(bucket=S3_SONGS_BUCKET, s3_key=s3_key, filename="song.flac")

        finally:
            db.close()

    except ValueError:
        return jsonify({"error": "Invalid choice ID format"}), 400
    except SongS3MigrationError as e:
        logger.warning("FLAC migration failed", choice_id=choice_id, error=str(e))
        return jsonify({"error": "FLAC not available"}), 404
    except Exception as e:
        logger.error("Error serving choice FLAC", choice_id=choice_id, error=str(e), error_type=type(e).__name__)
        return jsonify({"error": "Failed to load FLAC"}), 500


@api_song_v1.route("/choice/<choice_id>/wav", methods=["GET"])
@jwt_required
def serve_choice_wav(choice_id: str):
    """
    Serve song choice WAV via backend proxy from S3

    Path Parameters:
        - choice_id (UUID): Choice ID

    Response:
        200: Binary audio data (audio/wav)
        401: {'error': 'Unauthorized'}
        404: {'error': 'Choice not found' | 'WAV not available'}
        500: {'error': 'Failed to load WAV'}

    Example:
        GET /api/v1/song/choice/550e8400-e29b-41d4-a716-446655440000/wav
        Headers: Authorization: Bearer <JWT_TOKEN>
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        from adapters.s3.s3_proxy_service import s3_proxy_service
        from business.song_orchestrator import song_orchestrator
        from config.settings import S3_SONGS_BUCKET

        choice_uuid = UUID(choice_id)

        logger.debug("Serving choice WAV", choice_id=choice_id, user_id=user_id)

        # Get DB session
        db: Session = next(get_db())
        try:
            s3_key = song_orchestrator.migrate_choice_to_s3(db, str(choice_uuid), "wav")

            # Stream from S3 using generic proxy service
            return s3_proxy_service.serve_resource(bucket=S3_SONGS_BUCKET, s3_key=s3_key, filename="song.wav")

        finally:
            db.close()

    except ValueError:
        return jsonify({"error": "Invalid choice ID format"}), 400
    except SongS3MigrationError as e:
        logger.warning("WAV migration failed", choice_id=choice_id, error=str(e))
        return jsonify({"error": "WAV not available"}), 404
    except Exception as e:
        logger.error("Error serving choice WAV", choice_id=choice_id, error=str(e), error_type=type(e).__name__)
        return jsonify({"error": "Failed to load WAV"}), 500


@api_song_v1.route("/choice/<choice_id>/stems", methods=["GET"])
@jwt_required
def serve_choice_stems(choice_id: str):
    """
    Serve song choice stems ZIP via backend proxy from S3

    Path Parameters:
        - choice_id (UUID): Choice ID

    Response:
        200: Binary ZIP data (application/zip)
        401: {'error': 'Unauthorized'}
        404: {'error': 'Choice not found' | 'Stems not available'}
        500: {'error': 'Failed to load stems'}

    Example:
        GET /api/v1/song/choice/550e8400-e29b-41d4-a716-446655440000/stems
        Headers: Authorization: Bearer <JWT_TOKEN>
    """
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        from adapters.s3.s3_proxy_service import s3_proxy_service
        from business.song_orchestrator import song_orchestrator
        from config.settings import S3_SONGS_BUCKET

        choice_uuid = UUID(choice_id)

        logger.debug("Serving choice stems", choice_id=choice_id, user_id=user_id)

        # Get DB session
        db: Session = next(get_db())
        try:
            s3_key = song_orchestrator.migrate_choice_to_s3(db, str(choice_uuid), "stems")

            # Stream from S3 using generic proxy service
            return s3_proxy_service.serve_resource(bucket=S3_SONGS_BUCKET, s3_key=s3_key, filename="stems.zip")

        finally:
            db.close()

    except ValueError:
        return jsonify({"error": "Invalid choice ID format"}), 400
    except SongS3MigrationError as e:
        logger.warning("Stems migration failed", choice_id=choice_id, error=str(e))
        return jsonify({"error": "Stems not available"}), 404
    except Exception as e:
        logger.error("Error serving choice stems", choice_id=choice_id, error=str(e), error_type=type(e).__name__)
        return jsonify({"error": "Failed to load stems"}), 500
