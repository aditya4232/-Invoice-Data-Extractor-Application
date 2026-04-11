"""
Comprehensive Test Suite for Invoice Data Extractor Pro.

Run with: pytest tests/ -v
"""

import os
import sys
import json
import pytest
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from extractor import FieldExtractor
from utils import DataCleaner, InvoiceProcessor
from advanced_training import PatternLearner, AnnotationStore, ContinuousLearner


# ==================== Field Extractor Tests ====================

class TestFieldExtractoror:
    """Test FieldExtractoror class."""

    @pytest.fixture
    def extractor(self):
        return FieldExtractor()

    def test_gstin_extraction(self, extractor):
        text = """
        GSTIN: 27AABCU9603R1ZM
        Invoice No: INV-001
        Date: 15/01/2024
        Total: ₹15,000.00
        """
        result = extractor.extract_gstin(text)
        assert result == "27AABCU9603R1ZM"

    def test_gstin_not_found(self, extractor):
        text = "This is just regular text with no GST"
        result = extractor.extract_gstin(text)
        assert result == "Not Found"

    def test_pan_extraction(self, extractor):
        text = """
        PAN: AABCU9603R
        GSTIN: 27AABCU9603R1ZM
        """
        result = extractor.extract_pan(text)
        assert result == "AABCU9603R"

    def test_pan_derived_from_gstin(self, extractor):
        text = "GSTIN: 27AABCU9603R1ZM"
        fields = extractor.extract_all_fields(text)
        # PAN should be derived from GSTIN
        assert fields["pan"] == "AABCU9603R"

    def test_amount_extraction(self, extractor):
        text = """
        Total Amount: ₹15,000.00
        Grand Total: INR 15,000.00
        """
        result = extractor.extract_total_amount(text)
        assert "15000" in result.replace(",", "")

    def test_date_extraction(self, extractor):
        text = """
        Invoice Date: 15/01/2024
        Due Date: 14/02/2024
        """
        result = extractor.extract_invoice_date(text)
        assert "2024" in result
        assert "01" in result or "15" in result

    def test_empty_text(self, extractor):
        result = extractor.extract_all_fields("")
        assert result["vendor_name"] == "Not Found"
        assert result["gstin"] == "Not Found"
        assert result["total_amount"] == "Not Found"

    def test_all_fields_return_confidence(self, extractor):
        text = """
        GSTIN: 27AABCU9603R1ZM
        Invoice No: INV-001
        Date: 15/01/2024
        Total: ₹15,000.00
        """
        result = extractor.extract_all_fields(text)
        assert "_confidence_details" in result
        assert "gstin" in result["_confidence_details"]
        assert "confidence" in result["_confidence_details"]["gstin"]


# ==================== Data Cleaner Tests ====================

class TestDataCleaner:
    """Test DataCleaner class."""

    @pytest.fixture
    def cleaner(self):
        return DataCleaner()

    def test_gstin_validation(self, cleaner):
        assert cleaner.validate_gstin("27AABCU9603R1ZM") == True
        assert cleaner.validate_gstin("INVALID") == False
        assert cleaner.validate_gstin("Not Found") == False

    def test_pan_validation(self, cleaner):
        assert cleaner.validate_pan("AABCU9603R") == True
        assert cleaner.validate_pan("INVALID") == False
        assert cleaner.validate_pan("Not Found") == False

    def test_clean_amount(self, cleaner):
        assert cleaner.clean_field("total_amount", "₹15,000.00") == "15000.0"
        assert cleaner.clean_field("total_amount", "INR 10000") == "10000.0"

    def test_clean_gstin(self, cleaner):
        result = cleaner.clean_field("gstin", " 27aabcu9603r1zm ")
        assert result == "27AABCU9603R1ZM"

    def test_clean_date(self, cleaner):
        result = cleaner.clean_field("invoice_date", "15/01/2024")
        assert "2024" in result

    def test_clean_vendor_name(self, cleaner):
        result = cleaner.clean_field("vendor_name", "  Sample Tech Pvt Ltd  ")
        assert result == "Sample Tech Pvt Ltd"


# ==================== Pattern Learner Tests ====================

class TestPatternLearner:
    """Test PatternLearner class."""

    @pytest.fixture
    def learner(self, tmp_path):
        return PatternLearner(model_dir=str(tmp_path))

    def test_initial_accuracy(self, learner):
        # Initial accuracy should be 0.0 with no training
        assert learner.get_overall_accuracy() == 0.0

    def test_train_on_sample(self, learner):
        learner.train_on_sample(
            ocr_text="GSTIN: 27AABCU9603R1ZM",
            ground_truth={"gstin": "27AABCU9603R1ZM"},
            extracted={"gstin": "27AABCU9603R1ZM"},
            field_name="gstin",
            pattern_index=0
        )
        # Accuracy should be 1.0 after one correct sample
        assert learner.get_field_accuracy("gstin") == 1.0

    def test_pattern_weights_update(self, learner):
        # Train with correct sample
        learner.train_on_sample(
            ocr_text="GSTIN: 27AABCU9603R1ZM",
            ground_truth={"gstin": "27AABCU9603R1ZM"},
            extracted={"gstin": "27AABCU9603R1ZM"},
            field_name="gstin",
            pattern_index=0
        )
        weights = learner.pattern_weights.get("gstin", {})
        assert 0 in weights
        assert weights[0] > 1.0  # Should increase for correct predictions

    def test_get_ranked_patterns(self, learner):
        patterns = ["pattern1", "pattern2", "pattern3"]
        ranked = learner.get_ranked_patterns("gstin", patterns)
        assert len(ranked) == 3
        # All should have default weight of 1.0
        assert all(r[2] == 1.0 for r in ranked)

    def test_save_and_load_models(self, learner, tmp_path):
        learner.train_on_sample(
            ocr_text="Test",
            ground_truth={"gstin": "27AABCU9603R1ZM"},
            extracted={"gstin": "27AABCU9603R1ZM"},
            field_name="gstin",
            pattern_index=0
        )
        learner.save_models()

        # Load in new instance
        new_learner = PatternLearner(model_dir=str(tmp_path))
        assert new_learner.get_field_accuracy("gstin") == 1.0


