"""
Modulo per la valutazione della correttezza della postura durante gli esercizi
"""
import numpy as np

class PostureEvaluator:
    """
    Classe per valutare la correttezza della postura durante diversi esercizi
    """

    def __init__(self):
        """
        Inizializza l'evaluator con le soglie per ogni esercizio
        """
        # Soglie per la valutazione degli angoli (in gradi)
        self.thresholds = {
            'squat': {
                'knee_min': 70,      # Angolo minimo ginocchio per squat completo
                'knee_max': 160,     # Angolo massimo ginocchio per posizione eretta
                'back_min': 160,     # Angolo minimo schiena per mantenere dritta
                'hip_min': 70        # Angolo minimo anca
            },
            'pushup': {
                'elbow_min': 70,     # Angolo minimo gomito per push-up completo
                'elbow_max': 160,    # Angolo massimo gomito per posizione alta
                'back_min': 160,     # Schiena dritta
                'shoulder_alignment': 20  # Tolleranza allineamento spalle
            },
            'bicep_curl': {
                'elbow_min': 30,     # Angolo minimo gomito per curl completo
                'elbow_max': 160,    # Angolo massimo gomito per posizione iniziale
                'shoulder_stability': 15,  # Tolleranza movimento spalle
                'wrist_alignment': 20      # Tolleranza allineamento polsi
            }
        }

    def evaluate_squat(self, landmarks, pose_detector):
        """
        Valuta la correttezza di uno squat

        Args:
            landmarks: Dizionario con i landmark del corpo
            pose_detector: Istanza del PoseDetector per calcolare angoli

        Returns:
            dict: Risultato della valutazione con feedback
        """
        if not landmarks:
            return {'correct': False, 'feedback': 'Posizione non rilevata'}

        try:
            # Calcola angoli chiave
            # Angolo ginocchio destro
            right_knee_angle = pose_detector.calculate_angle(
                (landmarks['right_hip']['x'], landmarks['right_hip']['y']),
                (landmarks['right_knee']['x'], landmarks['right_knee']['y']),
                (landmarks['right_ankle']['x'], landmarks['right_ankle']['y'])
            )

            # Angolo ginocchio sinistro
            left_knee_angle = pose_detector.calculate_angle(
                (landmarks['left_hip']['x'], landmarks['left_hip']['y']),
                (landmarks['left_knee']['x'], landmarks['left_knee']['y']),
                (landmarks['left_ankle']['x'], landmarks['left_ankle']['y'])
            )

            # Angolo schiena (approssimativo)
            back_angle = pose_detector.calculate_angle(
                (landmarks['left_shoulder']['x'], landmarks['left_shoulder']['y']),
                (landmarks['left_hip']['x'], landmarks['left_hip']['y']),
                (landmarks['left_knee']['x'], landmarks['left_knee']['y'])
            )

            # Media degli angoli delle ginocchia
            knee_angle = (right_knee_angle + left_knee_angle) / 2

            # Valutazione
            feedback_messages = []
            is_correct = True

            # Controllo profondità squat
            if knee_angle > self.thresholds['squat']['knee_max']:
                phase = 'up'
            elif knee_angle < self.thresholds['squat']['knee_min']:
                phase = 'down'
                if knee_angle > self.thresholds['squat']['knee_min'] + 20:
                    feedback_messages.append("Scendi di più!")
                    is_correct = False
            else:
                phase = 'transition'

            # Controllo schiena dritta
            if back_angle < self.thresholds['squat']['back_min']:
                feedback_messages.append("Mantieni la schiena dritta!")
                is_correct = False

            # Controllo simmetria ginocchia
            if abs(right_knee_angle - left_knee_angle) > 15:
                feedback_messages.append("Mantieni le ginocchia allineate!")
                is_correct = False

            feedback = " ".join(feedback_messages) if feedback_messages else "Ottima forma!"

            return {
                'correct': is_correct,
                'feedback': feedback,
                'phase': phase,
                'knee_angle': knee_angle,
                'back_angle': back_angle
            }

        except Exception as e:
            return {'correct': False, 'feedback': f'Errore nella valutazione: {str(e)}'}

    def evaluate_pushup(self, landmarks, pose_detector):
        """
        Valuta la correttezza di un push-up

        Args:
            landmarks: Dizionario con i landmark del corpo
            pose_detector: Istanza del PoseDetector

        Returns:
            dict: Risultato della valutazione
        """
        if not landmarks:
            return {'correct': False, 'feedback': 'Posizione non rilevata'}

        try:
            # Angolo gomito destro
            right_elbow_angle = pose_detector.calculate_angle(
                (landmarks['right_shoulder']['x'], landmarks['right_shoulder']['y']),
                (landmarks['right_elbow']['x'], landmarks['right_elbow']['y']),
                (landmarks['right_wrist']['x'], landmarks['right_wrist']['y'])
            )

            # Angolo gomito sinistro
            left_elbow_angle = pose_detector.calculate_angle(
                (landmarks['left_shoulder']['x'], landmarks['left_shoulder']['y']),
                (landmarks['left_elbow']['x'], landmarks['left_elbow']['y']),
                (landmarks['left_wrist']['x'], landmarks['left_wrist']['y'])
            )

            # Angolo corpo (schiena dritta)
            body_angle = pose_detector.calculate_angle(
                (landmarks['left_shoulder']['x'], landmarks['left_shoulder']['y']),
                (landmarks['left_hip']['x'], landmarks['left_hip']['y']),
                (landmarks['left_knee']['x'], landmarks['left_knee']['y'])
            )

            elbow_angle = (right_elbow_angle + left_elbow_angle) / 2

            feedback_messages = []
            is_correct = True

            # Determinazione fase
            if elbow_angle > self.thresholds['pushup']['elbow_max'] - 20:
                phase = 'up'
            elif elbow_angle < self.thresholds['pushup']['elbow_min'] + 20:
                phase = 'down'
            else:
                phase = 'transition'

            # Controllo profondità
            if phase == 'down' and elbow_angle > self.thresholds['pushup']['elbow_min'] + 30:
                feedback_messages.append("Scendi di più!")
                is_correct = False

            # Controllo schiena dritta
            if body_angle < self.thresholds['pushup']['back_min']:
                feedback_messages.append("Mantieni il corpo dritto!")
                is_correct = False

            # Controllo simmetria gomiti
            if abs(right_elbow_angle - left_elbow_angle) > 20:
                feedback_messages.append("Mantieni i gomiti allineati!")
                is_correct = False

            feedback = " ".join(feedback_messages) if feedback_messages else "Ottima forma!"

            return {
                'correct': is_correct,
                'feedback': feedback,
                'phase': phase,
                'elbow_angle': elbow_angle,
                'body_angle': body_angle
            }

        except Exception as e:
            return {'correct': False, 'feedback': f'Errore nella valutazione: {str(e)}'}

    def evaluate_bicep_curl(self, landmarks, pose_detector):
        """
        Valuta la correttezza di un curl bicipiti

        Args:
            landmarks: Dizionario con i landmark del corpo
            pose_detector: Istanza del PoseDetector

        Returns:
            dict: Risultato della valutazione
        """
        if not landmarks:
            return {'correct': False, 'feedback': 'Posizione non rilevata'}

        try:
            # Angolo gomito destro
            right_elbow_angle = pose_detector.calculate_angle(
                (landmarks['right_shoulder']['x'], landmarks['right_shoulder']['y']),
                (landmarks['right_elbow']['x'], landmarks['right_elbow']['y']),
                (landmarks['right_wrist']['x'], landmarks['right_wrist']['y'])
            )

            # Angolo gomito sinistro
            left_elbow_angle = pose_detector.calculate_angle(
                (landmarks['left_shoulder']['x'], landmarks['left_shoulder']['y']),
                (landmarks['left_elbow']['x'], landmarks['left_elbow']['y']),
                (landmarks['left_wrist']['x'], landmarks['left_wrist']['y'])
            )

            elbow_angle = (right_elbow_angle + left_elbow_angle) / 2

            feedback_messages = []
            is_correct = True

            # Determinazione fase
            if elbow_angle > self.thresholds['bicep_curl']['elbow_max'] - 20:
                phase = 'down'
            elif elbow_angle < self.thresholds['bicep_curl']['elbow_min'] + 20:
                phase = 'up'
            else:
                phase = 'transition'

            # Controllo range di movimento
            if phase == 'up' and elbow_angle > self.thresholds['bicep_curl']['elbow_min'] + 30:
                feedback_messages.append("Fletti di più i gomiti!")
                is_correct = False

            # Controllo stabilità spalle (i gomiti dovrebbero rimanere vicini al corpo)
            shoulder_width = abs(landmarks['left_shoulder']['x'] - landmarks['right_shoulder']['x'])
            elbow_width = abs(landmarks['left_elbow']['x'] - landmarks['right_elbow']['x'])

            if elbow_width > shoulder_width * 1.2:
                feedback_messages.append("Mantieni i gomiti vicino al corpo!")
                is_correct = False

            # Controllo simmetria
            if abs(right_elbow_angle - left_elbow_angle) > 25:
                feedback_messages.append("Muovi entrambe le braccia insieme!")
                is_correct = False

            feedback = " ".join(feedback_messages) if feedback_messages else "Ottima forma!"

            return {
                'correct': is_correct,
                'feedback': feedback,
                'phase': phase,
                'elbow_angle': elbow_angle
            }

        except Exception as e:
            return {'correct': False, 'feedback': f'Errore nella valutazione: {str(e)}'}

    def get_posture_status_color(self, is_correct):
        """
        Ritorna il colore per l'indicatore di postura

        Args:
            is_correct: Bool che indica se la postura è corretta

        Returns:
            str: Codice colore hex
        """
        return "#00FF00" if is_correct else "#FF0000"  # Verde o Rosso
