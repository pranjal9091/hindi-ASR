import unittest
import sys
import os
import math

# Allow importing from src
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.feature_fusion import build_feature_vector
from src.model_adapter import predict_dementia

class TestFeatureFusion(unittest.TestCase):
    def setUp(self):
        # Sample mock data mirroring complete outputs
        self.mock_speech_analytics = {
            "speech_metrics": {
                "total_words": 150,
                "total_sentences": 12,
                "speech_duration": 45.0,
                "words_per_minute": 200.0,
                "chars_per_second": 12.5
            },
            "speech_fluency": {
                "speech_rate": 200.0,
                "articulation_rate": 220.0
            },
            "lexical_features": {
                "type_token_ratio": 0.65,
                "moving_average_ttr": 0.58,
                "vocabulary_size": 98
            },
            "fillers": {
                "fillers_per_minute": 2.5,
                "total_count": 2
            },
            "repetition_analysis": {
                "total_repetition_count": 5,
                "repeated_phrases_count": 1
            },
            "repetitions": {
                "perseveration_score": 0.033
            },
            "word_retrieval_difficulty": {
                "hesitation_count": 3
            },
            "pause_metrics": {
                "pause_ratio": 0.15,
                "average_pause_duration": 0.65,
                "maximum_pause_duration": 1.5,
                "long_pauses_count": 1
            },
            "executive_function": {
                "timeline_inconsistencies": ["Conflict 1"]
            },
            "memory_indicators": {
                "memory_loss_phrases_count": 2,
                "uncertainty_phrases_count": 3
            },
            "sentence_complexity": {
                "fragment_count": 2
            }
        }

        self.mock_acoustic_biomarkers = {
            "pitch": {"mean_pitch": 180.5, "median_pitch": 182.0, "std_pitch": 15.0, "min_pitch": 140.0, "max_pitch": 210.0},
            "energy": {"rms_mean": 0.045, "rms_std": 0.012, "peak_energy": 0.35},
            "speech_duration": {
                "total_audio_duration": 45.0,
                "estimated_speech_duration": 38.0,
                "silence_duration": 7.0,
                "silence_ratio": 0.156
            },
            "mfcc": {
                f"mfcc_{i}": {"mean": float(i * 1.5), "std": float(i * 0.25)} for i in range(1, 14)
            },
            "spectral": {
                "spectral_centroid": {"mean": 1200.0, "std": 150.0},
                "spectral_bandwidth": {"mean": 1400.0, "std": 120.0},
                "spectral_rolloff": {"mean": 2400.0, "std": 300.0},
                "zero_crossing_rate": {"mean": 0.085, "std": 0.012}
            },
            "prosody": {
                "voiced_ratio": 0.84,
                "pitch_variability": 0.083,
                "energy_variability": 0.267
            },
            "stability": {
                "articulation_consistency": 0.982,
                "pause_energy_variance": 0.00014
            }
        }

        self.mock_metadata = {
            "session_id": "4a713832-ec2e-4316-a7aa-a138322cf086",
            "timestamp": 1783490249.0,
            "language": "hi",
            "audio_duration": 45.0
        }

    def test_schema_consistency(self):
        result = build_feature_vector(
            "dummy transcript text",
            self.mock_speech_analytics,
            self.mock_acoustic_biomarkers,
            self.mock_metadata
        )
        
        self.assertIn("features", result)
        features = result["features"]
        
        # Verify specific key categories
        self.assertIn("transcript_total_words", features)
        self.assertIn("transcript_mattr", features)
        self.assertIn("acoustic_pitch_mean", features)
        self.assertIn("acoustic_mfcc_1_mean", features)
        self.assertIn("acoustic_mfcc_13_std", features)
        self.assertIn("meta_language", features)
        self.assertIn("meta_session_id", features)
        
        # Total feature count check: should be consistent at 77 parameters
        self.assertEqual(len(features), 77)

    def test_numeric_only_and_no_nan(self):
        # Pass containing NaNs and Nones to make sure they're cleaned
        bad_speech_analytics = {
            "speech_metrics": {"total_words": None, "total_sentences": float('nan')},
            "lexical_features": {"type_token_ratio": "not a number"}
        }
        
        result = build_feature_vector(
            None,
            bad_speech_analytics,
            None,
            None
        )
        
        features = result["features"]
        for key, val in features.items():
            # Assert type is strictly numeric (int or float)
            self.assertTrue(isinstance(val, (int, float)), f"Key {key} has non-numeric type {type(val)}")
            # Assert no nan
            self.assertFalse(math.isnan(val), f"Key {key} is NaN")
            # Assert no inf
            self.assertFalse(math.isinf(val), f"Key {key} is Inf")

    def test_missing_values_replaced_with_zero(self):
        # Empty dictionaries
        result = build_feature_vector("", {}, {}, {})
        features = result["features"]
        
        # Check specific values defaulted to 0.0
        self.assertEqual(features["transcript_total_words"], 0.0)
        self.assertEqual(features["acoustic_pitch_mean"], 0.0)
        self.assertEqual(features["acoustic_mfcc_1_mean"], 0.0)
        self.assertEqual(features["meta_session_id"], 0.0)
        
        # Check replacements count is greater than 0
        self.assertGreater(result["_missing_replacements_count"], 0)

    def test_deterministic_output(self):
        res1 = build_feature_vector("test", self.mock_speech_analytics, self.mock_acoustic_biomarkers, self.mock_metadata)
        res2 = build_feature_vector("test", self.mock_speech_analytics, self.mock_acoustic_biomarkers, self.mock_metadata)
        self.assertEqual(res1["features"], res2["features"])

    def test_model_adapter_placeholder(self):
        # Adapter prediction must accept feature vector and yield null fields
        features = build_feature_vector("test", {}, {}, {})["features"]
        prediction = predict_dementia(features)
        
        self.assertIn("language", prediction)
        self.assertIn("fluency", prediction)
        self.assertIn("overall", prediction)
        self.assertIsNone(prediction["overall"])
        self.assertIsNone(prediction["memory"])

if __name__ == "__main__":
    unittest.main()
