"""
Comprehensive Test Suite for Invoice Data Extractor.

Run with: pytest tests/ -v
"""

import os
import sys
import json
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from extractor import FieldExtractor
from utils import DataCleaner, InvoiceProcessor
from advanced_training import PatternLearner, AnnotationStore, ContinuousLearner
from sample_data import SAMPLE_INVOICES


class TestFieldExtractor:
    """Test FieldExtractor class."""

    @pytest.fixture
    def extractor(self):
        return FieldExtractor()

    def test_gstin_extraction(self, extractor):
        text = "GSTIN: 27AABCU9603R1ZM\nInvoice No: INV-001"
        result = extractor.extract_gstin(text)
        assert result == "27AABCU9603R1ZM"

    def test_gstin_not_found(self, extractor):
        text = "This is just regular text with no GST"
        result = extractor.extract_gstin(text)
        assert result == "Not Found"

    def test_pan_extraction(self, extractor):
        text = "PAN: AABCU9603R\nGSTIN: 27AABCU9603R1ZM"
        result = extractor.extract_pan(text)
        assert result == "AABCU9603R"

    def test_pan_derived_from_gstin(self, extractor):
        text = "GSTIN: 27AABCU9603R1ZM"
        fields = extractor.extract_all_fields(text)
        assert fields["pan"] == "AABCU9603R"

    def test_invoice_number_extraction(self, extractor):
        text = "Invoice No: INV-2024-001\nDate: 15/01/2024"
        result = extractor.extract_invoice_number(text)
        assert "INV-2024-001" in result

    def test_date_extraction_dd_mm_yyyy(self, extractor):
        text = "Invoice Date: 15/01/2024\nDue Date: 14/02/2024"
        result = extractor.extract_invoice_date(text)
        assert "2024" in result

    def test_date_extraction_dd_mm_yyyy_inverted(self, extractor):
        text = "Date: 05-03-2024"
        result = extractor.extract_invoice_date(text)
        assert "2024" in result

    def test_date_extraction_text_month(self, extractor):
        text = "Invoice Date: 25 March 2024"
        result = extractor.extract_invoice_date(text)
        assert "2024" in result

    def test_empty_text(self, extractor):
        result = extractor.extract_all_fields("")
        assert result["vendor_name"] == "Not Found"
        assert result["gstin"] == "Not Found"
        assert result["total_amount"] == "Not Found"

    def test_all_fields_return_confidence(self, extractor):
        text = "GSTIN: 27AABCU9603R1ZM\nInvoice No: INV-001\nDate: 15/01/2024"
        result = extractor.extract_all_fields(text)
        assert "_confidence_details" in result
        assert "gstin" in result["_confidence_details"]
        assert "confidence" in result["_confidence_details"]["gstin"]

    def test_total_amount_rupee_symbol(self, extractor):
        text = "Grand Total: 14,750.00\nTotal Amount: 14,750.00"
        result = extractor.extract_total_amount(text)
        assert "14750" in result.replace(",", "")

    def test_total_amount_inr(self, extractor):
        text = "Amount Payable: INR 26,28,500.00"
        result = extractor.extract_total_amount(text)
        assert "2628500" in result.replace(",", "")

    def test_po_number_extraction(self, extractor):
        text = "PO Number: PO-12345\nInvoice No: INV-001"
        result = extractor.extract_po_number(text)
        assert "PO-12345" in result

    def test_vendor_name_extraction(self, extractor):
        text = "ABC Technologies Pvt Ltd\n123 Business Park\nGSTIN: 27AABCU9603R1ZM"
        result = extractor.extract_vendor_name(text)
        assert "ABC Technologies" in result

    def test_place_of_supply(self, extractor):
        text = "Place of Supply: Maharashtra\nGSTIN: 27AABCU9603R1ZM"
        result = extractor.extract_place_of_supply(text)
        assert "Maharashtra" in result

    def test_cgst_extraction(self, extractor):
        text = "CGST @ 9%: 1,125.00\nSGST @ 9%: 1,125.00"
        result = extractor.extract_cgst(text)
        assert result == "1,125.00"

    def test_sgst_extraction(self, extractor):
        text = "CGST @ 9%: 1,125.00\nSGST @ 9%: 1,125.00"
        result = extractor.extract_sgst(text)
        assert result == "1,125.00"

    def test_igst_extraction(self, extractor):
        text = "IGST @ 18%: 4,03,500.00"
        result = extractor.extract_igst(text)
        assert result == "4,03,500.00"

    def test_extract_all_amounts(self, extractor):
        text = (
            "Software ₹10,000.00 Support Rs.2,500.00 Tax INR 1,125.00 Total ₹14,750.00"
        )
        result = extractor.extract_all_amounts(text)
        assert len(result) >= 3

    def test_derive_pan_from_gstin_valid(self, extractor):
        result = extractor._derive_pan_from_gstin("27AABCU9603R1ZM")
        assert result == "AABCU9603R"

    def test_derive_pan_from_gstin_invalid(self, extractor):
        result = extractor._derive_pan_from_gstin("INVALID123")
        assert result == "Not Found"


