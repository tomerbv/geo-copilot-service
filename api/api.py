from flask import Flask, request, jsonify
from flask_cors import CORS
from managers.engine_manager import EngineManager

def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)

    manager = EngineManager()

    @app.post("/api/chat")
    def api_chat():
        data = request.get_json(force=True)
        loc = (data["location"]["lat"], data["location"]["lon"])
        txt = manager.chat.run(loc, data.get("prompt", ""))
        return jsonify({"summary": txt})

    @app.post("/api/route")
    def api_route():
        data = request.get_json(force=True)
        start = (data["start"]["lat"], data["start"]["lon"])
        end   = (data["end"]["lat"],   data["end"]["lon"])
        txt = manager.route.run(start, end, data.get("prompt", ""))
        return jsonify({"summary": txt})

    return app
