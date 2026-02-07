"""
Flask App mit allen Blueprints + OpenAPI/Swagger Integration
"""

import contextlib
import traceback
from pathlib import Path

import tomli
import yaml
from apispec import APISpec
from flask import Blueprint, Flask, Response, jsonify
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

from utils.logger import logger

from .routes.chat_routes import api_chat_v1
from .routes.claude_chat_routes import api_claude_chat_v1
from .routes.conversation_routes import api_conversation_v1
from .routes.cost_routes import api_openai_costs_v1
from .routes.equipment_routes import api_equipment_v1
from .routes.health_routes import api_health_v1
from .routes.image_routes import api_image_v1
from .routes.lyric_parsing_rule_routes import api_lyric_parsing_rule_v1
from .routes.ollama_routes import api_ollama_v1
from .routes.openai_chat_routes import api_openai_chat_v1
from .routes.prompt_routes import api_prompt_v1
from .routes.sketch_routes import api_sketch_v1
from .routes.song_project_routes import api_song_projects_v1
from .routes.song_release_routes import api_song_releases_v1
from .routes.song_routes import api_song_v1
from .routes.user_routes import api_user_v1
from .routes.workshop_routes import api_workshop_v1


def get_version() -> str:
    """Read version from pyproject.toml"""
    try:
        # Path from src/api/app.py to aiproxysrv root (2 levels up)
        pyproject_path = Path(__file__).parents[2] / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            pyproject_data = tomli.load(f)
            return pyproject_data.get("project", {}).get("version", "unknown")
    except Exception as e:
        logger.warning("Failed to read version from pyproject.toml", error=str(e))
        return "unknown"


