"""
Database models and session management
Tracks OCR jobs, results, and usage statistics
"""

import logging
from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pathlib import Path

logger = logging.getLogger(__name__)

# Database URL (SQLite for simplicity, can be changed to PostgreSQL/MySQL)
DATABASE_URL = "sqlite:///./paddleocr.db"

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


class OCRJob(Base):
    """Model for OCR processing jobs"""
    __tablename__ = "ocr_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(64), unique=True, index=True, nullable=False)
    filename = Column(String(255), nullable=False)
    file_hash = Column(String(64), index=True)
    file_size = Column(Integer)  # in bytes

    # Configuration
    lang = Column(String(20))
    config = Column(JSON)  # Full configuration as JSON

    # Processing info
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    processing_time = Column(Float, nullable=True)  # in seconds

    # Results
    total_pages = Column(Integer, nullable=True)
    total_text_blocks = Column(Integer, nullable=True)
    total_characters = Column(Integer, nullable=True)
    average_confidence = Column(Float, nullable=True)

    # Table info
    tables_detected = Column(Integer, default=0)
    table_data = Column(JSON, nullable=True)

    # Error info
    error_message = Column(Text, nullable=True)

    # Flags
    cached = Column(Boolean, default=False)
    enhanced = Column(Boolean, default=False)


class UsageStatistics(Base):
    """Model for tracking usage statistics"""
    __tablename__ = "usage_statistics"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Metrics
    total_jobs = Column(Integer, default=0)
    successful_jobs = Column(Integer, default=0)
    failed_jobs = Column(Integer, default=0)
    cached_jobs = Column(Integer, default=0)

    # Processing metrics
    total_pages_processed = Column(Integer, default=0)
    total_characters_extracted = Column(Integer, default=0)
    total_tables_detected = Column(Integer, default=0)
    average_processing_time = Column(Float, nullable=True)
    average_confidence = Column(Float, nullable=True)

    # Resource metrics
    total_file_size_mb = Column(Float, default=0.0)


# Database utilities
def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database (create tables)"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")


def get_job(db: Session, job_id: str) -> Optional[OCRJob]:
    """Get job by ID"""
    return db.query(OCRJob).filter(OCRJob.job_id == job_id).first()


def create_job(db: Session, job_data: dict) -> OCRJob:
    """Create new OCR job"""
    job = OCRJob(**job_data)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def update_job(db: Session, job_id: str, updates: dict) -> Optional[OCRJob]:
    """Update job with new data"""
    job = get_job(db, job_id)
    if job:
        for key, value in updates.items():
            setattr(job, key, value)
        db.commit()
        db.refresh(job)
    return job


def get_recent_jobs(db: Session, limit: int = 10) -> list:
    """Get recent jobs"""
    return db.query(OCRJob).order_by(OCRJob.created_at.desc()).limit(limit).all()


def get_statistics(db: Session, days: int = 7) -> dict:
    """Get usage statistics for the last N days"""
    from datetime import timedelta
    from sqlalchemy import func

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    jobs = db.query(OCRJob).filter(OCRJob.created_at >= cutoff_date).all()

    if not jobs:
        return {
            "total_jobs": 0,
            "successful_jobs": 0,
            "failed_jobs": 0,
            "cached_jobs": 0,
            "average_processing_time": 0.0,
            "total_pages": 0,
            "total_tables": 0
        }

    total = len(jobs)
    successful = len([j for j in jobs if j.status == "completed"])
    failed = len([j for j in jobs if j.status == "failed"])
    cached = len([j for j in jobs if j.cached])

    processing_times = [j.processing_time for j in jobs if j.processing_time]
    avg_time = sum(processing_times) / len(processing_times) if processing_times else 0.0

    total_pages = sum(j.total_pages or 0 for j in jobs)
    total_tables = sum(j.tables_detected or 0 for j in jobs)

    return {
        "period_days": days,
        "total_jobs": total,
        "successful_jobs": successful,
        "failed_jobs": failed,
        "cached_jobs": cached,
        "average_processing_time": avg_time,
        "total_pages": total_pages,
        "total_tables": total_tables,
        "success_rate": (successful / total * 100) if total > 0 else 0.0
    }


# Initialize database on import
init_db()
