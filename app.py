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

# Emotion-based voice settings
EMOTIONS = {
    "normal": {
        "rate": "+15%",
        "pitch": "-5Hz",
        "volume": "+0%"
    },
    "angry": {
        "rate": "+25%",
        "pitch": "+15Hz",
        "volume": "+15%"
    },
    "savage": {
        "rate": "+18%",
        "pitch": "+5Hz",
        "volume": "+8%"
    },
    "happy": {
        "rate": "+22%",
        "pitch": "+20Hz",
        "volume": "+12%"
    },
    "sad": {
        "rate": "-15%",
        "pitch": "-15Hz",
        "volume": "-10%"
    },
    "caring": {
        "rate": "-8%",
        "pitch": "-5Hz",
        "volume": "-5%"
    },
    "surprised": {
        "rate": "+25%",
        "pitch": "+25Hz",
        "volume": "+10%"
    }
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
    emotion = str(data.get("emotion", "normal")).lower().strip()

    if not text:
        return jsonify({"error": "Text is required"}), 400

    if len(text) > 1500:
        return jsonify({"error": "Text is too long"}), 413

    voice = VOICES.get(voice_type)

    if not voice:
        return jsonify({"error": "Invalid voice"}), 400

    # Use normal emotion if an invalid emotion is received
    voice_settings = EMOTIONS.get(emotion)

    if not voice_settings:
        emotion = "normal"
        voice_settings = EMOTIONS["normal"]

    async def generate():
        with tempfile.NamedTemporaryFile(
            suffix=".mp3", delete=False
        ) as temp:
            path = temp.name

        try:
            communicator = edge_tts.Communicate(
                text,
                voice,
                rate=voice_settings["rate"],
                pitch=voice_settings["pitch"],
                volume=voice_settings["volume"]
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

    except Exception:
        app.logger.exception("Voice generation failed")
        return jsonify({"error": "Voice generation failed"}), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
