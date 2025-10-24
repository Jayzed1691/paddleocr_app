"""
Pytest configuration and fixtures
"""

import pytest
from pathlib import Path
from PIL import Image
import tempfile
import shutil


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_image():
    """Create a sample image for testing"""
    img = Image.new('RGB', (100, 100), color='white')
    return img


@pytest.fixture
def sample_text_file(temp_dir):
    """Create a sample text file"""
    file_path = temp_dir / "test.txt"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("This is a test document.\nWith multiple lines.\n")
    return file_path


@pytest.fixture
def mock_ocr_result():
    """Mock OCR result structure"""
    return [[
        [
            [[10, 10], [100, 10], [100, 30], [10, 30]],
            ('Test text', 0.95)
        ],
        [
            [[10, 40], [100, 40], [100, 60], [10, 60]],
            ('Another line', 0.92)
        ]
    ]]


@pytest.fixture
def empty_ocr_result():
    """Mock empty OCR result"""
    return [[]]
