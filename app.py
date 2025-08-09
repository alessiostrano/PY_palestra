"""
Fitness Tracker AI - Versione Ultra Compatibile Python 3.13
"""
import streamlit as st
import os
import sys
import time

# Environment setup
os.environ.setdefault('YOLO_CONFIG_DIR', '/tmp')
os.environ.setdefault('WANDB_DISABLED', 'true')

def check_dependencies():
    """Controlla e mostra status delle dipendenze"""
    deps = {}

    # OpenCV
    try:
        import cv2
        deps['opencv'] = f"✅ OpenCV {cv2.__version__}"
        opencv_ok = True
    except Exception as e:
        deps['opencv'] = f"❌ OpenCV: {str(e)[:50]}"
        opencv_ok = False

    # NumPy
    try:
        import numpy as np
        deps['numpy'] = f"✅ NumPy {np.__version__}"
        numpy_ok = True
    except Exception as e:
        deps['numpy'] = f"❌ NumPy: {str(e)[:50]}"
        numpy_ok = False

    # Ultralytics
    try:
        from ultralytics import YOLO
        deps['ultralytics'] = "✅ Ultralytics OK"
        yolo_ok = True
    except Exception as e:
        deps['ultralytics'] = f"❌ Ultralytics: {str(e)[:50]}"
        yolo_ok = False

    # PIL
    try:
        from PIL import Image
        deps['pillow'] = "✅ Pillow OK"
        pil_ok = True
    except Exception as e:
        deps['pillow'] = f"❌ Pillow: {str(e)[:50]}"
        pil_ok = False

    all_ok = opencv_ok and numpy_ok and yolo_ok and pil_ok
    return deps, all_ok

def load_yolo_model():
    """Carica il modello YOLO11 con gestione errori"""
    try:
        from ultralytics import YOLO
        with st.spinner("🤖 Caricamento YOLO11..."):
            model = YOLO('yolo11n-pose.pt')
            # Test rapido
            import numpy as np
            test_img = np.zeros((640, 480, 3), dtype=np.uint8)
            _ = model(test_img, verbose=False, save=False)
        return model, True
    except Exception as e:
        st.error(f"❌ Errore YOLO11: {str(e)}")
        return None, False

def demo_mode():
    """Modalità demo con upload immagini"""
    st.subheader("📸 Demo Mode - Upload Immagini")

    uploaded_file = st.file_uploader(
        "Carica una foto del tuo esercizio:",
        type=['png', 'jpg', 'jpeg'],
        help="Assicurati che il corpo sia completamente visibile"
    )

    if uploaded_file:
        from PIL import Image
        image = Image.open(uploaded_file)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📷 Immagine Originale")
            st.image(image, use_column_width=True)

        with col2:
            st.subheader("🤖 Analisi")

            if 'model' in st.session_state and st.session_state.model:
                try:
                    import cv2
                    import numpy as np

                    # Converti PIL a OpenCV
                    opencv_img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

                    # Analisi YOLO11
                    with st.spinner("🔄 Analisi in corso..."):
                        results = st.session_state.model(opencv_img, verbose=False, save=False)

                    if len(results) > 0 and results[0].keypoints is not None:
                        # Disegna risultati
                        annotated = results[0].plot()
                        annotated_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
                        st.image(annotated_rgb, use_column_width=True)

                        # Info rilevamento
                        num_people = len(results[0].keypoints.xy)
                        st.success(f"✅ Rilevate {num_people} persona/e!")

                        if num_people > 0:
                            keypoints = results[0].keypoints.xy[0]
                            confidence = results[0].keypoints.conf[0] if results[0].keypoints.conf is not None else None

                            st.info(f"📊 Keypoints rilevati: {len(keypoints)}")
                            if confidence is not None:
                                avg_conf = float(confidence.mean())
                                st.metric("🎯 Confidence Media", f"{avg_conf:.1%}")

                    else:
                        st.warning("⚠️ Nessuna persona rilevata nell'immagine")
                        st.info("Suggerimenti:\n- Corpo completamente visibile\n- Buona illuminazione\n- Posizione frontale o laterale")

                except Exception as e:
                    st.error(f"❌ Errore nell'analisi: {str(e)}")
            else:
                st.warning("⚠️ Modello YOLO11 non caricato")

