# app.py
from flask import Flask, request, jsonify, send_file
import os
import base64
from vosk import Model, KaldiRecognizer
import json
import subprocess

app = Flask(__name__)

# Percorso al modello Vosk
VOSK_MODEL_PATH = "assets/models/vosk-model-small-it"
model = None

# Carica il modello Vosk una volta
def load_vosk_model():
    global model
    if not model and os.path.exists(VOSK_MODEL_PATH):
        print("🔄 Caricamento modello Vosk...")
        model = Model(VOSK_MODEL_PATH)
    return model

@app.route('/')
def index():
    return send_file('gui.html')

@app.route('/transcribe', methods=['POST'])
def transcribe():
    data = request.get_json()
    audio_data_b64 = data.get('audio', '')

    # Decodifica l'audio da base64
    audio_data = base64.b64decode(audio_data_b64.split(',')[1])  # Rimuove "data:audio/wav;base64,"

    # Salva temporaneamente
    with open("temp.wav", "wb") as f:
        f.write(audio_data)

    # Trascrivi con Vosk
    vosk_model = load_vosk_model()
    if not vosk_model:
        return jsonify({"error": "Modello Vosk non trovato"})

    rec = KaldiRecognizer(vosk_model, 16000)
    with open("temp.wav", "rb") as f:
        f.read(44)  # Salta l'header WAV
        data_chunk = f.read(8000)
        final_text = ""
        while data_chunk:
            if rec.AcceptWaveform(data_chunk):
                result = rec.Result()
                final_text += json.loads(result)["text"] + " "
            data_chunk = f.read(8000)
        final_text += json.loads(rec.FinalResult())["text"]

    # Rimuovi il file temporaneo
    os.remove("temp.wav")

    return jsonify({"text": final_text.strip()})

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data.get("message", "").strip()
    reply = "Ho ricevuto: " + message  # Sostituisci con Phi-3-mini
    return jsonify({"reply": reply})

if __name__ == '__main__':
    app.run(port=5000, debug=False, use_reloader=False)
