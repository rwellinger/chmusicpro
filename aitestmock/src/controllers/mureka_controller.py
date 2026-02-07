from flask import jsonify, request

from services.mureka_service import MurekaService


class MurekaController:
    def __init__(self):
        self.service = MurekaService()

    def generate_song(self):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid authorization"}), 401

        data = request.get_json()

        lyrics = data.get("lyrics")
        model = data.get("model", "auto")
        prompt = data.get("prompt")  # This is the style prompt

        result = self.service.generate_song(lyrics, model, prompt)

        # Check for 429 error test cases
        if "error" in result and (
            "rate limit" in result.get("message", "").lower()
            or "quota" in result.get("message", "").lower()
        ):
            return jsonify(result), 429

        return jsonify(result)

    def generate_stem(self):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid authorization"}), 401

        data = request.get_json()
        url = data.get("url")

        result = self.service.generate_stem(url)

        return jsonify(result)

    def query_song_status(self, job_id):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid authorization"}), 401

        result = self.service.query_song_status(job_id)

        # Check for 429 error test cases
        if "error" in result and (
            "rate limit" in result.get("message", "").lower()
            or "quota" in result.get("message", "").lower()
        ):
            return jsonify(result), 429

        return jsonify(result)

    def get_billing_info(self):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid authorization"}), 401

        result = self.service.get_billing_info()

        return jsonify(result)

    def generate_instrumental(self):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid authorization"}), 401

        data = request.get_json()

        model = data.get("model", "auto")
        prompt = data.get("prompt")  # This is the style prompt

        result = self.service.generate_instrumental(model, prompt)

        # Check for 429 error test cases
        if "error" in result and (
            "rate limit" in result.get("message", "").lower()
            or "quota" in result.get("message", "").lower()
        ):
            return jsonify(result), 429

        return jsonify(result)

    def query_instrumental_status(self, job_id):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid authorization"}), 401

        result = self.service.query_instrumental_status(job_id)

        # Check for 429 error test cases
        if "error" in result and (
            "rate limit" in result.get("message", "").lower()
            or "quota" in result.get("message", "").lower()
        ):
            return jsonify(result), 429

        return jsonify(result)
