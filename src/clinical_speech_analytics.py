import re
import math

def calculate_median(values):
    """Computes the median of a list of numeric values."""
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    if n % 2 == 1:
        return float(sorted_vals[n // 2])
    else:
        return float((sorted_vals[(n // 2) - 1] + sorted_vals[n // 2]) / 2.0)

def calculate_mattr(words, window_size=20):
    """Computes the Moving Average Type-Token Ratio (MATTR) for a list of words."""
    if not words:
        return 0.0
    if len(words) <= window_size:
        return len(set(words)) / len(words)
    
    ttr_sum = 0.0
    count = 0
    for i in range(len(words) - window_size + 1):
        window = words[i:i+window_size]
        ttr_sum += len(set(window)) / window_size
        count += 1
    return ttr_sum / count if count > 0 else 0.0

def analyze_clinical_speech(transcript: str, segments: list) -> dict:
    """
    Computes transcript-based cognitive biomarkers and pause metrics used in dementia screening.
    Runs immediately after transcription and before JSON response.
    
    Args:
        transcript (str): The complete concatenated text transcript.
        segments (list): The list of segment dictionaries returned by Whisper.
        
    Returns:
        dict: Structured clinical speech analytics object containing detailed cognitive biomarkers.
    """
    # 1. Graceful check for empty transcript
    if not transcript or not transcript.strip():
        empty_response = {
            "pause_metrics": {
                "hesitation_pauses_count": 0,
                "significant_pauses_count": 0,
                "long_pauses_count": 0,
                "average_pause_duration": 0.0,
                "median_pause_duration": 0.0,
                "maximum_pause_duration": 0.0,
                "pause_ratio": 0.0,
                "longest_pause_timestamps": [],
                "total_pause_count": 0,
                "long_pause_count": 0,
                "max_pause": 0.0
            },
            "speech_fluency": {
                "words_per_minute": 0.0,
                "articulation_rate": 0.0,
                "speech_rate": 0.0,
                "mean_utterance_length": 0.0,
                "sentence_length_variance": 0.0
            },
            "fillers": {
                "filler_frequency": {},
                "fillers_per_minute": 0.0,
                "filler_distribution": [],
                "total_count": 0,
                "frequency": {}
            },
            "repetitions": {
                "immediate_repetitions_count": 0,
                "immediate_repetitions_examples": [],
                "delayed_repetitions_count": 0,
                "delayed_repetitions_examples": [],
                "phrase_repetitions_count": 0,
                "phrase_repetitions_examples": [],
                "perseveration_score": 0.0
            },
            "lexical_features": {
                "vocabulary_size": 0,
                "type_token_ratio": 0.0,
                "moving_average_ttr": 0.0,
                "lexical_richness": "Low"
            },
            "memory_indicators": {
                "memory_loss_phrases_count": 0,
                "memory_loss_phrases_examples": [],
                "uncertainty_phrases_count": 0,
                "uncertainty_phrases_examples": [],
                "self_corrections_count": 0,
                "self_corrections_examples": [],
                "recall_difficulty_indicators_count": 0,
                "recall_difficulty_locations": [],
                "memory_indicator_count": 0,
                "detected_phrases": [],
                "risk_score": 0.0
            },
            "executive_function": {
                "timeline_inconsistencies": [],
                "contradictory_statements": [],
                "incomplete_thoughts_count": 0,
                "incomplete_thoughts_examples": [],
                "abandoned_sentences_count": 0,
                "abandoned_sentences_examples": []
            },
            "speech_metrics": {
                "total_words": 0,
                "total_sentences": 0,
                "speech_duration": 0.0,
                "words_per_minute": 0.0,
                "chars_per_second": 0.0,
                "avg_sentence_length": 0.0,
                "longest_sentence": "",
                "shortest_sentence": ""
            },
            "repetition_analysis": {
                "repeated_words_count": 0,
                "repeated_words_examples": [],
                "repeated_phrases_count": 0,
                "repeated_phrases_examples": [],
                "repeated_sentences_count": 0,
                "repeated_sentences_examples": [],
                "total_repetition_count": 0
            },
            "lexical_diversity": {
                "unique_words_count": 0,
                "vocabulary_size": 0,
                "type_token_ratio": 0.0,
                "lexical_richness": "Low"
            },
            "sentence_complexity": {
                "avg_words_per_sentence": 0.0,
                "sentence_length_variance": 0.0,
                "incomplete_sentences_count": 0,
                "fragment_count": 0
            },
            "word_retrieval_difficulty": {
                "hesitation_count": 0,
                "locations": []
            },
            "self_corrections": {
                "correction_count": 0,
                "examples": []
            },
            "timeline_consistency": {
                "warnings": []
            },
            "emotion_indicators": {
                "neutral": 1.0,
                "anxious": 0.0,
                "sad": 0.0,
                "frustrated": 0.0,
                "confused": 0.0,
                "dominant_emotion": "Neutral"
            },
            "clinical_summary": {
                "memory_risk": "Low",
                "language_risk": "Low",
                "speech_risk": "Low",
                "overall_cognitive_risk": "Low",
                "explanation": "No transcript available.",
                "disclaimer": "This is an AI-generated cognitive screening summary for research/reference only."
            }
        }
        return empty_response

    text_clean = transcript.strip()
    text_lower = text_clean.lower()

    # Split into sentences
    sentences_raw = re.split(r'[।\n?.!]', text_clean)
    sentences = [s.strip() for s in sentences_raw if s.strip()]
    total_sentences = len(sentences) if sentences else 1

    # Extract words list with timestamps
    words_list = []
    flat_words_text = []
    for seg in segments:
        if seg.get("words"):
            for w in seg["words"]:
                word_clean = w["word"].strip().replace(",", "").replace(".", "").replace("?", "").replace("!", "").replace("।", "")
                if word_clean:
                    words_list.append({
                        "word": word_clean,
                        "start": w["start"],
                        "end": w["end"]
                    })
                    flat_words_text.append(word_clean)
        else:
            seg_text = seg.get("text", "")
            for wd in seg_text.split():
                wd_clean = wd.strip().replace(",", "").replace(".", "").replace("?", "").replace("!", "").replace("।", "")
                if wd_clean:
                    flat_words_text.append(wd_clean)

    total_words = len(flat_words_text)

    # Get speech duration
    duration = 0.0
    if segments:
        duration = max(0.1, segments[-1].get("end", 0.0) - segments[0].get("start", 0.0))
    else:
        duration = 1.0

    # ==========================================
    # 1. PAUSE METRICS
    # ==========================================
    pauses_all = []
    longest_pause_candidates = []
    
    if len(words_list) > 1:
        for i in range(len(words_list) - 1):
            gap = words_list[i+1]["start"] - words_list[i]["end"]
            if gap > 0.25:  # Consider gaps above 250ms as a clinical pause candidate
                pauses_all.append(gap)
                longest_pause_candidates.append({
                    "start": round(words_list[i]["end"], 2),
                    "end": round(words_list[i+1]["start"], 2),
                    "duration": round(gap, 2)
                })

    hesitation_pauses = [p for p in pauses_all if p > 0.3]
    significant_pauses = [p for p in pauses_all if p > 1.0]
    long_pauses = [p for p in pauses_all if p > 2.0]

    avg_pause = sum(pauses_all) / len(pauses_all) if pauses_all else 0.0
    median_pause = calculate_median(pauses_all)
    max_pause = max(pauses_all) if pauses_all else 0.0
    total_pause_time = sum(pauses_all)
    pause_ratio_val = total_pause_time / duration if duration > 0 else 0.0

    longest_pauses_sorted = sorted(longest_pause_candidates, key=lambda x: x["duration"], reverse=True)[:5]

    pause_metrics = {
        "hesitation_pauses_count": len(hesitation_pauses),
        "significant_pauses_count": len(significant_pauses),
        "long_pauses_count": len(long_pauses),
        "average_pause_duration": round(avg_pause, 2),
        "median_pause_duration": round(median_pause, 2),
        "maximum_pause_duration": round(max_pause, 2),
        "pause_ratio": round(pause_ratio_val, 3),
        "longest_pause_timestamps": longest_pauses_sorted,
        # Legacy support
        "total_pause_count": len(pauses_all),
        "long_pause_count": len(long_pauses),
        "max_pause": round(max_pause, 2)
    }

    # ==========================================
    # 2. SPEECH FLUENCY
    # ==========================================
    wpm = (total_words / duration) * 60.0
    
    # Articulation Rate: Words per minute excluding pauses
    fluent_duration = duration - total_pause_time
    if fluent_duration > 0.1:
        articulation_rate_val = (total_words / fluent_duration) * 60.0
    else:
        articulation_rate_val = wpm

    avg_sent_len = total_words / total_sentences
    sentence_lengths = [len(s.split()) for s in sentences]
    
    variance_val = 0.0
    if len(sentence_lengths) > 1:
        mean_len = sum(sentence_lengths) / len(sentence_lengths)
        variance_val = sum((x - mean_len) ** 2 for x in sentence_lengths) / len(sentence_lengths)

    speech_fluency = {
        "words_per_minute": round(wpm, 1),
        "articulation_rate": round(articulation_rate_val, 1),
        "speech_rate": round(wpm, 1),
        "mean_utterance_length": round(avg_sent_len, 1),
        "sentence_length_variance": round(variance_val, 2)
    }

    # ==========================================
    # 3. FILLERS
    # ==========================================
    filler_patterns = {
        "uh": ["uh", "अह"],
        "umm": ["umm", "um", "अम", "उम"],
        "aaa": ["aaa", "aa", "आ", "अ"],
        "haan": ["haan", "han", "हाँ", "हा"],
        "matlab": ["matlab", "मतलब"],
        "toh": ["toh", "तो"],
        "dekhiye": ["dekhiye", "देखिये", "देखो"],
        "acha": ["acha", "achha", "अच्छा"]
    }

    filler_frequency = {}
    total_fillers_count = 0
    filler_distribution = []

    # Map target words for exact matching
    word_to_filler_type = {}
    for f_type, variations in filler_patterns.items():
        for var in variations:
            word_to_filler_type[var.lower()] = f_type

    # Find fillers in words list with timestamps
    for w in words_list:
        w_norm = w["word"].lower()
        if w_norm in word_to_filler_type:
            f_type = word_to_filler_type[w_norm]
            filler_frequency[f_type] = filler_frequency.get(f_type, 0) + 1
            total_fillers_count += 1
            filler_distribution.append({
                "word": w["word"],
                "start": round(w["start"], 2),
                "end": round(w["end"], 2)
            })

    # Fallback to scanning transcript if flat words list has no timestamps
    if total_fillers_count == 0:
        for f_type, variations in filler_patterns.items():
            count = 0
            for var in variations:
                matches = re.findall(rf"\b{var}\b" if var.isascii() else var, text_lower)
                count += len(matches)
            if count > 0:
                filler_frequency[f_type] = count
                total_fillers_count += count

    fillers_per_minute_val = (total_fillers_count / duration) * 60.0

    fillers_data = {
        "filler_frequency": filler_frequency,
        "fillers_per_minute": round(fillers_per_minute_val, 1),
        "filler_distribution": filler_distribution,
        # Legacy support
        "total_count": total_fillers_count,
        "frequency": filler_frequency
    }

    # ==========================================
    # 4. REPETITIONS
    # ==========================================
    immediate_rep_list = []
    delayed_rep_list = []
    phrase_rep_list = []
    
    words_cleaned = [w.lower() for w in flat_words_text if w]

    # Immediate repetitions (back-to-back words)
    if len(words_cleaned) > 1:
        for i in range(len(words_cleaned) - 1):
            if words_cleaned[i] == words_cleaned[i+1]:
                immediate_rep_list.append(words_cleaned[i])

    # Delayed repetitions (duplicate words within 5-word window, but not back-to-back)
    if len(words_cleaned) > 2:
        for i in range(len(words_cleaned)):
            for j in range(i + 2, min(i + 6, len(words_cleaned))):
                if words_cleaned[i] == words_cleaned[j] and words_cleaned[i] != words_cleaned[i+1]:
                    delayed_rep_list.append(words_cleaned[i])
                    break

    # Phrase repetitions (consecutive or delayed repeated 2-4 ngrams)
    for n in range(2, 5):
        if len(words_cleaned) >= n * 2:
            for i in range(len(words_cleaned) - n * 2 + 1):
                phrase1 = words_cleaned[i : i+n]
                phrase2 = words_cleaned[i+n : i+2*n]
                if phrase1 == phrase2:
                    phrase_rep_list.append(" ".join(phrase1))

    total_rep_events = len(immediate_rep_list) + len(delayed_rep_list) + len(phrase_rep_list)
    perseveration_score_val = total_rep_events / len(words_cleaned) if words_cleaned else 0.0

    repetitions_data = {
        "immediate_repetitions_count": len(immediate_rep_list),
        "immediate_repetitions_examples": list(set(immediate_rep_list))[:5],
        "delayed_repetitions_count": len(delayed_rep_list),
        "delayed_repetitions_examples": list(set(delayed_rep_list))[:5],
        "phrase_repetitions_count": len(phrase_rep_list),
        "phrase_repetitions_examples": list(set(phrase_rep_list))[:5],
        "perseveration_score": round(perseveration_score_val, 3)
    }

    # ==========================================
    # 5. LEXICAL FEATURES
    # ==========================================
    unique_words_set = set(words_cleaned)
    vocab_size = len(unique_words_set)
    ttr_val = vocab_size / len(words_cleaned) if words_cleaned else 0.0
    mattr_val = calculate_mattr(words_cleaned, window_size=20)

    lexical_richness_val = "Low"
    if ttr_val > 0.65:
        lexical_richness_val = "High"
    elif ttr_val > 0.45:
        lexical_richness_val = "Medium"

    lexical_features = {
        "vocabulary_size": vocab_size,
        "type_token_ratio": round(ttr_val, 3),
        "moving_average_ttr": round(mattr_val, 3),
        "lexical_richness": lexical_richness_val
    }

    # ==========================================
    # 6. MEMORY INDICATORS
    # ==========================================
    memory_loss_patterns = [
        "याद नहीं", "याद नही", "भूल गया", "भूल गई", "भूल गए",
        "yaad nahi", "yaad nahi hai", "bhool gaya", "bhool gayi", "bhool gaye",
        "remember nahi", "can't remember", "cant remember", "don't recall", "dont recall",
        "i forgot", "forgot"
    ]
    detected_mem_loss = []
    for pat in memory_loss_patterns:
        if re.search(rf"\b{pat}\b" if pat.isascii() else pat, text_lower):
            detected_mem_loss.append(pat)

    uncertainty_patterns = [
        "शायद", "लगता है", "पता नहीं", "पता नही", "समझ नहीं",
        "shayad", "pata nahi", "maybe", "not sure", "don't know", "dont know", "might", "possibly"
    ]
    detected_uncertainty = []
    for pat in uncertainty_patterns:
        if re.search(rf"\b{pat}\b" if pat.isascii() else pat, text_lower):
            detected_uncertainty.append(pat)

    self_correction_patterns = ["नहीं...", "नही...", "मेरा मतलब", "mera matlab", "actually", "sorry"]
    detected_corrections = []
    for pat in self_correction_patterns:
        matches = re.findall(rf"\b{pat}\b" if pat.isascii() else pat, text_lower)
        if matches:
            detected_corrections.extend([pat] * len(matches))

    # Recall difficulties (hesitations or long pauses before content words)
    recall_difficulties = []
    if len(words_list) > 1:
        content_word_pattern = re.compile(r"^[a-zA-Z\u0900-\u097F]{4,}$")  # Content word approximation (4+ characters)
        for i in range(len(words_list) - 1):
            w1 = words_list[i]
            w2 = words_list[i+1]
            gap = w2["start"] - w1["end"]
            
            # Case 1: Long pause before a content word
            if gap > 1.2 and content_word_pattern.match(w2["word"]):
                recall_difficulties.append({
                    "word": w2["word"],
                    "start": round(w2["start"], 2),
                    "trigger": "pause_before_content_word",
                    "pause_duration": round(gap, 2)
                })
            # Case 2: Filler word preceding a pause
            elif gap > 0.8 and w1["word"].lower() in word_to_filler_type:
                recall_difficulties.append({
                    "word": w1["word"],
                    "start": round(w1["start"], 2),
                    "trigger": "filler_before_pause",
                    "pause_duration": round(gap, 2)
                })

    memory_indicators = {
        "memory_loss_phrases_count": len(detected_mem_loss),
        "memory_loss_phrases_examples": list(set(detected_mem_loss)),
        "uncertainty_phrases_count": len(detected_uncertainty),
        "uncertainty_phrases_examples": list(set(detected_uncertainty)),
        "self_corrections_count": len(detected_corrections),
        "self_corrections_examples": list(set(detected_corrections)),
        "recall_difficulty_indicators_count": len(recall_difficulties),
        "recall_difficulty_locations": recall_difficulties[:5],
        # Legacy support
        "memory_indicator_count": len(detected_mem_loss),
        "detected_phrases": list(set(detected_mem_loss)),
        "risk_score": round(min(10.0, len(detected_mem_loss) * 3.33), 1)
    }

    # ==========================================
    # 7. EXECUTIVE FUNCTION
    # ==========================================
    timeline_warnings = []
    
    # 7.1 Timeline Inconsistencies (Days of the week)
    days_hi = {"सोमवार": "Monday", "मंगलवार": "Tuesday", "बुधवार": "Wednesday", "गुरुवार": "Thursday", "शुक्रवार": "Friday", "शनिवार": "Saturday", "रविवार": "Sunday"}
    days_en = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    days_found = []
    for hi, en in days_hi.items():
        if hi in text_clean:
            days_found.append(en)
    for day in days_en:
        if re.search(rf"\b{day}\b", text_lower):
            days_found.append(day.capitalize())
    days_found = list(set(days_found))
    if len(days_found) > 1:
        timeline_warnings.append(f"Conflicting days mentioned ({', '.join(days_found)})")

    # 7.2 Timeline Inconsistencies (Years)
    years_found = re.findall(r'\b(19\d{2}|20\d{2})\b', text_clean)
    unique_years = list(set(years_found))
    if len(unique_years) > 1:
        timeline_warnings.append(f"Conflicting years mentioned ({', '.join(unique_years)})")

    # 7.3 Timeline Inconsistencies (Time of Day)
    morning_context = ["सुबह", "morning"]
    night_context = ["रात", "night", "evening"]
    if any(m in text_lower for m in morning_context) and any(n in text_lower for n in night_context):
        if len(text_lower.split()) < 30:  # If mentioned together in a short window
             timeline_warnings.append("Conflicting time of day mentioned (morning vs. night)")

    # Contradictory statements (simple checks for close proximity yes/no contradictions)
    contradictions = []
    if "हाँ" in text_clean and "नहीं" in text_clean:
        if abs(text_clean.find("हाँ") - text_clean.find("नहीं")) < 40:
            contradictions.append("Immediate Devanagari yes/no negation conflict")
    if "yes" in text_lower and "no" in text_lower:
        if abs(text_lower.find("yes") - text_lower.find("no")) < 30:
            contradictions.append("Immediate English yes/no negation conflict")

    # Incomplete thoughts (ending in ellipsis or dangling indicators)
    incomplete_sentences = []
    for s in sentences:
        if s.endswith("...") or s.endswith("..") or s.endswith("मतलब") or s.endswith("matlab"):
            incomplete_sentences.append(s)

    # Abandoned sentences (short sentence fragments under 3 words that end abruptly)
    abandoned_sentences = []
    for s in sentences:
        s_words = s.split()
        if len(s_words) > 0 and len(s_words) < 3 and not s.endswith("।") and not s.endswith("."):
            abandoned_sentences.append(s)

    executive_function = {
        "timeline_inconsistencies": timeline_warnings,
        "contradictory_statements": contradictions,
        "incomplete_thoughts_count": len(incomplete_sentences),
        "incomplete_thoughts_examples": incomplete_sentences[:5],
        "abandoned_sentences_count": len(abandoned_sentences),
        "abandoned_sentences_examples": abandoned_sentences[:5]
    }

    # ==========================================
    # 8. CLINICAL COGNITIVE SUMMARY
    # ==========================================
    mem_risk = "Low"
    mem_reasons = []
    if len(detected_mem_loss) >= 3 or len(timeline_warnings) >= 2:
        mem_risk = "High"
        mem_reasons.append(f"Multiple memory loss phrases ({len(detected_mem_loss)}) or timeline conflicts detected")
    elif len(detected_mem_loss) > 0 or timeline_warnings or len(detected_uncertainty) >= 2:
        mem_risk = "Medium"
        if len(detected_mem_loss) > 0:
            mem_reasons.append("Memory loss indicators present")
        if timeline_warnings:
            mem_reasons.append("Chronological timeline inconsistencies")
        if len(detected_uncertainty) >= 2:
            mem_reasons.append("Frequent verbal uncertainty")
    else:
        mem_reasons.append("Normal memory retrieval profile")

    lang_risk = "Low"
    lang_reasons = []
    if ttr_val < 0.45 and (total_fillers_count >= 10 or len(phrase_rep_list) >= 3):
        lang_risk = "High"
        lang_reasons.append("Reduced lexical diversity paired with high repetition or filler rates")
    elif ttr_val < 0.55 or total_fillers_count >= 5 or total_rep_events >= 3:
        lang_risk = "Medium"
        if ttr_val < 0.55:
            lang_reasons.append("Moderate type-token ratio")
        if total_fillers_count >= 5:
            lang_reasons.append("Frequent filler insertions")
        if total_rep_events >= 3:
            lang_reasons.append("Elevated verbal repetitions")
    else:
        lang_reasons.append("Vocabulary diversity and fluency within normal ranges")

    speech_risk = "Low"
    speech_reasons = []
    if avg_pause > 1.8 or pause_ratio_val > 0.35 or len(long_pauses) >= 3:
        speech_risk = "High"
        speech_reasons.append("Significantly elevated pause times and silence ratios")
    elif avg_pause > 1.0 or pause_ratio_val > 0.18 or len(long_pauses) >= 1:
        speech_risk = "Medium"
        if avg_pause > 1.0:
            speech_reasons.append("Moderate conversational pauses")
        if pause_ratio_val > 0.18:
            speech_reasons.append("Increased silence-to-speech ratio")
        if len(long_pauses) >= 1:
            speech_reasons.append("Long pauses (>2.0s) present")
    else:
        speech_reasons.append("Speech rate and rhythm within typical conversational bounds")

    risk_levels = [mem_risk, lang_risk, speech_risk]
    overall_cognitive_risk = "Low"
    if risk_levels.count("High") >= 2 or mem_risk == "High":
        overall_cognitive_risk = "High"
    elif "High" in risk_levels or "Medium" in risk_levels:
        overall_cognitive_risk = "Medium"

    explanation_parts = []
    explanation_parts.append(f"Memory: {mem_risk} ({', '.join(mem_reasons)}).")
    explanation_parts.append(f"Language: {lang_risk} ({', '.join(lang_reasons)}).")
    explanation_parts.append(f"Speech: {speech_risk} ({', '.join(speech_reasons)}).")
    explanation_summary = " ".join(explanation_parts)

    clinical_summary = {
        "memory_risk": mem_risk,
        "language_risk": lang_risk,
        "speech_risk": speech_risk,
        "overall_cognitive_risk": overall_cognitive_risk,
        "explanation": explanation_summary,
        "disclaimer": "This is an AI-generated cognitive biomarker screening summary for research/reference only. It is not a clinical diagnosis of dementia or other neurological conditions. Please consult a qualified neuropsychologist or doctor for professional assessments."
    }

    # ==========================================
    # LEGACY WRAPPER STRUCTURE FOR COMPATIBILITY
    # ==========================================
    legacy_speech_metrics = {
        "total_words": total_words,
        "total_sentences": total_sentences,
        "speech_duration": round(duration, 2),
        "words_per_minute": round(wpm, 1),
        "chars_per_second": round(len(text_clean.replace(" ", "")) / duration, 2),
        "avg_sentence_length": round(avg_sent_len, 1),
        "longest_sentence": max(sentences, key=len) if sentences else "",
        "shortest_sentence": min(sentences, key=len) if sentences else ""
    }

    # Emotion Lexicon mapping
    emotion_lexicon = {
        "anxious": ["घबराहट", "चिंता", "डर", "तनाव", "परेशान", "anxiety", "tension", "dar", "darr", "gabhrahat", "worry", "worried", "scared", "anxious"],
        "sad": ["उदास", "दुखी", "रोना", "अकेलापन", "sad", "lonely", "dukh", "udaas", "depressed", "crying"],
        "frustrated": ["गुस्सा", "चिड़चिड़ापन", "तंग", "frustrated", "annoyed", "gussa", "angry", "fed up"],
        "confused": ["भ्रम", "असमंजस", "समझ नहीं आ रहा", "उलझन", "confused", "confusion", "samajh nahi", "clueless"]
    }
    emotion_scores = {"neutral": 1.0, "anxious": 0.0, "sad": 0.0, "frustrated": 0.0, "confused": 0.0}
    matched_any = False
    for emo, keywords in emotion_lexicon.items():
        matches_count = 0
        for kw in keywords:
            matches_count += len(re.findall(rf"\b{kw}\b" if kw.isascii() else kw, text_lower))
        if matches_count > 0:
            emotion_scores[emo] = matches_count * 0.4
            matched_any = True
    if matched_any:
        emotion_scores["neutral"] = max(0.1, 1.0 - sum(v for k, v in emotion_scores.items() if k != "neutral"))
        total = sum(emotion_scores.values())
        for k in emotion_scores:
            emotion_scores[k] = round(emotion_scores[k] / total, 2)
    dominant_emo = max(emotion_scores, key=emotion_scores.get)
    emotion_indicators = {**emotion_scores, "dominant_emotion": dominant_emo.capitalize()}

    # Compile unified biomarker response payload
    return {
        "pause_metrics": pause_metrics,
        "speech_fluency": speech_fluency,
        "fillers": fillers_data,
        "repetitions": repetitions_data,
        "lexical_features": lexical_features,
        "memory_indicators": memory_indicators,
        "executive_function": executive_function,
        "clinical_summary": clinical_summary,
        "emotion_indicators": emotion_indicators,
        # Backward compatible layers
        "speech_metrics": legacy_speech_metrics,
        "repetition_analysis": {
            "repeated_words_count": len(immediate_rep_list),
            "repeated_words_examples": list(set(immediate_rep_list))[:5],
            "repeated_phrases_count": len(phrase_rep_list),
            "repeated_phrases_examples": list(set(phrase_rep_list))[:5],
            "repeated_sentences_count": 0,
            "repeated_sentences_examples": [],
            "total_repetition_count": len(immediate_rep_list) + len(phrase_rep_list)
        },
        "lexical_diversity": {
            "unique_words_count": vocab_size,
            "vocabulary_size": vocab_size,
            "type_token_ratio": round(ttr_val, 3),
            "lexical_richness": lexical_richness_val
        },
        "sentence_complexity": {
            "avg_words_per_sentence": round(avg_sent_len, 1),
            "sentence_length_variance": round(variance_val, 2),
            "incomplete_sentences_count": len(incomplete_sentences),
            "fragment_count": sum(1 for s in sentences if len(s.split()) < 3)
        },
        "word_retrieval_difficulty": {
            "hesitation_count": len(recall_difficulties),
            "locations": recall_difficulties[:5]
        },
        "self_corrections": {
            "correction_count": len(detected_corrections),
            "examples": list(set(detected_corrections))
        },
        "timeline_consistency": {
            "warnings": timeline_warnings
        }
    }
