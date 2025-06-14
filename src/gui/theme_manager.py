"""Theme manager for the application with light and dark mode support"""

from PySide6.QtCore import QObject, Signal, QSettings
from PySide6.QtWidgets import QApplication

class ThemeManager(QObject):
    """Manages application themes and provides consistent styling"""
    
    theme_changed = Signal(str)  # Emits theme name when changed
    
    def __init__(self):
        super().__init__()
        self.settings = QSettings("UK Business Lead Generator", "LeadGen")
        self.current_theme = self.settings.value("theme", "light", str)
        
    def get_current_theme(self):
        """Get the current theme name"""
        return self.current_theme
        
    def set_theme(self, theme_name):
        """Set the current theme"""
        if theme_name in ["light", "dark"]:
            self.current_theme = theme_name
            self.settings.setValue("theme", theme_name)
            self.theme_changed.emit(theme_name)
            
    def toggle_theme(self):
        """Toggle between light and dark themes"""
        new_theme = "dark" if self.current_theme == "light" else "light"
        self.set_theme(new_theme)
            
    def get_color(self, color_key, theme_name=None):
        """Get a specific color from the current theme"""
        colors = self.get_theme_colors(theme_name)
        
        # Map common color keys to theme colors
        color_mapping = {
            'primary': colors['accent_primary'],
            'secondary': colors['text_secondary'],
            'background': colors['bg_primary'],
            'text': colors['text_primary'],
            'border': colors['border_primary'],
            'hover': colors['bg_hover'],
            'selected': colors['bg_selected'],
            'success': colors['text_success'],
            'warning': colors['text_warning'],
            'error': colors['text_error']
        }
        
        return color_mapping.get(color_key, colors.get(color_key, colors['text_primary']))
    
    def get_theme_colors(self, theme_name=None):
        """Get color palette for the specified theme"""
        if theme_name is None:
            theme_name = self.current_theme
            
        if theme_name == "dark":
            return {
                # Background colors
                "bg_primary": "#2b2b2b",
                "bg_secondary": "#3c3c3c",
                "bg_tertiary": "#4a4a4a",
                "bg_input": "#404040",
                "bg_hover": "#505050",
                "bg_selected": "#0078d4",
                "bg_disabled": "#555555",
                
                # Text colors
                "text_primary": "#ffffff",
                "text_secondary": "#cccccc",
                "text_disabled": "#888888",
                "text_link": "#4fc3f7",
                "text_success": "#4caf50",
                "text_warning": "#ff9800",
                "text_error": "#f44336",
                
                # Border colors
                "border_primary": "#666666",
                "border_secondary": "#555555",
                "border_focus": "#0078d4",
                
                # Accent colors
                "accent_primary": "#0078d4",
                "accent_hover": "#106ebe",
                "accent_pressed": "#005a9e",
            }
        else:  # light theme
            return {
                # Background colors
                "bg_primary": "#ffffff",
                "bg_secondary": "#f8f9fa",
                "bg_tertiary": "#e9ecef",
                "bg_input": "#ffffff",
                "bg_hover": "#f0f0f0",
                "bg_selected": "#0078d4",
                "bg_disabled": "#e9ecef",
                
                # Text colors
                "text_primary": "#212529",
                "text_secondary": "#6c757d",
                "text_disabled": "#adb5bd",
                "text_link": "#0066cc",
                "text_success": "#28a745",
                "text_warning": "#fd7e14",
                "text_error": "#dc3545",
                
                # Border colors
                "border_primary": "#dee2e6",
                "border_secondary": "#ced4da",
                "border_focus": "#0078d4",
                
                # Accent colors
                "accent_primary": "#0078d4",
                "accent_hover": "#106ebe",
                "accent_pressed": "#005a9e",
            }
            
    def get_stylesheet(self, component=None, theme_name=None):
        """Get stylesheet for a specific component or global styles"""
        colors = self.get_theme_colors(theme_name)
        
        if component == "main_window":
            return f"""
            QMainWindow {{
                background-color: {colors['bg_secondary']};
                color: {colors['text_primary']};
            }}
            QTabWidget::pane {{
                border: none;
                background: {colors['bg_primary']};
                border-radius: 8px;
                margin: 10px;
            }}
            QTabWidget::tab-bar {{
                alignment: center;
            }}
            QTabBar::tab {{
                background: {colors['bg_tertiary']};
                color: {colors['text_primary']};
                min-width: 120px;
                padding: 12px 20px;
                margin: 0 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: 500;
                border: 1px solid {colors['border_secondary']};
            }}
            QTabBar::tab:selected {{
                background: {colors['bg_primary']};
                color: {colors['text_primary']};
                font-weight: bold;
                border-bottom: 1px solid {colors['bg_primary']};
            }}
            QTabBar::tab:hover {{
                background: {colors['bg_hover']};
            }}
            QStatusBar {{
                background: {colors['bg_primary']};
                color: {colors['text_primary']};
                padding: 5px;
                border-top: 1px solid {colors['border_primary']};
                font-weight: 500;
            }}
            QToolBar {{
                background: {colors['bg_primary']};
                border-bottom: 1px solid {colors['border_primary']};
                padding: 5px;
                spacing: 10px;
                color: {colors['text_primary']};
            }}
            QToolBar QToolButton {{
                color: {colors['text_primary']};
                background: transparent;
                border: none;
                padding: 8px 12px;
                border-radius: 4px;
                font-weight: 500;
            }}
            QToolBar QToolButton:hover {{
                background: {colors['bg_hover']};
                color: {colors['text_primary']};
            }}
            QToolBar QToolButton:pressed {{
                background: {colors['bg_selected']};
                color: white;
            }}
            QToolBar QLabel {{
                color: {colors['text_secondary']};
                font-size: 12px;
                padding: 4px 8px;
            }}
            """
            
        elif component == "form_controls":
            return f"""
            QLineEdit, QComboBox, QSpinBox, QTextEdit {{
                background-color: {colors['bg_input']};
                color: {colors['text_primary']};
                border: 2px solid {colors['border_primary']};
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
                selection-background-color: {colors['bg_selected']};
                selection-color: #ffffff;
            }}
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTextEdit:focus {{
                border-color: {colors['border_focus']};
            }}
            QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled, QTextEdit:disabled {{
                background-color: {colors['bg_disabled']};
                color: {colors['text_disabled']};
            }}
            QComboBox::drop-down {{
                border: none;
                background: {colors['bg_input']};
                width: 20px;
            }}
            QComboBox::down-arrow {{
                width: 12px;
                height: 12px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {colors['bg_input']};
                color: {colors['text_primary']};
                border: 1px solid {colors['border_primary']};
                selection-background-color: {colors['bg_selected']};
                selection-color: #ffffff;
            }}
            QComboBox QAbstractItemView::item {{
                background-color: {colors['bg_input']};
                color: {colors['text_primary']};
                padding: 8px;
                border: none;
                min-height: 20px;
            }}
            QComboBox QAbstractItemView::item:selected {{
                background-color: {colors['bg_selected']};
                color: #ffffff;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background-color: {colors['bg_hover']};
                color: {colors['text_primary']};
            }}
            QLineEdit, QComboBox, QSpinBox, QTextEdit {{
                color: {colors['text_primary']};
            }}
            """
            
        elif component == "buttons":
            return f"""
            QPushButton {{
                background-color: {colors['accent_primary']};
                color: #ffffff;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {colors['accent_hover']};
            }}
            QPushButton:pressed {{
                background-color: {colors['accent_pressed']};
            }}
            QPushButton:disabled {{
                background-color: {colors['bg_disabled']};
                color: {colors['text_disabled']};
            }}
            QPushButton[class="secondary"] {{
                background-color: {colors['bg_tertiary']};
                color: {colors['text_primary']};
                border: 1px solid {colors['border_primary']};
            }}
            QPushButton[class="secondary"]:hover {{
                background-color: {colors['bg_hover']};
            }}
            """
            
        elif component == "labels":
            return f"""
            QLabel {{
                color: {colors['text_primary']};
                background-color: transparent;
            }}
            QLabel.secondary {{
                color: {colors['text_secondary']};
            }}
            QLabel.success {{
                color: {colors['text_success']};
                font-weight: bold;
            }}
            QLabel.warning {{
                color: {colors['text_warning']};
                font-weight: bold;
            }}
            QLabel.error {{
                color: {colors['text_error']};
                font-weight: bold;
            }}
            
            /* Ensure all text widgets have proper colors */
            QWidget {{
                color: {colors['text_primary']} !important;
            }}
            
            /* Fix specific text visibility issues */
            QTextEdit, QPlainTextEdit {{
                color: {colors['text_primary']} !important;
                background-color: {colors['bg_input']} !important;
                border: 1px solid {colors['border_primary']};
            }}
            
            /* Fix QLabel text visibility in all contexts */
            QLabel {{
                color: {colors['text_primary']} !important;
                background-color: transparent;
            }}
            
            /* Ensure all input widgets have proper colors */
            QLineEdit, QComboBox, QSpinBox, QTextEdit {{
                color: {colors['text_primary']} !important;
                background-color: {colors['bg_input']} !important;
            }}
            
            /* Fix table text visibility */
            QTableView {{
                color: {colors['text_primary']} !important;
                background-color: {colors['bg_primary']} !important;
            }}
            
            QTableView::item {{
                color: {colors['text_primary']} !important;
                background-color: {colors['bg_primary']} !important;
            }}
            
            QTableView::item:selected {{
                color: #ffffff !important;
                background-color: {colors['bg_selected']} !important;
            }}
            
            /* Fix progress bar visibility */
            QProgressBar {{
                color: {colors['text_primary']} !important;
                background-color: {colors['bg_secondary']} !important;
                text-align: center;
                font-weight: bold;
            }}
            
            QProgressBar::chunk {{
                background-color: {colors['accent_primary']} !important;
            }}
            """
            
        elif component == "tables":
            return f"""
            QTableView {{
                background-color: {colors['bg_primary']};
                alternate-background-color: {colors['bg_secondary']};
                color: {colors['text_primary']};
                gridline-color: {colors['border_primary']};
                border: 1px solid {colors['border_primary']};
                border-radius: 4px;
                selection-background-color: {colors['bg_selected']};
                selection-color: #ffffff;
            }}
            QTableView::item {{
                padding: 8px;
                border: none;
            }}
            QTableView::item:hover {{
                background-color: {colors['bg_hover']};
            }}
            QTableView::item:selected {{
                background-color: {colors['bg_selected']};
                color: #ffffff;
            }}
            QHeaderView::section {{
                background-color: {colors['bg_tertiary']};
                color: {colors['text_primary']};
                padding: 10px;
                border: none;
                border-right: 1px solid {colors['border_primary']};
                border-bottom: 1px solid {colors['border_primary']};
                font-weight: bold;
            }}
            QHeaderView::section:hover {{
                background-color: {colors['bg_hover']};
            }}
            """
            
        elif component == "groups":
            return f"""
            QGroupBox {{
                color: {colors['text_primary']};
                font-weight: bold;
                border: 2px solid {colors['border_primary']};
                border-radius: 6px;
                margin-top: 1em;
                padding-top: 1em;
            }}
            QGroupBox::title {{
                color: {colors['text_primary']};
                font-weight: bold;
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 8px;
                background-color: {colors['bg_primary']};
            }}
            QCheckBox {{
                color: {colors['text_primary']};
                font-weight: 500;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {colors['border_primary']};
                border-radius: 3px;
                background-color: {colors['bg_input']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {colors['accent_primary']};
                border-color: {colors['accent_primary']};
            }}
            QCheckBox::indicator:hover {{
                border-color: {colors['border_focus']};
            }}
            """
            
        elif component == "progress_bars":
            return f"""
            QProgressBar {{
                background-color: {colors['bg_input']};
                border: 2px solid {colors['border_primary']};
                border-radius: 6px;
                text-align: center;
                font-weight: bold;
                color: {colors['text_primary']} !important;
                padding: 2px;
                font-size: 12px;
            }}
            QProgressBar::chunk {{
                background-color: {colors['accent_primary']};
                border-radius: 4px;
                margin: 1px;
            }}
            QProgressBar[class="performance"]::chunk {{
                background-color: #3498db;
            }}
            QProgressBar[class="seo"]::chunk {{
                background-color: #2ecc71;
            }}
            QProgressBar[class="accessibility"]::chunk {{
                background-color: #9b59b6;
            }}
            QProgressBar[class="best_practices"]::chunk {{
                background-color: #e67e22;
            }}
            QProgressBar[value="0"]::chunk {{
                background-color: {colors['bg_disabled']};
            }}
            """
            
        # Return combined stylesheet for all components
        return (
            self.get_stylesheet("main_window", theme_name) +
            self.get_stylesheet("form_controls", theme_name) +
            self.get_stylesheet("buttons", theme_name) +
            self.get_stylesheet("labels", theme_name) +
            self.get_stylesheet("tables", theme_name) +
            self.get_stylesheet("groups", theme_name) +
            self.get_stylesheet("progress_bars", theme_name)
        )

# Global theme manager instance
theme_manager = ThemeManager()