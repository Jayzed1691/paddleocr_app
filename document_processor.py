"""
Document processing utilities for converting various file formats to images
"""

import logging
import os
import platform
import sys
from pathlib import Path
from typing import List, Optional, Union

import numpy as np
from PIL import Image

from config import (
    FONT_PATHS,
    PDF_DPI,
    TEXT_LINE_WRAP_LENGTH,
    TEXT_TO_IMAGE_FONT_SIZE,
    TEXT_TO_IMAGE_LINE_SPACING,
    TEXT_TO_IMAGE_MARGIN,
    TEXT_TO_IMAGE_MIN_HEIGHT,
    TEXT_TO_IMAGE_WIDTH,
)

# Set up logging
logger = logging.getLogger(__name__)

try:
    from pdf2image import convert_from_bytes, convert_from_path
except ImportError:
    convert_from_path = None
    convert_from_bytes = None

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    from docx import Document
    from docx.oxml.table import CT_Tbl
    from docx.oxml.text.paragraph import CT_P
    from docx.table import Table, _Cell
    from docx.text.paragraph import Paragraph
except ImportError:
    Document = None


class DocumentProcessor:
    """Process different document formats and convert to images for OCR"""

    def __init__(self):
        self.supported_formats = [".pdf", ".docx", ".txt", ".png", ".jpg", ".jpeg"]
        self._font_cache: Optional[any] = None

    def _get_font(self, font_size: int):
        """
        Get a font for the current platform

        Args:
            font_size: Size of the font

        Returns:
            ImageFont object
        """
        from PIL import ImageFont

        if self._font_cache is not None:
            return self._font_cache

        # Determine platform
        system = platform.system().lower()
        if system == "darwin":
            platform_key = "darwin"
        elif system == "windows":
            platform_key = "windows"
        else:
            platform_key = "linux"

        # Try platform-specific font paths
        font_paths = FONT_PATHS.get(platform_key, FONT_PATHS["linux"])

        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    logger.info(f"Loading font from: {font_path}")
                    self._font_cache = ImageFont.truetype(font_path, font_size)
                    return self._font_cache
                except Exception as e:
                    logger.warning(f"Failed to load font from {font_path}: {e}")
                    continue

        # Fallback to default font
        logger.warning("No system fonts found, using default font")
        self._font_cache = ImageFont.load_default()
        return self._font_cache

    def process_file(self, file_path: Union[str, Path]) -> List[Image.Image]:
        """
        Process a file and return a list of PIL Images

        Args:
            file_path: Path to the file to process

        Returns:
            List of PIL Image objects
        """
        file_path = Path(file_path)
        extension = file_path.suffix.lower()

        if extension == ".pdf":
            return self.process_pdf(file_path)
        elif extension == ".docx":
            return self.process_docx(file_path)
        elif extension == ".txt":
            return self.process_txt(file_path)
        elif extension in [".png", ".jpg", ".jpeg"]:
            return self.process_image(file_path)
        else:
            raise ValueError(f"Unsupported file format: {extension}")

    def process_pdf(self, pdf_path: Union[str, Path]) -> List[Image.Image]:
        """Convert PDF pages to images"""
        if convert_from_path is None:
            raise ImportError(
                "pdf2image is required for PDF processing. Install with: pip install pdf2image"
            )

        try:
            logger.info(f"Converting PDF to images: {pdf_path}")
            # Convert PDF to images using configured DPI
            images = convert_from_path(str(pdf_path), dpi=PDF_DPI)
            logger.info(f"Successfully converted PDF to {len(images)} images")
            return images
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
            raise RuntimeError(f"Error processing PDF: {str(e)}")

    def process_docx(self, docx_path: Union[str, Path]) -> List[Image.Image]:
        """
        Convert DOCX to image by extracting text and rendering
        Note: This creates a simple text-based image representation
        """
        if Document is None:
            raise ImportError(
                "python-docx is required for DOCX processing. Install with: pip install python-docx"
            )

        try:
            logger.info(f"Processing DOCX file: {docx_path}")
            doc = Document(str(docx_path))

            # Extract all text from document
            full_text = []
            for element in doc.element.body:
                if isinstance(element, CT_P):
                    paragraph = Paragraph(element, doc)
                    if paragraph.text.strip():
                        full_text.append(paragraph.text)
                elif isinstance(element, CT_Tbl):
                    table = Table(element, doc)
                    for row in table.rows:
                        row_text = " | ".join(cell.text for cell in row.cells)
                        if row_text.strip():
                            full_text.append(row_text)

            if not full_text:
                logger.warning(f"No text content found in DOCX: {docx_path}")
                full_text = ["[Empty document]"]

            # Create image from text
            text_content = "\n".join(full_text)
            logger.info(f"Successfully extracted {len(full_text)} paragraphs/tables from DOCX")
            return [self._text_to_image(text_content)]

        except Exception as e:
            logger.error(f"Error processing DOCX {docx_path}: {str(e)}")
            raise RuntimeError(f"Error processing DOCX: {str(e)}")

    def process_txt(self, txt_path: Union[str, Path]) -> List[Image.Image]:
        """Convert text file to image"""
        try:
            logger.info(f"Processing TXT file: {txt_path}")
            with open(txt_path, "r", encoding="utf-8") as f:
                text_content = f.read()

            if not text_content.strip():
                logger.warning(f"Empty text file: {txt_path}")
                text_content = "[Empty file]"

            logger.info(f"Successfully read {len(text_content)} characters from TXT")
            return [self._text_to_image(text_content)]

        except UnicodeDecodeError as e:
            logger.error(f"Unicode decode error for {txt_path}: {str(e)}")
            # Try with different encoding
            try:
                with open(txt_path, "r", encoding="latin-1") as f:
                    text_content = f.read()
                logger.info(f"Successfully read file with latin-1 encoding")
                return [self._text_to_image(text_content)]
            except Exception as e2:
                logger.error(f"Failed to read with alternative encoding: {str(e2)}")
                raise RuntimeError(f"Error processing TXT (encoding issue): {str(e)}")
        except Exception as e:
            logger.error(f"Error processing TXT {txt_path}: {str(e)}")
            raise RuntimeError(f"Error processing TXT: {str(e)}")

    def process_image(self, image_path: Union[str, Path]) -> List[Image.Image]:
        """Load and return image file"""
        try:
            logger.info(f"Loading image file: {image_path}")
            img = Image.open(str(image_path))

            # Validate image
            if img.size[0] == 0 or img.size[1] == 0:
                raise ValueError("Image has zero dimensions")

            # Convert to RGB if necessary
            if img.mode != "RGB":
                logger.info(f"Converting image from {img.mode} to RGB")
                img = img.convert("RGB")

            logger.info(f"Successfully loaded image: {img.size[0]}x{img.size[1]}")
            return [img]
        except FileNotFoundError:
            logger.error(f"Image file not found: {image_path}")
            raise RuntimeError(f"Image file not found: {image_path}")
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {str(e)}")
            raise RuntimeError(f"Error processing image: {str(e)}")

    def _text_to_image(
        self, text: str, width: int = TEXT_TO_IMAGE_WIDTH, font_size: int = TEXT_TO_IMAGE_FONT_SIZE
    ) -> Image.Image:
        """
        Convert text to a PIL Image

        Args:
            text: Text content to convert
            width: Image width in pixels
            font_size: Font size for text rendering

        Returns:
            PIL Image object
        """
        from PIL import ImageDraw

        # Calculate image height based on text length
        lines = text.split("\n")
        line_height = font_size + TEXT_TO_IMAGE_LINE_SPACING
        height = max(
            len(lines) * line_height + (TEXT_TO_IMAGE_MARGIN * 2), TEXT_TO_IMAGE_MIN_HEIGHT
        )

        # Create white background image
        img = Image.new("RGB", (width, height), color="white")
        draw = ImageDraw.Draw(img)

        # Get font using cross-platform method
        font = self._get_font(font_size)

        # Draw text on image
        y_position = TEXT_TO_IMAGE_MARGIN
        for line in lines:
            # Wrap long lines
            if len(line) > TEXT_LINE_WRAP_LENGTH:
                wrapped_lines = [
                    line[i : i + TEXT_LINE_WRAP_LENGTH]
                    for i in range(0, len(line), TEXT_LINE_WRAP_LENGTH)
                ]
                for wrapped_line in wrapped_lines:
                    draw.text(
                        (TEXT_TO_IMAGE_MARGIN, y_position), wrapped_line, fill="black", font=font
                    )
                    y_position += line_height
            else:
                draw.text((TEXT_TO_IMAGE_MARGIN, y_position), line, fill="black", font=font)
                y_position += line_height

        return img

    def save_images(
        self, images: List[Image.Image], output_dir: Union[str, Path], prefix: str = "page"
    ) -> List[Path]:
        """
        Save images to directory

        Args:
            images: List of PIL Images
            output_dir: Directory to save images
            prefix: Prefix for image filenames

        Returns:
            List of saved file paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        saved_paths = []
        for i, img in enumerate(images, 1):
            output_path = output_dir / f"{prefix}_{i:03d}.png"
            img.save(output_path, "PNG")
            saved_paths.append(output_path)

        return saved_paths
