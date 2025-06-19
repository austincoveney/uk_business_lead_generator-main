"""Performance optimization utilities for the UK Business Lead Generator.

This module provides tools for optimizing performance across the application,
including memory management, CPU optimization, and resource monitoring.
"""

import gc
import psutil
import threading
import time
from typing import Dict, List, Optional, Any, Callable
from functools import wraps, lru_cache
from dataclasses import dataclass
from collections import defaultdict
import logging


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    execution_time: float
    function_calls: int
    cache_hits: int
    cache_misses: int


class PerformanceMonitor:
    """Monitor and track performance metrics."""
    
    def __init__(self):
        self.metrics: Dict[str, List[PerformanceMetrics]] = defaultdict(list)
        self.function_calls: Dict[str, int] = defaultdict(int)
        self.cache_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {'hits': 0, 'misses': 0})
        self._lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
    
    def record_metrics(self, function_name: str, execution_time: float):
        """Record performance metrics for a function call."""
        try:
            process = psutil.Process()
            cpu_percent = process.cpu_percent()
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            memory_mb = memory_info.rss / 1024 / 1024
            
            with self._lock:
                self.function_calls[function_name] += 1
                cache_stats = self.cache_stats[function_name]
                
                metrics = PerformanceMetrics(
                    cpu_percent=cpu_percent,
                    memory_percent=memory_percent,
                    memory_mb=memory_mb,
                    execution_time=execution_time,
                    function_calls=self.function_calls[function_name],
                    cache_hits=cache_stats['hits'],
                    cache_misses=cache_stats['misses']
                )
                
                self.metrics[function_name].append(metrics)
                
                # Keep only last 100 metrics per function
                if len(self.metrics[function_name]) > 100:
                    self.metrics[function_name] = self.metrics[function_name][-100:]
                    
        except Exception as e:
            self.logger.warning(f"Failed to record metrics for {function_name}: {e}")
    
    def get_average_metrics(self, function_name: str) -> Optional[PerformanceMetrics]:
        """Get average performance metrics for a function."""
        with self._lock:
            if function_name not in self.metrics or not self.metrics[function_name]:
                return None
            
            metrics_list = self.metrics[function_name]
            count = len(metrics_list)
            
            avg_metrics = PerformanceMetrics(
                cpu_percent=sum(m.cpu_percent for m in metrics_list) / count,
                memory_percent=sum(m.memory_percent for m in metrics_list) / count,
                memory_mb=sum(m.memory_mb for m in metrics_list) / count,
                execution_time=sum(m.execution_time for m in metrics_list) / count,
                function_calls=metrics_list[-1].function_calls,
                cache_hits=metrics_list[-1].cache_hits,
                cache_misses=metrics_list[-1].cache_misses
            )
            
            return avg_metrics
    
    def record_cache_hit(self, function_name: str):
        """Record a cache hit for a function."""
        with self._lock:
            self.cache_stats[function_name]['hits'] += 1
    
    def record_cache_miss(self, function_name: str):
        """Record a cache miss for a function."""
        with self._lock:
            self.cache_stats[function_name]['misses'] += 1
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate a comprehensive performance report."""
        report = {}
        
        with self._lock:
            for function_name in self.metrics:
                avg_metrics = self.get_average_metrics(function_name)
                if avg_metrics:
                    cache_stats = self.cache_stats[function_name]
                    total_cache_ops = cache_stats['hits'] + cache_stats['misses']
                    cache_hit_rate = (cache_stats['hits'] / total_cache_ops * 100) if total_cache_ops > 0 else 0
                    
                    report[function_name] = {
                        'avg_cpu_percent': round(avg_metrics.cpu_percent, 2),
                        'avg_memory_mb': round(avg_metrics.memory_mb, 2),
                        'avg_execution_time_ms': round(avg_metrics.execution_time * 1000, 2),
                        'total_calls': avg_metrics.function_calls,
                        'cache_hit_rate_percent': round(cache_hit_rate, 2),
                        'total_cache_hits': cache_stats['hits'],
                        'total_cache_misses': cache_stats['misses']
                    }
        
        return report


# Global performance monitor instance
_performance_monitor = None
_monitor_lock = threading.Lock()


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    global _performance_monitor
    
    if _performance_monitor is None:
        with _monitor_lock:
            if _performance_monitor is None:
                _performance_monitor = PerformanceMonitor()
    
    return _performance_monitor


def performance_monitor(func: Callable) -> Callable:
    """Decorator to monitor function performance."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        monitor = get_performance_monitor()
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            execution_time = time.time() - start_time
            monitor.record_metrics(func.__name__, execution_time)
    
    return wrapper


