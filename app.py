"""
Fitness Tracker AI - Simple Streaming con st.empty()
Soluzione semplice per camera sempre aperta senza dipendenze extra
"""
import streamlit as st
import cv2
import numpy as np
import time
from PIL import Image
import os
import threading
import base64
from io import BytesIO

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
    """Analisi pose veloce per real-time"""
    if keypoints is None or len(keypoints) == 0:
        return "", "", "neutral"

    try:
        if confidence is not None and len(confidence) > 16:
            hips_conf = (confidence[11] + confidence[12]) / 2
            knees_conf = (confidence[13] + confidence[14]) / 2
            shoulders_conf = (confidence[5] + confidence[6]) / 2
            elbows_conf = (confidence[7] + confidence[8]) / 2

            if exercise_type == "squat":
                if knees_conf > 0.6 and hips_conf > 0.6:
                    hip_y = (keypoints[11][1] + keypoints[12][1]) / 2
                    knee_y = (keypoints[13][1] + keypoints[14][1]) / 2

                    if hip_y > knee_y:
                        return "🟢 SQUAT PERFETTO!", "Perfetto! Continua così!", "excellent"
                    elif hip_y > knee_y * 0.95:
                        return "🟡 Quasi perfetto", "Scendi ancora un po'", "good"
                    else:
                        return "🔴 SCENDI DI PIÙ!", "Scendi di più!", "needs_work"
                else:
                    return "⚠️ Posizionati di lato", "Mettiti di lato alla camera", "positioning"

            elif exercise_type == "pushup":
                if shoulders_conf > 0.6 and elbows_conf > 0.6:
                    shoulder_y = (keypoints[5][1] + keypoints[6][1]) / 2
                    elbow_y = (keypoints[7][1] + keypoints[8][1]) / 2

                    if elbow_y > shoulder_y:
                        return "🟢 PUSH-UP PERFETTO!", "Perfetto! Ottima discesa!", "excellent"
                    else:
                        return "🔴 SCENDI DI PIÙ!", "Scendi di più!", "needs_work"
                else:
                    return "⚠️ Posizionati di lato", "Mettiti di lato alla camera", "positioning"

            elif exercise_type == "bicep_curl":
                if elbows_conf > 0.6:
                    elbow_y = keypoints[7][1]
                    wrist_y = keypoints[9][1] if len(keypoints) > 9 else elbow_y

                    if wrist_y < elbow_y:
                        return "🟢 CURL PERFETTO!", "Perfetto! Ottima flessione!", "excellent"
                    else:
                        return "🔴 FLETTI I GOMITI!", "Fletti i gomiti!", "needs_work"
                else:
                    return "⚠️ Posizionati frontale", "Mettiti frontale alla camera", "positioning"

        return "👤 Persona rilevata", "", "neutral"

    except Exception as e:
        return "❌ Errore analisi", "", "error"

def speak_with_web_api(message):
    """Web Speech API velocizzata"""
    if message:
        safe_message = message.replace("'", "\'").replace('"', '\"')
        # JavaScript più veloce
        speak_js = f"""
        <script>
        if ('speechSynthesis' in window && '{safe_message}') {{
            speechSynthesis.cancel(); // Cancella eventuali speech in corso
            const utterance = new SpeechSynthesisUtterance('{safe_message}');
            utterance.rate = 1.3;
            utterance.volume = 0.9;
            utterance.lang = 'it-IT';
            speechSynthesis.speak(utterance);
        }}
        </script>
        """
        st.components.v1.html(speak_js, height=0)

