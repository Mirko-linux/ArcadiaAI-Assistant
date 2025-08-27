# main.py - ArcadiaAI Assistant (Fork basato su Phi-2)
from flask import Flask, request, jsonify, send_from_directory
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import threading
import time
import os
import subprocess
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import ddg
import json

# --- CONFIGURAZIONE BASE ---
BASE_DIR = Path(__file__).parent
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max upload

# --- MODELLO LOCALE: PHI-2 (4-bit) ---
model = None
tokenizer = None
last_used = time.time()
MODEL_NAME = "microsoft/phi-2"

def load_model():
    global model, tokenizer, last_used
    if model is None:
        print("🔄 Caricamento Phi-2 in 4-bit...")
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            torch_dtype=torch.float16,
            device_map="auto",
            load_in_4bit=True
        )
        print("✅ Phi-2 caricato!")
    last_used = time.time()
    return model, tokenizer

def unload_model(delay=300):
    """Scarica il modello dopo X secondi di inattività"""
    time.sleep(delay)
    global model, tokenizer
    if time.time() - last_used >= delay:
        print("💤 Scarico Phi-2 per risparmiare risorse...")
        del model
        del tokenizer
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        model = tokenizer = None

# --- FUNZIONI CES LOCALI ---
def search_duckduckgo(query):
    results = ddg(query, max_results=5)
    return [{"title": r["title"], "href": r["href"], "body": r["body"]} for r in results]

def generate_image(prompt):
    # Usa un modello leggero locale (es. TinyStableDiffusion) o un servizio esterno
    # Per ora, ritorna un placeholder
    return f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}"

def get_weather(location):
    try:
        url = f"https://wttr.in/{location}?format=j1"
        response = requests.get(url, timeout=5)
        data = response.json()
        temp = data["current_condition"][0]["temp_C"]
        desc = data["current_condition"][0]["weatherDesc"][0]["value"]
        return f"🌡️ A {location}: {temp}°C, {desc}"
    except:
        return "❌ Impossibile ottenere il meteo."

# --- ROUTES ---
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/static/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

@app.route('/chat', methods=['POST'])
def chat():
    global model, tokenizer
    data = request.get_json()
    user_message = data.get("message", "").strip()
    history = data.get("history", [])
    attachments = data.get("attachments", [])

    if not user_message:
        return jsonify({"reply": "Scrivi un messaggio!"})

    # Carica modello
    model, tokenizer = load_model()

    # Wake-word simulato (per test)
    if user_message.lower().startswith("ehi arcadia"):
        user_message = user_message[len("ehi arcadia"):].strip()

    # Comandi SAC
    if user_message.startswith("@"):
        cmd = user_message.split()[0].lower()
        arg = " ".join(user_message.split()[1:]) if len(user_message.split()) > 1 else ""

        if cmd == "@cerca":
            results = search_duckduckoggo(arg or "informazioni")
            res_text = "\n".join([f"🔹 [{r['title']}]({r['href']})" for r in results])
            reply = f"🔍 Risultati per '{arg}':\n{res_text}"

        elif cmd == "@immagine":
            img_url = generate_image(arg or "un paesaggio")
            reply = f"🖼️ Ecco l'immagine:\n![]({img_url})"

        elif cmd == "@meteo":
            reply = get_weather(arg or "Roma")

        elif cmd == "@data":
            reply = f"📅 Oggi è {time.strftime('%d/%m/%Y, %H:%M')}"

        elif cmd == "@aiuto":
            reply = (
                "🎯 Comandi disponibili:\n"
                "- `@cerca [query]` → ricerca web\n"
                "- `@immagine [descrizione]` → genera immagine\n"
                "- `@meteo [luogo]` → meteo\n"
                "- `@data` → data/ora\n"
                "- `@app [nome]` → cerca app (Flathub, Snap, ecc.)\n"
                "- `@aiuto` → mostra questo messaggio"
            )

        else:
            reply = f"❌ Comando '{cmd}' non riconosciuto. Usa `@aiuto`."

    else:
        # Prompt contestuale
        prompt = (
            "Sei ArcadiaAI Assistant, un assistente open source locale basato su Phi-2.\n"
            "Creatore: Mirko Yuri Donato\n"
            "Rispondi in modo chiaro, utile e conciso.\n\n"
        )
        for msg in history[-6:]:
            prompt += f"{msg['role']}: {msg['content']}\n"
        prompt += f"Utente: {user_message}\nArcadiaAI:"

        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024).to(model.device)
        outputs = model.generate(**inputs, max_new_tokens=256, pad_token_id=tokenizer.eos_token_id)
        reply = tokenizer.decode(outputs[0], skip_special_tokens=True).split("ArcadiaAI:")[-1].strip()

    # Avvia thread per scarico modello
    threading.Thread(target=unload_model, daemon=True).start()

    return jsonify({"reply": reply})

# --- AVVIO ---
if __name__ == '__main__':
    print("🚀 ArcadiaAI Assistant avviato su http://localhost:5000")

    app.run(port=5000, debug=False)
