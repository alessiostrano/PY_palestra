"""
Fitness Tracker AI - Con st.camera_input per Streamlit Cloud
Questa versione FUNZIONA su server remoti senza webcam fisica!
"""
import streamlit as st
import numpy as np
import time
from PIL import Image
import os

# Environment setup
os.environ.setdefault('YOLO_CONFIG_DIR', '/tmp')
os.environ.setdefault('WANDB_DISABLED', 'true')

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

def analyze_image(image, model):
    """Analizza immagine con YOLO11"""
    try:
        import cv2

        # Converti PIL a OpenCV
        opencv_img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        # YOLO11 detection
        results = model(opencv_img, verbose=False, save=False)

        if len(results) > 0 and results[0].keypoints is not None:
            # Disegna keypoints
            annotated = results[0].plot()
            annotated_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)

            # Info rilevamento
            num_people = len(results[0].keypoints.xy)
            keypoints = results[0].keypoints.xy[0] if num_people > 0 else None
            confidence = results[0].keypoints.conf[0] if results[0].keypoints.conf is not None and num_people > 0 else None

            return annotated_rgb, num_people, keypoints, confidence
        else:
            return np.array(image), 0, None, None

    except Exception as e:
        st.error(f"❌ Errore analisi: {e}")
        return np.array(image), 0, None, None

def evaluate_simple_pose(keypoints, confidence, exercise_type):
    """Valutazione semplificata della posa"""
    if keypoints is None or len(keypoints) == 0:
        return "❓ Nessuna persona rilevata", "neutral"

    # Keypoints mapping (COCO format)
    # 5: left_shoulder, 6: right_shoulder, 7: left_elbow, 8: right_elbow
    # 9: left_wrist, 10: right_wrist, 11: left_hip, 12: right_hip  
    # 13: left_knee, 14: right_knee, 15: left_ankle, 16: right_ankle

    try:
        # Controlla se keypoints principali sono visibili
        if confidence is not None:
            key_points_conf = {
                'shoulders': (confidence[5] + confidence[6]) / 2 if len(confidence) > 6 else 0,
                'elbows': (confidence[7] + confidence[8]) / 2 if len(confidence) > 8 else 0,
                'hips': (confidence[11] + confidence[12]) / 2 if len(confidence) > 12 else 0,
                'knees': (confidence[13] + confidence[14]) / 2 if len(confidence) > 14 else 0
            }

            # Valutazione basata su visibilità keypoints
            if exercise_type == "squat":
                if key_points_conf['knees'] > 0.5 and key_points_conf['hips'] > 0.5:
                    return "🏋️ Posizione squat rilevata! Mantieni la schiena dritta.", "good"
                else:
                    return "⚠️ Posizionati di lato per migliore rilevamento squat", "warning"

            elif exercise_type == "pushup":
                if key_points_conf['shoulders'] > 0.5 and key_points_conf['elbows'] > 0.5:
                    return "💪 Posizione push-up rilevata! Mantieni il corpo dritto.", "good"
                else:
                    return "⚠️ Posizionati di lato per migliore rilevamento push-up", "warning"

            elif exercise_type == "bicep_curl":
                if key_points_conf['elbows'] > 0.5 and key_points_conf['shoulders'] > 0.5:
                    return "🏋️‍♀️ Posizione curl rilevata! Mantieni i gomiti vicini al corpo.", "good"
                else:
                    return "⚠️ Posizionati frontalmente per migliore rilevamento curl", "warning"

        return "👤 Persona rilevata - continua con l'esercizio!", "neutral"

    except:
        return "👤 Analisi pose in corso...", "neutral"

