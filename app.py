"""
PaddleOCR Streamlit Application
Complete OCR solution for PDF, DOCX, and TXT files
"""

import hashlib
import logging
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st

from config import (
    DEVICE_OPTIONS,
    LANGUAGE_OPTIONS,
    MAX_FILE_SIZE_MB,
    OCR_PRESETS,
    OUTPUT_FORMATS,
    PRECISION_OPTIONS,
    SUPPORTED_FORMATS,
    TEXTAREA_HEIGHT,
)
from document_processor import DocumentProcessor
from logger_config import setup_logging
from ocr_engine import OCREngine
from utils import format_file_size, sanitize_filename, validate_file

# Setup logging
setup_logging(
    log_level="INFO", console_output=False
)  # Disable console to avoid Streamlit conflicts
logger = logging.getLogger(__name__)


def initialize_session_state():
    """Initialize Streamlit session state variables"""
    if "ocr_results" not in st.session_state:
        st.session_state.ocr_results = None
    if "ocr_engine" not in st.session_state:
        st.session_state.ocr_engine = None
    if "processing_complete" not in st.session_state:
        st.session_state.processing_complete = False
    if "file_metadata" not in st.session_state:
        st.session_state.file_metadata = {}
    if "preview_images" not in st.session_state:
        st.session_state.preview_images = []


def clear_results():
    """Clear all processing results and reset state"""
    logger.info("Clearing results and resetting state")
    st.session_state.ocr_results = None
    st.session_state.processing_complete = False
    st.session_state.file_metadata = {}
    st.session_state.preview_images = []
    st.rerun()


def create_sidebar():
    """Create sidebar with OCR configuration options"""
    st.sidebar.title("⚙️ OCR Configuration")

    # Settings Preset Selection
    st.sidebar.subheader("⚡ Quick Settings")
    preset_name = st.sidebar.selectbox(
        "Settings Preset",
        options=list(OCR_PRESETS.keys()),
        index=1,  # Default to "Balanced"
        format_func=lambda x: OCR_PRESETS[x]["name"],
        help="Choose a preset or use Custom for manual configuration",
    )

    # Show preset description
    preset_desc = OCR_PRESETS[preset_name]["description"]
    st.sidebar.info(f"ℹ️ {preset_desc}")

    # Get preset config
    preset_config = OCR_PRESETS[preset_name]["config"]

    # Language selection (always shown)
    st.sidebar.subheader("Language Settings")
    language = st.sidebar.selectbox(
        "OCR Language",
        options=list(LANGUAGE_OPTIONS.keys()),
        format_func=lambda x: LANGUAGE_OPTIONS[x],
        help="Select the language for OCR recognition",
    )

    # Show detailed settings only for Custom preset
    if preset_name == "Custom":
        # Detection settings
        st.sidebar.subheader("Detection Settings")
        use_textline_orientation = st.sidebar.checkbox(
            "Enable Textline Orientation",
            value=True,
            help="Detect and correct text line orientation",
        )

        text_det_thresh = st.sidebar.slider(
            "Detection Threshold",
            min_value=0.1,
            max_value=0.9,
            value=0.3,
            step=0.05,
            help="Threshold for text detection",
        )

        text_det_box_thresh = st.sidebar.slider(
            "Box Threshold",
            min_value=0.1,
            max_value=0.9,
            value=0.6,
            step=0.05,
            help="Threshold for bounding box filtering",
        )

        # Recognition settings
        st.sidebar.subheader("Recognition Settings")
        text_rec_score_thresh = st.sidebar.slider(
            "Recognition Score Threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.05,
            help="Minimum confidence score for recognition results",
        )

        text_recognition_batch_size = st.sidebar.number_input(
            "Recognition Batch Size",
            min_value=1,
            max_value=32,
            value=6,
            help="Number of text lines to recognize in parallel",
        )

        # Advanced settings (collapsed by default)
        with st.sidebar.expander("Advanced Settings"):
            use_doc_orientation_classify = st.checkbox(
                "Enable Document Orientation Classification",
                value=False,
                help="Classify and correct document orientation",
            )

            use_doc_unwarping = st.checkbox(
                "Enable Document Unwarping", value=False, help="Unwarp distorted document images"
            )

            return_word_box = st.checkbox(
                "Return Word Boxes", value=False, help="Return bounding boxes for individual words"
            )

        # Build configuration from custom settings
        config = {
            "lang": language,
            "use_textline_orientation": use_textline_orientation,
            "text_det_thresh": text_det_thresh,
            "text_det_box_thresh": text_det_box_thresh,
            "text_rec_score_thresh": text_rec_score_thresh,
            "text_recognition_batch_size": text_recognition_batch_size,
            "use_doc_orientation_classify": use_doc_orientation_classify,
            "use_doc_unwarping": use_doc_unwarping,
            "return_word_box": return_word_box,
        }
    else:
        # Use preset configuration
        config = {"lang": language, **preset_config}

        # Show current settings in expandable section
        with st.sidebar.expander("📋 View Current Settings"):
            st.json(preset_config)

    return config


