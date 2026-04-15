"""
Streamlit Web UI for Invoice Data Extractor.

Provides a user-friendly interface for uploading invoices,
extracting data, annotating results, and downloading results in JSON/CSV format.
Includes learning dashboard and continuous improvement features.
"""

import os
import sys
import json
import tempfile
from pathlib import Path

import streamlit as st
from PIL import Image

try:
    from utils import InvoiceProcessor

    PROCESSOR_AVAILABLE = True
except ImportError as e:
    PROCESSOR_AVAILABLE = False
    IMPORT_ERROR = str(e)

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

SUPPORTED_TYPES = ["jpg", "jpeg", "png", "bmp", "tiff", "tif", "pdf"]

st.set_page_config(
    page_title="Invoice Data Extractor Pro",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded",
)


def init_processor():
    try:
        processor = InvoiceProcessor()
        return processor, True
    except EnvironmentError:
        # Tesseract not available - return processor with limited functionality
        return None, False
    except ImportError as e:
        st.error(f"**Missing Dependency**: {e}")
        st.info("Run `pip install -r requirements.txt` to install all dependencies.")
        return None, False


def render_sidebar():
    with st.sidebar:
        st.title("🧾 Settings")

        st.subheader("Processing")
        preprocess = st.checkbox("Enable Image Preprocessing", value=True)
        show_raw_text = st.checkbox("Show Raw OCR Text", value=False)
        show_confidence = st.checkbox("Show Confidence Score", value=True)
        enable_learning = st.checkbox("Enable Continuous Learning", value=True)

        st.divider()
        st.subheader("About")
        st.markdown(
            "**Invoice Data Extractor Pro** v2.0\n\n"
            "Extracts key data from invoice documents:\n"
            "- Vendor Name\n"
            "- Invoice Number\n"
            "- Invoice Date & Due Date\n"
            "- Total Amount\n"
            "- GSTIN & PAN (India)\n"
            "- Purchase Order Number\n\n"
            "Supports JPG, PNG, BMP, TIFF, and PDF files.\n\n"
            "✨ **New Features:**\n"
            "- Continuous learning from annotations\n"
            "- Per-field confidence scoring\n"
            "- Accuracy dashboard"
        )

        st.divider()
        st.subheader("Output Format")
        output_format = st.radio("Download format:", ["JSON", "CSV"], index=0)

    return preprocess, show_raw_text, show_confidence, enable_learning, output_format


def render_field_card(label, value, icon="📋", confidence=None):
    """Render a field card with optional confidence indicator."""
    if value and value != "Not Found":
        if confidence is not None:
            conf_color = (
                "#22c55e"
                if confidence >= 80
                else "#eab308"
                if confidence >= 60
                else "#ef4444"
            )
            st.success(
                f"{icon} **{label}**: {value}  \n"
                f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;🎯 Confidence: "
                f"<span style='color:{conf_color};font-weight:bold'>{confidence:.1f}%</span>"
            )
        else:
            st.success(f"{icon} **{label}**: {value}")
    else:
        st.warning(f"{icon} **{label}**: Not Found")


