"""
Fitness Tracker AI - Modalità Real-Time con Auto-Capture
Scatta foto automatiche ogni 2-3 secondi + feedback vocale immediato
"""
import streamlit as st
import numpy as np
import time
from PIL import Image
import os
import threading
import asyncio

# Environment setup
os.environ.setdefault('YOLO_CONFIG_DIR', '/tmp')
os.environ.setdefault('WANDB_DISABLED', 'true')

def init_tts():
    """Inizializza Text-to-Speech per feedback vocale"""
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty('rate', 180)  # Velocità parlato
        engine.setProperty('volume', 0.9)  # Volume alto
        return engine
    except:
        return None

def speak_feedback(engine, message):
    """Parla il feedback in thread separato per non bloccare"""
    if engine and message:
        def speak_thread():
            try:
                engine.say(message)
                engine.runAndWait()
            except:
                pass

        thread = threading.Thread(target=speak_thread, daemon=True)
        thread.start()

def load_yolo_model():
    """Carica YOLO11"""
    try:
        from ultralytics import YOLO
        with st.spinner("🤖 Caricamento YOLO11..."):
            model = YOLO('yolo11n-pose.pt')
            # Test veloce
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

    # Keypoints COCO: 5-6: shoulders, 7-8: elbows, 9-10: wrists
    # 11-12: hips, 13-14: knees, 15-16: ankles

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
                # Analisi squat avanzata
                if knees_conf > 0.6 and hips_conf > 0.6:
                    # Calcola "profondità" squat approssimativamente
                    hip_y = (keypoints[11][1] + keypoints[12][1]) / 2
                    knee_y = (keypoints[13][1] + keypoints[14][1]) / 2

                    if hip_y > knee_y:  # Hip più in basso delle ginocchia = squat profondo
                        feedback_text = "🟢 SQUAT PROFONDO - Ottima forma!"
                        voice_feedback = "Perfetto! Continua così!"
                        status = "excellent"
                    elif hip_y > knee_y * 0.95:  # Hip quasi al livello ginocchia
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
                    if abs(left_knee_x - right_knee_x) < 0.3:  # Ginocchia allineate
                        feedback_text += " Ginocchia ben allineate!"
                    else:
                        feedback_text += " ⚠️ Allinea meglio le ginocchia"
                        voice_feedback += " Allinea le ginocchia!"

                else:
                    feedback_text = "⚠️ Posizionati di LATO per miglior rilevamento"
                    voice_feedback = "Mettiti di lato alla camera"
                    status = "positioning"

            elif exercise_type == "pushup":
                if shoulders_conf > 0.6 and elbows_conf > 0.6:
                    # Analisi push-up
                    shoulder_y = (keypoints[5][1] + keypoints[6][1]) / 2
                    elbow_y = (keypoints[7][1] + keypoints[8][1]) / 2

                    if elbow_y > shoulder_y:  # Gomiti sotto spalle = push-up basso
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

                    # Controlla corpo dritto
                    if 'left_hip' in locals() and 'left_shoulder' in locals():
                        feedback_text += " Mantieni il corpo dritto!"

                else:
                    feedback_text = "⚠️ Posizionati di LATO per miglior rilevamento" 
                    voice_feedback = "Mettiti di lato alla camera"
                    status = "positioning"

            elif exercise_type == "bicep_curl":
                if elbows_conf > 0.6 and shoulders_conf > 0.6:
                    # Analisi curl
                    left_elbow_y = keypoints[7][1]
                    left_wrist_y = keypoints[9][1]
                    left_shoulder_y = keypoints[5][1]

                    if left_wrist_y < left_elbow_y < left_shoulder_y:  # Curl alto
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

                    if abs(left_elbow_x - left_shoulder_x) < 0.1:
                        feedback_text += " Gomiti ben fermi!"
                    else:
                        feedback_text += " ⚠️ Mantieni gomiti vicino al corpo"
                        voice_feedback += " Gomiti vicino al corpo!"

                else:
                    feedback_text = "⚠️ Posizionati FRONTALE per miglior rilevamento"
                    voice_feedback = "Mettiti frontale alla camera"
                    status = "positioning"

        return feedback_text, voice_feedback, status

    except Exception as e:
        return f"❌ Errore analisi: {str(e)}", "", "error"

