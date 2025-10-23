"""
PaddleOCR Streamlit Application
Complete OCR solution for PDF, DOCX, and TXT files
"""

import streamlit as st
import tempfile
import shutil
from pathlib import Path
from typing import List, Optional
import time

from ocr_engine import OCREngine
from document_processor import DocumentProcessor
from config import (
    SUPPORTED_FORMATS, 
    LANGUAGE_OPTIONS, 
    OUTPUT_FORMATS,
    DEVICE_OPTIONS,
    PRECISION_OPTIONS,
    MAX_FILE_SIZE_MB
)


def initialize_session_state():
    """Initialize Streamlit session state variables"""
    if 'ocr_results' not in st.session_state:
        st.session_state.ocr_results = None
    if 'processed_images' not in st.session_state:
        st.session_state.processed_images = None
    if 'ocr_engine' not in st.session_state:
        st.session_state.ocr_engine = None
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False


def create_sidebar():
    """Create sidebar with OCR configuration options"""
    st.sidebar.title("⚙️ OCR Configuration")
    
    # Language selection
    st.sidebar.subheader("Language Settings")
    language = st.sidebar.selectbox(
        "OCR Language",
        options=list(LANGUAGE_OPTIONS.keys()),
        format_func=lambda x: LANGUAGE_OPTIONS[x],
        help="Select the language for OCR recognition"
    )
    
    # Detection settings
    st.sidebar.subheader("Detection Settings")
    use_textline_orientation = st.sidebar.checkbox(
        "Enable Textline Orientation",
        value=True,
        help="Detect and correct text line orientation"
    )
    
    text_det_thresh = st.sidebar.slider(
        "Detection Threshold",
        min_value=0.1,
        max_value=0.9,
        value=0.3,
        step=0.05,
        help="Threshold for text detection"
    )
    
    text_det_box_thresh = st.sidebar.slider(
        "Box Threshold",
        min_value=0.1,
        max_value=0.9,
        value=0.6,
        step=0.05,
        help="Threshold for bounding box filtering"
    )
    
    # Recognition settings
    st.sidebar.subheader("Recognition Settings")
    text_rec_score_thresh = st.sidebar.slider(
        "Recognition Score Threshold",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.05,
        help="Minimum confidence score for recognition results"
    )
    
    text_recognition_batch_size = st.sidebar.number_input(
        "Recognition Batch Size",
        min_value=1,
        max_value=32,
        value=6,
        help="Number of text lines to recognize in parallel"
    )
    
    # Advanced settings (collapsed by default)
    with st.sidebar.expander("Advanced Settings"):
        use_doc_orientation_classify = st.checkbox(
            "Enable Document Orientation Classification",
            value=False,
            help="Classify and correct document orientation"
        )
        
        use_doc_unwarping = st.checkbox(
            "Enable Document Unwarping",
            value=False,
            help="Unwarp distorted document images"
        )
        
        return_word_box = st.checkbox(
            "Return Word Boxes",
            value=False,
            help="Return bounding boxes for individual words"
        )
    
    # Build configuration dictionary
    config = {
        'lang': language,
        'use_textline_orientation': use_textline_orientation,
        'text_det_thresh': text_det_thresh,
        'text_det_box_thresh': text_det_box_thresh,
        'text_rec_score_thresh': text_rec_score_thresh,
        'text_recognition_batch_size': text_recognition_batch_size,
        'use_doc_orientation_classify': use_doc_orientation_classify,
        'use_doc_unwarping': use_doc_unwarping,
        'return_word_box': return_word_box
    }
    
    return config


def process_uploaded_files(uploaded_files: List, config: dict, temp_dir: Path):
    """Process uploaded files with OCR"""
    
    # Initialize processors
    doc_processor = DocumentProcessor()
    
    # Initialize or update OCR engine
    if st.session_state.ocr_engine is None:
        with st.spinner("Initializing OCR engine..."):
            st.session_state.ocr_engine = OCREngine(config)
    else:
        with st.spinner("Updating OCR configuration..."):
            st.session_state.ocr_engine.update_config(config)
    
    ocr_engine = st.session_state.ocr_engine
    
    all_results = []
    all_images = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_files = len(uploaded_files)
    
    for file_idx, uploaded_file in enumerate(uploaded_files):
        # Save uploaded file temporarily
        file_path = temp_dir / uploaded_file.name
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        
        status_text.text(f"Processing {uploaded_file.name}...")
        
        # Convert document to images
        try:
            images = doc_processor.process_file(file_path)
            all_images.extend(images)
            
            # Process each image with OCR
            for img_idx, image in enumerate(images):
                status_text.text(
                    f"Processing {uploaded_file.name} - Page {img_idx + 1}/{len(images)}"
                )
                result = ocr_engine.process_image(image)
                all_results.append(result)
            
        except Exception as e:
            st.error(f"Error processing {uploaded_file.name}: {str(e)}")
            continue
        
        # Update progress
        progress_bar.progress((file_idx + 1) / total_files)
    
    status_text.text("Processing complete!")
    progress_bar.empty()
    
    return all_results, all_images