def render_results(result, show_raw_text=False, show_confidence=True):
    fields = result.get("fields", {})
    confidence_details = result.get("confidence_details", {})

    st.subheader("📊 Extracted Fields")

    col1, col2, col3 = st.columns(3)

    with col1:
        vendor_conf = (
            confidence_details.get("vendor_name")
            if isinstance(confidence_details, dict)
            else None
        )
        render_field_card("Vendor Name", fields.get("vendor_name"), "🏢", vendor_conf)

        inv_conf = (
            confidence_details.get("invoice_number")
            if isinstance(confidence_details, dict)
            else None
        )
        render_field_card(
            "Invoice Number", fields.get("invoice_number"), "📄", inv_conf
        )

        date_conf = (
            confidence_details.get("invoice_date")
            if isinstance(confidence_details, dict)
            else None
        )
        render_field_card("Invoice Date", fields.get("invoice_date"), "📅", date_conf)

    with col2:
        due_conf = (
            confidence_details.get("due_date")
            if isinstance(confidence_details, dict)
            else None
        )
        render_field_card("Due Date", fields.get("due_date"), "⏰", due_conf)

        amt_conf = (
            confidence_details.get("total_amount")
            if isinstance(confidence_details, dict)
            else None
        )
        render_field_card("Total Amount", fields.get("total_amount"), "💰", amt_conf)

        po_conf = (
            confidence_details.get("po_number")
            if isinstance(confidence_details, dict)
            else None
        )
        render_field_card("PO Number", fields.get("po_number"), "🔖", po_conf)

    with col3:
        gstin_conf = (
            confidence_details.get("gstin")
            if isinstance(confidence_details, dict)
            else None
        )
        render_field_card("GSTIN", fields.get("gstin"), "🇮🇳", gstin_conf)

        pan_conf = (
            confidence_details.get("pan")
            if isinstance(confidence_details, dict)
            else None
        )
        render_field_card("PAN", fields.get("pan"), "🆔", pan_conf)

        all_amounts = fields.get("all_amounts", [])
        if all_amounts and all_amounts != "Not Found":
            st.info(f"💵 **All Amounts**: {', '.join(str(a) for a in all_amounts)}")
        else:
            st.warning("💵 **All Amounts**: Not Found")

    if show_confidence and result.get("confidence") is not None:
        confidence = result["confidence"]
        if confidence >= 70:
            st.success(f"🎯 **OCR Confidence**: {confidence}% (Good)")
        elif confidence >= 50:
            st.warning(
                f"🎯 **OCR Confidence**: {confidence}% (Moderate - review recommended)"
            )
        else:
            st.error(
                f"🎯 **OCR Confidence**: {confidence}% (Low - manual review required)"
            )

    if show_raw_text and result.get("raw_text"):
        with st.expander("📝 Raw OCR Text", expanded=False):
            st.text_area("Extracted Text", result["raw_text"], height=300)


def render_annotation_interface(result, processor):
    """Render an annotation form for users to edit/correct extracted fields."""
    if not result.get("success"):
        return

    fields = result.get("fields", {})
    file_name = result.get("file_name", "unknown")
    raw_text = result.get("raw_text", "")

    with st.expander("✏️ Annotate & Correct Fields", expanded=False):
        st.markdown(
            "Review and correct the extracted fields. Changes will be saved as training data."
        )

        corrected_fields = {}

        col_a, col_b = st.columns(2)

        field_keys = [
            ("vendor_name", "Vendor Name", "🏢"),
            ("invoice_number", "Invoice Number", "📄"),
            ("invoice_date", "Invoice Date", "📅"),
            ("due_date", "Due Date", "⏰"),
            ("total_amount", "Total Amount", "💰"),
            ("po_number", "PO Number", "🔖"),
            ("gstin", "GSTIN", "🇮🇳"),
            ("pan", "PAN", "🆔"),
        ]

        with col_a:
            for key, label, icon in field_keys[:4]:
                current_value = fields.get(key, "")
                if current_value == "Not Found":
                    current_value = ""
                corrected_fields[key] = st.text_input(
                    f"{icon} {label}",
                    value=current_value,
                    key=f"annotate_{file_name}_{key}",
                    help=f"Correct the {label} if needed",
                )

        with col_b:
            for key, label, icon in field_keys[4:]:
                current_value = fields.get(key, "")
                if current_value == "Not Found":
                    current_value = ""
                corrected_fields[key] = st.text_input(
                    f"{icon} {label}",
                    value=current_value,
                    key=f"annotate_{file_name}_{key}",
                    help=f"Correct the {label} if needed",
                )

        st.divider()

        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            if st.button(
                "💾 Save as Training Data", type="primary", use_container_width=True
            ):
                if "annotations_saved" not in st.session_state:
                    st.session_state.annotations_saved = []

                annotation_key = (
                    f"{file_name}_{len(st.session_state.annotations_saved)}"
                )

                processor.add_annotation(
                    file_name=file_name,
                    raw_text=raw_text,
                    extracted_fields=fields,
                    corrected_fields=corrected_fields,
                )

                st.session_state.annotations_saved.append(annotation_key)
                st.success(f"✅ Annotation saved for **{file_name}**!")
                st.rerun()

        with col_btn2:
            if "annotations_saved" in st.session_state and any(
                file_name in k for k in st.session_state.annotations_saved
            ):
                st.success("✅ Already annotated for this file.")


