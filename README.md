# 💪 Fitness Tracker AI - REAL-TIME Edition

🎤 **Feedback vocale in tempo reale MENTRE fai l'esercizio!**

## 🚀 DUE SOLUZIONI COMPLETE

### 1. 📱 **Streamlit Cloud + Camera Input (CONSIGLIATA)**
- **Foto ogni 2-3 secondi** con st.camera_input
- **Feedback vocale immediato** "Perfetto!" / "Scendi di più!"
- **Funziona su cloud** senza webcam server
- **Cross-platform** Mac, Windows, Mobile

### 2. 💻 **App Desktop Locale**  
- **Webcam vera** con OpenCV continuo
- **Tracking real-time** 30 FPS
- **Solo per uso locale** (non deployabile su cloud)

## 🎤 FEEDBACK VOCALE SPECIFICO

### 🏋️ **Squat:**
- **"Perfetto! Continua così!"** ✅ Hip sotto ginocchia
- **"Scendi di più!"** ⚠️ Squat troppo alto  
- **"Allinea le ginocchia!"** ⚠️ Ginocchia storte
- **"Mettiti di lato alla camera"** ℹ️ Posizionamento

### 💪 **Push-up:**
- **"Perfetto! Ottima discesa!"** ✅ Gomiti sotto spalle
- **"Scendi di più! Push-up troppo alto!"** ⚠️ Range limitato
- **"Mantieni corpo dritto!"** ⚠️ Forma scorretta
- **"Mettiti di lato alla camera"** ℹ️ Posizionamento

### 🏋️‍♀️ **Bicep Curl:**
- **"Perfetto! Ottima flessione!"** ✅ Curl completo
- **"Fletti i gomiti!"** ⚠️ Range movimento piccolo
- **"Gomiti vicino al corpo!"** ⚠️ Stabilità gomiti
- **"Mettiti frontale alla camera"** ℹ️ Posizionamento

## 🚀 DEPLOY STREAMLIT CLOUD

### Files:
- `app_realtime.py` - Versione Streamlit con camera input
- `requirements.txt` - Include pyttsx3 per TTS  
- `packages.txt` - Include librerie espeak per TTS

### Steps:
1. **Upload** su GitHub repository
2. **https://share.streamlit.io/** → Deploy
3. **Carica YOLO11** + **Inizializza Audio**
4. **Inizia Real-Time** → **Scatta ogni 2-3 secondi**
5. **Feedback vocale immediato!** 🗣️

## 💻 USO LOCALE DESKTOP

### Requirements:
```bash
pip install ultralytics opencv-python pyttsx3 tkinter
```

### Run:
```bash
python app_desktop.py
```

## 🎯 COME FUNZIONA LA VERSIONE STREAMLIT

### **Setup Phase:**
1. **Carica YOLO11** (30-60s prima volta)
2. **Inizializza Audio** (TTS engine)  
3. **Seleziona esercizio** (Squat/Push-up/Curl)
4. **Clicca "INIZIA REAL-TIME"**

### **Training Phase:**
1. **st.camera_input** con key dinamica (auto-refresh)
2. **Scatta foto ogni 2-3 secondi** 📸
3. **YOLO11 analizza** keypoints in <1 secondo
4. **Feedback immediato** visivo + vocale
5. **Loop continuo** fino a "FERMA"

### **Feedback Types:**
- **Visual**: 🟢 Ottimo / 🟡 Migliorabile / 🔴 Errore  
- **Audio**: Istruzioni specifiche immediate
- **Stats**: Confidence e precision real-time

## 💡 VANTAGGI REAL-TIME

### **📸 Streamlit Cloud:**
- ✅ **Deploy ovunque** - nessun hardware speciale
- ✅ **Cross-platform** - Mac, Windows, Mobile  
- ✅ **Permission-based** - accesso camera sicuro
- ✅ **Scalabile** - funziona per tutti
- ✅ **Zero config** - nessuna installazione

### **💻 Desktop Locale:**  
- ✅ **Webcam continua** - 30 FPS real-time
- ✅ **Latenza zero** - processing locale
- ✅ **Privacy totale** - niente cloud
- ✅ **Performance** - hardware dedicato

## 🔧 TECHNICAL DETAILS

### **Analisi YOLO11:**
- **Keypoints COCO**: 17 punti corpo umano
- **Confidence threshold**: >0.5 per parti critiche  
- **Geometric analysis**: Calcoli angoli e distanze
- **Exercise-specific**: Algoritmi per ogni esercizio

### **TTS Integration:**
- **pyttsx3**: Cross-platform text-to-speech
- **Threading**: Non blocca UI durante speech
- **Rate limiting**: Evita spam vocale
- **Smart feedback**: Solo correzioni importanti

### **Real-time Logic:**
- **Photo interval**: 1-5 secondi configurabile
- **Analysis speed**: <1 secondo per foto
- **Memory efficient**: YOLO11n modello leggero
- **Error handling**: Robust failure recovery

---

**🎤 Il primo fitness tracker con feedback vocale in tempo reale! 💪**

*"Perfetto! Continua così!" - Your AI Personal Trainer*
