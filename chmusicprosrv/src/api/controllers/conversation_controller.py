"""Conversation Controller - Handles business logic for AI chat conversations."""

import traceback
import uuid
from datetime import datetime
from typing import Any

import requests
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.controllers.claude_chat_controller import ClaudeAPIError as ClaudeError
from api.controllers.claude_chat_controller import ClaudeChatController
from api.controllers.openai_chat_controller import OpenAIAPIError as OpenAIError
from api.controllers.openai_chat_controller import OpenAIChatController
from config.model_context_windows import (
    get_context_window_size,
    get_external_provider_context_window,
)
from config.settings import CLAUDE_MAX_TOKENS, OLLAMA_TIMEOUT, OLLAMA_URL, OPENAI_MAX_TOKENS
from db.models import Conversation, Message, MessageArchive
from schemas.conversation_schemas import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
    MessageResponse,
)
from utils.logger import logger


class ConversationController:
    """Controller for managing AI chat conversations."""

    def list_conversations(
        self,
        db: Session,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        provider: str = None,
        archived: bool = None,
    ) -> tuple[dict[str, Any], int]:
        """
        List all conversations for a user.

        Args:
            db: Database session
            user_id: User UUID
            skip: Pagination offset
            limit: Pagination limit
            provider: Optional provider filter ('internal' or 'external')
            archived: Optional archived filter (None = only non-archived, True = only archived, False = all)

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Get conversations with message count
            query = (
                db.query(Conversation, func.count(Message.id).label("message_count"))
                .outerjoin(Message, Conversation.id == Message.conversation_id)
                .filter(Conversation.user_id == user_id)
            )

            # Filter by provider if specified
            if provider:
                query = query.filter(Conversation.provider == provider)

            # Filter by archived status
            # None (default) = only non-archived conversations
            # True = only archived conversations
            # False = all conversations (no filter)
            if archived is None:
                # Default: show only non-archived conversations
                query = query.filter(Conversation.archived == False)  # noqa: E712
            elif archived is True:
                # Show only archived conversations
                query = query.filter(Conversation.archived == True)  # noqa: E712
            # If archived is False, no filter is applied (show all)

            query = query.group_by(Conversation.id).order_by(Conversation.updated_at.desc())

            total = query.count()
            conversations_with_count = query.offset(skip).limit(limit).all()

            # Build response
            conversations = []
            for conv, msg_count in conversations_with_count:
                conv_dict = ConversationResponse.from_orm(conv).dict()
                conv_dict["message_count"] = msg_count
                conversations.append(conv_dict)

            return {
                "conversations": conversations,
                "total": total,
                "skip": skip,
                "limit": limit,
            }, 200

        except Exception as e:
            logger.error(
                "Error listing conversations",
                error_type=type(e).__name__,
                error=str(e),
                stacktrace=traceback.format_exc(),
            )
            return {"error": f"Failed to list conversations: {e}"}, 500

    def get_conversation(
        self, db: Session, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> tuple[dict[str, Any], int]:
        """
        Get conversation with messages.

        Args:
            db: Database session
            conversation_id: Conversation UUID
            user_id: User UUID

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Get conversation
            conversation = (
                db.query(Conversation)
                .filter(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user_id,
                )
                .first()
            )

            if not conversation:
                return {"error": "Conversation not found"}, 404

            # Get messages
            messages = (
                db.query(Message)
                .filter(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.asc())
                .all()
            )

            # Check if conversation has archived messages
            has_archived = (
                db.query(MessageArchive).filter(MessageArchive.conversation_id == conversation_id).first() is not None
            )

            # Build conversation response
            conv_response = ConversationResponse.from_orm(conversation).dict()
            conv_response["has_archived_messages"] = has_archived

            return {
                "conversation": conv_response,
                "messages": [MessageResponse.from_orm(msg).dict() for msg in messages],
            }, 200

        except Exception as e:
            logger.error(
                "Error getting conversation",
                conversation_id=str(conversation_id),
                error_type=type(e).__name__,
                error=str(e),
                stacktrace=traceback.format_exc(),
            )
            return {"error": f"Failed to get conversation: {e}"}, 500

    def get_conversation_with_archive(
        self, db: Session, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> tuple[dict[str, Any], int]:
        """
        Get conversation with messages including archived messages (for export).

        This method merges active messages with archived messages,
        replacing summary messages with their original archived content.

        Args:
            db: Database session
            conversation_id: Conversation UUID
            user_id: User UUID

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Get conversation
            conversation = (
                db.query(Conversation)
                .filter(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user_id,
                )
                .first()
            )

            if not conversation:
                return {"error": "Conversation not found"}, 404

            # Get active messages
            active_messages = (
                db.query(Message)
                .filter(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.asc())
                .all()
            )

            # Get archived messages
            archived_messages = (
                db.query(MessageArchive)
                .filter(MessageArchive.conversation_id == conversation_id)
                .order_by(MessageArchive.original_created_at.asc())
                .all()
            )

            # Build complete message list
            all_messages = []

            for msg in active_messages:
                if msg.is_summary and msg.id:
                    # Replace summary with archived messages
                    related_archived = [a for a in archived_messages if a.summary_message_id == msg.id]
                    # Add archived messages as dict (with original timestamps)
                    for archive in related_archived:
                        all_messages.append(
                            {
                                "id": str(archive.original_message_id),
                                "conversation_id": str(archive.conversation_id),
                                "role": archive.role,
                                "content": archive.content,
                                "token_count": archive.token_count,
                                "created_at": archive.original_created_at.isoformat()
                                if archive.original_created_at
                                else None,
                                "is_archived": True,
                            }
                        )
                else:
                    # Add regular message (convert created_at to ISO string for consistent sorting)
                    msg_dict = MessageResponse.from_orm(msg).dict()
                    if msg.created_at:
                        msg_dict["created_at"] = msg.created_at.isoformat()
                    all_messages.append(msg_dict)

            # Sort by created_at (all are ISO strings now)
            all_messages.sort(key=lambda x: x.get("created_at") or "")

            return {
                "conversation": ConversationResponse.from_orm(conversation).dict(),
                "messages": all_messages,
                "has_archived": len(archived_messages) > 0,
            }, 200

        except Exception as e:
            logger.error(
                "Error getting conversation with archive",
                conversation_id=str(conversation_id),
                error_type=type(e).__name__,
                error=str(e),
                stacktrace=traceback.format_exc(),
            )
            return {"error": f"Failed to get conversation with archive: {e}"}, 500

    def create_conversation(
        self, db: Session, user_id: uuid.UUID, data: ConversationCreate
    ) -> tuple[dict[str, Any], int]:
        """
        Create a new conversation.

        Args:
            db: Database session
            user_id: User UUID
            data: Conversation creation data

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Validate external_provider field
            provider = data.provider or "internal"

            if provider == "external" and not data.external_provider:
                return {"error": "external_provider is required when provider='external'"}, 400

            if provider == "internal" and data.external_provider:
                return {"error": "external_provider should not be set when provider='internal'"}, 400

            # Get context window size for the model (provider-aware)
            if provider == "external" and data.external_provider:
                # External providers (Claude, OpenAI, etc.)
                context_window_size = get_external_provider_context_window(data.external_provider, data.model)
            else:
                # Internal (Ollama) models
                context_window_size = get_context_window_size(data.model)

            # Create conversation
            conversation = Conversation(
                id=uuid.uuid4(),
                user_id=user_id,
                title=data.title,
                model=data.model,
                provider=provider,
                external_provider=data.external_provider,
                system_context=data.system_context,
                context_window_size=context_window_size,
                current_token_count=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            db.add(conversation)

            # Add system context as first message if provided
            if data.system_context:
                system_message = Message(
                    id=uuid.uuid4(),
                    conversation_id=conversation.id,
                    role="system",
                    content=data.system_context,
                    token_count=len(data.system_context.split()),  # Rough approximation
                    created_at=datetime.utcnow(),
                )
                db.add(system_message)

            db.commit()
            db.refresh(conversation)

            logger.info(
                "Conversation created",
                conversation_id=str(conversation.id),
                user_id=str(user_id),
            )

            return ConversationResponse.from_orm(conversation).dict(), 201

        except Exception as e:
            db.rollback()
            error_details = f"{type(e).__name__}: {str(e)}"
            stack = traceback.format_exc()
            logger.error(f"Error creating conversation - {error_details}\nStacktrace:\n{stack}")
            return {"error": f"Failed to create conversation: {e}"}, 500

    def update_conversation(
        self, db: Session, conversation_id: uuid.UUID, user_id: uuid.UUID, data: ConversationUpdate
    ) -> tuple[dict[str, Any], int]:
        """
        Update a conversation (title only).

        Args:
            db: Database session
            conversation_id: Conversation UUID
            user_id: User UUID
            data: Update data

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            conversation = (
                db.query(Conversation)
                .filter(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user_id,
                )
                .first()
            )

            if not conversation:
                return {"error": "Conversation not found"}, 404

            # Update allowed fields
            if data.title is not None:
                conversation.title = data.title
            if data.archived is not None:
                conversation.archived = data.archived

            conversation.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(conversation)

            logger.info(
                "Conversation updated",
                conversation_id=str(conversation_id),
                user_id=str(user_id),
            )

            return ConversationResponse.from_orm(conversation).dict(), 200

        except Exception as e:
            db.rollback()
            logger.error(
                "Error updating conversation",
                conversation_id=str(conversation_id),
                error_type=type(e).__name__,
                error=str(e),
                stacktrace=traceback.format_exc(),
            )
            return {"error": f"Failed to update conversation: {e}"}, 500

    def delete_conversation(
        self, db: Session, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> tuple[dict[str, Any], int]:
        """
        Delete a conversation.

        Args:
            db: Database session
            conversation_id: Conversation UUID
            user_id: User UUID

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            conversation = (
                db.query(Conversation)
                .filter(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user_id,
                )
                .first()
            )

            if not conversation:
                return {"error": "Conversation not found"}, 404

            # Delete archived messages first (foreign key constraint)
            archived_count = db.query(MessageArchive).filter(MessageArchive.conversation_id == conversation_id).delete()

            if archived_count > 0:
                logger.debug(
                    "Deleted archived messages", conversation_id=str(conversation_id), archived_count=archived_count
                )

            # Now delete conversation (cascade will delete regular messages)
            db.delete(conversation)
            db.commit()

            logger.info(
                "Conversation deleted",
                conversation_id=str(conversation_id),
                user_id=str(user_id),
            )

            return {"message": "Conversation deleted successfully"}, 200

        except Exception as e:
            db.rollback()
            logger.error(
                "Error deleting conversation",
                conversation_id=str(conversation_id),
                error_type=type(e).__name__,
                error=str(e),
                stacktrace=traceback.format_exc(),
            )
            return {"error": f"Failed to delete conversation: {e}"}, 500

    def send_message(
        self, db: Session, conversation_id: uuid.UUID, user_id: uuid.UUID, content: str
    ) -> tuple[dict[str, Any], int]:
        """
        Send a message and get AI response.

        Args:
            db: Database session
            conversation_id: Conversation UUID
            user_id: User UUID
            content: Message content

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Get conversation
            conversation = (
                db.query(Conversation)
                .filter(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user_id,
                )
                .first()
            )

            if not conversation:
                return {"error": "Conversation not found"}, 404

            # Create user message
            user_message = Message(
                id=uuid.uuid4(),
                conversation_id=conversation_id,
                role="user",
                content=content,
                created_at=datetime.utcnow(),
            )
            db.add(user_message)
            db.flush()  # Get user_message.id

            # Get conversation history for context
            messages = (
                db.query(Message)
                .filter(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.asc())
                .all()
            )

            # Build messages for chat API
            chat_messages = []
            for msg in messages:
                chat_messages.append({"role": msg.role, "content": msg.content})

            # Route to appropriate provider
            try:
                if conversation.provider == "external":
                    # Route to external provider based on external_provider field
                    if not conversation.external_provider:
                        db.rollback()
                        logger.error(
                            "External conversation without external_provider field",
                            conversation_id=str(conversation_id),
                        )
                        return {
                            "error": "Invalid conversation: external provider requires external_provider field"
                        }, 500

                    if conversation.external_provider == "claude":
                        # Enhance system context with model information for Claude
                        enhanced_messages = self._enhance_claude_system_context(chat_messages, conversation.model)

                        # Call Claude Chat API
                        assistant_content, prompt_eval_count, eval_count = self._call_claude_chat_api(
                            conversation.model, enhanced_messages
                        )
                    elif conversation.external_provider == "openai":
                        # Call OpenAI Chat API
                        assistant_content, prompt_eval_count, eval_count = self._call_openai_chat_api(
                            conversation.model, chat_messages
                        )
                    else:
                        db.rollback()
                        logger.error(
                            "Unknown external_provider",
                            external_provider=conversation.external_provider,
                            conversation_id=str(conversation_id),
                        )
                        return {"error": f"Unknown external_provider: {conversation.external_provider}"}, 500
                else:
                    # Call Ollama chat API (default/internal)
                    assistant_content, prompt_eval_count, eval_count = self._call_ollama_chat_api(
                        conversation.model, chat_messages
                    )
            except (OllamaAPIError, OpenAIError, ClaudeError) as e:
                db.rollback()
                logger.error(
                    "Chat API Error", error=str(e), provider=conversation.provider, stacktrace=traceback.format_exc()
                )
                return {"error": f"Chat API Error: {e}"}, 500

            # Calculate user message token count (part of prompt_eval_count)
            # Note: prompt_eval_count includes system context + all previous messages + new user message
            # For simplicity, we use eval_count for assistant and store prompt_eval_count
            user_message.token_count = len(content.split())  # Rough approximation

            # Create assistant message
            assistant_message = Message(
                id=uuid.uuid4(),
                conversation_id=conversation_id,
                role="assistant",
                content=assistant_content,
                token_count=eval_count,
                created_at=datetime.utcnow(),
            )
            db.add(assistant_message)

            # Update conversation token count
            conversation.current_token_count = prompt_eval_count + eval_count

            # Update conversation timestamp
            conversation.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(user_message)
            db.refresh(assistant_message)

            logger.info(
                "Message sent and response received",
                conversation_id=str(conversation_id),
            )

            return {
                "user_message": MessageResponse.from_orm(user_message).dict(),
                "assistant_message": MessageResponse.from_orm(assistant_message).dict(),
                "conversation": ConversationResponse.from_orm(conversation).dict(),
            }, 200

        except Exception as e:
            db.rollback()
            logger.error(
                "Error sending message",
                conversation_id=str(conversation_id),
                error_type=type(e).__name__,
                error=str(e),
                stacktrace=traceback.format_exc(),
            )
            return {"error": f"Failed to send message: {e}"}, 500

    def _call_ollama_chat_api(self, model: str, messages: list[dict[str, str]]) -> tuple[str, int, int]:
        """
        Call Ollama chat API.

        Args:
            model: Model name
            messages: List of messages with role and content

        Returns:
            Tuple of (assistant_content, prompt_eval_count, eval_count)

        Raises:
            OllamaAPIError: If API call fails
        """
        api_url = f"{OLLAMA_URL}/api/chat"
        logger.debug("Calling Ollama chat API", api_url=api_url, model=model)

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
        }

        try:
            resp = requests.post(
                api_url,
                json=payload,
                timeout=OLLAMA_TIMEOUT,
            )
            resp.raise_for_status()

            resp_json = resp.json()
            logger.debug("Ollama chat API response received")

            # Extract assistant message
            if "message" in resp_json and "content" in resp_json["message"]:
                content = resp_json["message"]["content"]
                prompt_eval_count = resp_json.get("prompt_eval_count", 0)
                eval_count = resp_json.get("eval_count", 0)

                logger.debug("Token counts extracted", prompt_tokens=prompt_eval_count, response_tokens=eval_count)

                return content, prompt_eval_count, eval_count
            else:
                raise OllamaAPIError("Invalid API response format")

        except requests.exceptions.RequestException as e:
            logger.error("Ollama API Network Error", error=str(e))
            raise OllamaAPIError(f"Network Error: {e}")
        except Exception as e:
            logger.error(
                "Unexpected Ollama API error",
                error_type=type(e).__name__,
                error=str(e),
                stacktrace=traceback.format_exc(),
            )
            raise OllamaAPIError(f"Unexpected Error: {e}")

    def _call_openai_chat_api(self, model: str, messages: list[dict[str, str]]) -> tuple[str, int, int]:
        """
        Call OpenAI chat API.

        Args:
            model: Model name
            messages: List of messages with role and content

        Returns:
            Tuple of (assistant_content, prompt_tokens, completion_tokens)

        Raises:
            OpenAIError: If API call fails
        """
        openai_controller = OpenAIChatController()
        logger.debug("Calling OpenAI chat API", model=model)

        try:
            content, prompt_tokens, completion_tokens = openai_controller.send_chat_message(
                model=model, messages=messages, max_tokens=OPENAI_MAX_TOKENS
            )

            logger.debug("Token counts extracted", prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)

            return content, prompt_tokens, completion_tokens

        except OpenAIError as e:
            logger.error("OpenAI API Error", error=str(e), stacktrace=traceback.format_exc())
            raise

    def _call_claude_chat_api(self, model: str, messages: list[dict[str, str]]) -> tuple[str, int, int]:
        """
        Call Claude chat API.

        Args:
            model: Model name
            messages: List of messages with role and content

        Returns:
            Tuple of (assistant_content, input_tokens, output_tokens)

        Raises:
            ClaudeError: If API call fails
        """
        claude_controller = ClaudeChatController()
        logger.debug("Calling Claude chat API", model=model)

        try:
            content, input_tokens, output_tokens = claude_controller.send_chat_message(
                model=model, messages=messages, max_tokens=CLAUDE_MAX_TOKENS
            )

            logger.debug("Token counts extracted", input_tokens=input_tokens, output_tokens=output_tokens)

            # Claude uses input_tokens/output_tokens, we map to prompt_tokens/completion_tokens
            return content, input_tokens, output_tokens

        except ClaudeError as e:
            logger.error("Claude API Error", error=str(e), stacktrace=traceback.format_exc())
            raise

    def _enhance_claude_system_context(self, messages: list[dict[str, str]], model: str) -> list[dict[str, str]]:
        """
        Enhance system context for Claude with model identification.

        Claude models don't automatically know which version they are.
        This method adds model information to the system context.

        Args:
            messages: List of messages with role and content
            model: Model name (e.g., "claude-sonnet-4-5-20250929")

        Returns:
            Enhanced messages list with updated system context
        """
        # Model version mapping
        model_info = {
            "claude-sonnet-4-5-20250929": "Claude Sonnet 4.5",
            "claude-opus-4-5-20251101": "Claude Opus 4.5",
            "claude-haiku-4-5-20250929": "Claude Haiku 4.5",
        }

        # Get friendly model name
        model_version = model_info.get(model, model)

        # Model info text to prepend
        model_context = f"You are {model_version}. The exact model ID is {model}."

        # Find existing system message or create new one
        enhanced = []
        system_found = False

        for msg in messages:
            if msg.get("role") == "system":
                # Enhance existing system context
                existing_content = msg.get("content", "")
                enhanced.append(
                    {
                        "role": "system",
                        "content": f"{model_context}\n\n{existing_content}" if existing_content else model_context,
                    }
                )
                system_found = True
            else:
                enhanced.append(msg)

        # If no system message exists, prepend one
        if not system_found:
            enhanced.insert(0, {"role": "system", "content": model_context})

        return enhanced


class OllamaAPIError(Exception):
    """Custom exception for Ollama API errors."""

    pass
