"""
Modulo per il conteggio automatico delle ripetizioni degli esercizi
"""

class RepetitionCounter:
    """
    Classe per conteggiare automaticamente le ripetizioni degli esercizi
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

        self.phase_history.append({
            'phase': current_phase,
            'correct': is_correct,
            'timestamp': len(self.phase_history)
        })

        if len(self.phase_history) > 10:
            self.phase_history = self.phase_history[-10:]

        rep_completed = self._check_repetition_completion(exercise_type, current_phase, is_correct)

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

    def _check_repetition_completion(self, exercise_type, current_phase, is_correct):
        if self.correct_form_required and not is_correct:
            return False

        if exercise_type == 'squat':
            return self._check_squat_completion(current_phase, is_correct)
        elif exercise_type == 'pushup':
            return self._check_pushup_completion(current_phase, is_correct)
        elif exercise_type == 'bicep_curl':
            return self._check_bicep_curl_completion(current_phase, is_correct)

        return False

    def _check_squat_completion(self, current_phase, is_correct):
        if len(self.phase_history) < 3:
            return False

        recent_phases = [p['phase'] for p in self.phase_history[-3:]]

        if (len(recent_phases) >= 3 and
            recent_phases[-3] == 'up' and 
            recent_phases[-2] == 'down' and 
            recent_phases[-1] == 'up'):

            if self.correct_form_required:
                recent_correct = [p['correct'] for p in self.phase_history[-3:]]
                return any(recent_correct)
            return True

        return False

    def _check_pushup_completion(self, current_phase, is_correct):
        if len(self.phase_history) < 3:
            return False

        recent_phases = [p['phase'] for p in self.phase_history[-3:]]

        if (len(recent_phases) >= 3 and
            recent_phases[-3] == 'up' and 
            recent_phases[-2] == 'down' and 
            recent_phases[-1] == 'up'):

            if self.correct_form_required:
                recent_correct = [p['correct'] for p in self.phase_history[-3:]]
                return any(recent_correct)
            return True

        return False

    def _check_bicep_curl_completion(self, current_phase, is_correct):
        if len(self.phase_history) < 3:
            return False

        recent_phases = [p['phase'] for p in self.phase_history[-3:]]

        if (len(recent_phases) >= 3 and
            recent_phases[-3] == 'down' and 
            recent_phases[-2] == 'up' and 
            recent_phases[-1] == 'down'):

            if self.correct_form_required:
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
