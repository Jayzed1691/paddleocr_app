# PaddleOCR Streamlit Application

A comprehensive web-based OCR (Optical Character Recognition) application built with PaddleOCR and Streamlit. This application provides a user-friendly interface for performing OCR on PDF, DOCX, TXT, and image files with access to PaddleOCR's complete feature suite.

## Features

### Supported File Formats
- **PDF Documents** - Multi-page PDF processing with automatic page extraction
- **Word Documents (DOCX)** - Text extraction and OCR processing
- **Text Files (TXT)** - Convert text to images for OCR testing
- **Images** - PNG, JPG, JPEG formats

### OCR Capabilities
- **Multi-language Support** - English, Chinese, French, German, Japanese, Korean, Arabic, and more
- **Text Detection** - Automatic detection of text regions in documents
- **Text Recognition** - High-accuracy text recognition with confidence scores
- **Textline Orientation** - Detect and correct text orientation
- **Document Orientation Classification** - Classify and correct document rotation
- **Document Unwarping** - Rectify warped or distorted document images
- **Word-level Bounding Boxes** - Optional word-level detection

### Output Formats
- **Markdown** - Formatted text output with page numbers
- **JSON** - Structured data with bounding boxes and confidence scores
- **Plain Text** - Simple text extraction
- **HTML** - Formatted HTML output

### Advanced Features
- **Batch Processing** - Process multiple files simultaneously
- **Configurable Parameters** - Fine-tune detection and recognition thresholds
- **Statistics Dashboard** - View processing statistics and confidence metrics
- **Detailed View** - Page-by-page results with confidence scores
- **Export Results** - Download results in various formats

## Installation

### Prerequisites
- Python 3.11 or higher
- pip package manager
- (Optional) CUDA-compatible GPU for faster processing

### Step 1: Clone or Download the Application

```bash
# If using git
git clone <repository-url>
cd paddleocr_app

# Or download and extract the zip file
cd paddleocr_app
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- PaddlePaddle (CPU version)
- PaddleOCR
- Streamlit
- Document processing libraries (pdf2image, PyPDF2, python-docx)
- Image processing libraries (Pillow, OpenCV)

### Step 3: Additional System Dependencies

For PDF processing, you may need to install poppler-utils:

**Ubuntu/Debian:**
```bash
sudo apt-get install poppler-utils
```

**macOS:**
```bash
brew install poppler
```

**Windows:**
Download poppler from: https://github.com/oschwartz10612/poppler-windows/releases/

## Usage

### Starting the Application

```bash
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`

### Using the Application

#### 1. Configure OCR Settings (Sidebar)

**Language Settings:**
- Select the primary language for OCR recognition
- Supports 15+ languages including English, Chinese, French, German, etc.

**Detection Settings:**
- **Textline Orientation**: Enable to detect and correct text line rotation
- **Detection Threshold**: Adjust sensitivity for text detection (lower = more sensitive)
- **Box Threshold**: Filter detection boxes by confidence score

**Recognition Settings:**
- **Recognition Score Threshold**: Minimum confidence for accepting recognition results
- **Recognition Batch Size**: Number of text lines to process in parallel (higher = faster but more memory)

**Advanced Settings:**
- **Document Orientation Classification**: Correct rotated documents (0°, 90°, 180°, 270°)
- **Document Unwarping**: Fix warped or distorted document images
- **Return Word Boxes**: Get bounding boxes for individual words

#### 2. Upload Files

- Click "Browse files" or drag and drop files
- Select one or multiple files to process
- Supported formats: PDF, DOCX, TXT, PNG, JPG, JPEG
- Maximum file size: 50MB per file

#### 3. Select Output Format

Choose from:
- **Markdown**: Formatted text with page numbers
- **JSON**: Structured data with metadata
- **Text**: Plain text extraction
- **HTML**: Formatted HTML document

#### 4. Process Files

Click the "🚀 Process Files" button to start OCR processing.

#### 5. View Results

The application displays:
- **Statistics**: Total pages, text blocks, characters, and average confidence
- **Formatted Output**: Results in your selected format
- **Download Button**: Export results to a file
- **Detailed View**: Expandable page-by-page view with confidence scores

## Project Structure

```
paddleocr_app/
├── app.py                 # Main Streamlit application
├── ocr_engine.py         # PaddleOCR wrapper and processing logic
├── document_processor.py # Document-to-image conversion utilities
├── config.py             # Configuration constants and settings
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── test_ocr.py          # Test script for OCR functionality
└── samples/             # Sample files for testing
    └── sample.txt       # Sample text document
