"""
Table Recognition and Extraction Module
Specialized for detecting and extracting structured tables from documents
Uses PaddleOCR's table recognition capabilities
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from PIL import Image
import cv2

logger = logging.getLogger(__name__)


class TableRecognizer:
    """
    Advanced table detection and extraction using PaddleOCR
    """

    def __init__(self, lang: str = 'en'):
        """
        Initialize table recognizer

        Args:
            lang: Language for OCR (default: 'en')
        """
        self.lang = lang
        self.table_engine = None
        self._initialize_table_engine()

    def _initialize_table_engine(self):
        """Initialize PaddleOCR table recognition"""
        try:
            from paddleocr import PPStructure

            self.table_engine = PPStructure(
                table=True,
                ocr=True,
                show_log=False,
                lang=self.lang
            )
            logger.info("Table recognition engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize table engine: {e}")
            logger.warning("Table recognition will not be available")
            self.table_engine = None

    def detect_tables(
        self,
        image: Image.Image,
        conf_threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Detect tables in an image

        Args:
            image: PIL Image to analyze
            conf_threshold: Confidence threshold for table detection

        Returns:
            List of detected tables with bounding boxes, cells, and grid data
        """
        if self.table_engine is None:
            logger.warning("Table engine not initialized")
            return []

        try:
            # Convert PIL Image to numpy array
            img_array = np.array(image)

            # Run table detection
            result = self.table_engine(img_array)

            # Filter and process tables
            tables = []
            for item in result:
                if item['type'] == 'table' and item.get('score', 0) >= conf_threshold:
                    # Parse full table structure including grid
                    table_data = self._parse_table_structure(item)

                    # Only include if parsing was successful
                    if 'error' not in table_data:
                        tables.append(table_data)
                    else:
                        # Fallback to basic structure without grid
                        logger.warning(f"Could not parse table structure, using basic data: {table_data.get('error')}")
                        table_data = {
                            'bbox': item['bbox'],
                            'confidence': item.get('score', 0.0),
                            'type': 'table',
                            'html': item.get('res', {}).get('html', ''),
                            'cells': self._extract_cells(item),
                            'rows': self._count_rows(item),
                            'columns': self._count_columns(item),
                            'grid': []  # Empty grid as fallback
                        }
                        tables.append(table_data)

            logger.info(f"Detected {len(tables)} tables in image")
            return tables

        except Exception as e:
            logger.error(f"Error detecting tables: {e}")
            return []

    def extract_table_structure(
        self,
        image: Image.Image,
        table_bbox: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Extract structured data from a table region

        Args:
            image: PIL Image containing table
            table_bbox: Optional bounding box [x1, y1, x2, y2] for table region

        Returns:
            Structured table data with cells, rows, columns
        """
        if self.table_engine is None:
            return {'error': 'Table engine not initialized'}

        try:
            # Crop to table region if bbox provided
            if table_bbox:
                img_array = np.array(image)
                x1, y1, x2, y2 = table_bbox
                table_img = img_array[y1:y2, x1:x2]
            else:
                table_img = np.array(image)

            # Process table
            result = self.table_engine(table_img)

            # Extract structure
            for item in result:
                if item['type'] == 'table':
                    return self._parse_table_structure(item)

            return {'error': 'No table found in region'}

        except Exception as e:
            logger.error(f"Error extracting table structure: {e}")
            return {'error': str(e)}

    def _extract_cells(self, table_item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract individual cell data from table"""
        cells = []

        try:
            res = table_item.get('res', {})

            # Try to extract from HTML
            html = res.get('html', '')
            if html:
                cells = self._parse_html_cells(html)

            # Alternative: extract from cell boxes
            elif 'cell_bbox' in res:
                for cell in res['cell_bbox']:
                    cells.append({
                        'bbox': cell.get('bbox', []),
                        'text': cell.get('text', ''),
                        'row': cell.get('row', 0),
                        'col': cell.get('col', 0),
                        'row_span': cell.get('row_span', 1),
                        'col_span': cell.get('col_span', 1)
                    })

        except Exception as e:
            logger.debug(f"Error extracting cells: {e}")

        return cells

    def _parse_html_cells(self, html: str) -> List[Dict[str, Any]]:
        """Parse cells from HTML table"""
        cells = []

        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html, 'html.parser')
            table = soup.find('table')

            if table:
                for row_idx, row in enumerate(table.find_all('tr')):
                    for col_idx, cell in enumerate(row.find_all(['td', 'th'])):
                        cells.append({
                            'text': cell.get_text(strip=True),
                            'row': row_idx,
                            'col': col_idx,
                            'row_span': int(cell.get('rowspan', 1)),
                            'col_span': int(cell.get('colspan', 1)),
                            'is_header': cell.name == 'th'
                        })

        except ImportError:
            logger.warning("BeautifulSoup not available for HTML parsing")
        except Exception as e:
            logger.debug(f"Error parsing HTML cells: {e}")

        return cells

    def _count_rows(self, table_item: Dict[str, Any]) -> int:
        """Count number of rows in table"""
        try:
            cells = self._extract_cells(table_item)
            if cells:
                return max(cell['row'] for cell in cells) + 1
            return 0
        except:
            return 0

    def _count_columns(self, table_item: Dict[str, Any]) -> int:
        """Count number of columns in table"""
        try:
            cells = self._extract_cells(table_item)
            if cells:
                return max(cell['col'] for cell in cells) + 1
            return 0
        except:
            return 0

    def _parse_table_structure(self, table_item: Dict[str, Any]) -> Dict[str, Any]:
        """Parse complete table structure"""
        cells = self._extract_cells(table_item)

        # Create 2D grid
        if cells:
            max_row = max(cell['row'] for cell in cells) + 1
            max_col = max(cell['col'] for cell in cells) + 1

            grid = [['' for _ in range(max_col)] for _ in range(max_row)]

            for cell in cells:
                row, col = cell['row'], cell['col']
                grid[row][col] = cell['text']

            return {
                'rows': max_row,
                'columns': max_col,
                'cells': cells,
                'grid': grid,
                'html': table_item.get('res', {}).get('html', ''),
                'bbox': table_item.get('bbox', []),
                'confidence': table_item.get('score', 0.0)
            }

        return {
            'error': 'Could not parse table structure',
            'raw': table_item
        }

    def convert_to_dataframe(self, table_data: Dict[str, Any]):
        """
        Convert table structure to pandas DataFrame

        Args:
            table_data: Structured table data

        Returns:
            pandas DataFrame or None
        """
        try:
            import pandas as pd

            grid = table_data.get('grid', [])
            if not grid:
                return None

            # First row as headers if available
            if len(grid) > 1:
                headers = grid[0]
                data = grid[1:]
                df = pd.DataFrame(data, columns=headers)
            else:
                df = pd.DataFrame(grid)

            return df

        except ImportError:
            logger.warning("pandas not available for DataFrame conversion")
            return None
        except Exception as e:
            logger.error(f"Error converting to DataFrame: {e}")
            return None

    def export_to_excel(
        self,
        tables: List[Dict[str, Any]],
        output_path: str,
        sheet_names: Optional[List[str]] = None
    ) -> bool:
        """
        Export tables to Excel file

        Args:
            tables: List of table structures
            output_path: Path to save Excel file
            sheet_names: Optional names for sheets

        Returns:
            True if successful, False otherwise
        """
        try:
            import pandas as pd

            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                for idx, table in enumerate(tables):
                    df = self.convert_to_dataframe(table)
                    if df is not None:
                        sheet_name = (
                            sheet_names[idx] if sheet_names and idx < len(sheet_names)
                            else f'Table_{idx + 1}'
                        )
                        df.to_excel(writer, sheet_name=sheet_name, index=False)

            logger.info(f"Exported {len(tables)} tables to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error exporting to Excel: {e}")
            return False

    def export_to_csv(
        self,
        table_data: Dict[str, Any],
        output_path: str
    ) -> bool:
        """
        Export single table to CSV

        Args:
            table_data: Structured table data
            output_path: Path to save CSV file

        Returns:
            True if successful, False otherwise
        """
        try:
            import pandas as pd

            df = self.convert_to_dataframe(table_data)
            if df is not None:
                df.to_csv(output_path, index=False)
                logger.info(f"Exported table to {output_path}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return False

    def visualize_table_detection(
        self,
        image: Image.Image,
        tables: List[Dict[str, Any]]
    ) -> Image.Image:
        """
        Draw bounding boxes around detected tables

        Args:
            image: Original image
            tables: List of detected tables

        Returns:
            Image with table bounding boxes drawn
        """
        img_array = np.array(image.copy())

        for idx, table in enumerate(tables):
            bbox = table['bbox']
            confidence = table['confidence']

            # Draw rectangle
            x1, y1, x2, y2 = map(int, bbox)
            color = (0, 255, 0)  # Green
            thickness = 3

            cv2.rectangle(img_array, (x1, y1), (x2, y2), color, thickness)

            # Add label
            label = f"Table {idx + 1} ({confidence:.2f})"
            cv2.putText(
                img_array,
                label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2
            )

        return Image.fromarray(img_array)

    def get_table_statistics(self, tables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get statistics about detected tables

        Args:
            tables: List of detected tables

        Returns:
            Dictionary with statistics
        """
        if not tables:
            return {
                'total_tables': 0,
                'total_cells': 0,
                'avg_rows': 0,
                'avg_columns': 0,
                'avg_confidence': 0.0
            }

        total_cells = sum(len(t.get('cells', [])) for t in tables)
        total_rows = sum(t.get('rows', 0) for t in tables)
        total_cols = sum(t.get('columns', 0) for t in tables)
        total_conf = sum(t.get('confidence', 0) for t in tables)

        return {
            'total_tables': len(tables),
            'total_cells': total_cells,
            'avg_rows': total_rows / len(tables) if tables else 0,
            'avg_columns': total_cols / len(tables) if tables else 0,
            'avg_confidence': total_conf / len(tables) if tables else 0,
            'largest_table': max((t.get('rows', 0) * t.get('columns', 0) for t in tables), default=0)
        }
