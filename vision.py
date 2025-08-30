# vision.py
# Analisi di immagini e PDF senza LLM aggiuntivi
# Usa OpenCV, Tesseract, PyPDF2, Exif

import cv2
import pytesseract
from PIL import Image, ExifTags
import os
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
import tempfile

def analyze_image(image_path):
    """Analizza un'immagine e restituisce una descrizione testuale"""
    try:
        # Apri l'immagine
        img = Image.open(image_path)

        # 1. Estrai metadati Exif (data, posizione, dispositivo)
        exif_data = {}
        try:
            for tag, value in img._getexif().items():
                tag_name = ExifTags.TAGS.get(tag, tag)
                exif_data[tag_name] = str(value)
        except:
            pass

        exif_text = ""
        if "DateTime" in exif_data:
            exif_text += f"📅 Scattata il: {exif_data['DateTime']}\n"
        if "GPSInfo" in exif_data:
            exif_text += "📍 Ha coordinate GPS\n"
        if "Model" in exif_data:
            exif_text += f"📱 Dispositivo: {exif_data['Model']}\n"

        # 2. Converti in OpenCV
        img_cv = cv2.imread(image_path)
        h, w, _ = img_cv.shape

        # 3. Rileva se è scura o chiara
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        brightness = gray.mean()
        lighting = "luminosa" if brightness > 100 else "scuro"

        # 4. Rileva colore dominante
        avg_color = img_cv.mean(axis=0).mean(axis=0)
        dominant_color = "verde" if avg_color[1] > avg_color[0] and avg_color[1] > avg_color[2] else \
                        "rosso" if avg_color[0] > avg_color[1] and avg_color[0] > avg_color[2] else \
                        "blu" if avg_color[2] > avg_color[0] and avg_color[2] > avg_color[1] else "neutro"

        # 5. OCR: estrai testo
        text = pytesseract.image_to_string(img_cv, lang='ita+eng')
        text = text.strip()
        ocr_text = f"📄 Testo trovato:\n{text}" if text else "❌ Nessun testo trovato nell'immagine."

        # 6. Descrizione finale
        description = (
            f"Questa è un'immagine di dimensioni {w}x{h} pixel, scattata in condizioni {lighting}.\n"
            f"Colore dominante: {dominant_color}.\n"
        )
        if exif_text:
            description += f"\nInformazioni aggiuntive:\n{exif_text}"
        description += f"\n{ocr_text}"

        return description

    except Exception as e:
        return f"❌ Errore nell'analisi dell'immagine: {e}"

def extract_text_from_pdf(pdf_path):
    """Estrai testo da un PDF (prima pagina)"""
    try:
        reader = PdfReader(pdf_path)
        if len(reader.pages) == 0:
            return "❌ PDF vuoto."

        # Estrai testo dalla prima pagina
        text = reader.pages[0].extract_text()
        if text.strip():
            return f"📄 Testo estratto (prima pagina):\n{text.strip()}"

        # Se OCR non funziona, converti in immagine e usa Tesseract
        with tempfile.TemporaryDirectory() as path:
            images = convert_from_path(pdf_path, single_file=True, output_folder=path)
            for image in images:
                temp_img = os.path.join(path, "temp.jpg")
                image.save(temp_img, "JPEG")
                text = pytesseract.image_to_string(temp_img, lang='ita+eng')
                if text.strip():
                    return f"📄 Testo estratto (OCR):\n{text.strip()}"
        return "❌ Nessun testo leggibile nel PDF."

    except Exception as e:
        return f"❌ Errore lettura PDF: {e}"

# --- FUNZIONE PRINCIPALE ---
def describe_attachment(file_path):
    """Descrive un allegato (immagine o PDF)"""
    ext = os.path.splitext(file_path)[1].lower()

    if ext in [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]:
        return analyze_image(file_path)
    elif ext == ".pdf":
        return extract_text_from_pdf(file_path)
    else:
        return "❌ Tipo di file non supportato. Solo immagini e PDF."
