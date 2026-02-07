"""Prompt Template Validator - Pure validation functions (testable business logic)"""


class PromptTemplateValidationError(Exception):
    """Raised when prompt template validation fails"""

    pass


class PromptTemplateValidator:
    """Validation logic for prompt templates (pure functions, 100% testable)"""

    @staticmethod
    def validate_version_increment(current_version: str | None) -> str:
        """
        Calculate next version number (auto-increment by 0.1).

        Pure function - no side effects, fully unit-testable

        Args:
            current_version: Current version string (e.g., "1.0", "2.5")

        Returns:
            Next version string (e.g., "1.1", "2.6")

        Example:
            validate_version_increment("1.0")  # Returns: "1.1"
            validate_version_increment("2.5")  # Returns: "2.6"
            validate_version_increment(None)   # Returns: "1.0"
            validate_version_increment("invalid")  # Returns: "1.0"
        """
        if not current_version:
            return "1.0"

        try:
            version_float = float(current_version)
            new_version = f"{version_float + 0.1:.1f}"
            return new_version
        except (ValueError, TypeError):
            # If version is not a valid float, start with 1.0
            return "1.0"

    @staticmethod
    def validate_category_action_format(category: str, action: str) -> None:
        """
        Validate category and action format.

        Pure function - raises exception if invalid

        Args:
            category: Template category (must be non-empty string)
            action: Template action (must be non-empty string)

        Raises:
            PromptTemplateValidationError: If category or action is invalid

        Example:
            validate_category_action_format("lyrics", "generate")  # OK
            validate_category_action_format("", "generate")  # Raises
            validate_category_action_format("lyrics", "")  # Raises
        """
        if not category or not category.strip():
            raise PromptTemplateValidationError("Category is required and cannot be empty")

        if not action or not action.strip():
            raise PromptTemplateValidationError("Action is required and cannot be empty")
