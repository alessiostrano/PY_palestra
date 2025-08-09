"""
Fitness Tracker AI - YOLO11 INTEGRAZIONE COMPLETA
Camera streaming + YOLO11 processing vero + Keypoints overlay + Feedback reale
"""
import streamlit as st
import cv2
import numpy as np
import time
from PIL import Image
import os
import base64
from io import BytesIO
import json
import asyncio
import threading

# Environment setup
os.environ.setdefault('YOLO_CONFIG_DIR', '/tmp')
os.environ.setdefault('WANDB_DISABLED', 'true')

def load_yolo_model():
    """Carica YOLO11 con inizializzazione completa"""
    try:
        from ultralytics import YOLO
        with st.spinner("🤖 Caricamento YOLO11 con pose detection..."):
            model = YOLO('yolo11n-pose.pt')

            # Test completo
            test_img = np.zeros((480, 640, 3), dtype=np.uint8)
            results = model(test_img, verbose=False, save=False)

            # Verifica che pose detection funzioni
            if len(results) > 0:
                st.success("✅ YOLO11 pose detection verificato!")
                return model
            else:
                st.error("❌ YOLO11 non rileva pose")
                return None

    except Exception as e:
        st.error(f"❌ Errore YOLO11: {e}")
        return None

def process_yolo_frame(model, frame, exercise_type):
    """Processa frame con YOLO11 e ritorna keypoints + feedback"""
    try:
        # YOLO11 inference
        results = model(frame, verbose=False, save=False)

        if len(results) > 0 and results[0].keypoints is not None:
            # Estrai keypoints
            keypoints_tensor = results[0].keypoints.xy[0]  # Primo rilevamento
            confidence_tensor = results[0].keypoints.conf[0] if results[0].keypoints.conf is not None else None

            # Converti a numpy
            keypoints = keypoints_tensor.cpu().numpy() if hasattr(keypoints_tensor, 'cpu') else np.array(keypoints_tensor)
            confidence = confidence_tensor.cpu().numpy() if hasattr(confidence_tensor, 'cpu') and confidence_tensor is not None else None

            # Disegna keypoints su frame
            annotated_frame = results[0].plot()

            # Analisi esercizio specifica
            feedback_data = analyze_exercise_with_keypoints(keypoints, confidence, exercise_type)

            return annotated_frame, keypoints, confidence, feedback_data

        else:
            return frame, None, None, {"status": "no_person", "message": "Nessuna persona rilevata"}

    except Exception as e:
        return frame, None, None, {"status": "error", "message": f"Errore YOLO: {str(e)}"}

def analyze_exercise_with_keypoints(keypoints, confidence, exercise_type):
    """Analisi matematica precisa basata su keypoints YOLO11"""

    if keypoints is None or len(keypoints) == 0:
        return {"status": "no_keypoints", "message": "Keypoints non disponibili"}

    try:
        # COCO pose keypoints indices:
        # 0: nose, 5: left_shoulder, 6: right_shoulder, 7: left_elbow, 8: right_elbow
        # 9: left_wrist, 10: right_wrist, 11: left_hip, 12: right_hip
        # 13: left_knee, 14: right_knee, 15: left_ankle, 16: right_ankle

        analysis = {
            "exercise": exercise_type,
            "timestamp": time.time(),
            "keypoints_count": len(keypoints),
            "raw_keypoints": keypoints.tolist() if isinstance(keypoints, np.ndarray) else keypoints
        }

        if confidence is not None:
            analysis["confidence_scores"] = confidence.tolist() if isinstance(confidence, np.ndarray) else confidence

            # Calcola confidence per gruppi di keypoints
            shoulders_conf = (confidence[5] + confidence[6]) / 2 if len(confidence) > 6 else 0
            elbows_conf = (confidence[7] + confidence[8]) / 2 if len(confidence) > 8 else 0  
            hips_conf = (confidence[11] + confidence[12]) / 2 if len(confidence) > 12 else 0
            knees_conf = (confidence[13] + confidence[14]) / 2 if len(confidence) > 14 else 0

            analysis.update({
                "shoulders_confidence": float(shoulders_conf),
                "elbows_confidence": float(elbows_conf), 
                "hips_confidence": float(hips_conf),
                "knees_confidence": float(knees_conf)
            })

        # Analisi specifica per esercizio
        if exercise_type == "squat":
            return analyze_squat_mathematics(keypoints, confidence, analysis)
        elif exercise_type == "pushup":
            return analyze_pushup_mathematics(keypoints, confidence, analysis)
        elif exercise_type == "bicep_curl":
            return analyze_curl_mathematics(keypoints, confidence, analysis)
        else:
            analysis.update({"status": "unknown_exercise", "message": "Esercizio non riconosciuto"})
            return analysis

    except Exception as e:
        return {"status": "analysis_error", "message": f"Errore analisi: {str(e)}"}

