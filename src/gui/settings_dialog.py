# Settings dialog
"""
Settings dialog
"""
import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QTabWidget, QWidget, QGroupBox, QLineEdit, QPushButton,
    QCheckBox, QSpinBox, QComboBox, QFileDialog, QMessageBox,
    QTextEdit, QLabel
)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QFont

from src.gui.theme_manager import theme_manager
from src.utils.config import Config
from src.core.database import LeadDatabase

class SettingsDialog(QDialog):
    """Settings dialog for the application"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        
        # Load settings
        self.settings = QSettings("UK Business Lead Generator", "LeadGen")
        
        # Apply theme styling
        self.setStyleSheet(theme_manager.get_stylesheet())
        
        # Connect to theme changes
        theme_manager.theme_changed.connect(self.apply_theme)
        
        # Set up UI
        self.setup_ui()
        
        # Load current settings
        self.load_settings()
        
        # Apply theme
        self.apply_theme()
    
    def apply_theme(self):
        """Apply current theme to dialog"""
        self.setStyleSheet(theme_manager.get_stylesheet())
    
    def setup_ui(self):
        """Set up the user interface"""
        main_layout = QVBoxLayout(self)
        
        # Create tabs
        tab_widget = QTabWidget()
        
        # General settings tab
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        
        # Data folder settings
        data_group = QGroupBox("Data Storage")
        data_layout = QFormLayout(data_group)
        
        self.data_folder_edit = QLineEdit()
        self.data_folder_edit.setReadOnly(True)
        
        data_folder_layout = QHBoxLayout()
        data_folder_layout.addWidget(self.data_folder_edit)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.on_browse_clicked)
        data_folder_layout.addWidget(self.browse_button)
        
        data_layout.addRow("Data Folder:", data_folder_layout)
        
        # Keep data checkbox
        self.keep_data_checkbox = QCheckBox("Keep data when uninstalling")
        self.keep_data_checkbox.setChecked(True)
        data_layout.addRow("", self.keep_data_checkbox)
        
        general_layout.addWidget(data_group)
        
        # Search settings
        search_group = QGroupBox("Search Settings")
        search_layout = QFormLayout(search_group)
        
        self.results_limit_spin = QSpinBox()
        self.results_limit_spin.setRange(5, 100)
        self.results_limit_spin.setValue(20)
        self.results_limit_spin.setSingleStep(5)
        search_layout.addRow("Default Results Limit:", self.results_limit_spin)
        
        self.analyze_websites_checkbox = QCheckBox("Analyze websites by default")
        self.analyze_websites_checkbox.setChecked(True)
        search_layout.addRow("", self.analyze_websites_checkbox)
        
        self.use_selenium_checkbox = QCheckBox("Use Selenium for better results (recommended)")
        self.use_selenium_checkbox.setChecked(True)
        search_layout.addRow("", self.use_selenium_checkbox)
        
        general_layout.addWidget(search_group)
        
        # Add stretch
        general_layout.addStretch()
        
        # Analysis settings tab
        analysis_tab = QWidget()
        analysis_layout = QVBoxLayout(analysis_tab)
        
        # Lighthouse settings
        lighthouse_group = QGroupBox("Lighthouse Integration")
        lighthouse_layout = QFormLayout(lighthouse_group)
        
        self.use_lighthouse_checkbox = QCheckBox("Use Lighthouse for website analysis")
        self.use_lighthouse_checkbox.setChecked(True)
        lighthouse_layout.addRow("", self.use_lighthouse_checkbox)
        
        self.lighthouse_path_edit = QLineEdit()
        lighthouse_layout.addRow("Lighthouse Path:", self.lighthouse_path_edit)
        
        self.lighthouse_timeout_spin = QSpinBox()
        self.lighthouse_timeout_spin.setRange(30, 300)
        self.lighthouse_timeout_spin.setValue(60)
        self.lighthouse_timeout_spin.setSingleStep(10)
        self.lighthouse_timeout_spin.setSuffix
        self.lighthouse_timeout_spin.setSuffix(" seconds")
        lighthouse_layout.addRow("Lighthouse Timeout:", self.lighthouse_timeout_spin)
        
        analysis_layout.addWidget(lighthouse_group)
        
        # Fallback settings
        fallback_group = QGroupBox("Fallback Analysis")
        fallback_layout = QFormLayout(fallback_group)
        
        self.fallback_checkbox = QCheckBox("Use basic analysis when Lighthouse is unavailable")
        self.fallback_checkbox.setChecked(True)
        fallback_layout.addRow("", self.fallback_checkbox)
        
        analysis_layout.addWidget(fallback_group)
        
        # Thread settings
        thread_group = QGroupBox("Performance")
        thread_layout = QFormLayout(thread_group)
        
        self.max_threads_spin = QSpinBox()
        self.max_threads_spin.setRange(1, 8)
        self.max_threads_spin.setValue(3)
        thread_layout.addRow("Maximum Analysis Threads:", self.max_threads_spin)
        
        analysis_layout.addWidget(thread_group)
        
        # Add stretch
        analysis_layout.addStretch()
        
        # Export settings tab
        export_tab = QWidget()
        export_layout = QVBoxLayout(export_tab)
        
        # Default export format
        format_group = QGroupBox("Default Export Format")
        format_layout = QFormLayout(format_group)
        
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(["CSV", "Text Report", "HTML Report", "JSON"])
        format_layout.addRow("Default Format:", self.export_format_combo)
        
        export_layout.addWidget(format_group)
        
        # Default export path
        path_group = QGroupBox("Default Export Path")
        path_layout = QFormLayout(path_group)
        
        self.export_path_edit = QLineEdit()
        self.export_path_edit.setReadOnly(True)
        
        export_path_layout = QHBoxLayout()
        export_path_layout.addWidget(self.export_path_edit)
        
        self.export_browse_button = QPushButton("Browse...")
        self.export_browse_button.clicked.connect(self.on_export_browse_clicked)
        export_path_layout.addWidget(self.export_browse_button)
        
        path_layout.addRow("Export Folder:", export_path_layout)
        
        export_layout.addWidget(path_group)
        
        # Add stretch
        export_layout.addStretch()
        
        # Data Management tab
        data_mgmt_tab = QWidget()
        data_mgmt_layout = QVBoxLayout(data_mgmt_tab)
        
        # Clear Data section
        clear_data_group = QGroupBox("Data Management")
        clear_data_layout = QVBoxLayout(clear_data_group)
        
        clear_data_info = QLabel("Warning: This will permanently delete all stored business data, search results, and contact attempts.")
        clear_data_info.setWordWrap(True)
        clear_data_info.setStyleSheet("color: #dc3545; font-weight: bold; padding: 10px; background: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px;")
        clear_data_layout.addWidget(clear_data_info)
        
        self.clear_data_button = QPushButton("🗑️ Clear All Data")
        self.clear_data_button.setStyleSheet("QPushButton { background-color: #dc3545; color: white; font-weight: bold; padding: 10px; border-radius: 6px; } QPushButton:hover { background-color: #c82333; }")
        self.clear_data_button.clicked.connect(self.on_clear_data_clicked)
        clear_data_layout.addWidget(self.clear_data_button)
        
        data_mgmt_layout.addWidget(clear_data_group)
        
        # Business Types section
        business_types_group = QGroupBox("Custom Business Types")
        business_types_layout = QVBoxLayout(business_types_group)
        
        business_types_info = QLabel("Add custom business types to search for (one per line):")
        business_types_layout.addWidget(business_types_info)
        
        self.business_types_edit = QTextEdit()
        self.business_types_edit.setMaximumHeight(150)
        self.business_types_edit.setPlaceholderText("e.g.:\nCoffee Shops\nDigital Marketing Agencies\nLocal Restaurants\nFitness Centers")
        business_types_layout.addWidget(self.business_types_edit)
        
        business_types_note = QLabel("Note: These will appear in the business type dropdown when searching.")
        business_types_note.setStyleSheet("color: #6c757d; font-style: italic;")
        business_types_layout.addWidget(business_types_note)
        
        data_mgmt_layout.addWidget(business_types_group)
        
        # Add stretch
        data_mgmt_layout.addStretch()
        
        # Add tabs to tab widget
        tab_widget.addTab(general_tab, "General")
        tab_widget.addTab(analysis_tab, "Analysis")
        tab_widget.addTab(export_tab, "Export")
        tab_widget.addTab(data_mgmt_tab, "Data Management")
        
        main_layout.addWidget(tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.accept)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)
    
    def load_settings(self):
        """Load current settings values"""
        # General settings
        data_folder = self.settings.value(
            "general/data_folder",
            os.path.join(os.path.expanduser("~"), "UKLeadGen", "data")
        )
        self.data_folder_edit.setText(data_folder)
        
        self.keep_data_checkbox.setChecked(
            self.settings.value("general/keep_data_on_uninstall", True, bool)
        )
        
        # Search settings
        self.results_limit_spin.setValue(
            self.settings.value("search/limit", 20, int)
        )
        
        self.analyze_websites_checkbox.setChecked(
            self.settings.value("search/analyze_websites", True, bool)
        )
        
        self.use_selenium_checkbox.setChecked(
            self.settings.value("search/use_selenium", True, bool)
        )
        
        # Analysis settings
        self.use_lighthouse_checkbox.setChecked(
            self.settings.value("analysis/use_lighthouse", True, bool)
        )
        
        self.lighthouse_path_edit.setText(
            self.settings.value("analysis/lighthouse_path", "")
        )
        
        self.lighthouse_timeout_spin.setValue(
            self.settings.value("analysis/lighthouse_timeout", 60, int)
        )
        
        self.fallback_checkbox.setChecked(
            self.settings.value("analysis/use_fallback", True, bool)
        )
        
        self.max_threads_spin.setValue(
            self.settings.value("analysis/max_threads", 3, int)
        )
        
        # Export settings
        export_format = self.settings.value("export/default_format", "CSV")
        index = self.export_format_combo.findText(export_format)
        if index >= 0:
            self.export_format_combo.setCurrentIndex(index)
        
        export_path = self.settings.value(
            "export/default_path",
            os.path.join(os.path.expanduser("~"), "UKLeadGen", "exports")
        )
        self.export_path_edit.setText(export_path)
        
        # Business types
        business_types = self.settings.value("search/custom_business_types", "")
        self.business_types_edit.setPlainText(business_types)
    
    def save_settings(self):
        """Save settings values"""
        # General settings
        self.settings.setValue("general/data_folder", self.data_folder_edit.text())
        self.settings.setValue("general/keep_data_on_uninstall", self.keep_data_checkbox.isChecked())
        
        # Search settings
        self.settings.setValue("search/limit", self.results_limit_spin.value())
        self.settings.setValue("search/analyze_websites", self.analyze_websites_checkbox.isChecked())
        self.settings.setValue("search/use_selenium", self.use_selenium_checkbox.isChecked())
        
        # Analysis settings
        self.settings.setValue("analysis/use_lighthouse", self.use_lighthouse_checkbox.isChecked())
        self.settings.setValue("analysis/lighthouse_path", self.lighthouse_path_edit.text())
        self.settings.setValue("analysis/lighthouse_timeout", self.lighthouse_timeout_spin.value())
        self.settings.setValue("analysis/use_fallback", self.fallback_checkbox.isChecked())
        self.settings.setValue("analysis/max_threads", self.max_threads_spin.value())
        
        # Export settings
        self.settings.setValue("export/default_format", self.export_format_combo.currentText())
        self.settings.setValue("export/default_path", self.export_path_edit.text())
        
        # Business types
        self.settings.setValue("search/custom_business_types", self.business_types_edit.toPlainText())
    
    def accept(self):
        """Handle accept (save) button click"""
        # Save settings
        self.save_settings()
        
        # Create directories if they don't exist
        try:
            data_folder = self.data_folder_edit.text()
            os.makedirs(data_folder, exist_ok=True)
            
            export_path = self.export_path_edit.text()
            os.makedirs(export_path, exist_ok=True)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to create directories: {str(e)}"
            )
        
        super().accept()
    
    def on_browse_clicked(self):
        """Handle browse button click for data folder"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Data Folder",
            self.data_folder_edit.text()
        )
        
        if folder:
            self.data_folder_edit.setText(folder)
    
    def on_export_browse_clicked(self):
        """Handle browse button click for export folder"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Export Folder",
            self.export_path_edit.text()
        )
        
        if folder:
            self.export_path_edit.setText(folder)
    
    def on_clear_data_clicked(self):
        """Handle clear data button click"""
        reply = QMessageBox.question(
            self, 
            "Clear All Data",
            "Are you sure you want to permanently delete all stored business data?\n\n"
            "This action cannot be undone and will remove:\n"
            "• All business search results\n"
            "• Website analysis data\n"
            "• Contact attempt records\n\n"
            "Do you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Get data folder path
                data_folder = self.data_folder_edit.text()
                if not data_folder:
                    data_folder = os.path.join(os.path.expanduser("~"), "UKLeadGen", "data")
                
                # Find and clear all database files
                import glob
                db_files = glob.glob(os.path.join(data_folder, "*.db"))
                
                cleared_count = 0
                for db_file in db_files:
                    try:
                        db = LeadDatabase(db_file)
                        if db.clear_all_data():
                            cleared_count += 1
                        db.close()
                    except Exception as e:
                        print(f"Error clearing {db_file}: {e}")
                
                if cleared_count > 0:
                    QMessageBox.information(
                        self,
                        "Data Cleared",
                        f"Successfully cleared data from {cleared_count} database(s)."
                    )
                else:
                    QMessageBox.information(
                        self,
                        "No Data Found",
                        "No database files found to clear."
                    )
                    
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"An error occurred while clearing data:\n{str(e)}"
                )