class TestDataCleaner:
    """Test DataCleaner class."""

    @pytest.fixture
    def cleaner(self):
        return DataCleaner()

    def test_gstin_validation_valid(self, cleaner):
        assert cleaner.validate_gstin("27AABCU9603R1ZM") is True

    def test_gstin_validation_invalid(self, cleaner):
        assert cleaner.validate_gstin("INVALID") is False
        assert cleaner.validate_gstin("Not Found") is False
        assert cleaner.validate_gstin("") is False

    def test_pan_validation_valid(self, cleaner):
        assert cleaner.validate_pan("AABCU9603R") is True

    def test_pan_validation_invalid(self, cleaner):
        assert cleaner.validate_pan("INVALID") is False
        assert cleaner.validate_pan("Not Found") is False

    def test_clean_amount_rupee(self, cleaner):
        assert cleaner.clean_field("total_amount", "₹15,000.00") == "15000.0"

    def test_clean_amount_inr(self, cleaner):
        assert cleaner.clean_field("total_amount", "INR 10000") == "10000.0"

    def test_clean_amount_float(self, cleaner):
        assert cleaner.clean_field("total_amount", 15000.0) == "15000.0"

    def test_clean_gstin_uppercase(self, cleaner):
        result = cleaner.clean_field("gstin", " 27aabcu9603r1zm ")
        assert result == "27AABCU9603R1ZM"

    def test_clean_date_standard(self, cleaner):
        result = cleaner.clean_field("invoice_date", "15/01/2024")
        assert "2024" in result

    def test_clean_date_text_month(self, cleaner):
        result = cleaner.clean_field("invoice_date", "25th March 2024")
        assert "2024" in result

    def test_clean_vendor_name(self, cleaner):
        result = cleaner.clean_field("vendor_name", "  ABC Technologies Pvt Ltd.  \n")
        assert result == "ABC Technologies Pvt Ltd"

    def test_clean_invoice_number(self, cleaner):
        result = cleaner.clean_field("invoice_number", " INV-2024-001 ")
        assert "INV-2024-001" in result

    def test_clean_po_number(self, cleaner):
        result = cleaner.clean_field("po_number", " PO-12345 ")
        assert "PO-12345" in result

    def test_clean_field_not_found(self, cleaner):
        result = cleaner.clean_field("gstin", "Not Found")
        assert result == "Not Found"

    def test_clean_field_none(self, cleaner):
        result = cleaner.clean_field("gstin", None)
        assert result is None

    def test_clean_all(self, cleaner):
        fields = {
            "vendor_name": "  ABC Tech  ",
            "total_amount": "₹10,000",
            "gstin": " 27aabcu9603r1zm ",
        }
        result = cleaner.clean_all(fields)
        assert result["vendor_name"] == "ABC Tech"
        assert result["total_amount"] == "10000.0"
        assert result["gstin"] == "27AABCU9603R1ZM"


