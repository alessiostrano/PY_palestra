"""
Fitness Tracker AI - Real-Time con Web Speech API
Usa il TTS del BROWSER invece del server per feedback vocale
"""
import streamlit as st
import numpy as np
import time
from PIL import Image
import os
import json

# Environment setup
os.environ.setdefault('YOLO_CONFIG_DIR', '/tmp')
os.environ.setdefault('WANDB_DISABLED', 'true')

def load_yolo_model():
    """Carica YOLO11"""
    try:
        from ultralytics import YOLO
        with st.spinner("🤖 Caricamento YOLO11..."):
            model = YOLO('yolo11n-pose.pt')
            test_img = np.zeros((480, 640, 3), dtype=np.uint8)
            _ = model(test_img, verbose=False, save=False)
        return model
    except Exception as e:
        st.error(f"❌ Errore YOLO11: {e}")
        return None

def analyze_pose_for_exercise(keypoints, confidence, exercise_type):
    """Analisi specifica per esercizio con feedback vocale"""
    if keypoints is None or len(keypoints) == 0:
        return "❓ Nessuna persona rilevata", "", "neutral"

    try:
        feedback_text = ""
        voice_feedback = ""
        status = "neutral"

        if confidence is not None and len(confidence) > 16:
            # Calcola confidence per parti del corpo
            shoulders_conf = (confidence[5] + confidence[6]) / 2
            elbows_conf = (confidence[7] + confidence[8]) / 2  
            hips_conf = (confidence[11] + confidence[12]) / 2
            knees_conf = (confidence[13] + confidence[14]) / 2

            if exercise_type == "squat":
                if knees_conf > 0.6 and hips_conf > 0.6:
                    hip_y = (keypoints[11][1] + keypoints[12][1]) / 2
                    knee_y = (keypoints[13][1] + keypoints[14][1]) / 2

                    if hip_y > knee_y:
                        feedback_text = "🟢 SQUAT PROFONDO - Ottima forma!"
                        voice_feedback = "Perfetto! Continua così!"
                        status = "excellent"
                    elif hip_y > knee_y * 0.95:
                        feedback_text = "🟡 Scendi un po' di più"
                        voice_feedback = "Scendi ancora un po'"
                        status = "good"
                    else:
                        feedback_text = "🔴 SCENDI DI PIÙ! Hip sopra ginocchia"
                        voice_feedback = "Scendi di più! Hip sopra le ginocchia!"
                        status = "needs_work"

                    # Controlla allineamento
                    left_knee_x = keypoints[13][0]
                    right_knee_x = keypoints[14][0]
                    if abs(left_knee_x - right_knee_x) > 0.3:
                        feedback_text += " ⚠️ Allinea meglio le ginocchia"
                        voice_feedback += " Allinea le ginocchia!"

                else:
                    feedback_text = "⚠️ Posizionati di LATO per miglior rilevamento"
                    voice_feedback = "Mettiti di lato alla camera"
                    status = "positioning"

            elif exercise_type == "pushup":
                if shoulders_conf > 0.6 and elbows_conf > 0.6:
                    shoulder_y = (keypoints[5][1] + keypoints[6][1]) / 2
                    elbow_y = (keypoints[7][1] + keypoints[8][1]) / 2

                    if elbow_y > shoulder_y:
                        feedback_text = "🟢 PUSH-UP COMPLETO - Ottima discesa!"
                        voice_feedback = "Perfetto! Ottima discesa!"
                        status = "excellent"
                    elif elbow_y > shoulder_y * 0.9:
                        feedback_text = "🟡 Scendi un po' di più"
                        voice_feedback = "Scendi ancora"
                        status = "good"
                    else:
                        feedback_text = "🔴 SCENDI DI PIÙ! Push-up troppo alto"
                        voice_feedback = "Scendi di più! Push-up troppo alto!"
                        status = "needs_work"

                else:
                    feedback_text = "⚠️ Posizionati di LATO per miglior rilevamento" 
                    voice_feedback = "Mettiti di lato alla camera"
                    status = "positioning"

            elif exercise_type == "bicep_curl":
                if elbows_conf > 0.6 and shoulders_conf > 0.6:
                    left_elbow_y = keypoints[7][1]
                    left_wrist_y = keypoints[9][1]
                    left_shoulder_y = keypoints[5][1]

                    if left_wrist_y < left_elbow_y < left_shoulder_y:
                        feedback_text = "🟢 CURL COMPLETO - Ottima flessione!"
                        voice_feedback = "Perfetto! Ottima flessione!"
                        status = "excellent"
                    elif left_wrist_y < left_elbow_y:
                        feedback_text = "🟡 Fletti un po' di più"
                        voice_feedback = "Fletti di più"
                        status = "good"
                    else:
                        feedback_text = "🔴 FLETTI I GOMITI! Movimento troppo piccolo"
                        voice_feedback = "Fletti i gomiti! Movimento troppo piccolo!"
                        status = "needs_work"

                    # Controlla stabilità gomiti
                    left_elbow_x = keypoints[7][0]
                    left_shoulder_x = keypoints[5][0]

                    if abs(left_elbow_x - left_shoulder_x) > 0.1:
                        feedback_text += " ⚠️ Mantieni gomiti vicino al corpo"
                        voice_feedback += " Gomiti vicino al corpo!"

                else:
                    feedback_text = "⚠️ Posizionati FRONTALE per miglior rilevamento"
                    voice_feedback = "Mettiti frontale alla camera"
                    status = "positioning"

        return feedback_text, voice_feedback, status

    except Exception as e:
        return f"❌ Errore analisi: {str(e)}", "", "error"

