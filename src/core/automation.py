"""Automation engine for continuous business lead generation"""

import time
import logging
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from ..utils.config import Config
from ..utils.logger import setup_logger
from .scraper import BusinessScraper
from .analyzer import WebsiteAnalyzer
from .database import LeadDatabase


class AutomationStatus(Enum):
    """Status of automation engine"""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


@dataclass
class SearchTask:
    """Individual search task configuration"""
    location: str
    business_type: Optional[str] = None
    limit: int = 50
    priority: int = 1  # 1=high, 2=medium, 3=low
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    enabled: bool = True
    

@dataclass
class AutomationConfig:
    """Configuration for automation engine"""
    # Timing settings
    search_interval_minutes: int = 60  # Time between searches
    max_concurrent_searches: int = 2
    daily_search_limit: int = 100
    
    # Operating hours
    start_hour: int = 9  # 24-hour format
    end_hour: int = 17
    weekend_enabled: bool = False
    
    # Quality controls
    min_contact_completeness: int = 30
    skip_analyzed_businesses: bool = True
    auto_analyze_websites: bool = True
    
    # Stopping conditions
    max_total_leads: Optional[int] = 1000
    max_runtime_hours: Optional[int] = 24
    stop_on_error_count: int = 10
    
    # Notification settings
    progress_callback: Optional[Callable] = None
    error_callback: Optional[Callable] = None
    completion_callback: Optional[Callable] = None


