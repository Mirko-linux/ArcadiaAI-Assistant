# wake_word.py
import speech_recognition as sr
import threading
import time
import subprocess
import os

# --- CONFIGURAZIONE ---
WAKE_WORD = "ehi arcadia"  # Parola chiave (tutto minuscolo)
LISTENING_TIMEOUT = 5       # Massimo tempo di ascolto dopo wake word
SILENCE_TIMEOUT = 0.5       # Tempo di attesa prima di riprendere l'ascolto
DEVICE_INDEX = None         # Imposta se hai più microfoni (usa sr.Microphone.list_microphone_names())

# Riconoscitore
r = sr.Recognizer()
r.energy_threshold = 300    # Sensibilità (puoi regolarla)
r.dynamic_energy_threshold = True

def listen_for_wake_word():
    """Ascolta continuamente per la wake word"""
    print("👂 In ascolto per 'Ehi Arcadia'... (premi Ctrl+C per fermare)")
    while True:
        try:
            with sr.Microphone(device_index=DEVICE_INDEX) as source:
                r.adjust_for_ambient_noise(source, duration=0.5)  # Adatta al rumore ambiente
                print("🟢 Ascolto...", end="\r")

                # Ascolta una breve frase
                audio = r.listen(source, phrase_time_limit=2, timeout=5)

            # Riconoscimento offline con PocketSphinx
            text = r.recognize_sphinx(audio).lower()
            print(f"🎙️  Riconosciuto: '{text}'")

            if WAKE_WORD in text:
                print("✅ Wake word rilevata! Avvio assistente...")
                on_wake()

        except sr.UnknownValueError:
            # Audio non chiaro, ignora e continua
            pass
        except sr.RequestError as e:
            print(f"❌ Errore riconoscimento: {e}")
        except KeyboardInterrupt:
            print("\n👋 Interruzione rilevata. Uscita...")
            break
        except Exception as e:
            print(f"⚠️  Errore: {e}")

        # Breve pausa per ridurre carico CPU
        time.sleep(SILENCE_TIMEOUT)

def on_wake():
    """Aziona l'assistente principale (es. apri interfaccia Flask o fai partire chat vocale)"""
    # Opzione 1: Apri il browser
    # os.system("xdg-open http://localhost:5000")  # Linux
    # os.system("open http://localhost:5000")     # macOS
    # os.system("start http://localhost:5000")    # Windows

    # Opzione 2: Attiva un comando (es. suonare un beep)
    print("\a")  # Beep di conferma

    # Opzione 3: Invia un segnale al tuo server Flask (es. tramite WebSocket o file flag)
    # Es. crea un file temporaneo per segnalare il wake
    with open("wake_flag.txt", "w") as f:
        f.write("1")

    # Dopo 1 secondo, cancella il flag
    threading.Timer(1.0, lambda: os.remove("wake_flag.txt") if os.path.exists("wake_flag.txt") else None).start()

    # Opzione 4: Avvia un comando vocale (es. registrazione vera e propria con Whisper locale)
    # Qui puoi chiamare un altro script che usa il tuo modello Phi-2
    # subprocess.run(["python", "voice_command.py"])

# --- AVVIO ---
if __name__ == "__main__":
    listen_for_wake_word()