class TestSampleData:
    """Test extraction against realistic sample invoice data."""

    @pytest.fixture
    def extractor(self):
        return FieldExtractor()

    def test_indian_gst_invoice_001(self, extractor):
        text = SAMPLE_INVOICES["indian_gst_invoice_001"]
        fields = extractor.extract_all_fields(text)
        assert fields["gstin"] == "27AABCU9603R1ZM"
        assert fields["pan"] == "AABCU9603R"
        assert "ABC Technologies" in fields["vendor_name"]
        assert "INV-2024-001" in fields["invoice_number"]

    def test_indian_gst_invoice_002(self, extractor):
        text = SAMPLE_INVOICES["indian_gst_invoice_002"]
        fields = extractor.extract_all_fields(text)
        assert fields["gstin"] == "27AABCR5678P1Z3"
        assert fields["pan"] == "AABCR5678P"
        assert "Reliance Retail" in fields["vendor_name"]

    def test_indian_gst_invoice_003(self, extractor):
        text = SAMPLE_INVOICES["indian_gst_invoice_003"]
        fields = extractor.extract_all_fields(text)
        assert fields["gstin"] == "29AABCW1234P1Z3"
        assert fields["pan"] == "AABCW1234P"
        assert "Wipro" in fields["vendor_name"]

    def test_international_invoice(self, extractor):
        text = SAMPLE_INVOICES["international_invoice_001"]
        fields = extractor.extract_all_fields(text)
        assert "invoice_number" in fields
        assert "INV" in fields["invoice_number"]

    def test_minimal_invoice(self, extractor):
        text = SAMPLE_INVOICES["minimal_invoice_001"]
        fields = extractor.extract_all_fields(text)
        assert fields["gstin"] == "06AABCF1234Q1Z8"

    def test_edge_case_no_gstin(self, extractor):
        text = SAMPLE_INVOICES["edge_case_no_gstin"]
        fields = extractor.extract_all_fields(text)
        assert fields["gstin"] == "Not Found"
        assert (
            "INV" in fields["invoice_number"] or "FREELANCE" in fields["invoice_number"]
        )

    def test_edge_case_multiple_amounts(self, extractor):
        text = SAMPLE_INVOICES["edge_case_multiple_amounts"]
        fields = extractor.extract_all_fields(text)
        assert fields["total_amount"] is not None
        assert fields["total_amount"] != "Not Found"

    def test_edge_case_igst_inter_state(self, extractor):
        text = SAMPLE_INVOICES["edge_case_igst_inter_state"]
        fields = extractor.extract_all_fields(text)
        assert fields["gstin"] == "33AABCS5678Q1Z5"
        assert "South India" in fields["vendor_name"]


class TestPatternLearner:
    """Test PatternLearner class."""

    @pytest.fixture
    def learner(self, tmp_path):
        return PatternLearner(model_dir=str(tmp_path))

    def test_initial_accuracy(self, learner):
        assert learner.get_overall_accuracy() == 0.0

    def test_train_on_sample_correct(self, learner):
        learner.train_on_sample(
            ocr_text="GSTIN: 27AABCU9603R1ZM",
            ground_truth={"gstin": "27AABCU9603R1ZM"},
            extracted={"gstin": "27AABCU9603R1ZM"},
            field_name="gstin",
            pattern_index=0,
        )
        assert learner.get_field_accuracy("gstin") == 1.0

    def test_train_on_sample_incorrect(self, learner):
        learner.train_on_sample(
            ocr_text="GSTIN: 27AABCU9603R1ZM",
            ground_truth={"gstin": "27AABCU9603R1ZM"},
            extracted={"gstin": "WRONGGSTIN"},
            field_name="gstin",
            pattern_index=0,
        )
        assert learner.get_field_accuracy("gstin") == 0.0

    def test_pattern_weights_increase_correct(self, learner):
        learner.train_on_sample(
            ocr_text="Test",
            ground_truth={"gstin": "27AABCU9603R1ZM"},
            extracted={"gstin": "27AABCU9603R1ZM"},
            field_name="gstin",
            pattern_index=0,
        )
        assert learner.pattern_weights["gstin"][0] > 1.0

    def test_pattern_weights_decrease_incorrect(self, learner):
        learner.train_on_sample(
            ocr_text="Test",
            ground_truth={"gstin": "27AABCU9603R1ZM"},
            extracted={"gstin": "WRONG"},
            field_name="gstin",
            pattern_index=0,
        )
        assert learner.pattern_weights["gstin"][0] < 1.0

    def test_get_ranked_patterns(self, learner):
        patterns = ["pat1", "pat2", "pat3"]
        ranked = learner.get_ranked_patterns("gstin", patterns)
        assert len(ranked) == 3
        assert all(r[2] == 1.0 for r in ranked)

    def test_save_and_load_models(self, learner, tmp_path):
        learner.train_on_sample(
            ocr_text="Test",
            ground_truth={"gstin": "27AABCU9603R1ZM"},
            extracted={"gstin": "27AABCU9603R1ZM"},
            field_name="gstin",
            pattern_index=0,
        )
        learner.save_models()
        new_learner = PatternLearner(model_dir=str(tmp_path))
        assert new_learner.get_field_accuracy("gstin") == 1.0

    def test_learning_report(self, learner):
        learner.train_on_sample(
            ocr_text="Test",
            ground_truth={"gstin": "27AABCU9603R1ZM"},
            extracted={"gstin": "27AABCU9603R1ZM"},
            field_name="gstin",
            pattern_index=0,
        )
        report = learner.get_learning_report()
        assert "fields" in report
        assert "overall_accuracy" in report
        assert report["overall_accuracy"] == 1.0


