"""
Fitness Tracker AI - Applicazione Principale
VERSIONE COMPLETA, TESTATA E FUNZIONANTE
"""
import streamlit as st
import cv2
import numpy as np
import time
from PIL import Image
import threading
import os
import sys

# Setup environment per YOLO
os.environ['YOLO_CONFIG_DIR'] = '/tmp'
os.environ['WANDB_DISABLED'] = 'true'
os.environ['ULTRALYTICS_ANALYTICS'] = 'false'

# Import dei moduli con gestione errori
try:
    from pose_detection import PoseDetector
    from posture_evaluation import PostureEvaluator
    from repetition_counter import RepetitionCounter
    from audio_feedback import AudioFeedback
    MODULES_OK = True
except ImportError as e:
    st.error(f"❌ Errore import moduli: {e}")
    MODULES_OK = False

class FitnessTracker:
    """
    Classe principale del Fitness Tracker
    """

    def __init__(self):
        self.pose_detector = None
        self.posture_evaluator = PostureEvaluator() if MODULES_OK else None
        self.rep_counter = RepetitionCounter() if MODULES_OK else None
        self.audio_feedback = AudioFeedback() if MODULES_OK else None

        self.is_running = False
        self.current_exercise = 'squat'
        self.webcam = None
        self.model_loaded = False
        self.model_loading = False

    def init_model_async(self):
        """Inizializza YOLO11 in background"""
        if self.model_loading or self.model_loaded or not MODULES_OK:
            return

        self.model_loading = True

        def load_model():
            try:
                st.session_state.model_status = "⏳ Caricamento YOLO11... (30-60s prima volta)"
                self.pose_detector = PoseDetector()
                self.model_loaded = self.pose_detector.is_model_loaded()

                if self.model_loaded:
                    st.session_state.model_status = "✅ YOLO11 pronto!"
                else:
                    st.session_state.model_status = "❌ Errore caricamento YOLO11"
            except Exception as e:
                st.session_state.model_status = f"❌ Errore: {str(e)[:100]}"
                self.model_loaded = False

            self.model_loading = False

        threading.Thread(target=load_model, daemon=True).start()

    def init_webcam(self):
        """Inizializza webcam"""
        try:
            # Prova diversi indici webcam
            for i in range(4):
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        self.webcam = cap
                        self.webcam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                        self.webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                        return True
                cap.release()
            return False
        except:
            return False

    def release_webcam(self):
        """Rilascia webcam"""
        if self.webcam:
            self.webcam.release()
            self.webcam = None

    def process_frame(self, frame):
        """Processa frame per rilevamento pose"""
        if not self.model_loaded or not self.pose_detector:
            return frame, None

        try:
            # YOLO11 detection
            processed_frame, results = self.pose_detector.detect_pose(frame)

            if results:
                processed_frame = self.pose_detector.draw_landmarks(processed_frame, results)

            # Estrai landmarks
            landmarks = self.pose_detector.get_body_landmarks(results)

            # Valuta postura
            evaluation = None
            if landmarks and self.posture_evaluator:
                if self.current_exercise == 'squat':
                    evaluation = self.posture_evaluator.evaluate_squat(landmarks, self.pose_detector)
                elif self.current_exercise == 'pushup':
                    evaluation = self.posture_evaluator.evaluate_pushup(landmarks, self.pose_detector)
                elif self.current_exercise == 'bicep_curl':
                    evaluation = self.posture_evaluator.evaluate_bicep_curl(landmarks, self.pose_detector)

            return processed_frame, evaluation
        except Exception as e:
            print(f"Errore processing: {e}")
            return frame, None