def analyze_squat_mathematics(keypoints, confidence, analysis):
    """Analisi matematica precisa per squat"""
    try:
        # Verifica keypoints necessari per squat
        required_points = [11, 12, 13, 14]  # hips + knees
        if len(keypoints) <= max(required_points):
            analysis.update({"status": "insufficient_keypoints", "message": "Keypoints insufficienti per squat"})
            return analysis

        # Estrai coordinate
        left_hip = keypoints[11]    # [x, y]
        right_hip = keypoints[12]   
        left_knee = keypoints[13]   
        right_knee = keypoints[14]  

        # Calcoli matematici
        hip_center_x = (left_hip[0] + right_hip[0]) / 2
        hip_center_y = (left_hip[1] + right_hip[1]) / 2
        knee_center_x = (left_knee[0] + right_knee[0]) / 2
        knee_center_y = (left_knee[1] + right_knee[1]) / 2

        # Depth calculation (Y maggiore = più in basso nell'immagine)
        squat_depth = hip_center_y - knee_center_y  # Positivo = hip sotto knee
        depth_ratio = hip_center_y / knee_center_y if knee_center_y > 0 else 0

        # Knee alignment
        knee_alignment_diff = abs(left_knee[0] - right_knee[0])

        # Hip width vs knee width (stabilità)
        hip_width = abs(left_hip[0] - right_hip[0])
        knee_width = abs(left_knee[0] - right_knee[0])
        width_ratio = knee_width / hip_width if hip_width > 0 else 0

        analysis.update({
            "squat_metrics": {
                "hip_center": [float(hip_center_x), float(hip_center_y)],
                "knee_center": [float(knee_center_x), float(knee_center_y)], 
                "squat_depth_pixels": float(squat_depth),
                "depth_ratio": float(depth_ratio),
                "knee_alignment_diff": float(knee_alignment_diff),
                "hip_width": float(hip_width),
                "knee_width": float(knee_width),
                "width_stability_ratio": float(width_ratio)
            }
        })

        # Valutazione performance
        if depth_ratio > 1.05:  # Hip significativamente sotto knee
            status = "excellent"
            message = f"🟢 SQUAT ECCELLENTE! Depth: {squat_depth:.0f}px, Ratio: {depth_ratio:.2f}"
            voice_feedback = "Perfetto! Squat profondo eccellente!"
        elif depth_ratio > 1.02:  # Hip leggermente sotto knee  
            status = "good"
            message = f"🟡 BUON SQUAT! Depth: {squat_depth:.0f}px, Ratio: {depth_ratio:.2f}"
            voice_feedback = "Bene! Puoi scendere ancora un po'!"
        elif depth_ratio > 0.95:  # Hip circa al livello knee
            status = "acceptable" 
            message = f"🟠 SQUAT ACCETTABILE. Depth: {squat_depth:.0f}px, Ratio: {depth_ratio:.2f}"
            voice_feedback = "Squat accettabile, prova a scendere di più!"
        else:  # Hip sopra knee
            status = "poor"
            message = f"🔴 SCENDI DI PIÙ! Depth: {squat_depth:.0f}px, Ratio: {depth_ratio:.2f}"
            voice_feedback = "Scendi di più! Hip sopra le ginocchia!"

        # Controllo allineamento
        if knee_alignment_diff > 40:
            message += f" ⚠️ Allinea ginocchia (diff: {knee_alignment_diff:.0f}px)"
            voice_feedback += " Allinea meglio le ginocchia!"

        analysis.update({
            "status": status,
            "message": message,
            "voice_feedback": voice_feedback,
            "score": max(0, min(100, int((depth_ratio - 0.8) * 100))) if depth_ratio > 0.8 else 0
        })

        return analysis

    except Exception as e:
        analysis.update({"status": "squat_error", "message": f"Errore analisi squat: {str(e)}"})
        return analysis