def render_learning_dashboard(processor):
    """Render the learning dashboard with accuracy metrics and training controls."""
    st.subheader("🎓 Learning Dashboard")

    dashboard_data = processor.get_learning_dashboard()

    if not dashboard_data:
        st.info(
            "No learning data available yet. Start annotating invoices to build training data."
        )
        return

    annotations = dashboard_data.get("annotations", {})
    learning = dashboard_data.get("learning", {})
    recommendations = dashboard_data.get("recommendations", [])

    total_annotations = annotations.get("total", 0)
    fields_covered = annotations.get("fields_covered", [])
    overall_accuracy = learning.get("overall_accuracy", 0.0)

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="📊 Total Annotations",
            value=total_annotations,
            help="Number of invoices annotated for training",
        )

    with col2:
        accuracy_pct = round(overall_accuracy * 100, 1)
        st.metric(
            label="🎯 Overall Accuracy",
            value=f"{accuracy_pct}%",
            delta=f"{accuracy_pct - 50:+.1f}%" if accuracy_pct > 0 else None,
            help="Pattern matching accuracy across all fields",
        )

    with col3:
        st.metric(
            label="📋 Fields Covered",
            value=len(fields_covered),
            help="Number of unique fields with training data",
        )

    st.markdown("---")

    st.subheader("📈 Per-Field Accuracy")

    field_data = learning.get("fields", {})

    if field_data:
        for field_name, data in field_data.items():
            accuracy = data.get("accuracy", 0.0)
            total_samples = data.get("total_samples", 0)
            correct = data.get("correct_predictions", 0)

            col_f1, col_f2 = st.columns([3, 1])
            with col_f1:
                st.markdown(f"**{field_name.replace('_', ' ').title()}**")
                st.progress(accuracy, text=f"{accuracy:.0%}")
            with col_f2:
                st.caption(f"{correct}/{total_samples} correct")
    else:
        st.info(
            "No per-field data yet. Annotate more invoices to see accuracy metrics."
        )

    st.markdown("---")

    st.subheader("🤖 Train on All Annotations")

    if total_annotations > 0:
        st.markdown(
            f"Training will use all **{total_annotations}** annotated invoices to improve pattern recognition."
        )

        if st.button(
            "🚀 Train on All Annotations", type="primary", use_container_width=True
        ):
            with st.spinner("Training on annotations... This may take a moment."):
                try:
                    report = processor.train_on_annotations()

                    st.success("✅ Training complete!")

                    if report:
                        overall = report.get("overall_accuracy", 0)
                        st.metric("New Overall Accuracy", f"{overall:.1%}")

                        with st.expander("📊 Training Report", expanded=True):
                            for field_name, data in report.get("fields", {}).items():
                                st.markdown(
                                    f"**{field_name.replace('_', ' ').title()}**: "
                                    f"{data.get('accuracy', 0):.0%} accuracy "
                                    f"({data.get('total_samples', 0)} samples)"
                                )
                except Exception as e:
                    st.error(f"Training failed: {e}")
    else:
        st.info("No annotations to train on. Start by annotating some invoices first.")

    st.markdown("---")

    if recommendations:
        st.subheader("💡 Recommendations")
        for rec in recommendations:
            st.info(rec)


