"""
Modulo per feedback audio con text-to-speech
VERSIONE SEMPLIFICATA E ROBUSTA
"""
import threading
import time

class AudioFeedback:
    """
    Sistema di feedback audio con fallback per deployment
    """

    def __init__(self, rate=200, volume=0.8):
        self.rate = rate
        self.volume = volume
        self.engine = None
        self.is_speaking = False

        self.last_message = ""
        self.last_message_time = 0
        self.min_message_interval = 2.5

        self._init_tts()

    def _init_tts(self):
        """Inizializza TTS con fallback sicuro"""
        try:
            import pyttsx3
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', self.rate)
            self.engine.setProperty('volume', self.volume)
            print("✅ TTS inizializzato")
        except Exception as e:
            print(f"⚠️ TTS non disponibile: {e}")
            self.engine = None

    def speak(self, message, priority=False):
        """Pronuncia messaggio con fallback console"""
        if not message:
            return

        current_time = time.time()

        # Evita spam di messaggi
        if not priority and (message == self.last_message and 
                           current_time - self.last_message_time < self.min_message_interval):
            return

        self.last_message = message
        self.last_message_time = current_time

        # Console fallback sempre disponibile
        print(f"🔊 Audio: {message}")

        # Prova TTS se disponibile
        if self.engine:
            def speak_thread():
                try:
                    if not self.is_speaking:
                        self.is_speaking = True
                        self.engine.say(message)
                        self.engine.runAndWait()
                        self.is_speaking = False
                except:
                    self.is_speaking = False

            threading.Thread(target=speak_thread, daemon=True).start()

    def announce_rep_count(self, count):
        """Annuncia conteggio ripetizioni"""
        if count == 1:
            message = "Prima ripetizione!"
        elif count <= 5:
            message = f"{count} ripetizioni!"
        elif count % 5 == 0:
            message = f"Ottimo! {count} ripetizioni!"
        else:
            return

        self.speak(message, priority=True)

    def provide_form_feedback(self, feedback_message):
        """Fornisce feedback sulla forma"""
        if feedback_message and feedback_message not in ["Ottima forma!", "Errore"]:
            self.speak(feedback_message)

    def announce_exercise_start(self, exercise_name):
        """Annuncia inizio esercizio"""
        exercise_names = {
            'squat': 'squat',
            'pushup': 'flessioni', 
            'bicep_curl': 'curl bicipiti'
        }

        name = exercise_names.get(exercise_name, exercise_name)
        message = f"Iniziamo con {name}!"
        self.speak(message, priority=True)

    def test_audio(self):
        """Test del sistema audio"""
        self.speak("Sistema audio funzionante!", priority=True)

    def set_voice_properties(self, rate=None, volume=None):
        """Modifica proprietà voce"""
        if self.engine:
            try:
                if rate is not None:
                    self.rate = rate
                    self.engine.setProperty('rate', rate)
                if volume is not None:
                    self.volume = volume
                    self.engine.setProperty('volume', volume)
            except:
                pass

    def stop(self):
        """Ferma il sistema audio"""
        if self.engine:
            try:
                self.engine.stop()
            except:
                pass
