# main.py

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.clock import mainthread
import threading
import time
import webbrowser
import os
import sys
from pathlib import Path
from cython import compile_file
from jnius import autoclass, cast

# --- GESTIONE CONFIGURAZIONE ---
import json
from pathlib import Path

# --- PERCORSI ---
BASE_DIR = Path(__file__).parent
APP_PY = BASE_DIR / "app.py"
GUI_PATH = BASE_DIR / "gui.html"
CONFIG_FILE = BASE_DIR / "user_config.json"

DEFAULT_CONFIG = {
    "model_version": "balanced",
    "use_cloud": False,
    "wake_word_enabled": True
}

def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"❌ Errore salvataggio: {e}")
        return False

# Carica la configurazione all'avvio
config = load_config()



# --- IMPORTA MODULI DI LOGICA (senza interfaccia) ---
from add_your_key import show_api_key_manager, get_api_keys

# --- IDENTITÀ ---
CES_IDENTITY = {
    "name": "ArcadiaAI Assistant",
    "creator": "Mirko Yuri Donato",
    "version": "3.5",
    "model": "Phi-3-mini (simulato)",
    "license": "MPL 2.0",
    "repository": "https://github.com/Mirko-linux/ArcadiaAI-Assistant"
}

# --- PAROLE BANNATE (anti-abuso) ---
PAROLE_BANNATE = []

MODEL_CONFIGS = {
    "full": {
        "url": "https://huggingface.co/microsoft/Phi-3-mini-4K-instruct-onnx/resolve/main/cpu-and-gpu-fp16/model.onnx",
        "path": "assets/models/phi3-full.onnx",
        "description": "Alta qualità, richiede 4GB+ RAM"
    },
    "balanced": {
        "url": "https://huggingface.co/microsoft/Phi-3-mini-4K-instruct-onnx/resolve/main/cpu-int4-rtn-block-128/model.onnx",
        "path": "assets/models/phi3-balanced.onnx",
        "description": "Qualità e velocità bilanciate"
    },
    "light": {
        "url": "https://huggingface.co/microsoft/Phi-3-mini-4K-instruct-onnx/resolve/main/cpu-int4-rtn-block-32/model.onnx",
        "path": "assets/models/phi3-light.onnx",
        "description": "Leggera, per dispositivi con poca RAM"
    }
}

# --- COMANDI SAC ---
SAC_COMMANDS = {
    "aiuto": "Mostra i comandi",
    "info": "Informazioni su ArcadiaAI",
    "cerca [query]": "Cerca su web",
    "immagine [descrizione]": "Genera un'immagine",
    "mappe [luogo]": "Mostra una mappa",
    "app [nome]": "Cerca un'app",
    "data": "Mostra data e ora",
    "codice_sorgente": "Link al codice sorgente",
    "telegraph [testo]": "Pubblica su Telegraph",
    "telegram [link] [testo]": "Invia a un canale Telegram",
    "esporta": "Esporta la chat"
}

# --- BACKEND CES-IMAGE ---
CES_IMAGE_API = "https://arcadiaai.onrender.com/api/ces-image"

# --- SIMULAZIONE LLM ---
def generate_phi3(prompt):
    simple_responses = {
        "ciao": "Ciao! Sono ArcadiaAI, il tuo assistente intelligente. 😊",
        "come stai": "Sto benissimo, grazie per chiedere! Sono qui per aiutarti.",
        "chi ti ha creato": "Sono stato creato da Mirko Yuri Donato con tanto amore per il software libero!",
        "grazie": "Di nulla! Sono felice di esserti stato d'aiuto. 😊"
    }
    for key in simple_responses:
        if key in prompt.lower():
            return simple_responses[key]
    return "Ho elaborato la tua richiesta. Per funzionalità avanzate, usa i comandi come '@aiuto'."

from urllib.parse import quote_plus

def get_installed_apps():
    """Restituisce una lista di app installate: [{'name': 'WhatsApp', 'package': 'com.whatsapp'}]"""
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    activity = PythonActivity.mActivity
    pm = activity.getPackageManager()

    apps = []
    packages = pm.getInstalledPackages(0)
    for package_info in packages:
        package_info = cast('android.content.pm.PackageInfo', package_info)
        app_name = package_info.applicationInfo.loadLabel(pm)
        package_name = package_info.packageName
        # Escludi app di sistema non apribili
        if "android" not in package_name and not package_name.startswith("com.android."):
            apps.append({
                "name": app_name.lower(),
                "package": package_name
            })
    return apps

