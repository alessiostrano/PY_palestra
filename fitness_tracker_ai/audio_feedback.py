"""
Modulo per generare e riprodurre feedback audio usando text-to-speech
"""
import pyttsx3
import threading
import queue
import time

class AudioFeedback:
    """
    Classe per gestire il feedback audio in tempo reale durante gli esercizi
    """

    def __init__(self, rate=200, volume=0.8):
        """
        Inizializza il sistema di text-to-speech

        Args:
            rate: Velocità di pronuncia (parole per minuto)
            volume: Volume audio (0.0-1.0)
        """
        try:
            self.engine = pyttsx3.init()

            # Configura le proprietà del TTS
            self.engine.setProperty('rate', rate)
            self.engine.setProperty('volume', volume)

            # Prova a impostare una voce italiana se disponibile
            voices = self.engine.getProperty('voices')
            for voice in voices:
                if 'italian' in voice.name.lower() or 'it' in voice.id.lower():
                    self.engine.setProperty('voice', voice.id)
                    break

            # Sistema di code per gestire i messaggi audio in modo asincrono
            self.audio_queue = queue.Queue()
            self.is_speaking = False
            self.audio_thread = None
            self.stop_audio = False

            # Avvia il thread per l'audio
            self._start_audio_thread()

            # Cache dei messaggi per evitare ripetizioni eccessive
            self.last_message = ""
            self.last_message_time = 0
            self.min_message_interval = 2.0  # Secondi tra messaggi simili

        except Exception as e:
            print(f"Errore nell'inizializzazione del TTS: {e}")
            self.engine = None

    def _start_audio_thread(self):
        """
        Avvia il thread per gestire l'audio in background
        """
        self.audio_thread = threading.Thread(target=self._audio_worker, daemon=True)
        self.audio_thread.start()

    def _audio_worker(self):
        """
        Worker thread per gestire la riproduzione audio
        """
        while not self.stop_audio:
            try:
                # Aspetta un messaggio dalla coda con timeout
                message = self.audio_queue.get(timeout=1.0)

                if message and self.engine:
                    self.is_speaking = True

                    # Pulisce eventuali messaggi in coda per evitare sovrapposizioni
                    while not self.audio_queue.empty():
                        try:
                            self.audio_queue.get_nowait()
                        except queue.Empty:
                            break

                    # Pronuncia il messaggio
                    self.engine.say(message)
                    self.engine.runAndWait()

                    self.is_speaking = False

                self.audio_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                print(f"Errore nel thread audio: {e}")
                self.is_speaking = False

    def speak(self, message, priority=False):
        """
        Aggiunge un messaggio alla coda per la riproduzione

        Args:
            message: Testo da pronunciare
            priority: Se True, svuota la coda e riproduce immediatamente
        """
        if not self.engine or not message:
            return

        current_time = time.time()

        # Evita ripetizioni eccessive dello stesso messaggio
        if (message == self.last_message and 
            current_time - self.last_message_time < self.min_message_interval):
            return

        self.last_message = message
        self.last_message_time = current_time

        # Se è prioritario, svuota la coda
        if priority:
            while not self.audio_queue.empty():
                try:
                    self.audio_queue.get_nowait()
                    self.audio_queue.task_done()
                except queue.Empty:
                    break

        # Aggiunge il messaggio alla coda
        try:
            self.audio_queue.put(message, timeout=1.0)
        except queue.Full:
            print("Coda audio piena, messaggio ignorato")

    def announce_rep_count(self, count):
        """
        Annuncia il numero di ripetizioni completate

        Args:
            count: Numero di ripetizioni
        """
        if count == 1:
            message = "Prima ripetizione!"
        elif count <= 10:
            message = f"{count} ripetizioni!"
        elif count % 5 == 0:  # Annuncia ogni 5 ripetizioni dopo le prime 10
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
        if feedback_message and feedback_message != "Ottima forma!":
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

        if rate is not None:
            self.engine.setProperty('rate', rate)
        if volume is not None:
            self.engine.setProperty('volume', volume)

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
        self.stop_audio = True

        # Pulisce la coda
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
                self.audio_queue.task_done()
            except queue.Empty:
                break

        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=2.0)

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
