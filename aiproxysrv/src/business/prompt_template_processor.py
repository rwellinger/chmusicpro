"""Prompt Template Processor - Pure business logic for template processing

This module contains core business logic for processing prompt templates.
All functions are pure (no DB, no file system) and 100% unit-testable.

Architecture:
- Direct parameter access from templates (NO fallbacks!)
- Pure functions only (transformations, string manipulation)
- No database queries (Repository layer handles that)
- No HTTP calls (Controller layer handles that)
"""

from typing import TYPE_CHECKING, Any

from utils.logger import logger


if TYPE_CHECKING:
    from db.models import PromptTemplate


class PromptTemplateProcessorError(Exception):
    """Raised when template processing fails due to incomplete template"""

    pass


class PromptTemplateProcessor:
    """
    Pure business logic for prompt template processing.

    All methods are static and pure functions (100% testable without mocks).
    NO fallbacks - templates MUST be complete or will raise error.
    """

    @staticmethod
    def build_prompt(template: "PromptTemplate", user_input: str) -> str:
        """
        Build complete prompt from template and user input.

        Pure function - no side effects, fully unit-testable

        Args:
            template: PromptTemplate instance
            user_input: User's input text

        Returns:
            Complete prompt string combining pre_condition + user_input + post_condition

        Example:
            template = PromptTemplate(
                pre_condition="You are a lyric writer.",
                post_condition="Format as verse-chorus structure."
            )
            prompt = build_prompt(template, "Write about love")
            # Returns:
            # "You are a lyric writer.
            #
            # Write about love
            #
            # Format as verse-chorus structure."
        """
        pre_condition = template.pre_condition or ""
        post_condition = template.post_condition or ""

        # Build the complete prompt with double newlines as separators
        parts = []
        if pre_condition.strip():
            parts.append(pre_condition.strip())
        if user_input.strip():
            parts.append(user_input.strip())
        if post_condition.strip():
            parts.append(post_condition.strip())

        complete_prompt = "\n\n".join(parts)

        logger.debug(
            "Built prompt",
            category=template.category,
            action=template.action,
            template_id=template.id,
            prompt_length=len(complete_prompt),
            has_pre_condition=bool(pre_condition.strip()),
            has_post_condition=bool(post_condition.strip()),
        )

        return complete_prompt

    @staticmethod
    def process_template(template: "PromptTemplate", user_input: str) -> dict[str, Any]:
        """
        Complete template processing: validate parameters and build prompt.

        This is the main entry point for template processing.
        NO FALLBACKS - template MUST be complete or raises error.

        Pure function - only logs, no other side effects

        Args:
            template: PromptTemplate instance
            user_input: User's input text

        Returns:
            Dict with complete processing result:
            {
                "prompt": str,              # Complete prompt text
                "model": str,               # Model name from template
                "temperature": float,       # Temperature from template
                "max_tokens": int | None    # Max tokens from template (None = no limit)
            }

        Raises:
            PromptTemplateProcessorError: If template is missing required fields (model, temperature)

        Side Effects:
            Logs INFO for success, ERROR if template incomplete

        Example:
            result = PromptTemplateProcessor.process_template(template, "Write a song")
            # Use result["prompt"], result["model"], etc. for API call
        """
        # Step 1: Validate required fields (NO FALLBACKS!)
        if not template.model or not template.model.strip():
            raise PromptTemplateProcessorError(
                f"Template {template.category}/{template.action} missing required field: model"
            )

        if template.temperature is None:
            raise PromptTemplateProcessorError(
                f"Template {template.category}/{template.action} missing required field: temperature"
            )

        # max_tokens can be None (means no limit) - this is valid!
        model = template.model
        temperature = template.temperature
        max_tokens = template.max_tokens  # None or int (0 also means no limit)

        # Step 2: Build prompt
        prompt = PromptTemplateProcessor.build_prompt(template, user_input)

        # Step 3: Combine everything
        result = {
            "prompt": prompt,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        logger.info(
            "Processed template",
            category=template.category,
            action=template.action,
            template_id=template.id,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens if max_tokens is not None else "no_limit",
            prompt_length=len(prompt),
        )

        return result
