"""
FastAPI REST API Server for PaddleOCR Application
Provides programmatic access to OCR functionality
"""

import logging
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import uvicorn
from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from cache_manager import CacheManager
from document_processor import DocumentProcessor
from image_enhancer import ImageEnhancer
from logger_config import setup_logging
from ocr_engine import OCREngine
from table_recognizer import TableRecognizer
from utils import compute_file_hash, sanitize_filename

# Setup logging
setup_logging(log_level="INFO")
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="PaddleOCR API",
    description="REST API for OCR processing with table recognition",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
cache_manager = CacheManager(enabled=True)
table_recognizer = TableRecognizer()


# Request/Response Models
class OCRConfig(BaseModel):
    """OCR configuration parameters"""

    lang: str = Field(default="en", description="Language for OCR")
    use_textline_orientation: bool = Field(default=True)
    text_det_thresh: float = Field(default=0.3, ge=0.1, le=0.9)
    text_rec_score_thresh: float = Field(default=0.5, ge=0.0, le=1.0)
    detect_tables: bool = Field(default=False, description="Enable table detection")
    table_conf_threshold: float = Field(default=0.5, ge=0.1, le=1.0)


class ImageEnhancementConfig(BaseModel):
    """Image enhancement parameters"""

    rotation: float = Field(default=0.0, description="Rotation angle in degrees")
    brightness: float = Field(default=1.0, ge=0.1, le=3.0)
    contrast: float = Field(default=1.0, ge=0.1, le=3.0)
    sharpness: float = Field(default=1.0, ge=0.1, le=3.0)
    denoise: bool = Field(default=False)
    deskew: bool = Field(default=False)
    grayscale: bool = Field(default=False)
    adaptive_threshold: bool = Field(default=False)


class OCRResponse(BaseModel):
    """OCR processing response"""

    success: bool
    processing_time: float
    total_pages: int
    total_text_blocks: int
    total_characters: int
    average_confidence: float
    results: List[dict]
    tables: Optional[List[dict]] = None
    cached: bool = False


class HealthResponse(BaseModel):
    """Health check response"""

    status: str
    timestamp: str
    version: str
    services: dict


# Dependency injection
async def get_ocr_engine(config: OCRConfig) -> OCREngine:
    """Get or create OCR engine with configuration"""
    return OCREngine(config.dict())


async def get_document_processor() -> DocumentProcessor:
    """Get document processor"""
    return DocumentProcessor()


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint

    Returns service status and version information
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="3.0.0",
        services={
            "ocr": "available",
            "table_recognition": "available" if table_recognizer.table_engine else "unavailable",
            "cache": "enabled" if cache_manager.enabled else "disabled",
        },
    )


