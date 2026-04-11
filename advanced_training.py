"""
Advanced Training Module for Invoice Data Extractor.

Implements ML-based pattern learning from annotated invoices,
continuous improvement through feedback loops, and model persistence.
"""

import os
import json
import pickle
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict

import numpy as np
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class PatternLearner:
    """Learns and adapts extraction patterns from annotated data."""

    def __init__(self, model_dir: str = "models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

        self.pattern_weights: Dict[str, Dict] = {}
        self.field_statistics: Dict[str, Dict] = defaultdict(
            lambda: {"total": 0, "correct": 0, "patterns_used": defaultdict(int)}
        )

        self._load_models()

    def _load_models(self):
        weights_file = self.model_dir / "pattern_weights.pkl"
        stats_file = self.model_dir / "field_statistics.pkl"

        if weights_file.exists():
            try:
                with open(weights_file, "rb") as f:
                    self.pattern_weights = pickle.load(f)
                logger.info(f"Loaded pattern weights from {weights_file}")
            except Exception as e:
                logger.warning(f"Failed to load pattern weights: {e}")

        if stats_file.exists():
            try:
                with open(stats_file, "rb") as f:
                    self.field_statistics = pickle.load(f)
                logger.info(f"Loaded field statistics from {stats_file}")
            except Exception as e:
                logger.warning(f"Failed to load field statistics: {e}")

    def save_models(self):
        weights_file = self.model_dir / "pattern_weights.pkl"
        stats_file = self.model_dir / "field_statistics.pkl"

        try:
            with open(weights_file, "wb") as f:
                pickle.dump(self.pattern_weights, f)
            with open(stats_file, "wb") as f:
                pickle.dump(dict(self.field_statistics), f)
            logger.info("Saved models successfully")
        except Exception as e:
            logger.error(f"Failed to save models: {e}")

    def train_on_sample(
        self,
        ocr_text: str,
        ground_truth: Dict[str, str],
        extracted: Dict[str, str],
        field_name: str,
        pattern_index: int,
    ):
        """Train on a single annotated sample."""
        expected = ground_truth.get(field_name, "")
        actual = extracted.get(field_name, "")

        self.field_statistics[field_name]["total"] += 1

        if self._calculate_similarity(expected, actual) > 0.9:
            self.field_statistics[field_name]["correct"] += 1
            self.pattern_weights.setdefault(field_name, {}).setdefault(
                pattern_index, 1.0
            )
            self.pattern_weights[field_name][pattern_index] *= 1.05
            self.field_statistics[field_name]["patterns_used"][pattern_index] += 1
        else:
            self.pattern_weights.setdefault(field_name, {}).setdefault(
                pattern_index, 1.0
            )
            self.pattern_weights[field_name][pattern_index] *= 0.95

        logger.debug(
            f"Trained on {field_name}: expected={expected}, actual={actual}, "
            f"pattern_idx={pattern_index}, weight={self.pattern_weights[field_name].get(pattern_index, 1.0):.3f}"
        )

    def get_ranked_patterns(
        self, field_name: str, patterns: List[str]
    ) -> List[Tuple[int, str, float]]:
        """Return patterns ranked by their learned weights."""
        weights = self.pattern_weights.get(field_name, {})

        ranked = []
        for idx, pattern in enumerate(patterns):
            weight = weights.get(idx, 1.0)
            ranked.append((idx, pattern, weight))

        ranked.sort(key=lambda x: x[2], reverse=True)
        return ranked

    def get_field_accuracy(self, field_name: str) -> float:
        """Get accuracy for a specific field."""
        stats = self.field_statistics.get(field_name, {})
        total = stats.get("total", 0)
        correct = stats.get("correct", 0)
        return correct / total if total > 0 else 0.0

    def get_overall_accuracy(self) -> float:
        """Get overall accuracy across all fields."""
        total = sum(s["total"] for s in self.field_statistics.values())
        correct = sum(s["correct"] for s in self.field_statistics.values())
        return correct / total if total > 0 else 0.0

    def get_learning_report(self) -> Dict:
        """Generate a comprehensive learning report."""
        report = {"fields": {}, "overall_accuracy": self.get_overall_accuracy()}

        for field_name, stats in self.field_statistics.items():
            total = stats["total"]
            correct = stats["correct"]
            accuracy = correct / total if total > 0 else 0.0

            top_patterns = sorted(
                stats["patterns_used"].items(), key=lambda x: x[1], reverse=True
            )[:5]

            report["fields"][field_name] = {
                "accuracy": round(accuracy, 3),
                "total_samples": total,
                "correct_predictions": correct,
                "top_patterns": top_patterns,
            }

        return report

    @staticmethod
    def _calculate_similarity(s1: str, s2: str) -> float:
        """Calculate string similarity (Levenshtein-based)."""
        if not s1 and not s2:
            return 1.0
        if not s1 or not s2:
            return 0.0

        s1, s2 = s1.lower().strip(), s2.lower().strip()

        if s1 == s2:
            return 1.0

        if s1 in s2 or s2 in s1:
            return 0.8

        max_len = max(len(s1), len(s2))
        if max_len == 0:
            return 0.0

        distance = PatternLearner._levenshtein_distance(s1, s2)
        return 1.0 - (distance / max_len)

    @staticmethod
    def _levenshtein_distance(s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return PatternLearner._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        prev_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            curr_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = prev_row[j + 1] + 1
                deletions = curr_row[j] + 1
                substitutions = prev_row[j] + (c1 != c2)
                curr_row.append(min(insertions, deletions, substitutions))
            prev_row = curr_row

        return prev_row[-1]


class AnnotationStore:
    """Stores annotated invoices for training and evaluation."""

    def __init__(self, annotations_file: str = "annotations.json"):
        self.annotations_file = Path(annotations_file)
        self.annotations: Dict[str, Dict] = {}
        self._load_annotations()

    def _load_annotations(self):
        if self.annotations_file.exists():
            try:
                with open(self.annotations_file, "r", encoding="utf-8") as f:
                    self.annotations = json.load(f)
                logger.info(
                    f"Loaded {len(self.annotations)} annotations from {self.annotations_file}"
                )
            except Exception as e:
                logger.warning(f"Failed to load annotations: {e}")
                self.annotations = {}

    def save_annotations(self):
        try:
            with open(self.annotations_file, "w", encoding="utf-8") as f:
                json.dump(self.annotations, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(self.annotations)} annotations")
        except Exception as e:
            logger.error(f"Failed to save annotations: {e}")

    def add_annotation(
        self,
        file_name: str,
        ocr_text: str,
        extracted_fields: Dict[str, str],
        corrected_fields: Dict[str, str],
        metadata: Optional[Dict] = None,
    ):
        """Add or update an annotation."""
        self.annotations[file_name] = {
            "file_name": file_name,
            "ocr_text": ocr_text,
            "extracted_fields": extracted_fields,
            "corrected_fields": corrected_fields,
            "metadata": metadata or {},
            "annotated_at": datetime.now().isoformat(),
        }
        self.save_annotations()

    def get_annotation(self, file_name: str) -> Optional[Dict]:
        """Get annotation for a specific file."""
        return self.annotations.get(file_name)

    def get_all_annotations(self) -> List[Dict]:
        """Get all annotations."""
        return list(self.annotations.values())

    def get_training_data(
        self, field_name: str
    ) -> List[Tuple[str, str, str, int, float]]:
        """Get training data for a specific field.

        Returns: List of (ocr_text, expected_value, extracted_value, pattern_idx, score)
        """
        training_data = []

        for annotation in self.annotations.values():
            corrected = annotation.get("corrected_fields", {})
            extracted = annotation.get("extracted_fields", {})

            if field_name in corrected:
                expected = corrected[field_name]
                actual = extracted.get(field_name, "Not Found")
                ocr_text = annotation.get("ocr_text", "")
                training_data.append((ocr_text, expected, actual, 0, 1.0))

        return training_data

    def remove_annotation(self, file_name: str):
        """Remove an annotation."""
        if file_name in self.annotations:
            del self.annotations[file_name]
            self.save_annotations()

    def get_annotation_stats(self) -> Dict:
        """Get statistics about annotations."""
        if not self.annotations:
            return {"total": 0}

        return {
            "total": len(self.annotations),
            "fields_covered": list(
                set().union(
                    *[
                        set(a.get("corrected_fields", {}).keys())
                        for a in self.annotations.values()
                    ]
                )
            ),
            "latest_annotation": max(
                a.get("annotated_at", "") for a in self.annotations.values()
            ),
        }


class ContinuousLearner:
    """Combines pattern learning with annotation store for continuous improvement."""

    def __init__(
        self,
        model_dir: str = "models",
        annotations_file: str = "annotations.json",
    ):
        self.pattern_learner = PatternLearner(model_dir)
        self.annotation_store = AnnotationStore(annotations_file)

    def learn_from_annotation(self, file_name: str):
        """Learn from a single annotation."""
        annotation = self.annotation_store.get_annotation(file_name)
        if not annotation:
            return

        corrected = annotation.get("corrected_fields", {})
        extracted = annotation.get("extracted_fields", {})
        ocr_text = annotation.get("ocr_text", "")

        for field_name, expected_value in corrected.items():
            actual_value = extracted.get(field_name, "Not Found")
            self.pattern_learner.train_on_sample(
                ocr_text, {field_name: expected_value}, extracted, field_name, 0
            )

        self.pattern_learner.save_models()

    def learn_from_all_annotations(self):
        """Learn from all stored annotations."""
        annotations = self.annotation_store.get_all_annotations()
        logger.info(f"Learning from {len(annotations)} annotations...")

        for annotation in annotations:
            file_name = annotation.get("file_name", "")
            self.learn_from_annotation(file_name)

        report = self.pattern_learner.get_learning_report()
        logger.info(f"Overall accuracy: {report['overall_accuracy']:.3f}")
        return report

    def get_improved_patterns(
        self, field_name: str, patterns: List[str]
    ) -> List[Tuple[int, str, float]]:
        """Get patterns ranked by learned weights."""
        return self.pattern_learner.get_ranked_patterns(field_name, patterns)

    def get_learning_dashboard(self) -> Dict:
        """Get comprehensive learning dashboard data."""
        report = self.pattern_learner.get_learning_report()
        annotation_stats = self.annotation_store.get_annotation_stats()

        return {
            "learning": report,
            "annotations": annotation_stats,
            "recommendations": self._generate_recommendations(report),
        }

    def _generate_recommendations(self, report: Dict) -> List[str]:
        """Generate recommendations for improvement."""
        recommendations = []

        for field_name, field_data in report.get("fields", {}).items():
            accuracy = field_data.get("accuracy", 0)
            total_samples = field_data.get("total_samples", 0)

            if accuracy < 0.7 and total_samples < 10:
                recommendations.append(
                    f"📊 {field_name}: Add more training samples (currently {total_samples}, accuracy {accuracy:.0%})"
                )
            elif accuracy < 0.7:
                recommendations.append(
                    f"⚠️ {field_name}: Low accuracy ({accuracy:.0%}). Consider improving regex patterns."
                )

        if report.get("overall_accuracy", 0) < 0.8:
            recommendations.append(
                "🎯 Overall accuracy is below 80%. Consider adding more diverse training data."
            )

        if not recommendations:
            recommendations.append("✅ System is performing well. Keep adding annotations to improve.")

        return recommendations
