"""
Tests for utility functions
"""

from pathlib import Path
from unittest.mock import Mock

import pytest

import utils
from config import MAX_FILE_SIZE_MB


class TestValidateFile:
    """Tests for file validation"""

    def test_validate_valid_pdf(self, temp_dir):
        """Test validation of valid PDF file"""
        file_path = temp_dir / "test.pdf"
        file_path.touch()

        mock_uploaded_file = Mock()
        mock_uploaded_file.name = "test.pdf"
        mock_uploaded_file.size = 1024 * 1024  # 1MB

        is_valid, error_msg = utils.validate_file(file_path, mock_uploaded_file)
        assert is_valid
        assert error_msg is None

    def test_validate_file_too_large(self, temp_dir):
        """Test validation fails for files exceeding size limit"""
        file_path = temp_dir / "large.pdf"
        file_path.touch()

        mock_uploaded_file = Mock()
        mock_uploaded_file.name = "large.pdf"
        mock_uploaded_file.size = (MAX_FILE_SIZE_MB + 1) * 1024 * 1024  # Over limit

        is_valid, error_msg = utils.validate_file(file_path, mock_uploaded_file)
        assert not is_valid
        assert "exceeds maximum allowed size" in error_msg

    def test_validate_unsupported_format(self, temp_dir):
        """Test validation fails for unsupported file format"""
        file_path = temp_dir / "test.xyz"
        file_path.touch()

        mock_uploaded_file = Mock()
        mock_uploaded_file.name = "test.xyz"
        mock_uploaded_file.size = 1024

        is_valid, error_msg = utils.validate_file(file_path, mock_uploaded_file)
        assert not is_valid
        assert "Unsupported file format" in error_msg

    def test_validate_path_traversal(self, temp_dir):
        """Test validation fails for path traversal attempts"""
        file_path = temp_dir / "test.pdf"
        file_path.touch()

        mock_uploaded_file = Mock()
        mock_uploaded_file.name = "../../../etc/passwd"
        mock_uploaded_file.size = 1024

        is_valid, error_msg = utils.validate_file(file_path, mock_uploaded_file)
        assert not is_valid
        assert "path traversal" in error_msg.lower()


class TestSanitizeFilename:
    """Tests for filename sanitization"""

    def test_sanitize_simple_filename(self):
        """Test sanitization of simple filename"""
        result = utils.sanitize_filename("test.pdf")
        assert result == "test.pdf"

    def test_sanitize_filename_with_spaces(self):
        """Test sanitization replaces spaces"""
        result = utils.sanitize_filename("test file.pdf")
        assert result == "test_file.pdf"

    def test_sanitize_filename_with_special_chars(self):
        """Test sanitization removes special characters"""
        result = utils.sanitize_filename("test@file#.pdf")
        assert result == "test_file_.pdf"

    def test_sanitize_filename_with_path(self):
        """Test sanitization removes path components"""
        result = utils.sanitize_filename("/path/to/test.pdf")
        assert result == "test.pdf"


class TestFormatFileSize:
    """Tests for file size formatting"""

    def test_format_bytes(self):
        """Test formatting bytes"""
        assert utils.format_file_size(500) == "500.0 B"

    def test_format_kilobytes(self):
        """Test formatting kilobytes"""
        assert utils.format_file_size(1024 * 2) == "2.0 KB"

    def test_format_megabytes(self):
        """Test formatting megabytes"""
        assert utils.format_file_size(1024 * 1024 * 5) == "5.0 MB"

    def test_format_gigabytes(self):
        """Test formatting gigabytes"""
        assert utils.format_file_size(1024 * 1024 * 1024 * 2) == "2.0 GB"


class TestComputeFileHash:
    """Tests for file hash computation"""

    def test_compute_hash_same_content(self, temp_dir):
        """Test that same content produces same hash"""
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"

        content = "Test content"
        file1.write_text(content)
        file2.write_text(content)

        hash1 = utils.compute_file_hash(file1)
        hash2 = utils.compute_file_hash(file2)

        assert hash1 == hash2

    def test_compute_hash_different_content(self, temp_dir):
        """Test that different content produces different hash"""
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"

        file1.write_text("Content 1")
        file2.write_text("Content 2")

        hash1 = utils.compute_file_hash(file1)
        hash2 = utils.compute_file_hash(file2)

        assert hash1 != hash2
