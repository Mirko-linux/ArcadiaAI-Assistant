# ArcadiaAI-Assistant

[![License: MPL 2.0](https://img.shields.io/badge/License-MPL%202.0-brightgreen.svg)](https://opensource.org/licenses/MPL-2.0)
[![F-Droid Friendly](https://img.shields.io/badge/F--Droid-friendly-brightgreen)](https://f-droid.org)
[![Kivy](https://img.shields.io/badge/Powered_by-Kivy-blue)](https://kivy.org)

ArcadiaAI Assistant è un assistente virtuale che funziona **senza google**, **tracciamento**, e **connessione ad internet** (tranne per la ricerca su internet e la generazione di immagini).
Perfetto per dispositivi senza Google Services (Huawei, /e/, GrapheneOS, LineageOS)

---
## Caratteristiche
ArcadiaAI Assistant si basa su [ArcadiaAI](https://github.com/Mirko-linux/ArcadiaAI), ma a differenza di esso, Assistant usa Phi 3 Mini, un piccolo modello locale da 3B di parametri porigettato per essere eseguito su cellulari di fascia media. 
Il modello verrà installato automaticamente assieme all'app e verrà eseguito solo quando questa è attiva risparmiando notevolmente sulle risorse del telefono.

### Funzionalità principali
- **Wake word**: "Ehi Arcadia" (con Vosk)
- **IA locale**: Phi-3-mini 3.8B (ONNX)
- **Generazione immagini** con Pollinations.ai
- **Ricerca web** (DuckDuckGo)
- **Supporto allegati** (testo, immagini)
- **Comandi offline**: meteo, data, mappe OSM
- **Nessuna API esterna di default**
- **Interfaccia moderna**

---

## API Key (Opzionale)

Oltre al modello locale Phi-3-mini, puoi scegliere di utilizzare modelli cloud avanzati come GPT (OpenAI), Claude (Anthropic) o Google Gemini, inserendo la tua API Key personale. 

> Questa funzione è completamente opzionale e disattivata di default.

L’uso di API esterne comporta: 

-   I tuoi messaggi verranno inviati ai server di OpenAI, Anthropic o Google
-   Potrebbero essere tracciati, archiviati o usati per l’addestramento dei loro modelli
-   Acetti i Termini di Servizio (ToS) di ciascun provider
     
> ArcadiaAI Assistant non è responsabile dell’uso che questi servizi fanno dei tuoi dati

---
