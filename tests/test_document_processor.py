"""
Tests for document processor
"""

from pathlib import Path

import pytest
from PIL import Image

from document_processor import DocumentProcessor


class TestDocumentProcessor:
    """Tests for DocumentProcessor class"""

    def test_init(self):
        """Test processor initialization"""
        processor = DocumentProcessor()
        assert processor.supported_formats == [".pdf", ".docx", ".txt", ".png", ".jpg", ".jpeg"]

    def test_process_txt_file(self, sample_text_file):
        """Test processing text file"""
        processor = DocumentProcessor()
        images = processor.process_txt(sample_text_file)

        assert len(images) == 1
        assert isinstance(images[0], Image.Image)
        assert images[0].mode == "RGB"

    def test_process_empty_txt_file(self, temp_dir):
        """Test processing empty text file"""
        file_path = temp_dir / "empty.txt"
        file_path.write_text("")

        processor = DocumentProcessor()
        images = processor.process_txt(file_path)

        assert len(images) == 1
        assert isinstance(images[0], Image.Image)

    def test_process_image_file(self, temp_dir, sample_image):
        """Test processing image file"""
        file_path = temp_dir / "test.png"
        sample_image.save(file_path)

        processor = DocumentProcessor()
        images = processor.process_image(file_path)

        assert len(images) == 1
        assert isinstance(images[0], Image.Image)
        assert images[0].mode == "RGB"

    def test_process_image_converts_to_rgb(self, temp_dir):
        """Test that non-RGB images are converted"""
        file_path = temp_dir / "test_grayscale.png"
        grayscale_img = Image.new("L", (100, 100), color=128)
        grayscale_img.save(file_path)

        processor = DocumentProcessor()
        images = processor.process_image(file_path)

        assert images[0].mode == "RGB"

    def test_process_nonexistent_file(self, temp_dir):
        """Test processing non-existent file raises error"""
        file_path = temp_dir / "nonexistent.png"

        processor = DocumentProcessor()
        with pytest.raises(RuntimeError):
            processor.process_image(file_path)

    def test_process_file_unsupported_format(self, temp_dir):
        """Test processing unsupported format raises error"""
        file_path = temp_dir / "test.xyz"
        file_path.touch()

        processor = DocumentProcessor()
        with pytest.raises(ValueError, match="Unsupported file format"):
            processor.process_file(file_path)

    def test_save_images(self, temp_dir, sample_image):
        """Test saving images to directory"""
        processor = DocumentProcessor()
        output_dir = temp_dir / "output"

        images = [sample_image, sample_image]
        saved_paths = processor.save_images(images, output_dir, prefix="test")

        assert len(saved_paths) == 2
        assert all(p.exists() for p in saved_paths)
        assert all(p.suffix == ".png" for p in saved_paths)

    def test_text_to_image_basic(self):
        """Test text to image conversion"""
        processor = DocumentProcessor()
        text = "Test text content"

        image = processor._text_to_image(text)

        assert isinstance(image, Image.Image)
        assert image.mode == "RGB"
        assert image.size[0] > 0
        assert image.size[1] > 0

    def test_text_to_image_long_text(self):
        """Test text to image with long text"""
        processor = DocumentProcessor()
        text = "A" * 200  # Long line that should wrap

        image = processor._text_to_image(text)

        assert isinstance(image, Image.Image)
        # Image should be tall enough for wrapped lines
        assert image.size[1] > 50

    def test_get_font_caching(self):
        """Test that font is cached after first retrieval"""
        processor = DocumentProcessor()

        font1 = processor._get_font(16)
        font2 = processor._get_font(16)

        assert font1 is font2  # Should be same object (cached)