class TestAnnotationStore:
    """Test AnnotationStore class."""

    @pytest.fixture
    def store(self, tmp_path):
        return AnnotationStore(annotations_file=str(tmp_path / "test_ann.json"))

    def test_add_annotation(self, store):
        store.add_annotation(
            file_name="test.pdf",
            ocr_text="Sample OCR",
            extracted_fields={"gstin": "27AABCU9603R1ZM"},
            corrected_fields={"gstin": "27AABCU9603R1ZM"},
        )
        assert store.get_annotation("test.pdf") is not None

    def test_get_annotation_not_found(self, store):
        assert store.get_annotation("nonexistent.pdf") is None

    def test_get_all_annotations(self, store):
        store.add_annotation("f1", "t1", {}, {})
        store.add_annotation("f2", "t2", {}, {})
        assert len(store.get_all_annotations()) == 2

    def test_remove_annotation(self, store):
        store.add_annotation("test.pdf", "OCR", {}, {})
        store.remove_annotation("test.pdf")
        assert store.get_annotation("test.pdf") is None

    def test_get_training_data(self, store):
        store.add_annotation(
            "test.pdf",
            "GSTIN: 27AABCU9603R1ZM",
            {"gstin": "27AABCU9603R1ZM"},
            {"gstin": "27AABCU9603R1ZM"},
        )
        data = store.get_training_data("gstin")
        assert len(data) == 1

    def test_annotation_stats(self, store):
        store.add_annotation("f1", "t1", {}, {"gstin": "X"})
        store.add_annotation("f2", "t2", {}, {"pan": "Y"})
        stats = store.get_annotation_stats()
        assert stats["total"] == 2
        assert "gstin" in stats["fields_covered"]

    def test_save_and_load(self, store, tmp_path):
        store.add_annotation("test.pdf", "OCR", {"gstin": "X"}, {"gstin": "X"})
        new_store = AnnotationStore(annotations_file=str(tmp_path / "test_ann.json"))
        assert len(new_store.get_all_annotations()) == 1


