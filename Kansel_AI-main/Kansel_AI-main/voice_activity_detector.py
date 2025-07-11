import pyaudio
import numpy as np
import time

class VoiceActivityDetector:
    def __init__(self, threshold=400, sample_rate=16000, chunk_size=1024, required_duration=3.0):
        self.threshold = threshold
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.required_duration = required_duration

        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paInt16,
                                  channels=1,
                                  rate=self.sample_rate,
                                  input=True,
                                  frames_per_buffer=self.chunk_size)

        self.voice_start_time = None
        self.last_voice_time = None
        self.is_speaking = False

    def is_voice_detected(self):
        data = self.stream.read(self.chunk_size, exception_on_overflow=False)
        audio_data = np.frombuffer(data, dtype=np.int16)
        volume = np.linalg.norm(audio_data)

        current_time = time.time()

        if volume > self.threshold:
            if self.voice_start_time is None:
                self.voice_start_time = current_time
            self.last_voice_time = current_time

            duration = current_time - self.voice_start_time
            if duration >= self.required_duration:
                if not self.is_speaking:
                    self.is_speaking = True
                    return True
        else:
            if self.last_voice_time and current_time - self.last_voice_time > 1.0:
                self.voice_start_time = None
                self.last_voice_time = None
                self.is_speaking = False

        return False

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