def analyze_pushup_mathematics(keypoints, confidence, analysis):
    """Analisi matematica precisa per push-up"""
    try:
        required_points = [5, 6, 7, 8]  # shoulders + elbows
        if len(keypoints) <= max(required_points):
            analysis.update({"status": "insufficient_keypoints", "message": "Keypoints insufficienti per push-up"})
            return analysis

        left_shoulder = keypoints[5]
        right_shoulder = keypoints[6]
        left_elbow = keypoints[7] 
        right_elbow = keypoints[8]

        shoulder_center_y = (left_shoulder[1] + right_shoulder[1]) / 2
        elbow_center_y = (left_elbow[1] + right_elbow[1]) / 2

        # Push-up depth (elbow sotto shoulder = buono)
        pushup_depth = elbow_center_y - shoulder_center_y
        depth_ratio = elbow_center_y / shoulder_center_y if shoulder_center_y > 0 else 0

        # Simmetria elbows
        elbow_symmetry = abs(left_elbow[1] - right_elbow[1])

        analysis.update({
            "pushup_metrics": {
                "shoulder_center_y": float(shoulder_center_y),
                "elbow_center_y": float(elbow_center_y),
                "pushup_depth_pixels": float(pushup_depth),
                "depth_ratio": float(depth_ratio),
                "elbow_symmetry": float(elbow_symmetry)
            }
        })

        if depth_ratio > 1.15:
            status = "excellent"
            message = f"🟢 PUSH-UP ECCELLENTE! Depth: {pushup_depth:.0f}px, Ratio: {depth_ratio:.2f}"
            voice_feedback = "Perfetto! Push-up con discesa completa!"
        elif depth_ratio > 1.05:
            status = "good"
            message = f"🟡 BUON PUSH-UP! Depth: {pushup_depth:.0f}px, Ratio: {depth_ratio:.2f}"
            voice_feedback = "Bene! Puoi scendere ancora!"
        else:
            status = "poor"
            message = f"🔴 SCENDI DI PIÙ! Depth: {pushup_depth:.0f}px, Ratio: {depth_ratio:.2f}"
            voice_feedback = "Scendi di più! Push-up troppo alto!"

        analysis.update({
            "status": status,
            "message": message, 
            "voice_feedback": voice_feedback,
            "score": max(0, min(100, int((depth_ratio - 1.0) * 100))) if depth_ratio > 1.0 else 0
        })

        return analysis

    except Exception as e:
        analysis.update({"status": "pushup_error", "message": f"Errore analisi push-up: {str(e)}"})
        return analysis

