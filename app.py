"""
Applicazione Streamlit per il fitness tracking con YOLO11 e feedback audio
VERSIONE FIXED per Render - Gestisce caricamento YOLO11
"""
import streamlit as st
import cv2
import numpy as np
import time
from PIL import Image
import threading
import os

# Fix environment per YOLO prima degli import
os.environ['YOLO_CONFIG_DIR'] = '/tmp'
os.environ['WANDB_DISABLED'] = 'true'
os.environ['ULTRALYTICS_ANALYTICS'] = 'false'

# Import dei moduli personalizzati
from pose_detection import PoseDetector
from posture_evaluation import PostureEvaluator
from repetition_counter import RepetitionCounter
from audio_feedback import AudioFeedback

class FitnessTracker:
    """
    Classe principale per l'applicazione di fitness tracking con YOLO11
    """

    def __init__(self):
        """
        Inizializza tutti i componenti dell'applicazione
        """
        self.pose_detector = None
        self.posture_evaluator = PostureEvaluator()
        self.rep_counter = RepetitionCounter()
        self.audio_feedback = AudioFeedback()

        # Stato dell'applicazione
        self.is_running = False
        self.current_exercise = 'squat'
        self.webcam = None
        self.model_loaded = False
        self.model_loading = False

    def init_pose_detector_async(self):
        """
        Inizializza il detector YOLO11 in modo asincrono
        """
        if self.model_loading or self.model_loaded:
            return

        self.model_loading = True

        def load_model():
            try:
                st.session_state.model_status = "⏳ Download modello YOLO11 in corso..."
                self.pose_detector = PoseDetector(model_name='yolo11n-pose.pt')
                self.model_loaded = self.pose_detector.is_model_loaded()

                if self.model_loaded:
                    st.session_state.model_status = "✅ YOLO11 caricato e pronto!"
                else:
                    st.session_state.model_status = "❌ Errore nel caricamento YOLO11"

            except Exception as e:
                st.session_state.model_status = f"❌ Errore YOLO11: {str(e)}"
                self.model_loaded = False

            self.model_loading = False

        # Carica in thread separato per non bloccare UI
        thread = threading.Thread(target=load_model, daemon=True)
        thread.start()

    def initialize_webcam(self):
        """
        Inizializza la webcam

        Returns:
            bool: True se la webcam è stata inizializzata correttamente
        """
        try:
            self.webcam = cv2.VideoCapture(0)
            if not self.webcam.isOpened():
                # Prova indici alternativi
                for i in range(1, 4):
                    self.webcam = cv2.VideoCapture(i)
                    if self.webcam.isOpened():
                        break

            if self.webcam.isOpened():
                self.webcam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.webcam.set(cv2.CAP_PROP_FPS, 15)  # Ridotto per prestazioni
                return True
            return False

        except Exception as e:
            st.error(f"Errore nell'inizializzazione della webcam: {e}")
            return False

    def release_webcam(self):
        """
        Rilascia la webcam
        """
        if self.webcam:
            self.webcam.release()
            self.webcam = None

    def process_frame(self, frame):
        """
        Processa un singolo frame per il rilevamento della pose

        Args:
            frame: Frame dalla webcam

        Returns:
            tuple: (processed_frame, evaluation_result)
        """
        if not self.model_loaded or not self.pose_detector:
            return frame, None

        try:
            # Rileva la pose con YOLO11
            processed_frame, pose_results = self.pose_detector.detect_pose(frame)

            # Disegna i keypoints
            if pose_results:
                processed_frame = self.pose_detector.draw_landmarks(processed_frame, pose_results)

            # Ottieni i landmark del corpo
            landmarks = self.pose_detector.get_body_landmarks(pose_results)

            # Valuta la postura basandosi sull'esercizio selezionato
            evaluation_result = None
            if landmarks:
                if self.current_exercise == 'squat':
                    evaluation_result = self.posture_evaluator.evaluate_squat(landmarks, self.pose_detector)
                elif self.current_exercise == 'pushup':
                    evaluation_result = self.posture_evaluator.evaluate_pushup(landmarks, self.pose_detector)
                elif self.current_exercise == 'bicep_curl':
                    evaluation_result = self.posture_evaluator.evaluate_bicep_curl(landmarks, self.pose_detector)

            return processed_frame, evaluation_result

        except Exception as e:
            print(f"Errore nel processing frame: {e}")
            return frame, None

    def update_repetitions(self, evaluation_result):
        """
        Aggiorna il conteggio delle ripetizioni
        """
        return self.rep_counter.update(self.current_exercise, evaluation_result)

    def provide_audio_feedback(self, evaluation_result, rep_status):
        """
        Fornisce feedback audio basandosi sulla valutazione
        """
        if evaluation_result:
            # Feedback sulla forma
            if not evaluation_result['correct']:
                self.audio_feedback.provide_form_feedback(evaluation_result['feedback'])

            # Annuncio ripetizioni completate
            if rep_status.get('rep_completed', False):
                self.audio_feedback.announce_rep_count(rep_status['count'])

