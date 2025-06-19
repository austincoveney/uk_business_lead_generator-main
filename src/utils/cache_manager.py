"""Advanced caching system with multiple cache types and strategies."""

import time
import pickle
import hashlib
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, Union, Tuple
from dataclasses import dataclass, field
from collections import OrderedDict, defaultdict
from pathlib import Path
import json
import logging
from enum import Enum
from contextlib import contextmanager


class CacheStrategy(Enum):
    """Cache eviction strategies."""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    FIFO = "fifo"  # First In, First Out
    TTL = "ttl"  # Time To Live
    ADAPTIVE = "adaptive"  # Adaptive based on access patterns


class CacheType(Enum):
    """Types of cache storage."""
    MEMORY = "memory"
    DISK = "disk"
    HYBRID = "hybrid"


@dataclass
class CacheEntry:
    """Individual cache entry with metadata."""
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    ttl_seconds: Optional[float] = None
    size_bytes: int = 0
    tags: List[str] = field(default_factory=list)
    
    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        if self.ttl_seconds is None:
            return False
        return (datetime.now() - self.created_at).total_seconds() > self.ttl_seconds
    
    def touch(self) -> None:
        """Update access metadata."""
        self.last_accessed = datetime.now()
        self.access_count += 1
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'key': self.key,
            'created_at': self.created_at.isoformat(),
            'last_accessed': self.last_accessed.isoformat(),
            'access_count': self.access_count,
            'ttl_seconds': self.ttl_seconds,
            'size_bytes': self.size_bytes,
            'tags': self.tags
        }


