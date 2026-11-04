import os
import wave
import deepspeech
import numpy as np
from scipy.signal import resample


class AudioText:
    deep_speech_rate = 16000

    def __init__(self, wav_file: str, model_path: str, scorer_path: str):
        if not os.path.isfile(wav_file):
            raise ValueError("The specified wav file does not exist.")
        self.wav_file = wav_file

        if not os.path.isfile(model_path):
            raise ValueError("The specified model file does not exist.")
        if not os.path.isfile(scorer_path):
            raise ValueError("The specified scorer file does not exist.")

        self.model = deepspeech.Model(model_path)
        self.model.enableExternalScorer(scorer_path)

    def read_wav_file(self):
        with wave.open(self.wav_file, "rb") as wf:
            channels = wf.getnchannels()
            frames = wf.getnframes()
            buffer = wf.readframes(frames)
            rate = wf.getframerate()
            return buffer, rate, channels

    @staticmethod
    def resample_audio(audio, original_rate, target_rate=deep_speech_rate):
        if original_rate != target_rate:
            print(f"Resampling from {original_rate} Hz to {target_rate} Hz...")
            duration = len(audio) / original_rate
            num_samples = int(duration * target_rate)
            audio = resample(audio, num_samples)
        return audio

    @staticmethod
    def convert_to_mono(audio, channels):
        if channels == 2:
            print("Converting stereo to mono...")
            audio = audio.reshape((-1, 2))
            audio = audio.mean(axis=1)
        return audio

    def run(self):
        try:
            buffer, rate, channels = self.read_wav_file()
        except Exception as e:
            print(f"Error reading WAV file: {e}")
            return None

        audio = np.frombuffer(buffer, dtype=np.int16)
        audio = AudioText.convert_to_mono(audio, channels)

        if rate != AudioText.deep_speech_rate:
            audio = AudioText.resample_audio(audio, rate)

        audio = audio.astype(np.int16)
        text = self.model.stt(audio)
        return text


if __name__ == "__main__":
    audio_file = r"wav_files/2.wav"
    obj = AudioText(audio_file, "models/deepspeech-0.9.3-models.pbmm", "models/deepspeech-0.9.3-models.scorer")
    print(obj.run())
