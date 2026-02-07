"""Tests for PromptTemplateProcessor - Business logic unit tests"""

from unittest.mock import Mock

from business.prompt_template_processor import PromptTemplateProcessor


class TestBuildPrompt:
    """Test build_prompt() - prompt construction"""

    def test_build_prompt_with_all_parts(self):
        """Build prompt with pre_condition, user_input, and post_condition"""
        template = Mock(
            pre_condition="You are a lyric writer.",
            post_condition="Format as verse-chorus.",
            category="lyrics",
            action="generate",
            id=1,
        )

        prompt = PromptTemplateProcessor.build_prompt(template, "Write about love")

        assert "You are a lyric writer." in prompt
        assert "Write about love" in prompt
        assert "Format as verse-chorus." in prompt
        # Parts should be separated by double newlines
        assert "\n\n" in prompt

    def test_build_prompt_minimal(self):
        """Build prompt with only user_input (no pre/post conditions)"""
        template = Mock(pre_condition="", post_condition="", category="test", action="test", id=1)

        prompt = PromptTemplateProcessor.build_prompt(template, "Just this text")

        assert prompt == "Just this text"

    def test_build_prompt_no_pre_condition(self):
        """Build prompt without pre_condition"""
        template = Mock(pre_condition="", post_condition="Output JSON.", category="test", action="test", id=1)

        prompt = PromptTemplateProcessor.build_prompt(template, "Generate data")

        assert "Generate data" in prompt
        assert "Output JSON." in prompt
        assert prompt.startswith("Generate data")  # No leading newlines

    def test_build_prompt_no_post_condition(self):
        """Build prompt without post_condition"""
        template = Mock(pre_condition="You are helpful.", post_condition="", category="test", action="test", id=1)

        prompt = PromptTemplateProcessor.build_prompt(template, "Help me")

        assert "You are helpful." in prompt
        assert "Help me" in prompt
        assert prompt.endswith("Help me")  # No trailing newlines

    def test_build_prompt_none_values(self):
        """Handle None values for pre/post conditions"""
        template = Mock(pre_condition=None, post_condition=None, category="test", action="test", id=1)

        prompt = PromptTemplateProcessor.build_prompt(template, "User input")

        assert prompt == "User input"

    def test_build_prompt_whitespace_handling(self):
        """Whitespace in pre/post conditions is stripped"""
        template = Mock(
            pre_condition="  Instruction  ", post_condition="  Format  ", category="test", action="test", id=1
        )

        prompt = PromptTemplateProcessor.build_prompt(template, "  Input  ")

        assert prompt == "Instruction\n\nInput\n\nFormat"

    def test_build_prompt_empty_user_input(self):
        """Handle empty user input"""
        template = Mock(pre_condition="Pre", post_condition="Post", category="test", action="test", id=1)

        prompt = PromptTemplateProcessor.build_prompt(template, "")

        # Empty user_input should be skipped
        assert prompt == "Pre\n\nPost"

    def test_build_prompt_multiline_content(self):
        """Handle multiline content in all parts"""
        template = Mock(
            pre_condition="Line 1\nLine 2", post_condition="End 1\nEnd 2", category="test", action="test", id=1
        )

        prompt = PromptTemplateProcessor.build_prompt(template, "Middle 1\nMiddle 2")

        assert "Line 1\nLine 2" in prompt
        assert "Middle 1\nMiddle 2" in prompt
        assert "End 1\nEnd 2" in prompt


class TestProcessTemplate:
    """Test process_template() - complete processing workflow"""

    def test_process_template_complete(self):
        """Process template with all parameters configured"""
        template = Mock(
            model="llama3.2",
            temperature=0.8,
            max_tokens=1000,
            pre_condition="You are helpful.",
            post_condition="Be concise.",
            category="test",
            action="action",
            id=1,
        )

        result = PromptTemplateProcessor.process_template(template, "Help me")

        assert result["prompt"] == "You are helpful.\n\nHelp me\n\nBe concise."
        assert result["model"] == "llama3.2"
        assert result["temperature"] == 0.8
        assert result["max_tokens"] == 1000

    def test_process_template_returns_all_fields(self):
        """Verify all required fields are in result"""
        template = Mock(
            model="test-model",
            temperature=0.5,
            max_tokens=500,
            pre_condition="",
            post_condition="",
            category="test",
            action="test",
            id=1,
        )

        result = PromptTemplateProcessor.process_template(template, "test")

        required_fields = ["prompt", "model", "temperature"]
        for field in required_fields:
            assert field in result

    def test_process_template_different_categories(self):
        """Process templates from different categories"""
        categories = [("lyrics", "generate"), ("image", "enhance"), ("music", "translate"), ("title", "generate")]

        for category, action in categories:
            template = Mock(
                model="test",
                temperature=0.7,
                max_tokens=100,
                pre_condition="Pre",
                post_condition="Post",
                category=category,
                action=action,
                id=1,
            )

            result = PromptTemplateProcessor.process_template(template, "Input")

            assert result["prompt"] == "Pre\n\nInput\n\nPost"
