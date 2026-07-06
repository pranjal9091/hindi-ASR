import subprocess
import os
import sys

def preprocess_audio(input_path: str, output_path: str, normalize: bool = False, denoise: bool = False) -> str:
    """
    Preprocess input audio to 16kHz, mono, PCM 16-bit WAV format using FFmpeg.
    
    Args:
        input_path (str): Path to the input audio file.
        output_path (str): Path to save the preprocessed WAV file.
        normalize (bool): Enable EBU R128 loudness normalization.
        denoise (bool): Enable FFT-based noise reduction.
        
    Returns:
        str: Absolute path of the preprocessed audio file.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input audio file not found: {input_path}")
        
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Build FFmpeg command
    cmd = ["ffmpeg", "-y", "-i", input_path]
    
    # Audio filters
    audio_filters = []
    if denoise:
        audio_filters.append("afftdn")
    if normalize:
        audio_filters.append("loudnorm")
        
    if audio_filters:
        cmd.extend(["-af", ",".join(audio_filters)])
        
    # Standard output parameters for Whisper: 16kHz, mono, 16-bit PCM WAV
    cmd.extend([
        "-ar", "16000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        output_path
    ])
    
    print(f"Running FFmpeg command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("FFmpeg audio preprocessing complete.")
        return os.path.abspath(output_path)
    except subprocess.CalledProcessError as e:
        print(f"Error during FFmpeg audio preprocessing:\n{e.stderr}", file=sys.stderr)
        raise RuntimeError(f"FFmpeg failed with exit code {e.returncode}: {e.stderr}")
    except FileNotFoundError:
        raise RuntimeError("FFmpeg executable not found on the system. Please ensure FFmpeg is installed and in the PATH.")
