"""
Modulo per il rilevamento delle pose usando MediaPipe
"""
import cv2
import mediapipe as mp
import numpy as np

class PoseDetector:
    """
    Classe per rilevare le pose umane utilizzando MediaPipe
    """

    def __init__(self, min_detection_confidence=0.5, min_tracking_confidence=0.5):
        """
        Inizializza il detector delle pose

        Args:
            min_detection_confidence (float): Soglia minima per il rilevamento
            min_tracking_confidence (float): Soglia minima per il tracking
        """
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_pose = mp.solutions.pose

        self.pose = self.mp_pose.Pose(
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )

    def detect_pose(self, image):
        """
        Rileva le pose nell'immagine fornita

        Args:
            image: Immagine BGR da OpenCV

        Returns:
            tuple: (image_rgb, results) dove results contiene i landmark delle pose
        """
        # Converti BGR a RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False

        # Processa l'immagine
        results = self.pose.process(image_rgb)

        # Riconverti a BGR per la visualizzazione
        image_rgb.flags.writeable = True
        image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)

        return image_bgr, results

    def draw_landmarks(self, image, results):
        """
        Disegna i landmark delle pose sull'immagine

        Args:
            image: Immagine su cui disegnare
            results: Risultati del rilevamento pose

        Returns:
            image: Immagine con i landmark disegnati
        """
        if results.pose_landmarks:
            self.mp_drawing.draw_landmarks(
                image, 
                results.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS
            )
        return image

    def get_landmark_coordinates(self, results, landmark_id):
        """
        Estrae le coordinate di un landmark specifico

        Args:
            results: Risultati del rilevamento pose
            landmark_id: ID del landmark da estrarre

        Returns:
            tuple: (x, y, z, visibility) o None se non trovato
        """
        if results.pose_landmarks:
            landmark = results.pose_landmarks.landmark[landmark_id]
            return (landmark.x, landmark.y, landmark.z, landmark.visibility)
        return None

    def calculate_angle(self, point1, point2, point3):
        """
        Calcola l'angolo tra tre punti

        Args:
            point1, point2, point3: Tuple (x, y) dei tre punti

        Returns:
            float: Angolo in gradi
        """
        # Converti in array numpy
        a = np.array(point1)  # Primo punto
        b = np.array(point2)  # Punto centrale (vertice)
        c = np.array(point3)  # Terzo punto

        # Calcola i vettori
        ba = a - b
        bc = c - b

        # Calcola l'angolo usando il prodotto scalare
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))

        return np.degrees(angle)

    def get_body_landmarks(self, results):
        """
        Estrae i principali landmark del corpo per l'analisi degli esercizi

        Args:
            results: Risultati del rilevamento pose

        Returns:
            dict: Dizionario con le coordinate dei principali landmark
        """
        if not results.pose_landmarks:
            return None

        landmarks = {}

        # Landmark principali per gli esercizi
        landmark_mapping = {
            'nose': self.mp_pose.PoseLandmark.NOSE,
            'left_shoulder': self.mp_pose.PoseLandmark.LEFT_SHOULDER,
            'right_shoulder': self.mp_pose.PoseLandmark.RIGHT_SHOULDER,
            'left_elbow': self.mp_pose.PoseLandmark.LEFT_ELBOW,
            'right_elbow': self.mp_pose.PoseLandmark.RIGHT_ELBOW,
            'left_wrist': self.mp_pose.PoseLandmark.LEFT_WRIST,
            'right_wrist': self.mp_pose.PoseLandmark.RIGHT_WRIST,
            'left_hip': self.mp_pose.PoseLandmark.LEFT_HIP,
            'right_hip': self.mp_pose.PoseLandmark.RIGHT_HIP,
            'left_knee': self.mp_pose.PoseLandmark.LEFT_KNEE,
            'right_knee': self.mp_pose.PoseLandmark.RIGHT_KNEE,
            'left_ankle': self.mp_pose.PoseLandmark.LEFT_ANKLE,
            'right_ankle': self.mp_pose.PoseLandmark.RIGHT_ANKLE
        }

        for name, landmark_id in landmark_mapping.items():
            coords = self.get_landmark_coordinates(results, landmark_id)
            if coords:
                landmarks[name] = {
                    'x': coords[0],
                    'y': coords[1],
                    'z': coords[2],
                    'visibility': coords[3]
                }

        return landmarks
