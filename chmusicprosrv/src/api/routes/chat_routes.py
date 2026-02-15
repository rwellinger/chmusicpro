"""
Chat Generation Routes - Multi-Provider AI Integration with Pydantic validation
"""

from flask import Blueprint, jsonify
from flask_pydantic import validate

from api.auth_middleware import get_current_user_id, jwt_required
from api.controllers.chat_controller import ChatController
from config.ai_config import AI_MODE_EXTERNAL, PROVIDER_OLLAMA, AIConfig
from config.settings import CHAT_DEBUG_LOGGING
from schemas.chat_schemas import ChatErrorResponse, UnifiedChatRequest
from utils.logger import logger


api_chat_v1 = Blueprint("api_chat_v1", __name__, url_prefix="/api/v1/ollama/chat")

# Controller instance
chat_controller = ChatController()


def _resolve_provider_and_model(category: str | None, action: str | None, request_model: str | None):
    """Determine provider and model from template + AI config.

    Priority:
    1. Load template from DB -> use template.provider and template.model
    2. If external-only mode and template says ollama -> override with external config
    3. Fallback (no template): external mode -> external provider, else ollama
    """
    provider = PROVIDER_OLLAMA
    model = request_model

    # Try to load template from DB for provider info
    if category and action:
        try:
            from db.database import SessionLocal
            from db.prompt_template_service import PromptTemplateService

            db = SessionLocal()
            try:
                service = PromptTemplateService()
                template = service.get_template_by_category_action(db, category, action)
                if template:
                    provider = template.provider or PROVIDER_OLLAMA
                    if not model:
                        model = template.model
            finally:
                db.close()
        except Exception as e:
            logger.warning("Failed to load template for provider resolution", error=str(e))

    # External-only mode override: if provider is ollama but mode is external-only
    mode = AIConfig.get_mode()
    if mode == AI_MODE_EXTERNAL and provider == PROVIDER_OLLAMA:
        provider = AIConfig.get_external_provider()
        model = AIConfig.get_external_model()
        logger.info(
            "External-only mode: overriding ollama template",
            new_provider=provider,
            new_model=model,
        )
    elif not category and not action:
        # No template context - use mode to decide
        if mode == AI_MODE_EXTERNAL:
            provider = AIConfig.get_external_provider()
            if not model:
                model = AIConfig.get_external_model()

    return provider, model


@api_chat_v1.route("/generate-unified", methods=["POST"])
@jwt_required
@validate()
def generate_unified(body: UnifiedChatRequest):
    """Generate chat response with unified request structure and template support"""
    try:
        # Resolve provider and model from template + config
        provider, resolved_model = _resolve_provider_and_model(body.category, body.action, body.model)
        model = resolved_model or body.model

        # Validate that required template parameters are provided
        if model is None:
            raise ValueError("Model parameter is required but not provided by template")
        if body.temperature is None:
            raise ValueError("Temperature parameter is required but not provided by template")

        # Conditional logging based on .env setting
        if CHAT_DEBUG_LOGGING:
            input_text_short = body.input_text[:50] + "..." if len(body.input_text) > 50 else body.input_text
            logger.debug(
                "Unified chat request",
                category=body.category,
                action=body.action,
                model=model,
                provider=provider,
                temperature=body.temperature,
                max_tokens=body.max_tokens,
                pre_condition=body.pre_condition,
                input_text=input_text_short,
                post_condition=body.post_condition,
            )
        else:
            logger.info(
                "Chat request",
                category=body.category,
                action=body.action,
                model=model,
                provider=provider,
                input_length=len(body.input_text),
            )

        user_id = get_current_user_id()

        response_data, status_code = chat_controller.generate_chat(
            model=model,
            pre_condition=body.pre_condition,
            prompt=body.input_text,
            post_condition=body.post_condition,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
            user_instructions=body.user_instructions,
            category=body.category,
            action=body.action,
            user_id=str(user_id) if user_id else None,
            provider=provider,
        )
        return jsonify(response_data), status_code
    except Exception as e:
        logger.error(f"Error in generate_unified: {str(e)}")
        error_response = ChatErrorResponse(error=str(e), model=body.model)
        return jsonify(error_response.dict()), 500
