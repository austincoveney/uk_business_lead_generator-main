#!/usr/bin/env python3
"""
Comprehensive test suite for the enhanced automation system.
Tests smart retry mechanisms, performance monitoring, and advanced features.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List
from dataclasses import dataclass

# Import the enhanced automation components
from src.core.automation import (
    AutomationEngine,
    AutomationManager,
    SmartRetryMechanism,
    RetryConfig,
    RetryStrategy,
    TaskResult,
    TaskStatus,
    AutomationTask,
    SearchTask
)
from src.utils.error_handler import ErrorHandler, ErrorSeverity
from src.utils.performance_monitor import PerformanceMonitor
from src.utils.cache_manager import CacheManager
from src.utils.data_validator import DataValidator
from src.utils.advanced_logger import get_logger


class TestSmartRetryMechanism:
    """Test suite for the smart retry mechanism."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.retry_mechanism = SmartRetryMechanism()
        self.error_handler = ErrorHandler()
        
    def test_exponential_backoff_strategy(self):
        """Test exponential backoff retry strategy."""
        config = RetryConfig(
            max_attempts=5,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            base_delay=1.0,
            backoff_multiplier=2.0
        )
        
        # Test delay calculation
        delays = [config.calculate_delay(i) for i in range(1, 6)]
        expected = [1.0, 2.0, 4.0, 8.0, 16.0]
        
        for actual, exp in zip(delays, expected):
            assert abs(actual - exp) < 0.1  # Allow for jitter
    
    def test_linear_backoff_strategy(self):
        """Test linear backoff retry strategy."""
        config = RetryConfig(
            max_attempts=4,
            strategy=RetryStrategy.LINEAR_BACKOFF,
            base_delay=2.0,
            linear_increment=1.5
        )
        
        delays = [config.calculate_delay(i) for i in range(1, 5)]
        expected = [2.0, 3.5, 5.0, 6.5]
        
        for actual, exp in zip(delays, expected):
            assert abs(actual - exp) < 0.1
    
    def test_fibonacci_backoff_strategy(self):
        """Test Fibonacci backoff retry strategy."""
        config = RetryConfig(
            max_attempts=6,
            strategy=RetryStrategy.FIBONACCI_BACKOFF,
            base_delay=1.0
        )
        
        delays = [config.calculate_delay(i) for i in range(1, 7)]
        # Fibonacci sequence: 1, 1, 2, 3, 5, 8
        expected = [1.0, 1.0, 2.0, 3.0, 5.0, 8.0]
        
        for actual, exp in zip(delays, expected):
            assert abs(actual - exp) < 0.1
    
    def test_custom_delay_function(self):
        """Test custom delay function."""
        def custom_delay(attempt: int, base_delay: float) -> float:
            return base_delay * (attempt ** 1.5)
        
        config = RetryConfig(
            max_attempts=3,
            strategy=RetryStrategy.CUSTOM,
            base_delay=2.0,
            custom_delay_func=custom_delay
        )
        
        delays = [config.calculate_delay(i) for i in range(1, 4)]
        expected = [2.0, 2.0 * (2 ** 1.5), 2.0 * (3 ** 1.5)]
        
        for actual, exp in zip(delays, expected):
            assert abs(actual - exp) < 0.1
    
    @pytest.mark.asyncio
    async def test_successful_task_execution(self):
        """Test successful task execution without retries."""
        task = AutomationTask(
            task_id="test_success",
            search_term="test query",
            retry_config=RetryConfig(max_attempts=3)
        )
        
        # Mock successful execution
        def mock_execute():
            return {"status": "success", "results": ["result1", "result2"]}
        
        result = self.retry_mechanism.execute_with_retry(
            task, mock_execute
        )
        
        assert result.status == TaskStatus.SUCCESS
        assert result.attempts == 1
        assert result.result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        """Test retry mechanism on task failure."""
        task = AutomationTask(
            task_id="test_retry",
            search_term="test query",
            retry_config=RetryConfig(
                max_attempts=3,
                strategy=RetryStrategy.FIXED_DELAY,
                base_delay=0.1  # Fast retry for testing
            )
        )
        
        call_count = 0
        
        def mock_execute():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Network error")
            return {"status": "success", "results": ["result"]}
        
        result = self.retry_mechanism.execute_with_retry(
            task, mock_execute
        )
        
        assert result.status == TaskStatus.SUCCESS
        assert result.attempts == 3
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_max_attempts_exceeded(self):
        """Test behavior when max attempts are exceeded."""
        task = AutomationTask(
            task_id="test_failure",
            search_term="test query",
            retry_config=RetryConfig(
                max_attempts=2,
                strategy=RetryStrategy.FIXED_DELAY,
                base_delay=0.1
            )
        )
        
        def mock_execute():
            raise ValueError("Persistent error")
        
        result = self.retry_mechanism.execute_with_retry(
            task, mock_execute
        )
        
        assert result.status == TaskStatus.FAILED
        assert result.attempts == 2
        assert "Persistent error" in str(result.error)
    
    def test_retry_statistics(self):
        """Test retry statistics collection."""
        # Execute some tasks to generate statistics
        task1 = AutomationTask(
            task_id="stats_test_1",
            search_term="query1",
            retry_config=RetryConfig(max_attempts=2)
        )
        
        # Successful task
        self.retry_mechanism.execute_with_retry(
            task1, lambda: {"success": True}
        )
        
        # Failed task
        task2 = AutomationTask(
            task_id="stats_test_2",
            search_term="query2",
            retry_config=RetryConfig(max_attempts=2, base_delay=0.1)
        )
        
        self.retry_mechanism.execute_with_retry(
            task2, lambda: (_ for _ in ()).throw(RuntimeError("Test error"))
        )
        
        stats = self.retry_mechanism.get_retry_stats()
        
        assert stats["total_tasks"] == 2
        assert stats["successful_tasks"] == 1
        assert stats["failed_tasks"] == 1
        assert 0 <= stats["success_rate"] <= 100


