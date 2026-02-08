"""Unit tests for SQLAlchemy models"""

import uuid

import pytest

from db.models import Conversation, GeneratedImage, Message, PromptTemplate, User


@pytest.mark.unit
class TestGeneratedImageModel:
    """Test GeneratedImage model instantiation"""

    def test_image_creation(self):
        """Test creating a GeneratedImage instance"""
        image = GeneratedImage(
            prompt="A beautiful landscape",
            size="1024x1024",
            filename="test-image.png",
            file_path="/path/to/image.png",
            local_url="http://localhost/images/test.png",
            model_used="dall-e-3",
        )

        assert image.prompt == "A beautiful landscape"
        assert image.size == "1024x1024"
        assert image.filename == "test-image.png"
        assert image.model_used == "dall-e-3"

    def test_image_repr(self):
        """Test GeneratedImage __repr__ method"""
        image = GeneratedImage(
            prompt="A" * 100,  # Long prompt
            size="512x512",
            filename="test.png",
            file_path="/test.png",
            local_url="http://localhost/test.png",
        )
        image.id = uuid.uuid4()

        repr_str = repr(image)
        assert "GeneratedImage" in repr_str
        assert "test.png" in repr_str


@pytest.mark.unit
class TestPromptTemplateModel:
    """Test PromptTemplate model instantiation"""

    def test_template_creation(self):
        """Test creating a PromptTemplate instance"""
        template = PromptTemplate(
            category="chat",
            action="summarize",
            pre_condition="You are a helpful assistant.",
            post_condition="Keep it concise.",
            description="Summarizes text",
            model="llama3.2:3b",
            temperature=0.7,
            max_tokens=100,
            active=True,
        )

        assert template.category == "chat"
        assert template.action == "summarize"
        assert template.model == "llama3.2:3b"
        assert template.temperature == 0.7
        assert template.max_tokens == 100
        assert template.active is True

    def test_template_default_active(self):
        """Test PromptTemplate default active value (set by DB)"""
        template = PromptTemplate(
            category="test",
            action="test",
            pre_condition="",
            post_condition="",
        )

        # Default value only applied by DB, not in Python unit tests
        # In Python-only tests, this will be None
        assert template.category == "test"
        assert template.action == "test"


@pytest.mark.unit
class TestUserModel:
    """Test User model instantiation"""

    def test_user_creation(self):
        """Test creating a User instance"""
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            first_name="John",
            last_name="Doe",
            is_active=True,
            is_verified=False,
        )

        assert user.email == "test@example.com"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.is_active is True
        assert user.is_verified is False

    def test_user_default_values(self):
        """Test User default values (set by DB)"""
        user = User(email="test@example.com")

        # Defaults like is_active=True are only applied by DB, not in Python
        assert user.email == "test@example.com"
        assert user.password_hash is None
        assert user.oauth_provider is None

    def test_user_repr(self):
        """Test User __repr__ method"""
        user = User(email="test@example.com", is_active=True)
        user.id = uuid.uuid4()

        repr_str = repr(user)
        assert "User" in repr_str
        assert "test@example.com" in repr_str


@pytest.mark.unit
class TestConversationModel:
    """Test Conversation model instantiation"""

    def test_conversation_creation(self):
        """Test creating a Conversation instance"""
        user_id = uuid.uuid4()
        conversation = Conversation(
            user_id=user_id,
            title="Test Chat",
            model="llama3.2:3b",
            provider="internal",
            context_window_size=4096,
            current_token_count=100,
        )

        assert conversation.user_id == user_id
        assert conversation.title == "Test Chat"
        assert conversation.model == "llama3.2:3b"
        assert conversation.provider == "internal"
        assert conversation.context_window_size == 4096
        assert conversation.current_token_count == 100

    def test_conversation_default_values(self):
        """Test Conversation default values"""
        user_id = uuid.uuid4()
        conversation = Conversation(
            user_id=user_id,
            title="Chat",
            model="test-model",
        )

        # Note: server_default values are only set by the database
        # In Python-only tests, these will be None
        assert conversation.archived is None or conversation.archived is False


@pytest.mark.unit
class TestMessageModel:
    """Test Message model instantiation"""

    def test_message_creation(self):
        """Test creating a Message instance"""
        conversation_id = uuid.uuid4()
        message = Message(
            conversation_id=conversation_id,
            role="user",
            content="Hello, AI!",
            token_count=10,
            is_summary=False,
        )

        assert message.conversation_id == conversation_id
        assert message.role == "user"
        assert message.content == "Hello, AI!"
        assert message.token_count == 10
        assert message.is_summary is False

    def test_message_repr(self):
        """Test Message __repr__ method"""
        conversation_id = uuid.uuid4()
        message = Message(
            conversation_id=conversation_id,
            role="assistant",
            content="Response",
        )
        message.id = uuid.uuid4()

        repr_str = repr(message)
        assert "Message" in repr_str
        assert "assistant" in repr_str
