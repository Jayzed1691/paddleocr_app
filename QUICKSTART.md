# Quick Start Guide

## Installation (5 minutes)

```bash
# 1. Navigate to the application directory
cd paddleocr_app

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Install poppler for PDF support
# Ubuntu/Debian:
sudo apt-get install poppler-utils

# macOS:
brew install poppler
```

## Running the Application (1 minute)

```bash
# Start the Streamlit application
streamlit run app.py
```

The application will automatically open in your browser at `http://localhost:8501`

## Basic Usage (2 minutes)

### Step 1: Configure Settings (Optional)
- In the left sidebar, select your language (default: English)
- Adjust detection and recognition thresholds if needed
- Default settings work well for most documents

### Step 2: Upload Files
- Click "Browse files" button
- Select PDF, DOCX, TXT, or image files
- You can upload multiple files at once

### Step 3: Select Output Format
- Choose from: Markdown, JSON, Text, or HTML
- Markdown is recommended for readable output

### Step 4: Process
- Click the "🚀 Process Files" button
- Wait for processing to complete
- View results and download if needed

## Example: Processing a PDF

1. **Upload**: Click "Browse files" and select a PDF document
2. **Configure**: Leave default settings or adjust as needed
3. **Process**: Click "🚀 Process Files"
4. **Results**: View extracted text, statistics, and confidence scores
5. **Download**: Click "📥 Download Markdown" to save results

## Tips for Best Results

✅ **For high accuracy:**
- Use clear, high-resolution images
- Enable "Document Unwarping" for distorted images
- Lower the detection threshold to catch more text

✅ **For faster processing:**
- Increase recognition batch size
- Process fewer files at once
- Use default thresholds

✅ **For multi-language documents:**
- Select the appropriate language in sidebar
- Use 'ch' for Chinese & English mixed documents

## Common Use Cases

### Use Case 1: Extract Text from PDF
1. Upload PDF file
2. Select "Text" output format
3. Process and download plain text

### Use Case 2: Convert Document to Markdown
1. Upload PDF or DOCX file
2. Select "Markdown" output format
3. Process and get formatted markdown with page numbers

### Use Case 3: Get Structured Data
1. Upload any supported file
2. Select "JSON" output format
3. Process and get structured data with bounding boxes and confidence scores

### Use Case 4: Batch Processing
1. Upload multiple files at once
2. Configure settings once
3. Process all files together
4. Results are combined in output

## Keyboard Shortcuts

- `Ctrl+R` or `Cmd+R`: Refresh the application
- `Ctrl+Shift+R` or `Cmd+Shift+R`: Hard refresh (clear cache)

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore advanced settings in the sidebar
- Try different output formats
- Experiment with threshold settings for your specific documents

## Need Help?

Check the [Troubleshooting](README.md#troubleshooting) section in README.md