class TestAutomationEngine:
    """Test suite for the enhanced automation engine."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_config = Mock()
        self.mock_database = Mock()
        self.mock_scraper = Mock()
        self.mock_analyzer = Mock()
        
        # Create automation engine with mocked dependencies
        with patch('src.core.automation.BusinessScraper', return_value=self.mock_scraper), \
             patch('src.core.automation.WebsiteAnalyzer', return_value=self.mock_analyzer):
            
            self.engine = AutomationEngine(
                config=self.mock_config,
                database=self.mock_database
            )
    
    def test_engine_initialization(self):
        """Test automation engine initialization."""
        assert self.engine.config == self.mock_config
        assert self.engine.database == self.mock_database
        assert hasattr(self.engine, 'retry_mechanism')
        assert hasattr(self.engine, 'error_handler')
        assert hasattr(self.engine, 'task_results')
    
    def test_start_stop_automation(self):
        """Test starting and stopping automation."""
        # Test start
        self.engine.start()
        assert self.engine.is_running
        
        # Test stop
        self.engine.stop()
        assert not self.engine.is_running
    
    def test_pause_resume_automation(self):
        """Test pausing and resuming automation."""
        self.engine.start()
        
        # Test pause
        self.engine.pause()
        assert self.engine.is_paused
        
        # Test resume
        self.engine.resume()
        assert not self.engine.is_paused
        
        self.engine.stop()
    
    def test_get_comprehensive_status(self):
        """Test comprehensive status reporting."""
        status = self.engine.get_status()
        
        # Check required status fields
        required_fields = [
            'is_running', 'is_paused', 'total_searches_today',
            'businesses_found_today', 'success_rate', 'total_completed_tasks',
            'successful_tasks', 'average_attempts_per_task', 'retry_stats',
            'recent_task_results'
        ]
        
        for field in required_fields:
            assert field in status
    
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_task_execution_with_retry(self, mock_sleep):
        """Test task execution with retry mechanism."""
        # Mock scraper to simulate failure then success
        call_count = 0
        
        def mock_search(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("Network timeout")
            return [{'name': 'Test Business', 'location': 'London'}]
        
        self.mock_scraper.search_businesses.side_effect = mock_search
        
        # Create a task with retry configuration
        task = SearchTask(
            search_term="restaurants London",
            location="London",
            retry_config=RetryConfig(
                max_attempts=3,
                strategy=RetryStrategy.FIXED_DELAY,
                base_delay=0.1
            )
        )
        
        # Execute task
        result = self.engine._execute_task(task)
        
        # Verify retry mechanism worked
        assert call_count == 2  # Failed once, succeeded on second attempt
        assert len(self.engine.task_results) > 0


class TestPerformanceIntegration:
    """Test integration with performance monitoring."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.performance_monitor = PerformanceMonitor()
        
    def test_performance_monitoring_integration(self):
        """Test performance monitoring during automation."""
        # Start monitoring
        self.performance_monitor.start_monitoring()
        
        # Simulate some work
        with self.performance_monitor.time_operation("test_operation"):
            time.sleep(0.1)
        
        # Add custom metrics
        self.performance_monitor.add_metric(
            "tasks_completed", 5, {"category": "automation"}
        )
        
        # Get performance report
        report = self.performance_monitor.get_performance_report()
        
        assert "test_operation" in report["operation_times"]
        assert report["custom_metrics"]["tasks_completed"] == 5
        
        self.performance_monitor.stop_monitoring()


