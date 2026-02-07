"""Conversation Routes - AI Chat Conversation Management."""

import uuid

from flask import Blueprint, jsonify, request
from flask_pydantic import validate

from api.auth_middleware import get_current_user_id, jwt_required
from api.controllers.compression_controller import CompressionController
from api.controllers.conversation_controller import ConversationController
from db.database import get_db
from schemas.conversation_schemas import (
    ConversationCreate,
    ConversationUpdate,
    SendMessageRequest,
)
from utils.logger import logger


api_conversation_v1 = Blueprint("api_conversation_v1", __name__, url_prefix="/api/v1/conversations")

# Controller instances
conversation_controller = ConversationController()
compression_controller = CompressionController()


@api_conversation_v1.route("", methods=["GET"])
@jwt_required
def list_conversations():
    """List all conversations for the authenticated user."""
    try:
        user_id = get_current_user_id()
        db = next(get_db())

        # Get pagination params
        skip = request.args.get("skip", default=0, type=int)
        limit = request.args.get("limit", default=20, type=int)
        provider = request.args.get("provider", default=None, type=str)

        # Get archived filter (defaults to None = only non-archived)
        # 'true' = only archived, 'false' = all conversations
        archived_param = request.args.get("archived", default=None, type=str)
        archived = None  # Default: show only non-archived
        if archived_param == "true":
            archived = True  # Show only archived
        elif archived_param == "false":
            archived = False  # Show all conversations (no filter)

        response_data, status_code = conversation_controller.list_conversations(
            db=db, user_id=user_id, skip=skip, limit=limit, provider=provider, archived=archived
        )

        return jsonify(response_data), status_code

    except Exception as e:
        logger.error("Error in list_conversations route", error=str(e))
        return jsonify({"error": f"Failed to list conversations: {e}"}), 500


@api_conversation_v1.route("", methods=["POST"])
@jwt_required
@validate()
def create_conversation(body: ConversationCreate):
    """Create a new conversation."""
    try:
        user_id = get_current_user_id()
        db = next(get_db())

        response_data, status_code = conversation_controller.create_conversation(db=db, user_id=user_id, data=body)

        return jsonify(response_data), status_code

    except Exception as e:
        logger.error("Error in create_conversation route", error=str(e))
        return jsonify({"error": f"Failed to create conversation: {e}"}), 500


@api_conversation_v1.route("/<conversation_id>", methods=["GET"])
@jwt_required
def get_conversation(conversation_id: str):
    """Get a conversation with its messages."""
    try:
        user_id = get_current_user_id()
        db = next(get_db())

        # Parse UUID
        try:
            conv_uuid = uuid.UUID(conversation_id)
        except ValueError:
            return jsonify({"error": "Invalid conversation ID format"}), 400

        response_data, status_code = conversation_controller.get_conversation(
            db=db, conversation_id=conv_uuid, user_id=user_id
        )

        return jsonify(response_data), status_code

    except Exception as e:
        logger.error("Error in get_conversation route", error=str(e))
        return jsonify({"error": f"Failed to get conversation: {e}"}), 500


@api_conversation_v1.route("/<conversation_id>", methods=["PATCH"])
@jwt_required
@validate()
def update_conversation(conversation_id: str, body: ConversationUpdate):
    """Update a conversation (title only)."""
    try:
        user_id = get_current_user_id()
        db = next(get_db())

        # Parse UUID
        try:
            conv_uuid = uuid.UUID(conversation_id)
        except ValueError:
            return jsonify({"error": "Invalid conversation ID format"}), 400

        response_data, status_code = conversation_controller.update_conversation(
            db=db, conversation_id=conv_uuid, user_id=user_id, data=body
        )

        return jsonify(response_data), status_code

    except Exception as e:
        logger.error("Error in update_conversation route", error=str(e))
        return jsonify({"error": f"Failed to update conversation: {e}"}), 500


