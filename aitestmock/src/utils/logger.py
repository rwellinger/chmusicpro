"""
Centralized logging configuration using loguru.
Replaces all print() statements with structured logging.
"""

import logging
import sys

from loguru import logger

from config.settings import LOG_LEVEL


# Remove default logger
logger.remove()


# Custom formatter function to handle extra fields
def format_record(record):
    """
    Custom formatter that displays extra fields based on log level:
    - DEBUG: Shows extra fields inline (compact, single-line)
    - INFO/WARNING: Message only (clean for production)
    - ERROR/CRITICAL: Shows extra fields multi-line (detailed error analysis)
    """
    # Base format
    format_str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    # Show extra fields for ALL levels (different formatting per level)
    extra = record["extra"]

    if record["level"].name in ("ERROR", "CRITICAL"):
        # ERROR/CRITICAL: Multi-line format with special handling for error fields
        if "error_type" in extra:
            format_str += "\n  <yellow>└─ Type:</yellow> <red>{extra[error_type]}</red>"

        if "error" in extra:
            format_str += "\n  <yellow>└─ Error:</yellow> <red>{extra[error]}</red>"

        if "stacktrace" in extra and extra["stacktrace"]:
            format_str += (
                "\n  <yellow>└─ Stacktrace:</yellow>\n<red>{extra[stacktrace]}</red>"
            )

        # Show other extra fields (except already handled ones)
        other_extras = {
            k: v
            for k, v in extra.items()
            if k not in ("error_type", "error", "stacktrace") and not k.startswith("_")
        }
        if other_extras:
            for key, value in other_extras.items():
                # Serialize complex objects and escape braces
                if isinstance(value, (dict, list)):
                    import json

                    value_str = json.dumps(value, ensure_ascii=False)
                else:
                    value_str = str(value)
                value_str = value_str.replace("{", "{{").replace("}", "}}")
                format_str += f"\n  <yellow>└─ {key}:</yellow> {value_str}"
    else:
        # DEBUG, INFO, WARNING: Compact inline format (key=value key=value)
        relevant_extras = {k: v for k, v in extra.items() if not k.startswith("_")}
        if relevant_extras:
            for key, value in relevant_extras.items():
                # Serialize complex objects (dict, list) to avoid format string issues
                if isinstance(value, (dict, list)):
                    import json

                    value_str = json.dumps(value, ensure_ascii=False)
                else:
                    value_str = str(value)

                # Truncate long values for readability
                if len(value_str) > 100:
                    value_str = value_str[:97] + "..."

                # Escape curly braces to prevent format string errors
                value_str = value_str.replace("{", "{{").replace("}", "}}")

                format_str += f" <cyan>{key}</cyan>=<yellow>{value_str}</yellow>"

    format_str += "\n"
    return format_str


# Console handler: INFO and above with colors
logger.add(
    sys.stderr,
    level=LOG_LEVEL,
    format=format_record,
    colorize=True,
)


# Flask-Logging auf loguru umleiten
class LoguruHandler(logging.Handler):
    def emit(self, record):
        # LogRecord in loguru format umwandeln
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Frame für korrekte Anzeige finden
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


# Celery-Logging auf loguru umleiten
class CeleryInterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())


# Export configured logger
__all__ = ["logger"]
