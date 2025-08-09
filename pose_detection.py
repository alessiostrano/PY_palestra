"""
Modulo per il rilevamento delle pose usando YOLO11 (Ultralytics)
VERSIONE COMPLETA E FUNZIONANTE
"""
import cv2
import numpy as np
import os
import tempfile

# Fix per la directory di configurazione YOLO
os.environ['YOLO_CONFIG_DIR'] = '/tmp'
os.environ['WANDB_DISABLED'] = 'true'
os.environ['ULTRALYTICS_ANALYTICS'] = 'false'

from ultralytics import YOLO

class PoseDetector:
    """
    Classe per rilevare le pose umane utilizzando YOLO11
    """

    def __init__(self, model_name='yolo11n-pose.pt', confidence=0.5):
        """
        Inizializza il detector delle pose con YOLO11
        """
        try:
            print(f"🤖 Caricamento modello YOLO11: {model_name}")
            print("⏳ Download in corso...")

            # Carica il modello YOLO11 per pose estimation
            self.model = YOLO(model_name)
            self.confidence = confidence

            # Definisce i keypoints COCO (17 punti)
            self.keypoint_names = [
                'nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear',
                'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
                'left_wrist', 'right_wrist', 'left_hip', 'right_hip',
                'left_knee', 'right_knee', 'left_ankle', 'right_ankle'
            ]

            # Mapping per compatibilità
            self.landmark_mapping = {
                'nose': 0,
                'left_shoulder': 5, 'right_shoulder': 6,
                'left_elbow': 7, 'right_elbow': 8,
                'left_wrist': 9, 'right_wrist': 10,
                'left_hip': 11, 'right_hip': 12,
                'left_knee': 13, 'right_knee': 14,
                'left_ankle': 15, 'right_ankle': 16
            }

            # Test del modello
            test_image = np.zeros((480, 640, 3), dtype=np.uint8)
            _ = self.model(test_image, verbose=False, save=False)

            print("✅ YOLO11 inizializzato e testato correttamente")

        except Exception as e:
            print(f"❌ Errore nell'inizializzazione YOLO11: {e}")
            self.model = None

    def detect_pose(self, image):
        """
        Rileva le pose nell'immagine
        """
        if not self.model:
            return image, None

        try:
            # Esegue l'inferenza
            results = self.model(image, conf=self.confidence, verbose=False, save=False)

            processed_image = image.copy()

            if len(results) > 0 and results[0].keypoints is not None:
                return processed_image, results[0]
            else:
                return processed_image, None

        except Exception as e:
            print(f"Errore rilevamento: {e}")
            return image, None

    def draw_landmarks(self, image, results):
        """
        Disegna i keypoints sulla immagine
        """
        if not results or results.keypoints is None:
            return image

        try:
            annotated_image = results.plot(verbose=False)
            return annotated_image
        except Exception as e:
            print(f"Errore disegno: {e}")
            return image

    def calculate_angle(self, point1, point2, point3):
        """
        Calcola l'angolo tra tre punti
        """
        try:
            a = np.array(point1)
            b = np.array(point2)  # Vertice
            c = np.array(point3)

            ba = a - b
            bc = c - b

            cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
            cosine_angle = np.clip(cosine_angle, -1.0, 1.0)
            angle = np.arccos(cosine_angle)

            return np.degrees(angle)
        except:
            return 180.0

    def get_body_landmarks(self, results):
        """
        Estrae i landmark del corpo
        """
        if not results or results.keypoints is None or len(results.keypoints.xy) == 0:
            return None

        try:
            keypoints = results.keypoints.xy[0]
            confidences = results.keypoints.conf[0] if results.keypoints.conf is not None else None

            landmarks = {}
            h, w = results.orig_shape

            for name, idx in self.landmark_mapping.items():
                if idx < len(keypoints):
                    x, y = keypoints[idx]
                    confidence = confidences[idx] if confidences is not None else 1.0

                    if confidence > 0.3:
                        landmarks[name] = {
                            'x': float(x / w),
                            'y': float(y / h),
                            'z': 0.0,
                            'visibility': float(confidence)
                        }

            return landmarks if landmarks else None
        except:
            return None

    def is_model_loaded(self):
        return self.model is not None

    def get_model_info(self):
        if not self.model:
            return {'status': 'Model not loaded'}

        return {
            'model_type': 'YOLO11 Pose',
            'confidence_threshold': self.confidence,
            'keypoints_count': len(self.keypoint_names),
            'status': 'Ready'
        }
