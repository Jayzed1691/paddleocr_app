"""
Integration tests for complete workflows
"""

import pytest
from pathlib import Path
from PIL import Image
import tempfile
import shutil

from document_processor import DocumentProcessor
from ocr_engine import OCREngine
from cache_manager import CacheManager
from image_enhancer import ImageEnhancer
from utils import compute_file_hash


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows"""

    @pytest.mark.integration
    def test_text_file_to_ocr_workflow(self, temp_dir):
        """Test complete workflow: text file -> images -> OCR"""
        # Create test text file
        test_file = temp_dir / "test.txt"
        test_file.write_text("Test OCR Document\nLine 2\nLine 3")

        # Process document
        processor = DocumentProcessor()
        images = processor.process_file(test_file)

        assert len(images) == 1
        assert isinstance(images[0], Image.Image)

    @pytest.mark.integration
    def test_image_enhancement_workflow(self, temp_dir):
        """Test image enhancement workflow"""
        # Create test image
        img = Image.new('RGB', (200, 100), color='white')
        test_file = temp_dir / "test.png"
        img.save(test_file)

        # Process and enhance
        processor = DocumentProcessor()
        images = processor.process_file(test_file)

        enhancer = ImageEnhancer()
        enhanced = enhancer.enhance(
            images[0],
            brightness=1.2,
            contrast=1.1,
            sharpness=1.3
        )

        assert isinstance(enhanced, Image.Image)
        assert enhanced.size == images[0].size

    @pytest.mark.integration
    def test_cache_workflow(self, temp_dir):
        """Test caching workflow"""
        # Create test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("Cached content")

        # Compute hash
        file_hash = compute_file_hash(test_file)

        # Create cache manager
        cache_dir = temp_dir / "cache"
        cache = CacheManager(cache_dir=cache_dir, max_size=10, ttl=3600)

        # Test cache miss
        config = {'lang': 'en'}
        result = cache.get(file_hash, config)
        assert result is None

        # Store in cache
        test_result = {"text": "Test result"}
        cache.set(file_hash, config, test_result)

        # Test cache hit
        cached_result = cache.get(file_hash, config)
        assert cached_result == test_result

        # Test cache stats
        stats = cache.get_stats()
        assert stats['items'] == 1
        assert stats['enabled'] is True

    @pytest.mark.integration
    def test_lru_cache_eviction(self, temp_dir):
        """Test LRU cache eviction"""
        cache_dir = temp_dir / "cache"
        cache = CacheManager(cache_dir=cache_dir, max_size=3, ttl=3600)

        config = {'lang': 'en'}

        # Add 4 items (should evict oldest)
        for i in range(4):
            file_hash = f"hash_{i}"
            result = {"data": f"result_{i}"}
            cache.set(file_hash, config, result)

        # First item should be evicted
        assert cache.get("hash_0", config) is None

        # Other items should be present
        assert cache.get("hash_1", config) is not None
        assert cache.get("hash_2", config) is not None
        assert cache.get("hash_3", config) is not None

    @pytest.mark.integration
    def test_multiple_file_processing(self, temp_dir):
        """Test processing multiple files"""
        # Create multiple test files
        files = []
        for i in range(3):
            test_file = temp_dir / f"test_{i}.txt"
            test_file.write_text(f"Document {i}\nContent here")
            files.append(test_file)

        # Process all files
        processor = DocumentProcessor()
        all_images = []

        for file in files:
            images = processor.process_file(file)
            all_images.extend(images)

        assert len(all_images) == 3

    @pytest.mark.integration
    def test_image_enhancement_preserves_size(self, temp_dir):
        """Test that image enhancement preserves image dimensions"""
        # Create test image
        original_size = (400, 300)
        img = Image.new('RGB', original_size, color='gray')

        enhancer = ImageEnhancer()

        # Apply various enhancements
        enhanced = enhancer.enhance(
            img,
            rotation=0,  # No rotation to preserve size
            brightness=1.5,
            contrast=1.2,
            sharpness=1.3,
            denoise=True,
            grayscale=True
        )

        assert enhanced.size == original_size

    @pytest.mark.integration
    def test_cache_with_different_configs(self, temp_dir):
        """Test that different configs create different cache entries"""
        cache_dir = temp_dir / "cache"
        cache = CacheManager(cache_dir=cache_dir)

        file_hash = "test_hash"
        config1 = {'lang': 'en', 'threshold': 0.5}
        config2 = {'lang': 'ch', 'threshold': 0.5}

        result1 = {"text": "English result"}
        result2 = {"text": "Chinese result"}

        # Cache with different configs
        cache.set(file_hash, config1, result1)
        cache.set(file_hash, config2, result2)

        # Retrieve with specific configs
        retrieved1 = cache.get(file_hash, config1)
        retrieved2 = cache.get(file_hash, config2)

        assert retrieved1 == result1
        assert retrieved2 == result2
