"""
Fitness Tracker AI - App Desktop con Webcam Real-Time
Per uso locale con feedback vocale continuo
"""
import cv2
import numpy as np
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
import os

# Environment setup
os.environ.setdefault('YOLO_CONFIG_DIR', '/tmp')
os.environ.setdefault('WANDB_DISABLED', 'true')

class FitnessTrackerDesktop:
    def __init__(self):
        self.model = None
        self.tts_engine = None
        self.webcam = None
        self.running = False
        self.exercise_type = "squat"
        self.last_feedback_time = 0
        self.feedback_interval = 2.0

        # Setup UI
        self.setup_ui()
        self.init_models()

    def setup_ui(self):
        """Crea interfaccia desktop"""
        self.root = tk.Tk()
        self.root.title("💪 Fitness Tracker AI - Desktop")
        self.root.geometry("800x600")

        # Frame controlli
        control_frame = ttk.Frame(self.root)
        control_frame.pack(pady=10)

        # Selezione esercizio
        ttk.Label(control_frame, text="Esercizio:").pack(side=tk.LEFT)
        self.exercise_var = tk.StringVar(value="squat")
        exercise_combo = ttk.Combobox(control_frame, textvariable=self.exercise_var,
                                    values=["squat", "pushup", "bicep_curl"], state="readonly")
        exercise_combo.pack(side=tk.LEFT, padx=5)

        # Pulsanti
        self.start_btn = ttk.Button(control_frame, text="▶️ Start", command=self.start_tracking)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(control_frame, text="⏹️ Stop", command=self.stop_tracking, state="disabled")
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # Feedback area
        self.feedback_text = tk.Text(self.root, height=8, width=80)
        self.feedback_text.pack(pady=10)

        # Status
        self.status_var = tk.StringVar(value="Inizializzazione...")
        ttk.Label(self.root, textvariable=self.status_var).pack()

    def init_models(self):
        """Inizializza YOLO11 e TTS"""
        try:
            from ultralytics import YOLO
            self.model = YOLO('yolo11n-pose.pt')
            self.log_feedback("✅ YOLO11 caricato")
        except Exception as e:
            self.log_feedback(f"❌ YOLO11 errore: {e}")

        try:
            import pyttsx3
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 180)
            self.tts_engine.setProperty('volume', 0.9)
            self.log_feedback("✅ TTS inizializzato")
            self.speak("Sistema pronto!")
        except Exception as e:
            self.log_feedback(f"❌ TTS errore: {e}")

        self.status_var.set("Sistema pronto!")

    def log_feedback(self, message):
        """Aggiungi messaggio al log"""
        self.feedback_text.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {message}\n")
        self.feedback_text.see(tk.END)
        self.root.update()

    def speak(self, message):
        """Text-to-speech in thread separato"""
        if self.tts_engine and message:
            def speak_thread():
                try:
                    self.tts_engine.say(message)
                    self.tts_engine.runAndWait()
                except:
                    pass
            threading.Thread(target=speak_thread, daemon=True).start()

    def start_tracking(self):
        """Avvia tracking real-time"""
        if not self.model or not self.tts_engine:
            messagebox.showerror("Errore", "Modelli non caricati!")
            return

        # Inizializza webcam
        self.webcam = cv2.VideoCapture(0)
        if not self.webcam.isOpened():
            messagebox.showerror("Errore", "Webcam non disponibile!")
            return

        self.running = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")

        self.exercise_type = self.exercise_var.get()
        self.speak(f"Iniziamo con {self.exercise_type}! Preparati!")
        self.log_feedback(f"🚀 Tracking {self.exercise_type} iniziato")

        # Avvia loop in thread
        threading.Thread(target=self.tracking_loop, daemon=True).start()

    def stop_tracking(self):
        """Ferma tracking"""
        self.running = False
        if self.webcam:
            self.webcam.release()
        cv2.destroyAllWindows()

        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

        self.speak("Sessione terminata!")
        self.log_feedback("⏹️ Tracking fermato")

    def tracking_loop(self):
        """Loop principale di tracking con webcam"""
        while self.running:
            ret, frame = self.webcam.read()
            if not ret:
                break

            current_time = time.time()

            # Analizza ogni N secondi per feedback vocale
            if current_time - self.last_feedback_time > self.feedback_interval:
                try:
                    # YOLO11 detection
                    results = self.model(frame, verbose=False, save=False)

                    if len(results) > 0 and results[0].keypoints is not None:
                        # Analisi pose
                        keypoints = results[0].keypoints.xy[0]
                        confidence = results[0].keypoints.conf[0] if results[0].keypoints.conf is not None else None

                        feedback_text, voice_feedback = self.analyze_exercise(keypoints, confidence)

                        if voice_feedback:
                            self.speak(voice_feedback)
                            self.log_feedback(f"🗣️ {voice_feedback}")

                        # Disegna keypoints su frame
                        frame_with_pose = results[0].plot()
                        cv2.imshow(f'Fitness Tracker - {self.exercise_type.upper()}', frame_with_pose)

                    else:
                        self.speak("Non ti vedo! Posizionati meglio!")
                        cv2.imshow(f'Fitness Tracker - {self.exercise_type.upper()}', frame)

                    self.last_feedback_time = current_time

                except Exception as e:
                    self.log_feedback(f"❌ Errore analisi: {e}")
            else:
                # Mostra frame normale
                cv2.imshow(f'Fitness Tracker - {self.exercise_type.upper()}', frame)

            # ESC per uscire
            if cv2.waitKey(1) & 0xFF == 27:  # ESC
                break

            time.sleep(0.03)  # ~30 FPS

        self.stop_tracking()

    def analyze_exercise(self, keypoints, confidence):
        """Analizza esercizio specifico"""
        if keypoints is None or len(keypoints) == 0:
            return "Nessuna persona", "Non ti vedo"

        if confidence is None or len(confidence) < 17:
            return "Confidence bassa", "Avvicinati alla camera"

        # Analisi basata su esercizio
        if self.exercise_type == "squat":
            return self.analyze_squat(keypoints, confidence)
        elif self.exercise_type == "pushup":
            return self.analyze_pushup(keypoints, confidence)
        elif self.exercise_type == "bicep_curl":
            return self.analyze_bicep_curl(keypoints, confidence)

        return "Esercizio sconosciuto", ""

    def analyze_squat(self, keypoints, confidence):
        """Analisi squat dettagliata"""
        try:
            # Hip e knee confidence
            hip_conf = (confidence[11] + confidence[12]) / 2
            knee_conf = (confidence[13] + confidence[14]) / 2

            if hip_conf < 0.5 or knee_conf < 0.5:
                return "Posizionati di lato", "Mettiti di lato alla camera"

            # Calcola profondità squat
            hip_y = (keypoints[11][1] + keypoints[12][1]) / 2
            knee_y = (keypoints[13][1] + keypoints[14][1]) / 2

            if hip_y > knee_y * 1.05:  # Hip significativamente sotto ginocchia
                return "SQUAT PERFETTO", "Perfetto! Ottima discesa!"
            elif hip_y > knee_y:  # Hip sotto ginocchia
                return "Squat buono", "Bene! Continua così!"
            elif hip_y > knee_y * 0.9:  # Hip quasi al livello
                return "Scendi di più", "Scendi ancora un po'"
            else:
                return "TROPPO ALTO", "Scendi di più! Hip sopra ginocchia!"

        except:
            return "Errore analisi squat", "Errore nell'analisi"

    def analyze_pushup(self, keypoints, confidence):
        """Analisi push-up"""
        try:
            shoulder_conf = (confidence[5] + confidence[6]) / 2
            elbow_conf = (confidence[7] + confidence[8]) / 2

            if shoulder_conf < 0.5 or elbow_conf < 0.5:
                return "Posizionati di lato", "Mettiti di lato alla camera"

            shoulder_y = (keypoints[5][1] + keypoints[6][1]) / 2
            elbow_y = (keypoints[7][1] + keypoints[8][1]) / 2

            if elbow_y > shoulder_y * 1.1:  # Gomiti molto sotto spalle
                return "PUSH-UP PERFETTO", "Perfetto! Ottima discesa!"
            elif elbow_y > shoulder_y:  # Gomiti sotto spalle
                return "Push-up buono", "Bene! Continua così!"
            else:
                return "SCENDI DI PIÙ", "Scendi di più! Push-up troppo alto!"

        except:
            return "Errore analisi push-up", "Errore nell'analisi"

    def analyze_bicep_curl(self, keypoints, confidence):
        """Analisi bicep curl"""
        try:
            elbow_conf = confidence[7]  # Left elbow
            wrist_conf = confidence[9]  # Left wrist

            if elbow_conf < 0.5 or wrist_conf < 0.5:
                return "Posizionati frontale", "Mettiti frontale alla camera"

            elbow_y = keypoints[7][1]
            wrist_y = keypoints[9][1]
            shoulder_y = keypoints[5][1]

            if wrist_y < elbow_y < shoulder_y:  # Curl completo
                return "CURL PERFETTO", "Perfetto! Ottima flessione!"
            elif wrist_y < elbow_y:  # Curl parziale
                return "Fletti di più", "Fletti ancora i gomiti"
            else:
                return "MOVIMENTO TROPPO PICCOLO", "Fletti i gomiti! Movimento troppo piccolo!"

        except:
            return "Errore analisi curl", "Errore nell'analisi"

    def run(self):
        """Avvia applicazione"""
        self.root.mainloop()

if __name__ == "__main__":
    app = FitnessTrackerDesktop()
    app.run()
