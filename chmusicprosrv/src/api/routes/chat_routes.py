"""
Chat Generation Routes - Ollama Integration with Pydantic validation
"""

import logging

from flask import Blueprint, jsonify
from flask_pydantic import validate

from api.auth_middleware import jwt_required
from api.controllers.chat_controller import ChatController
from config.settings import CHAT_DEBUG_LOGGING
from schemas.chat_schemas import ChatErrorResponse, UnifiedChatRequest
from utils.logger import logger


api_chat_v1 = Blueprint("api_chat_v1", __name__, url_prefix="/api/v1/ollama/chat")

# Controller instance
chat_controller = ChatController()


@api_chat_v1.route("/generate-unified", methods=["POST"])
@jwt_required
@validate()
def generate_unified(body: UnifiedChatRequest):
    """Generate chat response with unified request structure and template support"""
    try:
        # Validate that required template parameters are provided
        # Note: max_tokens is optional (None/0 means no limit, let model decide)
        if body.model is None:
            raise ValueError("Model parameter is required but not provided by template")
        if body.temperature is None:
            raise ValueError("Temperature parameter is required but not provided by template")

        # Conditional logging based on .env setting
        if CHAT_DEBUG_LOGGING:
            input_text_short = body.input_text[:50] + "..." if len(body.input_text) > 50 else body.input_text
            structured_prompt = (
                f"[INSTRUCTION] {body.pre_condition} [USER] {body.input_text} [FORMAT] {body.post_condition}"
            )

            logger.debug(
                "Unified chat request",
                category=body.category,
                action=body.action,
                model=body.model,
                temperature=body.temperature,
                max_tokens=body.max_tokens,
                pre_condition=body.pre_condition,
                input_text=input_text_short,
                post_condition=body.post_condition,
                final_prompt=structured_prompt,
            )
        else:
            # Minimal logging
            logger.info(
                "Chat request",
                category=body.category,
                action=body.action,
                model=body.model,
                input_length=len(body.input_text),
            )

        response_data, status_code = chat_controller.generate_chat(
            model=body.model,
            pre_condition=body.pre_condition,
            prompt=body.input_text,
            post_condition=body.post_condition,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
            user_instructions=body.user_instructions,
            category=body.category,
            action=body.action,
        )
        return jsonify(response_data), status_code
    except Exception as e:
        logging.error(f"Error in generate_unified: {str(e)}")
        error_response = ChatErrorResponse(error=str(e), model=body.model)
        return jsonify(error_response.dict()), 500