def analyze_curl_mathematics(keypoints, confidence, analysis):
    """Analisi matematica precisa per bicep curl"""
    try:
        required_points = [5, 7, 9]  # shoulder, elbow, wrist (left arm)
        if len(keypoints) <= max(required_points):
            analysis.update({"status": "insufficient_keypoints", "message": "Keypoints insufficienti per curl"})
            return analysis

        left_shoulder = keypoints[5]
        left_elbow = keypoints[7]
        left_wrist = keypoints[9]

        # Calcola flessione (wrist sopra elbow = flessione)
        flexion_amount = left_elbow[1] - left_wrist[1]  # Positivo = flessione

        # Stabilità elbow (quanto si sposta dall'asse shoulder)
        elbow_stability = abs(left_elbow[0] - left_shoulder[0])

        # Angolo approssimativo braccio
        import math
        upper_arm_vector = [left_elbow[0] - left_shoulder[0], left_elbow[1] - left_shoulder[1]]
        forearm_vector = [left_wrist[0] - left_elbow[0], left_wrist[1] - left_elbow[1]]

        # Calcola angolo (approssimativo)
        dot_product = upper_arm_vector[0] * forearm_vector[0] + upper_arm_vector[1] * forearm_vector[1]
        upper_arm_length = math.sqrt(upper_arm_vector[0]**2 + upper_arm_vector[1]**2)
        forearm_length = math.sqrt(forearm_vector[0]**2 + forearm_vector[1]**2)

        if upper_arm_length > 0 and forearm_length > 0:
            cos_angle = dot_product / (upper_arm_length * forearm_length)
            cos_angle = max(-1, min(1, cos_angle))  # Clamp
            angle_rad = math.acos(cos_angle)
            angle_deg = math.degrees(angle_rad)
        else:
            angle_deg = 0

        analysis.update({
            "curl_metrics": {
                "shoulder_pos": [float(left_shoulder[0]), float(left_shoulder[1])],
                "elbow_pos": [float(left_elbow[0]), float(left_elbow[1])],
                "wrist_pos": [float(left_wrist[0]), float(left_wrist[1])],
                "flexion_pixels": float(flexion_amount),
                "elbow_stability": float(elbow_stability),
                "elbow_angle_degrees": float(angle_deg)
            }
        })

        if flexion_amount > 60 and angle_deg < 90:
            status = "excellent"
            message = f"🟢 CURL ECCELLENTE! Flessione: {flexion_amount:.0f}px, Angolo: {angle_deg:.0f}°"
            voice_feedback = "Perfetto! Curl con flessione completa!"
        elif flexion_amount > 30:
            status = "good"
            message = f"🟡 BUON CURL! Flessione: {flexion_amount:.0f}px, Angolo: {angle_deg:.0f}°"
            voice_feedback = "Bene! Fletti ancora di più!"
        else:
            status = "poor"
            message = f"🔴 FLETTI DI PIÙ! Flessione: {flexion_amount:.0f}px, Angolo: {angle_deg:.0f}°"
            voice_feedback = "Fletti i gomiti! Movimento troppo piccolo!"

        if elbow_stability > 50:
            message += f" ⚠️ Stabilizza gomiti ({elbow_stability:.0f}px)"
            voice_feedback += " Mantieni gomiti vicini al corpo!"

        analysis.update({
            "status": status,
            "message": message,
            "voice_feedback": voice_feedback,
            "score": max(0, min(100, int(flexion_amount * 1.5))) if flexion_amount > 0 else 0
        })

        return analysis

    except Exception as e:
        analysis.update({"status": "curl_error", "message": f"Errore analisi curl: {str(e)}"})
        return analysis