def open_app_by_name(app_name):
    """Apre un'app per nome (es. 'whatsapp', 'telegram')"""
    app_name = app_name.lower().strip()
    
    # Ottieni lista app installate
    try:
        apps = get_installed_apps()
    except Exception as e:
        return f"❌ Errore lettura app: {e}"

    # Cerca corrispondenza (anche parziale)
    for app in apps:
        if app_name in app["name"] or app["name"] in app_name:
            try:
                Intent = autoclass('android.content.Intent')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                activity = PythonActivity.mActivity
                
                intent = activity.getPackageManager().getLaunchIntentForPackage(app["package"])
                if intent:
                    activity.startActivity(intent)
                    return f"✅ Aperto {app['name'].title()}"
                else:
                    return f"❌ Impossibile avviare {app['name']}"
            except Exception as e:
                return f"❌ Errore: {e}"
    
    return f"❌ App '{app_name}' non trovata"

# --- WAKE-WORD: "EHI ARCADIA" (solo Android) ---
wake_word_enabled = False

if hasattr(sys, 'getandroidapilevel'):  # Rileva Android
    try:
        from vosk import Model, KaldiRecognizer
        import sounddevice as sd
        import queue

        VOSK_MODEL_PATH = str(BASE_DIR / "assets" / "models" / "vosk-model-small-it")
        if os.path.exists(VOSK_MODEL_PATH):
            vosk_model = Model(VOSK_MODEL_PATH)
            recognizer = KaldiRecognizer(vosk_model, 16000)
            audio_queue = queue.Queue()
            wake_word_enabled = True

            def listen_for_wake():
                with sd.InputStream(samplerate=16000, channels=1, callback=lambda indata, *args: audio_queue.put(bytes(indata)), blocksize=8000):
                    while True:
                        data = audio_queue.get()
                        if recognizer.AcceptWaveform(data):
                            text = recognizer.Result()[14:-3].lower()
                            if "ehi arcadia" in text:
                                print("✅ Wake word rilevata!")
                                # Puoi inviare un evento a Flask
                                requests.post("http://localhost:5000/wake", json={"detected": True})
            threading.Thread(target=listen_for_wake, daemon=True).start()
    except Exception as e:
        print(f"❌ Vosk non disponibile: {e}")

# --- SINTESI VOCALE (TTS) ---
try:
    from gtts import gTTS
    import pygame
    pygame.mixer.init()
    def speak_text(text):
        try:
            tts = gTTS(text=text, lang='it', slow=False)
            filepath = str(BASE_DIR / "speech.mp3")
            tts.save(filepath)
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
        except Exception as e:
            print("❌ TTS fallito:", e)
except:
    def speak_text(text):
        print(f"[TTS] {text}")
def show_model_choice_popup():
    from kivy.uix.popup import Popup
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.label import Label
    from kivy.uix.button import Button

    layout = BoxLayout(orientation='vertical', padding=15, spacing=10)

    layout.add_widget(Label(
        text="🔧 Scegli la versione del modello:",
        size_hint_y=None,
        height=40
    ))

    # Carica configurazione
    config = load_config()

    for key, info in MODEL_CONFIGS.items():
        btn = Button(
            text=f"{key.capitalize()}\n{info['description']}",
            size_hint_y=None,
            height=80
        )
        if config.get("model_version") == key:
            btn.background_color = (0.1, 0.6, 0.9, 1)  # Blu selezionato
            btn.color = (1, 1, 1, 1)

        def on_press(k=key):
            config["model_version"] = k
            save_config(config)
            App.get_running_app().chatbox.add_message(f"✅ Modello impostato su {k}. Riavvia per applicare.")
            popup.dismiss()

        btn.bind(on_press=on_press)
        layout.add_widget(btn)

    popup = Popup(
        title="Versione modello",
        content=layout,
        size_hint=(0.9, 0.8)
    )
    popup.open()

phi3_session = None
phi3_tokenizer = None

def load_phi3_model():
    global phi3_session, phi3_tokenizer

    config = load_config()
    model_key = config.get("model_version", "balanced")
    model_info = MODEL_CONFIGS[model_key]

    if not os.path.exists(model_info["path"]):
        App.get_running_app().chatbox.add_message(
            f"⚠️ Modello {model_key} non trovato. Usa `@aiuto` per scaricarlo."
        )
        return None, None

    try:
        from transformers import AutoTokenizer
        import onnxruntime as ort

        print(f"🔄 Caricamento modello: {model_key}...")
        phi3_tokenizer = AutoTokenizer.from_pretrained("microsoft/Phi-3-mini-4K-instruct")
        phi3_session = ort.InferenceSession(
            model_info["path"],
            providers=['CPUExecutionProvider']
        )
        print("✅ Modello caricato!")
        return phi3_session, phi3_tokenizer
    except Exception as e:
        print(f"❌ Errore caricamento: {e}")
        return None, None
    


