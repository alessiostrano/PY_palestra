"""
Modulo per il conteggio automatico delle ripetizioni degli esercizi
Versione aggiornata per YOLO11
"""

class RepetitionCounter:
    """
    Classe per conteggiare automaticamente le ripetizioni degli esercizi
    basandosi sulla fase dell'esercizio e la correttezza della postura
    """

    def __init__(self):
        """
        Inizializza il contatore delle ripetizioni
        """
        self.reset()

    def reset(self):
        """
        Resetta il contatore delle ripetizioni
        """
        self.count = 0
        self.last_phase = None
        self.phase_history = []
        self.correct_form_required = True

    def update(self, exercise_type, evaluation_result):
        """
        Aggiorna il conteggio delle ripetizioni basandosi sulla valutazione dell'esercizio

        Args:
            exercise_type: Tipo di esercizio ('squat', 'pushup', 'bicep_curl')
            evaluation_result: Risultato della valutazione della postura

        Returns:
            dict: Informazioni aggiornate sul conteggio
        """
        if not evaluation_result or 'phase' not in evaluation_result:
            return self._get_status()

        current_phase = evaluation_result['phase']
        is_correct = evaluation_result['correct']

        # Ignora fasi di errore
        if current_phase in ['unknown', 'error']:
            return self._get_status()

        # Aggiorna la cronologia delle fasi
        self.phase_history.append({
            'phase': current_phase,
            'correct': is_correct,
            'timestamp': len(self.phase_history)
        })

        # Mantieni solo le ultime 10 fasi per efficienza
        if len(self.phase_history) > 10:
            self.phase_history = self.phase_history[-10:]

        # Logica di conteggio basata sul tipo di esercizio
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
        """
        Controlla se una ripetizione è stata completata

        Args:
            exercise_type: Tipo di esercizio
            current_phase: Fase attuale dell'esercizio
            is_correct: Se la forma è corretta

        Returns:
            bool: True se la ripetizione è completata
        """
        # Richiedi forma corretta se abilitato
        if self.correct_form_required and not is_correct:
            return False

        # Logica specifica per ogni esercizio
        if exercise_type == 'squat':
            return self._check_squat_completion(current_phase, is_correct)
        elif exercise_type == 'pushup':
            return self._check_pushup_completion(current_phase, is_correct)
        elif exercise_type == 'bicep_curl':
            return self._check_bicep_curl_completion(current_phase, is_correct)

        return False

    def _check_squat_completion(self, current_phase, is_correct):
        """
        Controlla il completamento di uno squat
        Una ripetizione completa: up -> down -> up
        """
        if len(self.phase_history) < 3:
            return False

        # Cerca il pattern up -> down -> up nelle ultime fasi
        recent_phases = [p['phase'] for p in self.phase_history[-3:]]

        # Pattern completo rilevato
        if (len(recent_phases) >= 3 and
            recent_phases[-3] == 'up' and 
            recent_phases[-2] == 'down' and 
            recent_phases[-1] == 'up'):

            # Verifica che almeno una delle fasi sia stata corretta
            if self.correct_form_required:
                recent_correct = [p['correct'] for p in self.phase_history[-3:]]
                return any(recent_correct)
            return True

        return False

    def _check_pushup_completion(self, current_phase, is_correct):
        """
        Controlla il completamento di un push-up
        Una ripetizione completa: up -> down -> up
        """
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
        """
        Controlla il completamento di un curl bicipiti
        Una ripetizione completa: down -> up -> down
        """
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
        """
        Ritorna lo status attuale del contatore

        Returns:
            dict: Status del contatore
        """
        return {
            'count': self.count,
            'rep_completed': False,
            'current_phase': self.last_phase,
            'form_correct': False
        }

    def set_form_requirement(self, required=True):
        """
        Imposta se è richiesta la forma corretta per conteggiare le ripetizioni

        Args:
            required: Bool se la forma corretta è richiesta
        """
        self.correct_form_required = required

    def get_statistics(self):
        """
        Ritorna statistiche sul conteggio

        Returns:
            dict: Statistiche del conteggio
        """
        if not self.phase_history:
            return {'total_reps': self.count, 'correct_form_percentage': 0, 'total_phases_tracked': 0}

        correct_phases = sum(1 for p in self.phase_history if p['correct'])
        correct_percentage = (correct_phases / len(self.phase_history)) * 100

        return {
            'total_reps': self.count,
            'correct_form_percentage': round(correct_percentage, 1),
            'total_phases_tracked': len(self.phase_history)
        }