def main():
    """
    Funzione principale dell'applicazione Streamlit
    """
    st.set_page_config(
        page_title="Fitness Tracker AI - YOLO11",
        page_icon="💪",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("💪 Fitness Tracker AI")
    st.subheader("🚀 Powered by YOLO11 - Render Optimized")

    # Inizializza l'app in session state
    if 'fitness_tracker' not in st.session_state:
        st.session_state.fitness_tracker = FitnessTracker()
        st.session_state.model_status = "⏳ Inizializzazione..."

    fitness_tracker = st.session_state.fitness_tracker

    # Avvia caricamento modello se non già fatto
    if not fitness_tracker.model_loaded and not fitness_tracker.model_loading:
        fitness_tracker.init_pose_detector_async()

    # Status del modello con progress
    if hasattr(st.session_state, 'model_status'):
        if "✅" in st.session_state.model_status:
            st.success(st.session_state.model_status)
        elif "⏳" in st.session_state.model_status:
            st.info(st.session_state.model_status)
            if fitness_tracker.model_loading:
                st.progress(0.5, text="Download del modello YOLO11 in corso... (prima volta: ~30-60 secondi)")
        else:
            st.error(st.session_state.model_status)

    # Se il modello sta caricando, mostra solo informazioni
    if fitness_tracker.model_loading:
        st.info("""
        ### ⏳ Caricamento YOLO11 in corso...

        **Prima volta:**
        - Download modello: ~20MB (~30-60 secondi)
        - Setup configurazione 
        - Test funzionamento

        **Volte successive:** Caricamento istantaneo!

        Attendere prego... ⏳
        """)

        # Auto-refresh per controllare lo stato
        time.sleep(2)
        st.rerun()
        return

    # Sidebar con controlli (solo se modello caricato)
    st.sidebar.header("⚙️ Controlli")

    # Informazioni sul modello
    if fitness_tracker.model_loaded:
        model_info = fitness_tracker.pose_detector.get_model_info()
        st.sidebar.success(f"🤖 {model_info['model_type']} Ready")
        st.sidebar.text(f"Config: {model_info.get('config_dir', '/tmp')}")
    else:
        st.sidebar.warning("❌ YOLO11 non caricato")

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
        index=0,
        disabled=not fitness_tracker.model_loaded
    )

    # Aggiorna l'esercizio corrente
    if selected_exercise != fitness_tracker.current_exercise and fitness_tracker.model_loaded:
        fitness_tracker.current_exercise = selected_exercise
        fitness_tracker.rep_counter.reset()
        fitness_tracker.audio_feedback.announce_exercise_start(selected_exercise)

    # Controlli audio
    st.sidebar.subheader("🔊 Audio Settings")

    audio_rate = st.sidebar.slider("Velocità voce", 150, 300, 200, disabled=not fitness_tracker.model_loaded)
    audio_volume = st.sidebar.slider("Volume", 0.1, 1.0, 0.8, disabled=not fitness_tracker.model_loaded)

    if st.sidebar.button("🔧 Test Audio", disabled=not fitness_tracker.model_loaded):
        fitness_tracker.audio_feedback.set_voice_properties(audio_rate, audio_volume)
        fitness_tracker.audio_feedback.test_audio()

    # Form requirement toggle
    require_correct_form = st.sidebar.checkbox(
        "Richiedi forma corretta per conteggio", 
        value=True, 
        disabled=not fitness_tracker.model_loaded
    )
    if fitness_tracker.model_loaded:
        fitness_tracker.rep_counter.set_form_requirement(require_correct_form)

    # Pulsanti principali
    col1, col2, col3 = st.columns(3)

    with col1:
        start_disabled = not fitness_tracker.model_loaded
        start_button = st.button(
            "▶️ Inizia", 
            type="primary",
            disabled=start_disabled,
            help="Attendi che YOLO11 si carichi" if start_disabled else "Avvia il tracking"
        )

    with col2:
        stop_button = st.button("⏹️ Stop", type="secondary")

    with col3:
        reset_button = st.button("🔄 Reset Contatore", disabled=not fitness_tracker.model_loaded)

    # Gestione pulsanti
    if start_button and fitness_tracker.model_loaded:
        if not fitness_tracker.is_running:
            if fitness_tracker.initialize_webcam():
                fitness_tracker.is_running = True
                st.success("✅ Webcam inizializzata. Tracking avviato!")
                st.rerun()
            else:
                st.error("❌ Impossibile inizializzare la webcam")

    if stop_button:
        fitness_tracker.is_running = False
        fitness_tracker.release_webcam()
        st.info("⏹️ Tracking fermato")
        st.rerun()

    if reset_button and fitness_tracker.model_loaded:
        fitness_tracker.rep_counter.reset()
        st.success("🔄 Contatore resettato")

    # Layout principale
    main_col1, main_col2 = st.columns([3, 1])

    with main_col1:
        video_placeholder = st.empty()
        status_placeholder = st.empty()

    with main_col2:
        st.subheader("📊 Statistiche")
        rep_count_placeholder = st.empty()
        form_status_placeholder = st.empty()
        stats_placeholder = st.empty()

        st.subheader("💬 Feedback")
        feedback_placeholder = st.empty()

    # Loop video principale
    if fitness_tracker.is_running and fitness_tracker.webcam and fitness_tracker.model_loaded:
        try:
            ret, frame = fitness_tracker.webcam.read()

            if ret:
                # Processa frame
                processed_frame, evaluation_result = fitness_tracker.process_frame(frame)
                rep_status = fitness_tracker.update_repetitions(evaluation_result)
                fitness_tracker.provide_audio_feedback(evaluation_result, rep_status)

                # Aggiorna UI
                if processed_frame is not None:
                    frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                    video_placeholder.image(frame_rgb, channels="RGB", use_column_width=True)

                # Stats
                rep_count_placeholder.metric(
                    "🔢 Ripetizioni",
                    value=rep_status['count'],
                    delta=1 if rep_status.get('rep_completed', False) else None
                )

                if evaluation_result:
                    form_color = "🟢" if evaluation_result['correct'] else "🔴"
                    form_text = "Corretta" if evaluation_result['correct'] else "Da correggere"
                    form_status_placeholder.metric(f"{form_color} Forma", value=form_text)

                    if evaluation_result['feedback']:
                        feedback_placeholder.info(f"💡 {evaluation_result['feedback']}")

                stats = fitness_tracker.rep_counter.get_statistics()
                stats_placeholder.markdown(f"""
                **📈 Sessione:**
                - 🎯 Ripetizioni: {stats['total_reps']}
                - ✅ Forma corretta: {stats['correct_form_percentage']:.1f}%
                - 📊 Fasi: {stats['total_phases_tracked']}
                """)

                if evaluation_result and 'phase' in evaluation_result:
                    phase_emoji = {'up': '⬆️', 'down': '⬇️', 'transition': '🔄'}
                    phase_icon = phase_emoji.get(evaluation_result['phase'], '❓')
                    status_placeholder.info(f"{phase_icon} Fase: {evaluation_result['phase'].title()}")

                time.sleep(0.05)  # Frame rate control
                st.rerun()

            else:
                st.error("❌ Errore webcam")
                fitness_tracker.is_running = False

        except Exception as e:
            st.error(f"❌ Errore processing: {str(e)}")
            fitness_tracker.is_running = False

    else:
        # Istruzioni
        with main_col1:
            if fitness_tracker.model_loaded:
                st.info("""
                ### 📋 Istruzioni:

                1. **Clicca "Inizia"** per attivare webcam
                2. **Posizionati** con tutto il corpo visibile  
                3. **Inizia l'esercizio** - YOLO11 rileverà i movimenti
                4. **Segui il feedback audio** per migliorare

                ### 🎯 Esercizi:
                - **Squat**: Schiena dritta, scendi profondo
                - **Push-up**: Corpo dritto, scendi completamente  
                - **Curl**: Gomiti vicini al corpo
                """)
            else:
                st.warning("""
                ### ⏳ Caricamento YOLO11...

                **Il modello si sta caricando:**
                - Prima volta: Download ~20MB
                - Tempo: 30-60 secondi  
                - Setup automatico configurazione

                **Attendi il completamento per iniziare! ⏳**
                """)

        with main_col2:
            if fitness_tracker.model_loaded:
                st.success("""
                ### ✅ Sistema Pronto!

                - 🤖 YOLO11 Caricato
                - 🔊 Audio Attivo
                - 📸 Webcam Pronta

                **Clicca "Inizia"!**
                """)
            else:
                st.info("""
                ### ⏳ Caricamento...

                YOLO11 si sta preparando.

                Prima volta richiede
                download del modello.

                **Pazienza!** ⏳
                """)

    # Footer
    st.markdown("---")
    st.markdown("💪 **Fitness Tracker - YOLO11 Render Edition** 🚀")

if __name__ == "__main__":
    main()
