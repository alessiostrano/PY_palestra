"""
Fitness Tracker AI - Streaming Real-Time con WebRTC
Camera sempre aperta + YOLO11 continuo + feedback vocale
"""
import streamlit as st
import cv2
import numpy as np
import time
from PIL import Image
import os
import threading
import queue
import json

# Environment setup
os.environ.setdefault('YOLO_CONFIG_DIR', '/tmp')
os.environ.setdefault('WANDB_DISABLED', 'true')

# Prova import streamlit-webrtc per streaming video
try:
    from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
    WEBRTC_AVAILABLE = True
except ImportError:
    WEBRTC_AVAILABLE = False

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
    """Analisi pose ottimizzata per real-time"""
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
                        return "🟢 PERFETTO!", "Perfetto! Continua così!", "excellent"
                    elif hip_y > knee_y * 0.95:
                        return "🟡 Bene", "Bene! Scendi ancora un po'", "good"
                    else:
                        return "🔴 SCENDI!", "Scendi di più!", "needs_work"
                else:
                    return "⚠️ Posizione", "Mettiti di lato", "positioning"

            elif exercise_type == "pushup":
                if shoulders_conf > 0.6 and elbows_conf > 0.6:
                    shoulder_y = (keypoints[5][1] + keypoints[6][1]) / 2
                    elbow_y = (keypoints[7][1] + keypoints[8][1]) / 2

                    if elbow_y > shoulder_y:
                        return "🟢 PERFETTO!", "Perfetto! Ottima discesa!", "excellent"
                    else:
                        return "🔴 SCENDI!", "Scendi di più!", "needs_work"
                else:
                    return "⚠️ Posizione", "Mettiti di lato", "positioning"

            elif exercise_type == "bicep_curl":
                if elbows_conf > 0.6:
                    elbow_y = keypoints[7][1]
                    wrist_y = keypoints[9][1]

                    if wrist_y < elbow_y:
                        return "🟢 PERFETTO!", "Perfetto! Ottima flessione!", "excellent"
                    else:
                        return "🔴 FLETTI!", "Fletti i gomiti!", "needs_work"
                else:
                    return "⚠️ Posizione", "Mettiti frontale", "positioning"

        return "👤 Rilevato", "", "neutral"

    except:
        return "❌ Errore", "", "error"

def speak_with_web_api(message):
    """Web Speech API per feedback vocale"""
    if message:
        safe_message = message.replace("'", "\'").replace('"', '\"')
        speak_js = f"""
        <script>
        if ('speechSynthesis' in window) {{
            const utterance = new SpeechSynthesisUtterance('{safe_message}');
            utterance.rate = 1.2;
            utterance.volume = 0.9;
            utterance.lang = 'it-IT';
            speechSynthesis.speak(utterance);
        }}
        </script>
        """
        st.components.v1.html(speak_js, height=0)

class VideoProcessor:
    def __init__(self):
        self.model = None
        self.exercise_type = "squat"
        self.last_feedback_time = 0
        self.feedback_interval = 2.0
        self.speech_enabled = True
        self.frame_count = 0

    def set_model(self, model):
        self.model = model

    def set_exercise(self, exercise):
        self.exercise_type = exercise

    def set_speech(self, enabled):
        self.speech_enabled = enabled

    def process_frame(self, frame):
        """Processa ogni frame del video"""
        if self.model is None:
            return frame

        self.frame_count += 1

        # Analizza solo ogni N frame per performance
        if self.frame_count % 10 != 0:  # Ogni 10 frame (~3 volte al secondo a 30fps)
            return frame

        try:
            # YOLO11 detection
            results = self.model(frame, verbose=False, save=False)

            if len(results) > 0 and results[0].keypoints is not None:
                # Disegna keypoints
                annotated_frame = results[0].plot()

                # Analisi per feedback (solo ogni N secondi)
                current_time = time.time()
                if current_time - self.last_feedback_time > self.feedback_interval:
                    keypoints = results[0].keypoints.xy[0]
                    confidence = results[0].keypoints.conf[0] if results[0].keypoints.conf is not None else None

                    feedback_text, voice_feedback, status = analyze_pose_for_exercise(
                        keypoints, confidence, self.exercise_type
                    )

                    # Salva feedback nel session state per UI
                    st.session_state.current_feedback = feedback_text
                    st.session_state.current_status = status

                    # Feedback vocale
                    if self.speech_enabled and voice_feedback and status in ['excellent', 'needs_work']:
                        speak_with_web_api(voice_feedback)

                    self.last_feedback_time = current_time

                return annotated_frame
            else:
                return frame

        except Exception as e:
            # In caso di errore, ritorna frame originale
            return frame