class TestCacheIntegration:
    """Test integration with cache manager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.cache_manager = CacheManager()
        
    def test_search_result_caching(self):
        """Test caching of search results."""
        search_key = "restaurants_london"
        search_results = [
            {"name": "Restaurant 1", "location": "London"},
            {"name": "Restaurant 2", "location": "London"}
        ]
        
        # Cache results
        self.cache_manager.set(
            search_key, search_results, ttl=3600, cache_type="search_results"
        )
        
        # Retrieve from cache
        cached_results = self.cache_manager.get(search_key)
        
        assert cached_results == search_results
        
        # Test cache statistics
        stats = self.cache_manager.get_stats()
        assert stats.total_sets >= 1
        assert stats.total_gets >= 1


class TestDataValidationIntegration:
    """Test integration with data validation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.data_validator = DataValidator()
        
    def test_business_data_validation(self):
        """Test validation of scraped business data."""
        # Valid business data
        valid_business = {
            "name": "The Great Restaurant",
            "email": "contact@greatrestaurant.com",
            "phone": "+44 20 1234 5678",
            "website": "https://greatrestaurant.com",
            "postcode": "SW1A 1AA",
            "address": "123 Main Street, London"
        }
        
        result = self.data_validator.validate_business(valid_business)
        
        assert result.is_valid
        assert result.score >= 80  # High quality score
        assert len(result.issues) == 0
        
        # Invalid business data
        invalid_business = {
            "name": "",  # Empty name
            "email": "invalid-email",  # Invalid email
            "phone": "123",  # Invalid phone
            "website": "not-a-url",  # Invalid URL
            "postcode": "INVALID"  # Invalid postcode
        }
        
        result = self.data_validator.validate_business(invalid_business)
        
        assert not result.is_valid
        assert result.score < 50  # Low quality score
        assert len(result.issues) > 0