def main():
    st.set_page_config(
        page_title="💪 Fitness Tracker AI - Real Time",
        page_icon="💪",
        layout="wide"
    )

    st.title("💪 Fitness Tracker AI - REAL TIME")
    st.subheader("🎤 Con Feedback Vocale in Tempo Reale!")

    # Inizializza session state
    if 'model' not in st.session_state:
        st.session_state.model = None
    if 'tts_engine' not in st.session_state:
        st.session_state.tts_engine = None
    if 'realtime_mode' not in st.session_state:
        st.session_state.realtime_mode = False
    if 'last_feedback_time' not in st.session_state:
        st.session_state.last_feedback_time = 0

    # Sidebar
    st.sidebar.header("⚙️ Controlli Real-Time")

    # Carica modelli
    if st.sidebar.button("🤖 Carica YOLO11", type="primary"):
        st.session_state.model = load_yolo_model()
        if st.session_state.model:
            st.sidebar.success("✅ YOLO11 Pronto!")

    if st.sidebar.button("🎤 Inizializza Audio"):
        st.session_state.tts_engine = init_tts()
        if st.session_state.tts_engine:
            st.sidebar.success("✅ TTS Pronto!")
            speak_feedback(st.session_state.tts_engine, "Sistema audio attivato!")
        else:
            st.sidebar.warning("⚠️ TTS non disponibile")

    # Status modelli
    if st.session_state.model:
        st.sidebar.success("🤖 YOLO11 Ready")
    if st.session_state.tts_engine:
        st.sidebar.success("🎤 Audio Ready")

    # Selezione esercizio
    exercise_type = st.sidebar.selectbox(
        "🎯 Esercizio:",
        ["squat", "pushup", "bicep_curl"],
        format_func=lambda x: {"squat": "🏋️ Squat", "pushup": "💪 Push-up", "bicep_curl": "🏋️‍♀️ Curl"}[x]
    )

    # Velocità feedback
    feedback_interval = st.sidebar.slider("🔄 Feedback ogni X secondi", 1, 5, 2)

    # Modalità real-time
    col1, col2 = st.columns(2)

    with col1:
        if st.button("▶️ INIZIA REAL-TIME", type="primary", disabled=not (st.session_state.model and st.session_state.tts_engine)):
            st.session_state.realtime_mode = True
            speak_feedback(st.session_state.tts_engine, f"Iniziamo con {exercise_type}! Preparati!")

    with col2:
        if st.button("⏹️ FERMA", type="secondary"):
            st.session_state.realtime_mode = False
            speak_feedback(st.session_state.tts_engine, "Sessione terminata!")

    if not (st.session_state.model and st.session_state.tts_engine):
        st.warning("⚠️ Carica prima YOLO11 e Audio per modalità real-time!")
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

        # Loop continuo per camera input
        camera_input = st.camera_input(
            f"📷 {exercise_type.upper()} - Scatta per feedback:", 
            key=f"realtime_{int(time.time())}"  # Key dinamica per refresh
        )

        if camera_input:
            current_time = time.time()

            # Throttling feedback per non spammare
            if current_time - st.session_state.last_feedback_time > feedback_interval:

                # Analizza foto
                image = Image.open(camera_input)

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

                        # FEEDBACK VOCALE IMMEDIATO
                        if voice_feedback:
                            speak_feedback(st.session_state.tts_engine, voice_feedback)

                        # Stats
                        if confidence is not None:
                            avg_conf = float(confidence.mean())
                            stats_placeholder.metric("🎯 Precision", f"{avg_conf:.1%}")

                        st.session_state.last_feedback_time = current_time

                    else:
                        feedback_placeholder.warning("⚠️ Nessuna persona rilevata")
                        speak_feedback(st.session_state.tts_engine, "Non ti vedo! Posizionati meglio!")

                except Exception as e:
                    feedback_placeholder.error(f"❌ Errore: {e}")

        # Auto-refresh per continuare il loop
        time.sleep(0.5)
        st.rerun()

    else:
        # Modalità normale
        st.info("""
        ### 🎤 Modalità Real-Time - Come Funziona:

        1. **Carica YOLO11** 🤖 e **Inizializza Audio** 🎤
        2. **Seleziona esercizio** dalla sidebar
        3. **Clicca "INIZIA REAL-TIME"** ▶️
        4. **Scatta foto ogni 2-3 secondi** 📸
        5. **Ricevi feedback vocale IMMEDIATO!** 🗣️

        ### 🏋️ Feedback Vocale Includes:
        - **"Perfetto! Continua così!"** ✅
        - **"Scendi di più!"** per squat shallow
        - **"Fletti i gomiti!"** per curl incomplete  
        - **"Mantieni corpo dritto!"** per push-up
        - **"Allinea le ginocchia!"** per squat form

        ### 💡 Tips per Miglior Esperienza:
        - **Audio cuffie/altoparlanti** ON 🔊
        - **Buona illuminazione** 💡
        - **Corpo intero visibile** 👤
        - **Scatta ogni 2-3 secondi** ⏱️
        """)

if __name__ == "__main__":
    main()
