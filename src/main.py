import argparse
import os
import sys
import time

# Append the directory containing this script to sys.path to allow imports when running from project root
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from audio_utils import preprocess_audio
import utils

def transcribe_audio(
    input_path: str,
    output_dir: str = "data/output",
    normalize: bool = False,
    denoise: bool = False,
    ground_truth: str = None,
    model_size: str = "large-v3",
    device: str = "cpu",
    compute_type: str = "int8",
    model = None
):
    """
    Runs the Hindi ASR transcription pipeline.
    Reuses existing WhisperModel instance if provided, otherwise loads a new one.
    """
    # Verify input exists
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file '{input_path}' does not exist.")
        
    os.makedirs(output_dir, exist_ok=True)
    
    # Determine preprocessed audio path
    input_filename = os.path.basename(input_path)
    name, _ = os.path.splitext(input_filename)
    preprocessed_wav_path = os.path.join(output_dir, f"{name}_preprocessed.wav")
    
    # Step 1: Preprocess Audio
    print("=== STEP 1: Audio Preprocessing ===")
    start_time = time.time()
    preprocessed_path = preprocess_audio(
        input_path=input_path,
        output_path=preprocessed_wav_path,
        normalize=normalize,
        denoise=denoise
    )
    print(f"Preprocessed audio saved to: {preprocessed_path}")
    preprocess_duration = time.time() - start_time
    print(f"Preprocessing took {preprocess_duration:.2f} seconds.\n")
    
    # Step 2: Load Faster-Whisper Model (if not provided)
    if model is None:
        print("=== STEP 2: Loading Faster-Whisper Model ===")
        print(f"Loading '{model_size}' model on '{device}' with '{compute_type}'...")
        whisper_load_start = time.time()
        from faster_whisper import WhisperModel
        model = WhisperModel(model_size, device=device, compute_type=compute_type)
        print(f"Model loaded in {time.time() - whisper_load_start:.2f} seconds.\n")
    else:
        print("=== STEP 2: Reusing Provided Faster-Whisper Model ===")
        
    # Step 3: Run Transcription
    print("=== STEP 3: Transcribing Audio (Hindi Only) ===")
    transcribe_start = time.time()
    
    # Force language="hi" to prevent language identification, and set task="transcribe"
    # Enable word_timestamps to collect timestamps and probabilities for every word
    segments_gen, info = model.transcribe(
        preprocessed_path,
        language="hi",
        task="transcribe",
        word_timestamps=True
    )
    
    print(f"Detected language info: language='{info.language}', probability={info.language_probability:.4f}")
    print(f"Audio duration: {info.duration:.2f} seconds")
    print("Transcribing segments...")
    
    # Consume the generator to get all segments
    segments_list = list(segments_gen)
    transcription_duration = time.time() - transcribe_start
    print(f"Transcription completed in {transcription_duration:.2f} seconds.\n")
    
    # Step 4: Process and Save Outputs
    print("=== STEP 4: Saving Output Files ===")
    
    # Convert segments to JSON-serializable structure
    raw_segments = utils.serialize_segments(segments_list)
    
    # 4.1 Save raw_whisper.json
    raw_whisper_path = os.path.join(output_dir, "raw_whisper.json")
    utils.save_json(raw_segments, raw_whisper_path)
    print(f"Saved raw Whisper segments to: {raw_whisper_path}")
    
    # 4.2 Save corrected_transcript.json
    corrected_data = utils.build_corrected_transcript(
        segments=raw_segments,
        language=info.language,
        language_prob=info.language_probability,
        duration=info.duration
    )
    corrected_transcript_path = os.path.join(output_dir, "corrected_transcript.json")
    utils.save_json(corrected_data, corrected_transcript_path)
    print(f"Saved corrected transcript to: {corrected_transcript_path}")
    
    # 4.3 Load ground truth text if provided
    ground_truth_text = None
    if ground_truth:
        if os.path.exists(ground_truth):
            with open(ground_truth, 'r', encoding='utf-8') as gtf:
                ground_truth_text = gtf.read().strip()
            print(f"Loaded ground truth text from: {ground_truth}")
        else:
            print(f"Warning: Ground truth file '{ground_truth}' not found. Comparison report will omit WER/CER.", file=sys.stderr)
            
    # 4.4 Save comparison_report.csv
    comparison_report_path = os.path.join(output_dir, "comparison_report.csv")
    utils.generate_comparison_report(raw_segments, comparison_report_path, ground_truth_text)
    print(f"Saved comparison report to: {comparison_report_path}")
    
    # Output brief summary
    print("\n=== PIPELINE SUCCESSFUL ===")
    print(f"Full transcript: {corrected_data['full transcript']}")
    print(f"All outputs saved under: {os.path.abspath(output_dir)}")
    
    return corrected_data

def main():
    parser = argparse.ArgumentParser(
        description="Hindi Automatic Speech Recognition (ASR) Pipeline using Faster-Whisper Large-v3"
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to the input audio file"
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="data/output",
        help="Directory to save output files (default: data/output)"
    )
    parser.add_argument(
        "--normalize",
        action="store_true",
        help="Enable FFmpeg loudness normalization (EBU R128)"
    )
    parser.add_argument(
        "--denoise",
        action="store_true",
        help="Enable FFmpeg noise reduction (afftdn)"
    )
    parser.add_argument(
        "--ground-truth", "-g",
        help="Optional path to a file containing ground truth Hindi text for WER/CER comparison"
    )
    parser.add_argument(
        "--model-size",
        default="large-v3",
        help="Faster-Whisper model size to use (default: large-v3)"
    )
    parser.add_argument(
        "--device",
        default="cpu",
        help="Device to run inference on: 'cpu', 'cuda', etc. (default: cpu)"
    )
    parser.add_argument(
        "--compute-type",
        default="int8",
        help="Quantization type: 'int8', 'float16', 'float32', etc. (default: int8)"
    )
    
    args = parser.parse_args()
    
    try:
        transcribe_audio(
            input_path=args.input,
            output_dir=args.output_dir,
            normalize=args.normalize,
            denoise=args.denoise,
            ground_truth=args.ground_truth,
            model_size=args.model_size,
            device=args.device,
            compute_type=args.compute_type
        )
    except Exception as e:
        print(f"ASR pipeline failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

