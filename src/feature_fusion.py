import math
import logging
import numpy as np

logger = logging.getLogger("hindi-asr-backend")

def build_feature_vector(
    transcript: str,
    speech_analytics: dict,
    acoustic_biomarkers: dict,
    metadata: dict = None
) -> dict:
    """
    Combines every transcript and acoustic feature into a single numerical feature vector.
    Missing, NaN, or non-numeric values are replaced with 0.0.
    
    Returns a dict with a single "features" key containing the flattened numerical values
    and a log count of replaced missing values.
    """
    if speech_analytics is None:
        speech_analytics = {}
    if acoustic_biomarkers is None:
        acoustic_biomarkers = {}
    if metadata is None:
        metadata = {}

    missing_replacements_count = 0

    def clean_num(val) -> float:
        nonlocal missing_replacements_count
        if val is None:
            missing_replacements_count += 1
            return 0.0
        try:
            # Handle float conversions
            fval = float(val)
            if math.isnan(fval) or math.isinf(fval):
                missing_replacements_count += 1
                return 0.0
            return fval
        except (ValueError, TypeError):
            missing_replacements_count += 1
            return 0.0

    features = {}

    # ==========================================
    # 1. Transcript-Based Features
    # ==========================================
    # Safely extract sub-dictionaries
    speech_metrics = speech_analytics.get("speech_metrics", {})
    speech_fluency = speech_analytics.get("speech_fluency", {})
    lexical_features = speech_analytics.get("lexical_features", {})
    fillers = speech_analytics.get("fillers", {})
    repetition_analysis = speech_analytics.get("repetition_analysis", {})
    repetitions = speech_analytics.get("repetitions", {})
    pause_metrics = speech_analytics.get("pause_metrics", {})
    executive_function = speech_analytics.get("executive_function", {})
    memory_indicators = speech_analytics.get("memory_indicators", {})
    sentence_complexity = speech_analytics.get("sentence_complexity", {})
    word_retrieval_difficulty = speech_analytics.get("word_retrieval_difficulty", {})

    features["transcript_total_words"] = clean_num(speech_metrics.get("total_words"))
    features["transcript_total_sentences"] = clean_num(speech_metrics.get("total_sentences"))
    features["transcript_wpm"] = clean_num(speech_fluency.get("speech_rate", speech_metrics.get("words_per_minute")))
    features["transcript_articulation_rate"] = clean_num(speech_fluency.get("articulation_rate"))
    features["transcript_ttr"] = clean_num(lexical_features.get("type_token_ratio"))
    features["transcript_mattr"] = clean_num(lexical_features.get("moving_average_ttr"))
    features["transcript_vocabulary_size"] = clean_num(lexical_features.get("vocabulary_size"))
    features["transcript_fillers_per_minute"] = clean_num(fillers.get("fillers_per_minute"))
    features["transcript_filler_count"] = clean_num(fillers.get("total_count"))
    features["transcript_repetition_count"] = clean_num(repetition_analysis.get("total_repetition_count"))
    features["transcript_phrase_repetition_count"] = clean_num(repetition_analysis.get("repeated_phrases_count"))
    features["transcript_perseveration_score"] = clean_num(repetitions.get("perseveration_score"))
    features["transcript_hesitation_count"] = clean_num(word_retrieval_difficulty.get("hesitation_count"))
    features["transcript_pause_ratio"] = clean_num(pause_metrics.get("pause_ratio"))
    features["transcript_average_pause"] = clean_num(pause_metrics.get("average_pause_duration"))
    features["transcript_max_pause"] = clean_num(pause_metrics.get("maximum_pause_duration"))
    features["transcript_long_pause_count"] = clean_num(pause_metrics.get("long_pauses_count"))
    
    # Timeline warnings count
    warnings = executive_function.get("timeline_inconsistencies")
    features["transcript_timeline_conflict_count"] = clean_num(len(warnings) if isinstance(warnings, list) else None)
    
    features["transcript_memory_phrase_count"] = clean_num(memory_indicators.get("memory_loss_phrases_count"))
    features["transcript_uncertainty_phrase_count"] = clean_num(memory_indicators.get("uncertainty_phrases_count"))
    features["transcript_fragment_count"] = clean_num(sentence_complexity.get("fragment_count"))

    # ==========================================
    # 2. Acoustic features
    # ==========================================
    pitch = acoustic_biomarkers.get("pitch", {})
    energy = acoustic_biomarkers.get("energy", {})
    speech_duration = acoustic_biomarkers.get("speech_duration", {})
    mfcc_dict = acoustic_biomarkers.get("mfcc", {})
    spectral = acoustic_biomarkers.get("spectral", {})
    prosody = acoustic_biomarkers.get("prosody", {})
    stability = acoustic_biomarkers.get("stability", {})

    features["acoustic_pitch_mean"] = clean_num(pitch.get("mean_pitch"))
    features["acoustic_pitch_median"] = clean_num(pitch.get("median_pitch"))
    features["acoustic_pitch_std"] = clean_num(pitch.get("std_pitch"))
    features["acoustic_pitch_min"] = clean_num(pitch.get("min_pitch"))
    features["acoustic_pitch_max"] = clean_num(pitch.get("max_pitch"))

    features["acoustic_energy_rms_mean"] = clean_num(energy.get("rms_mean"))
    features["acoustic_energy_rms_std"] = clean_num(energy.get("rms_std"))
    features["acoustic_energy_peak"] = clean_num(energy.get("peak_energy"))

    # 13 MFCC Coefficients (Mean & Std)
    for i in range(1, 14):
        coef_stats = mfcc_dict.get(f"mfcc_{i}", {})
        features[f"acoustic_mfcc_{i}_mean"] = clean_num(coef_stats.get("mean"))
        features[f"acoustic_mfcc_{i}_std"] = clean_num(coef_stats.get("std"))

    # Spectral
    sc = spectral.get("spectral_centroid", {})
    sb = spectral.get("spectral_bandwidth", {})
    sr = spectral.get("spectral_rolloff", {})
    zcr = spectral.get("zero_crossing_rate", {})

    features["acoustic_spectral_centroid_mean"] = clean_num(sc.get("mean"))
    features["acoustic_spectral_centroid_std"] = clean_num(sc.get("std"))
    features["acoustic_spectral_bandwidth_mean"] = clean_num(sb.get("mean"))
    features["acoustic_spectral_bandwidth_std"] = clean_num(sb.get("std"))
    features["acoustic_spectral_rolloff_mean"] = clean_num(sr.get("mean"))
    features["acoustic_spectral_rolloff_std"] = clean_num(sr.get("std"))
    features["acoustic_zero_crossing_rate_mean"] = clean_num(zcr.get("mean"))
    features["acoustic_zero_crossing_rate_std"] = clean_num(zcr.get("std"))

    # Speech duration
    features["acoustic_speech_duration_total"] = clean_num(speech_duration.get("total_audio_duration"))
    features["acoustic_speech_duration_estimated"] = clean_num(speech_duration.get("estimated_speech_duration"))
    features["acoustic_speech_duration_silence"] = clean_num(speech_duration.get("silence_duration"))
    features["acoustic_silence_ratio"] = clean_num(speech_duration.get("silence_ratio"))

    # Prosody & Stability
    features["acoustic_voiced_ratio"] = clean_num(prosody.get("voiced_ratio"))
    features["acoustic_pitch_variability"] = clean_num(prosody.get("pitch_variability"))
    features["acoustic_energy_variability"] = clean_num(prosody.get("energy_variability"))
    features["acoustic_articulation_consistency"] = clean_num(stability.get("articulation_consistency"))
    features["acoustic_pause_energy_variance"] = clean_num(stability.get("pause_energy_variance"))

    # ==========================================
    # 3. Metadata
    # ==========================================
    features["meta_audio_duration"] = clean_num(metadata.get("audio_duration", speech_duration.get("total_audio_duration", speech_metrics.get("speech_duration"))))
    features["meta_transcript_length"] = clean_num(len(transcript) if transcript is not None else None)
    
    # Language: Map "hi" -> 1.0, any other -> 2.0, missing -> 0.0
    lang_str = metadata.get("language", "hi")
    if lang_str == "hi":
        features["meta_language"] = 1.0
    elif lang_str:
        features["meta_language"] = 2.0
    else:
        features["meta_language"] = 0.0

    features["meta_timestamp"] = clean_num(metadata.get("timestamp"))
    
    # Session ID UUID numerical hash
    sess_id = metadata.get("session_id")
    if sess_id:
        try:
            import uuid
            val_uuid = uuid.UUID(str(sess_id))
            features["meta_session_id"] = float(val_uuid.int & 0xFFFFFFFF)  # Cap size to standard 32-bit int representation
        except Exception:
            features["meta_session_id"] = clean_num(hash(str(sess_id)))
    else:
        features["meta_session_id"] = 0.0

    # Log replacing summary
    logger.info(f"Feature Fusion complete: {len(features)} features collected. Replaced {missing_replacements_count} missing values with 0.0.")

    return {
        "features": features,
        "_missing_replacements_count": missing_replacements_count
    }
