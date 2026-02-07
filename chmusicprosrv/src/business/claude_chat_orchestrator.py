"""Claude Chat Orchestrator - Coordinates Claude Messages API operations (NOT testable, orchestration only)."""

from typing import Any

from adapters.claude.api_client import ClaudeAPIClient, ClaudeAPIError
from business.claude_chat_transformer import (
    build_messages_payload,
    filter_models_by_whitelist,
    get_available_models,
    parse_configured_claude_models,
    parse_messages_response,
    transform_api_models_to_frontend,
)
from config.settings import CHAT_DEBUG_LOGGING, CLAUDE_CHAT_MODELS
from utils.logger import logger


class ClaudeChatOrchestrator:
    """Orchestrator for Claude Messages API integration (coordinates services, NO business logic)."""

    def __init__(self):
        self.api_client = ClaudeAPIClient()

    def send_chat_message(
        self, model: str, messages: list[dict[str, str]], max_tokens: int, temperature: float = 0.7
    ) -> tuple[str, int, int]:
        """
        Send chat message to Claude Messages API (orchestrates transformer + API client).

        Args:
            model: Claude model name (e.g., "claude-sonnet-4-5-20250929")
            messages: List of messages with role and content
            max_tokens: Maximum tokens to generate (REQUIRED by Claude)
            temperature: Sampling temperature (0.0-1.0)

        Returns:
            Tuple of (assistant_content, input_tokens, output_tokens)

        Raises:
            ClaudeAPIError: If API call fails
        """
        # Build payload using transformer
        payload = build_messages_payload(model, messages, max_tokens, temperature)

        # Call API client
        resp_json = self.api_client.messages_create(payload)

        # Parse response using transformer
        content, input_tokens, output_tokens = parse_messages_response(resp_json)

        if CHAT_DEBUG_LOGGING:
            logger.debug(
                "Token counts extracted",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                content_length=len(content),
            )

        return content, input_tokens, output_tokens

    def get_available_models(self) -> list[dict[str, Any]]:
        """
        Get available Claude Chat models from Anthropic API.

        Orchestrates: API client + Transformer
        - CLAUDE_CHAT_MODELS empty: Fetch all models from API (dynamic)
        - CLAUDE_CHAT_MODELS set: Fetch from API, then filter by whitelist (hybrid)

        Fallback Strategy:
        - On API failure: Return hardcoded fallback list
        - Log error but don't fail the request

        Returns:
            List of model dictionaries with name and context_window

        Notes:
            - Always calls Anthropic API (simple approach per user decision)
            - Applies whitelist filter if CLAUDE_CHAT_MODELS is set
            - Falls back to static list on API errors
        """
        try:
            # Parse whitelist from configuration
            whitelist = parse_configured_claude_models(CLAUDE_CHAT_MODELS)

            # Always call API (simple solution - per user decision)
            logger.info("Fetching Claude models from Anthropic API", has_whitelist=bool(whitelist))

            # Call API client
            api_response = self.api_client.get_models()
            api_models = api_response.get("data", [])

            # Transform API models to frontend format
            models = transform_api_models_to_frontend(api_models)

            # Apply whitelist filter if configured
            if whitelist:
                models = filter_models_by_whitelist(models, whitelist)
                logger.info(
                    "Claude models fetched and filtered by whitelist",
                    total_from_api=len(api_models),
                    after_filtering=len(models),
                )
            else:
                logger.info(
                    "Claude models fetched (no whitelist)",
                    model_count=len(models),
                )

            return models

        except ClaudeAPIError as e:
            # Fallback to static list on API error
            logger.warning(
                "Claude API error, falling back to static model list",
                error=str(e),
                error_type=type(e).__name__,
            )

            # Return fallback hardcoded list
            fallback_models = get_available_models(CLAUDE_CHAT_MODELS)

            logger.info(
                "Using fallback Claude model list",
                model_count=len(fallback_models),
            )

            return fallback_models

        except Exception as e:
            # Unexpected error - also fallback to static list
            logger.error(
                "Unexpected error in get_available_models, falling back to static list",
                error=str(e),
                error_type=type(e).__name__,
            )

            fallback_models = get_available_models(CLAUDE_CHAT_MODELS)
            return fallback_models
