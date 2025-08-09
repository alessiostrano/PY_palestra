"""
Modulo per la valutazione della correttezza della postura
VERSIONE COMPLETA E FUNZIONANTE
"""
import numpy as np

class PostureEvaluator:
    """
    Valuta la correttezza della postura durante gli esercizi
    """

    def __init__(self):
        self.thresholds = {
            'squat': {
                'knee_min': 80,      
                'knee_max': 160,     
                'back_min': 160,     
            },
            'pushup': {
                'elbow_min': 70,     
                'elbow_max': 160,    
            },
            'bicep_curl': {
                'elbow_min': 30,     
                'elbow_max': 160,    
            }
        }

    def evaluate_squat(self, landmarks, pose_detector):
        if not landmarks:
            return {'correct': False, 'feedback': 'Posizione non rilevata', 'phase': 'unknown'}

        try:
            required = ['right_hip', 'right_knee', 'right_ankle', 'left_hip', 'left_knee', 'left_ankle']

            if not all(lm in landmarks for lm in required):
                return {'correct': False, 'feedback': 'Posizionati meglio davanti alla camera', 'phase': 'unknown'}

            # Calcola angoli ginocchia
            right_knee_angle = pose_detector.calculate_angle(
                (landmarks['right_hip']['x'], landmarks['right_hip']['y']),
                (landmarks['right_knee']['x'], landmarks['right_knee']['y']),
                (landmarks['right_ankle']['x'], landmarks['right_ankle']['y'])
            )

            left_knee_angle = pose_detector.calculate_angle(
                (landmarks['left_hip']['x'], landmarks['left_hip']['y']),
                (landmarks['left_knee']['x'], landmarks['left_knee']['y']),
                (landmarks['left_ankle']['x'], landmarks['left_ankle']['y'])
            )

            knee_angle = (right_knee_angle + left_knee_angle) / 2

            # Determina fase
            if knee_angle > 140:
                phase = 'up'
            elif knee_angle < 100:
                phase = 'down'
            else:
                phase = 'transition'

            # Valutazione
            feedback_messages = []
            is_correct = True

            if phase == 'down' and knee_angle > self.thresholds['squat']['knee_min'] + 20:
                feedback_messages.append("Scendi di più!")
                is_correct = False

            if abs(right_knee_angle - left_knee_angle) > 30:
                feedback_messages.append("Mantieni le ginocchia allineate!")
                is_correct = False

            feedback = " ".join(feedback_messages) if feedback_messages else "Ottima forma!"

            return {
                'correct': is_correct,
                'feedback': feedback,
                'phase': phase,
                'knee_angle': knee_angle
            }

        except Exception as e:
            return {'correct': False, 'feedback': 'Errore nella valutazione', 'phase': 'error'}

    def evaluate_pushup(self, landmarks, pose_detector):
        if not landmarks:
            return {'correct': False, 'feedback': 'Posizione non rilevata', 'phase': 'unknown'}

        try:
            required = ['right_shoulder', 'right_elbow', 'right_wrist', 'left_shoulder', 'left_elbow', 'left_wrist']

            if not all(lm in landmarks for lm in required):
                return {'correct': False, 'feedback': 'Posizionati meglio', 'phase': 'unknown'}

            # Calcola angoli gomiti
            right_elbow_angle = pose_detector.calculate_angle(
                (landmarks['right_shoulder']['x'], landmarks['right_shoulder']['y']),
                (landmarks['right_elbow']['x'], landmarks['right_elbow']['y']),
                (landmarks['right_wrist']['x'], landmarks['right_wrist']['y'])
            )

            left_elbow_angle = pose_detector.calculate_angle(
                (landmarks['left_shoulder']['x'], landmarks['left_shoulder']['y']),
                (landmarks['left_elbow']['x'], landmarks['left_elbow']['y']),
                (landmarks['left_wrist']['x'], landmarks['left_wrist']['y'])
            )

            elbow_angle = (right_elbow_angle + left_elbow_angle) / 2

            # Determina fase
            if elbow_angle > 140:
                phase = 'up'
            elif elbow_angle < 90:
                phase = 'down'
            else:
                phase = 'transition'

            # Valutazione
            feedback_messages = []
            is_correct = True

            if phase == 'down' and elbow_angle > 100:
                feedback_messages.append("Scendi di più!")
                is_correct = False

            if abs(right_elbow_angle - left_elbow_angle) > 40:
                feedback_messages.append("Mantieni i gomiti allineati!")
                is_correct = False

            feedback = " ".join(feedback_messages) if feedback_messages else "Ottima forma!"

            return {
                'correct': is_correct,
                'feedback': feedback,
                'phase': phase,
                'elbow_angle': elbow_angle
            }

        except:
            return {'correct': False, 'feedback': 'Errore nella valutazione', 'phase': 'error'}

    def evaluate_bicep_curl(self, landmarks, pose_detector):
        if not landmarks:
            return {'correct': False, 'feedback': 'Posizione non rilevata', 'phase': 'unknown'}

        try:
            required = ['right_shoulder', 'right_elbow', 'right_wrist', 'left_shoulder', 'left_elbow', 'left_wrist']

            if not all(lm in landmarks for lm in required):
                return {'correct': False, 'feedback': 'Posizionati meglio', 'phase': 'unknown'}

            # Calcola angoli gomiti
            right_elbow_angle = pose_detector.calculate_angle(
                (landmarks['right_shoulder']['x'], landmarks['right_shoulder']['y']),
                (landmarks['right_elbow']['x'], landmarks['right_elbow']['y']),
                (landmarks['right_wrist']['x'], landmarks['right_wrist']['y'])
            )

            left_elbow_angle = pose_detector.calculate_angle(
                (landmarks['left_shoulder']['x'], landmarks['left_shoulder']['y']),
                (landmarks['left_elbow']['x'], landmarks['left_elbow']['y']),
                (landmarks['left_wrist']['x'], landmarks['left_wrist']['y'])
            )

            elbow_angle = (right_elbow_angle + left_elbow_angle) / 2

            # Determina fase  
            if elbow_angle > 140:
                phase = 'down'
            elif elbow_angle < 60:
                phase = 'up'
            else:
                phase = 'transition'

            # Valutazione
            feedback_messages = []
            is_correct = True

            if phase == 'up' and elbow_angle > 80:
                feedback_messages.append("Fletti di più i gomiti!")
                is_correct = False

            # Controllo stabilità spalle
            if 'left_shoulder' in landmarks and 'right_shoulder' in landmarks:
                shoulder_width = abs(landmarks['left_shoulder']['x'] - landmarks['right_shoulder']['x'])
                elbow_width = abs(landmarks['left_elbow']['x'] - landmarks['right_elbow']['x'])

                if elbow_width > shoulder_width * 1.4:
                    feedback_messages.append("Mantieni i gomiti vicino al corpo!")
                    is_correct = False

            feedback = " ".join(feedback_messages) if feedback_messages else "Ottima forma!"

            return {
                'correct': is_correct,
                'feedback': feedback,
                'phase': phase,
                'elbow_angle': elbow_angle
            }

        except:
            return {'correct': False, 'feedback': 'Errore nella valutazione', 'phase': 'error'}