def main():
    st.set_page_config(
        page_title="💪 Fitness Tracker AI",
        page_icon="💪",
        layout="wide"
    )

    st.title("💪 Fitness Tracker AI")
    st.subheader("📸 Versione Camera Cloud - Streamlit Compatible")

    st.info("""
    ### 📸 Modalità Camera Cloud

    **Perfetto per Streamlit Cloud!** Questa versione usa la **camera del tuo dispositivo** 
    tramite il browser, non richiede webcam sul server.

    1. **Seleziona esercizio**
    2. **Scatta foto** con il pulsante camera
    3. **Analisi automatica** con YOLO11
    """)

    # Sidebar controlli
    st.sidebar.header("⚙️ Controlli")

    # Selezione esercizio
    exercise_type = st.sidebar.selectbox(
        "🎯 Seleziona esercizio:",
        ["squat", "pushup", "bicep_curl"],
        format_func=lambda x: {"squat": "🏋️ Squat", "pushup": "💪 Push-up", "bicep_curl": "🏋️‍♀️ Curl Bicipiti"}[x]
    )

    # Carica modello
    if 'model' not in st.session_state:
        st.session_state.model = None

    if st.sidebar.button("🤖 Carica YOLO11", type="primary"):
        st.session_state.model = load_yolo_model()
        if st.session_state.model:
            st.sidebar.success("✅ YOLO11 Pronto!")

    if st.session_state.model:
        st.sidebar.success("🤖 YOLO11 Caricato")

    # Camera input - FUNZIONA SU STREAMLIT CLOUD!
    st.subheader("📸 Camera Input")

    camera_input = st.camera_input(
        "📷 Scatta una foto durante l'esercizio:",
        help="Assicurati che tutto il corpo sia visibile"
    )

    if camera_input and st.session_state.model:
        # Analizza immagine
        image = Image.open(camera_input)

        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("📷 Foto Scattata")
            st.image(image, use_column_width=True)

        with col2:
            st.subheader("🤖 Analisi YOLO11")

            with st.spinner("🔄 Analizzando..."):
                analyzed_img, num_people, keypoints, confidence = analyze_image(image, st.session_state.model)

            st.image(analyzed_img, use_column_width=True)

            # Risultati
            if num_people > 0:
                st.success(f"✅ {num_people} persona/e rilevata/e!")

                # Valutazione pose specifica per esercizio
                feedback, status = evaluate_simple_pose(keypoints, confidence, exercise_type)

                if status == "good":
                    st.success(feedback)
                elif status == "warning":
                    st.warning(feedback)
                else:
                    st.info(feedback)

                # Statistiche
                if confidence is not None:
                    avg_conf = float(confidence.mean())
                    st.metric("🎯 Confidence Media", f"{avg_conf:.1%}")

                st.metric("📊 Keypoints Rilevati", len(keypoints))

            else:
                st.warning("⚠️ Nessuna persona rilevata")
                st.info("""
                **Suggerimenti:**
                - Corpo completamente visibile nella foto
                - Buona illuminazione
                - Sfondo semplice
                - Distanza 2-3 metri dalla camera
                """)

    elif camera_input and not st.session_state.model:
        st.warning("⚠️ Carica prima il modello YOLO11!")

    # Istruzioni esercizi
    st.subheader(f"🎯 Istruzioni {exercise_type.title()}")

    exercise_instructions = {
        "squat": {
            "setup": "Piedi alla larghezza delle spalle",
            "movimento": "Scendi mantenendo la schiena dritta",
            "tips": "Ginocchia allineate ai piedi, peso sui talloni",
            "camera": "Posizionati di LATO rispetto alla camera"
        },
        "pushup": {
            "setup": "Posizione plank, braccia tese",
            "movimento": "Scendi fino a sfiorare il pavimento",
            "tips": "Corpo dritto come una tavola", 
            "camera": "Posizionati di LATO rispetto alla camera"
        },
        "bicep_curl": {
            "setup": "In piedi, braccia lungo i fianchi",
            "movimento": "Fletti i gomiti mantenendoli vicini al corpo",
            "tips": "Solo gli avambracci si muovono",
            "camera": "Posizionati FRONTALE alla camera"
        }
    }

    instructions = exercise_instructions[exercise_type]

    col1, col2 = st.columns(2)
    with col1:
        st.info(f"""
        **📋 Setup:**
        {instructions['setup']}

        **🔄 Movimento:**  
        {instructions['movimento']}
        """)

    with col2:
        st.success(f"""
        **💡 Tips:**
        {instructions['tips']}

        **📸 Camera:**
        {instructions['camera']}
        """)

    # File upload alternativo
    st.subheader("📁 Upload Immagine (Alternativo)")
    uploaded_file = st.file_uploader(
        "O carica un'immagine dal dispositivo:",
        type=['png', 'jpg', 'jpeg'],
        help="Se la camera non funziona, usa questa opzione"
    )

    if uploaded_file and st.session_state.model:
        image = Image.open(uploaded_file)

        with st.spinner("🔄 Analizzando immagine caricata..."):
            analyzed_img, num_people, keypoints, confidence = analyze_image(image, st.session_state.model)

        col1, col2 = st.columns(2)

        with col1:
            st.image(image, caption="Immagine Caricata", use_column_width=True)
        with col2:
            st.image(analyzed_img, caption="Analisi YOLO11", use_column_width=True)

        if num_people > 0:
            feedback, status = evaluate_simple_pose(keypoints, confidence, exercise_type)
            if status == "good":
                st.success(feedback)
            elif status == "warning":
                st.warning(feedback)
            else:
                st.info(feedback)

    # Footer
    st.markdown("---")
    st.markdown("💪 **Fitness Tracker AI - Camera Cloud Edition** 🚀")
    st.markdown("*Perfetto per Streamlit Community Cloud - Nessuna webcam server richiesta!*")

if __name__ == "__main__":
    main()
