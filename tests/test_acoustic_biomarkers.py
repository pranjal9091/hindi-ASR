import unittest
import os
import tempfile
import sys
import numpy as np
import scipy.io.wavfile as wavfile

# Allow importing from src
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.acoustic_biomarkers import extract_acoustic_biomarkers

class TestAcousticBiomarkers(unittest.TestCase):
    def setUp(self):
        self.temp_files = []

    def tearDown(self):
        for path in self.temp_files:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass

    def _create_temp_wav(self, signal, sr=16000):
        # Scale signal to 16-bit integer PCM WAV format
        scaled_signal = np.int16(signal * 32767)
        temp_fd, temp_path = tempfile.mkstemp(suffix=".wav")
        os.close(temp_fd)
        wavfile.write(temp_path, sr, scaled_signal)
        self.temp_files.append(temp_path)
        return temp_path

    def test_valid_wav(self):
        # 1-second 220Hz sine wave (voiced speech approximation) at 16kHz
        sr = 16000
        t = np.linspace(0, 1.0, sr, endpoint=False)
        # Sine wave with amplitude 0.5
        signal = 0.5 * np.sin(2 * np.pi * 220 * t)
        
        wav_path = self._create_temp_wav(signal, sr)
        
        result = extract_acoustic_biomarkers(wav_path)
        
        # Verify presence of all required sections
        self.assertIn("pitch", result)
        self.assertIn("energy", result)
        self.assertIn("speech_duration", result)
        self.assertIn("mfcc", result)
        self.assertIn("spectral", result)
        self.assertIn("prosody", result)
        self.assertIn("stability", result)
        
        # Duration verification
        self.assertAlmostEqual(result["speech_duration"]["total_audio_duration"], 1.0, delta=0.05)
        
        # Pitch verification (sine wave pitch should be near 220 Hz)
        self.assertGreater(result["pitch"]["mean_pitch"], 0.0)
        self.assertAlmostEqual(result["pitch"]["mean_pitch"], 220.0, delta=10.0)
        
        # Energy verification
        self.assertGreater(result["energy"]["rms_mean"], 0.0)
        self.assertAlmostEqual(result["energy"]["peak_energy"], 0.5, delta=0.05)

    def test_silent_wav(self):
        # 1-second silence
        sr = 16000
        signal = np.zeros(sr)
        
        wav_path = self._create_temp_wav(signal, sr)
        
        result = extract_acoustic_biomarkers(wav_path)
        
        # Silent audio fundamental frequency pitch tracking should yield 0.0
        self.assertEqual(result["pitch"]["mean_pitch"], 0.0)
        
        # Energy should be virtually 0.0
        self.assertAlmostEqual(result["energy"]["rms_mean"], 0.0, places=3)
        self.assertAlmostEqual(result["energy"]["peak_energy"], 0.0, places=3)
        
        # Silence ratio should be close to 1.0 (highly silent)
        self.assertGreaterEqual(result["speech_duration"]["silence_ratio"], 0.9)

    def test_short_wav(self):
        # 50-millisecond short segment (800 samples)
        sr = 16000
        t = np.linspace(0, 0.05, 800, endpoint=False)
        signal = 0.5 * np.sin(2 * np.pi * 200 * t)
        
        wav_path = self._create_temp_wav(signal, sr)
        
        # Process should execute successfully without crash/nfft errors
        result = extract_acoustic_biomarkers(wav_path)
        self.assertAlmostEqual(result["speech_duration"]["total_audio_duration"], 0.05, delta=0.01)

    def test_corrupted_wav(self):
        # Write corrupted binary bytes instead of a valid WAV header
        temp_fd, temp_path = tempfile.mkstemp(suffix=".wav")
        os.close(temp_fd)
        with open(temp_path, "wb") as f:
            f.write(b"RIFF\x00\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00random corrupted garbage data bytes")
        
        self.temp_files.append(temp_path)
        
        # Should raise an exception when processed by librosa/sndfile
        with self.assertRaises(Exception):
            extract_acoustic_biomarkers(temp_path)

if __name__ == "__main__":
    unittest.main()
