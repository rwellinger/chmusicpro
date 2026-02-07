from flask import Blueprint, request

from controllers.openai_controller import OpenAIController
from utils.logger import logger


openai_routes = Blueprint("openai", __name__)
controller = OpenAIController()


@openai_routes.route("/images/generations", methods=["POST"])
def generate_image():
    """Simulation of https://api.openai.com/v1/images/generations"""
    logger.debug("Generating image")
    return controller.generate_image()


@openai_routes.route("/organization/costs", methods=["GET"])
def organization_costs():
    """Simulation of https://api.openai.com/v1/organization/costs"""
    start_time = int(request.args.get("start_time", 0))
    end_time = int(request.args.get("end_time", 0))
    limit = int(request.args.get("limit", 7))

    logger.debug(
        "Mock OpenAI Cost API called",
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )
    return controller.organization_costs(start_time, end_time, limit)