def process_single_file(processor, uploaded_file, preprocess=True):
    suffix = Path(uploaded_file.name).suffix.lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        tmp_path = tmp.name

    try:
        result = processor.process_invoice(tmp_path, preprocess=preprocess)
        return result
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def render_single_mode(
    processor,
    preprocess,
    show_raw_text,
    show_confidence,
    output_format,
    tesseract_available=True,
):
    st.subheader("📁 Upload Single Invoice")

    # If Tesseract is not available, show manual text input
    if not tesseract_available:
        st.info(
            "💡 **Manual Mode:** Paste OCR text below and extract fields using pattern matching."
        )

        manual_text = st.text_area(
            "Paste OCR Text Here:",
            height=200,
            help="Paste the text extracted from an invoice to extract structured fields",
        )

        if manual_text.strip() and st.button(
            "🔍 Extract Fields from Text", type="primary", use_container_width=True
        ):
            try:
                from extractor import FieldExtractor
                from utils import DataCleaner

                extractor = FieldExtractor()
                cleaner = DataCleaner()

                fields = extractor.extract_all_fields(manual_text)
                confidence_details = fields.pop("_confidence_details", None)
                cleaned_fields = cleaner.clean_all(fields)
                cleaned_fields.pop("_confidence_details", None)

                result = {
                    "file_path": "manual_input",
                    "file_name": "Manual Input",
                    "extraction_time": "< 1 sec",
                    "confidence": None,
                    "fields": cleaned_fields,
                    "raw_text": manual_text,
                    "success": True,
                    "error": None,
                }

                if confidence_details:
                    result["confidence_details"] = confidence_details

                st.success("✅ Fields extracted from text!")
                render_results(result, show_raw_text, show_confidence)

            except Exception as e:
                st.error(f"Error: {e}")

        st.divider()
        st.caption(
            "💡 For automatic OCR extraction, install Tesseract and run locally or deploy with Docker/Railway."
        )
        return

    # Normal file upload mode when Tesseract is available
    uploaded_file = st.file_uploader(
        "Choose an invoice file",
        type=SUPPORTED_TYPES,
        help="Upload a JPG, PNG, BMP, TIFF, or PDF invoice",
    )

    if uploaded_file is not None:
        st.success(f"Uploaded: **{uploaded_file.name}** ({uploaded_file.size:,} bytes)")

        if not uploaded_file.name.lower().endswith(".pdf"):
            try:
                image = Image.open(uploaded_file)
                st.image(image, caption="Invoice Preview", use_container_width=True)
            except Exception:
                st.info("Preview not available for this file type.")
            uploaded_file.seek(0)

        if st.button("🔍 Extract Data", type="primary", use_container_width=True):
            with st.spinner("Processing invoice... This may take a few seconds."):
                try:
                    result = process_single_file(processor, uploaded_file, preprocess)

                    if result.get("success"):
                        st.success("✅ Data extracted successfully!")
                    else:
                        st.error(
                            f"❌ Extraction failed: {result.get('error', 'Unknown error')}"
                        )

                    render_results(result, show_raw_text, show_confidence)

                    if result.get("success"):
                        col_dl1, col_dl2 = st.columns(2)
                        with col_dl1:
                            json_str = json.dumps(
                                result, indent=2, ensure_ascii=False, default=str
                            )
                            st.download_button(
                                "📄 Download JSON",
                                data=json_str,
                                file_name=f"{Path(uploaded_file.name).stem}_result.json",
                                mime="application/json",
                                use_container_width=True,
                            )
                        with col_dl2:
                            output_path = tempfile.mktemp(suffix=".csv")
                            processor.save_results_csv(result, output_path)
                            with open(output_path, "r", encoding="utf-8") as f:
                                csv_data = f.read()
                            try:
                                os.unlink(output_path)
                            except OSError:
                                pass
                            st.download_button(
                                "📊 Download CSV",
                                data=csv_data,
                                file_name=f"{Path(uploaded_file.name).stem}_result.csv",
                                mime="text/csv",
                                use_container_width=True,
                            )

                        st.divider()
                        render_annotation_interface(result, processor)

                except Exception as e:
                    st.error(f"Error processing file: {e}")
                    with st.expander("Error Details"):
                        st.code(str(e))