def process_uploaded_files(uploaded_files: List, config: dict, temp_dir: Path):
    """Process uploaded files with OCR"""

    logger.info(f"Starting to process {len(uploaded_files)} file(s)")

    # Initialize processors
    doc_processor = DocumentProcessor()

    # Initialize or update OCR engine
    if st.session_state.ocr_engine is None:
        with st.spinner("Initializing OCR engine..."):
            try:
                st.session_state.ocr_engine = OCREngine(config)
                logger.info("OCR engine initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OCR engine: {e}")
                st.error(f"Failed to initialize OCR engine: {str(e)}")
                return [], {}
    else:
        with st.spinner("Updating OCR configuration..."):
            try:
                st.session_state.ocr_engine.update_config(config)
                logger.info("OCR configuration updated")
            except Exception as e:
                logger.error(f"Failed to update OCR configuration: {e}")
                st.error(f"Failed to update OCR configuration: {str(e)}")
                return [], {}

    ocr_engine = st.session_state.ocr_engine

    all_results = []
    file_metadata = {}

    progress_bar = st.progress(0)
    status_text = st.empty()
    detail_text = st.empty()

    total_files = len(uploaded_files)
    total_pages = 0

    for file_idx, uploaded_file in enumerate(uploaded_files):
        file_start_time = time.time()

        # Sanitize filename
        safe_filename = sanitize_filename(uploaded_file.name)
        file_path = temp_dir / safe_filename

        # Validate file
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        is_valid, error_msg = validate_file(file_path, uploaded_file)
        if not is_valid:
            logger.warning(f"File validation failed for {uploaded_file.name}: {error_msg}")
            st.error(f"❌ {uploaded_file.name}: {error_msg}")
            continue

        status_text.markdown(
            f"**Processing file {file_idx + 1}/{total_files}:** `{uploaded_file.name}`"
        )
        detail_text.text(f"Size: {format_file_size(uploaded_file.size)}")

        # Convert document to images
        try:
            logger.info(f"Converting document to images: {uploaded_file.name}")
            images = doc_processor.process_file(file_path)
            num_pages = len(images)
            total_pages += num_pages

            logger.info(f"Document converted to {num_pages} image(s)")

            # Store first image for preview (thumbnail only, not full size)
            if images and file_idx == 0:  # Only store preview for first file
                preview_img = images[0].copy()
                preview_img.thumbnail((200, 200))  # Create thumbnail
                st.session_state.preview_images = [preview_img]

            # Process each image with OCR
            page_results = []
            for img_idx, image in enumerate(images):
                status_text.markdown(
                    f"**Processing file {file_idx + 1}/{total_files}:** `{uploaded_file.name}`"
                )
                detail_text.text(
                    f"Page {img_idx + 1}/{num_pages} | Total pages processed: {total_pages}"
                )

                try:
                    result = ocr_engine.process_image(image)
                    page_results.append(result)
                    all_results.append(result)
                except Exception as e:
                    logger.error(f"OCR failed for page {img_idx + 1} of {uploaded_file.name}: {e}")
                    st.warning(f"⚠️ Failed to process page {img_idx + 1} of {uploaded_file.name}")
                    page_results.append([[]])  # Empty result for failed page
                    all_results.append([[]])

            # Store metadata
            file_metadata[uploaded_file.name] = {
                "size": uploaded_file.size,
                "pages": num_pages,
                "processing_time": time.time() - file_start_time,
                "results_count": len(page_results),
            }

            logger.info(
                f"Successfully processed {uploaded_file.name} in {time.time() - file_start_time:.2f}s"
            )

        except Exception as e:
            logger.error(f"Error processing {uploaded_file.name}: {e}", exc_info=True)
            st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
            continue

        # Update progress
        progress_bar.progress((file_idx + 1) / total_files)

    status_text.markdown("**✅ Processing complete!**")
    detail_text.text(f"Total files: {len(file_metadata)} | Total pages: {total_pages}")
    time.sleep(1)  # Brief pause to show completion
    progress_bar.empty()
    status_text.empty()
    detail_text.empty()

    logger.info(f"Processing complete. Processed {len(file_metadata)} files, {total_pages} pages")

    return all_results, file_metadata


