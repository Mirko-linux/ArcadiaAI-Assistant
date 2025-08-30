# add_your_key.py

import json
import os
from pathlib import Path
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.scrollview import ScrollView
from kivy.app import App

# --- PERCORSI ---
BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "user_config.json"

# --- CONFIGURAZIONE DI DEFAULT ---
DEFAULT_CONFIG = {
    "openai_api_key": "",
    "anthropic_api_key": "",
    "gemini_api_key": "",
    "use_cloud_ai": False  # Disattivato di default
}

def load_config():
    """Carica la configurazione dall'utente (se esiste)"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Assicura che tutte le chiavi siano presenti
                for key in DEFAULT_CONFIG:
                    if key not in data:
                        data[key] = DEFAULT_CONFIG[key]
                return data
        except Exception as e:
            print(f"❌ Errore lettura config: {e}")
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()

def save_config(config):
    """Salva la configurazione in locale"""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"❌ Errore salvataggio: {e}")
        return False

# --- INTERFACCIA KIVY ---
class ApiKeyManager(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = 15
        self.spacing = 12
        self.size_hint_y = None
        self.bind(minimum_height=self.setter('height'))

        self.config = load_config()

        # --- Titolo ---
        self.add_widget(Label(
            text="🔐 API Key (Opzionale)",
            font_size=20,
            size_hint_y=None,
            height=40,
            bold=True
        ))

        # --- Avviso importante ---
        warning_text = (
            "⚠️ Attenzione: l'uso di API esterne comporta:\n"
            "• I tuoi messaggi verranno inviati ai server di OpenAI, Anthropic o Google\n"
            "• Potrebbero essere tracciati, archiviati o usati per addestramento\n"
            "• Accetti i ToS dei rispettivi provider\n\n"
            "🔐 Le chiavi sono salvate SOLO sul tuo dispositivo.\n"
            "ArcadiaAI non le legge né le invia a nessuno."
        )
        warning_label = Label(
            text=warning_text,
            color=(0.9, 0.6, 0.2, 1),
            font_size=13,
            halign="left",
            valign="top",
            text_size=(None, None),
            size_hint_y=None
        )
        warning_label.bind(texture_size=warning_label.setter('size'))
        self.add_widget(warning_label)

        # --- Toggle uso AI esterna ---
        toggle_layout = BoxLayout(size_hint_y=None, height=40, spacing=10)
        toggle_layout.add_widget(Label(
            text="Usa AI esterna:",
            size_hint_x=0.6
        ))
        self.use_cloud_toggle = ToggleButton(
            text="Sì" if self.config.get("use_cloud_ai", False) else "No",
            state="down" if self.config.get("use_cloud_ai", False) else "normal",
            size_hint_x=0.4
        )
        toggle_layout.add_widget(self.use_cloud_toggle)
        self.add_widget(toggle_layout)

        # --- OpenAI ---
        self.add_widget(Label(
            text="OpenAI API Key (GPT):",
            halign="left",
            size_hint_y=None,
            height=30
        ))
        self.openai_input = TextInput(
            password=True,
            text=self.config.get("openai_api_key", ""),
            multiline=False,
            hint_text="sk-...",
            size_hint_y=None,
            height=40
        )
        self.add_widget(self.openai_input)

        # --- Anthropic ---
        self.add_widget(Label(
            text="Anthropic API Key (Claude):",
            halign="left",
            size_hint_y=None,
            height=30
        ))
        self.anthropic_input = TextInput(
            password=True,
            text=self.config.get("anthropic_api_key", ""),
            multiline=False,
            hint_text="sk-ant-...",
            size_hint_y=None,
            height=40
        )
        self.add_widget(self.anthropic_input)

        # --- Google Gemini ---
        self.add_widget(Label(
            text="Google Gemini API Key:",
            halign="left",
            size_hint_y=None,
            height=30
        ))
        self.gemini_input = TextInput(
            password=True,
            text=self.config.get("gemini_api_key", ""),
            multiline=False,
            hint_text="AIza...",
            size_hint_y=None,
            height=40
        )
        self.add_widget(self.gemini_input)

        # --- Pulsanti ---
        btn_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        save_btn = Button(text="💾 Salva")
        save_btn.bind(on_press=self.save_keys)
        cancel_btn = Button(text="❌ Annulla")
        cancel_btn.bind(on_press=self.close_popup)
        btn_layout.add_widget(save_btn)
        btn_layout.add_widget(cancel_btn)
        self.add_widget(btn_layout)

    def save_keys(self, *args):
        """Salva le chiavi e aggiorna il config"""
        new_config = {
            "openai_api_key": self.openai_input.text.strip(),
            "anthropic_api_key": self.anthropic_input.text.strip(),
            "gemini_api_key": self.gemini_input.text.strip(),
            "use_cloud_ai": self.use_cloud_toggle.state == "down"
        }

        if save_config(new_config):
            # Mostra successo
            popup = Popup(
                title="✅ Salvato",
                content=Label(text="Chiavi API salvate in locale."),
                size_hint=(0.6, 0.3)
            )
            popup.open()
            # Chiudi dopo 1.5s
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: popup.dismiss(), 1.5)
            # Aggiorna stato
            self.config = new_config
        else:
            popup = Popup(
                title="❌ Errore",
                content=Label(text="Impossibile salvare il file."),
                size_hint=(0.6, 0.3)
            )
            popup.open()

    def close_popup(self, *args):
        """Chiude il popup corrente"""
        app = App.get_running_app()
        if app and app.root_window and app.root_window.children:
            app.root_window.children[0].dismiss()


# --- FUNZIONI PUBBLICHE ---
def show_api_key_manager():
    """Apre il popup per la gestione delle API Key"""
    scroll = ScrollView(size_hint=(0.9, 0.8))
    manager = ApiKeyManager()
    scroll.add_widget(manager)

    popup = Popup(
        title="🔑 Le tue API Key",
        content=scroll,
        size_hint=(0.95, 0.9)
    )
    popup.open()


def get_api_keys():
    """
    Restituisce le API key dell'utente.
    Usa: {'openai': '...', 'anthropic': '...', 'gemini': '...', 'use_cloud': True/False}
    """
    config = load_config()
    return {
        "openai": config.get("openai_api_key", "").strip(),
        "anthropic": config.get("anthropic_api_key", "").strip(),
        "gemini": config.get("gemini_api_key", "").strip(),
        "use_cloud": config.get("use_cloud_ai", False)
    }


def clear_api_keys():
    """Rimuove tutte le API key salvate"""
    config = load_config()
    config.update({
        "openai_api_key": "",
        "anthropic_api_key": "",
        "gemini_api_key": "",
        "use_cloud_ai": False
    })
    save_config(config)


def are_keys_set():
    """Restituisce True se almeno una chiave è impostata"""
    keys = get_api_keys()
    return any(keys[k] for k in ["openai", "anthropic", "gemini"])
