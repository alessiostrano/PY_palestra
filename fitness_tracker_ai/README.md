# 💪 Fitness Tracker AI

Un'applicazione web avanzata per il monitoraggio degli esercizi fisici in tempo reale usando visione artificiale e feedback audio.

## 🎯 Caratteristiche Principali

- **Rilevamento Pose in Tempo Reale**: Utilizza MediaPipe per tracciare i movimenti del corpo
- **Riconoscimento Esercizi**: Supporta squat, push-up e curl bicipiti
- **Valutazione Postura**: Analizza la correttezza della forma dell'esercizio
- **Conteggio Automatico**: Conta le ripetizioni solo quando eseguite correttamente
- **Feedback Audio**: Fornisce suggerimenti vocali personalizzati in tempo reale
- **Interfaccia Web**: Completamente utilizzabile via browser con Streamlit

## 🛠️ Installazione

### Prerequisiti

- Python 3.8 o superiore
- Webcam funzionante
- Cuffie o altoparlanti per l'audio feedback

### Installazione Dipendenze

```bash
pip install -r requirements.txt
```

### Possibili Problemi di Installazione

**Su Windows:**
```bash
# Se hai problemi con pyttsx3
pip install pywin32

# Se hai problemi con OpenCV
pip install opencv-python-headless
```

**Su macOS:**
```bash
# Installa le dipendenze di sistema
brew install portaudio

# Se hai problemi con pyttsx3
pip install pyobjc-framework-Cocoa
```

**Su Linux:**
```bash
# Installa le dipendenze audio
sudo apt-get install espeak espeak-data libespeak-dev ffmpeg

# Dipendenze per OpenCV
sudo apt-get install python3-opencv
```

## 🚀 Utilizzo

### Avvio dell'Applicazione

```bash
streamlit run app.py
```

L'applicazione si aprirà automaticamente nel browser all'indirizzo `http://localhost:8501`

### Uso dell'Interfaccia

1. **Selezione Esercizio**: Scegli l'esercizio dalla barra laterale
2. **Configurazione Audio**: Regola velocità e volume del feedback vocale
3. **Avvio Tracking**: Clicca "Inizia" per attivare la webcam
4. **Posizionamento**: Assicurati che tutto il corpo sia visibile nella camera
5. **Esecuzione**: Inizia l'esercizio - il sistema fornirà feedback in tempo reale

### Esercizi Supportati

#### 🏋️ Squat
- **Posizione**: Piedi alla larghezza delle spalle
- **Movimento**: Scendi mantenendo la schiena dritta
- **Feedback**: "Scendi di più", "Mantieni la schiena dritta"

#### 💪 Push-up
- **Posizione**: Plank con braccia tese
- **Movimento**: Scendi fino a toccare quasi il pavimento
- **Feedback**: "Scendi di più", "Mantieni il corpo dritto"

#### 🏋️‍♀️ Curl Bicipiti
- **Posizione**: In piedi con braccia lungo i fianchi
- **Movimento**: Fletti i gomiti mantenendoli vicini al corpo
- **Feedback**: "Mantieni i gomiti vicino al corpo"

## 📁 Struttura del Progetto

```
fitness-tracker/
├── app.py                    # Applicazione Streamlit principale
├── pose_detection.py         # Modulo rilevamento pose
├── posture_evaluation.py     # Modulo valutazione postura
├── repetition_counter.py     # Modulo conteggio ripetizioni
├── audio_feedback.py         # Modulo feedback audio
├── requirements.txt          # Dipendenze Python
└── README.md                # Questo file
```

## 🔧 Configurazione Avanzata

### Personalizzazione Audio

Nel file `audio_feedback.py` puoi modificare:
- Velocità di pronuncia (rate)
- Volume audio
- Lingua del TTS (se supportata dal sistema)
- Frequenza dei messaggi

### Soglie degli Esercizi

Nel file `posture_evaluation.py` puoi regolare:
- Angoli minimi e massimi per ogni esercizio
- Tolleranze per l'allineamento del corpo
- Soglie di correttezza

### Parametri di Rilevamento

Nel file `pose_detection.py` puoi modificare:
- Confidenza minima per il rilevamento
- Confidenza minima per il tracking
- Risoluzione della webcam

## 🐛 Risoluzione Problemi

### Webcam Non Rilevata
```python
# Prova a cambiare l'indice della webcam in app.py
self.webcam = cv2.VideoCapture(1)  # Invece di 0
```

### Audio Non Funzionante
- Verifica che le cuffie/altoparlanti siano collegati
- Su Linux, installa: `sudo apt-get install pulseaudio`
- Su Windows, verifica i driver audio

### Performance Lente
- Riduci la risoluzione della webcam
- Chiudi altre applicazioni che usano la webcam
- Verifica che il computer abbia risorse sufficienti

### Rilevamento Pose Impreciso
- Assicurati di avere buona illuminazione
- Indossa abiti aderenti e di colore contrastante
- Mantieni tutto il corpo nel frame della camera

## 📊 Metriche e Statistiche

L'applicazione traccia:
- **Ripetizioni Totali**: Conteggio delle ripetizioni completate
- **Percentuale Forma Corretta**: % di movimenti eseguiti correttamente
- **Fasi Tracciate**: Numero di fasi di movimento analizzate

## 🛡️ Privacy e Sicurezza

- **Tutti i dati vengono processati localmente**
- **Nessuna immagine o video viene salvato**
- **Nessun dato viene trasmesso online**
- **La webcam è attiva solo durante l'uso dell'applicazione**

## 🔄 Aggiornamenti Futuri

Possibili miglioramenti:
- [ ] Supporto per più esercizi
- [ ] Salvataggio sessioni di allenamento
- [ ] Grafici di progresso
- [ ] Modalità allenamento guidato
- [ ] Integrazione con dispositivi fitness
- [ ] Rilevamento automatico tipo di esercizio

## 📝 Note Tecniche

### Requisiti Hardware Minimi
- **CPU**: Dual-core 2.0 GHz
- **RAM**: 4 GB
- **Webcam**: 720p o superiore
- **Audio**: Cuffie/altoparlanti

### Prestazioni Ottimali
- **CPU**: Quad-core 3.0 GHz o superiore
- **RAM**: 8 GB o superiore
- **Webcam**: 1080p con buona illuminazione

## 🆘 Supporto

In caso di problemi:
1. Verifica che tutte le dipendenze siano installate
2. Controlla che la webcam funzioni con altre applicazioni
3. Verifica che l'audio funzioni correttamente
4. Prova a riavviare l'applicazione
5. Controlla i log di errore nella console

## 📜 Licenza

Questo progetto è rilasciato sotto licenza MIT. Consulta il file LICENSE per i dettagli.

---

**Buon allenamento! 💪🏋️‍♀️**