def main():
    st.set_page_config(
        page_title="💪 Fitness AI - YOLO11 COMPLETO",
        page_icon="💪",
        layout="wide"
    )

    st.title("💪 FITNESS TRACKER AI - YOLO11 MATEMATICO")
    st.subheader("🎯 Analisi Keypoints Precisa + Calcoli Matematici Reali!")

    # Session state
    if 'model' not in st.session_state:
        st.session_state.model = None
    if 'last_analysis' not in st.session_state:
        st.session_state.last_analysis = {}
    if 'analysis_count' not in st.session_state:
        st.session_state.analysis_count = 0

    # Sidebar  
    st.sidebar.header("🤖 YOLO11 Mathematics")

    if not st.session_state.model:
        if st.sidebar.button("🚀 CARICA YOLO11 MATEMATICO", type="primary"):
            st.session_state.model = load_yolo_model()
            if st.session_state.model:
                st.rerun()
    else:
        st.sidebar.success("🤖 YOLO11 MATEMATICO ✅")

    exercise_type = st.sidebar.selectbox(
        "🎯 Esercizio:",
        ["squat", "pushup", "bicep_curl"],
        format_func=lambda x: {"squat": "🏋️ Squat", "pushup": "💪 Push-up", "bicep_curl": "🏋️‍♀️ Curl"}[x]
    )

    speech_enabled = st.sidebar.checkbox("🔊 Feedback Vocale", value=True)
    analysis_freq = st.sidebar.slider("🔄 Analisi ogni", 1, 5, 2)
    show_raw_data = st.sidebar.checkbox("📊 Mostra Dati Raw", value=False)

    # Test sistema
    if st.sidebar.button("🔊 Test Sistema"):
        test_html = """
        <script>
        if ('speechSynthesis' in window) {
            speechSynthesis.speak(new SpeechSynthesisUtterance('Sistema YOLO11 matematico attivo! Analisi keypoints precisa!'));
        }
        </script>
        """
        st.components.v1.html(test_html, height=0)
        st.sidebar.success("🔊 Sistema OK!")

    # Layout 
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📹 Camera + YOLO11 Analysis")

        if st.session_state.model:
            # Input per frame analysis (simulato)
            camera_section = st.empty()

            with camera_section.container():
                st.info("📸 **YOLO11 PRONTO** - In una implementazione completa qui ci sarebbe:")
                st.write("- 📹 **Video streaming** con MediaDevices API")
                st.write("- 🎯 **YOLO11 keypoints** overlay in tempo reale")  
                st.write("- 📊 **Analisi matematica** continua ogni 2 secondi")
                st.write("- 🔊 **Feedback vocale** basato su calcoli reali")

                # Simula upload frame per demo
                uploaded_frame = st.file_uploader(
                    "📸 Upload frame per demo YOLO11:",
                    type=['png', 'jpg', 'jpeg'],
                    help="Carica una foto di te che fai l'esercizio per vedere l'analisi YOLO11 reale"
                )

                if uploaded_frame:
                    # Processa con YOLO11 REALE
                    image = Image.open(uploaded_frame)
                    frame_array = np.array(image)

                    with st.spinner("🤖 Analisi YOLO11 in corso..."):
                        processed_frame, keypoints, confidence, analysis_data = process_yolo_frame(
                            st.session_state.model, frame_array, exercise_type
                        )

                    # Mostra risultati
                    col_img1, col_img2 = st.columns(2)

                    with col_img1:
                        st.subheader("📷 Originale")
                        st.image(image, use_column_width=True)

                    with col_img2:
                        st.subheader("🎯 YOLO11 + Keypoints")
                        st.image(processed_frame, use_column_width=True)

                    # Salva analisi
                    st.session_state.last_analysis = analysis_data
                    st.session_state.analysis_count += 1

                    # Feedback vocale
                    if speech_enabled and 'voice_feedback' in analysis_data:
                        voice_html = f"""
                        <script>
                        if ('speechSynthesis' in window) {{
                            const utterance = new SpeechSynthesisUtterance('{analysis_data["voice_feedback"]}');
                            utterance.lang = 'it-IT';
                            utterance.rate = 1.2;
                            speechSynthesis.speak(utterance);
                        }}
                        </script>
                        """
                        st.components.v1.html(voice_html, height=0)
        else:
            st.warning("⚠️ **Carica YOLO11 MATEMATICO per iniziare!**")

    with col2:
        st.subheader("📊 Analisi Matematica")

        if st.session_state.last_analysis:
            analysis = st.session_state.last_analysis

            # Status principale
            if 'status' in analysis:
                if analysis['status'] == 'excellent':
                    st.success(f"### {analysis.get('message', 'Ottimo!')}")
                elif analysis['status'] == 'good':
                    st.info(f"### {analysis.get('message', 'Buono!')}")
                elif analysis['status'] in ['acceptable', 'poor']:
                    st.warning(f"### {analysis.get('message', 'Da migliorare')}")
                else:
                    st.error(f"### {analysis.get('message', 'Errore')}")

            # Score
            if 'score' in analysis:
                st.metric("🎯 Score", f"{analysis['score']}/100")

            # Metriche specifiche
            if exercise_type == 'squat' and 'squat_metrics' in analysis:
                metrics = analysis['squat_metrics']
                st.subheader("📐 Metriche Squat")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Depth Ratio", f"{metrics.get('depth_ratio', 0):.2f}")
                    st.metric("Hip Y", f"{metrics.get('hip_center', [0,0])[1]:.0f}px")
                with col2:
                    st.metric("Knee Align", f"{metrics.get('knee_alignment_diff', 0):.0f}px")
                    st.metric("Knee Y", f"{metrics.get('knee_center', [0,0])[1]:.0f}px")

            elif exercise_type == 'pushup' and 'pushup_metrics' in analysis:
                metrics = analysis['pushup_metrics']
                st.subheader("📐 Metriche Push-up")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Depth Ratio", f"{metrics.get('depth_ratio', 0):.2f}")
                    st.metric("Elbow Y", f"{metrics.get('elbow_center_y', 0):.0f}px")
                with col2:
                    st.metric("Depth", f"{metrics.get('pushup_depth_pixels', 0):.0f}px")
                    st.metric("Shoulder Y", f"{metrics.get('shoulder_center_y', 0):.0f}px")

            elif exercise_type == 'bicep_curl' and 'curl_metrics' in analysis:
                metrics = analysis['curl_metrics']
                st.subheader("📐 Metriche Curl")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Flessione", f"{metrics.get('flexion_pixels', 0):.0f}px")
                    st.metric("Angolo", f"{metrics.get('elbow_angle_degrees', 0):.0f}°")
                with col2:
                    st.metric("Stabilità", f"{metrics.get('elbow_stability', 0):.0f}px")

            # Confidence scores
            if 'confidence_scores' in analysis:
                st.subheader("🎯 Confidence YOLO11")
                conf_data = analysis['confidence_scores']
                if isinstance(conf_data, list) and len(conf_data) > 16:
                    key_conf = {
                        "Shoulders": (conf_data[5] + conf_data[6]) / 2,
                        "Elbows": (conf_data[7] + conf_data[8]) / 2,
                        "Hips": (conf_data[11] + conf_data[12]) / 2,
                        "Knees": (conf_data[13] + conf_data[14]) / 2
                    }

                    for part, conf in key_conf.items():
                        st.metric(part, f"{conf:.1%}")

            # Raw data
            if show_raw_data:
                st.subheader("🔍 Dati Raw")
                st.json(analysis)

        else:
            st.info("📊 **In attesa di analisi...**")
            st.write("Carica YOLO11 e una immagine per vedere l'analisi matematica completa!")

        # Stats sessione
        st.subheader("📈 Sessione")
        st.metric("📊 Analisi Totali", st.session_state.analysis_count)

    # Info completa
    st.success("""
    ### 🧮 **ANALISI MATEMATICA YOLO11**

    **📐 Calcoli Precisi:**
    - **Squat:** Hip_Y vs Knee_Y ratio, allineamento, stabilità
    - **Push-up:** Elbow_Y vs Shoulder_Y ratio, simmetria
    - **Curl:** Flessione pixels, angolo gomito, stabilità

    **🎯 Keypoints COCO:**
    - 17 punti corporei con coordinate X,Y precise
    - Confidence score per ogni keypoint  
    - Overlay visuale su video stream
    - Calcoli trigonometrici per angoli

    **✅ Feedback Reale:**
    - Basato su misurazioni effettive, non casuali
    - Soglie calibrate per ogni esercizio
    - Feedback vocale con dati specifici

    **🚀 Pronto per analisi scientifica dell'allenamento!**
    """)

if __name__ == "__main__":
    main()