# ==================== Annotation Store Tests ====================

class TestAnnotationStore:
    """Test AnnotationStore class."""

    @pytest.fixture
    def store(self, tmp_path):
        return AnnotationStore(annotations_file=str(tmp_path / "test_annotations.json"))

    def test_add_annotation(self, store):
        store.add_annotation(
            file_name="test_invoice.pdf",
            ocr_text="Sample OCR text",
            extracted_fields={"gstin": "27AABCU9603R1ZM"},
            corrected_fields={"gstin": "27AABCU9603R1ZM"}
        )
        assert store.get_annotation("test_invoice.pdf") is not None

    def test_get_all_annotations(self, store):
        store.add_annotation(
            file_name="invoice1.pdf",
            ocr_text="OCR1",
            extracted_fields={},
            corrected_fields={}
        )
        store.add_annotation(
            file_name="invoice2.pdf",
            ocr_text="OCR2",
            extracted_fields={},
            corrected_fields={}
        )
        assert len(store.get_all_annotations()) == 2

    def test_remove_annotation(self, store):
        store.add_annotation(
            file_name="test.pdf",
            ocr_text="OCR",
            extracted_fields={},
            corrected_fields={}
        )
        store.remove_annotation("test.pdf")
        assert store.get_annotation("test.pdf") is None

    def test_save_and_load(self, store, tmp_path):
        store.add_annotation(
            file_name="test.pdf",
            ocr_text="OCR text",
            extracted_fields={"gstin": "27AABCU9603R1ZM"},
            corrected_fields={"gstin": "27AABCU9603R1ZM"}
        )

        # Load in new instance
        new_store = AnnotationStore(annotations_file=str(tmp_path / "test_annotations.json"))
        assert len(new_store.get_all_annotations()) == 1


# ==================== Continuous Learner Tests ====================

class TestContinuousLearner:
    """Test ContinuousLearner class."""

    @pytest.fixture
    def learner(self, tmp_path):
        return ContinuousLearner(
            model_dir=str(tmp_path / "models"),
            annotations_file=str(tmp_path / "annotations.json")
        )

    def test_learn_from_annotation(self, learner):
        learner.annotation_store.add_annotation(
            file_name="test.pdf",
            ocr_text="GSTIN: 27AABCU9603R1ZM",
            extracted_fields={"gstin": "27AABCU9603R1ZM"},
            corrected_fields={"gstin": "27AABCU9603R1ZM"}
        )
        learner.learn_from_annotation("test.pdf")
        # Pattern learner should have learned from this
        assert learner.pattern_learner.get_field_accuracy("gstin") == 1.0

    def test_learning_dashboard(self, learner):
        # Add some annotations
        learner.annotation_store.add_annotation(
            file_name="test1.pdf",
            ocr_text="OCR1",
            extracted_fields={"gstin": "27AABCU9603R1ZM"},
            corrected_fields={"gstin": "27AABCU9603R1ZM"}
        )

        dashboard = learner.get_learning_dashboard()
        assert "learning" in dashboard
        assert "annotations" in dashboard
        assert "recommendations" in dashboard


# ==================== Integration Tests ====================

class TestIntegration:
    """Integration tests for the full pipeline."""

    def test_invoice_processor_initialization(self):
        processor = InvoiceProcessor(enable_learning=False)
        assert processor.ocr is not None
        assert processor.extractor is not None
        assert processor.cleaner is not None

    def test_process_invoice_with_learning(self, tmp_path):
        processor = InvoiceProcessor(enable_learning=True)
        # Should initialize without errors
        assert processor.learner is not None


# ==================== Confidence Scoring Tests ====================

class TestConfidenceScoring:
    """Test confidence scoring functionality."""

    @pytest.fixture
    def extractor(self):
        return FieldExtractor()

    def test_high_confidence_gstin(self, extractor):
        text = "GSTIN: 27AABCU9603R1ZM"
        fields = extractor.extract_all_fields(text)
        gstin_conf = fields["_confidence_details"]["gstin"]["confidence"]
        assert gstin_conf >= 80.0  # Should be high for valid GSTIN

    def test_low_confidence_missing_field(self, extractor):
        text = "Just random text without any invoice data"
        fields = extractor.extract_all_fields(text)
        gstin_conf = fields["_confidence_details"]["gstin"]["confidence"]
        assert gstin_conf == 0.0  # Should be 0 for not found

    def test_confidence_details_structure(self, extractor):
        text = "GSTIN: 27AABCU9603R1ZM\nInvoice: INV-001"
        fields = extractor.extract_all_fields(text)

        for field_name in ["gstin", "invoice_number", "vendor_name"]:
            assert field_name in fields["_confidence_details"]
            details = fields["_confidence_details"][field_name]
            assert "confidence" in details
            assert "pattern_index" in details
            assert "pattern_preview" in details


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