def create_app():
    """Flask App Factory with OpenAPI/Swagger Integration"""
    app = Flask(__name__)

    # Add ProxyFix middleware to handle reverse proxy headers
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

    # Monkey patch json.dumps to handle ValueError serialization globally
    import json

    original_dumps = json.dumps

    def patched_dumps(obj, **kwargs):
        try:
            return original_dumps(obj, **kwargs)
        except TypeError as e:
            if "ValueError" in str(e) and "not JSON serializable" in str(e):
                # Convert ValueError objects to strings recursively
                def convert_valueerrors(o):
                    if isinstance(o, ValueError):
                        return str(o)
                    elif isinstance(o, dict):
                        return {k: convert_valueerrors(v) for k, v in o.items()}
                    elif isinstance(o, list):
                        return [convert_valueerrors(item) for item in o]
                    return o

                converted_obj = convert_valueerrors(obj)
                return original_dumps(converted_obj, **kwargs)
            raise e

    # Replace json.dumps globally
    json.dumps = patched_dumps

    # Configure CORS to allow requests from Angular frontend
    CORS(app, origins="*", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])

    # OpenAPI/Swagger Configuration
    spec = APISpec(
        title="thWellys AI-Proxy API",
        version=get_version(),
        openapi_version="3.0.2",
        info={
            "description": "API für AI-Services: Bildgenerierung, Musikgenerierung und Chat-Integration",
            "contact": {"name": "rwellinger", "url": "https://github.com/rwellinger/thwellys-ai-toolbox"},
        },
        servers=[{"url": "http://localhost:5050/api/v1", "description": "Development Server"}],
    )

    # Global API Blueprint
    api_v1 = Blueprint("api_v1", __name__, url_prefix="/api/v1")

    @api_v1.route("/health")
    def health():
        """Health check endpoint"""
        from schemas.common_schemas import HealthResponse

        response = HealthResponse()
        return jsonify(response.model_dump()), 200

    @app.route("/api/openapi.json")
    def openapi_spec():
        """OpenAPI JSON specification endpoint"""
        try:
            # Import and register schemas
            # Equipment schemas (defined in controller)
            from api.controllers.equipment_controller import (
                EquipmentCreateRequest,
                EquipmentListResponse,
                EquipmentResponse,
                EquipmentUpdateRequest,
            )
            from schemas.chat_schemas import ChatErrorResponse, ChatRequest, ChatResponse, UnifiedChatRequest
            from schemas.common_schemas import (
                BulkDeleteRequest,
                BulkDeleteResponse,
                ErrorResponse,
                HealthResponse,
            )
            from schemas.conversation_schemas import (
                ConversationCreate,
                ConversationDetailResponse,
                ConversationListResponse,
                ConversationResponse,
                ConversationUpdate,
                MessageCreate,
                MessageResponse,
                SendMessageRequest,
                SendMessageResponse,
            )
            from schemas.image_schemas import (
                ImageDeleteResponse,
                ImageGenerateRequest,
                ImageGenerateResponse,
                ImageListRequest,
                ImageListResponse,
                ImageResponse,
                ImageUpdateRequest,
                ImageUpdateResponse,
            )
            from schemas.lyric_parsing_rule_schemas import (
                LyricParsingRuleCreate,
                LyricParsingRuleListResponse,
                LyricParsingRuleReorderRequest,
                LyricParsingRuleResponse,
                LyricParsingRuleUpdate,
            )
            from schemas.openai_chat_schemas import OpenAIChatRequest, OpenAIChatResponse, OpenAIModelsListResponse
            from schemas.prompt_schemas import (
                PromptCategoryResponse,
                PromptTemplateCreate,
                PromptTemplateListResponse,
                PromptTemplateResponse,
                PromptTemplatesGroupedResponse,
                PromptTemplateUpdate,
            )
            from schemas.sketch_schemas import (
                SketchCreateRequest,
                SketchDeleteResponse,
                SketchDetailResponse,
                SketchListRequest,
                SketchListResponse,
                SketchResponse,
                SketchUpdateRequest,
            )
            from schemas.song_project_schemas import (
                FileResponse,
                FileUploadResponse,
                FolderResponse,
                ProjectCreateRequest,
                ProjectDetailResponse,
                ProjectListResponse,
                ProjectResponse,
                ProjectUpdateRequest,
            )
            from schemas.song_schemas import (
                ChoiceRatingUpdateRequest,
                ChoiceRatingUpdateResponse,
                SongDeleteResponse,
                SongListRequest,
                SongListResponse,
                SongResponse,
                SongUpdateRequest,
                SongUpdateResponse,
            )
            from schemas.user_schemas import (
                LoginRequest,
                LoginResponse,
                LogoutResponse,
                PasswordChangeRequest,
                PasswordChangeResponse,
                PasswordResetRequest,
                PasswordResetResponse,
                TokenValidationResponse,
                UserCreateRequest,
                UserCreateResponse,
                UserListResponse,
                UserResponse,
                UserUpdateRequest,
                UserUpdateResponse,
            )

            # Register schemas with APISpec (only if not already registered)
            schemas_to_register = [
                # Image schemas
                ("ImageGenerateRequest", ImageGenerateRequest),
                ("ImageResponse", ImageResponse),
                ("ImageGenerateResponse", ImageGenerateResponse),
                ("ImageListRequest", ImageListRequest),
                ("ImageListResponse", ImageListResponse),
                ("ImageUpdateRequest", ImageUpdateRequest),
                ("ImageUpdateResponse", ImageUpdateResponse),
                ("ImageDeleteResponse", ImageDeleteResponse),
                # Song schemas
                ("SongResponse", SongResponse),
                ("SongListRequest", SongListRequest),
                ("SongListResponse", SongListResponse),
                ("SongUpdateRequest", SongUpdateRequest),
                ("SongUpdateResponse", SongUpdateResponse),
                ("SongDeleteResponse", SongDeleteResponse),
                ("ChoiceRatingUpdateRequest", ChoiceRatingUpdateRequest),
                ("ChoiceRatingUpdateResponse", ChoiceRatingUpdateResponse),
                # Chat schemas
                ("ChatRequest", ChatRequest),
                ("ChatResponse", ChatResponse),
                ("UnifiedChatRequest", UnifiedChatRequest),
                ("ChatErrorResponse", ChatErrorResponse),
                # Conversation schemas
                ("ConversationCreate", ConversationCreate),
                ("ConversationResponse", ConversationResponse),
                ("ConversationListResponse", ConversationListResponse),
                ("ConversationDetailResponse", ConversationDetailResponse),
                ("ConversationUpdate", ConversationUpdate),
                ("MessageCreate", MessageCreate),
                ("MessageResponse", MessageResponse),
                ("SendMessageRequest", SendMessageRequest),
                ("SendMessageResponse", SendMessageResponse),
                # OpenAI Chat schemas
                ("OpenAIChatRequest", OpenAIChatRequest),
                ("OpenAIChatResponse", OpenAIChatResponse),
                ("OpenAIModelsListResponse", OpenAIModelsListResponse),
                # Lyric Parsing Rule schemas
                ("LyricParsingRuleCreate", LyricParsingRuleCreate),
                ("LyricParsingRuleUpdate", LyricParsingRuleUpdate),
                ("LyricParsingRuleResponse", LyricParsingRuleResponse),
                ("LyricParsingRuleListResponse", LyricParsingRuleListResponse),
                ("LyricParsingRuleReorderRequest", LyricParsingRuleReorderRequest),
                # Prompt schemas
                ("PromptTemplateCreate", PromptTemplateCreate),
                ("PromptTemplateUpdate", PromptTemplateUpdate),
                ("PromptTemplateResponse", PromptTemplateResponse),
                ("PromptTemplateListResponse", PromptTemplateListResponse),
                ("PromptCategoryResponse", PromptCategoryResponse),
                ("PromptTemplatesGroupedResponse", PromptTemplatesGroupedResponse),
                # Common schemas
                ("ErrorResponse", ErrorResponse),
                ("HealthResponse", HealthResponse),
                ("BulkDeleteRequest", BulkDeleteRequest),
                ("BulkDeleteResponse", BulkDeleteResponse),
                # User schemas
                ("UserCreateRequest", UserCreateRequest),
                ("UserCreateResponse", UserCreateResponse),
                ("LoginRequest", LoginRequest),
                ("LoginResponse", LoginResponse),
                ("UserUpdateRequest", UserUpdateRequest),
                ("UserUpdateResponse", UserUpdateResponse),
                ("PasswordChangeRequest", PasswordChangeRequest),
                ("PasswordChangeResponse", PasswordChangeResponse),
                ("PasswordResetRequest", PasswordResetRequest),
                ("PasswordResetResponse", PasswordResetResponse),
                ("UserResponse", UserResponse),
                ("UserListResponse", UserListResponse),
                ("LogoutResponse", LogoutResponse),
                ("TokenValidationResponse", TokenValidationResponse),
                # Song Project schemas
                ("ProjectCreateRequest", ProjectCreateRequest),
                ("ProjectUpdateRequest", ProjectUpdateRequest),
                ("ProjectResponse", ProjectResponse),
                ("ProjectDetailResponse", ProjectDetailResponse),
                ("ProjectListResponse", ProjectListResponse),
                ("FolderResponse", FolderResponse),
                ("FileResponse", FileResponse),
                ("FileUploadResponse", FileUploadResponse),
                # Sketch schemas
                ("SketchCreateRequest", SketchCreateRequest),
                ("SketchUpdateRequest", SketchUpdateRequest),
                ("SketchResponse", SketchResponse),
                ("SketchListRequest", SketchListRequest),
                ("SketchListResponse", SketchListResponse),
                ("SketchDetailResponse", SketchDetailResponse),
                ("SketchDeleteResponse", SketchDeleteResponse),
                # Equipment schemas
                ("EquipmentCreateRequest", EquipmentCreateRequest),
                ("EquipmentUpdateRequest", EquipmentUpdateRequest),
                ("EquipmentResponse", EquipmentResponse),
                ("EquipmentListResponse", EquipmentListResponse),
            ]

            # Only register schemas that aren't already registered
            for schema_name, schema_class in schemas_to_register:
                with contextlib.suppress(Exception):
                    # Schema already registered, skip silently
                    spec.components.schema(schema_name, schema=schema_class)

            # Automatic route discovery and OpenAPI generation
            def generate_paths_from_routes():
                """Automatically generate OpenAPI paths from Flask routes"""
                import inspect

                # Tag mapping for cleaner organization
                tag_mapping = {
                    "api_image_v1": "Images",
                    "api_song_v1": "Songs",
                    "api_song_projects_v1": "Song Projects",
                    "api_song_releases_v1": "Song Releases",
                    "api_sketch_v1": "Sketches",
                    "api_lyric_parsing_rule_v1": "Lyric Parsing Rules",
                    "api_prompt_v1": "Prompt Templates",
                    "api_chat_v1": "Chat",
                    "api_conversation_v1": "Conversations",
                    "api_openai_chat_v1": "OpenAI Chat",
                    "api_claude_chat_v1": "Claude Chat",
                    "api_openai_costs_v1": "OpenAI Costs",
                    "api_equipment_v1": "Equipment",
                    "api_user_v1": "User Management",
                    "api_ollama_v1": "Ollama",
                    "api_v1": "System",
                }

                current_paths = set(spec.to_dict().get("paths", {}).keys())

                for rule in app.url_map.iter_rules():
                    # Only process API routes
                    if not rule.endpoint.startswith(
                        (
                            "api_image_v1",
                            "api_song_v1",
                            "api_song_projects_v1",
                            "api_song_releases_v1",
                            "api_sketch_v1",
                            "api_lyric_parsing_rule_v1",
                            "api_prompt_v1",
                            "api_chat_v1",
                            "api_conversation_v1",
                            "api_openai_chat_v1",
                            "api_claude_chat_v1",
                            "api_openai_costs_v1",
                            "api_equipment_v1",
                            "api_user_v1",
                            "api_ollama_v1",
                            "api_v1",
                        )
                    ):
                        continue

                    # Skip if already added
                    route_path = rule.rule.replace("/api/v1", "")
                    if route_path in current_paths:
                        continue

                    try:
                        # Get the view function
                        view_func = app.view_functions.get(rule.endpoint)
                        if not view_func:
                            continue

                        # Extract blueprint name for tagging
                        blueprint_name = (
                            rule.endpoint.split(".")[0]
                            if "." in rule.endpoint
                            else rule.endpoint.split("_")[0] + "_" + rule.endpoint.split("_")[1] + "_v1"
                        )
                        tag = tag_mapping.get(blueprint_name, "API")

                        # Get function signature for parameter detection
                        sig = inspect.signature(view_func)

                        # Build operations for each HTTP method
                        operations = {}
                        for method in rule.methods:
                            if method in ["OPTIONS", "HEAD"]:
                                continue

                            operation = {
                                "tags": [tag],
                                "summary": (view_func.__doc__ or f"{method} {route_path}").strip(),
                                "description": view_func.__doc__ or f"API endpoint for {route_path}",
                                "responses": {
                                    "200": {
                                        "description": "Success",
                                        "content": {"application/json": {"schema": {"type": "object"}}},
                                    },
                                    "400": {
                                        "description": "Bad Request",
                                        "content": {
                                            "application/json": {
                                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                            }
                                        },
                                    },
                                },
                            }

                            # Add request body for POST/PUT methods with Pydantic models
                            if method.lower() in ["post", "put"]:
                                # Try to detect Pydantic model from function signature
                                for param_name, param in sig.parameters.items():
                                    if param_name == "body" and hasattr(param.annotation, "__name__"):
                                        schema_name = param.annotation.__name__
                                        operation["requestBody"] = {
                                            "required": True,
                                            "content": {
                                                "application/json": {
                                                    "schema": {"$ref": f"#/components/schemas/{schema_name}"}
                                                }
                                            },
                                        }
                                        break

                            # Add path parameters
                            if "<" in rule.rule:
                                operation["parameters"] = []
                                for arg in rule.arguments:
                                    # noinspection PyTypeChecker
                                    operation["parameters"].append(
                                        {
                                            "name": arg,
                                            "in": "path",
                                            "required": True,
                                            "schema": {"type": "string"},
                                            "description": f"Path parameter: {arg}",
                                        }
                                    )

                            operations[method.lower()] = operation

                        # Add path to spec
                        if operations:
                            spec.path(path=route_path, operations=operations)

                    except Exception as e:
                        # Skip problematic routes
                        logger.warning(f"Could not process route {rule.rule}", error=str(e))
                        continue

            # Generate all paths automatically
            generate_paths_from_routes()

            return jsonify(spec.to_dict())
        except Exception as e:
            logger.error("OpenAPI spec generation failed", error=str(e), stacktrace=traceback.format_exc())
            return jsonify({"error": f"OpenAPI generation failed: {str(e)}"}), 500

    @app.route("/api/openapi.yaml")
    def openapi_spec_yaml():
        """OpenAPI YAML specification endpoint"""
        try:
            # Get the JSON spec
            with app.test_request_context():
                json_response = openapi_spec()
                if json_response.status_code != 200:
                    return json_response

                openapi_dict = json_response.get_json()
                yaml_content = yaml.dump(openapi_dict, default_flow_style=False, allow_unicode=True)

                return Response(
                    yaml_content,
                    mimetype="application/x-yaml",
                    headers={"Content-Disposition": 'inline; filename="openapi.yaml"'},
                )
        except Exception as e:
            logger.error("OpenAPI YAML spec generation failed", error=str(e), stacktrace=traceback.format_exc())
            return jsonify({"error": f"OpenAPI YAML generation failed: {str(e)}"}), 500

    @app.route("/api/docs/")
    def swagger_ui():
        """Swagger UI endpoint"""
        swagger_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI Proxy Service API Documentation</title>
            <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@3.25.0/swagger-ui.css" />
        </head>
        <body>
            <div id="swagger-ui"></div>
            <script src="https://unpkg.com/swagger-ui-dist@3.25.0/swagger-ui-bundle.js"></script>
            <script>
                SwaggerUIBundle({
                    url: '../openapi.json',
                    dom_id: '#swagger-ui',
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIBundle.presets.standalone
                    ]
                });
            </script>
        </body>
        </html>
        """
        return swagger_html

    # Error Handler
    @app.errorhandler(404)
    def not_found(error):
        logger.warning("404 - Resource not found", error=str(error))
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(429)
    def subscription_error(error):
        logger.error("429 - Rate limit exceeded", error=str(error))
        return jsonify({"error": str(error)}), 429

    @app.errorhandler(500)
    def internal_error(error):
        logger.error("500 - Internal server error", error=str(error), stacktrace=traceback.format_exc())
        return jsonify({"error": "Internal server error"}), 500

    # Add specific Pydantic ValidationError handler
    from pydantic import ValidationError

    @app.errorhandler(ValidationError)
    def handle_pydantic_validation_error(error):
        """Handle Pydantic validation errors with HTTP 400"""

        # Extract field-specific error messages
        error_details = []
        for err in error.errors():
            field = ".".join(str(x) for x in err["loc"])
            message = err["msg"]
            error_details.append(f"{field}: {message}")

        logger.error("Pydantic validation error", error=str(error), fields=error_details)

        error_message = "; ".join(error_details) if error_details else str(error)
        return jsonify({"error": error_message, "validation_errors": error.errors()}), 400

    @app.errorhandler(ValueError)
    def handle_value_error(error):
        """Handle ValueError from Pydantic validators with HTTP 400"""
        error_str = str(error)

        # Check if this is likely a validation error from our Pydantic validators
        validation_keywords = ["must be one of", "must be a valid", "must be either", "Field required"]
        if any(keyword in error_str for keyword in validation_keywords):
            logger.error("Pydantic validator error", error=error_str)
            return jsonify({"error": error_str}), 400

        # For other ValueErrors, fall back to 500
        logger.error("ValueError", error=error_str)
        return jsonify({"error": "An unexpected error occurred"}), 500

    @app.errorhandler(Exception)
    def handle_general_exception(error):
        """Handle all other exceptions with HTTP 500"""
        logger.error(
            "Unhandled exception", error_type=type(error).__name__, error=str(error), stacktrace=traceback.format_exc()
        )
        return jsonify({"error": "An unexpected error occurred"}), 500

    # Register Blueprints
    app.register_blueprint(api_v1)
    app.register_blueprint(api_health_v1)
    app.register_blueprint(api_image_v1)
    app.register_blueprint(api_song_v1)
    app.register_blueprint(api_song_projects_v1)
    app.register_blueprint(api_song_releases_v1)
    app.register_blueprint(api_sketch_v1)
    app.register_blueprint(api_lyric_parsing_rule_v1)
    app.register_blueprint(api_chat_v1)
    app.register_blueprint(api_openai_costs_v1)
    app.register_blueprint(api_prompt_v1)
    app.register_blueprint(api_user_v1)
    app.register_blueprint(api_conversation_v1)
    app.register_blueprint(api_ollama_v1)
    app.register_blueprint(api_openai_chat_v1)
    app.register_blueprint(api_claude_chat_v1)
    app.register_blueprint(api_equipment_v1)
    app.register_blueprint(api_workshop_v1)

    return app
