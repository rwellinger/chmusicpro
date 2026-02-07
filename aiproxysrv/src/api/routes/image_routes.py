"""
DALL-E Image Generation Routes with Pydantic validation
"""

import traceback

from flask import Blueprint, jsonify, request, send_from_directory
from flask_pydantic import validate

from api.auth_middleware import get_current_user_id, jwt_required
from api.controllers.image_controller import ImageController
from config.settings import IMAGES_DIR
from schemas.common_schemas import ErrorResponse
from schemas.image_schemas import (
    ImageGenerateRequest,
    ImageListRequest,
    ImageUpdateRequest,
)
from schemas.project_asset_schemas import AssignToProjectRequest
from utils.logger import logger


api_image_v1 = Blueprint("api_image_v1", __name__, url_prefix="/api/v1/image")

# Controller instance
image_controller = ImageController()


@api_image_v1.route("/generate", methods=["POST"])
@jwt_required
@validate()
def generate(body: ImageGenerateRequest):
    """Generate image with DALL-E"""
    try:
        response_data, status_code = image_controller.generate_image(
            prompt=body.prompt,
            size=body.size,
            title=body.title,
            user_prompt=body.user_prompt,
            artistic_style=body.artistic_style,
            composition=body.composition,
            lighting=body.lighting,
            color_palette=body.color_palette,
            detail_level=body.detail_level,
        )
        return jsonify(response_data), status_code
    except Exception as e:
        error_response = ErrorResponse(error=str(e))
        return jsonify(error_response.dict()), 500


@api_image_v1.route("/list", methods=["GET"])
@jwt_required
@validate()
def list_images(query: ImageListRequest):
    """Get list of generated images with pagination, search and sorting"""
    try:
        response_data, status_code = image_controller.get_images(
            limit=query.limit, offset=query.offset, search=query.search, sort_by=query.sort, sort_direction=query.order
        )
        return jsonify(response_data), status_code
    except Exception as e:
        error_response = ErrorResponse(error=str(e))
        return jsonify(error_response.dict()), 500


@api_image_v1.route("/list-for-text-overlay", methods=["GET"])
@jwt_required
def list_images_for_text_overlay():
    """Get list of images suitable for text overlay (only images with title, album-cover first)"""
    try:
        response_data, status_code = image_controller.get_images_for_text_overlay()
        return jsonify(response_data), status_code
    except Exception as e:
        error_response = ErrorResponse(error=str(e))
        return jsonify(error_response.dict()), 500


@api_image_v1.route("/<path:filename>")
@jwt_required
def serve_image(filename):
    """Serve stored images from filesystem (backward compatibility)"""
    try:
        logger.debug("Serving image", filename=filename)
        return send_from_directory(IMAGES_DIR, filename)
    except Exception as e:
        logger.error(
            "Error serving image",
            filename=filename,
            error=str(e),
            error_type=type(e).__name__,
            stacktrace=traceback.format_exc(),
        )
        return jsonify({"error": "Image not found"}), 404


@api_image_v1.route("/s3/<string:image_id>", methods=["GET"])
@jwt_required
def serve_s3_image(image_id):
    """Serve S3-stored images via backend proxy (streams from S3)"""
    try:
        from adapters.s3.s3_proxy_service import s3_proxy_service
        from config.settings import S3_IMAGES_BUCKET
        from db.image_service import ImageService

        logger.debug("Serving S3 image", image_id=image_id)

        # Get image from DB
        image = ImageService.get_image_by_id(image_id)
        if not image:
            return jsonify({"error": "Image not found"}), 404

        # Verify it's an S3 image
        if image.storage_backend != "s3" or not image.s3_key:
            return jsonify({"error": "Not an S3 image"}), 400

        # Stream from S3 using generic proxy service
        return s3_proxy_service.serve_resource(bucket=S3_IMAGES_BUCKET, s3_key=image.s3_key, filename=image.filename)

    except Exception as e:
        logger.error(
            "Error serving S3 image",
            image_id=image_id,
            error=str(e),
            error_type=type(e).__name__,
            stacktrace=traceback.format_exc(),
        )
        return jsonify({"error": "Failed to load image from S3"}), 500


@api_image_v1.route("/<string:image_id>", methods=["GET"])
@jwt_required
def get_image(image_id):
    """Get single image by ID"""
    response_data, status_code = image_controller.get_image_by_id(image_id)

    return jsonify(response_data), status_code


@api_image_v1.route("/<string:image_id>", methods=["DELETE"])
@jwt_required
def delete_image(image_id):
    """Delete image by ID"""
    response_data, status_code = image_controller.delete_image(image_id)

    return jsonify(response_data), status_code


