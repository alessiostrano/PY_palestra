"""
Modulo per il conteggio automatico delle ripetizioni
VERSIONE COMPLETA E FUNZIONANTE
"""

class RepetitionCounter:
    """
    Conta automaticamente le ripetizioni degli esercizi
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self.count = 0
        self.last_phase = None
        self.phase_history = []
        self.correct_form_required = True

    def update(self, exercise_type, evaluation_result):
        if not evaluation_result or 'phase' not in evaluation_result:
            return self._get_status()

        current_phase = evaluation_result['phase']
        is_correct = evaluation_result['correct']

        if current_phase in ['unknown', 'error']:
            return self._get_status()

        # Aggiorna cronologia
        self.phase_history.append({
            'phase': current_phase,
            'correct': is_correct
        })

        # Mantieni solo ultime 5 fasi
        if len(self.phase_history) > 5:
            self.phase_history = self.phase_history[-5:]

        # Controlla completamento ripetizione
        rep_completed = self._check_repetition_completion(exercise_type)

        if rep_completed:
            self.count += 1
            return {
                'count': self.count,
                'rep_completed': True,
                'current_phase': current_phase,
                'form_correct': is_correct
            }

        self.last_phase = current_phase
        return self._get_status()

    def _check_repetition_completion(self, exercise_type):
        if len(self.phase_history) < 3:
            return False

        recent_phases = [p['phase'] for p in self.phase_history[-3:]]

        # Pattern per ogni esercizio
        if exercise_type == 'squat':
            pattern = ['up', 'down', 'up']
        elif exercise_type == 'pushup':
            pattern = ['up', 'down', 'up']
        elif exercise_type == 'bicep_curl':
            pattern = ['down', 'up', 'down']
        else:
            return False

        # Controlla se pattern è completato
        if recent_phases == pattern:
            if self.correct_form_required:
                # Almeno una fase deve essere corretta
                recent_correct = [p['correct'] for p in self.phase_history[-3:]]
                return any(recent_correct)
            return True

        return False

    def _get_status(self):
        return {
            'count': self.count,
            'rep_completed': False,
            'current_phase': self.last_phase,
            'form_correct': False
        }

    def set_form_requirement(self, required=True):
        self.correct_form_required = required

    def get_statistics(self):
        if not self.phase_history:
            return {'total_reps': self.count, 'correct_form_percentage': 0, 'total_phases_tracked': 0}

        correct_phases = sum(1 for p in self.phase_history if p['correct'])
        correct_percentage = (correct_phases / len(self.phase_history)) * 100

        return {
            'total_reps': self.count,
            'correct_form_percentage': round(correct_percentage, 1),
            'total_phases_tracked': len(self.phase_history)
        }
