"""Automation panel for continuous lead generation"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QLineEdit, QSpinBox, QComboBox,
    QCheckBox, QTextEdit, QTableWidget, QTableWidgetItem,
    QGroupBox, QProgressBar, QTabWidget, QTimeEdit,
    QMessageBox, QDialog, QDialogButtonBox, QFormLayout,
    QHeaderView, QFrame, QSplitter
)
from PySide6.QtCore import QTimer, Qt, Signal, QTime
from PySide6.QtGui import QFont, QIcon, QPalette

from ..core.automation import (
    AutomationEngine, AutomationConfig, SearchTask,
    AutomationStatus, AutomationManager
)
from ..core.database import LeadDatabase
from ..utils.logger import setup_logger


class TaskConfigDialog(QDialog):
    """Dialog for configuring automation tasks"""
    
    def __init__(self, parent=None, task: Optional[SearchTask] = None):
        super().__init__(parent)
        self.task = task
        self.setWindowTitle("Configure Automation Task")
        self.setModal(True)
        self.resize(400, 300)
        
        self.setup_ui()
        if task:
            self.load_task(task)
            
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Location
        self.location_edit = QLineEdit()
        self.location_edit.setPlaceholderText("e.g., London, Manchester, SW1A 1AA")
        form_layout.addRow("Location:", self.location_edit)
        
        # Business type
        self.business_type_combo = QComboBox()
        self.business_type_combo.setEditable(True)
        self.business_type_combo.addItems([
            "", "Technology", "Consulting", "Marketing", "Finance",
            "Healthcare", "Education", "Retail", "Manufacturing",
            "Construction", "Real Estate", "Legal", "Accounting"
        ])
        form_layout.addRow("Business Type:", self.business_type_combo)
        
        # Search limit
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(1, 500)
        self.limit_spin.setValue(50)
        form_layout.addRow("Search Limit:", self.limit_spin)
        
        # Priority
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["High (1)", "Medium (2)", "Low (3)"])
        form_layout.addRow("Priority:", self.priority_combo)
        
        # Enabled
        self.enabled_check = QCheckBox("Enabled")
        self.enabled_check.setChecked(True)
        form_layout.addRow("", self.enabled_check)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def load_task(self, task: SearchTask):
        """Load task data into form"""
        self.location_edit.setText(task.location)
        if task.business_type:
            self.business_type_combo.setCurrentText(task.business_type)
        self.limit_spin.setValue(task.limit)
        self.priority_combo.setCurrentIndex(task.priority - 1)
        self.enabled_check.setChecked(task.enabled)
        
    def get_task(self) -> SearchTask:
        """Get task from form data"""
        business_type = self.business_type_combo.currentText().strip()
        if not business_type:
            business_type = None
            
        return SearchTask(
            location=self.location_edit.text().strip(),
            business_type=business_type,
            limit=self.limit_spin.value(),
            priority=self.priority_combo.currentIndex() + 1,
            enabled=self.enabled_check.isChecked()
        )


class AutomationConfigDialog(QDialog):
    """Dialog for configuring automation settings"""
    
    def __init__(self, parent=None, config: Optional[AutomationConfig] = None):
        super().__init__(parent)
        self.config = config or AutomationConfig()
        self.setWindowTitle("Automation Configuration")
        self.setModal(True)
        self.resize(500, 600)
        
        self.setup_ui()
        self.load_config()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Tab widget
        tabs = QTabWidget()
        
        # Timing tab
        timing_tab = QWidget()
        timing_layout = QFormLayout(timing_tab)
        
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 1440)  # 1 minute to 24 hours
        self.interval_spin.setSuffix(" minutes")
        timing_layout.addRow("Search Interval:", self.interval_spin)
        
        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setRange(1, 10)
        timing_layout.addRow("Max Concurrent Searches:", self.concurrent_spin)
        
        self.daily_limit_spin = QSpinBox()
        self.daily_limit_spin.setRange(1, 1000)
        timing_layout.addRow("Daily Search Limit:", self.daily_limit_spin)
        
        tabs.addTab(timing_tab, "Timing")
        
        # Operating hours tab
        hours_tab = QWidget()
        hours_layout = QFormLayout(hours_tab)
        
        self.start_time = QTimeEdit()
        self.start_time.setTime(QTime(9, 0))
        hours_layout.addRow("Start Time:", self.start_time)
        
        self.end_time = QTimeEdit()
        self.end_time.setTime(QTime(17, 0))
        hours_layout.addRow("End Time:", self.end_time)
        
        self.weekend_check = QCheckBox("Enable Weekend Operation")
        hours_layout.addRow("", self.weekend_check)
        
        tabs.addTab(hours_tab, "Operating Hours")
        
        # Quality controls tab
        quality_tab = QWidget()
        quality_layout = QFormLayout(quality_tab)
        
        self.min_completeness_spin = QSpinBox()
        self.min_completeness_spin.setRange(0, 100)
        self.min_completeness_spin.setSuffix("%")
        quality_layout.addRow("Min Contact Completeness:", self.min_completeness_spin)
        
        self.skip_analyzed_check = QCheckBox("Skip Already Analyzed Businesses")
        quality_layout.addRow("", self.skip_analyzed_check)
        
        self.auto_analyze_check = QCheckBox("Auto-Analyze Websites")
        quality_layout.addRow("", self.auto_analyze_check)
        
        tabs.addTab(quality_tab, "Quality Controls")
        
        # Stopping conditions tab
        stopping_tab = QWidget()
        stopping_layout = QFormLayout(stopping_tab)
        
        self.max_leads_spin = QSpinBox()
        self.max_leads_spin.setRange(0, 10000)
        self.max_leads_spin.setSpecialValueText("No limit")
        stopping_layout.addRow("Max Total Leads:", self.max_leads_spin)
        
        self.max_runtime_spin = QSpinBox()
        self.max_runtime_spin.setRange(0, 168)  # Up to 1 week
        self.max_runtime_spin.setSpecialValueText("No limit")
        self.max_runtime_spin.setSuffix(" hours")
        stopping_layout.addRow("Max Runtime:", self.max_runtime_spin)
        
        self.max_errors_spin = QSpinBox()
        self.max_errors_spin.setRange(1, 100)
        stopping_layout.addRow("Stop After Errors:", self.max_errors_spin)
        
        tabs.addTab(stopping_tab, "Stopping Conditions")
        
        layout.addWidget(tabs)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def load_config(self):
        """Load configuration into form"""
        self.interval_spin.setValue(self.config.search_interval_minutes)
        self.concurrent_spin.setValue(self.config.max_concurrent_searches)
        self.daily_limit_spin.setValue(self.config.daily_search_limit)
        
        self.start_time.setTime(QTime(self.config.start_hour, 0))
        self.end_time.setTime(QTime(self.config.end_hour, 0))
        self.weekend_check.setChecked(self.config.weekend_enabled)
        
        self.min_completeness_spin.setValue(self.config.min_contact_completeness)
        self.skip_analyzed_check.setChecked(self.config.skip_analyzed_businesses)
        self.auto_analyze_check.setChecked(self.config.auto_analyze_websites)
        
        if self.config.max_total_leads:
            self.max_leads_spin.setValue(self.config.max_total_leads)
        if self.config.max_runtime_hours:
            self.max_runtime_spin.setValue(self.config.max_runtime_hours)
        self.max_errors_spin.setValue(self.config.stop_on_error_count)
        
    def get_config(self) -> AutomationConfig:
        """Get configuration from form"""
        return AutomationConfig(
            search_interval_minutes=self.interval_spin.value(),
            max_concurrent_searches=self.concurrent_spin.value(),
            daily_search_limit=self.daily_limit_spin.value(),
            start_hour=self.start_time.time().hour(),
            end_hour=self.end_time.time().hour(),
            weekend_enabled=self.weekend_check.isChecked(),
            min_contact_completeness=self.min_completeness_spin.value(),
            skip_analyzed_businesses=self.skip_analyzed_check.isChecked(),
            auto_analyze_websites=self.auto_analyze_check.isChecked(),
            max_total_leads=self.max_leads_spin.value() if self.max_leads_spin.value() > 0 else None,
            max_runtime_hours=self.max_runtime_spin.value() if self.max_runtime_spin.value() > 0 else None,
            stop_on_error_count=self.max_errors_spin.value()
        )


class AutomationPanel(QWidget):
    """Main automation panel widget"""
    
    automation_started = Signal()
    automation_stopped = Signal()
    
    def __init__(self, database: LeadDatabase, parent=None):
        super().__init__(parent)
        self.database = database
        self.automation_manager = AutomationManager(database)
        self.logger = setup_logger('automation_panel')
        
        # State
        self.tasks: List[SearchTask] = []
        self.config = AutomationConfig()
        
        self.setup_ui()
        self.setup_timer()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Automation Control")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Status indicator
        self.status_label = QLabel("Stopped")
        self.status_label.setStyleSheet(
            "QLabel { background-color: #ff4444; color: white; "
            "padding: 4px 8px; border-radius: 4px; }"
        )
        header_layout.addWidget(self.status_label)
        
        layout.addLayout(header_layout)
        
        # Main content splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Controls
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        
        # Control buttons
        button_layout = QGridLayout()
        
        self.start_btn = QPushButton("Start Automation")
        self.start_btn.clicked.connect(self.start_automation)
        button_layout.addWidget(self.start_btn, 0, 0)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_automation)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn, 0, 1)
        
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.pause_automation)
        self.pause_btn.setEnabled(False)
        button_layout.addWidget(self.pause_btn, 1, 0)
        
        self.resume_btn = QPushButton("Resume")
        self.resume_btn.clicked.connect(self.resume_automation)
        self.resume_btn.setEnabled(False)
        button_layout.addWidget(self.resume_btn, 1, 1)
        
        controls_layout.addLayout(button_layout)
        
        # Configuration
        config_group = QGroupBox("Configuration")
        config_layout = QVBoxLayout(config_group)
        
        config_btn_layout = QHBoxLayout()
        
        self.config_btn = QPushButton("Configure Settings")
        self.config_btn.clicked.connect(self.configure_automation)
        config_btn_layout.addWidget(self.config_btn)
        
        self.preset_btn = QPushButton("Load Presets")
        self.preset_btn.clicked.connect(self.load_presets)
        config_btn_layout.addWidget(self.preset_btn)
        
        config_layout.addLayout(config_btn_layout)
        controls_layout.addWidget(config_group)
        
        # Statistics
        stats_group = QGroupBox("Statistics")
        stats_layout = QFormLayout(stats_group)
        
        self.total_leads_label = QLabel("0")
        stats_layout.addRow("Total Leads Found:", self.total_leads_label)
        
        self.daily_searches_label = QLabel("0")
        stats_layout.addRow("Daily Searches:", self.daily_searches_label)
        
        self.runtime_label = QLabel("0 minutes")
        stats_layout.addRow("Runtime:", self.runtime_label)
        
        self.error_count_label = QLabel("0")
        stats_layout.addRow("Errors:", self.error_count_label)
        
        self.next_task_label = QLabel("None")
        stats_layout.addRow("Next Task:", self.next_task_label)
        
        controls_layout.addWidget(stats_group)
        
        # Progress
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.current_task_label = QLabel("No active task")
        progress_layout.addWidget(self.current_task_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        controls_layout.addWidget(progress_group)
        
        controls_layout.addStretch()
        splitter.addWidget(controls_widget)
        
        # Right panel - Tasks
        tasks_widget = QWidget()
        tasks_layout = QVBoxLayout(tasks_widget)
        
        # Tasks header
        tasks_header = QHBoxLayout()
        
        tasks_title = QLabel("Automation Tasks")
        tasks_title.setFont(title_font)
        tasks_header.addWidget(tasks_title)
        
        tasks_header.addStretch()
        
        self.add_task_btn = QPushButton("Add Task")
        self.add_task_btn.clicked.connect(self.add_task)
        tasks_header.addWidget(self.add_task_btn)
        
        self.edit_task_btn = QPushButton("Edit")
        self.edit_task_btn.clicked.connect(self.edit_task)
        self.edit_task_btn.setEnabled(False)
        tasks_header.addWidget(self.edit_task_btn)
        
        self.remove_task_btn = QPushButton("Remove")
        self.remove_task_btn.clicked.connect(self.remove_task)
        self.remove_task_btn.setEnabled(False)
        tasks_header.addWidget(self.remove_task_btn)
        
        tasks_layout.addLayout(tasks_header)
        
        # Tasks table
        self.tasks_table = QTableWidget()
        self.tasks_table.setColumnCount(6)
        self.tasks_table.setHorizontalHeaderLabels([
            "Location", "Business Type", "Limit", "Priority", "Last Run", "Enabled"
        ])
        self.tasks_table.horizontalHeader().setStretchLastSection(True)
        self.tasks_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.tasks_table.itemSelectionChanged.connect(self.on_task_selection_changed)
        tasks_layout.addWidget(self.tasks_table)
        
        # Log output
        log_group = QGroupBox("Activity Log")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        tasks_layout.addWidget(log_group)
        
        splitter.addWidget(tasks_widget)
        splitter.setSizes([300, 500])
        
        layout.addWidget(splitter)
        
    def setup_timer(self):
        """Setup timer for status updates"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(1000)  # Update every second
        
    def start_automation(self):
        """Start automation with current configuration"""
        if not self.tasks:
            QMessageBox.warning(self, "No Tasks", "Please add at least one automation task.")
            return
            
        # Setup callbacks
        self.config.progress_callback = self.on_progress
        self.config.error_callback = self.on_error
        self.config.completion_callback = self.on_completion
        
        # Start automation
        if self.automation_manager.start_automation(self.config, self.tasks):
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.pause_btn.setEnabled(True)
            self.automation_started.emit()
            self.log_message("Automation started")
        else:
            QMessageBox.warning(self, "Start Failed", "Failed to start automation.")
            
    def stop_automation(self):
        """Stop automation"""
        self.automation_manager.stop_automation()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.automation_stopped.emit()
        self.log_message("Automation stopped")
        
    def pause_automation(self):
        """Pause automation"""
        if self.automation_manager.engine:
            self.automation_manager.engine.pause()
            self.pause_btn.setEnabled(False)
            self.resume_btn.setEnabled(True)
            self.log_message("Automation paused")
            
    def resume_automation(self):
        """Resume automation"""
        if self.automation_manager.engine:
            self.automation_manager.engine.resume()
            self.pause_btn.setEnabled(True)
            self.resume_btn.setEnabled(False)
            self.log_message("Automation resumed")
            
    def configure_automation(self):
        """Open automation configuration dialog"""
        dialog = AutomationConfigDialog(self, self.config)
        if dialog.exec() == QDialog.Accepted:
            self.config = dialog.get_config()
            self.log_message("Configuration updated")
            
    def load_presets(self):
        """Load preset automation tasks"""
        reply = QMessageBox.question(
            self, "Load Presets",
            "This will replace all current tasks with preset campaigns. Continue?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.tasks = self.automation_manager.create_preset_campaigns()
            self.update_tasks_table()
            self.log_message(f"Loaded {len(self.tasks)} preset tasks")
            
    def add_task(self):
        """Add new automation task"""
        dialog = TaskConfigDialog(self)
        if dialog.exec() == QDialog.Accepted:
            task = dialog.get_task()
            if task.location:
                self.tasks.append(task)
                self.update_tasks_table()
                self.log_message(f"Added task: {task.location}")
            else:
                QMessageBox.warning(self, "Invalid Task", "Location is required.")
                
    def edit_task(self):
        """Edit selected task"""
        current_row = self.tasks_table.currentRow()
        if current_row >= 0 and current_row < len(self.tasks):
            task = self.tasks[current_row]
            dialog = TaskConfigDialog(self, task)
            if dialog.exec() == QDialog.Accepted:
                updated_task = dialog.get_task()
                if updated_task.location:
                    self.tasks[current_row] = updated_task
                    self.update_tasks_table()
                    self.log_message(f"Updated task: {updated_task.location}")
                else:
                    QMessageBox.warning(self, "Invalid Task", "Location is required.")
                    
    def remove_task(self):
        """Remove selected task"""
        current_row = self.tasks_table.currentRow()
        if current_row >= 0 and current_row < len(self.tasks):
            task = self.tasks[current_row]
            reply = QMessageBox.question(
                self, "Remove Task",
                f"Remove task for {task.location}?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                del self.tasks[current_row]
                self.update_tasks_table()
                self.log_message(f"Removed task: {task.location}")
                
    def update_tasks_table(self):
        """Update tasks table display"""
        self.tasks_table.setRowCount(len(self.tasks))
        
        for i, task in enumerate(self.tasks):
            self.tasks_table.setItem(i, 0, QTableWidgetItem(task.location))
            self.tasks_table.setItem(i, 1, QTableWidgetItem(task.business_type or "All"))
            self.tasks_table.setItem(i, 2, QTableWidgetItem(str(task.limit)))
            
            priority_text = ["High", "Medium", "Low"][task.priority - 1]
            self.tasks_table.setItem(i, 3, QTableWidgetItem(priority_text))
            
            last_run = task.last_run.strftime("%Y-%m-%d %H:%M") if task.last_run else "Never"
            self.tasks_table.setItem(i, 4, QTableWidgetItem(last_run))
            
            enabled_item = QTableWidgetItem("Yes" if task.enabled else "No")
            self.tasks_table.setItem(i, 5, enabled_item)
            
    def on_task_selection_changed(self):
        """Handle task selection change"""
        has_selection = bool(self.tasks_table.selectedItems())
        self.edit_task_btn.setEnabled(has_selection)
        self.remove_task_btn.setEnabled(has_selection)
        
    def update_status(self):
        """Update automation status display"""
        status = self.automation_manager.get_automation_status()
        if not status:
            return
            
        # Update status label
        status_text = status['status'].title()
        if status_text == "Running":
            self.status_label.setStyleSheet(
                "QLabel { background-color: #44aa44; color: white; "
                "padding: 4px 8px; border-radius: 4px; }"
            )
        elif status_text == "Paused":
            self.status_label.setStyleSheet(
                "QLabel { background-color: #ffaa44; color: white; "
                "padding: 4px 8px; border-radius: 4px; }"
            )
        else:
            self.status_label.setStyleSheet(
                "QLabel { background-color: #ff4444; color: white; "
                "padding: 4px 8px; border-radius: 4px; }"
            )
        self.status_label.setText(status_text)
        
        # Update statistics
        stats = status['statistics']
        self.total_leads_label.setText(str(stats['total_leads_found']))
        self.daily_searches_label.setText(str(stats['daily_searches']))
        self.runtime_label.setText(f"{stats['runtime_minutes']:.1f} minutes")
        self.error_count_label.setText(str(stats['error_count']))
        
        # Update current task
        current_task = status['current_task']
        if current_task['location']:
            task_text = f"{current_task['location']}"
            if current_task['business_type']:
                task_text += f" - {current_task['business_type']}"
            self.current_task_label.setText(f"Running: {task_text}")
        else:
            self.current_task_label.setText("No active task")
            
        # Update next task time
        next_task_time = status.get('next_task_time')
        if next_task_time:
            self.next_task_label.setText(next_task_time.strftime("%H:%M:%S"))
        else:
            self.next_task_label.setText("None")
            
    def on_progress(self, progress_data):
        """Handle progress callback"""
        task = progress_data['task']
        new_leads = progress_data['new_leads']
        total_leads = progress_data['total_leads']
        
        message = f"Task completed: {task.location} - {new_leads} new leads (Total: {total_leads})"
        self.log_message(message)
        
    def on_error(self, error_message):
        """Handle error callback"""
        self.log_message(f"ERROR: {error_message}")
        
    def on_completion(self, final_status):
        """Handle completion callback"""
        stats = final_status['statistics']
        message = f"Automation completed. Total leads: {stats['total_leads_found']}, Runtime: {stats['runtime_minutes']:.1f} minutes"
        self.log_message(message)
        
        # Reset UI state
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        
    def log_message(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
        # Keep log size manageable
        if self.log_text.document().blockCount() > 100:
            cursor = self.log_text.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.select(cursor.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()  # Remove the newline