class TestContinuousLearner:
    """Test ContinuousLearner class."""

    @pytest.fixture
    def learner(self, tmp_path):
        return ContinuousLearner(
            model_dir=str(tmp_path / "models"),
            annotations_file=str(tmp_path / "ann.json"),
        )

    def test_initialization(self, learner):
        assert learner.pattern_learner is not None
        assert learner.annotation_store is not None

    def test_learn_from_annotation(self, learner):
        learner.annotation_store.add_annotation(
            "test.pdf",
            "GSTIN: 27AABCU9603R1ZM",
            {"gstin": "27AABCU9603R1ZM"},
            {"gstin": "27AABCU9603R1ZM"},
        )
        learner.learn_from_annotation("test.pdf")
        assert learner.pattern_learner.get_field_accuracy("gstin") == 1.0

    def test_learn_from_all_annotations(self, learner):
        learner.annotation_store.add_annotation(
            "f1", "GST: X", {"gstin": "X"}, {"gstin": "X"}
        )
        learner.annotation_store.add_annotation(
            "f2", "GST: Y", {"gstin": "Y"}, {"gstin": "Y"}
        )
        report = learner.learn_from_all_annotations()
        assert "overall_accuracy" in report

    def test_get_learning_dashboard(self, learner):
        learner.annotation_store.add_annotation(
            "f1", "T", {"gstin": "X"}, {"gstin": "X"}
        )
        dashboard = learner.get_learning_dashboard()
        assert "learning" in dashboard
        assert "annotations" in dashboard
        assert "recommendations" in dashboard

    def test_get_improved_patterns(self, learner):
        patterns = ["p1", "p2"]
        ranked = learner.get_improved_patterns("gstin", patterns)
        assert len(ranked) == 2


class TestInvoiceProcessor:
    """Test InvoiceProcessor class."""

    def test_initialization_no_learning(self):
        processor = InvoiceProcessor(enable_learning=False)
        assert processor.extractor is not None
        assert processor.cleaner is not None
        assert processor.learner is None

    def test_initialization_with_learning(self):
        processor = InvoiceProcessor(enable_learning=True)
        assert processor.learner is not None

    def test_ensure_dirs(self, tmp_path):
        import os

        old_cwd = os.getcwd()
        test_dir = tmp_path / "test_app"
        test_dir.mkdir()
        os.chdir(test_dir)
        try:
            processor = InvoiceProcessor(enable_learning=False)
            assert (test_dir / "output").exists()
            assert (test_dir / "logs").exists()
            assert (test_dir / "cache").exists()
            assert (test_dir / "sample_invoices").exists()
        finally:
            os.chdir(old_cwd)

    def test_file_not_found_raises(self):
        processor = InvoiceProcessor(enable_learning=False)
        with pytest.raises(FileNotFoundError):
            processor.process_invoice("nonexistent_file.pdf")

    def test_save_results_json(self, processor, tmp_path):
        results = [{"file_name": "test.pdf", "success": True, "fields": {}}]
        output_path = tmp_path / "results.json"
        saved_path = processor.save_results_json(results, str(output_path))
        assert Path(saved_path).exists()

    def test_save_results_csv(self, processor, tmp_path):
        results = [{"file_name": "test.pdf", "success": True, "fields": {}}]
        output_path = tmp_path / "results.csv"
        saved_path = processor.save_results_csv(results, str(output_path))
        assert Path(saved_path).exists()

    def test_get_summary_empty(self, processor):
        result = processor.get_summary([])
        assert result["total"] == 0
        assert result["successful"] == 0
        assert result["failed"] == 0
        assert result["success_rate"] == 0

    def test_get_summary_with_results(self, processor):
        results = [
            {"success": True, "fields": {"gstin": "X"}},
            {"success": True, "fields": {"gstin": "Y"}},
            {"success": False, "fields": {}},
        ]
        summary = processor.get_summary(results)
        assert summary["total"] == 3
        assert summary["successful"] == 2
        assert summary["failed"] == 1
        assert summary["success_rate"] == pytest.approx(66.7, 0.1)

    @pytest.fixture
    def processor(self):
        return InvoiceProcessor(enable_learning=False)


class TestConfidenceScoring:
    """Test confidence scoring functionality."""

    @pytest.fixture
    def extractor(self):
        return FieldExtractor()

    def test_high_confidence_valid_gstin(self, extractor):
        text = "GSTIN: 27AABCU9603R1ZM"
        fields = extractor.extract_all_fields(text)
        conf = fields["_confidence_details"]["gstin"]["confidence"]
        assert conf >= 50.0

    def test_zero_confidence_not_found(self, extractor):
        text = "Random text with no invoice data"
        fields = extractor.extract_all_fields(text)
        conf = fields["_confidence_details"]["gstin"]["confidence"]
        assert conf == 0.0

    def test_confidence_details_has_required_keys(self, extractor):
        text = "GSTIN: 27AABCU9603R1ZM\nInvoice: INV-001"
        fields = extractor.extract_all_fields(text)
        for field in ["gstin", "invoice_number"]:
            details = fields["_confidence_details"][field]
            assert "confidence" in details
            assert "pattern_index" in details
            assert "pattern_preview" in details