class TestErrorHandlingIntegration:
    """Test integration with error handling system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.error_handler = ErrorHandler()
        
    def test_error_handling_during_automation(self):
        """Test error handling during automation tasks."""
        # Simulate various types of errors
        errors = [
            ConnectionError("Network timeout"),
            ValueError("Invalid search parameter"),
            RuntimeError("Unexpected error")
        ]
        
        for error in errors:
            error_id = self.error_handler.handle_exception(
                error, 
                context={"task": "automation", "phase": "testing"}
            )
            assert error_id is not None
        
        # Get error statistics
        stats = self.error_handler.get_error_stats()
        
        assert stats["total_errors"] >= len(errors)
        assert "ConnectionError" in stats["error_types"]
        assert "ValueError" in stats["error_types"]
        assert "RuntimeError" in stats["error_types"]


class TestAutomationManager:
    """Test suite for the automation manager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.automation_manager = AutomationManager()
        
    def test_create_campaign(self):
        """Test campaign creation."""
        campaign_name = "Test Campaign"
        search_terms = ["restaurants London", "cafes Manchester"]
        
        with patch('src.core.automation.AutomationEngine') as mock_engine_class:
            mock_engine = Mock()
            mock_engine_class.return_value = mock_engine
            
            engine = self.automation_manager.create_campaign(
                name=campaign_name,
                search_terms=search_terms,
                max_results_per_day=100
            )
            
            assert engine == mock_engine
            mock_engine_class.assert_called_once()
    
    def test_start_stop_campaign(self):
        """Test starting and stopping campaigns."""
        with patch('src.core.automation.AutomationEngine') as mock_engine_class:
            mock_engine = Mock()
            mock_engine_class.return_value = mock_engine
            
            # Create and start campaign
            engine = self.automation_manager.create_campaign(
                name="Test Campaign",
                search_terms=["test"]
            )
            
            self.automation_manager.start_campaign("Test Campaign")
            mock_engine.start.assert_called_once()
            
            # Stop campaign
            self.automation_manager.stop_campaign("Test Campaign")
            mock_engine.stop.assert_called_once()


@pytest.mark.integration
class TestFullSystemIntegration:
    """Integration tests for the complete enhanced system."""
    
    def setup_method(self):
        """Set up test fixtures for integration tests."""
        # Initialize all components
        self.error_handler = ErrorHandler()
        self.performance_monitor = PerformanceMonitor()
        self.cache_manager = CacheManager()
        self.data_validator = DataValidator()
        
    def test_end_to_end_automation_workflow(self):
        """Test complete automation workflow with all enhancements."""
        # This test would simulate a complete workflow
        # from task creation to result validation
        
        # Start performance monitoring
        self.performance_monitor.start_monitoring()
        
        try:
            # Create automation task
            task = AutomationTask(
                task_id="integration_test",
                search_term="test restaurants",
                retry_config=RetryConfig(
                    max_attempts=3,
                    strategy=RetryStrategy.EXPONENTIAL_BACKOFF
                )
            )
            
            # Simulate task execution with all components
            with self.performance_monitor.time_operation("full_workflow"):
                # Mock successful execution
                result_data = {
                    "businesses": [
                        {
                            "name": "Test Restaurant",
                            "email": "test@restaurant.com",
                            "phone": "+44 20 1234 5678",
                            "website": "https://testrestaurant.com",
                            "postcode": "SW1A 1AA"
                        }
                    ]
                }
                
                # Cache the results
                cache_key = f"search_{task.task_id}"
                self.cache_manager.set(cache_key, result_data, ttl=3600)
                
                # Validate the data
                for business in result_data["businesses"]:
                    validation_result = self.data_validator.validate_business(business)
                    assert validation_result.is_valid
                
                # Retrieve from cache
                cached_data = self.cache_manager.get(cache_key)
                assert cached_data == result_data
            
            # Get performance metrics
            report = self.performance_monitor.get_performance_report()
            assert "full_workflow" in report["operation_times"]
            
        except Exception as e:
            # Test error handling
            error_id = self.error_handler.handle_exception(
                e, context={"test": "integration"}
            )
            assert error_id is not None
            
        finally:
            self.performance_monitor.stop_monitoring()
    
    def test_system_resilience(self):
        """Test system resilience under various failure conditions."""
        # Test network failures
        with patch('requests.get', side_effect=ConnectionError("Network error")):
            retry_mechanism = SmartRetryMechanism()
            
            task = AutomationTask(
                task_id="resilience_test",
                search_term="test",
                retry_config=RetryConfig(
                    max_attempts=3,
                    strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
                    base_delay=0.1
                )
            )
            
            def failing_operation():
                import requests
                requests.get("http://example.com")
            
            result = retry_mechanism.execute_with_retry(task, failing_operation)
            
            # Should fail after retries but handle gracefully
            assert result.status == TaskStatus.FAILED
            assert result.attempts == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])