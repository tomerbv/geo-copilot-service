import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from engines.engine_manager import EngineManager

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

if __name__ == "__main__":
    app.run(host=os.getenv("FLASK_HOST", "0.0.0.0"),
            port=int(os.getenv("FLASK_PORT", "8080")),
            debug=True)
