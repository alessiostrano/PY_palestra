import streamlit as st
from PIL import Image
import numpy as np

st.title("💪 Fitness Tracker AI - DEMO")

st.info("""
### 🌐 Versione DEMO per Server Cloud

**Limitazioni Render:**
- ❌ Webcam non disponibile (server senza hardware)
- ❌ Audio non disponibile (server senza sistema audio)

**Come usare:**
1. Scatta una foto mentre fai un esercizio
2. Carica la foto qui sotto  
3. L'AI analizzerà la tua postura
""")

uploaded_file = st.file_uploader("📸 Carica una foto del tuo esercizio", type=['png', 'jpg', 'jpeg'])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Tua foto caricata")
    st.success("✅ Foto caricata! (Analisi YOLO11 sarà disponibile quando il modello sarà ottimizzato)")

st.info("🚀 **Per la versione COMPLETA con webcam e audio**: Usa Streamlit Community Cloud!")
