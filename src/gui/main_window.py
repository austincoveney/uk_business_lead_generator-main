"""
Main application window
"""
import psutil
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QVBoxLayout, QHBoxLayout, 
    QWidget, QToolBar, QStatusBar, QMessageBox,
    QMenu, QFileDialog, QLabel, QSizePolicy
)
from PySide6.QtGui import QIcon, QKeySequence, QAction, QCursor
from PySide6.QtCore import Qt, Signal, Slot, QSettings, QTimer, QSize

from src.gui.search_panel import SearchPanel
from src.gui.results_panel import ResultsPanel
from src.gui.report_view import ReportView
from src.gui.automation_panel import AutomationPanel
from src.gui.settings_dialog import SettingsDialog
from src.gui.theme_manager import theme_manager
from src.core.database import LeadDatabase

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("UK Business Lead Generator")
        self.setMinimumSize(1200, 800)
        
        # Initialize settings
        self.settings = QSettings("UK Business Lead Generator", "LeadGen")
        
        # Initialize memory monitoring
        self.memory_label = QLabel()
        self.memory_timer = QTimer(self)
        self.memory_timer.timeout.connect(self.update_memory_usage)
        self.memory_timer.start(10000)  # Update every 10 seconds
        
        # Initial memory update
        self.update_memory_usage()
        
        # Apply theme styling
        self.apply_theme()
        
        # Connect to theme changes
        theme_manager.theme_changed.connect(self.apply_theme)
        
        # Create central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Create tabs with modern styling
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setElideMode(Qt.TextElideMode.ElideNone)
        self.main_layout.addWidget(self.tab_widget)
        
        # Initialize database for automation
        self.database = LeadDatabase()
        
        # Create panels
        self.search_panel = SearchPanel()
        self.results_panel = ResultsPanel()
        self.report_view = ReportView()
        self.automation_panel = AutomationPanel(self.database)
        
        # Add panels to tabs with icons
        self.tab_widget.addTab(self.search_panel, "🔍 Search")
        self.tab_widget.addTab(self.results_panel, "📊 Results")
        self.tab_widget.addTab(self.automation_panel, "🤖 Automation")
        self.tab_widget.addTab(self.report_view, "📑 Reports")
        
        # Create toolbar
        self.setup_toolbar()
        
        # Create status bar with modern style
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready to search")
        self.status_bar.setFixedHeight(30)
        
        # Connect signals
        self.search_panel.search_started.connect(self.on_search_started)
        self.search_panel.search_completed.connect(self.on_search_completed)
        self.search_panel.search_error.connect(self.on_search_error)
        
        # Connect automation signals
        self.automation_panel.automation_started.connect(self.on_automation_started)
        self.automation_panel.automation_stopped.connect(self.on_automation_stopped)
        
        # Apply saved settings
        self.restore_settings()
        
        # Initialize theme button text
        self.update_theme_button_text()
    
    def setup_toolbar(self):
        """Set up the main toolbar with modern styling"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setObjectName("mainToolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(toolbar)
        
        # New search action with icon
        new_search_action = QAction("🔍 New Search", self)
        new_search_action.setStatusTip("Start a new business search")
        new_search_action.setShortcut(QKeySequence("Ctrl+N"))
        new_search_action.triggered.connect(self.on_new_search)
        toolbar.addAction(new_search_action)
        
        toolbar.addSeparator()
        
        # Export action with icon
        export_action = QAction("📊 Export", self)
        export_action.setStatusTip("Export results to Excel or CSV")
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.triggered.connect(self.on_export)
        toolbar.addAction(export_action)
        
        # Settings action with icon
        settings_action = QAction("⚙️ Settings", self)
        settings_action.setStatusTip("Configure search and analysis settings")
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        settings_action.triggered.connect(self.on_settings)
        toolbar.addAction(settings_action)
        
        # Help action with icon
        help_action = QAction("❓ Help", self)
        help_action.setStatusTip("View documentation and tips")
        help_action.setShortcut(QKeySequence("F1"))
        help_action.triggered.connect(self.on_help)
        toolbar.addAction(help_action)
        
        toolbar.addSeparator()
        
        # Theme toggle action
        theme_action = QAction("🌙 Dark Mode", self)
        theme_action.setStatusTip("Toggle between light and dark themes")
        theme_action.setShortcut(QKeySequence("Ctrl+T"))
        theme_action.triggered.connect(self.toggle_theme)
        toolbar.addAction(theme_action)
        self.theme_action = theme_action  # Store reference to update text
        
        # Add flexible spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        toolbar.addWidget(spacer)
        
        # Add memory usage indicator
        self.memory_label = QLabel()
        self.update_memory_usage()
        toolbar.addWidget(self.memory_label)
        
        # Start memory usage update timer
        self.memory_timer = QTimer(self)
        self.memory_timer.timeout.connect(self.update_memory_usage)
        self.memory_timer.start(10000)  # Update every 10 seconds
    
    def update_memory_usage(self):
        """Update memory usage display with improved monitoring"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            memory_percent = process.memory_percent()
            
            # Update status bar with more detailed info
            self.memory_label.setText(f"Memory: {memory_mb:.1f} MB ({memory_percent:.1f}%)")
            
            # Progressive memory warnings
            if memory_mb > 1000:  # Critical threshold
                logging.critical(f"Critical memory usage: {memory_mb:.1f} MB ({memory_percent:.1f}%)")
                self.memory_label.setStyleSheet("color: red; font-weight: bold;")
            elif memory_mb > 750:  # Warning threshold
                logging.warning(f"High memory usage: {memory_mb:.1f} MB ({memory_percent:.1f}%)")
                self.memory_label.setStyleSheet("color: orange; font-weight: bold;")
            elif memory_mb > 500:  # Info threshold
                logging.info(f"Elevated memory usage: {memory_mb:.1f} MB ({memory_percent:.1f}%)")
                self.memory_label.setStyleSheet("color: yellow;")
            else:
                self.memory_label.setStyleSheet("color: green;")
                
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            logging.error(f"Process monitoring error: {e}")
            self.memory_label.setText("Memory: N/A")
        except Exception as e:
            logging.error(f"Unexpected error updating memory usage: {e}")
            self.memory_label.setText("Memory: Error")
    
    def restore_settings(self):
        """Restore saved window settings"""
        # Restore window geometry
        if self.settings.contains("geometry"):
            self.restoreGeometry(self.settings.value("geometry"))
        
        # Restore window state
        if self.settings.contains("windowState"):
            self.restoreState(self.settings.value("windowState"))
    
    def save_settings(self):
        """Save window settings"""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Save settings before closing
        self.save_settings()
        event.accept()
    
    @Slot()
    def on_new_search(self):
        """Handle new search action"""
        self.tab_widget.setCurrentIndex(0)  # Switch to Search tab
        self.search_panel.clear_form()
    
    @Slot()
    def on_export(self):
        """Handle export action"""
        # Check if we have results to export
        if not self.results_panel.has_results():
            QMessageBox.information(self, "Export", "No results to export.")
            return
        
        # Show export options menu
        export_menu = QMenu(self)
        
        csv_action = export_menu.addAction("Export to CSV")
        text_action = export_menu.addAction("Export to Text Report")
        html_action = export_menu.addAction("Export to HTML Report")
        json_action = export_menu.addAction("Export to JSON")
        
        # Show menu at current mouse position
        action = export_menu.exec(QCursor.pos())
        
        if action == csv_action:
            self.export_csv()
        elif action == text_action:
            self.export_text()
        elif action == html_action:
            self.export_html()
        elif action == json_action:
            self.export_json()
    
    def export_csv(self):
        """Export results to CSV"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export to CSV", "", "CSV Files (*.csv)")
        
        if file_path:
            if not file_path.endswith('.csv'):
                file_path += '.csv'
            
            success = self.results_panel.export_to_csv(file_path)
            
            if success:
                self.status_bar.showMessage(f"Exported to {file_path}")
            else:
                QMessageBox.warning(self, "Export Error", "Failed to export to CSV.")
    
    def export_text(self):
        """Export results to text report"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export to Text Report", "", "Text Files (*.txt)")
        
        if file_path:
            if not file_path.endswith('.txt'):
                file_path += '.txt'
            
            success = self.results_panel.export_to_text(file_path)
            
            if success:
                self.status_bar.showMessage(f"Exported to {file_path}")
            else:
                QMessageBox.warning(self, "Export Error", "Failed to export to text report.")
    
    def export_html(self):
        """Export results to HTML report"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export to HTML Report", "", "HTML Files (*.html)")
        
        if file_path:
            if not file_path.endswith('.html'):
                file_path += '.html'
            
            success = self.results_panel.export_to_html(file_path)
            
            if success:
                self.status_bar.showMessage(f"Exported to {file_path}")
            else:
                QMessageBox.warning(self, "Export Error", "Failed to export to HTML report.")
    
    def export_json(self):
        """Export results to JSON"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export to JSON", "", "JSON Files (*.json)")
        
        if file_path:
            if not file_path.endswith('.json'):
                file_path += '.json'
            
            success = self.results_panel.export_to_json(file_path)
            
            if success:
                self.status_bar.showMessage(f"Exported to {file_path}")
            else:
                QMessageBox.warning(self, "Export Error", "Failed to export to JSON.")
    
    @Slot()
    def on_settings(self):
        """Handle settings action"""
        dialog = SettingsDialog(self)
        if dialog.exec():
            # Apply settings if dialog was accepted
            self.search_panel.load_settings()
            self.search_panel.load_business_types()  # Refresh business types
            self.results_panel.load_settings()
            self.report_view.load_settings()
    
    @Slot()
    def on_help(self):
        """Handle help action"""
        QMessageBox.information(
            self, 
            "Help",
            "UK Business Lead Generator\n\n"
            "1. Enter a UK location (city, town, or postal code) in the Search tab\n"
            "2. Optionally specify a business category\n"
            "3. Click 'Generate Leads' to start the search\n"
            "4. View results in the Results tab\n"
            "5. Generate reports or export data using the toolbar\n\n"
            "For more information, please refer to the documentation."
        )
    
    @Slot()
    def on_search_started(self):
        """Handle search started signal"""
        self.status_bar.showMessage("Searching...")
    
    @Slot(int)
    def on_search_completed(self, count):
        """Handle search completed signal"""
        self.status_bar.showMessage(f"Search completed. Found {count} businesses.")
        self.tab_widget.setCurrentIndex(1)  # Switch to Results tab
        
        # Update results panel
        self.results_panel.load_results()
    
    @Slot(str)
    def on_search_error(self, error_message):
        """Handle search error signal"""
        self.status_bar.showMessage("Search failed.")
        QMessageBox.warning(self, "Search Error", error_message)
    
    @Slot()
    def on_automation_started(self):
        """Handle automation started signal"""
        self.status_bar.showMessage("Automation running...")
    
    @Slot()
    def on_automation_stopped(self):
        """Handle automation stopped signal"""
        self.status_bar.showMessage("Automation stopped.")
    
    def apply_theme(self):
        """Apply the current theme to the main window"""
        self.setStyleSheet(theme_manager.get_stylesheet())
        
        # Update all child panels
        if hasattr(self, 'search_panel'):
            self.search_panel.setStyleSheet(theme_manager.get_stylesheet())
        if hasattr(self, 'results_panel'):
            self.results_panel.setStyleSheet(theme_manager.get_stylesheet())
        if hasattr(self, 'automation_panel'):
            self.automation_panel.setStyleSheet(theme_manager.get_stylesheet())
        if hasattr(self, 'report_view'):
            self.report_view.setStyleSheet(theme_manager.get_stylesheet())
    
    def update_theme_button_text(self):
        """Update theme button text based on current theme"""
        if hasattr(self, 'theme_action'):
            if theme_manager.current_theme == 'dark':
                self.theme_action.setText("☀️ Light Mode")
            else:
                self.theme_action.setText("🌙 Dark Mode")
    
    def toggle_theme(self):
        """Toggle between light and dark themes"""
        theme_manager.toggle_theme()
        
        # Update button text
        self.update_theme_button_text()
            
        # Apply theme immediately
        self.apply_theme()