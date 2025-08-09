"""
Applicazione Streamlit per il fitness tracking con rilevamento pose e feedback audio
"""
import streamlit as st
import cv2
import numpy as np
import time
from PIL import Image

# Import dei moduli personalizzati
from pose_detection import PoseDetector
from posture_evaluation import PostureEvaluator
from repetition_counter import RepetitionCounter
from audio_feedback import AudioFeedback

class FitnessTracker:
    """
    Classe principale per l'applicazione di fitness tracking
    """

    def __init__(self):
        """
        Inizializza tutti i componenti dell'applicazione
        """
        self.pose_detector = PoseDetector()
        self.posture_evaluator = PostureEvaluator()
        self.rep_counter = RepetitionCounter()
        self.audio_feedback = AudioFeedback()

        # Stato dell'applicazione
        self.is_running = False
        self.current_exercise = 'squat'
        self.webcam = None

    def initialize_webcam(self):
        """
        Inizializza la webcam

        Returns:
            bool: True se la webcam è stata inizializzata correttamente
        """
        try:
            self.webcam = cv2.VideoCapture(0)
            self.webcam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            return True
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
        # Rileva la pose
        processed_frame, pose_results = self.pose_detector.detect_pose(frame)

        # Disegna i landmark
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

    def update_repetitions(self, evaluation_result):
        """
        Aggiorna il conteggio delle ripetizioni

        Args:
            evaluation_result: Risultato della valutazione della postura

        Returns:
            dict: Stato aggiornato delle ripetizioni
        """
        return self.rep_counter.update(self.current_exercise, evaluation_result)

    def provide_audio_feedback(self, evaluation_result, rep_status):
        """
        Fornisce feedback audio basandosi sulla valutazione

        Args:
            evaluation_result: Risultato della valutazione
            rep_status: Stato delle ripetizioni
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
        page_title="Fitness Tracker AI",
        page_icon="💪",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("💪 Fitness Tracker AI")
    st.subheader("Rilevamento pose e conteggio ripetizioni con feedback audio")

    # Inizializza l'app in session state
    if 'fitness_tracker' not in st.session_state:
        st.session_state.fitness_tracker = FitnessTracker()

    fitness_tracker = st.session_state.fitness_tracker

    # Sidebar con controlli
    st.sidebar.header("⚙️ Controlli")

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
        index=0
    )

    # Aggiorna l'esercizio corrente
    if selected_exercise != fitness_tracker.current_exercise:
        fitness_tracker.current_exercise = selected_exercise
        fitness_tracker.rep_counter.reset()
        fitness_tracker.audio_feedback.announce_exercise_start(selected_exercise)

    # Controlli audio
    st.sidebar.subheader("🔊 Audio Settings")

    audio_rate = st.sidebar.slider("Velocità voce", 150, 300, 200)
    audio_volume = st.sidebar.slider("Volume", 0.1, 1.0, 0.8)

    if st.sidebar.button("🔧 Test Audio"):
        fitness_tracker.audio_feedback.set_voice_properties(audio_rate, audio_volume)
        fitness_tracker.audio_feedback.test_audio()

    # Form requirement toggle
    require_correct_form = st.sidebar.checkbox("Richiedi forma corretta per conteggio", value=True)
    fitness_tracker.rep_counter.set_form_requirement(require_correct_form)

    # Pulsanti principali
    col1, col2, col3 = st.columns(3)

    with col1:
        start_button = st.button("▶️ Inizia", type="primary")

    with col2:
        stop_button = st.button("⏹️ Stop", type="secondary")

    with col3:
        reset_button = st.button("🔄 Reset Contatore")

    # Gestione pulsanti
    if start_button:
        if not fitness_tracker.is_running:
            if fitness_tracker.initialize_webcam():
                fitness_tracker.is_running = True
                st.success("✅ Webcam inizializzata. Tracking avviato!")
            else:
                st.error("❌ Impossibile inizializzare la webcam")

    if stop_button:
        fitness_tracker.is_running = False
        fitness_tracker.release_webcam()
        st.info("⏹️ Tracking fermato")

    if reset_button:
        fitness_tracker.rep_counter.reset()
        st.success("🔄 Contatore resettato")

    # Layout principale con colonne
    main_col1, main_col2 = st.columns([3, 1])

    with main_col1:
        # Placeholder per il video
        video_placeholder = st.empty()

        # Placeholder per i messaggi di stato
        status_placeholder = st.empty()

    with main_col2:
        # Pannello informazioni
        st.subheader("📊 Statistiche")

        # Contatori
        rep_count_placeholder = st.empty()
        form_status_placeholder = st.empty()

        # Statistiche dettagliate
        stats_placeholder = st.empty()

        # Feedback corrente
        st.subheader("💬 Feedback")
        feedback_placeholder = st.empty()

    # Loop principale per il processing video
    if fitness_tracker.is_running and fitness_tracker.webcam:

        try:
            # Leggi frame dalla webcam
            ret, frame = fitness_tracker.webcam.read()

            if ret:
                # Processa il frame
                processed_frame, evaluation_result = fitness_tracker.process_frame(frame)

                # Aggiorna le ripetizioni
                rep_status = fitness_tracker.update_repetitions(evaluation_result)

                # Fornisci feedback audio
                fitness_tracker.provide_audio_feedback(evaluation_result, rep_status)

                # Aggiorna l'interfaccia

                # Video feed
                frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                video_placeholder.image(frame_rgb, channels="RGB", use_column_width=True)

                # Conteggio ripetizioni
                rep_count_placeholder.metric(
                    "🔢 Ripetizioni",
                    value=rep_status['count'],
                    delta=1 if rep_status.get('rep_completed', False) else None
                )

                # Stato forma
                if evaluation_result:
                    form_color = "🟢" if evaluation_result['correct'] else "🔴"
                    form_text = "Corretta" if evaluation_result['correct'] else "Da correggere"
                    form_status_placeholder.metric(
                        f"{form_color} Forma",
                        value=form_text
                    )

                    # Feedback
                    if evaluation_result['feedback']:
                        feedback_placeholder.info(f"💡 {evaluation_result['feedback']}")

                # Statistiche
                stats = fitness_tracker.rep_counter.get_statistics()
                stats_placeholder.markdown(f"""
                **📈 Dettagli Sessione:**
                - 🎯 Ripetizioni totali: {stats['total_reps']}
                - ✅ Forma corretta: {stats['correct_form_percentage']:.1f}%
                - 📊 Fasi tracciate: {stats['total_phases_tracked']}
                """)

                # Status message
                if evaluation_result and 'phase' in evaluation_result:
                    phase_emoji = {
                        'up': '⬆️',
                        'down': '⬇️',
                        'transition': '🔄'
                    }
                    phase_icon = phase_emoji.get(evaluation_result['phase'], '❓')
                    status_placeholder.info(f"{phase_icon} Fase: {evaluation_result['phase'].title()}")

            else:
                st.error("❌ Errore nella lettura del frame dalla webcam")
                fitness_tracker.is_running = False

        except Exception as e:
            st.error(f"❌ Errore durante il processing: {str(e)}")
            fitness_tracker.is_running = False

    elif fitness_tracker.is_running and not fitness_tracker.webcam:
        st.warning("⚠️ Webcam non disponibile. Clicca 'Inizia' per riavviare.")

    else:
        # Mostra istruzioni quando l'app non è in esecuzione
        with main_col1:
            st.info("""
            ### 📋 Istruzioni per l'uso:

            1. **Seleziona l'esercizio** dalla barra laterale
            2. **Clicca "Inizia"** per attivare la webcam
            3. **Posizionati** davanti alla camera in modo che tutto il corpo sia visibile
            4. **Inizia l'esercizio** - il sistema rileverà automaticamente i tuoi movimenti
            5. **Mantieni la forma corretta** per far conteggiare le ripetizioni
            6. **Ascolta il feedback audio** per migliorare la tecnica

            ### 🎯 Esercizi supportati:
            - **Squat**: Scendi mantenendo la schiena dritta
            - **Push-up**: Mantieni il corpo dritto e scendi completamente
            - **Curl Bicipiti**: Tieni i gomiti vicini al corpo
            """)

        with main_col2:
            st.info("""
            ### 🔊 Audio Feedback:

            Il sistema fornirà:
            - ✅ Conferma ripetizioni
            - ⚠️ Correzioni postura
            - 📊 Aggiornamenti progresso

            **Assicurati che le cuffie siano collegate!**
            """)

    # Footer
    st.markdown("---")
    st.markdown("💪 **Fitness Tracker AI** - Mantieni la forma, raggiungi i tuoi obiettivi!")

if __name__ == "__main__":
    main()