def main():
    st.set_page_config(
        page_title="💪 Fitness Tracker AI - Streaming",
        page_icon="💪",
        layout="wide"
    )

    st.title("💪 Fitness Tracker AI - STREAMING REAL-TIME")
    st.subheader("📹 Camera Sempre Aperta + YOLO11 Continuo!")

    # Check WebRTC availability
    if not WEBRTC_AVAILABLE:
        st.error("""
        ❌ **streamlit-webrtc non disponibile!**

        **Per streaming video real-time serve:**
        ```
        pip install streamlit-webrtc
        ```

        **Oppure aggiungi a requirements.txt:**
        ```
        streamlit-webrtc>=0.47.0
        ```

        **In alternativa, usa la versione con camera_input.**
        """)
        return

    # Inizializza session state
    if 'model' not in st.session_state:
        st.session_state.model = None
    if 'current_feedback' not in st.session_state:
        st.session_state.current_feedback = "Nessun feedback"
    if 'current_status' not in st.session_state:
        st.session_state.current_status = "neutral"

    # Sidebar controlli
    st.sidebar.header("⚙️ Controlli Streaming")

    # Carica YOLO11
    if st.sidebar.button("🤖 Carica YOLO11", type="primary"):
        st.session_state.model = load_yolo_model()
        if st.session_state.model:
            st.sidebar.success("✅ YOLO11 Pronto!")
            speak_with_web_api("YOLO11 caricato! Sistema pronto!")

    if st.session_state.model:
        st.sidebar.success("🤖 YOLO11 Ready")

    # Controlli esercizio
    exercise_type = st.sidebar.selectbox(
        "🎯 Esercizio:",
        ["squat", "pushup", "bicep_curl"],
        format_func=lambda x: {"squat": "🏋️ Squat", "pushup": "💪 Push-up", "bicep_curl": "🏋️‍♀️ Curl"}[x]
    )

    # Audio settings
    speech_enabled = st.sidebar.checkbox("🔊 Feedback Vocale", value=True)
    feedback_interval = st.sidebar.slider("🔄 Feedback ogni X secondi", 1, 5, 2)

    # Test audio
    if st.sidebar.button("🔊 Test Audio"):
        speak_with_web_api("Sistema audio funzionante!")

    # Layout principale
    col1, col2 = st.columns([3, 1])

    with col1:
        st.subheader("📹 Video Stream Real-Time")

        if not st.session_state.model:
            st.warning("⚠️ Carica prima YOLO11 per iniziare!")
        else:
            # Configura video processor
            processor = VideoProcessor()
            processor.set_model(st.session_state.model)
            processor.set_exercise(exercise_type)
            processor.set_speech(speech_enabled)
            processor.feedback_interval = feedback_interval

            # WebRTC streamer
            webrtc_ctx = webrtc_streamer(
                key="fitness-tracker",
                mode=WebRtcMode.SENDRECV,
                rtc_configuration=RTCConfiguration({
                    "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
                }),
                video_processor_factory=lambda: processor,
                media_stream_constraints={"video": True, "audio": False},
                async_processing=True
            )

            if webrtc_ctx.video_processor:
                st.success("✅ Streaming video attivo!")
            else:
                st.info("▶️ Clicca 'START' per iniziare lo streaming")

    with col2:
        st.subheader("💬 Feedback Live")

        # Mostra feedback corrente
        if st.session_state.current_status == "excellent":
            st.success(st.session_state.current_feedback)
        elif st.session_state.current_status == "good":
            st.info(st.session_state.current_feedback)
        elif st.session_state.current_status == "needs_work":
            st.warning(st.session_state.current_feedback)
        elif st.session_state.current_status == "positioning":
            st.error(st.session_state.current_feedback)
        else:
            st.write(st.session_state.current_feedback)

        # Istruzioni esercizio
        st.subheader("📋 Istruzioni")
        exercise_instructions = {
            "squat": "🏋️ Posizionati di LATO. Scendi con le anche sotto le ginocchia.",
            "pushup": "💪 Posizionati di LATO. Scendi completamente col petto.",
            "bicep_curl": "🏋️‍♀️ Posizionati FRONTALE. Fletti completamente i gomiti."
        }
        st.info(exercise_instructions[exercise_type])

        # Stats
        st.subheader("📊 Stats")
        st.metric("🎯 Esercizio", exercise_type.title())
        st.metric("🔊 Audio", "ON" if speech_enabled else "OFF")
        st.metric("⏱️ Interval", f"{feedback_interval}s")

    # Istruzioni
    st.info("""
    ### 📹 Streaming Real-Time - Come Funziona:

    1. **Carica YOLO11** 🤖
    2. **Clicca "START"** per attivare streaming
    3. **Consenti accesso webcam** nel browser
    4. **Camera rimane SEMPRE aperta** 📹
    5. **YOLO11 analizza continuo** (~3 volte/secondo)
    6. **Feedback vocale automatico** ogni 2 secondi! 🗣️

    ### 💡 Vantaggi Streaming:
    - ✅ **Camera sempre aperta** - no apertura/chiusura
    - ✅ **Processing continuo** - YOLO11 real-time  
    - ✅ **Performance ottimizzata** - analisi ogni 10 frame
    - ✅ **Feedback intelligente** - solo correzioni importanti
    """)

if __name__ == "__main__":
    main()
