import unittest
import sys
import os

# Allow importing from src
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.clinical_speech_analytics import analyze_clinical_speech

class TestClinicalSpeechAnalytics(unittest.TestCase):
    def setUp(self):
        # Base setup
        self.mock_normal_segments = [
            {
                "id": 0,
                "start": 0.0,
                "end": 3.0,
                "text": "मरीज बिल्कुल ठीक है। उसे कोई बीमारी नहीं है।",
                "words": [
                    {"word": "मरीज", "start": 0.0, "end": 0.5, "probability": 0.99},
                    {"word": "बिल्कुल", "start": 0.6, "end": 1.2, "probability": 0.99},
                    {"word": "ठीक", "start": 1.3, "end": 1.8, "probability": 0.99},
                    {"word": "है", "start": 1.9, "end": 2.2, "probability": 0.99},
                    {"word": "उसे", "start": 2.3, "end": 2.5, "probability": 0.99},
                    {"word": "कोई", "start": 2.6, "end": 2.8, "probability": 0.99},
                    {"word": "बीमारी", "start": 2.9, "end": 3.0, "probability": 0.99}
                ]
            }
        ]

    def test_normal_transcript(self):
        transcript = "मरीज बिल्कुल ठीक है। उसे कोई बीमारी नहीं है।"
        result = analyze_clinical_speech(transcript, self.mock_normal_segments)
        
        # Check presence of all outer metrics keys
        self.assertIn("speech_metrics", result)
        self.assertIn("pause_metrics", result)
        self.assertIn("fillers", result)
        self.assertIn("repetition_analysis", result)
        self.assertIn("lexical_diversity", result)
        self.assertIn("sentence_complexity", result)
        self.assertIn("memory_indicators", result)
        self.assertIn("clinical_summary", result)
        
        # Normal content expectations
        self.assertEqual(result["clinical_summary"]["overall_cognitive_risk"], "Low")
        self.assertEqual(result["memory_indicators"]["memory_indicator_count"], 0)
        self.assertEqual(result["fillers"]["total_count"], 0)

    def test_transcript_with_fillers(self):
        transcript = "मरीज को मतलब थोड़ा बुखार है और वो toh कल आएगा haan"
        mock_segments = [
            {
                "id": 0,
                "start": 0.0,
                "end": 5.0,
                "text": transcript,
                "words": [
                    {"word": "मरीज", "start": 0.0, "end": 0.5, "probability": 0.99},
                    {"word": "को", "start": 0.6, "end": 0.8, "probability": 0.99},
                    {"word": "मतलब", "start": 0.9, "end": 1.4, "probability": 0.99},
                    {"word": "थोड़ा", "start": 1.5, "end": 1.8, "probability": 0.99},
                    {"word": "बुखार", "start": 1.9, "end": 2.2, "probability": 0.99},
                    {"word": "है", "start": 2.3, "end": 2.5, "probability": 0.99},
                    {"word": "और", "start": 2.6, "end": 2.8, "probability": 0.99},
                    {"word": "वो", "start": 2.9, "end": 3.1, "probability": 0.99},
                    {"word": "toh", "start": 3.2, "end": 3.5, "probability": 0.99},
                    {"word": "कल", "start": 3.6, "end": 3.9, "probability": 0.99},
                    {"word": "आएगा", "start": 4.0, "end": 4.4, "probability": 0.99},
                    {"word": "haan", "start": 4.5, "end": 4.8, "probability": 0.99}
                ]
            }
        ]
        
        result = analyze_clinical_speech(transcript, mock_segments)
        self.assertGreater(result["fillers"]["total_count"], 0)
        self.assertIn("matlab", result["fillers"]["frequency"])
        self.assertIn("toh", result["fillers"]["frequency"])
        self.assertIn("haan", result["fillers"]["frequency"])

    def test_transcript_with_repetitions(self):
        # Simulating duplicate consecutive words, phrases and sentences
        transcript = "मुझे मुझे बहुत दर्द है। बहुत दर्द है। डॉक्टर साहब बहुत दर्द है।"
        mock_segments = [
            {
                "id": 0, "start": 0.0, "end": 4.0, "text": "मुझे मुझे बहुत दर्द है।",
                "words": [
                    {"word": "मुझे", "start": 0.0, "end": 0.4},
                    {"word": "मुझे", "start": 0.5, "end": 0.9},
                    {"word": "बहुत", "start": 1.0, "end": 1.4},
                    {"word": "दर्द", "start": 1.5, "end": 2.0},
                    {"word": "है", "start": 2.1, "end": 2.5}
                ]
            },
            {
                "id": 1, "start": 4.1, "end": 8.0, "text": "बहुत दर्द है। डॉक्टर साहब बहुत दर्द है।",
                "words": [
                    {"word": "बहुत", "start": 4.1, "end": 4.5},
                    {"word": "दर्द", "start": 4.6, "end": 5.0},
                    {"word": "है", "start": 5.1, "end": 5.5},
                    {"word": "डॉक्टर", "start": 5.6, "end": 6.1},
                    {"word": "साहब", "start": 6.2, "end": 6.7},
                    {"word": "बहुत", "start": 6.8, "end": 7.1},
                    {"word": "दर्द", "start": 7.2, "end": 7.6},
                    {"word": "है", "start": 7.7, "end": 8.0}
                ]
            }
        ]
        
        result = analyze_clinical_speech(transcript, mock_segments)
        # Check repeated words
        self.assertGreaterEqual(result["repetition_analysis"]["repeated_words_count"], 1)
        self.assertIn("मुझे", result["repetition_analysis"]["repeated_words_examples"])
        # Check repeated phrases ("बहुत दर्द है")
        self.assertGreaterEqual(result["repetition_analysis"]["repeated_phrases_count"], 1)

    def test_transcript_with_long_pauses(self):
        # We mock a timeline with word end and next word start gaps exceeding 2.0 seconds
        transcript = "दवाई लेनी थी पर याद नहीं।"
        mock_segments = [
            {
                "id": 0,
                "start": 0.0,
                "end": 6.0,
                "text": transcript,
                "words": [
                    {"word": "दवाई", "start": 0.0, "end": 0.5},
                    {"word": "लेनी", "start": 0.6, "end": 1.0},
                    {"word": "थी", "start": 1.1, "end": 1.5},
                    # Silence gap: 4.0 - 1.5 = 2.5s (long pause)
                    {"word": "पर", "start": 4.0, "end": 4.4},
                    {"word": "याद", "start": 4.5, "end": 5.0},
                    {"word": "नहीं", "start": 5.1, "end": 5.6}
                ]
            }
        ]
        
        result = analyze_clinical_speech(transcript, mock_segments)
        self.assertGreater(result["pause_metrics"]["total_pause_count"], 0)
        self.assertEqual(result["pause_metrics"]["long_pause_count"], 1)
        self.assertGreater(result["pause_metrics"]["pause_ratio"], 0.2)

    def test_transcript_containing_memory_loss_phrases(self):
        # Memory indication "yaad nahi" and "bhool gaya"
        transcript = "मुझे अपना फोन नंबर yaad nahi है, मैं उसे bhool gaya।"
        result = analyze_clinical_speech(transcript, [])
        
        self.assertEqual(result["memory_indicators"]["memory_indicator_count"], 2)
        self.assertIn("yaad nahi", result["memory_indicators"]["detected_phrases"])
        self.assertIn("bhool gaya", result["memory_indicators"]["detected_phrases"])
        self.assertGreater(result["memory_indicators"]["risk_score"], 5.0)

    def test_transcript_with_contradictory_timeline_references(self):
        # Conflicting days: Monday vs Wednesday. Conflicting years: 2020 vs 2024
        transcript = "मैंने सोमवार को दवाई ली थी। नहीं, बुधवार को ली थी 2020 में। शायद 2024 था।"
        result = analyze_clinical_speech(transcript, [])
        
        warnings = result["timeline_consistency"]["warnings"]
        self.assertTrue(any("Monday" in w and "Wednesday" in w for w in warnings))
        self.assertTrue(any("2020" in w and "2024" in w for w in warnings))

if __name__ == "__main__":
    unittest.main()
