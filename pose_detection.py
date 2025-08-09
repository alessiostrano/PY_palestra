"""
Modulo per il rilevamento delle pose usando YOLO11 (Ultralytics)
"""
import cv2
import numpy as np
from ultralytics import YOLO
import torch

class PoseDetector:
    """
    Classe per rilevare le pose umane utilizzando YOLO11
    """

    def __init__(self, model_name='yolo11n-pose.pt', confidence=0.5):
        """
        Inizializza il detector delle pose con YOLO11

        Args:
            model_name (str): Nome del modello YOLO11 pose
            confidence (float): Soglia minima per il rilevamento
        """
        try:
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

            # Mapping per compatibilità con il codice esistente
            self.landmark_mapping = {
                'nose': 0,
                'left_shoulder': 5, 'right_shoulder': 6,
                'left_elbow': 7, 'right_elbow': 8,
                'left_wrist': 9, 'right_wrist': 10,
                'left_hip': 11, 'right_hip': 12,
                'left_knee': 13, 'right_knee': 14,
                'left_ankle': 15, 'right_ankle': 16
            }

            print("✅ YOLO11 Pose Detection inizializzato correttamente")

        except Exception as e:
            print(f"❌ Errore nell'inizializzazione YOLO11: {e}")
            self.model = None

    def detect_pose(self, image):
        """
        Rileva le pose nell'immagine fornita usando YOLO11

        Args:
            image: Immagine BGR da OpenCV

        Returns:
            tuple: (processed_image, results) dove results contiene i keypoints
        """
        if not self.model:
            return image, None

        try:
            # Esegue l'inferenza con YOLO11
            results = self.model(image, conf=self.confidence, verbose=False)

            # Crea una copia dell'immagine per il disegno
            processed_image = image.copy()

            # Estrae i risultati
            if len(results) > 0 and results[0].keypoints is not None:
                return processed_image, results[0]
            else:
                return processed_image, None

        except Exception as e:
            print(f"Errore nel rilevamento pose: {e}")
            return image, None

    def draw_landmarks(self, image, results):
        """
        Disegna i keypoints delle pose sull'immagine

        Args:
            image: Immagine su cui disegnare
            results: Risultati del rilevamento YOLO11

        Returns:
            image: Immagine con i keypoints disegnati
        """
        if not results or results.keypoints is None:
            return image

        try:
            # Disegna automaticamente usando YOLO11
            annotated_image = results.plot()
            return annotated_image

        except Exception as e:
            print(f"Errore nel disegno landmarks: {e}")
            return image

    def get_landmark_coordinates(self, results, landmark_name):
        """
        Estrae le coordinate di un landmark specifico

        Args:
            results: Risultati del rilevamento YOLO11
            landmark_name: Nome del landmark da estrarre

        Returns:
            tuple: (x, y, confidence) o None se non trovato
        """
        if not results or results.keypoints is None:
            return None

        try:
            keypoints = results.keypoints.xy[0]  # Prende la prima persona
            confidences = results.keypoints.conf[0] if results.keypoints.conf is not None else None

            if landmark_name in self.landmark_mapping:
                idx = self.landmark_mapping[landmark_name]
                if idx < len(keypoints):
                    x, y = keypoints[idx]
                    confidence = confidences[idx] if confidences is not None else 1.0

                    # Normalizza le coordinate (YOLO11 le restituisce in pixel)
                    h, w = results.orig_shape
                    x_norm = float(x / w)
                    y_norm = float(y / h)

                    return (x_norm, y_norm, 0.0, float(confidence))

            return None

        except Exception as e:
            print(f"Errore nell'estrazione coordinate: {e}")
            return None

    def calculate_angle(self, point1, point2, point3):
        """
        Calcola l'angolo tra tre punti

        Args:
            point1, point2, point3: Tuple (x, y) dei tre punti

        Returns:
            float: Angolo in gradi
        """
        try:
            # Converti in array numpy
            a = np.array(point1)  # Primo punto
            b = np.array(point2)  # Punto centrale (vertice)
            c = np.array(point3)  # Terzo punto

            # Calcola i vettori
            ba = a - b
            bc = c - b

            # Calcola l'angolo usando il prodotto scalare
            cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
            cosine_angle = np.clip(cosine_angle, -1.0, 1.0)
            angle = np.arccos(cosine_angle)

            return np.degrees(angle)

        except Exception as e:
            print(f"Errore nel calcolo angolo: {e}")
            return 180.0  # Angolo di default

    def get_body_landmarks(self, results):
        """
        Estrae i principali landmark del corpo per l'analisi degli esercizi

        Args:
            results: Risultati del rilevamento YOLO11

        Returns:
            dict: Dizionario con le coordinate dei principali landmark
        """
        if not results or results.keypoints is None or len(results.keypoints.xy) == 0:
            return None

        try:
            keypoints = results.keypoints.xy[0]  # Prima persona rilevata
            confidences = results.keypoints.conf[0] if results.keypoints.conf is not None else None

            landmarks = {}
            h, w = results.orig_shape

            # Estrae i landmark principali per gli esercizi
            for name, idx in self.landmark_mapping.items():
                if idx < len(keypoints):
                    x, y = keypoints[idx]
                    confidence = confidences[idx] if confidences is not None else 1.0

                    # Solo se il keypoint è abbastanza confidenziale
                    if confidence > 0.3:
                        landmarks[name] = {
                            'x': float(x / w),  # Normalizzato
                            'y': float(y / h),  # Normalizzato
                            'z': 0.0,
                            'visibility': float(confidence)
                        }

            return landmarks if landmarks else None

        except Exception as e:
            print(f"Errore nell'estrazione body landmarks: {e}")
            return None

    def is_model_loaded(self):
        """
        Controlla se il modello è caricato correttamente

        Returns:
            bool: True se il modello è caricato
        """
        return self.model is not None

    def get_model_info(self):
        """
        Ritorna informazioni sul modello caricato

        Returns:
            dict: Informazioni sul modello
        """
        if not self.model:
            return {'status': 'Model not loaded'}

        return {
            'model_type': 'YOLO11 Pose',
            'confidence_threshold': self.confidence,
            'keypoints_count': len(self.keypoint_names),
            'status': 'Ready'
        }