class TestDataCleanerEdgeCases:
    """Test DataCleaner edge cases."""

    @pytest.fixture
    def cleaner(self):
        return DataCleaner()

    def test_gstin_checksum_valid(self, cleaner):
        assert cleaner.validate_gstin("27AABCU9603R1ZM") is True

    def test_gstin_checksum_invalid_format(self, cleaner):
        assert cleaner.validate_gstin("27AABCU9603R1Z") is False
        assert cleaner.validate_gstin("27AABCU9603R1ZMM") is False

    def test_pan_valid_format(self, cleaner):
        assert cleaner.validate_pan("AABCU9603R") is True

    def test_pan_invalid_format(self, cleaner):
        assert cleaner.validate_pan("ABC123") is False
        assert cleaner.validate_pan("AABCU9603") is False
        assert cleaner.validate_pan("1234567890") is False

    def test_clean_po_number_trailing_punctuation(self, cleaner):
        result = cleaner.clean_field("po_number", "PO-12345.,;:")
        assert result == "PO-12345"

    def test_clean_amount_various_formats(self, cleaner):
        assert "15000" in cleaner.clean_field("total_amount", "₹15,000.00").replace(
            ",", ""
        )
        assert "2628500" in cleaner.clean_field("total_amount", "26,28,500.00").replace(
            ",", ""
        )

    def test_clean_date_unparseable(self, cleaner):
        result = cleaner.clean_field("invoice_date", "not a date at all")
        assert result == "not a date at all"


class TestAnnotationStoreEdgeCases:
    """Test AnnotationStore edge cases."""

    @pytest.fixture
    def store(self, tmp_path):
        return AnnotationStore(annotations_file=str(tmp_path / "empty.json"))

    def test_empty_store_stats(self, store):
        stats = store.get_annotation_stats()
        assert stats["total"] == 0

    def test_remove_nonexistent(self, store):
        store.remove_annotation("nonexistent.pdf")
        assert len(store.get_all_annotations()) == 0


class TestPatternLearnerEdgeCases:
    """Test PatternLearner edge cases."""

    def test_field_accuracy_no_data(self, tmp_path):
        learner = PatternLearner(model_dir=str(tmp_path))
        assert learner.get_field_accuracy("nonexistent_field") == 0.0

    def test_get_ranked_patterns_no_weights(self, tmp_path):
        learner = PatternLearner(model_dir=str(tmp_path))
        patterns = ["a", "b", "c"]
        ranked = learner.get_ranked_patterns("new_field", patterns)
        assert all(r[2] == 1.0 for r in ranked)

    def test_calculate_similarity_identical(self):
        from advanced_training import PatternLearner

        sim = PatternLearner._calculate_similarity("ABC", "ABC")
        assert sim == 1.0

    def test_calculate_similarity_empty(self):
        from advanced_training import PatternLearner

        sim = PatternLearner._calculate_similarity("", "")
        assert sim == 1.0

    def test_calculate_similarity_one_empty(self):
        from advanced_training import PatternLearner

        sim = PatternLearner._calculate_similarity("ABC", "")
        assert sim == 0.0

    def test_calculate_similarity_substring(self):
        from advanced_training import PatternLearner

        sim = PatternLearner._calculate_similarity("ABC", "ABCDEF")
        assert sim == 0.8

    def test_levenshtein_identical(self):
        from advanced_training import PatternLearner

        dist = PatternLearner._levenshtein_distance("hello", "hello")
        assert dist == 0

    def test_levenshtein_one_char_diff(self):
        from advanced_training import PatternLearner

        dist = PatternLearner._levenshtein_distance("hello", "hallo")
        assert dist == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