class AutomationEngine:
    """Continuous automation engine for business lead generation"""
    
    def __init__(self, config: AutomationConfig, database: LeadDatabase):
        self.config = config
        self.database = database
        self.logger = setup_logger('automation')
        
        # Core components
        self.scraper = BusinessScraper()
        self.analyzer = WebsiteAnalyzer()
        
        # State management
        self.status = AutomationStatus.STOPPED
        self.tasks: List[SearchTask] = []
        self.current_task: Optional[SearchTask] = None
        self.start_time: Optional[datetime] = None
        self.error_count = 0
        self.total_leads_found = 0
        self.daily_searches = 0
        self.last_reset_date = datetime.now().date()
        
        # Threading
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._automation_thread: Optional[threading.Thread] = None
        
    def add_task(self, task: SearchTask) -> None:
        """Add a search task to the automation queue"""
        self.tasks.append(task)
        self.logger.info(f"Added automation task: {task.location} - {task.business_type}")
        
    def remove_task(self, location: str, business_type: Optional[str] = None) -> bool:
        """Remove a task from the automation queue"""
        for i, task in enumerate(self.tasks):
            if task.location == location and task.business_type == business_type:
                del self.tasks[i]
                self.logger.info(f"Removed automation task: {location} - {business_type}")
                return True
        return False
        
    def start(self) -> bool:
        """Start the automation engine"""
        if self.status == AutomationStatus.RUNNING:
            self.logger.warning("Automation engine is already running")
            return False
            
        if not self.tasks:
            self.logger.error("No tasks configured for automation")
            return False
            
        self.status = AutomationStatus.RUNNING
        self.start_time = datetime.now()
        self.error_count = 0
        self._stop_event.clear()
        self._pause_event.clear()
        
        # Start automation thread
        self._automation_thread = threading.Thread(target=self._automation_loop, daemon=True)
        self._automation_thread.start()
        
        self.logger.info("Automation engine started")
        return True
        
    def stop(self) -> None:
        """Stop the automation engine"""
        if self.status == AutomationStatus.STOPPED:
            return
            
        self._stop_event.set()
        self.status = AutomationStatus.STOPPED
        
        if self._automation_thread and self._automation_thread.is_alive():
            self._automation_thread.join(timeout=5)
            
        self.logger.info("Automation engine stopped")
        
    def pause(self) -> None:
        """Pause the automation engine"""
        if self.status == AutomationStatus.RUNNING:
            self._pause_event.set()
            self.status = AutomationStatus.PAUSED
            self.logger.info("Automation engine paused")
            
    def resume(self) -> None:
        """Resume the automation engine"""
        if self.status == AutomationStatus.PAUSED:
            self._pause_event.clear()
            self.status = AutomationStatus.RUNNING
            self.logger.info("Automation engine resumed")
            
    def get_status(self) -> Dict:
        """Get current automation status and statistics"""
        runtime = None
        if self.start_time:
            runtime = datetime.now() - self.start_time
            
        return {
            'status': self.status.value,
            'current_task': {
                'location': self.current_task.location if self.current_task else None,
                'business_type': self.current_task.business_type if self.current_task else None
            },
            'statistics': {
                'total_leads_found': self.total_leads_found,
                'daily_searches': self.daily_searches,
                'error_count': self.error_count,
                'runtime_minutes': runtime.total_seconds() / 60 if runtime else 0,
                'tasks_remaining': len([t for t in self.tasks if t.enabled])
            },
            'next_task_time': self._get_next_task_time()
        }
        
    def _automation_loop(self) -> None:
        """Main automation loop"""
        try:
            while not self._stop_event.is_set():
                # Check if paused
                if self._pause_event.is_set():
                    time.sleep(1)
                    continue
                    
                # Reset daily counter if needed
                self._reset_daily_counter_if_needed()
                
                # Check stopping conditions
                if self._should_stop():
                    break
                    
                # Check operating hours
                if not self._is_operating_hours():
                    self.logger.info("Outside operating hours, waiting...")
                    time.sleep(300)  # Check every 5 minutes
                    continue
                    
                # Find next task to run
                task = self._get_next_task()
                if not task:
                    self.logger.info("No tasks ready to run, waiting...")
                    time.sleep(60)  # Wait 1 minute
                    continue
                    
                # Execute task
                self._execute_task(task)
                
                # Wait before next iteration
                time.sleep(30)  # Check every 30 seconds
                
        except Exception as e:
            self.logger.error(f"Automation loop error: {e}")
            self.status = AutomationStatus.ERROR
            if self.config.error_callback:
                self.config.error_callback(str(e))
        finally:
            self.status = AutomationStatus.STOPPED
            if self.config.completion_callback:
                self.config.completion_callback(self.get_status())
                
    def _execute_task(self, task: SearchTask) -> None:
        """Execute a single search task"""
        self.current_task = task
        task.last_run = datetime.now()
        
        try:
            self.logger.info(f"Executing task: {task.location} - {task.business_type}")
            
            # Perform search
            businesses = self.scraper.search_businesses(
                location=task.location,
                business_type=task.business_type,
                limit=task.limit
            )
            
            new_leads = 0
            for business in businesses:
                # Check if business already exists
                if self.config.skip_analyzed_businesses:
                    existing = self.database.get_business_by_name_and_location(
                        business.get('name', ''),
                        business.get('address', '')
                    )
                    if existing:
                        continue
                        
                # Filter by contact completeness
                completeness = business.get('contact_completeness', 0)
                if completeness < self.config.min_contact_completeness:
                    continue
                    
                # Add to database
                business_id = self.database.add_business(business)
                new_leads += 1
                
                # Analyze website if enabled
                if self.config.auto_analyze_websites and business.get('website'):
                    try:
                        analysis = self.analyzer.analyze_website(business['website'])
                        self.database.update_business_analysis(business_id, analysis)
                    except Exception as e:
                        self.logger.warning(f"Website analysis failed for {business['website']}: {e}")
                        
            self.total_leads_found += new_leads
            self.daily_searches += 1
            
            # Schedule next run
            task.next_run = datetime.now() + timedelta(minutes=self.config.search_interval_minutes)
            
            self.logger.info(f"Task completed: {new_leads} new leads found")
            
            # Progress callback
            if self.config.progress_callback:
                self.config.progress_callback({
                    'task': task,
                    'new_leads': new_leads,
                    'total_leads': self.total_leads_found
                })
                
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"Task execution failed: {e}")
            
            # Schedule retry (with backoff)
            retry_delay = min(60 * (2 ** min(self.error_count, 5)), 3600)  # Max 1 hour
            task.next_run = datetime.now() + timedelta(seconds=retry_delay)
            
            if self.config.error_callback:
                self.config.error_callback(f"Task failed: {task.location} - {e}")
        finally:
            self.current_task = None
            
    def _get_next_task(self) -> Optional[SearchTask]:
        """Get the next task that should be executed"""
        now = datetime.now()
        ready_tasks = []
        
        for task in self.tasks:
            if not task.enabled:
                continue
                
            # First run or scheduled time reached
            if task.next_run is None or task.next_run <= now:
                ready_tasks.append(task)
                
        if not ready_tasks:
            return None
            
        # Sort by priority (1=highest) then by last run time
        ready_tasks.sort(key=lambda t: (t.priority, t.last_run or datetime.min))
        return ready_tasks[0]
        
    def _get_next_task_time(self) -> Optional[datetime]:
        """Get the time when the next task will run"""
        next_times = [t.next_run for t in self.tasks if t.enabled and t.next_run]
        return min(next_times) if next_times else None
        
    def _should_stop(self) -> bool:
        """Check if automation should stop based on configured conditions"""
        # Max leads reached
        if (self.config.max_total_leads and 
            self.total_leads_found >= self.config.max_total_leads):
            self.logger.info(f"Max leads reached: {self.total_leads_found}")
            return True
            
        # Max runtime reached
        if (self.config.max_runtime_hours and self.start_time and
            datetime.now() - self.start_time >= timedelta(hours=self.config.max_runtime_hours)):
            self.logger.info("Max runtime reached")
            return True
            
        # Too many errors
        if self.error_count >= self.config.stop_on_error_count:
            self.logger.error(f"Too many errors: {self.error_count}")
            return True
            
        # Daily search limit reached
        if self.daily_searches >= self.config.daily_search_limit:
            self.logger.info(f"Daily search limit reached: {self.daily_searches}")
            return True
            
        return False
        
    def _is_operating_hours(self) -> bool:
        """Check if current time is within operating hours"""
        now = datetime.now()
        
        # Check weekend
        if not self.config.weekend_enabled and now.weekday() >= 5:  # Saturday=5, Sunday=6
            return False
            
        # Check hours
        current_hour = now.hour
        if self.config.start_hour <= self.config.end_hour:
            # Same day (e.g., 9 AM to 5 PM)
            return self.config.start_hour <= current_hour < self.config.end_hour
        else:
            # Overnight (e.g., 10 PM to 6 AM)
            return current_hour >= self.config.start_hour or current_hour < self.config.end_hour
            
    def _reset_daily_counter_if_needed(self) -> None:
        """Reset daily search counter if it's a new day"""
        today = datetime.now().date()
        if today != self.last_reset_date:
            self.daily_searches = 0
            self.last_reset_date = today
            self.logger.info("Daily search counter reset")


