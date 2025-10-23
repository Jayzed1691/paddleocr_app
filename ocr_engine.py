"""
PaddleOCR Engine wrapper with full feature support
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Union, Optional
from PIL import Image
import numpy as np

from paddleocr import PaddleOCR


class OCREngine:
    """
    Wrapper for PaddleOCR with comprehensive feature support
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize OCR Engine
        
        Args:
            config: Configuration dictionary for PaddleOCR
        """
        self.config = config or {}
        self.ocr = None
        self._initialize_ocr()
    
    def _initialize_ocr(self):
        """Initialize PaddleOCR instance with configuration"""
        # Default configuration for PaddleOCR 3.x
        default_config = {
            'lang': 'en',
        }
        
        # Merge with user config
        final_config = {**default_config, **self.config}
        
        # Initialize PaddleOCR
        self.ocr = PaddleOCR(**final_config)
    
    def update_config(self, new_config: Dict[str, Any]):
        """
        Update OCR configuration and reinitialize
        
        Args:
            new_config: New configuration parameters
        """
        self.config.update(new_config)
        self._initialize_ocr()
    
    def process_image(self, image: Union[str, Path, Image.Image, np.ndarray]) -> List[Any]:
        """
        Process a single image with OCR
        
        Args:
            image: Image path, PIL Image, or numpy array
            
        Returns:
            OCR results from PaddleOCR
        """
        if isinstance(image, (str, Path)):
            image_input = str(image)
        elif isinstance(image, Image.Image):
            # Convert PIL Image to numpy array
            image_input = np.array(image)
        elif isinstance(image, np.ndarray):
            image_input = image
        else:
            raise ValueError(f"Unsupported image type: {type(image)}")
        
        # Run OCR
        result = self.ocr.ocr(image_input, cls=self.config.get('use_angle_cls', True))
        return result
    
    def process_images(self, images: List[Union[str, Path, Image.Image, np.ndarray]]) -> List[List[Any]]:
        """
        Process multiple images with OCR
        
        Args:
            images: List of images (paths, PIL Images, or numpy arrays)
            
        Returns:
            List of OCR results for each image
        """
        results = []
        for image in images:
            result = self.process_image(image)
            results.append(result)
        return results
    
    def extract_text(self, ocr_result: List[Any]) -> str:
        """
        Extract plain text from OCR result
        
        Args:
            ocr_result: OCR result from PaddleOCR
            
        Returns:
            Extracted text as string
        """
        if not ocr_result or ocr_result[0] is None:
            return ""
        
        text_lines = []
        for line in ocr_result[0]:
            if line and len(line) >= 2:
                text = line[1][0]  # Extract text from (text, confidence) tuple
                text_lines.append(text)
        
        return '\n'.join(text_lines)
    
    def extract_structured_data(self, ocr_result: List[Any]) -> List[Dict[str, Any]]:
        """
        Extract structured data from OCR result including bounding boxes and confidence
        
        Args:
            ocr_result: OCR result from PaddleOCR
            
        Returns:
            List of dictionaries with text, bounding box, and confidence
        """
        if not ocr_result or ocr_result[0] is None:
            return []
        
        structured_data = []
        for line in ocr_result[0]:
            if line and len(line) >= 2:
                bbox = line[0]  # Bounding box coordinates
                text_info = line[1]  # (text, confidence)
                
                structured_data.append({
                    'text': text_info[0],
                    'confidence': float(text_info[1]),
                    'bbox': [[int(coord) for coord in point] for point in bbox]
                })
        
        return structured_data
    
    def format_as_markdown(self, ocr_results: List[List[Any]], page_numbers: bool = True) -> str:
        """
        Format OCR results as Markdown
        
        Args:
            ocr_results: List of OCR results from multiple pages
            page_numbers: Whether to include page numbers
            
        Returns:
            Formatted Markdown string
        """
        markdown_parts = []
        
        for i, result in enumerate(ocr_results, 1):
            if page_numbers:
                markdown_parts.append(f"## Page {i}\n")
            
            text = self.extract_text(result)
            if text:
                markdown_parts.append(text)
                markdown_parts.append("\n")
        
        return '\n'.join(markdown_parts)
    
    def format_as_json(self, ocr_results: List[List[Any]]) -> str:
        """
        Format OCR results as JSON
        
        Args:
            ocr_results: List of OCR results from multiple pages
            
        Returns:
            JSON string
        """
        json_data = {
            'total_pages': len(ocr_results),
            'pages': []
        }
        
        for i, result in enumerate(ocr_results, 1):
            page_data = {
                'page_number': i,
                'text_blocks': self.extract_structured_data(result),
                'full_text': self.extract_text(result)
            }
            json_data['pages'].append(page_data)
        
        return json.dumps(json_data, indent=2, ensure_ascii=False)
    
    def format_as_html(self, ocr_results: List[List[Any]]) -> str:
        """
        Format OCR results as HTML
        
        Args:
            ocr_results: List of OCR results from multiple pages
            
        Returns:
            HTML string
        """
        html_parts = [
            '<!DOCTYPE html>',
            '<html>',
            '<head>',
            '<meta charset="UTF-8">',
            '<title>OCR Results</title>',
            '<style>',
            'body { font-family: Arial, sans-serif; margin: 20px; }',
            '.page { margin-bottom: 30px; padding: 20px; border: 1px solid #ccc; }',
            '.page-number { font-size: 18px; font-weight: bold; margin-bottom: 10px; }',
            '.text-block { margin: 5px 0; }',
            '</style>',
            '</head>',
            '<body>',
        ]
        
        for i, result in enumerate(ocr_results, 1):
            html_parts.append(f'<div class="page">')
            html_parts.append(f'<div class="page-number">Page {i}</div>')
            
            text = self.extract_text(result)
            if text:
                for line in text.split('\n'):
                    if line.strip():
                        html_parts.append(f'<div class="text-block">{line}</div>')
            
            html_parts.append('</div>')
        
        html_parts.extend(['</body>', '</html>'])
        return '\n'.join(html_parts)
    
    def get_statistics(self, ocr_results: List[List[Any]]) -> Dict[str, Any]:
        """
        Get statistics from OCR results
        
        Args:
            ocr_results: List of OCR results from multiple pages
            
        Returns:
            Dictionary with statistics
        """
        total_text_blocks = 0
        total_characters = 0
        avg_confidence = []
        
        for result in ocr_results:
            structured_data = self.extract_structured_data(result)
            total_text_blocks += len(structured_data)
            
            for block in structured_data:
                total_characters += len(block['text'])
                avg_confidence.append(block['confidence'])
        
        return {
            'total_pages': len(ocr_results),
            'total_text_blocks': total_text_blocks,
            'total_characters': total_characters,
            'average_confidence': sum(avg_confidence) / len(avg_confidence) if avg_confidence else 0.0,
            'min_confidence': min(avg_confidence) if avg_confidence else 0.0,
            'max_confidence': max(avg_confidence) if avg_confidence else 0.0
        }

