# 🚀 Deploy Instructions

## 📱 Streamlit Cloud (Consigliata)

1. **Upload files** su GitHub:
   - `app_realtime.py` → rinomina in `app.py`
   - `requirements.txt`
   - `packages.txt`
   - `README.md`

2. **Deploy**: https://share.streamlit.io/
   - New app → Connect repository
   - Deploy automatico

3. **Utilizzo**:
   - Carica YOLO11 → Inizializza Audio
   - Seleziona esercizio → Inizia Real-Time
   - Scatta foto ogni 2-3 secondi
   - **Ascolta feedback vocale immediato!**

## 💻 Desktop Locale

1. **Install**:
   ```bash
   pip install -r desktop_requirements.txt
   ```

2. **Run**:
   ```bash
   python app_desktop.py
   ```

3. **Utilizzo**:
   - Seleziona esercizio → Start
   - Webcam finestra OpenCV
   - Feedback vocale automatico
   - ESC per uscire

## 🎤 Audio Requirements

### Streamlit Cloud:
- Browser deve supportare Web Speech API
- Cuffie/altoparlanti consigliati
- Permessi audio browser

### Desktop:
- Sistema audio funzionante
- Microfono non richiesto (solo output)
- Driver audio standard

---

**💪 Ready to train with AI voice coaching!**