def webcam_mode():
    """Modalità webcam in tempo reale"""
    st.subheader("📹 Webcam Mode - Tempo Reale")

    if 'webcam_running' not in st.session_state:
        st.session_state.webcam_running = False

    col1, col2 = st.columns(2)

    with col1:
        if st.button("▶️ Avvia Webcam", type="primary"):
            st.session_state.webcam_running = True
            st.rerun()

    with col2:
        if st.button("⏹️ Ferma Webcam"):
            st.session_state.webcam_running = False
            st.rerun()

    if st.session_state.webcam_running:
        try:
            import cv2

            # Inizializza webcam
            if 'webcam' not in st.session_state or st.session_state.webcam is None:
                for i in range(4):
                    cap = cv2.VideoCapture(i)
                    if cap.isOpened():
                        ret, frame = cap.read()
                        if ret:
                            st.session_state.webcam = cap
                            break
                        cap.release()

                if 'webcam' not in st.session_state or st.session_state.webcam is None:
                    st.error("❌ Nessuna webcam disponibile")
                    return

            # Leggi frame
            ret, frame = st.session_state.webcam.read()

            if ret:
                # Processa con YOLO11 se disponibile
                if 'model' in st.session_state and st.session_state.model:
                    try:
                        results = st.session_state.model(frame, verbose=False, save=False)
                        if len(results) > 0 and results[0].keypoints is not None:
                            frame = results[0].plot()
                    except:
                        pass  # Usa frame originale se errore

                # Mostra frame
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                st.image(frame_rgb, channels="RGB", use_column_width=True)

                # Auto-refresh
                time.sleep(0.1)
                st.rerun()
            else:
                st.error("❌ Errore lettura webcam")

        except Exception as e:
            st.error(f"❌ Errore webcam: {str(e)}")
    else:
        st.info("""
        ### 📋 Modalità Webcam:

        1. **Clicca "Avvia Webcam"**
        2. **Consenti accesso** camera nel browser
        3. **Posizionati** davanti alla camera
        4. **Il sistema rileverà** automaticamente la tua pose

        **Nota**: Richiede webcam funzionante e permessi browser
        """)

def main():
    st.set_page_config(
        page_title="💪 Fitness Tracker AI",
        page_icon="💪",
        layout="wide"
    )

    st.title("💪 Fitness Tracker AI")
    st.subheader("🚀 Versione Ultra-Compatibile Python 3.13")

    # Info sistema
    st.sidebar.header("ℹ️ Sistema")
    st.sidebar.info(f"🐍 Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

    # Controlla dipendenze
    with st.spinner("🔍 Controllo dipendenze..."):
        deps, all_ok = check_dependencies()

    st.sidebar.subheader("📦 Dipendenze")
    for name, status in deps.items():
        if "✅" in status:
            st.sidebar.success(status)
        else:
            st.sidebar.error(status)

    if not all_ok:
        st.error("""
        ❌ **Alcune dipendenze mancano!**

        **Per risolvere:**
        1. Controlla che tutti i packages siano installati
        2. Prova a fare refresh della pagina
        3. Riavvia l'applicazione se necessario
        """)
        return

    # Carica modello YOLO11
    if 'model_loaded' not in st.session_state:
        st.session_state.model_loaded = False

    if not st.session_state.model_loaded:
        if st.button("🤖 Carica Modello YOLO11", type="primary"):
            model, success = load_yolo_model()
            if success:
                st.session_state.model = model
                st.session_state.model_loaded = True
                st.success("✅ YOLO11 caricato con successo!")
                st.rerun()
    else:
        st.sidebar.success("🤖 YOLO11 Pronto")

    # Modalità operative
    st.subheader("🎯 Modalità Operative")

    mode = st.radio(
        "Scegli modalità:",
        ["📸 Demo (Upload Immagini)", "📹 Webcam (Tempo Reale)"],
        horizontal=True
    )

    if mode == "📸 Demo (Upload Immagini)":
        demo_mode()
    elif mode == "📹 Webcam (Tempo Reale)":
        webcam_mode()

    # Istruzioni
    with st.expander("📖 Istruzioni"):
        st.markdown("""
        ### 🎯 Come usare:

        **Modalità Demo:**
        1. Scatta una foto mentre fai un esercizio
        2. Carica la foto usando il pulsante upload
        3. Visualizza l'analisi YOLO11 con keypoints

        **Modalità Webcam:**  
        1. Clicca "Avvia Webcam"
        2. Consenti accesso alla camera
        3. Posizionati davanti alla webcam
        4. Muoviti per vedere il tracking in tempo reale

        ### 🏋️ Esercizi supportati:
        - **Squat**: Posizione laterale per migliore rilevamento
        - **Push-up**: Posizione laterale, corpo dritto
        - **Pose generiche**: Qualsiasi movimento corporeo

        ### 💡 Tips:
        - **Illuminazione**: Buona luce naturale
        - **Sfondo**: Semplice e uniforme
        - **Posizione**: Corpo completamente visibile
        - **Distanza**: 2-3 metri dalla camera
        """)

    # Footer
    st.markdown("---")
    st.markdown("💪 **Fitness Tracker AI - Ultra Compatible Edition** 🚀")
    st.markdown("*Ottimizzato per Python 3.13 e deployment cloud*")

if __name__ == "__main__":
    main()