def display_results(ocr_results: List, ocr_engine: OCREngine, output_format: str):
    """Display OCR results in selected format"""
    
    st.subheader("📊 OCR Results")
    
    # Display statistics
    stats = ocr_engine.get_statistics(ocr_results)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Pages", stats['total_pages'])
    with col2:
        st.metric("Text Blocks", stats['total_text_blocks'])
    with col3:
        st.metric("Characters", stats['total_characters'])
    with col4:
        st.metric("Avg Confidence", f"{stats['average_confidence']:.2%}")
    
    st.divider()
    
    # Display results in selected format
    if output_format == "Markdown":
        markdown_text = ocr_engine.format_as_markdown(ocr_results, page_numbers=True)
        st.markdown("### Markdown Output")
        st.text_area("Markdown", markdown_text, height=400)
        
        # Download button
        st.download_button(
            label="📥 Download Markdown",
            data=markdown_text,
            file_name="ocr_results.md",
            mime="text/markdown"
        )
    
    elif output_format == "JSON":
        json_text = ocr_engine.format_as_json(ocr_results)
        st.markdown("### JSON Output")
        st.json(json_text)
        
        # Download button
        st.download_button(
            label="📥 Download JSON",
            data=json_text,
            file_name="ocr_results.json",
            mime="application/json"
        )
    
    elif output_format == "Text":
        text_output = ocr_engine.format_as_markdown(ocr_results, page_numbers=False)
        st.markdown("### Plain Text Output")
        st.text_area("Text", text_output, height=400)
        
        # Download button
        st.download_button(
            label="📥 Download Text",
            data=text_output,
            file_name="ocr_results.txt",
            mime="text/plain"
        )
    
    elif output_format == "HTML":
        html_text = ocr_engine.format_as_html(ocr_results)
        st.markdown("### HTML Output")
        st.code(html_text, language="html")
        
        # Download button
        st.download_button(
            label="📥 Download HTML",
            data=html_text,
            file_name="ocr_results.html",
            mime="text/html"
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
                        st.text(block['text'])
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
        initial_sidebar_state="expanded"
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
    st.subheader("📁 File Upload")
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Choose files to process",
        type=list(SUPPORTED_FORMATS.keys()),
        accept_multiple_files=True,
        help=f"Maximum file size: {MAX_FILE_SIZE_MB}MB per file"
    )
    
    # Output format selection
    col1, col2 = st.columns([3, 1])
    with col1:
        output_format = st.selectbox(
            "Output Format",
            options=OUTPUT_FORMATS,
            help="Select the format for OCR results"
        )
    with col2:
        process_button = st.button("🚀 Process Files", type="primary", use_container_width=True)
    
    # Process files when button is clicked
    if process_button and uploaded_files:
        # Create temporary directory
        temp_dir = Path(tempfile.mkdtemp())
        
        try:
            # Process files
            start_time = time.time()
            ocr_results, processed_images = process_uploaded_files(
                uploaded_files, config, temp_dir
            )
            processing_time = time.time() - start_time
            
            # Store results in session state
            st.session_state.ocr_results = ocr_results
            st.session_state.processed_images = processed_images
            st.session_state.processing_complete = True
            
            st.success(f"✅ Processing completed in {processing_time:.2f} seconds!")
            
        except Exception as e:
            st.error(f"❌ Error during processing: {str(e)}")
        
        finally:
            # Cleanup temporary directory
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    elif process_button and not uploaded_files:
        st.warning("⚠️ Please upload at least one file to process.")
    
    # Display results if available
    if st.session_state.processing_complete and st.session_state.ocr_results:
        st.divider()
        display_results(
            st.session_state.ocr_results,
            st.session_state.ocr_engine,
            output_format
        )
    
    # Footer
    st.divider()
    st.markdown(
        """
        <div style='text-align: center; color: gray; padding: 20px;'>
        <p>Powered by <a href='https://github.com/PaddlePaddle/PaddleOCR' target='_blank'>PaddleOCR</a> | 
        Built with <a href='https://streamlit.io' target='_blank'>Streamlit</a></p>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()

