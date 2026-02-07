"""
Zentrale Konfiguration für aitestmock
"""

import os

from dotenv import load_dotenv


load_dotenv()

# --------------------------------------------------
# Flask Server Config
# --------------------------------------------------
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# --------------------------------------------------
# loguru
# --------------------------------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG" if DEBUG else "WARNING")
