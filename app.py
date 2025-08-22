import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from engines.llm_engine import chat_recommendation, route_recommendation

load_dotenv()

app = Flask(__name__)
CORS(app)

@app.post("/api/chat")
def api_chat():
    data = request.get_json(force=True)
    loc = data["location"]      # {lat, lon}
    prompt = data.get("prompt", "")
    radius_m = int(data.get("radius_m", 3000))

    result = chat_recommendation(loc, prompt, radius_m=radius_m)
    return jsonify({"summary": result})

@app.post("/api/route")
def api_route():
    data = request.get_json(force=True)
    start = data["start"]       # {lat, lon}
    end = data["end"]           # {lat, lon}
    prompt = data.get("prompt", "")

    result = route_recommendation(start, end, prompt)
    return jsonify({"summary": result})

if __name__ == "__main__":
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", "8080"))
    app.run(host=host, port=port, debug=True)