# --- GESTIONE COMANDI ---
def handle_sac_command(command, argument=""):
    command = command.lower().strip()
    if command == "apri" and argument:
        return open_app_by_name(argument)
    if command == "aiuto":
        return "[b]🎯 Comandi disponibili:[/b]\n" + "\n".join([f"- [i]@{cmd}[/i] → {desc}" for cmd, desc in SAC_COMMANDS.items()])
    elif command == "info":
        return f"[b]ℹ️ {CES_IDENTITY['name']} v{CES_IDENTITY['version']}[/b]\n• Creatore: {CES_IDENTITY['creator']}\n• Modello: {CES_IDENTITY['model']}\n• [ref={CES_IDENTITY['repository']}][color=0000ff]Codice sorgente[/color][/ref]"
    elif command == "data":
        from datetime import datetime
        return f"📅 Oggi è {datetime.now().strftime('%d/%m/%Y, %H:%M')}"
    elif command == "modello":
        if not argument:
            current = config.get("model_version", "balanced")
            return (
                f"🔧 **Modello attuale**: {current}\n\n"
                "Disponibili:\n"
                "• `@modello completa`\n"
                "• `@modello bilanciata`\n"
                "• `@modello leggera`\n\n"
                "Usa `@aiuto` per scaricare il modello scelto."
            )
        elif argument in ["completa", "bilanciata", "leggera"]:
            config["model_version"] = {"completa": "full", "bilanciata": "balanced", "leggera": "light"}[argument]
            save_config(config)
            return f"✅ Modello impostato su **{argument}**. Riavvia per applicare."
        else:
            return "❌ Usa: `@modello [completa|bilanciata|leggera]`"
    elif command == "cerca" and argument:
        try:
            from duckduckgo_search import ddg
            results = ddg(argument, max_results=3)
            return "\n".join([f"[ref={r['href']}][color=0000ff][u]{r['title']}[/u][/color][/ref]" for r in results])
        except:
            return "❌ Ricerca fallita."
    elif command == "immagine" and argument:
        if not argument:
            return "❌ Specifica cosa disegnare."
        if any(parola in argument.lower() for parola in PAROLE_BANNATE):
            return "❌ Questo prompt non è consentito."
        try:
            import requests
            response = requests.post(CES_IMAGE_API, json={"prompt": argument}, timeout=20)
            if response.status_code == 200:
                data = response.json()
                return "__IMAGE__:" + data.get("image_url") if data.get("image_url") else "⚠️ Nessuna immagine."
            return f"❌ Errore API: {response.status_code}"
        except Exception as e:
            return f"❌ Errore: {e}"
    else:
        return "❌ Comando non riconosciuto. Usa `@aiuto`."
    
# --- AVVIA IL SERVER FLASK ---
def start_flask_server():
    import subprocess
    subprocess.Popen([sys.executable, str(APP_PY)], cwd=BASE_DIR)

# --- APP KIVY (SOLO LAUNCHER) ---
class ArcadiaAIApp(App):
    def build(self):
        Window.clearcolor = (0.9, 0.95, 1, 1)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        # Titolo
        layout.add_widget(Label(
            text="[b]ArcadiaAI Assistant[/b]",
            markup=True,
            font_size=24,
            color=(0.1, 0.3, 0.6, 1),
            size_hint_y=None,
            height=60
        ))

        # Pulsante "Avvia Assistente"
        start_btn = Button(
            text="🚀 Avvia Assistente",
            font_size=18,
            size_hint_y=None,
            height=60,
            background_color=(0.1, 0.5, 0.8, 1),
            color=(1, 1, 1, 1)
        )
        start_btn.bind(on_press=self.start_assistant)
        layout.add_widget(start_btn)

        # Pulsante "API Esterne"
        keys_btn = Button(
            text="🔑 API Esterne (opzionale)",
            font_size=16,
            size_hint_y=None,
            height=50,
            background_color=(0.9, 0.9, 0.9, 1),
            color=(0.2, 0.2, 0.2, 1)
        )
        keys_btn.bind(on_press=lambda x: show_api_key_manager())
        layout.add_widget(keys_btn)

        # Stato
        self.status = Label(
            text="Pronto",
            font_size=14,
            color=(0.5, 0.5, 0.5, 1),
            size_hint_y=None,
            height=40
        )
        layout.add_widget(self.status)

        return layout

    def start_assistant(self, *args):
        self.status.text = "Avvio server..."
        threading.Thread(target=start_flask_server, daemon=True).start()
        time.sleep(2)
        webbrowser.open("http://localhost:5000")
        self.status.text = "✅ Aperto in browser!"

# --- AVVIO ---
if __name__ == '__main__':
    ArcadiaAIApp().run()
