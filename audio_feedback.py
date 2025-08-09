"""
Modulo per generare e riprodurre feedback audio usando text-to-speech
"""
import threading
import time

class AudioFeedback:
    """
    Classe per gestire il feedback audio in tempo reale durante gli esercizi
    """

    def __init__(self, rate=200, volume=0.8):
        self.rate = rate
        self.volume = volume
        self.engine = None
        self.is_speaking = False

        self.last_message = ""
        self.last_message_time = 0
        self.min_message_interval = 3.0

        self._init_tts()

    def _init_tts(self):
        try:
            import pyttsx3
            self.engine = pyttsx3.init()

            self.engine.setProperty('rate', self.rate)
            self.engine.setProperty('volume', self.volume)

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
        if not self.engine or not message:
            print(f"🔊 Audio: {message}")
            return

        current_time = time.time()

        if not priority and (message == self.last_message and 
                           current_time - self.last_message_time < self.min_message_interval):
            return

        self.last_message = message
        self.last_message_time = current_time

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
        if count == 1:
            message = "Prima ripetizione!"
        elif count <= 5:
            message = f"{count} ripetizioni!"
        elif count % 5 == 0:
            message = f"{count} ripetizioni, ottimo lavoro!"
        else:
            return

        self.speak(message, priority=True)

    def provide_form_feedback(self, feedback_message):
        if feedback_message and feedback_message not in ["Ottima forma!", "Errore"]:
            self.speak(feedback_message)

    def announce_exercise_start(self, exercise_name):
        exercise_names = {
            'squat': 'squat',
            'pushup': 'flessioni',
            'bicep_curl': 'curl bicipiti'
        }

        name = exercise_names.get(exercise_name, exercise_name)
        message = f"Iniziamo con {name}. Mantieni la forma corretta!"
        self.speak(message, priority=True)

    def set_voice_properties(self, rate=None, volume=None):
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

    def test_audio(self):
        self.speak("Sistema audio funzionante!", priority=True)

    def stop(self):
        if self.engine:
            try:
                self.engine.stop()
            except:
                pass
