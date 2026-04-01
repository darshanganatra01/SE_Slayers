from flask_restx import Namespace, Resource

health_ns = Namespace("health", description="Health-check endpoints")


@health_ns.route("/")
class HealthCheck(Resource):
    """Simple health-check to verify the API is running."""

    def get(self):
        """Return API health status."""
        return {"status": "ok", "message": "SE Slayers API is running 🚀"}
