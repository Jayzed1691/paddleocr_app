"""
Configuration settings for PaddleOCR Streamlit Application
"""

# Supported file formats
SUPPORTED_FORMATS = {
    '.pdf': 'PDF Documents',
    '.docx': 'Word Documents',
    '.txt': 'Text Files',
    '.png': 'PNG Images',
    '.jpg': 'JPEG Images',
    '.jpeg': 'JPEG Images'
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

# Document processing constants
PDF_DPI = 300  # DPI for PDF to image conversion
TEXT_TO_IMAGE_WIDTH = 800  # Image width for text rendering
TEXT_TO_IMAGE_FONT_SIZE = 16  # Font size for text rendering
TEXT_TO_IMAGE_LINE_SPACING = 4  # Additional spacing between lines
TEXT_TO_IMAGE_MIN_HEIGHT = 400  # Minimum image height
TEXT_TO_IMAGE_MARGIN = 20  # Margin around text
TEXT_LINE_WRAP_LENGTH = 80  # Character limit before wrapping

# UI Constants
TEXTAREA_HEIGHT = 400  # Height of text area widgets
PROGRESS_UPDATE_INTERVAL = 0.1  # Seconds between progress updates

# Default font paths by platform
FONT_PATHS = {
    'linux': [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
        '/usr/share/fonts/TTF/DejaVuSans.ttf'
    ],
    'darwin': [  # macOS
        '/System/Library/Fonts/Helvetica.ttc',
        '/Library/Fonts/Arial.ttf'
    ],
    'windows': [
        'C:\\Windows\\Fonts\\arial.ttf',
        'C:\\Windows\\Fonts\\calibri.ttf'
    ]
}

# Logging configuration
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
LOG_LEVEL = 'INFO'

# Cache configuration
CACHE_TTL = 3600  # Cache time-to-live in seconds (1 hour)
MAX_CACHE_SIZE = 100  # Maximum number of cached results

# OCR configuration that requires reinitialization
OCR_REINIT_PARAMS = {
    'lang', 'use_angle_cls', 'use_gpu', 'det_model_dir',
    'rec_model_dir', 'cls_model_dir'
}

# OCR Settings Presets
OCR_PRESETS = {
    'Fast': {
        'name': 'Fast Processing',
        'description': 'Optimized for speed with acceptable accuracy',
        'config': {
            'use_textline_orientation': False,
            'text_det_thresh': 0.4,
            'text_det_box_thresh': 0.7,
            'text_rec_score_thresh': 0.3,
            'text_recognition_batch_size': 12,
            'use_doc_orientation_classify': False,
            'use_doc_unwarping': False,
            'return_word_box': False
        }
    },
    'Balanced': {
        'name': 'Balanced (Recommended)',
        'description': 'Good balance between speed and accuracy',
        'config': {
            'use_textline_orientation': True,
            'text_det_thresh': 0.3,
            'text_det_box_thresh': 0.6,
            'text_rec_score_thresh': 0.5,
            'text_recognition_batch_size': 6,
            'use_doc_orientation_classify': False,
            'use_doc_unwarping': False,
            'return_word_box': False
        }
    },
    'High Quality': {
        'name': 'High Quality',
        'description': 'Maximum accuracy, slower processing',
        'config': {
            'use_textline_orientation': True,
            'text_det_thresh': 0.2,
            'text_det_box_thresh': 0.5,
            'text_rec_score_thresh': 0.6,
            'text_recognition_batch_size': 3,
            'use_doc_orientation_classify': True,
            'use_doc_unwarping': True,
            'return_word_box': True
        }
    },
    'Custom': {
        'name': 'Custom Settings',
        'description': 'Manually configure all parameters',
        'config': {}  # Will use user-defined settings
    }
}

