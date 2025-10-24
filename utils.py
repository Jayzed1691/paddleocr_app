"""
Utility functions for the PaddleOCR application
"""

import os
import hashlib
import logging
from pathlib import Path
from typing import Optional, Tuple
import magic

from config import MAX_FILE_SIZE_MB, SUPPORTED_FORMATS

logger = logging.getLogger(__name__)


def validate_file(file_path: Path, uploaded_file: any) -> Tuple[bool, Optional[str]]:
    """
    Validate uploaded file for security and format compliance

    Args:
        file_path: Path to the uploaded file
        uploaded_file: Streamlit UploadedFile object

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check file size
    file_size_mb = uploaded_file.size / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        return False, f"File size ({file_size_mb:.1f}MB) exceeds maximum allowed size ({MAX_FILE_SIZE_MB}MB)"

    # Check file extension
    file_extension = file_path.suffix.lower()
    if file_extension not in SUPPORTED_FORMATS:
        return False, f"Unsupported file format: {file_extension}. Supported formats: {', '.join(SUPPORTED_FORMATS.keys())}"

    # Validate file name (no path traversal)
    if '..' in uploaded_file.name or '/' in uploaded_file.name or '\\' in uploaded_file.name:
        return False, "Invalid file name (potential path traversal)"

    # Additional validation: Check MIME type matches extension
    try:
        if os.path.exists(file_path):
            mime_type = get_mime_type(file_path)
            if not is_mime_type_valid(mime_type, file_extension):
                logger.warning(f"MIME type mismatch: {mime_type} for extension {file_extension}")
                # Don't fail, just log warning as magic library may not be available
    except Exception as e:
        logger.warning(f"Could not validate MIME type: {e}")

    return True, None


def get_mime_type(file_path: Path) -> str:
    """
    Get MIME type of a file

    Args:
        file_path: Path to the file

    Returns:
        MIME type string
    """
    try:
        # Try using python-magic if available
        mime = magic.Magic(mime=True)
        return mime.from_file(str(file_path))
    except (ImportError, AttributeError):
        # Fallback to simple extension-based detection
        extension_to_mime = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg'
        }
        return extension_to_mime.get(file_path.suffix.lower(), 'application/octet-stream')


def is_mime_type_valid(mime_type: str, file_extension: str) -> bool:
    """
    Check if MIME type matches expected type for file extension

    Args:
        mime_type: Detected MIME type
        file_extension: File extension (with dot)

    Returns:
        True if valid, False otherwise
    """
    valid_mimes = {
        '.pdf': ['application/pdf'],
        '.docx': [
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/zip'  # DOCX files are zip archives
        ],
        '.txt': ['text/plain', 'text/x-c', 'application/octet-stream'],  # Text files can have various MIME types
        '.png': ['image/png'],
        '.jpg': ['image/jpeg'],
        '.jpeg': ['image/jpeg']
    }

    expected_mimes = valid_mimes.get(file_extension.lower(), [])
    return mime_type in expected_mimes if expected_mimes else True


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent security issues

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove any directory components
    filename = os.path.basename(filename)

    # Remove any non-alphanumeric characters except dots, dashes, and underscores
    safe_chars = []
    for char in filename:
        if char.isalnum() or char in '.-_':
            safe_chars.append(char)
        else:
            safe_chars.append('_')

    return ''.join(safe_chars)


def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA256 hash of a file

    Args:
        file_path: Path to the file

    Returns:
        Hexadecimal hash string
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"