def create_download_button(label: str, data: str, filename: str, mime_type: str):
    """Helper function to create download button"""
    st.download_button(
        label=f"📥 {label}", data=data, file_name=filename, mime=mime_type, use_container_width=True
    )


def display_results(ocr_results: List, ocr_engine: OCREngine, output_format: str):
    """Display OCR results in selected format"""

    st.subheader("📊 OCR Results")

    # Display statistics
    stats = ocr_engine.get_statistics(ocr_results)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Pages", stats["total_pages"])
    with col2:
        st.metric("Text Blocks", stats["total_text_blocks"])
    with col3:
        st.metric("Characters", stats["total_characters"])
    with col4:
        st.metric("Avg Confidence", f"{stats['average_confidence']:.2%}")

    # Display file metadata if available
    if st.session_state.file_metadata:
        with st.expander("📋 File Processing Details"):
            for filename, metadata in st.session_state.file_metadata.items():
                st.markdown(f"**{filename}**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.text(f"Size: {format_file_size(metadata['size'])}")
                with col2:
                    st.text(f"Pages: {metadata['pages']}")
                with col3:
                    st.text(f"Time: {metadata['processing_time']:.2f}s")
                st.divider()

    st.divider()

    # Format mappings
    format_config = {
        "Markdown": {
            "title": "Markdown Output",
            "formatter": lambda: ocr_engine.format_as_markdown(ocr_results, page_numbers=True),
            "display": lambda text: st.text_area("Markdown", text, height=TEXTAREA_HEIGHT),
            "filename": "ocr_results.md",
            "mime": "text/markdown",
            "download_label": "Download Markdown",
        },
        "JSON": {
            "title": "JSON Output",
            "formatter": lambda: ocr_engine.format_as_json(ocr_results),
            "display": lambda text: st.json(text),
            "filename": "ocr_results.json",
            "mime": "application/json",
            "download_label": "Download JSON",
        },
        "Text": {
            "title": "Plain Text Output",
            "formatter": lambda: ocr_engine.format_as_markdown(ocr_results, page_numbers=False),
            "display": lambda text: st.text_area("Text", text, height=TEXTAREA_HEIGHT),
            "filename": "ocr_results.txt",
            "mime": "text/plain",
            "download_label": "Download Text",
        },
        "HTML": {
            "title": "HTML Output",
            "formatter": lambda: ocr_engine.format_as_html(ocr_results),
            "display": lambda text: st.code(text, language="html"),
            "filename": "ocr_results.html",
            "mime": "text/html",
            "download_label": "Download HTML",
        },
    }

    # Get configuration for selected format
    config = format_config.get(output_format)
    if config:
        st.markdown(f"### {config['title']}")
        formatted_text = config["formatter"]()
        config["display"](formatted_text)

        # Download button
        create_download_button(
            config["download_label"], formatted_text, config["filename"], config["mime"]
        )

    # Detailed view
    with st.expander("🔍 Detailed View (Page by Page)"):
        for i, result in enumerate(ocr_results, 1):
            st.markdown(f"#### Page {i}")
            structured_data = ocr_engine.extract_structured_data(result)

            if structured_data:
                for block in structured_data:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.text(block["text"])
                    with col2:
                        st.caption(f"Conf: {block['confidence']:.2%}")
            else:
                st.info("No text detected on this page")

            st.divider()


def main():
    """Main application function"""

    # Page configuration
    st.set_page_config(
        page_title="PaddleOCR Application",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Initialize session state
    initialize_session_state()

    # Header
    st.title("📄 PaddleOCR Document Processing")
    st.markdown(
        "Upload PDF, DOCX, TXT, or image files for OCR processing with PaddleOCR's complete feature suite."
    )

    # Sidebar configuration
    config = create_sidebar()

    # Main content area
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("📁 File Upload")
    with col2:
        if st.session_state.processing_complete:
            if st.button("🔄 Clear Results", use_container_width=True):
                clear_results()

    # File uploader
    uploaded_files = st.file_uploader(
        "Choose files to process",
        type=[ext.lstrip(".") for ext in SUPPORTED_FORMATS.keys()],  # Remove dots for Streamlit
        accept_multiple_files=True,
        help=f"Supported formats: {', '.join(SUPPORTED_FORMATS.values())} | Max size: {MAX_FILE_SIZE_MB}MB per file",
    )

    # Show file preview if files are uploaded
    if uploaded_files:
        with st.expander(f"📎 Uploaded Files ({len(uploaded_files)})", expanded=False):
            for uploaded_file in uploaded_files:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.text(f"📄 {uploaded_file.name}")
                with col2:
                    st.text(format_file_size(uploaded_file.size))
                with col3:
                    extension = Path(uploaded_file.name).suffix.lower()
                    st.text(SUPPORTED_FORMATS.get(extension, "Unknown"))

    # Output format and process button
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        output_format = st.selectbox(
            "Output Format", options=OUTPUT_FORMATS, help="Select the format for OCR results"
        )
    with col2:
        st.write("")  # Spacing
    with col3:
        st.write("")  # Spacing
        process_button = st.button("🚀 Process Files", type="primary", use_container_width=True)

    # Process files when button is clicked
    if process_button and uploaded_files:
        logger.info(f"Process button clicked with {len(uploaded_files)} files")
        # Create temporary directory
        temp_dir = Path(tempfile.mkdtemp())

        try:
            # Process files
            start_time = time.time()
            ocr_results, file_metadata = process_uploaded_files(uploaded_files, config, temp_dir)
            processing_time = time.time() - start_time

            # Store results in session state
            if ocr_results:
                st.session_state.ocr_results = ocr_results
                st.session_state.file_metadata = file_metadata
                st.session_state.processing_complete = True

                st.success(f"✅ Processing completed in {processing_time:.2f} seconds!")
                logger.info(f"Processing completed successfully in {processing_time:.2f}s")
            else:
                st.warning("⚠️ No results generated. Please check the files and try again.")
                logger.warning("Processing completed but no results generated")

        except Exception as e:
            logger.error(f"Error during processing: {e}", exc_info=True)
            st.error(f"❌ Error during processing: {str(e)}")

        finally:
            # Cleanup temporary directory
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
                logger.info(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp directory: {e}")

    elif process_button and not uploaded_files:
        st.warning("⚠️ Please upload at least one file to process.")
        logger.warning("Process button clicked without files")

    # Show image preview if available
    if st.session_state.preview_images:
        with st.expander("🖼️ Preview (First Page)", expanded=False):
            st.image(
                st.session_state.preview_images[0],
                caption="First page preview",
                use_container_width=False,
            )

    # Display results if available
    if st.session_state.processing_complete and st.session_state.ocr_results:
        st.divider()
        display_results(st.session_state.ocr_results, st.session_state.ocr_engine, output_format)

    # Footer
    st.divider()
    st.markdown(
        """
        <div style='text-align: center; color: gray; padding: 20px;'>
        <p>Powered by <a href='https://github.com/PaddlePaddle/PaddleOCR' target='_blank'>PaddleOCR</a> | 
        Built with <a href='https://streamlit.io' target='_blank'>Streamlit</a></p>
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