class AutomationManager:
    """High-level manager for automation features"""
    
    def __init__(self, database: LeadDatabase):
        self.database = database
        self.engine: Optional[AutomationEngine] = None
        self.logger = setup_logger('automation_manager')
        
    def create_preset_campaigns(self) -> List[SearchTask]:
        """Create preset automation campaigns for common scenarios"""
        campaigns = [
            # Major UK cities
            SearchTask("London", "Technology", limit=100, priority=1),
            SearchTask("Manchester", "Technology", limit=50, priority=1),
            SearchTask("Birmingham", "Technology", limit=50, priority=1),
            SearchTask("Leeds", "Technology", limit=30, priority=2),
            SearchTask("Glasgow", "Technology", limit=30, priority=2),
            
            # Business services
            SearchTask("London", "Consulting", limit=50, priority=1),
            SearchTask("London", "Marketing", limit=50, priority=1),
            SearchTask("London", "Finance", limit=50, priority=2),
            
            # Regional coverage
            SearchTask("Bristol", None, limit=30, priority=2),
            SearchTask("Edinburgh", None, limit=30, priority=2),
            SearchTask("Cardiff", None, limit=30, priority=3),
            SearchTask("Belfast", None, limit=30, priority=3),
        ]
        
        return campaigns
        
    def start_automation(self, config: AutomationConfig, tasks: List[SearchTask]) -> bool:
        """Start automation with given configuration and tasks"""
        if self.engine and self.engine.status == AutomationStatus.RUNNING:
            self.logger.warning("Automation is already running")
            return False
            
        self.engine = AutomationEngine(config, self.database)
        
        # Add tasks
        for task in tasks:
            self.engine.add_task(task)
            
        return self.engine.start()
        
    def stop_automation(self) -> None:
        """Stop current automation"""
        if self.engine:
            self.engine.stop()
            
    def get_automation_status(self) -> Optional[Dict]:
        """Get current automation status"""
        if self.engine:
            return self.engine.get_status()
        return None