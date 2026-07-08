import os
import logging
import numpy as np
import librosa
import scipy.stats

logger = logging.getLogger("hindi-asr-backend")

def extract_acoustic_biomarkers(audio_path: str) -> dict:
    """
    Extracts acoustic biomarkers directly from the normalized 16 kHz WAV audio file.
    Completely read-only, never modifies the input audio.
    
    Returns a dictionary containing pitch, energy, speech_duration, mfcc, spectral,
    prosody, and stability metrics.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file '{audio_path}' does not exist.")

    # 1. Load Audio
    # Keep native sample rate (None) which will be 16kHz for normalized WAVs
    y, sr = librosa.load(audio_path, sr=None)
    
    total_audio_duration = librosa.get_duration(y=y, sr=sr)
    if len(y) == 0 or total_audio_duration == 0.0:
        # Graceful empty/silent audio metrics return
        return {
            "pitch": {"mean_pitch": 0.0, "median_pitch": 0.0, "std_pitch": 0.0, "min_pitch": 0.0, "max_pitch": 0.0},
            "energy": {"rms_mean": 0.0, "rms_std": 0.0, "peak_energy": 0.0},
            "speech_duration": {
                "total_audio_duration": 0.0,
                "estimated_speech_duration": 0.0,
                "silence_duration": 0.0,
                "silence_ratio": 0.0
            },
            "mfcc": {f"mfcc_{i}": {"mean": 0.0, "std": 0.0} for i in range(1, 14)},
            "spectral": {
                "spectral_centroid": {"mean": 0.0, "std": 0.0},
                "spectral_bandwidth": {"mean": 0.0, "std": 0.0},
                "spectral_rolloff": {"mean": 0.0, "std": 0.0},
                "zero_crossing_rate": {"mean": 0.0, "std": 0.0}
            },
            "prosody": {"voiced_ratio": 0.0, "pitch_variability": 0.0, "energy_variability": 0.0},
            "stability": {"articulation_consistency": 1.0, "pause_energy_variance": 0.0}
        }

    # 2. Voice Energy Metrics
    rms = librosa.feature.rms(y=y)[0]
    rms_mean = np.mean(rms)
    rms_std = np.std(rms)
    peak_energy = np.max(np.abs(y)) if len(y) > 0 else 0.0

    energy_metrics = {
        "rms_mean": round(float(rms_mean), 4),
        "rms_std": round(float(rms_std), 4),
        "peak_energy": round(float(peak_energy), 4)
    }

    # 3. Speech Duration & Silence Ratio
    # Split audio based on silence detection (top_db=25 is standard for speech)
    # If absolute peak energy is extremely low, treat the entire file as silent
    if peak_energy < 1e-4:
        non_silent_intervals = []
    else:
        non_silent_intervals = librosa.effects.split(y, top_db=25)
        
    estimated_speech_duration = sum((end - start) / sr for start, end in non_silent_intervals)
    silence_duration = max(0.0, total_audio_duration - estimated_speech_duration)
    silence_ratio = silence_duration / total_audio_duration if total_audio_duration > 0 else 0.0

    speech_duration_metrics = {
        "total_audio_duration": round(float(total_audio_duration), 2),
        "estimated_speech_duration": round(float(estimated_speech_duration), 2),
        "silence_duration": round(float(silence_duration), 2),
        "silence_ratio": round(float(silence_ratio), 3)
    }

    # 4. Pitch Features (F0 Estimation using PYIN)
    fmin = 75
    fmax = 300
    try:
        # Use pyin for high-precision fundamental frequency tracking
        f0, voiced_flag, voiced_probs = librosa.pyin(
            y, fmin=fmin, fmax=fmax, sr=sr
        )
        voiced_f0 = f0[~np.isnan(f0)]
    except Exception as pyin_ex:
        logger.warning(f"pYIN failed for pitch tracking: {pyin_ex}. Falling back to YIN.")
        try:
            # Fallback to YIN pitch tracker
            f0 = librosa.yin(y, fmin=fmin, fmax=fmax, sr=sr)
            voiced_f0 = f0
            voiced_flag = np.ones_like(f0)
        except Exception:
            voiced_f0 = np.array([])
            voiced_flag = np.array([])

    if len(voiced_f0) > 0:
        mean_pitch = np.mean(voiced_f0)
        median_pitch = np.median(voiced_f0)
        std_pitch = np.std(voiced_f0)
        min_pitch = np.min(voiced_f0)
        max_pitch = np.max(voiced_f0)
    else:
        mean_pitch = median_pitch = std_pitch = min_pitch = max_pitch = 0.0

    pitch_metrics = {
        "mean_pitch": round(float(mean_pitch), 2),
        "median_pitch": round(float(median_pitch), 2),
        "std_pitch": round(float(std_pitch), 2),
        "min_pitch": round(float(min_pitch), 2),
        "max_pitch": round(float(max_pitch), 2)
    }

    # 5. MFCC Statistics (Coefficients 1-13)
    # limit n_fft in case audio signal is extremely short
    n_fft = min(2048, len(y))
    hop_length = n_fft // 4
    
    # Extract mel-frequency cepstral coefficients
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, n_fft=n_fft, hop_length=hop_length)
    mfcc_metrics = {}
    for i in range(13):
        coef_vals = mfccs[i]
        mfcc_metrics[f"mfcc_{i+1}"] = {
            "mean": round(float(np.mean(coef_vals)), 2),
            "std": round(float(np.std(coef_vals)), 2)
        }

    # 6. Spectral Features (Centroid, Bandwidth, Rolloff, ZCR)
    try:
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr, n_fft=n_fft, hop_length=hop_length)[0]
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr, n_fft=n_fft, hop_length=hop_length)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, n_fft=n_fft, hop_length=hop_length)[0]
    except Exception:
        spectral_centroid = np.array([0.0])
        spectral_bandwidth = np.array([0.0])
        spectral_rolloff = np.array([0.0])
        
    zero_crossing_rate = librosa.feature.zero_crossing_rate(y=y, frame_length=n_fft, hop_length=hop_length)[0]

    spectral_metrics = {
        "spectral_centroid": {
            "mean": round(float(np.mean(spectral_centroid)), 2),
            "std": round(float(np.std(spectral_centroid)), 2)
        },
        "spectral_bandwidth": {
            "mean": round(float(np.mean(spectral_bandwidth)), 2),
            "std": round(float(np.std(spectral_bandwidth)), 2)
        },
        "spectral_rolloff": {
            "mean": round(float(np.mean(spectral_rolloff)), 2),
            "std": round(float(np.std(spectral_rolloff)), 2)
        },
        "zero_crossing_rate": {
            "mean": round(float(np.mean(zero_crossing_rate)), 4),
            "std": round(float(np.std(zero_crossing_rate)), 4)
        }
    }

    # 7. Prosody Features
    voiced_ratio = np.mean(voiced_flag) if len(voiced_flag) > 0 else 0.0
    pitch_variability = std_pitch / mean_pitch if mean_pitch > 0 else 0.0
    energy_variability = rms_std / rms_mean if rms_mean > 0 else 0.0

    prosody_metrics = {
        "voiced_ratio": round(float(voiced_ratio), 3),
        "pitch_variability": round(float(pitch_variability), 3),
        "energy_variability": round(float(energy_variability), 3)
    }

    # 8. Speaking Stability
    # Articulation consistency: variance of consecutive fundamental frequency differences
    if len(voiced_f0) > 1:
        diffs = np.diff(voiced_f0)
        # Higher consistency corresponds to a lower variance of differences
        articulation_consistency = 1.0 / (1.0 + np.var(diffs))
    else:
        articulation_consistency = 1.0

    # Pause energy variance: variance of RMS energy in silent frames
    pause_rms = rms[rms < rms_mean] if len(rms) > 0 else np.array([])
    pause_energy_variance = np.var(pause_rms) if len(pause_rms) > 0 else 0.0

    stability_metrics = {
        "articulation_consistency": round(float(articulation_consistency), 4),
        "pause_energy_variance": round(float(pause_energy_variance), 6)
    }

    return {
        "pitch": pitch_metrics,
        "energy": energy_metrics,
        "speech_duration": speech_duration_metrics,
        "mfcc": mfcc_metrics,
        "spectral": spectral_metrics,
        "prosody": prosody_metrics,
        "stability": stability_metrics
    }
