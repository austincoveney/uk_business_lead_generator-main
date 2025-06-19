"""Performance monitoring and metrics collection system."""

import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from collections import deque, defaultdict
import json
from pathlib import Path
import logging
from contextlib import contextmanager


@dataclass
class PerformanceMetric:
    """Individual performance metric data point."""
    timestamp: datetime
    metric_name: str
    value: float
    unit: str
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'metric_name': self.metric_name,
            'value': self.value,
            'unit': self.unit,
            'tags': self.tags
        }


@dataclass
class SystemMetrics:
    """System resource metrics snapshot."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_free_gb: float
    network_bytes_sent: int
    network_bytes_recv: int
    active_threads: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'cpu_percent': self.cpu_percent,
            'memory_percent': self.memory_percent,
            'memory_used_mb': self.memory_used_mb,
            'memory_available_mb': self.memory_available_mb,
            'disk_usage_percent': self.disk_usage_percent,
            'disk_free_gb': self.disk_free_gb,
            'network_bytes_sent': self.network_bytes_sent,
            'network_bytes_recv': self.network_bytes_recv,
            'active_threads': self.active_threads
        }


@dataclass
class PerformanceAlert:
    """Performance alert configuration."""
    metric_name: str
    threshold: float
    comparison: str  # 'gt', 'lt', 'eq'
    duration_seconds: int
    callback: Optional[Callable[[PerformanceMetric], None]] = None
    enabled: bool = True
    last_triggered: Optional[datetime] = None
    
    def should_trigger(self, metric: PerformanceMetric) -> bool:
        """Check if alert should be triggered."""
        if not self.enabled or metric.metric_name != self.metric_name:
            return False
            
        # Check cooldown period
        if self.last_triggered:
            cooldown = timedelta(seconds=self.duration_seconds)
            if datetime.now() - self.last_triggered < cooldown:
                return False
        
        # Check threshold
        if self.comparison == 'gt':
            return metric.value > self.threshold
        elif self.comparison == 'lt':
            return metric.value < self.threshold
        elif self.comparison == 'eq':
            return abs(metric.value - self.threshold) < 0.001
        
        return False


class PerformanceMonitor:
    """Comprehensive performance monitoring system."""
    
    def __init__(self, 
                 max_metrics: int = 10000,
                 collection_interval: float = 5.0,
                 auto_start: bool = True):
        self.max_metrics = max_metrics
        self.collection_interval = collection_interval
        self.logger = logging.getLogger(__name__)
        
        # Metrics storage
        self.metrics: deque = deque(maxlen=max_metrics)
        self.system_metrics: deque = deque(maxlen=max_metrics)
        self.custom_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Performance tracking
        self.operation_timers: Dict[str, float] = {}
        self.operation_stats: Dict[str, Dict] = defaultdict(lambda: {
            'count': 0,
            'total_time': 0.0,
            'min_time': float('inf'),
            'max_time': 0.0,
            'avg_time': 0.0
        })
        
        # Alerts
        self.alerts: List[PerformanceAlert] = []
        
        # Monitoring control
        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Network baseline for delta calculations
        self._last_network_stats = None
        
        if auto_start:
            self.start_monitoring()
    
    def start_monitoring(self) -> None:
        """Start background system metrics collection."""
        if self.monitoring_active:
            return
            
        self.monitoring_active = True
        self._stop_event.clear()
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitoring_thread.start()
        self.logger.info("Performance monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop background system metrics collection."""
        if not self.monitoring_active:
            return
            
        self.monitoring_active = False
        self._stop_event.set()
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5.0)
            
        self.logger.info("Performance monitoring stopped")
    
    def _monitoring_loop(self) -> None:
        """Background monitoring loop."""
        while not self._stop_event.wait(self.collection_interval):
            try:
                self._collect_system_metrics()
            except Exception as e:
                self.logger.error(f"Error collecting system metrics: {e}")
    
    def collect_system_metrics(self) -> None:
        """Public method to collect current system metrics."""
        self._collect_system_metrics()
    
    def _collect_system_metrics(self) -> None:
        """Collect current system metrics."""
        try:
            # CPU and Memory
            cpu_percent = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Network stats
            network = psutil.net_io_counters()
            
            # Thread count
            active_threads = threading.active_count()
            
            # Create metrics
            timestamp = datetime.now()
            
            system_metric = SystemMetrics(
                timestamp=timestamp,
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / (1024 * 1024),
                memory_available_mb=memory.available / (1024 * 1024),
                disk_usage_percent=disk.used / disk.total * 100,
                disk_free_gb=disk.free / (1024 * 1024 * 1024),
                network_bytes_sent=network.bytes_sent,
                network_bytes_recv=network.bytes_recv,
                active_threads=active_threads
            )
            
            self.system_metrics.append(system_metric)
            
            # Create individual metrics for alerting
            metrics_to_add = [
                PerformanceMetric(timestamp, 'cpu_percent', cpu_percent, '%'),
                PerformanceMetric(timestamp, 'memory_percent', memory.percent, '%'),
                PerformanceMetric(timestamp, 'memory_used_mb', memory.used / (1024 * 1024), 'MB'),
                PerformanceMetric(timestamp, 'disk_usage_percent', disk.used / disk.total * 100, '%'),
                PerformanceMetric(timestamp, 'active_threads', active_threads, 'count')
            ]
            
            for metric in metrics_to_add:
                self.add_metric(metric)
                
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
    
    def add_metric(self, metric: PerformanceMetric) -> None:
        """Add a custom performance metric."""
        self.metrics.append(metric)
        self.custom_metrics[metric.metric_name].append(metric)
        
        # Check alerts
        self._check_alerts(metric)
    
    def _check_alerts(self, metric: PerformanceMetric) -> None:
        """Check if any alerts should be triggered."""
        for alert in self.alerts:
            if alert.should_trigger(metric):
                alert.last_triggered = datetime.now()
                self.logger.warning(
                    f"Performance alert triggered: {alert.metric_name} "
                    f"{alert.comparison} {alert.threshold} (current: {metric.value})"
                )
                
                if alert.callback:
                    try:
                        alert.callback(metric)
                    except Exception as e:
                        self.logger.error(f"Error in alert callback: {e}")
    
    def add_alert(self, alert: PerformanceAlert) -> None:
        """Add a performance alert."""
        self.alerts.append(alert)
        self.logger.info(f"Added performance alert for {alert.metric_name}")
    
    @contextmanager
    def time_operation(self, operation_name: str, tags: Optional[Dict[str, str]] = None):
        """Context manager for timing operations."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.record_operation_time(operation_name, duration, tags or {})
    
    def record_operation_time(self, operation_name: str, duration: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record the execution time of an operation."""
        # Update operation statistics
        stats = self.operation_stats[operation_name]
        stats['count'] += 1
        stats['total_time'] += duration
        stats['min_time'] = min(stats['min_time'], duration)
        stats['max_time'] = max(stats['max_time'], duration)
        stats['avg_time'] = stats['total_time'] / stats['count']
        
        # Add as metric
        metric = PerformanceMetric(
            timestamp=datetime.now(),
            metric_name=f"operation_time_{operation_name}",
            value=duration,
            unit='seconds',
            tags=tags or {}
        )
        self.add_metric(metric)
    
    def get_operation_stats(self, operation_name: Optional[str] = None) -> Dict:
        """Get operation timing statistics."""
        if operation_name:
            return self.operation_stats.get(operation_name, {})
        return dict(self.operation_stats)
    
    def get_system_metrics_summary(self, minutes: int = 60) -> Dict:
        """Get summary of system metrics for the last N minutes."""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_metrics = [
            m for m in self.system_metrics 
            if m.timestamp >= cutoff_time
        ]
        
        if not recent_metrics:
            return {}
        
        # Calculate averages
        avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
        avg_disk = sum(m.disk_usage_percent for m in recent_metrics) / len(recent_metrics)
        
        # Get current values
        latest = recent_metrics[-1]
        
        return {
            'period_minutes': minutes,
            'samples_count': len(recent_metrics),
            'averages': {
                'cpu_percent': round(avg_cpu, 2),
                'memory_percent': round(avg_memory, 2),
                'disk_usage_percent': round(avg_disk, 2)
            },
            'current': {
                'cpu_percent': latest.cpu_percent,
                'memory_percent': latest.memory_percent,
                'memory_used_mb': round(latest.memory_used_mb, 2),
                'disk_free_gb': round(latest.disk_free_gb, 2),
                'active_threads': latest.active_threads
            }
        }
    
    def get_performance_report(self) -> Dict:
        """Get comprehensive performance report."""
        return {
            'monitoring_active': self.monitoring_active,
            'collection_interval': self.collection_interval,
            'total_metrics': len(self.metrics),
            'system_metrics_count': len(self.system_metrics),
            'custom_metrics_count': {name: len(metrics) for name, metrics in self.custom_metrics.items()},
            'operation_stats': self.get_operation_stats(),
            'system_summary': self.get_system_metrics_summary(),
            'alerts_count': len(self.alerts),
            'active_alerts': len([a for a in self.alerts if a.enabled])
        }
    
    def export_metrics(self, file_path: str, format: str = 'json') -> None:
        """Export metrics to file."""
        try:
            data = {
                'export_timestamp': datetime.now().isoformat(),
                'system_metrics': [m.to_dict() for m in self.system_metrics],
                'custom_metrics': {
                    name: [m.to_dict() for m in metrics]
                    for name, metrics in self.custom_metrics.items()
                },
                'operation_stats': self.get_operation_stats(),
                'performance_report': self.get_performance_report()
            }
            
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            if format.lower() == 'json':
                with open(path, 'w') as f:
                    json.dump(data, f, indent=2)
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
            self.logger.info(f"Metrics exported to {file_path}")
            
        except Exception as e:
            self.logger.error(f"Error exporting metrics: {e}")
            raise
    
    def clear_metrics(self) -> None:
        """Clear all stored metrics."""
        self.metrics.clear()
        self.system_metrics.clear()
        self.custom_metrics.clear()
        self.operation_stats.clear()
        self.logger.info("All metrics cleared")
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        self.stop_monitoring()


# Global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def time_operation(operation_name: str, tags: Optional[Dict[str, str]] = None):
    """Decorator for timing function execution."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            with monitor.time_operation(operation_name, tags):
                return func(*args, **kwargs)
        return wrapper
    return decorator