@api_image_v1.route("/bulk-delete", methods=["DELETE"])
@jwt_required
def bulk_delete_images():
    """Delete multiple images by IDs"""
    raw_json = request.get_json(silent=True)

    if not raw_json:
        return jsonify({"error": "No JSON provided"}), 400

    image_ids = raw_json.get("ids", [])

    if not isinstance(image_ids, list):
        return jsonify({"error": "ids must be an array"}), 400

    response_data, status_code = image_controller.bulk_delete_images(image_ids)

    return jsonify(response_data), status_code


@api_image_v1.route("/<string:image_id>", methods=["PUT"])
@jwt_required
@validate()
def update_image_metadata(image_id: str, body: ImageUpdateRequest):
    """Update image metadata (title and/or tags)"""
    try:
        response_data, status_code = image_controller.update_image_metadata(image_id, body.title, body.tags)
        return jsonify(response_data), status_code
    except Exception as e:
        error_response = ErrorResponse(error=str(e))
        return jsonify(error_response.dict()), 500


@api_image_v1.route("/id/<string:image_id>/assign-to-project", methods=["POST"])
@jwt_required
@validate()
def assign_to_project(image_id: str, body: AssignToProjectRequest):
    """Assign image to project"""
    try:
        response_data, status_code = image_controller.assign_to_project(
            image_id, str(body.project_id), str(body.folder_id) if body.folder_id else None
        )
        return jsonify(response_data), status_code
    except Exception as e:
        error_response = ErrorResponse(error=str(e))
        return jsonify(error_response.dict()), 500


@api_image_v1.route("/id/<string:image_id>/unassign-from-project/<string:project_id>", methods=["DELETE"])
@jwt_required
def unassign_from_project(image_id: str, project_id: str):
    """Remove image from project (link only, image remains)"""
    try:
        response_data, status_code = image_controller.unassign_from_project(image_id, project_id)
        return jsonify(response_data), status_code
    except Exception as e:
        error_response = ErrorResponse(error=str(e))
        return jsonify(error_response.dict()), 500


@api_image_v1.route("/id/<string:image_id>/projects", methods=["GET"])
@jwt_required
def get_projects_for_image(image_id: str):
    """Get list of projects this image is assigned to"""
    try:
        response_data, status_code = image_controller.get_projects_for_image(image_id)
        return jsonify(response_data), status_code
    except Exception as e:
        error_response = ErrorResponse(error=str(e))
        return jsonify(error_response.dict()), 500


@api_image_v1.route("/add-text-overlay", methods=["POST"])
@jwt_required
def add_text_overlay():
    """Add text overlay to existing image"""
    user_id = get_current_user_id()

    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    raw_json = request.get_json(silent=True)

    if not raw_json:
        return jsonify({"error": "No JSON provided"}), 400

    # Extract parameters (V2 - with separate title/artist controls)
    image_id = raw_json.get("image_id")
    title = raw_json.get("title")
    artist = raw_json.get("artist")
    font_style = raw_json.get("font_style", "bold")

    # V2 parameters
    title_position = raw_json.get("title_position", "center")
    title_font_size = raw_json.get("title_font_size", 0.08)
    title_color = raw_json.get("title_color", "#FFFFFF")
    title_outline_color = raw_json.get("title_outline_color", "#000000")
    artist_position = raw_json.get("artist_position")
    artist_font_size = raw_json.get("artist_font_size", 0.05)
    artist_color = raw_json.get("artist_color")
    artist_outline_color = raw_json.get("artist_outline_color")
    artist_font_style = raw_json.get("artist_font_style")

    # Legacy parameters (fallback for old clients)
    position = raw_json.get("position")
    text_color = raw_json.get("text_color")
    outline_color = raw_json.get("outline_color")

    # Validate required fields
    if not image_id or not title:
        return jsonify({"error": "image_id and title are required"}), 400

    # Call controller
    response_data, status_code = image_controller.add_text_overlay(
        image_id=image_id,
        user_id=str(user_id),
        title=title,
        artist=artist,
        font_style=font_style,
        title_position=title_position,
        title_font_size=title_font_size,
        title_color=title_color,
        title_outline_color=title_outline_color,
        artist_position=artist_position,
        artist_font_size=artist_font_size,
        artist_color=artist_color,
        artist_outline_color=artist_outline_color,
        artist_font_style=artist_font_style,
        position=position,
        text_color=text_color,
        outline_color=outline_color,
    )

    return jsonify(response_data), status_code