def render_batch_mode(
    processor,
    preprocess,
    show_raw_text,
    show_confidence,
    output_format,
    tesseract_available=True,
):
    if not tesseract_available:
        st.subheader("📁 Batch Processing")
        st.info(
            "⚠️ Batch processing requires Tesseract OCR. Use manual mode above or deploy with Docker/Railway for full functionality."
        )
        return

    st.subheader("📁 Batch Processing")
    st.info("Upload multiple invoice files to process them all at once.")

    uploaded_files = st.file_uploader(
        "Choose invoice files",
        type=SUPPORTED_TYPES,
        accept_multiple_files=True,
        help="Upload multiple JPG, PNG, BMP, TIFF, or PDF invoices",
    )

    if uploaded_files:
        st.success(f"**{len(uploaded_files)}** file(s) selected for processing")

        if st.button("🔄 Process All Files", type="primary", use_container_width=True):
            results = []
            progress = st.progress(0)
            status = st.empty()

            for i, file in enumerate(uploaded_files):
                status.info(f"Processing {i + 1}/{len(uploaded_files)}: {file.name}")
                try:
                    result = process_single_file(processor, file, preprocess)
                    results.append(result)
                except Exception as e:
                    results.append(
                        {
                            "file_name": file.name,
                            "success": False,
                            "error": str(e),
                            "fields": {},
                        }
                    )
                progress.progress((i + 1) / len(uploaded_files))

            status.empty()

            summary = processor.get_summary(results)
            st.subheader("📊 Batch Summary")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Files", summary["total"])
            col2.metric("Successful", summary["successful"])
            col3.metric("Failed", summary["failed"])
            col4.metric("Success Rate", f"{summary['success_rate']}%")

            st.subheader("📋 Results")
            for result in results:
                with st.expander(
                    f"{'✅' if result.get('success') else '❌'} {result.get('file_name', 'Unknown')}",
                    expanded=False,
                ):
                    if result.get("success"):
                        render_results(result, show_raw_text, show_confidence)
                        st.divider()
                        render_annotation_interface(result, processor)
                    else:
                        st.error(f"Error: {result.get('error', 'Unknown error')}")

            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                json_str = json.dumps(
                    results, indent=2, ensure_ascii=False, default=str
                )
                st.download_button(
                    "📄 Download All as JSON",
                    data=json_str,
                    file_name="batch_results.json",
                    mime="application/json",
                    use_container_width=True,
                )
            with col_dl2:
                output_path = tempfile.mktemp(suffix=".csv")
                processor.save_results_csv(results, output_path)
                with open(output_path, "r", encoding="utf-8") as f:
                    csv_data = f.read()
                try:
                    os.unlink(output_path)
                except OSError:
                    pass
                st.download_button(
                    "📊 Download All as CSV",
                    data=csv_data,
                    file_name="batch_results.csv",
                    mime="text/csv",
                    use_container_width=True,
                )


def main():
    st.title("🧾 Invoice Data Extractor")
    st.markdown("Extract key data from invoice documents using OCR & NLP")

    preprocess, show_raw_text, show_confidence, enable_learning, output_format = (
        render_sidebar()
    )

    if not PROCESSOR_AVAILABLE:
        st.error(f"**Import Error**: {IMPORT_ERROR}")
        st.info(
            "Please ensure all dependencies are installed: `pip install -r requirements.txt`"
        )
        st.stop()

    processor, tesseract_available = init_processor()

    # Show warning if Tesseract is not available
    if not tesseract_available:
        st.warning(
            "⚠️ **Tesseract OCR not available.** Automatic extraction is disabled."
        )
        st.info(
            "💡 **You can still:**\n"
            "• Use **Manual Text Input** to paste OCR text\n"
            "• View the **Learning Dashboard**\n"
            "• Test extraction patterns\n\n"
            "**To enable full OCR:**\n"
            "• **Local:** Install Tesseract and run locally\n"
            "• **Docker:** Use the included Dockerfile\n"
            "• **Railway/Heroku:** Deploy with system package support"
        )

    if processor is None:
        st.stop()

    tab_single, tab_batch, tab_learning = st.tabs(
        [
            "📄 Single Invoice",
            "📁 Batch Processing",
            "🎓 Learning",
        ]
    )

    with tab_single:
        render_single_mode(
            processor,
            preprocess,
            show_raw_text,
            show_confidence,
            output_format,
            tesseract_available=tesseract_available,
        )

    with tab_batch:
        render_batch_mode(
            processor,
            preprocess,
            show_raw_text,
            show_confidence,
            output_format,
            tesseract_available=tesseract_available,
        )

    with tab_learning:
        render_learning_dashboard(processor)

    st.divider()
    st.caption(
        "Invoice Data Extractor v2.0 | Built with Python, Tesseract OCR & Streamlit | "
        "Supports India-focused fields (GSTIN, PAN) | Continuous Learning Enabled"
    )


if __name__ == "__main__":
    main()