@api_conversation_v1.route("/<conversation_id>", methods=["DELETE"])
@jwt_required
def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    try:
        user_id = get_current_user_id()
        db = next(get_db())

        # Parse UUID
        try:
            conv_uuid = uuid.UUID(conversation_id)
        except ValueError:
            return jsonify({"error": "Invalid conversation ID format"}), 400

        response_data, status_code = conversation_controller.delete_conversation(
            db=db, conversation_id=conv_uuid, user_id=user_id
        )

        return jsonify(response_data), status_code

    except Exception as e:
        logger.error("Error in delete_conversation route", error=str(e))
        return jsonify({"error": f"Failed to delete conversation: {e}"}), 500


@api_conversation_v1.route("/<conversation_id>/messages", methods=["POST"])
@jwt_required
@validate()
def send_message(conversation_id: str, body: SendMessageRequest):
    """Send a message in a conversation and get AI response."""
    try:
        user_id = get_current_user_id()
        db = next(get_db())

        # Parse UUID
        try:
            conv_uuid = uuid.UUID(conversation_id)
        except ValueError:
            return jsonify({"error": "Invalid conversation ID format"}), 400

        response_data, status_code = conversation_controller.send_message(
            db=db,
            conversation_id=conv_uuid,
            user_id=user_id,
            content=body.content,
        )

        return jsonify(response_data), status_code

    except Exception as e:
        logger.error("Error in send_message route", error=str(e))
        return jsonify({"error": f"Failed to send message: {e}"}), 500


@api_conversation_v1.route("/<conversation_id>/compress", methods=["POST"])
@jwt_required
def compress_conversation(conversation_id: str):
    """Compress conversation by archiving old messages and creating AI summary."""
    try:
        user_id = get_current_user_id()
        db = next(get_db())

        # Parse UUID
        try:
            conv_uuid = uuid.UUID(conversation_id)
        except ValueError:
            return jsonify({"error": "Invalid conversation ID format"}), 400

        # Get optional keep_recent parameter (default=2, min=1, max=20)
        keep_recent = request.args.get("keep_recent", default=2, type=int)
        # Validate parameter range
        if keep_recent < 1 or keep_recent > 20:
            return jsonify({"error": "keep_recent must be between 1 and 20"}), 400

        response_data, status_code = compression_controller.compress_conversation(
            db=db, conversation_id=conv_uuid, user_id=user_id, keep_recent=keep_recent
        )

        return jsonify(response_data), status_code

    except Exception as e:
        logger.error("Error in compress_conversation route", error=str(e))
        return jsonify({"error": f"Failed to compress conversation: {e}"}), 500


@api_conversation_v1.route("/<conversation_id>/restore-archive", methods=["POST"])
@jwt_required
def restore_archive(conversation_id: str):
    """Restore archived messages (replace summary with original messages)."""
    try:
        user_id = get_current_user_id()
        db = next(get_db())

        # Parse UUID
        try:
            conv_uuid = uuid.UUID(conversation_id)
        except ValueError:
            return jsonify({"error": "Invalid conversation ID format"}), 400

        response_data, status_code = compression_controller.restore_archive(
            db=db, conversation_id=conv_uuid, user_id=user_id
        )

        return jsonify(response_data), status_code

    except Exception as e:
        logger.error("Error in restore_archive route", error=str(e))
        return jsonify({"error": f"Failed to restore archive: {e}"}), 500


@api_conversation_v1.route("/<conversation_id>/export-full", methods=["GET"])
@jwt_required
def get_conversation_for_export(conversation_id: str):
    """Get conversation with all messages including archived (for export)."""
    try:
        user_id = get_current_user_id()
        db = next(get_db())

        # Parse UUID
        try:
            conv_uuid = uuid.UUID(conversation_id)
        except ValueError:
            return jsonify({"error": "Invalid conversation ID format"}), 400

        response_data, status_code = conversation_controller.get_conversation_with_archive(
            db=db, conversation_id=conv_uuid, user_id=user_id
        )

        return jsonify(response_data), status_code

    except Exception as e:
        logger.error("Error in get_conversation_for_export route", error=str(e))
        return jsonify({"error": f"Failed to get conversation for export: {e}"}), 500