def main():
    st.set_page_config(
        page_title="💪 Fitness Tracker AI - Stream",
        page_icon="💪",
        layout="wide"
    )

    st.title("💪 Fitness Tracker AI - STREAM MODE")
    st.subheader("📹 Camera Continua + Feedback Vocale Real-Time!")

    # Session state
    if 'model' not in st.session_state:
        st.session_state.model = None
    if 'stream_running' not in st.session_state:
        st.session_state.stream_running = False
    if 'last_feedback_time' not in st.session_state:
        st.session_state.last_feedback_time = 0
    if 'frame_count' not in st.session_state:
        st.session_state.frame_count = 0

    # Sidebar
    st.sidebar.header("⚙️ Controlli Stream")

    # Carica YOLO11
    if st.sidebar.button("🤖 Carica YOLO11", type="primary"):
        st.session_state.model = load_yolo_model()
        if st.session_state.model:
            st.sidebar.success("✅ YOLO11 Ready!")
            speak_with_web_api("YOLO11 caricato! Sistema pronto!")

    if st.session_state.model:
        st.sidebar.success("🤖 YOLO11 Loaded")

    # Controlli
    exercise_type = st.sidebar.selectbox(
        "🎯 Esercizio:",
        ["squat", "pushup", "bicep_curl"],
        format_func=lambda x: {"squat": "🏋️ Squat", "pushup": "💪 Push-up", "bicep_curl": "🏋️‍♀️ Curl"}[x]
    )

    speech_enabled = st.sidebar.checkbox("🔊 Feedback Vocale", value=True)
    feedback_interval = st.sidebar.slider("🔄 Feedback ogni X sec", 1, 5, 2)

    # Test audio
    if st.sidebar.button("🔊 Test Audio"):
        speak_with_web_api("Sistema audio attivo!")

    # Stream controls
    col1, col2 = st.columns(2)

    with col1:
        if st.button("▶️ INIZIA STREAM", type="primary", disabled=not st.session_state.model):
            st.session_state.stream_running = True
            speak_with_web_api(f"Iniziamo con {exercise_type}! Preparati!")
            st.rerun()

    with col2:
        if st.button("⏹️ FERMA STREAM"):
            st.session_state.stream_running = False
            speak_with_web_api("Stream fermato!")
            st.rerun()

    if not st.session_state.model:
        st.warning("⚠️ Carica prima YOLO11!")
        return

    # Layout principale
    if st.session_state.stream_running:

        col1, col2 = st.columns([3, 1])

        with col1:
            st.subheader("📹 Live Stream")
            video_placeholder = st.empty()

        with col2:
            st.subheader("💬 Feedback")
            feedback_placeholder = st.empty()
            stats_placeholder = st.empty()

        # Modalità streaming continua con camera_input ad alta frequenza
        st.info("📸 Modalità Stream Attiva - Scatta continuamente per analisi real-time!")

        # Camera input con refresh veloce
        camera_key = f"stream_{int(time.time() * 2)}"  # Key cambia ogni 0.5 secondi

        camera_input = st.camera_input(
            f"📷 STREAM {exercise_type.upper()} - Auto-capture",
            key=camera_key
        )

        if camera_input:
            st.session_state.frame_count += 1
            current_time = time.time()

            # Processa ogni frame
            image = Image.open(camera_input)

            try:
                # YOLO11 detection
                import cv2
                opencv_img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                results = st.session_state.model(opencv_img, verbose=False, save=False)

                if len(results) > 0 and results[0].keypoints is not None:
                    # Disegna keypoints
                    annotated = results[0].plot()
                    annotated_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)

                    # Mostra video
                    video_placeholder.image(annotated_rgb, use_column_width=True)

                    # Feedback solo ogni N secondi
                    if current_time - st.session_state.last_feedback_time > feedback_interval:
                        keypoints = results[0].keypoints.xy[0]
                        confidence = results[0].keypoints.conf[0] if results[0].keypoints.conf is not None else None

                        feedback_text, voice_feedback, status = analyze_pose_for_exercise(
                            keypoints, confidence, exercise_type
                        )

                        # UI feedback
                        if status == "excellent":
                            feedback_placeholder.success(feedback_text)
                        elif status == "good":
                            feedback_placeholder.info(feedback_text)
                        elif status == "needs_work":
                            feedback_placeholder.warning(feedback_text)
                        elif status == "positioning":
                            feedback_placeholder.error(feedback_text)

                        # Feedback vocale
                        if speech_enabled and voice_feedback and status in ['excellent', 'needs_work', 'positioning']:
                            speak_with_web_api(voice_feedback)

                        st.session_state.last_feedback_time = current_time

                    # Stats
                    stats_placeholder.metric("📊 Frame", st.session_state.frame_count)
                    if results[0].keypoints.conf is not None:
                        avg_conf = float(results[0].keypoints.conf[0].mean())
                        stats_placeholder.metric("🎯 Confidence", f"{avg_conf:.1%}")

                else:
                    video_placeholder.image(image, use_column_width=True)
                    feedback_placeholder.warning("⚠️ Nessuna persona rilevata")

                    if speech_enabled and current_time - st.session_state.last_feedback_time > feedback_interval:
                        speak_with_web_api("Non ti vedo! Posizionati meglio!")
                        st.session_state.last_feedback_time = current_time

            except Exception as e:
                feedback_placeholder.error(f"❌ Errore: {e}")

        # Auto-refresh veloce per streaming
        time.sleep(0.3)  # Refresh ogni 0.3 secondi
        st.rerun()

    else:
        # Stato idle
        st.info("""
        ### 📹 Stream Mode - Caratteristiche:

        1. **Camera sempre aperta** durante la sessione
        2. **Auto-capture continuo** ogni 0.5 secondi  
        3. **YOLO11 real-time** su ogni frame
        4. **Feedback vocale** ogni 2 secondi
        5. **Performance ottimizzata** per streaming

        ### 🎯 Come Usare:

        1. **Carica YOLO11** 🤖
        2. **Test Audio** per verificare TTS 🔊
        3. **Seleziona esercizio** dalla sidebar
        4. **INIZIA STREAM** ▶️
        5. **Muoviti e allena!** Il sistema ti guida con la voce 🗣️

        ### 💡 Vantaggi:

        - ✅ **Nessuna dipendenza extra** (no streamlit-webrtc)
        - ✅ **Camera non si chiude** durante la sessione
        - ✅ **Feedback continuo** con Web Speech API
        - ✅ **Deploy immediato** su Streamlit Cloud
        - ✅ **Performance ottimizzata** per cloud

        **Pronto per l'allenamento real-time!** 💪
        """)

if __name__ == "__main__":
    main()
