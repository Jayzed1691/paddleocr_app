"""
Cache Manager for OCR Results
Implements LRU caching with file hash-based keys
"""

import hashlib
import json
import logging
import pickle
from collections import OrderedDict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

from config import CACHE_TTL, MAX_CACHE_SIZE

logger = logging.getLogger(__name__)


class CacheManager:
    """
    LRU Cache manager for OCR results
    """

    def __init__(
        self,
        cache_dir: Path = None,
        max_size: int = MAX_CACHE_SIZE,
        ttl: int = CACHE_TTL,
        enabled: bool = True,
    ):
        """
        Initialize cache manager

        Args:
            cache_dir: Directory to store cache files
            max_size: Maximum number of cached items
            ttl: Time-to-live in seconds
            enabled: Whether caching is enabled
        """
        self.enabled = enabled
        self.max_size = max_size
        self.ttl = ttl

        if cache_dir is None:
            cache_dir = Path.home() / ".paddleocr_cache"

        self.cache_dir = Path(cache_dir)
        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

        # In-memory cache (LRU)
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()

        # Load existing cache index
        self._index_file = self.cache_dir / "cache_index.json"
        self._load_index()

        logger.info(
            f"Cache manager initialized: dir={self.cache_dir}, max_size={max_size}, ttl={ttl}s"
        )

    def _load_index(self):
        """Load cache index from disk"""
        if not self.enabled:
            return

        if self._index_file.exists():
            try:
                with open(self._index_file, "r") as f:
                    index_data = json.load(f)

                # Load items, checking expiration
                current_time = datetime.now()
                for key, metadata in index_data.items():
                    created_at = datetime.fromisoformat(metadata["created_at"])
                    if (current_time - created_at).total_seconds() < self.ttl:
                        self._cache[key] = metadata
                        self._cache.move_to_end(key)  # Most recently loaded
                    else:
                        # Remove expired cache file
                        cache_file = self.cache_dir / f"{key}.pkl"
                        if cache_file.exists():
                            cache_file.unlink()

                logger.info(f"Loaded {len(self._cache)} items from cache index")
            except Exception as e:
                logger.error(f"Failed to load cache index: {e}")
                self._cache = OrderedDict()

    def _save_index(self):
        """Save cache index to disk"""
        if not self.enabled:
            return

        try:
            with open(self._index_file, "w") as f:
                json.dump(dict(self._cache), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache index: {e}")

    def compute_key(self, file_hash: str, config: Dict[str, Any]) -> str:
        """
        Compute cache key from file hash and configuration

        Args:
            file_hash: Hash of the input file
            config: OCR configuration dictionary

        Returns:
            Cache key string
        """
        # Create a deterministic config string
        config_items = sorted(config.items())
        config_str = json.dumps(config_items, sort_keys=True)

        # Compute combined hash
        combined = f"{file_hash}_{config_str}"
        key = hashlib.sha256(combined.encode()).hexdigest()[:16]

        return key

    def get(self, file_hash: str, config: Dict[str, Any]) -> Optional[Any]:
        """
        Retrieve cached OCR result

        Args:
            file_hash: Hash of the input file
            config: OCR configuration dictionary

        Returns:
            Cached result or None if not found/expired
        """
        if not self.enabled:
            return None

        key = self.compute_key(file_hash, config)

        # Check in-memory cache
        if key in self._cache:
            metadata = self._cache[key]

            # Check expiration
            created_at = datetime.fromisoformat(metadata["created_at"])
            if (datetime.now() - created_at).total_seconds() >= self.ttl:
                logger.info(f"Cache expired for key {key}")
                self.delete(key)
                return None

            # Load from disk
            cache_file = self.cache_dir / f"{key}.pkl"
            if cache_file.exists():
                try:
                    with open(cache_file, "rb") as f:
                        result = pickle.load(f)

                    # Move to end (most recently used)
                    self._cache.move_to_end(key)

                    logger.info(f"Cache hit for key {key}")
                    return result
                except Exception as e:
                    logger.error(f"Failed to load cache file {key}: {e}")
                    self.delete(key)
                    return None
            else:
                # Index exists but file missing
                logger.warning(f"Cache file missing for key {key}")
                self.delete(key)
                return None

        logger.info(f"Cache miss for key {key}")
        return None

    def set(
        self,
        file_hash: str,
        config: Dict[str, Any],
        result: Any,
        file_metadata: Dict[str, Any] = None,
    ):
        """
        Store OCR result in cache

        Args:
            file_hash: Hash of the input file
            config: OCR configuration dictionary
            result: OCR result to cache
            file_metadata: Optional metadata about the file
        """
        if not self.enabled:
            return

        key = self.compute_key(file_hash, config)

        # Enforce size limit (LRU eviction)
        while len(self._cache) >= self.max_size:
            # Remove oldest item
            oldest_key = next(iter(self._cache))
            self.delete(oldest_key)
            logger.info(f"Evicted oldest cache item: {oldest_key}")

        # Save result to disk
        cache_file = self.cache_dir / f"{key}.pkl"
        try:
            with open(cache_file, "wb") as f:
                pickle.dump(result, f)

            # Update index
            metadata = {
                "file_hash": file_hash,
                "created_at": datetime.now().isoformat(),
                "config_hash": hashlib.sha256(
                    json.dumps(config, sort_keys=True).encode()
                ).hexdigest()[:8],
                "file_metadata": file_metadata or {},
            }

            self._cache[key] = metadata
            self._cache.move_to_end(key)

            # Save index
            self._save_index()

            logger.info(f"Cached result for key {key}")
        except Exception as e:
            logger.error(f"Failed to cache result: {e}")

    def delete(self, key: str):
        """
        Delete cached item

        Args:
            key: Cache key to delete
        """
        if key in self._cache:
            del self._cache[key]

        cache_file = self.cache_dir / f"{key}.pkl"
        if cache_file.exists():
            cache_file.unlink()

        self._save_index()

    def clear(self):
        """Clear all cache"""
        if not self.enabled:
            return

        logger.info("Clearing all cache")

        # Delete all cache files
        for cache_file in self.cache_dir.glob("*.pkl"):
            cache_file.unlink()

        # Clear index
        self._cache.clear()
        if self._index_file.exists():
            self._index_file.unlink()

        logger.info("Cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache stats
        """
        if not self.enabled:
            return {"enabled": False}

        total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.pkl"))

        return {
            "enabled": True,
            "items": len(self._cache),
            "max_size": self.max_size,
            "ttl": self.ttl,
            "total_disk_size_mb": total_size / (1024 * 1024),
            "cache_dir": str(self.cache_dir),
        }
