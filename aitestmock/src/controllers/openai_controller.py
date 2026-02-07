import time

from flask import jsonify, request

from services.openai_service import OpenAIService


class OpenAIController:
    def __init__(self):
        self.service = OpenAIService()

    def generate_image(self):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid authorization"}), 401

        data = request.get_json()

        prompt = data.get("prompt")
        model = data.get("model", "dall-e-3")
        size = data.get("size", "1024x1024")
        quality = data.get("quality", "standard")
        n = data.get("n", 1)

        result = self.service.generate_image(prompt, model, size, quality, n)

        return jsonify(result)

    def organization_costs(self, start_time: int, end_time: int, limit: int):
        """Mock OpenAI Admin Cost API"""
        # Simulate slow API response (5 seconds)
        time.sleep(5)

        # Generate mock data (10 daily buckets)
        buckets = []
        current_ts = start_time
        day_seconds = 86400

        for i in range(min(10, limit)):
            bucket_start = current_ts
            bucket_end = current_ts + day_seconds

            # Mock costs: Some days with activity, some empty
            results = []
            if i % 3 == 0:  # Every 3rd day has DALL-E costs
                results.append(
                    {
                        "object": "organization.costs.result",
                        "amount": {"value": 0.08, "currency": "usd"},
                        "line_item": "dall-e 3, standard, 1024x1792, 1792x1024",
                        "project_id": "proj_mock123",
                        "organization_id": "org-mock123",
                    }
                )
            if i % 2 == 1:  # Every 2nd day has GPT costs
                results.extend(
                    [
                        {
                            "object": "organization.costs.result",
                            "amount": {"value": 0.00549, "currency": "usd"},
                            "line_item": "gpt-4o-2024-08-06, input",
                            "project_id": "proj_mock123",
                            "organization_id": "org-mock123",
                        },
                        {
                            "object": "organization.costs.result",
                            "amount": {"value": 0.00454, "currency": "usd"},
                            "line_item": "gpt-4o-2024-08-06, output",
                            "project_id": "proj_mock123",
                            "organization_id": "org-mock123",
                        },
                    ]
                )

            buckets.append(
                {
                    "object": "bucket",
                    "start_time": bucket_start,
                    "end_time": bucket_end,
                    "results": results,
                }
            )

            current_ts += day_seconds

        response = {
            "object": "page",
            "has_more": False,
            "next_page": None,
            "data": buckets,
            "organization_id": "org-mock123",  # Top-level org ID (like real OpenAI API)
        }

        return jsonify(response), 200