def speak_with_web_api(message):
    """Usa Web Speech API del browser per parlare"""
    if message:
        # Escape delle virgolette per JavaScript
        safe_message = message.replace("'", "\'").replace('"', '\"')

        # JavaScript per Web Speech API
        speak_js = f"""
        <script>
        function speak() {{
            if ('speechSynthesis' in window) {{
                const utterance = new SpeechSynthesisUtterance('{safe_message}');
                utterance.rate = 1.0;
                utterance.volume = 0.8;
                utterance.pitch = 1.0;
                utterance.lang = 'it-IT';
                speechSynthesis.speak(utterance);
            }} else {{
                console.log('TTS non supportato: {safe_message}');
            }}
        }}
        speak();
        </script>
        """

        # Mostra lo script per l'esecuzione
        st.components.v1.html(speak_js, height=0)

def main():
    st.set_page_config(
        page_title="💪 Fitness Tracker AI - Web TTS",
        page_icon="💪",
        layout="wide"
    )

    st.title("💪 Fitness Tracker AI - REAL TIME")
    st.subheader("🎤 Con Web Speech API (Funziona su Cloud!)")

    # Inizializza session state
    if 'model' not in st.session_state:
        st.session_state.model = None
    if 'realtime_mode' not in st.session_state:
        st.session_state.realtime_mode = False
    if 'last_feedback_time' not in st.session_state:
        st.session_state.last_feedback_time = 0
    if 'speech_enabled' not in st.session_state:
        st.session_state.speech_enabled = True

    # Test Web Speech API
    st.info("""
    ### 🔊 Web Speech API 

    Questa versione usa il **TTS del tuo browser** invece del server!

    **Compatibile con:**
    - ✅ Chrome, Firefox, Safari, Edge
    - ✅ Desktop e Mobile
    - ✅ Streamlit Cloud
    """)

    # Test audio
    if st.button("🔊 Test Audio Browser"):
        speak_with_web_api("Sistema audio browser funzionante!")
        st.success("✅ Test audio inviato al browser!")

    # Sidebar
    st.sidebar.header("⚙️ Controlli Real-Time")

    # Audio settings
    st.session_state.speech_enabled = st.sidebar.checkbox("🔊 Feedback Vocale", value=True)

    # Carica modello
    if st.sidebar.button("🤖 Carica YOLO11", type="primary"):
        st.session_state.model = load_yolo_model()
        if st.session_state.model:
            st.sidebar.success("✅ YOLO11 Pronto!")
            if st.session_state.speech_enabled:
                speak_with_web_api("YOLO11 caricato! Sistema pronto!")

    # Status modello
    if st.session_state.model:
        st.sidebar.success("🤖 YOLO11 Ready")

    # Selezione esercizio
    exercise_type = st.sidebar.selectbox(
        "🎯 Esercizio:",
        ["squat", "pushup", "bicep_curl"],
        format_func=lambda x: {"squat": "🏋️ Squat", "pushup": "💪 Push-up", "bicep_curl": "🏋️‍♀️ Curl"}[x]
    )

    # Velocità feedback
    feedback_interval = st.sidebar.slider("🔄 Feedback ogni X secondi", 1, 5, 3)

    # Modalità real-time
    col1, col2 = st.columns(2)

    with col1:
        if st.button("▶️ INIZIA REAL-TIME", type="primary", disabled=not st.session_state.model):
            st.session_state.realtime_mode = True
            if st.session_state.speech_enabled:
                speak_with_web_api(f"Iniziamo con {exercise_type}! Preparati!")

    with col2:
        if st.button("⏹️ FERMA", type="secondary"):
            st.session_state.realtime_mode = False
            if st.session_state.speech_enabled:
                speak_with_web_api("Sessione terminata!")

    if not st.session_state.model:
        st.warning("⚠️ Carica prima YOLO11 per modalità real-time!")
        return

    # Area principale
    if st.session_state.realtime_mode:
        st.success("🔴 **MODALITÀ REAL-TIME ATTIVA** 🔴")
        st.info("📸 Scatta foto ogni pochi secondi per feedback continuo!")

        # Placeholder per risultati
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("📸 Live Analysis")
            camera_placeholder = st.empty()

        with col2:
            st.subheader("💬 Feedback Live")
            feedback_placeholder = st.empty()
            stats_placeholder = st.empty()

            # Contatore sessione
            if 'session_photos' not in st.session_state:
                st.session_state.session_photos = 0

            st.metric("📸 Foto Analizzate", st.session_state.session_photos)

        # Camera input con key dinamica
        camera_input = st.camera_input(
            f"📷 {exercise_type.upper()} - Scatta per feedback:", 
            key=f"realtime_{int(time.time())}"
        )

        if camera_input:
            current_time = time.time()

            # Throttling feedback
            if current_time - st.session_state.last_feedback_time > feedback_interval:

                # Analizza foto
                image = Image.open(camera_input)
                st.session_state.session_photos += 1

                try:
                    import cv2
                    opencv_img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                    results = st.session_state.model(opencv_img, verbose=False, save=False)

                    if len(results) > 0 and results[0].keypoints is not None:
                        # Disegna keypoints
                        annotated = results[0].plot()
                        annotated_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)

                        # Mostra immagine
                        camera_placeholder.image(annotated_rgb, use_column_width=True)

                        # Analisi pose
                        keypoints = results[0].keypoints.xy[0]
                        confidence = results[0].keypoints.conf[0] if results[0].keypoints.conf is not None else None

                        feedback_text, voice_feedback, status = analyze_pose_for_exercise(keypoints, confidence, exercise_type)

                        # Mostra feedback visivo
                        if status == "excellent":
                            feedback_placeholder.success(feedback_text)
                        elif status == "good":
                            feedback_placeholder.info(feedback_text)
                        elif status == "needs_work":
                            feedback_placeholder.warning(feedback_text)
                        else:
                            feedback_placeholder.error(feedback_text)

                        # FEEDBACK VOCALE CON WEB SPEECH API
                        if st.session_state.speech_enabled and voice_feedback:
                            speak_with_web_api(voice_feedback)

                        # Stats
                        if confidence is not None:
                            avg_conf = float(confidence.mean())
                            stats_placeholder.metric("🎯 Precision", f"{avg_conf:.1%}")

                        st.session_state.last_feedback_time = current_time

                    else:
                        feedback_placeholder.warning("⚠️ Nessuna persona rilevata")
                        camera_placeholder.image(image, use_column_width=True)

                        if st.session_state.speech_enabled:
                            speak_with_web_api("Non ti vedo! Posizionati meglio!")

                except Exception as e:
                    feedback_placeholder.error(f"❌ Errore: {e}")

        # Auto-refresh per continuare il loop
        time.sleep(1)
        st.rerun()

    else:
        # Modalità normale
        st.info("""
        ### 🎤 Real-Time con Web Speech API - Come Funziona:

        1. **Clicca "Test Audio Browser"** per verificare TTS 🔊
        2. **Carica YOLO11** 🤖  
        3. **Seleziona esercizio** dalla sidebar
        4. **Clicca "INIZIA REAL-TIME"** ▶️
        5. **Scatta foto ogni 3 secondi** 📸
        6. **Ascolta feedback dal TUO BROWSER!** 🗣️

        ### 🏋️ Feedback Vocale Examples:
        - **"Perfetto! Continua così!"** ✅
        - **"Scendi di più! Hip sopra ginocchia!"** ⚠️
        - **"Fletti i gomiti! Movimento troppo piccolo!"** ⚠️  
        - **"Mantieni corpo dritto!"** ⚠️

        ### 💡 Vantaggi Web Speech API:
        - ✅ **Funziona su Streamlit Cloud** 🌐
        - ✅ **Usa audio del browser** (non server)
        - ✅ **Supporta italiano** 🇮🇹
        - ✅ **Cross-platform** 📱💻
        - ✅ **Zero configurazione** ⚙️

        ### 📱 Browser Supportati:
        - Chrome ✅ | Firefox ✅ | Safari ✅ | Edge ✅
        """)

if __name__ == "__main__":
    main()
