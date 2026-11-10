import os
import tempfile
import asyncio
from flask import Flask, request, send_file, jsonify
import edge_tts

app = Flask(__name__)

API_KEY = os.environ.get("JARVIS_VOICE_KEY")

VOICES = {
    "male_indian_english": "en-IN-PrabhatNeural",
    "male_indian_hindi": "hi-IN-MadhurNeural"
}


@app.get("/")
def home():
    return jsonify({
        "status": "online",
        "service": "JARVIS Neural Voice"
    })


@app.post("/speak")
def speak():
    if not API_KEY:
        return jsonify({"error": "Server key not configured"}), 500

    supplied_key = request.headers.get("X-API-Key", "")

    if supplied_key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    voice_type = data.get("voice", "male_indian_english")

    if not text:
        return jsonify({"error": "Text is required"}), 400

    if len(text) > 1500:
        return jsonify({"error": "Text is too long"}), 413

    voice = VOICES.get(voice_type)

    if not voice:
        return jsonify({"error": "Invalid voice"}), 400

    async def generate():
        with tempfile.NamedTemporaryFile(
            suffix=".mp3", delete=False
        ) as temp:
            path = temp.name

        try:
            communicator = edge_tts.Communicate(
                text,
                voice,
                rate="+15%",
                pitch="-5Hz"
            )
            await communicator.save(path)
            return path
        except Exception:
            if os.path.exists(path):
                os.remove(path)
            raise

    try:
        path = asyncio.run(generate())

        response = send_file(
            path,
            mimetype="audio/mpeg",
            as_attachment=False,
            download_name="jarvis.mp3"
        )

        response.call_on_close(
            lambda: os.path.exists(path) and os.remove(path)
        )

        return response

    except Exception as error:
        app.logger.exception("Voice generation failed")
        return jsonify({"error": "Voice generation failed"}), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
