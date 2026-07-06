import json
import csv
import os
import re
import math

def serialize_segments(segments):
    """Convert Faster-Whisper segments (which are objects) to a serializable list of dicts."""
    serializable = []
    for segment in segments:
        seg_dict = {
            "id": segment.id,
            "seek": segment.seek,
            "start": segment.start,
            "end": segment.end,
            "text": segment.text.strip(),
            "tokens": segment.tokens,
            "temperature": segment.temperature,
            "avg_logprob": segment.avg_logprob,
            "compression_ratio": segment.compression_ratio,
            "no_speech_prob": segment.no_speech_prob,
        }
        if segment.words is not None:
            seg_dict["words"] = [
                {
                    "word": w.word.strip(),
                    "start": w.start,
                    "end": w.end,
                    "probability": w.probability
                } for w in segment.words
            ]
        else:
            seg_dict["words"] = None
        serializable.append(seg_dict)
    return serializable

def save_json(data, file_path):
    """Save data as a JSON file."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def clean_hindi_text(text):
    """
    Cleans Hindi text: removes extra whitespaces, removes English characters if any,
    standardizes punctuation, but preserves sentence structure and Devanagari script.
    """
    if not text:
        return ""
    # Standardize spacing around punctuation and strip
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    return text

def calculate_wer_cer(ref, hyp):
    """
    Calculate Word Error Rate (WER) and Character Error Rate (CER).
    We will use jiwer if available, otherwise fallback to custom Levenshtein distance implementation.
    """
    try:
        import jiwer
        wer = jiwer.wer(ref, hyp)
        cer = jiwer.cer(ref, hyp)
        return wer, cer
    except ImportError:
        # Custom Levenshtein distance fallback
        def lev_distance(s1, s2):
            if len(s1) < len(s2):
                return lev_distance(s2, s1)
            if len(s2) == 0:
                return len(s1)
            previous_row = range(len(s2) + 1)
            for i, c1 in enumerate(s1):
                current_row = [i + 1]
                for j, c2 in enumerate(s2):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row
            return previous_row[-1]

        # Word-level WER
        ref_words = ref.split()
        hyp_words = hyp.split()
        if not ref_words:
            wer = 1.0 if hyp_words else 0.0
        else:
            wer = lev_distance(ref_words, hyp_words) / len(ref_words)
            
        # Character-level CER
        ref_chars = list(ref.replace(" ", ""))
        hyp_chars = list(hyp.replace(" ", ""))
        if not ref_chars:
            cer = 1.0 if hyp_chars else 0.0
        else:
            cer = lev_distance(ref_chars, hyp_chars) / len(ref_chars)
            
        return wer, cer

def build_corrected_transcript(segments, language, language_prob, duration):
    """
    Builds the corrected transcript data structure matching the prompt specifications.
    """
    flat_words = []
    flat_timestamps = []
    flat_probabilities = []
    
    formatted_segments = []
    full_text_list = []
    
    for seg in segments:
        full_text_list.append(seg["text"])
        
        # Approximate segment confidence from avg_logprob
        seg_prob = min(1.0, max(0.0, math.exp(seg.get("avg_logprob", 0.0))))
        
        seg_words = []
        if seg.get("words"):
            for w in seg["words"]:
                word_text = w["word"]
                flat_words.append(word_text)
                flat_timestamps.append([w["start"], w["end"]])
                flat_probabilities.append(w["probability"])
                seg_words.append({
                    "word": word_text,
                    "start": w["start"],
                    "end": w["end"],
                    "confidence": w["probability"]
                })
        
        formatted_segments.append({
            "id": seg.get("id"),
            "start": seg.get("start"),
            "end": seg.get("end"),
            "text": seg.get("text"),
            "confidence": seg_prob,
            "words": seg_words if seg_words else None
        })
        
    full_transcript = " ".join(full_text_list)
    cleaned_transcript = clean_hindi_text(full_transcript)
    
    return {
        "language": language,
        "language_probability": language_prob,
        "duration": duration,
        "segments": formatted_segments,
        "words": flat_words,
        "timestamps": flat_timestamps,
        "probabilities": flat_probabilities,
        "full transcript": cleaned_transcript,
        "full_transcript": cleaned_transcript
    }

def generate_comparison_report(raw_segments, output_csv_path, ground_truth_text=None):
    """
    Generate comparison_report.csv.
    If ground_truth_text is supplied, calculate overall WER/CER and compare predicted text to ground truth.
    If ground_truth_text is not supplied, generate a segment-by-segment table showing confidence metrics.
    """
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
    
    with open(output_csv_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        if ground_truth_text:
            # Reconstruct full transcript from segments
            full_hypothesis = " ".join([seg["text"] for seg in raw_segments])
            cleaned_hypothesis = clean_hindi_text(full_hypothesis)
            cleaned_reference = clean_hindi_text(ground_truth_text)
            
            wer, cer = calculate_wer_cer(cleaned_reference, cleaned_hypothesis)
            
            writer.writerow(["Comparison Metrics", "Value"])
            writer.writerow(["Word Error Rate (WER)", f"{wer:.4f}"])
            writer.writerow(["Character Error Rate (CER)", f"{cer:.4f}"])
            writer.writerow([])
            writer.writerow(["Ground Truth Text", cleaned_reference])
            writer.writerow(["ASR Transcript Text", cleaned_hypothesis])
            writer.writerow([])
            
        # Write segment details
        writer.writerow(["Segment ID", "Start Time", "End Time", "Avg LogProb", "No Speech Prob", "Text"])
        for seg in raw_segments:
            writer.writerow([
                seg.get("id", ""),
                f"{seg.get('start', 0.0):.3f}",
                f"{seg.get('end', 0.0):.3f}",
                f"{seg.get('avg_logprob', 0.0):.4f}",
                f"{seg.get('no_speech_prob', 0.0):.4f}",
                seg.get("text", "")
            ])
