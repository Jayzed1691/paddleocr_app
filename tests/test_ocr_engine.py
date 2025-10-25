"""
Tests for OCR engine
"""

from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest
from PIL import Image

from ocr_engine import OCREngine


class TestOCREngine:
    """Tests for OCREngine class"""

    @patch("ocr_engine.PaddleOCR")
    def test_init_default_config(self, mock_paddle):
        """Test initialization with default configuration"""
        engine = OCREngine()

        assert engine.config == {}
        assert engine.ocr is not None
        mock_paddle.assert_called_once()

    @patch("ocr_engine.PaddleOCR")
    def test_init_custom_config(self, mock_paddle):
        """Test initialization with custom configuration"""
        config = {"lang": "ch", "use_angle_cls": False}
        engine = OCREngine(config)

        assert engine.config == config
        mock_paddle.assert_called_once()

    @patch("ocr_engine.PaddleOCR")
    def test_update_config_no_reinit(self, mock_paddle):
        """Test updating config without reinitialization"""
        engine = OCREngine({"lang": "en"})
        initial_call_count = mock_paddle.call_count

        # Update parameter not in OCR_REINIT_PARAMS or RUNTIME_PARAMS
        # (custom parameters that don't affect OCR behavior)
        engine.update_config({"custom_param": "value"})

        # Should not reinitialize
        assert mock_paddle.call_count == initial_call_count

    @patch("ocr_engine.PaddleOCR")
    def test_update_config_with_reinit(self, mock_paddle):
        """Test updating config requiring reinitialization"""
        engine = OCREngine({"lang": "en"})
        initial_call_count = mock_paddle.call_count

        # Update critical parameter (lang requires reinit)
        engine.update_config({"lang": "ch"})

        # Should reinitialize
        assert mock_paddle.call_count > initial_call_count

    @patch("ocr_engine.PaddleOCR")
    def test_update_config_runtime_param_reinit(self, mock_paddle):
        """Test that runtime parameters now trigger reinitialization (bug fix)"""
        engine = OCREngine({"lang": "en"})
        initial_call_count = mock_paddle.call_count

        # Update runtime parameter (text_det_thresh now requires reinit after bug fix)
        engine.update_config({"text_det_thresh": 0.5})

        # Should reinitialize (this is the bug fix - runtime params were being ignored)
        assert mock_paddle.call_count > initial_call_count

    def test_extract_text(self, mock_ocr_result):
        """Test text extraction from OCR result"""
        engine = OCREngine.__new__(OCREngine)  # Create without __init__
        engine.ocr = Mock()

        text = engine.extract_text(mock_ocr_result)

        assert "Test text" in text
        assert "Another line" in text

    def test_extract_text_empty_result(self, empty_ocr_result):
        """Test text extraction from empty result"""
        engine = OCREngine.__new__(OCREngine)
        engine.ocr = Mock()

        text = engine.extract_text(empty_ocr_result)

        assert text == ""

    def test_extract_structured_data(self, mock_ocr_result):
        """Test structured data extraction"""
        engine = OCREngine.__new__(OCREngine)
        engine.ocr = Mock()

        structured = engine.extract_structured_data(mock_ocr_result)

        assert len(structured) == 2
        assert structured[0]["text"] == "Test text"
        assert structured[0]["confidence"] == 0.95
        assert "bbox" in structured[0]

    def test_extract_structured_data_empty(self, empty_ocr_result):
        """Test structured data extraction from empty result"""
        engine = OCREngine.__new__(OCREngine)
        engine.ocr = Mock()

        structured = engine.extract_structured_data(empty_ocr_result)

        assert structured == []

    def test_format_as_markdown_with_page_numbers(self, mock_ocr_result):
        """Test Markdown formatting with page numbers"""
        engine = OCREngine.__new__(OCREngine)
        engine.ocr = Mock()

        markdown = engine.format_as_markdown([mock_ocr_result], page_numbers=True)

        assert "## Page 1" in markdown
        assert "Test text" in markdown

    def test_format_as_markdown_without_page_numbers(self, mock_ocr_result):
        """Test Markdown formatting without page numbers"""
        engine = OCREngine.__new__(OCREngine)
        engine.ocr = Mock()

        markdown = engine.format_as_markdown([mock_ocr_result], page_numbers=False)

        assert "## Page" not in markdown
        assert "Test text" in markdown

    def test_format_as_json(self, mock_ocr_result):
        """Test JSON formatting"""
        engine = OCREngine.__new__(OCREngine)
        engine.ocr = Mock()

        json_str = engine.format_as_json([mock_ocr_result])

        assert '"total_pages": 1' in json_str
        assert '"text"' in json_str
        assert '"confidence"' in json_str

    def test_format_as_html(self, mock_ocr_result):
        """Test HTML formatting"""
        engine = OCREngine.__new__(OCREngine)
        engine.ocr = Mock()

        html = engine.format_as_html([mock_ocr_result])

        assert "<!DOCTYPE html>" in html
        assert "Test text" in html
        assert "Page 1" in html

    def test_get_statistics(self, mock_ocr_result):
        """Test statistics computation"""
        engine = OCREngine.__new__(OCREngine)
        engine.ocr = Mock()

        stats = engine.get_statistics([mock_ocr_result])

        assert stats["total_pages"] == 1
        assert stats["total_text_blocks"] == 2
        assert stats["total_characters"] > 0
        assert 0 <= stats["average_confidence"] <= 1

    def test_get_statistics_empty(self, empty_ocr_result):
        """Test statistics from empty result"""
        engine = OCREngine.__new__(OCREngine)
        engine.ocr = Mock()

        stats = engine.get_statistics([empty_ocr_result])

        assert stats["total_pages"] == 1
        assert stats["total_text_blocks"] == 0
        assert stats["total_characters"] == 0
        assert stats["average_confidence"] == 0.0

    @patch("ocr_engine.PaddleOCR")
    def test_process_image_pil(self, mock_paddle):
        """Test processing PIL Image"""
        mock_ocr_instance = Mock()
        mock_ocr_instance.ocr.return_value = [[]]
        mock_paddle.return_value = mock_ocr_instance

        engine = OCREngine()
        img = Image.new("RGB", (100, 100))

        result = engine.process_image(img)

        assert result is not None
        mock_ocr_instance.ocr.assert_called_once()

    @patch("ocr_engine.PaddleOCR")
    def test_process_image_numpy(self, mock_paddle):
        """Test processing numpy array"""
        mock_ocr_instance = Mock()
        mock_ocr_instance.ocr.return_value = [[]]
        mock_paddle.return_value = mock_ocr_instance

        engine = OCREngine()
        img_array = np.zeros((100, 100, 3), dtype=np.uint8)

        result = engine.process_image(img_array)

        assert result is not None
        mock_ocr_instance.ocr.assert_called_once()

    @patch("ocr_engine.PaddleOCR")
    def test_process_image_invalid_type(self, mock_paddle):
        """Test processing invalid image type raises error"""
        engine = OCREngine()

        with pytest.raises(ValueError, match="Unsupported image type"):
            engine.process_image("not an image")

    @patch("ocr_engine.PaddleOCR")
    def test_process_images_batch(self, mock_paddle):
        """Test batch processing of images"""
        mock_ocr_instance = Mock()
        mock_ocr_instance.ocr.return_value = [[]]
        mock_paddle.return_value = mock_ocr_instance

        engine = OCREngine()
        images = [Image.new("RGB", (100, 100)), Image.new("RGB", (100, 100))]

        results = engine.process_images(images)

        assert len(results) == 2
        assert mock_ocr_instance.ocr.call_count == 2