# OCR processing endpoint
@app.post("/ocr/process", response_model=OCRResponse)
async def process_ocr(
    file: UploadFile = File(..., description="Document file to process"),
    config: OCRConfig = Depends(),
    enhancement: Optional[ImageEnhancementConfig] = None,
    use_cache: bool = Query(default=True, description="Use result caching"),
):
    """
    Process document with OCR

    - **file**: Document file (PDF, DOCX, TXT, PNG, JPG, JPEG)
    - **config**: OCR configuration parameters
    - **enhancement**: Optional image enhancement parameters
    - **use_cache**: Whether to use caching

    Returns OCR results with text, confidence scores, and optionally tables
    """
    import time

    start_time = time.time()

    temp_dir = Path(tempfile.mkdtemp())

    try:
        # Save uploaded file
        safe_filename = sanitize_filename(file.filename)
        file_path = temp_dir / safe_filename

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Compute file hash for caching
        file_hash = compute_file_hash(file_path)

        # Check cache
        cached_result = None
        if use_cache:
            cached_result = cache_manager.get(file_hash, config.dict())

        if cached_result:
            logger.info(f"Cache hit for {file.filename}")
            processing_time = time.time() - start_time
            return OCRResponse(**cached_result, processing_time=processing_time, cached=True)

        # Process document
        doc_processor = DocumentProcessor()
        images = doc_processor.process_file(file_path)

        # Apply enhancement if specified
        if enhancement:
            enhancer = ImageEnhancer()
            images = [
                enhancer.enhance(
                    img,
                    rotation=enhancement.rotation,
                    brightness=enhancement.brightness,
                    contrast=enhancement.contrast,
                    sharpness=enhancement.sharpness,
                    denoise=enhancement.denoise,
                    deskew=enhancement.deskew,
                    grayscale=enhancement.grayscale,
                    adaptive_threshold=enhancement.adaptive_threshold,
                )
                for img in images
            ]

        # Initialize OCR engine
        ocr_engine = OCREngine(config.dict())

        # Process with OCR
        ocr_results = []
        for image in images:
            result = ocr_engine.process_image(image)
            ocr_results.append(result)

        # Detect tables if requested
        tables_data = None
        if config.detect_tables:
            tables_data = []
            for image in images:
                tables = table_recognizer.detect_tables(
                    image, conf_threshold=config.table_conf_threshold
                )
                tables_data.extend(tables)

        # Get statistics
        stats = ocr_engine.get_statistics(ocr_results)

        # Prepare response
        response_data = {
            "success": True,
            "processing_time": time.time() - start_time,
            "total_pages": stats["total_pages"],
            "total_text_blocks": stats["total_text_blocks"],
            "total_characters": stats["total_characters"],
            "average_confidence": stats["average_confidence"],
            "results": [
                {
                    "page": i + 1,
                    "text": ocr_engine.extract_text(result),
                    "structured_data": ocr_engine.extract_structured_data(result),
                }
                for i, result in enumerate(ocr_results)
            ],
            "tables": tables_data,
            "cached": False,
        }

        # Cache result
        if use_cache:
            cache_manager.set(file_hash, config.dict(), response_data)

        return OCRResponse(**response_data)

    except Exception as e:
        logger.error(f"Error processing file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


# Table extraction endpoint
@app.post("/ocr/extract-tables")
async def extract_tables(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    lang: str = Query(default="en"),
    conf_threshold: float = Query(default=0.5, ge=0.1, le=1.0),
    export_format: str = Query(default="json", regex="^(json|excel|csv)$"),
):
    """
    Extract tables from document

    - **file**: Document file
    - **lang**: Language for OCR
    - **conf_threshold**: Confidence threshold for table detection
    - **export_format**: Output format (json, excel, csv)

    Returns detected tables in specified format
    """
    temp_dir = Path(tempfile.mkdtemp())

    try:
        # Save file
        file_path = temp_dir / sanitize_filename(file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())

        # Process to images
        doc_processor = DocumentProcessor()
        images = doc_processor.process_file(file_path)

        # Detect tables
        all_tables = []
        for page_idx, image in enumerate(images):
            tables = table_recognizer.detect_tables(image, conf_threshold)
            for table in tables:
                table["page"] = page_idx + 1
                all_tables.append(table)

        if not all_tables:
            # Cleanup immediately for JSON response
            shutil.rmtree(temp_dir, ignore_errors=True)
            return JSONResponse(
                content={"message": "No tables detected", "tables": []}, status_code=200
            )

        # Export based on format
        if export_format == "excel":
            output_path = temp_dir / "tables.xlsx"
            success = table_recognizer.export_to_excel(all_tables, str(output_path))

            if success:
                # Schedule cleanup after response is sent
                background_tasks.add_task(shutil.rmtree, temp_dir, ignore_errors=True)
                return FileResponse(
                    path=output_path,
                    filename="extracted_tables.xlsx",
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

        elif export_format == "csv" and len(all_tables) > 0:
            output_path = temp_dir / "table.csv"
            success = table_recognizer.export_to_csv(all_tables[0], str(output_path))

            if success:
                # Schedule cleanup after response is sent
                background_tasks.add_task(shutil.rmtree, temp_dir, ignore_errors=True)
                return FileResponse(
                    path=output_path, filename="extracted_table.csv", media_type="text/csv"
                )

        # Default: JSON - cleanup immediately
        stats = table_recognizer.get_table_statistics(all_tables)
        shutil.rmtree(temp_dir, ignore_errors=True)
        return JSONResponse(content={"tables": all_tables, "statistics": stats})

    except Exception as e:
        logger.error(f"Error extracting tables: {e}", exc_info=True)
        # Cleanup on error
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=str(e))


# Cache management endpoints
@app.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics"""
    return cache_manager.get_stats()


@app.post("/cache/clear")
async def clear_cache():
    """Clear all cache"""
    cache_manager.clear()
    return {"message": "Cache cleared successfully"}


# Export endpoints
@app.post("/ocr/export/{format}")
async def export_results(
    background_tasks: BackgroundTasks,
    format: str,
    file: UploadFile = File(...),
    config: OCRConfig = Depends(),
):
    """
    Process document and export in specified format

    - **format**: Export format (markdown, json, html, txt)
    - **file**: Document file
    - **config**: OCR configuration
    """
    temp_dir = Path(tempfile.mkdtemp())

    try:
        # Process document
        file_path = temp_dir / sanitize_filename(file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())

        doc_processor = DocumentProcessor()
        images = doc_processor.process_file(file_path)

        ocr_engine = OCREngine(config.dict())
        results = [ocr_engine.process_image(img) for img in images]

        # Export based on format
        if format == "markdown":
            content = ocr_engine.format_as_markdown(results, page_numbers=True)
            output_path = temp_dir / "output.md"
            output_path.write_text(content)
            # Schedule cleanup after response is sent
            background_tasks.add_task(shutil.rmtree, temp_dir, ignore_errors=True)
            return FileResponse(output_path, filename="ocr_result.md", media_type="text/markdown")

        elif format == "json":
            content = ocr_engine.format_as_json(results)
            output_path = temp_dir / "output.json"
            output_path.write_text(content)
            # Schedule cleanup after response is sent
            background_tasks.add_task(shutil.rmtree, temp_dir, ignore_errors=True)
            return FileResponse(
                output_path, filename="ocr_result.json", media_type="application/json"
            )

        elif format == "html":
            content = ocr_engine.format_as_html(results)
            output_path = temp_dir / "output.html"
            output_path.write_text(content)
            # Schedule cleanup after response is sent
            background_tasks.add_task(shutil.rmtree, temp_dir, ignore_errors=True)
            return FileResponse(output_path, filename="ocr_result.html", media_type="text/html")

        elif format == "txt":
            content = ocr_engine.format_as_markdown(results, page_numbers=False)
            output_path = temp_dir / "output.txt"
            output_path.write_text(content)
            # Schedule cleanup after response is sent
            background_tasks.add_task(shutil.rmtree, temp_dir, ignore_errors=True)
            return FileResponse(output_path, filename="ocr_result.txt", media_type="text/plain")

        else:
            # Cleanup immediately for error
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

    except Exception as e:
        logger.error(f"Error exporting: {e}", exc_info=True)
        # Cleanup on error
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=str(e))


# Run server
if __name__ == "__main__":
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