```

## Configuration

### Customizing Default Settings

Edit `config.py` to modify:
- Supported file formats
- Language options
- Default OCR parameters
- Maximum file size limits

### PaddleOCR Parameters

The application supports the following PaddleOCR 3.x parameters:

- `lang`: Language for OCR (default: 'en')
- `use_textline_orientation`: Enable text orientation detection
- `text_det_thresh`: Detection threshold (0.0-1.0)
- `text_det_box_thresh`: Box filtering threshold (0.0-1.0)
- `text_det_unclip_ratio`: Detection box expansion ratio
- `text_rec_score_thresh`: Recognition confidence threshold
- `text_recognition_batch_size`: Batch size for recognition
- `use_doc_orientation_classify`: Enable document orientation classification
- `use_doc_unwarping`: Enable document unwarping
- `return_word_box`: Return word-level bounding boxes

## Testing

Run the test script to verify OCR functionality:

```bash
python test_ocr.py
```

This will:
1. Initialize the OCR engine
2. Process the sample text file
3. Extract text and statistics
4. Display results

## Performance Tips

### For Faster Processing:
1. **Increase Batch Size**: Set recognition batch size to 16-32 (requires more memory)
2. **Use GPU**: Install PaddlePaddle GPU version for CUDA acceleration
3. **Adjust Thresholds**: Higher thresholds = faster but may miss some text

### For Better Accuracy:
1. **Lower Detection Threshold**: Detect more text regions (slower)
2. **Enable All Features**: Use orientation classification and unwarping
3. **Reduce Batch Size**: Process fewer items at once for better quality

### Memory Management:
- Process large PDFs in smaller batches
- Close the application between large processing jobs
- Reduce recognition batch size if experiencing memory issues

## Troubleshooting

### Common Issues

**Issue: "pdf2image requires poppler"**
- Solution: Install poppler-utils (see Installation section)

**Issue: "Out of memory" errors**
- Solution: Reduce recognition batch size or process fewer files at once

**Issue: Poor OCR accuracy**
- Solution: Check image quality, adjust detection thresholds, enable document unwarping

**Issue: Application is slow**
- Solution: Reduce file size, increase batch size, or consider GPU version

**Issue: Models downloading on first run**
- Solution: This is normal - PaddleOCR downloads models on first use (one-time only)

## Advanced Usage

### Using the OCR Engine Programmatically

```python
from ocr_engine import OCREngine
from document_processor import DocumentProcessor

# Initialize
config = {'lang': 'en', 'show_log': False}
ocr_engine = OCREngine(config)
doc_processor = DocumentProcessor()

# Process a file
images = doc_processor.process_file('document.pdf')
results = ocr_engine.process_images(images)

# Extract text
text = ocr_engine.format_as_markdown(results)
print(text)

# Get structured data
json_output = ocr_engine.format_as_json(results)

# Get statistics
stats = ocr_engine.get_statistics(results)
print(f"Confidence: {stats['average_confidence']:.2%}")
```

### Custom Document Processing

```python
from document_processor import DocumentProcessor
from PIL import Image

processor = DocumentProcessor()

# Convert document to images
images = processor.process_file('document.docx')

# Save images
saved_paths = processor.save_images(images, 'output_dir', prefix='page')
```

## Technical Details

### PaddleOCR Version
- PaddleOCR: 3.3.0
- PaddlePaddle: 3.0.0-beta1

### Supported Languages
English, Chinese (Simplified & Traditional), French, German, Korean, Japanese, Tamil, Telugu, Kannada, Latin, Arabic, Cyrillic, Devanagari, and more.

### Model Information
PaddleOCR automatically downloads pre-trained models on first use:
- Text detection model
- Text recognition model
- Text orientation classification model (optional)
- Document orientation classification model (optional)

Models are cached locally for subsequent use.

## Credits

- **PaddleOCR**: https://github.com/PaddlePaddle/PaddleOCR
- **Streamlit**: https://streamlit.io
- **PaddlePaddle**: https://www.paddlepaddle.org.cn

## License

This application is provided as-is for educational and commercial use. Please refer to PaddleOCR and PaddlePaddle licenses for the underlying OCR engine.

## Support

For issues related to:
- **This application**: Check the Troubleshooting section or review the code
- **PaddleOCR**: Visit https://github.com/PaddlePaddle/PaddleOCR
- **Streamlit**: Visit https://docs.streamlit.io

## Version History

### Version 1.0.0 (2025-10-23)
- Initial release
- Support for PDF, DOCX, TXT, and image files
- Complete PaddleOCR feature integration
- Multiple output formats
- Configurable OCR parameters
- Statistics and detailed view
- Batch processing support

