# 🚀 Deploy Guide - Streaming Real-Time

## 📹 Opzione 1: Simple Stream (CONSIGLIATA)

**Perfetta per Streamlit Cloud - Zero dipendenze extra**

### Files da deployare:
1. `app_simple_stream.py` → rinomina in `app.py`
2. `requirements_simple.txt` → rinomina in `requirements.txt`  
3. `packages.txt` → mantieni nome
4. `README.md` → mantieni nome

### Deploy:
1. Upload su GitHub repository
2. https://share.streamlit.io/ → New app
3. Connect repository → Deploy
4. **FUNZIONA IMMEDIATAMENTE!** 🎉

## 🏆 Opzione 2: WebRTC Stream (Premium)

**Per esperienza streaming professionale**

### Files da deployare:
1. `app_streaming.py` → rinomina in `app.py`
2. `requirements_webrtc.txt` → rinomina in `requirements.txt`
3. `packages.txt` → mantieni nome

### Note WebRTC:
- Richiede `streamlit-webrtc>=0.47.0`
- Potrebbe avere problemi su alcuni cloud
- Ottimo per deploy locale o server dedicati

## 🎯 Utilizzo Post-Deploy

### Setup Iniziale:
1. **Carica YOLO11** (30-60s prima volta)
2. **Test Audio** per verificare TTS browser
3. **Configura esercizio** e intervalli

### Sessione Allenamento:
1. **INIZIA STREAM** ▶️
2. **Consenti webcam** browser  
3. **Camera rimane aperta** 📹
4. **Allenati con feedback vocale!** 🗣️

## 💡 Troubleshooting

### Camera non si apre:
- Permissions browser per webcam
- Refresh pagina e riprova
- Controlla altre app usando camera

### Audio non funziona:
- Browser deve supportare Web Speech API
- Verifica volume sistema/browser
- Test con "🔊 Test Audio"

### Performance lenta:
- Normale su prima analisi YOLO11
- Riduci intervallo feedback (3-5 secondi)
- Refresh browser se necessario

---

**💪 Ready to stream your workout! 📹**