def smart_cache(maxsize: int = 128, ttl: Optional[float] = None):
    """Enhanced caching decorator with TTL and performance monitoring."""
    def decorator(func: Callable) -> Callable:
        cache = {}
        cache_times = {}
        cache_lock = threading.Lock()
        monitor = get_performance_monitor()
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            key = str(args) + str(sorted(kwargs.items()))
            current_time = time.time()
            
            with cache_lock:
                # Check if key exists and is not expired
                if key in cache:
                    if ttl is None or (current_time - cache_times[key]) < ttl:
                        monitor.record_cache_hit(func.__name__)
                        return cache[key]
                    else:
                        # Remove expired entry
                        del cache[key]
                        del cache_times[key]
                
                # Cache miss
                monitor.record_cache_miss(func.__name__)
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Store in cache
                if len(cache) >= maxsize:
                    # Remove oldest entry
                    oldest_key = min(cache_times.keys(), key=lambda k: cache_times[k])
                    del cache[oldest_key]
                    del cache_times[oldest_key]
                
                cache[key] = result
                cache_times[key] = current_time
                
                return result
        
        # Add cache management methods
        wrapper.cache_clear = lambda: cache.clear() or cache_times.clear()
        wrapper.cache_info = lambda: {
            'size': len(cache),
            'maxsize': maxsize,
            'ttl': ttl,
            'hits': monitor.cache_stats[func.__name__]['hits'],
            'misses': monitor.cache_stats[func.__name__]['misses']
        }
        
        return wrapper
    
    return decorator


class MemoryOptimizer:
    """Utilities for memory optimization."""
    
    @staticmethod
    def force_garbage_collection():
        """Force garbage collection and return memory freed."""
        before = psutil.Process().memory_info().rss
        gc.collect()
        after = psutil.Process().memory_info().rss
        freed_mb = (before - after) / 1024 / 1024
        return freed_mb
    
    @staticmethod
    def get_memory_usage() -> Dict[str, float]:
        """Get current memory usage statistics."""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,
            'vms_mb': memory_info.vms / 1024 / 1024,
            'percent': process.memory_percent(),
            'available_mb': psutil.virtual_memory().available / 1024 / 1024
        }
    
    @staticmethod
    def optimize_large_lists(data_list: List[Any], chunk_size: int = 1000) -> List[List[Any]]:
        """Split large lists into smaller chunks for better memory management."""
        return [data_list[i:i + chunk_size] for i in range(0, len(data_list), chunk_size)]
    
    @staticmethod
    def memory_efficient_generator(data_list: List[Any]):
        """Convert list to memory-efficient generator."""
        for item in data_list:
            yield item


class CPUOptimizer:
    """Utilities for CPU optimization."""
    
    @staticmethod
    def get_optimal_thread_count() -> int:
        """Get optimal thread count based on CPU cores."""
        cpu_count = psutil.cpu_count(logical=False)  # Physical cores
        logical_count = psutil.cpu_count(logical=True)  # Logical cores
        
        # For I/O bound tasks, use more threads
        # For CPU bound tasks, use fewer threads
        return min(logical_count, cpu_count * 2)
    
    @staticmethod
    def get_cpu_usage() -> Dict[str, float]:
        """Get current CPU usage statistics."""
        return {
            'percent': psutil.cpu_percent(interval=1),
            'per_cpu': psutil.cpu_percent(interval=1, percpu=True),
            'load_avg': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
        }


def batch_processor(batch_size: int = 100):
    """Decorator to process data in batches for better performance."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(data_list: List[Any], *args, **kwargs):
            if not isinstance(data_list, list):
                return func(data_list, *args, **kwargs)
            
            results = []
            for i in range(0, len(data_list), batch_size):
                batch = data_list[i:i + batch_size]
                batch_result = func(batch, *args, **kwargs)
                if isinstance(batch_result, list):
                    results.extend(batch_result)
                else:
                    results.append(batch_result)
                
                # Optional: Force garbage collection between batches
                if i % (batch_size * 10) == 0:
                    gc.collect()
            
            return results
        
        return wrapper
    
    return decorator


def resource_monitor(memory_threshold_mb: float = 500, cpu_threshold_percent: float = 80):
    """Decorator to monitor resource usage and warn if thresholds are exceeded."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(__name__)
            
            # Check resources before execution
            memory_usage = MemoryOptimizer.get_memory_usage()
            cpu_usage = CPUOptimizer.get_cpu_usage()
            
            if memory_usage['rss_mb'] > memory_threshold_mb:
                logger.warning(f"High memory usage before {func.__name__}: {memory_usage['rss_mb']:.1f}MB")
            
            if cpu_usage['percent'] > cpu_threshold_percent:
                logger.warning(f"High CPU usage before {func.__name__}: {cpu_usage['percent']:.1f}%")
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Check resources after execution
            memory_usage_after = MemoryOptimizer.get_memory_usage()
            memory_increase = memory_usage_after['rss_mb'] - memory_usage['rss_mb']
            
            if memory_increase > 50:  # More than 50MB increase
                logger.warning(f"Function {func.__name__} increased memory by {memory_increase:.1f}MB")
            
            return result
        
        return wrapper
    
    return decorator