from flask import Blueprint

from controllers.mureka_controller import MurekaController
from utils.logger import logger


mureka_routes = Blueprint("mureka", __name__)
controller = MurekaController()


@mureka_routes.route("/song/generate", methods=["POST"])
def generate_song():
    """Simulation of https://api.mureka.ai/v1/song/generate"""
    logger.debug("Generating song")
    return controller.generate_song()


@mureka_routes.route("/song/stem", methods=["POST"])
def generate_stem():
    """Simulation of https://api.mureka.ai/v1/song/stem"""
    logger.debug("Generating stem")
    return controller.generate_stem()


@mureka_routes.route("/song/query/<job_id>", methods=["GET"])
def query_song_status(job_id):
    """Simulation of https://api.mureka.ai/v1/song/query/<job_id>"""
    logger.debug("Querying song status", job_id=job_id)
    return controller.query_song_status(job_id)


@mureka_routes.route("/account/billing", methods=["GET"])
def get_billing_info():
    """Simulation of https://api.mureka.ai/v1/account/billing"""
    logger.debug("Getting billing info")
    return controller.get_billing_info()


@mureka_routes.route("/instrumental/generate", methods=["POST"])
def generate_instrumental():
    """Simulation of https://api.mureka.ai/v1/instrumental/generate"""
    logger.debug("Generating instrumental")
    return controller.generate_instrumental()


@mureka_routes.route("/instrumental/query/<job_id>", methods=["GET"])
def query_instrumental_status(job_id):
    """Simulation of https://api.mureka.ai/v1/instrumental/query/<job_id>"""
    logger.debug("Querying instrumental status", job_id=job_id)
    return controller.query_instrumental_status(job_id)
