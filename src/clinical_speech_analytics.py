import re
import math

def analyze_clinical_speech(transcript: str, segments: list) -> dict:
    """
    Computes transcript-based cognitive biomarkers and pause metrics used in dementia screening.
    Runs immediately after transcription and before JSON response.
    
    Args:
        transcript (str): The complete concatenated text transcript.
        segments (list): The list of segment dictionaries returned by Whisper.
        
    Returns:
        dict: Structured clinical speech analytics object.
    """
    # 1. Graceful check for empty transcript
    if not transcript or not transcript.strip():
        return {
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
            "pause_metrics": {
                "total_pause_count": 0,
                "average_pause_duration": 0.0,
                "max_pause": 0.0,
                "long_pause_count": 0,
                "pause_ratio": 0.0
            },
            "fillers": {
                "total_count": 0,
                "frequency": {},
                "fillers_per_minute": 0.0
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
            "memory_indicators": {
                "memory_indicator_count": 0,
                "detected_phrases": [],
                "risk_score": 0.0
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
            "negation_detection": {
                "negated_medical_statements": []
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
                "disclaimer": "This is an AI-generated screening summary. It is not a medical diagnosis."
            }
        }

    # Normalize transcript
    text_clean = transcript.strip()
    text_lower = text_clean.lower()

    # Split into sentences using common Hindi and English sentence delimiters
    sentences_raw = re.split(r'[।\n?.!]', text_clean)
    sentences = [s.strip() for s in sentences_raw if s.strip()]
    total_sentences = len(sentences) if sentences else 1

    # Extract all flat words and their timestamps
    words_list = []
    flat_words_text = []
    for seg in segments:
        if seg.get("words"):
            for w in seg["words"]:
                # Normalize word formatting (strip spaces/symbols)
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

    # 1. Speech Duration
    duration = 0.0
    if segments:
        duration = max(0.1, segments[-1].get("end", 0.0) - segments[0].get("start", 0.0))
    else:
        duration = 1.0

    # 2. Speech Metrics
    wpm = (total_words / duration) * 60.0
    total_chars_no_spaces = len(text_clean.replace(" ", ""))
    cps = total_chars_no_spaces / duration
    avg_sent_len = total_words / total_sentences

    sentence_lengths = [len(s.split()) for s in sentences]
    
    longest_idx = sentence_lengths.index(max(sentence_lengths)) if sentence_lengths else 0
    longest_sent = sentences[longest_idx] if sentences else ""
    
    shortest_idx = sentence_lengths.index(min(sentence_lengths)) if sentence_lengths else 0
    shortest_sent = sentences[shortest_idx] if sentences else ""

    speech_metrics = {
        "total_words": total_words,
        "total_sentences": total_sentences,
        "speech_duration": round(duration, 2),
        "words_per_minute": round(wpm, 1),
        "chars_per_second": round(cps, 2),
        "avg_sentence_length": round(avg_sent_len, 1),
        "longest_sentence": longest_sent,
        "shortest_sentence": shortest_sent
    }

    # 3. Pause Metrics (Silence Gaps using Word Timestamps)
    pauses = []
    long_pauses = 0
    if len(words_list) > 1:
        for i in range(len(words_list) - 1):
            gap = words_list[i+1]["start"] - words_list[i]["end"]
            if gap > 0.25:  # Pause threshold: 250ms
                pauses.append(gap)
                if gap > 2.0:
                    long_pauses += 1
    
    total_pauses = len(pauses)
    avg_pause = sum(pauses) / total_pauses if total_pauses > 0 else 0.0
    max_pause = max(pauses) if total_pauses > 0 else 0.0
    pause_time = sum(pauses)
    pause_ratio = pause_time / duration if duration > 0 else 0.0

    pause_metrics = {
        "total_pause_count": total_pauses,
        "average_pause_duration": round(avg_pause, 2),
        "max_pause": round(max_pause, 2),
        "long_pause_count": long_pauses,
        "pause_ratio": round(pause_ratio, 3)
    }

    # 4. Filler Words Analysis
    # Maps filler labels to regex variations (Devanagari and Hinglish)
    filler_patterns = {
        "uh": [r"\buh\b", r"\bअह\b"],
        "umm": [r"\bumm\b", r"\bum\b", r"\bअम\b", r"\bउम\b"],
        "aaa": [r"\baaa\b", r"\baa\b", r"\bआ\b", r"\bअ\b"],
        "haan": [r"\bhaan\b", r"\bhan\b", r"\bहाँ\b", r"\bहा\b"],
        "matlab": [r"\bmatlab\b", r"\bमतलब\b"],
        "toh": [r"\btoh\b", r"\bतो\b"],
        "dekhiye": [r"\bdekhiye\b", r"\bदेखिये\b", r"\bदेखो\b"],
        "acha": [r"\bacha\b", r"\bachha\b", r"\bअच्छा\b"]
    }
    
    filler_counts = {}
    total_fillers = 0
    for filler, patterns in filler_patterns.items():
        count = 0
        for pattern in patterns:
            matches = re.findall(pattern, text_lower)
            count += len(matches)
        if count > 0:
            filler_counts[filler] = count
            total_fillers += count

    fillers_per_min = (total_fillers / duration) * 60.0
    
    fillers = {
        "total_count": total_fillers,
        "frequency": filler_counts,
        "fillers_per_minute": round(fillers_per_min, 1)
    }

    # 5. Repetition Analysis
    # 5.1 Word Repetitions
    repeated_words_list = []
    if len(flat_words_text) > 1:
        for i in range(len(flat_words_text) - 1):
            if flat_words_text[i].lower() == flat_words_text[i+1].lower():
                repeated_words_list.append(flat_words_text[i])
    repeated_words_count = len(repeated_words_list)

    # 5.2 Phrase Repetitions (2-4 consecutive words)
    repeated_phrases = []
    words_lower = [w.lower() for w in flat_words_text]
    for n in range(2, 5):  # 2-grams, 3-grams, 4-grams
        if len(words_lower) >= n * 2:
            for i in range(len(words_lower) - n * 2 + 1):
                phrase1 = words_lower[i : i+n]
                phrase2 = words_lower[i+n : i+2*n]
                if phrase1 == phrase2:
                    repeated_phrases.append(" ".join(phrase1))
    repeated_phrases_count = len(repeated_phrases)

    # 5.3 Sentence Repetitions
    repeated_sentences = []
    if len(sentences) > 1:
        for i in range(len(sentences) - 1):
            s1 = re.sub(r'\s+', ' ', sentences[i].lower().strip())
            s2 = re.sub(r'\s+', ' ', sentences[i+1].lower().strip())
            if s1 == s2 and s1:
                repeated_sentences.append(sentences[i])
    repeated_sentences_count = len(repeated_sentences)

    repetition_analysis = {
        "repeated_words_count": repeated_words_count,
        "repeated_words_examples": list(set(repeated_words_list))[:5],
        "repeated_phrases_count": repeated_phrases_count,
        "repeated_phrases_examples": list(set(repeated_phrases))[:5],
        "repeated_sentences_count": repeated_sentences_count,
        "repeated_sentences_examples": list(set(repeated_sentences))[:5],
        "total_repetition_count": repeated_words_count + repeated_phrases_count + repeated_sentences_count
    }

    # 6. Lexical Diversity
    words_cleaned = [w.lower() for w in flat_words_text if w]
    unique_words = set(words_cleaned)
    vocab_size = len(unique_words)
    ttr = vocab_size / len(words_cleaned) if words_cleaned else 0.0
    
    lexical_richness = "Low"
    if ttr > 0.65:
        lexical_richness = "High"
    elif ttr > 0.45:
        lexical_richness = "Medium"

    lexical_diversity = {
        "unique_words_count": vocab_size,
        "vocabulary_size": vocab_size,
        "type_token_ratio": round(ttr, 3),
        "lexical_richness": lexical_richness
    }

    # 7. Sentence Complexity
    variance = 0.0
    if len(sentence_lengths) > 1:
        mean = sum(sentence_lengths) / len(sentence_lengths)
        variance = sum((x - mean) ** 2 for x in sentence_lengths) / len(sentence_lengths)
    
    # Incomplete sentences: ending with hesitation ellipses or dangling relative markers
    incomplete_count = 0
    for s in sentences:
        if s.endswith("...") or s.endswith("..") or s.endswith("wo") or s.endswith("मतलब") or s.endswith("matlab"):
            incomplete_count += 1
            
    # Fragments: short sentences with < 3 words
    fragments = sum(1 for s in sentences if len(s.split()) < 3)

    sentence_complexity = {
        "avg_words_per_sentence": round(avg_sent_len, 1),
        "sentence_length_variance": round(variance, 2),
        "incomplete_sentences_count": incomplete_count,
        "fragment_count": fragments
    }

    # 8. Memory Indicators
    memory_patterns = [
        "याद नहीं", "याद नही", "भूल गया", "भूल गई", "भूल गए",
        "yaad nahi", "yaad nahi hai", "bhool gaya", "bhool gayi", "bhool gaye",
        "remember nahi", "can't remember", "cant remember", "don't recall", "dont recall",
        "i forgot", "forgot"
    ]
    detected_mem_phrases = []
    for pat in memory_patterns:
        # Check Devanagari or English boundary-friendly searches
        if re.search(rf"\b{pat}\b" if not pat.strip().startswith("याद") else pat, text_lower):
            detected_mem_phrases.append(pat)

    memory_indicator_count = len(detected_mem_phrases)
    mem_risk_score = min(10.0, memory_indicator_count * 3.33)

    memory_indicators = {
        "memory_indicator_count": memory_indicator_count,
        "detected_phrases": list(set(detected_mem_phrases)),
        "risk_score": round(mem_risk_score, 1)
    }

    # 9. Word Retrieval Difficulty (Hesitations on the word timeline or in text)
    hesitation_words = {"wo", "voh", "वह", "वो", "मतलब", "matlab", "jo", "जो", "haan", "हाँ", "हा"}
    hesitations = []
    if len(words_list) > 1:
        for i in range(len(words_list) - 1):
            w = words_list[i]
            gap = words_list[i+1]["start"] - w["end"]
            if w["word"].lower() in hesitation_words and gap > 1.0:
                hesitations.append({
                    "word": w["word"],
                    "start": round(w["start"], 2),
                    "pause_duration": round(gap, 2)
                })
                
    # Also find ellipses matching hesitations in text
    ellipses_matches = re.finditer(r"\b(wo|मतलब|matlab|jo|जो|haan|हाँ)\s*\.\.\.", text_lower)
    for m in ellipses_matches:
        start_char = m.start()
        approx_time = (start_char / len(text_clean)) * duration
        if not any(abs(h["start"] - approx_time) < 2.0 for h in hesitations):
            hesitations.append({
                "word": m.group(1),
                "start": round(approx_time, 2),
                "pause_duration": 1.2
            })

    word_retrieval_difficulty = {
        "hesitation_count": len(hesitations),
        "locations": hesitations
    }

    # 10. Self-Corrections
    correction_patterns = ["नहीं...", "नही...", "मेरा मतलब", "mera matlab", "actually"]
    corrections_found = []
    for pat in correction_patterns:
        count = len(re.findall(rf"\b{pat}\b" if not pat.endswith("...") else pat, text_lower))
        if count > 0:
            corrections_found.extend([pat] * count)

    self_corrections = {
        "correction_count": len(corrections_found),
        "examples": list(set(corrections_found))
    }

    # 11. Timeline Consistency Warnings
    timeline_warnings = []
    
    # Check for multiple conflicting days of the week
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
        timeline_warnings.append(f"Inconsistency: Multiple conflicting days of the week mentioned ({', '.join(days_found)}).")

    # Check for conflicting years
    years = re.findall(r'\b(19\d{2}|20\d{2})\b', text_clean)
    unique_years = list(set(years))
    if len(unique_years) > 1:
        timeline_warnings.append(f"Inconsistency: Multiple conflicting years mentioned ({', '.join(unique_years)}).")

    # Check for morning vs night current-time conflicts
    morning_context = ["आज सुबह", "अभी सुबह", "morning today", "morning now"]
    night_context = ["आज रात", "अभी रात", "night today", "night now"]
    if any(m in text_clean or m in text_lower for m in morning_context) and any(n in text_clean or n in text_lower for n in night_context):
        timeline_warnings.append("Inconsistency: Conflicting statements about current time of day (morning vs. night).")

    timeline_consistency = {
        "warnings": timeline_warnings
    }

    # 12. Negation Detection
    # Clinical dictionaries from NER to identify medical context
    medical_terms = [
        "पैरासिटामोल", "paracetamol", "मेटफॉर्मिन", "metformin", "एस्पिरिन", "aspirin", 
        "इबुप्रोफेन", "ibuprofen", "अमोक्सिसिलिन", "amoxicillin", "दवा", "दवाई", "गोली", 
        "कैप्सूल", "सिरप", "इंजेक्शन", "इंसुलिन", "मधुमेह", "डायबिटीज", "diabetes", 
        "उच्च रक्तचाप", "हाइपरटेंशन", "hypertension", "बीपी", "bp", "कैंसर", "cancer", 
        "बुखार", "fever", "दर्द", "pain", "खांसी", "cough", "उल्टी", "vomit", "सांस", "breath"
    ]
    negations = ["नहीं", "नही", "मत", "no", "not", "didn't", "didnt", "cannot", "cant", "can't", "never"]
    negated_statements = []
    for s in sentences:
        s_lower = s.lower()
        if any(neg in s_lower.split() or neg in s_lower for neg in negations):
            if any(term in s_lower for term in medical_terms):
                negated_statements.append(s)

    negation_detection = {
        "negated_medical_statements": negated_statements
    }

    # 13. Emotion Indicators
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
            matches_count += len(re.findall(rf"\b{kw}\b" if not kw.strip().startswith("असे") else kw, text_lower))
        if matches_count > 0:
            emotion_scores[emo] = matches_count * 0.4
            matched_any = True
            
    # Normalize scores
    if matched_any:
        emotion_scores["neutral"] = max(0.1, 1.0 - sum(v for k, v in emotion_scores.items() if k != "neutral"))
        total = sum(emotion_scores.values())
        for k in emotion_scores:
            emotion_scores[k] = round(emotion_scores[k] / total, 2)
            
    dominant_emo = max(emotion_scores, key=emotion_scores.get)
    emotion_indicators = {**emotion_scores, "dominant_emotion": dominant_emo.capitalize()}

    # 14. Clinical Summary (Screening Classifier)
    # 14.1 Memory Risk
    mem_risk = "Low"
    mem_reasons = []
    if memory_indicator_count >= 3:
        mem_risk = "High"
        mem_reasons.append(f"Multiple memory indicators ({memory_indicator_count}) detected")
    elif memory_indicator_count > 0 or timeline_warnings:
        mem_risk = "Medium"
        if memory_indicator_count > 0:
            mem_reasons.append(f"Memory indicators ({memory_indicator_count}) detected")
        if timeline_warnings:
            mem_reasons.append("Timeline discrepancies found")
    else:
        mem_reasons.append("No significant memory indications or inconsistencies found")

    # 14.2 Language Risk
    lang_risk = "Low"
    lang_reasons = []
    if ttr < 0.45 and (total_fillers >= 10 or repeated_words_count >= 5):
        lang_risk = "High"
        lang_reasons.append("Low vocabulary diversity combined with high filler/repetition count")
    elif ttr < 0.55 or total_fillers >= 5 or repeated_words_count >= 2:
        lang_risk = "Medium"
        if ttr < 0.55:
            lang_reasons.append("Moderate vocabulary diversity")
        if total_fillers >= 5:
            lang_reasons.append("Moderate filler count")
        if repeated_words_count >= 2:
            lang_reasons.append("Word/phrase repetitions detected")
    else:
        lang_reasons.append("Lexical variety and syntax flow within standard margins")

    # 14.3 Speech Risk
    speech_risk = "Low"
    speech_reasons = []
    if avg_pause > 1.8 or pause_ratio > 0.35 or long_pauses >= 3:
        speech_risk = "High"
        speech_reasons.append("Elevated pause times and silence ratios")
    elif avg_pause > 1.0 or pause_ratio > 0.18 or long_pauses >= 1:
        speech_risk = "Medium"
        if avg_pause > 1.0:
            speech_reasons.append("Moderate conversational pauses")
        if pause_ratio > 0.18:
            speech_reasons.append("Slightly elevated silence ratio")
        if long_pauses >= 1:
            speech_reasons.append("Long pauses (>2.0s) detected")
    else:
        speech_reasons.append("Speech rate and conversational pauses within normal bounds")

    # 14.4 Overall Cognitive Risk
    risk_levels = [mem_risk, lang_risk, speech_risk]
    overall_risk = "Low"
    if risk_levels.count("High") >= 2 or mem_risk == "High":
        overall_risk = "High"
    elif "High" in risk_levels or "Medium" in risk_levels:
        overall_risk = "Medium"

    # Compile Explanation
    explanation_parts = []
    explanation_parts.append(f"Memory Assessment: {mem_risk} ({', '.join(mem_reasons)}).")
    explanation_parts.append(f"Language Flow: {lang_risk} ({', '.join(lang_reasons)}).")
    explanation_parts.append(f"Speech Rhythm: {speech_risk} ({', '.join(speech_reasons)}).")
    explanation_summary = " ".join(explanation_parts)

    clinical_summary = {
        "memory_risk": mem_risk,
        "language_risk": lang_risk,
        "speech_risk": speech_risk,
        "overall_cognitive_risk": overall_risk,
        "explanation": explanation_summary,
        "disclaimer": "This is an AI-generated cognitive screening summary for research/reference only. It does not constitute a clinical diagnosis of dementia or other neurological conditions. Please consult a qualified clinical specialist for professional evaluations."
    }

    return {
        "speech_metrics": speech_metrics,
        "pause_metrics": pause_metrics,
        "fillers": fillers,
        "repetition_analysis": repetition_analysis,
        "lexical_diversity": lexical_diversity,
        "sentence_complexity": sentence_complexity,
        "memory_indicators": memory_indicators,
        "word_retrieval_difficulty": word_retrieval_difficulty,
        "self_corrections": self_corrections,
        "timeline_consistency": timeline_consistency,
        "negation_detection": negation_detection,
        "emotion_indicators": emotion_indicators,
        "clinical_summary": clinical_summary
    }