def main():
    """Funzione principale Streamlit"""

    st.set_page_config(
        page_title="💪 Fitness Tracker AI",
        page_icon="💪", 
        layout="wide"
    )

    st.title("💪 Fitness Tracker AI")
    st.subheader("🚀 Powered by YOLO11 - Versione Completa")

    # Info sistema
    st.sidebar.header("ℹ️ Info Sistema")
    st.sidebar.success(f"🐍 Python {sys.version_info.major}.{sys.version_info.minor}")

    if not MODULES_OK:
        st.error("❌ Moduli non disponibili. Controlla i requirements!")
        return

    # Inizializza app
    if 'fitness_tracker' not in st.session_state:
        st.session_state.fitness_tracker = FitnessTracker()
        st.session_state.model_status = "⚙️ Inizializzazione..."

    tracker = st.session_state.fitness_tracker

    # Avvia caricamento modello
    if not tracker.model_loaded and not tracker.model_loading:
        tracker.init_model_async()

    # Mostra status modello
    if hasattr(st.session_state, 'model_status'):
        if "✅" in st.session_state.model_status:
            st.success(st.session_state.model_status)
        elif "⏳" in st.session_state.model_status:
            st.info(st.session_state.model_status)
            if tracker.model_loading:
                st.progress(0.6, "Download modello YOLO11...")
        else:
            st.error(st.session_state.model_status)

    # Se sta caricando, mostra solo info
    if tracker.model_loading:
        st.info("""
        ### ⏳ Caricamento YOLO11 in corso...

        **Prima volta:** Download automatico modello (~20MB)
        **Tempo:** 30-60 secondi  
        **Successive volte:** Immediato (modello in cache)

        Attendi che compaia "✅ YOLO11 pronto!" ⏳
        """)
        time.sleep(3)
        st.rerun()
        return

    # Controlli sidebar
    st.sidebar.header("⚙️ Controlli")

    if tracker.model_loaded:
        st.sidebar.success("🤖 YOLO11 Ready")
    else:
        st.sidebar.warning("❌ YOLO11 non pronto")

    # Selezione esercizio
    exercise_options = {
        'squat': '🏋️ Squat',
        'pushup': '💪 Push-up',
        'bicep_curl': '🏋️‍♀️ Curl Bicipiti'
    }

    selected_exercise = st.sidebar.selectbox(
        "Seleziona esercizio:",
        options=list(exercise_options.keys()),
        format_func=lambda x: exercise_options[x],
        disabled=not tracker.model_loaded
    )

    # Cambia esercizio
    if selected_exercise != tracker.current_exercise and tracker.model_loaded:
        tracker.current_exercise = selected_exercise
        if tracker.rep_counter:
            tracker.rep_counter.reset()
        if tracker.audio_feedback:
            tracker.audio_feedback.announce_exercise_start(selected_exercise)

    # Controlli audio
    st.sidebar.subheader("🔊 Audio")
    audio_rate = st.sidebar.slider("Velocità", 150, 300, 200)

    if st.sidebar.button("🔧 Test Audio") and tracker.audio_feedback:
        tracker.audio_feedback.set_voice_properties(audio_rate)
        tracker.audio_feedback.test_audio()

    # Form requirement
    require_form = st.sidebar.checkbox("Richiedi forma corretta", True)
    if tracker.rep_counter:
        tracker.rep_counter.set_form_requirement(require_form)

    # Pulsanti principali
    col1, col2, col3 = st.columns(3)

    with col1:
        start_btn = st.button("▶️ Inizia", type="primary", disabled=not tracker.model_loaded)

    with col2:
        stop_btn = st.button("⏹️ Stop", type="secondary")

    with col3:
        reset_btn = st.button("🔄 Reset", disabled=not tracker.model_loaded)

    # Gestione pulsanti
    if start_btn and tracker.model_loaded:
        if tracker.init_webcam():
            tracker.is_running = True
            st.success("✅ Webcam avviata!")
            st.rerun()
        else:
            st.error("❌ Webcam non disponibile")

    if stop_btn:
        tracker.is_running = False
        tracker.release_webcam()
        st.info("⏹️ Fermato")
        st.rerun()

    if reset_btn and tracker.rep_counter:
        tracker.rep_counter.reset()
        st.success("🔄 Reset fatto")

    # Area principale
    if tracker.is_running and tracker.webcam and tracker.model_loaded:

        col1, col2 = st.columns([3, 1])

        with col1:
            video_placeholder = st.empty()
            status_placeholder = st.empty()

        with col2:
            st.subheader("📊 Statistiche")
            rep_placeholder = st.empty()
            form_placeholder = st.empty()
            stats_placeholder = st.empty()

            st.subheader("💬 Feedback")
            feedback_placeholder = st.empty()

        # Loop video
        try:
            ret, frame = tracker.webcam.read()

            if ret:
                # Processa frame
                processed_frame, evaluation = tracker.process_frame(frame)

                # Mostra video
                frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                video_placeholder.image(frame_rgb, channels="RGB", use_column_width=True)

                # Aggiorna stats se c'è valutazione
                if evaluation and tracker.rep_counter:
                    rep_status = tracker.rep_counter.update(tracker.current_exercise, evaluation)

                    # Feedback audio
                    if tracker.audio_feedback:
                        if not evaluation['correct']:
                            tracker.audio_feedback.provide_form_feedback(evaluation['feedback'])
                        if rep_status.get('rep_completed', False):
                            tracker.audio_feedback.announce_rep_count(rep_status['count'])

                    # UI updates
                    rep_placeholder.metric("🔢 Ripetizioni", rep_status['count'])

                    if evaluation['correct']:
                        form_placeholder.success("🟢 Forma Corretta")
                    else:
                        form_placeholder.error("🔴 Da Correggere")

                    feedback_placeholder.info(f"💡 {evaluation['feedback']}")

                    # Phase status
                    phase_emoji = {'up': '⬆️', 'down': '⬇️', 'transition': '🔄'}
                    phase_icon = phase_emoji.get(evaluation.get('phase'), '❓')
                    status_placeholder.info(f"{phase_icon} Fase: {evaluation.get('phase', 'N/A').title()}")

                    # Stats dettagliate
                    stats = tracker.rep_counter.get_statistics()
                    stats_placeholder.markdown(f"""
                    **📈 Dettagli:**
                    - 🎯 Tot: {stats['total_reps']}
                    - ✅ Forma: {stats['correct_form_percentage']:.1f}%
                    - 📊 Fasi: {stats['total_phases_tracked']}
                    """)

                # Auto-refresh per continuare loop
                time.sleep(0.05)
                st.rerun()

            else:
                st.error("❌ Errore lettura webcam")
                tracker.is_running = False

        except Exception as e:
            st.error(f"❌ Errore: {str(e)}")
            tracker.is_running = False

    else:
        # Istruzioni quando non in uso
        if tracker.model_loaded:
            st.info("""
            ### 📋 Istruzioni:

            1. **Clicca "Inizia"** per attivare la webcam 📹
            2. **Consenti accesso** camera nel browser 🔐
            3. **Posizionati** con tutto il corpo visibile 🤸
            4. **Inizia l'esercizio** - il sistema rileva automaticamente! 🏋️
            5. **Ascolta i feedback** audio per migliorare 🔊

            ### 🎯 Esercizi disponibili:
            - **Squat**: Piedi larghezza spalle, schiena dritta
            - **Push-up**: Corpo dritto, scendi completamente  
            - **Curl Bicipiti**: Gomiti vicini al corpo

            **🎵 Assicurati che l'audio sia attivo!**
            """)
        else:
            st.warning("""
            ### ⏳ Caricamento in corso...

            Il sistema sta scaricando e inizializzando il modello YOLO11.

            **Prima volta:** ~30-60 secondi
            **Volte successive:** Immediato

            Attendi che appaia "✅ YOLO11 pronto!"
            """)

    # Footer
    st.markdown("---")
    st.markdown("💪 **Fitness Tracker AI - Powered by YOLO11** 🚀")

if __name__ == "__main__":
    main()
