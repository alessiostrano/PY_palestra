"""
Modulo per generare e riprodurre feedback audio usando text-to-speech
Versione aggiornata e semplificata per deployment
"""
import threading
import time

class AudioFeedback:
    """
    Classe per gestire il feedback audio in tempo reale durante gli esercizi
    Versione semplificata per evitare problemi di deployment
    """

    def __init__(self, rate=200, volume=0.8):
        """
        Inizializza il sistema di text-to-speech

        Args:
            rate: Velocità di pronuncia (parole per minuto)
            volume: Volume audio (0.0-1.0)
        """
        self.rate = rate
        self.volume = volume
        self.engine = None
        self.is_speaking = False

        # Cache dei messaggi per evitare ripetizioni eccessive
        self.last_message = ""
        self.last_message_time = 0
        self.min_message_interval = 3.0  # Secondi tra messaggi simili

        # Inizializza TTS in modo sicuro
        self._init_tts()

    def _init_tts(self):
        """
        Inizializza TTS in modo sicuro per deployment
        """
        try:
            import pyttsx3
            self.engine = pyttsx3.init()

            # Configura le proprietà del TTS
            self.engine.setProperty('rate', self.rate)
            self.engine.setProperty('volume', self.volume)

            # Prova a impostare una voce italiana se disponibile
            voices = self.engine.getProperty('voices')
            if voices:
                for voice in voices:
                    if voice and ('italian' in voice.name.lower() or 'it' in voice.id.lower()):
                        self.engine.setProperty('voice', voice.id)
                        break

            print("✅ TTS inizializzato correttamente")

        except Exception as e:
            print(f"⚠️ TTS non disponibile: {e}")
            self.engine = None

    def speak(self, message, priority=False):
        """
        Pronuncia un messaggio (versione semplificata per deployment)

        Args:
            message: Testo da pronunciare
            priority: Se True, ignora l'intervallo minimo
        """
        if not self.engine or not message:
            print(f"🔊 Audio: {message}")  # Fallback a console
            return

        current_time = time.time()

        # Evita ripetizioni eccessive dello stesso messaggio
        if not priority and (message == self.last_message and 
                           current_time - self.last_message_time < self.min_message_interval):
            return

        self.last_message = message
        self.last_message_time = current_time

        # Pronuncia in thread separato per non bloccare l'app
        def speak_thread():
            try:
                if not self.is_speaking:
                    self.is_speaking = True
                    self.engine.say(message)
                    self.engine.runAndWait()
                    self.is_speaking = False
            except Exception as e:
                print(f"Errore TTS: {e}")
                self.is_speaking = False

        thread = threading.Thread(target=speak_thread, daemon=True)
        thread.start()

    def announce_rep_count(self, count):
        """
        Annuncia il numero di ripetizioni completate

        Args:
            count: Numero di ripetizioni
        """
        if count == 1:
            message = "Prima ripetizione!"
        elif count <= 5:
            message = f"{count} ripetizioni!"
        elif count % 5 == 0:  # Annuncia ogni 5 ripetizioni dopo le prime 5
            message = f"{count} ripetizioni, ottimo lavoro!"
        else:
            return  # Non annunciare per evitare troppi messaggi

        self.speak(message, priority=True)

    def provide_form_feedback(self, feedback_message):
        """
        Fornisce feedback sulla forma dell'esercizio

        Args:
            feedback_message: Messaggio di feedback
        """
        if feedback_message and feedback_message not in ["Ottima forma!", "Errore"]:
            self.speak(feedback_message)

    def announce_exercise_start(self, exercise_name):
        """
        Annuncia l'inizio di un esercizio

        Args:
            exercise_name: Nome dell'esercizio
        """
        exercise_names = {
            'squat': 'squat',
            'pushup': 'flessioni',
            'bicep_curl': 'curl bicipiti'
        }

        name = exercise_names.get(exercise_name, exercise_name)
        message = f"Iniziamo con {name}. Mantieni la forma corretta!"
        self.speak(message, priority=True)

    def announce_good_form(self):
        """
        Conferma quando la forma è corretta
        """
        messages = ["Ottima forma!", "Perfetto!", "Continua così!"]
        import random
        message = random.choice(messages)
        self.speak(message)

    def announce_session_complete(self, total_reps, exercise_type):
        """
        Annuncia il completamento della sessione

        Args:
            total_reps: Numero totale di ripetizioni
            exercise_type: Tipo di esercizio
        """
        exercise_names = {
            'squat': 'squat',
            'pushup': 'flessioni',
            'bicep_curl': 'curl bicipiti'
        }

        name = exercise_names.get(exercise_type, exercise_type)

        if total_reps == 0:
            message = "Sessione completata! Riprova con la forma corretta."
        elif total_reps == 1:
            message = f"Sessione completata! Hai fatto 1 {name} perfetto!"
        else:
            message = f"Sessione completata! Hai fatto {total_reps} {name}. Ottimo lavoro!"

        self.speak(message, priority=True)

    def set_voice_properties(self, rate=None, volume=None):
        """
        Modifica le proprietà della voce

        Args:
            rate: Nuova velocità di pronuncia
            volume: Nuovo volume
        """
        if not self.engine:
            return

        try:
            if rate is not None:
                self.rate = rate
                self.engine.setProperty('rate', rate)
            if volume is not None:
                self.volume = volume
                self.engine.setProperty('volume', volume)
        except Exception as e:
            print(f"Errore impostazione voce: {e}")

    def is_currently_speaking(self):
        """
        Controlla se il sistema sta attualmente parlando

        Returns:
            bool: True se sta parlando
        """
        return self.is_speaking

    def stop(self):
        """
        Ferma il sistema audio e pulisce le risorse
        """
        if self.engine:
            try:
                self.engine.stop()
            except:
                pass

    def test_audio(self):
        """
        Testa il sistema audio
        """
        self.speak("Sistema audio funzionante!", priority=True)