@dataclass
class CacheStats:
    """Cache performance statistics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size_bytes: int = 0
    entry_count: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    @property
    def miss_rate(self) -> float:
        """Calculate cache miss rate."""
        return 1.0 - self.hit_rate
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'hits': self.hits,
            'misses': self.misses,
            'evictions': self.evictions,
            'size_bytes': self.size_bytes,
            'entry_count': self.entry_count,
            'hit_rate': self.hit_rate,
            'miss_rate': self.miss_rate
        }


class MemoryCache:
    """In-memory cache with configurable eviction strategies."""
    
    def __init__(self, 
                 max_size: int = 1000,
                 max_memory_mb: float = 100.0,
                 strategy: CacheStrategy = CacheStrategy.LRU,
                 default_ttl: Optional[float] = None):
        self.max_size = max_size
        self.max_memory_bytes = int(max_memory_mb * 1024 * 1024)
        self.strategy = strategy
        self.default_ttl = default_ttl
        
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order: OrderedDict = OrderedDict()
        self._frequency: defaultdict = defaultdict(int)
        self._lock = threading.RLock()
        self._stats = CacheStats()
        
        self.logger = logging.getLogger(__name__)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._stats.misses += 1
                return None
            
            if entry.is_expired():
                self._remove_entry(key)
                self._stats.misses += 1
                return None
            
            # Update access metadata
            entry.touch()
            self._update_access_tracking(key)
            
            self._stats.hits += 1
            return entry.value
    
    def put(self, key: str, value: Any, ttl: Optional[float] = None, tags: Optional[List[str]] = None) -> None:
        """Put value into cache."""
        with self._lock:
            # Calculate size
            try:
                size_bytes = len(pickle.dumps(value))
            except Exception:
                size_bytes = 0
            
            # Create entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                ttl_seconds=ttl or self.default_ttl,
                size_bytes=size_bytes,
                tags=tags or []
            )
            
            # Remove existing entry if present
            if key in self._cache:
                self._remove_entry(key)
            
            # Check if we need to evict
            while self._should_evict(size_bytes):
                self._evict_one()
            
            # Add new entry
            self._cache[key] = entry
            self._update_access_tracking(key)
            
            # Update stats
            self._stats.entry_count = len(self._cache)
            self._stats.size_bytes += size_bytes
    
    def delete(self, key: str) -> bool:
        """Delete entry from cache."""
        with self._lock:
            if key in self._cache:
                self._remove_entry(key)
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()
            self._frequency.clear()
            self._stats = CacheStats()
    
    def clear_by_tags(self, tags: List[str]) -> int:
        """Clear entries with specific tags."""
        with self._lock:
            keys_to_remove = []
            for key, entry in self._cache.items():
                if any(tag in entry.tags for tag in tags):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                self._remove_entry(key)
            
            return len(keys_to_remove)
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        with self._lock:
            self._stats.entry_count = len(self._cache)
            return self._stats
    
    def _should_evict(self, new_entry_size: int) -> bool:
        """Check if eviction is needed."""
        return (len(self._cache) >= self.max_size or 
                self._stats.size_bytes + new_entry_size > self.max_memory_bytes)
    
    def _evict_one(self) -> None:
        """Evict one entry based on strategy."""
        if not self._cache:
            return
        
        if self.strategy == CacheStrategy.LRU:
            key = next(iter(self._access_order))
        elif self.strategy == CacheStrategy.LFU:
            key = min(self._cache.keys(), key=lambda k: self._frequency[k])
        elif self.strategy == CacheStrategy.FIFO:
            key = next(iter(self._cache))
        elif self.strategy == CacheStrategy.TTL:
            # Find expired entries first, then oldest
            expired_keys = [k for k, e in self._cache.items() if e.is_expired()]
            if expired_keys:
                key = expired_keys[0]
            else:
                key = min(self._cache.keys(), key=lambda k: self._cache[k].created_at)
        else:  # ADAPTIVE
            key = self._adaptive_evict()
        
        self._remove_entry(key)
        self._stats.evictions += 1
    
    def _adaptive_evict(self) -> str:
        """Adaptive eviction based on access patterns."""
        # Score based on recency, frequency, and size
        scores = {}
        now = datetime.now()
        
        for key, entry in self._cache.items():
            recency_score = (now - entry.last_accessed).total_seconds()
            frequency_score = 1.0 / (entry.access_count + 1)
            size_score = entry.size_bytes / (1024 * 1024)  # MB
            
            # Higher score = more likely to evict
            scores[key] = recency_score * frequency_score * (1 + size_score)
        
        return max(scores.keys(), key=lambda k: scores[k])
    
    def _remove_entry(self, key: str) -> None:
        """Remove entry and update tracking."""
        if key in self._cache:
            entry = self._cache.pop(key)
            self._stats.size_bytes -= entry.size_bytes
            
        if key in self._access_order:
            del self._access_order[key]
            
        if key in self._frequency:
            del self._frequency[key]
    
    def _update_access_tracking(self, key: str) -> None:
        """Update access tracking for different strategies."""
        # Update LRU order
        if key in self._access_order:
            del self._access_order[key]
        self._access_order[key] = True
        
        # Update frequency
        self._frequency[key] += 1


class DiskCache:
    """Persistent disk-based cache."""
    
    def __init__(self, cache_dir: str, max_size_mb: float = 500.0):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_bytes = int(max_size_mb * 1024 * 1024)
        
        self._metadata_file = self.cache_dir / "metadata.json"
        self._metadata: Dict[str, Dict] = self._load_metadata()
        self._lock = threading.RLock()
        self._stats = CacheStats()
        
        self.logger = logging.getLogger(__name__)
        
        # Clean up expired entries on startup
        self._cleanup_expired()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from disk cache."""
        with self._lock:
            key_hash = self._hash_key(key)
            
            if key_hash not in self._metadata:
                self._stats.misses += 1
                return None
            
            metadata = self._metadata[key_hash]
            
            # Check expiration
            if self._is_expired(metadata):
                self._remove_entry(key_hash)
                self._stats.misses += 1
                return None
            
            # Load from disk
            try:
                file_path = self.cache_dir / f"{key_hash}.cache"
                with open(file_path, 'rb') as f:
                    value = pickle.load(f)
                
                # Update access metadata
                metadata['last_accessed'] = datetime.now().isoformat()
                metadata['access_count'] = metadata.get('access_count', 0) + 1
                self._save_metadata()
                
                self._stats.hits += 1
                return value
                
            except Exception as e:
                self.logger.error(f"Error loading cache entry {key}: {e}")
                self._remove_entry(key_hash)
                self._stats.misses += 1
                return None
    
    def put(self, key: str, value: Any, ttl: Optional[float] = None, tags: Optional[List[str]] = None) -> None:
        """Put value into disk cache."""
        with self._lock:
            key_hash = self._hash_key(key)
            
            try:
                # Serialize value
                serialized = pickle.dumps(value)
                size_bytes = len(serialized)
                
                # Check if we need to evict
                while self._should_evict(size_bytes):
                    self._evict_one()
                
                # Save to disk
                file_path = self.cache_dir / f"{key_hash}.cache"
                with open(file_path, 'wb') as f:
                    f.write(serialized)
                
                # Update metadata
                now = datetime.now()
                self._metadata[key_hash] = {
                    'key': key,
                    'created_at': now.isoformat(),
                    'last_accessed': now.isoformat(),
                    'access_count': 1,
                    'ttl_seconds': ttl,
                    'size_bytes': size_bytes,
                    'tags': tags or []
                }
                
                self._save_metadata()
                self._stats.size_bytes += size_bytes
                
            except Exception as e:
                self.logger.error(f"Error saving cache entry {key}: {e}")
    
    def delete(self, key: str) -> bool:
        """Delete entry from disk cache."""
        with self._lock:
            key_hash = self._hash_key(key)
            if key_hash in self._metadata:
                self._remove_entry(key_hash)
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            for key_hash in list(self._metadata.keys()):
                self._remove_entry(key_hash)
            self._metadata.clear()
            self._save_metadata()
            self._stats = CacheStats()
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        with self._lock:
            self._stats.entry_count = len(self._metadata)
            return self._stats
    
    def _hash_key(self, key: str) -> str:
        """Generate hash for cache key."""
        return hashlib.sha256(key.encode()).hexdigest()[:16]
    
    def _load_metadata(self) -> Dict[str, Dict]:
        """Load metadata from disk."""
        try:
            if self._metadata_file.exists():
                with open(self._metadata_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading cache metadata: {e}")
        return {}
    
    def _save_metadata(self) -> None:
        """Save metadata to disk."""
        try:
            with open(self._metadata_file, 'w') as f:
                json.dump(self._metadata, f, indent=2)
        except (PermissionError, OSError, IOError) as e:
            self.logger.error(f"Error writing cache metadata file {self._metadata_file}: {e}")
        except (TypeError, ValueError) as e:
            self.logger.error(f"Error serializing cache metadata: {e}")
    
    def _is_expired(self, metadata: Dict) -> bool:
        """Check if entry is expired."""
        ttl = metadata.get('ttl_seconds')
        if ttl is None:
            return False
        
        created_at = datetime.fromisoformat(metadata['created_at'])
        return (datetime.now() - created_at).total_seconds() > ttl
    
    def _should_evict(self, new_entry_size: int) -> bool:
        """Check if eviction is needed."""
        return self._stats.size_bytes + new_entry_size > self.max_size_bytes
    
    def _evict_one(self) -> None:
        """Evict least recently used entry."""
        if not self._metadata:
            return
        
        # Find LRU entry
        lru_key = min(self._metadata.keys(), 
                     key=lambda k: self._metadata[k]['last_accessed'])
        
        self._remove_entry(lru_key)
        self._stats.evictions += 1
    
    def _remove_entry(self, key_hash: str) -> None:
        """Remove entry from disk and metadata."""
        if key_hash in self._metadata:
            metadata = self._metadata.pop(key_hash)
            self._stats.size_bytes -= metadata.get('size_bytes', 0)
            
            # Remove file
            file_path = self.cache_dir / f"{key_hash}.cache"
            try:
                if file_path.exists():
                    file_path.unlink()
            except Exception as e:
                self.logger.error(f"Error removing cache file {file_path}: {e}")
    
    def _cleanup_expired(self) -> None:
        """Clean up expired entries."""
        expired_keys = []
        for key_hash, metadata in self._metadata.items():
            if self._is_expired(metadata):
                expired_keys.append(key_hash)
        
        for key_hash in expired_keys:
            self._remove_entry(key_hash)
        
        if expired_keys:
            self._save_metadata()
            self.logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")


class CacheManager:
    """Unified cache manager supporting multiple cache types."""
    
    def __init__(self, 
                 memory_cache_size: int = 1000,
                 memory_cache_mb: float = 100.0,
                 disk_cache_dir: Optional[str] = None,
                 disk_cache_mb: float = 500.0,
                 cache_type: CacheType = CacheType.HYBRID):
        
        self.cache_type = cache_type
        self.logger = logging.getLogger(__name__)
        
        # Initialize caches based on type
        if cache_type in [CacheType.MEMORY, CacheType.HYBRID]:
            self.memory_cache = MemoryCache(
                max_size=memory_cache_size,
                max_memory_mb=memory_cache_mb
            )
        else:
            self.memory_cache = None
        
        if cache_type in [CacheType.DISK, CacheType.HYBRID]:
            if disk_cache_dir is None:
                disk_cache_dir = "cache"
            self.disk_cache = DiskCache(
                cache_dir=disk_cache_dir,
                max_size_mb=disk_cache_mb
            )
        else:
            self.disk_cache = None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        # Try memory cache first (if available)
        if self.memory_cache:
            value = self.memory_cache.get(key)
            if value is not None:
                return value
        
        # Try disk cache
        if self.disk_cache:
            value = self.disk_cache.get(key)
            if value is not None:
                # Promote to memory cache if hybrid
                if self.cache_type == CacheType.HYBRID and self.memory_cache:
                    self.memory_cache.put(key, value)
                return value
        
        return None
    
    def put(self, key: str, value: Any, ttl: Optional[float] = None, 
            tags: Optional[List[str]] = None, memory_only: bool = False) -> None:
        """Put value into cache."""
        # Put in memory cache
        if self.memory_cache:
            self.memory_cache.put(key, value, ttl, tags)
        
        # Put in disk cache (unless memory_only)
        if self.disk_cache and not memory_only:
            self.disk_cache.put(key, value, ttl, tags)
    
    def delete(self, key: str) -> bool:
        """Delete from all caches."""
        deleted = False
        
        if self.memory_cache:
            deleted |= self.memory_cache.delete(key)
        
        if self.disk_cache:
            deleted |= self.disk_cache.delete(key)
        
        return deleted
    
    def clear(self) -> None:
        """Clear all caches."""
        if self.memory_cache:
            self.memory_cache.clear()
        
        if self.disk_cache:
            self.disk_cache.clear()
    
    def clear_by_tags(self, tags: List[str]) -> int:
        """Clear entries with specific tags."""
        total_cleared = 0
        
        if self.memory_cache:
            total_cleared += self.memory_cache.clear_by_tags(tags)
        
        # Note: Disk cache tag clearing would require loading metadata
        # This is a simplified implementation
        
        return total_cleared
    
    def clear_expired(self) -> int:
        """Clear expired entries from all caches."""
        total_cleared = 0
        
        # Clear expired from memory cache
        if self.memory_cache:
            with self.memory_cache._lock:
                expired_keys = []
                for key, entry in self.memory_cache._cache.items():
                    if entry.is_expired():
                        expired_keys.append(key)
                
                for key in expired_keys:
                    self.memory_cache._remove_entry(key)
                    total_cleared += 1
        
        # Clear expired from disk cache
        if self.disk_cache:
            with self.disk_cache._lock:
                self.disk_cache._cleanup_expired()
        
        if total_cleared > 0:
            self.logger.info(f"Cleared {total_cleared} expired cache entries")
        
        return total_cleared
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        stats = {
            'cache_type': self.cache_type.value,
            'memory_cache': None,
            'disk_cache': None
        }
        
        if self.memory_cache:
            stats['memory_cache'] = self.memory_cache.get_stats().to_dict()
        
        if self.disk_cache:
            stats['disk_cache'] = self.disk_cache.get_stats().to_dict()
        
        return stats
    
    @contextmanager
    def cached_operation(self, key: str, ttl: Optional[float] = None, 
                        tags: Optional[List[str]] = None):
        """Context manager for caching operation results."""
        # Check if result is already cached
        result = self.get(key)
        if result is not None:
            yield result
            return
        
        # Execute operation and cache result
        class CacheWrapper:
            def __init__(self, cache_manager):
                self.cache_manager = cache_manager
                self.result = None
            
            def set_result(self, value):
                self.result = value
                self.cache_manager.put(key, value, ttl, tags)
        
        wrapper = CacheWrapper(self)
        yield wrapper


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None
_cache_manager_lock = threading.Lock()


def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        with _cache_manager_lock:
            # Double-check locking pattern
            if _cache_manager is None:
                _cache_manager = CacheManager()
    return _cache_manager


def cached(key_func: Optional[Callable] = None, ttl: Optional[float] = None, 
          tags: Optional[List[str]] = None):
    """Decorator for caching function results."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hash((args, tuple(sorted(kwargs.items()))))}"
            
            cache_manager = get_cache_manager()
            
            # Try to get from cache
            result = cache_manager.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.put(cache_key, result, ttl, tags)
            
            return result
        return wrapper
    return decorator