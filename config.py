"""
Configuration settings for PaddleOCR Streamlit Application
"""

# Supported file formats
SUPPORTED_FORMATS = {
    'pdf': 'PDF Documents',
    'docx': 'Word Documents',
    'txt': 'Text Files',
    'png': 'PNG Images',
    'jpg': 'JPEG Images',
    'jpeg': 'JPEG Images'
}

# PaddleOCR default settings
DEFAULT_OCR_CONFIG = {
    'use_angle_cls': True,
    'lang': 'en',
    'use_gpu': False,
    'show_log': False
}

# Layout detection merge modes
LAYOUT_MERGE_MODES = ['large', 'small', 'union']

# Device options
DEVICE_OPTIONS = ['cpu', 'gpu:0', 'npu:0', 'xpu:0', 'mlu:0', 'dcu:0']

# Precision options
PRECISION_OPTIONS = ['fp32', 'fp16']

# Language options for PaddleOCR
LANGUAGE_OPTIONS = {
    'en': 'English',
    'ch': 'Chinese & English',
    'fr': 'French',
    'german': 'German',
    'korean': 'Korean',
    'japan': 'Japanese',
    'chinese_cht': 'Traditional Chinese',
    'ta': 'Tamil',
    'te': 'Telugu',
    'ka': 'Kannada',
    'latin': 'Latin',
    'arabic': 'Arabic',
    'cyrillic': 'Cyrillic',
    'devanagari': 'Devanagari'
}

# Output format options
OUTPUT_FORMATS = ['Markdown', 'JSON', 'Text', 'HTML']

# Maximum file size (in MB)
MAX_FILE_SIZE_MB = 50

