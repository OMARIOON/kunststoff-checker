import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import io
import base64
from openai import OpenAI

# Setup der Seite
st.set_page_config(page_title="KI-Zeichnungsprüfer (Kunststoff)", layout="wide")
st.title("🔍 PDF-Toleranz-Checker für Kunststoffteile")

# Sidebar für Einstellungen
with st.sidebar:
    st.header("Konfiguration")
    api_key = st.text_input("OpenAI API Key", type="password")
    norm_selection = st.selectbox("Norm wählen", ["ISO 20457", "DIN 16742", "Allgemeintoleranz Mittel"])
    st.info("Dieser Agent nutzt GPT-4o, um Zeichnungsinhalte visuell mit Industrienormen abzugleichen.")

# Datei-Upload
uploaded_file = st.file_uploader("Technische Zeichnung (PDF) hochladen", type=["pdf"])

def encode_image(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

if uploaded_file and api_key:
    client = OpenAI(api_key=api_key)
    
    # PDF in Bild umwandeln (Erste Seite)
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    page = doc.load_page(0)
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # Höhere Auflösung
    img_data = pix.tobytes("png")
    image = Image.open(io.BytesIO(img_data))
    
    st.image(image, caption="Hochgeladene Zeichnung", use_container_width=True)
    
    if st.button("Zeichnung jetzt prüfen"):
        with st.spinner("KI analysiert die Zeichnung auf Normeinhaltung..."):
            base64_image = encode_image(img_data)
            
            prompt = f"""
            Du bist ein Experte für Fertigungstechnik und Qualitätsmanagement im Kunststoffspritzguss.
            Analysiere diese technische Zeichnung. 
            Prüfe, ob die Toleranzangaben (Maßtoleranzen, Form- und Lagetoleranzen) der Norm {norm_selection} entsprechen.
            
            Beachte besonders:
            1. Sind die Toleranztabellen im Schriftfeld vorhanden?
            2. Passen die angegebenen Maße zu den üblichen Genauigkeitsgraden für Kunststoff (z.B. Reihe TG6)?
            3. Fehlen wichtige Angaben für die Kunststoffherstellung?
            
            Gib eine strukturierte Liste mit Fehlern oder Warnungen aus.
            """
            
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/png;base64,{base64_image}"}
                                },
                            ],
                        }
                    ],
                    max_tokens=1000,
                )
                
                st.subheader("Ergebnis der Prüfung:")
                st.markdown(response.choices[0].message.content)
                
            except Exception as e:
                st.error(f"Fehler bei der Analyse: {e}")

elif not api_key:
    st.warning("Bitte gib deinen OpenAI API Key in der Sidebar ein.")
