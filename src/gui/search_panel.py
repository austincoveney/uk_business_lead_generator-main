"""
Search settings panel
"""

import os
import threading
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QCheckBox,
    QPushButton,
    QProgressBar,
    QGroupBox,
    QRadioButton,
    QMessageBox,
    QGraphicsOpacityEffect,
    QFrame,
    QStyle,
    QCompleter,
    QListWidget,
    QListWidgetItem
)
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, Property, QTimer, QStringListModel
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import Qt, Signal, Slot, QSettings
from src.gui.theme_manager import theme_manager

from src.core.scraper import BusinessScraper
from src.core.analyzer import WebsiteAnalyzer
from src.core.database import LeadDatabase
from src.utils.helpers import validate_uk_location
from src.utils.search_history import SearchHistoryManager
from src.data.business_types import get_business_suggestions, ALL_BUSINESS_TYPES, POPULAR_TYPES


class LoadingSpinner(QWidget):
    """Custom loading spinner widget"""
    def __init__(self, parent=None, size=40, line_width=3):
        super().__init__(parent)
        self.size = size
        self.line_width = line_width
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        self.setFixedSize(size, size)
        self.hide()

    def paintEvent(self, event):
        if not self.isVisible() or not self.isEnabled():
            return
            
        # Check if widget is properly initialized
        if self.size <= 0 or self.line_width <= 0:
            return
        
        # Check if widget has valid geometry
        if self.width() <= 0 or self.height() <= 0:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Use theme-compatible color with fallback
        try:
            color = theme_manager.get_color('primary')
        except:
            color = QColor(0, 120, 212)  # Default blue color
        
        pen = QPen(color)
        pen.setWidth(self.line_width)
        painter.setPen(pen)
        
        painter.translate(self.size / 2, self.size / 2)
        painter.rotate(self.angle)
        
        for i in range(8):
            painter.rotate(45)
            painter.setOpacity(0.3 + ((i + 1) / 8) * 0.7)  # Increased minimum opacity
            painter.drawLine(self.size / 4, 0, self.size / 2 - self.line_width, 0)

    def rotate(self):
        self.angle = (self.angle + 45) % 360
        self.update()

    def start(self):
        self.show()
        self.timer.start(100)

    def stop(self):
        self.timer.stop()
        self.hide()


class SearchPanel(QWidget):
    """Search panel for configuring and starting lead generation"""

    # Signals
    search_started = Signal()
    search_completed = Signal(int)  # int: number of results
    search_error = Signal(str)  # str: error message

    def __init__(self):
        super().__init__()

        # Initialize settings
        self.settings = QSettings("UK Business Lead Generator", "LeadGen")

        # Initialize search thread
        self.search_thread = None
        
        # Initialize search history
        self.search_history = SearchHistoryManager(self.settings)

        # Initialize loading spinner
        self.loading_spinner = LoadingSpinner(self)

        # Set up UI
        self.setup_ui()

        # Setup animations and styles
        self.setup_animations()
        self.setup_styles()
        self.setup_auto_complete()
        
        # Load business types after auto-complete is set up
        self.load_business_types()

        # Load settings
        self.load_settings()
        
        # Connect signals
        self.search_button.clicked.connect(self.on_search_clicked)
        self.location_input.returnPressed.connect(self.on_search_clicked)
        self.category_input.lineEdit().returnPressed.connect(self.on_search_clicked)
    
    def setup_auto_complete(self):
        """Setup auto-complete functionality for inputs"""
        # Setup location auto-complete
        self.location_completer = QCompleter()
        self.location_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.location_completer.setFilterMode(Qt.MatchContains)
        self.location_input.setCompleter(self.location_completer)
        
        # Setup business type auto-complete for the combo box
        self.category_completer = QCompleter()
        self.category_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.category_completer.setFilterMode(Qt.MatchContains)
        self.category_input.setCompleter(self.category_completer)
        
        # Connect text change signals to update suggestions
        self.location_input.textChanged.connect(self.update_location_suggestions)
        self.category_input.lineEdit().textChanged.connect(self.update_business_type_suggestions)
        
        # Initial population of suggestions
        self.update_location_suggestions()
        self.update_business_type_suggestions()
    
    def update_location_suggestions(self, text=""):
        """Update location auto-complete suggestions"""
        # Check if completer is initialized
        if not hasattr(self, 'location_completer'):
            return
            
        suggestions = self.search_history.get_location_suggestions(text)
        model = QStringListModel(suggestions)
        self.location_completer.setModel(model)
    
    def update_business_type_suggestions(self, text=""):
        """Update business type auto-complete suggestions"""
        # Check if completer is initialized
        if not hasattr(self, 'category_completer'):
            return
            
        # Combine history suggestions with predefined types
        history_suggestions = self.search_history.get_business_type_suggestions(text)
        predefined_suggestions = get_business_suggestions(text)
        
        # Merge and deduplicate
        all_suggestions = list(dict.fromkeys(history_suggestions + predefined_suggestions))
        
        model = QStringListModel(all_suggestions)
        self.category_completer.setModel(model)

    def setup_styles(self):
        """Set up custom styles for widgets"""
        # Apply theme styling
        self.setStyleSheet(theme_manager.get_stylesheet())
        
        # Connect to theme changes
        theme_manager.theme_changed.connect(self.apply_theme)

    def validate_location(self, text):
        """Validate location input and provide visual feedback"""
        if not text:
            self.location_hint.setText("")
            self.location_input.setStyleSheet("")
            return

        is_valid = validate_uk_location(text)
        if is_valid:
            self.location_hint.setText("Valid UK location")
            self.location_hint.setStyleSheet("color: rgb(39, 174, 96); font-size: 12; margin-left: 4;")
            self.location_input.setStyleSheet("border: 2 solid rgb(39, 174, 96); border-radius: 6; padding: 8;")
        else:
            self.location_hint.setText("Please enter a valid UK location")
            self.location_hint.setStyleSheet("color: rgb(231, 76, 60); font-size: 12; margin-left: 4;")
            self.location_input.setStyleSheet("border: 2 solid rgb(231, 76, 60); border-radius: 6; padding: 8;")

    def setup_ui(self):
        """Set up the user interface with modern styling"""
        # Create search form container
        self.search_form = QFrame()
        self.search_form.setObjectName("searchForm")
        
        # Set panel styling
        # Set minimum width for input fields
        for widget in self.findChildren((QLineEdit, QComboBox, QSpinBox)):
            widget.setMinimumWidth(300)

        # Set minimum width for input fields
        for widget in self.findChildren((QLineEdit, QComboBox, QSpinBox)):
            widget.setMinimumWidth(300)


        # Initialize thread reference
        self.search_thread = None
    
    def apply_theme(self):
        """Apply the current theme"""
        self.setStyleSheet(theme_manager.get_stylesheet())

    def setup_animations(self):
        # Setup fade effect for the search form
        self.fade_effect = QGraphicsOpacityEffect(self)
        self.fade_effect.setOpacity(1.0)
        self.search_form.setGraphicsEffect(self.fade_effect)

        # Create fade animation
        self.fade_animation = QPropertyAnimation(self.fade_effect, b"opacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

    def setup_ui(self):
        """Set up the user interface with modern styling"""
        # Create search form container
        self.search_form = QFrame()
        self.search_form.setObjectName("searchForm")
        
        # Panel styling will be applied by theme manager

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Create search container
        search_container = QWidget()
        search_container.setObjectName("searchContainer")
        search_layout = QVBoxLayout(search_container)

        # Create form layout with improved spacing
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Location input with modern styling and tooltip
        location_container = QWidget()
        location_layout = QVBoxLayout(location_container)
        location_layout.setContentsMargins(0, 0, 0, 0)
        location_layout.setSpacing(4)
        
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("e.g., London, Manchester, SW1A 1AA...")
        self.location_input.setToolTip("Enter a UK city, region, or postcode to search for businesses")
        self.location_input.textChanged.connect(self.validate_location)
        location_layout.addWidget(self.location_input)
        
        self.location_hint = QLabel()
        location_layout.addWidget(self.location_hint)
        form_layout.addRow("Location:", location_container)

        # Business category input with enhanced styling and autocomplete
        category_container = QWidget()
        category_layout = QVBoxLayout(category_container)
        category_layout.setContentsMargins(0, 0, 0, 0)
        category_layout.setSpacing(4)
        
        self.category_input = QComboBox()
        self.category_input.setEditable(True)
        self.category_input.lineEdit().setPlaceholderText("e.g., Restaurant, Retail, Healthcare...")
        self.category_input.setToolTip("Select or enter a business category to search for")
        # Remove hardcoded styling - let theme manager handle it
        # self.category_input.setStyleSheet() - removed to use theme styling
        category_layout.addWidget(self.category_input)
        
        self.category_hint = QLabel("Start typing to see suggestions")
        self.category_hint.setProperty("class", "secondary")  # Use theme secondary text
        category_layout.addWidget(self.category_hint)
        form_layout.addRow("Business Type:", category_container)
        # Load default and custom business types (will be called after auto-complete setup)

        # Limit field with modern spinbox
        self.limit_input = QSpinBox()
        self.limit_input.setRange(5, 200)
        self.limit_input.setValue(50)
        self.limit_input.setSingleStep(10)
        self.limit_input.setPrefix("Up to ")
        self.limit_input.setSuffix(" results")
        # Remove hardcoded styling - let theme manager handle it
        form_layout.addRow("Search Limit:", self.limit_input)

        # Add form to search container
        search_layout.addLayout(form_layout)
        
        # Add search container to main layout
        main_layout.addWidget(search_container)

        # Options group
        options_group = QGroupBox("Search Options")
        options_layout = QVBoxLayout(options_group)

        # Website analysis options
        self.analyze_websites_checkbox = QCheckBox("Analyze Websites")
        self.analyze_websites_checkbox.setChecked(True)
        options_layout.addWidget(self.analyze_websites_checkbox)

        # Priority options
        priority_layout = QHBoxLayout()
        priority_label = QLabel("Focus on:")
        priority_layout.addWidget(priority_label)

        self.priority_all_radio = QRadioButton("All Businesses")
        self.priority_no_website_radio = QRadioButton("No Website")
        self.priority_poor_website_radio = QRadioButton("Poor Website")

        self.priority_all_radio.setChecked(True)

        priority_layout.addWidget(self.priority_all_radio)
        priority_layout.addWidget(self.priority_no_website_radio)
        priority_layout.addWidget(self.priority_poor_website_radio)

        options_layout.addLayout(priority_layout)

        # Business size filter
        size_layout = QHBoxLayout()
        size_label = QLabel("Business Size:")
        size_layout.addWidget(size_label)

        self.size_combo = QComboBox()
        self.size_combo.addItems(["All Sizes", "Small", "Medium", "Large", "Enterprise"])
        self.size_combo.setCurrentText("All Sizes")
        size_layout.addWidget(self.size_combo)
        size_layout.addStretch()

        options_layout.addLayout(size_layout)

        main_layout.addWidget(options_group)

        # Search button and progress bar with modern styling
        button_layout = QHBoxLayout()

        # Progress bar with modern styling
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 10;
                background: rgb(223, 230, 233);
                height: 8;
                text-align: center;
            }
            QProgressBar::chunk {
                border-radius: 10;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgb(9, 132, 227), stop:1 rgb(0, 206, 201));
            }
        """)
        button_layout.addWidget(self.progress_bar)

        # Search button with modern styling
        self.search_button = QPushButton("Generate Leads")
        self.search_button.clicked.connect(self.on_search_clicked)
        button_layout.addWidget(self.search_button)

        main_layout.addLayout(button_layout)

        # Status label
        self.status_label = QLabel()
        main_layout.addWidget(self.status_label)

        # Add stretch at the end
        main_layout.addStretch()

    def start_search(self, location, category, limit, analyze_websites, priority_focus, business_size=None):
        """Start the search process in a background thread"""
        # Update UI
        self.search_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Initializing search...")

        # Emit search started signal
        self.search_started.emit()

        # Start search thread
        self.search_thread = threading.Thread(
            target=self.perform_search,
            args=(location, category, limit, analyze_websites, priority_focus, business_size),
        )
        self.search_thread.daemon = True
        self.search_thread.start()

    def load_settings(self):
        """Load saved settings"""
        self.location_input.setText(self.settings.value("search/last_location", ""))

        category_index = self.settings.value("search/last_category_index", 0, int)
        if 0 <= category_index < self.category_input.count():
            self.category_input.setCurrentIndex(category_index)

        self.limit_input.setValue(self.settings.value("search/limit", 20, int))
        self.analyze_websites_checkbox.setChecked(
            self.settings.value("search/analyze_websites", True, bool)
        )

        priority_focus = self.settings.value("search/priority_focus", "all")
        if priority_focus == "no_website":
            self.priority_no_website_radio.setChecked(True)
        elif priority_focus == "poor_website":
            self.priority_poor_website_radio.setChecked(True)
        else:
            self.priority_all_radio.setChecked(True)

        # Load business size filter
        business_size = self.settings.value("search/business_size", "All Sizes")
        size_index = self.size_combo.findText(business_size)
        if size_index >= 0:
            self.size_combo.setCurrentIndex(size_index)

    def save_settings(self):
        """Save current settings"""
        self.settings.setValue("search/last_location", self.location_input.text())
        self.settings.setValue(
            "search/last_category_index", self.category_input.currentIndex()
        )
        self.settings.setValue("search/limit", self.limit_input.value())
        self.settings.setValue(
            "search/analyze_websites", self.analyze_websites_checkbox.isChecked()
        )

        if self.priority_no_website_radio.isChecked():
            self.settings.setValue("search/priority_focus", "no_website")
        elif self.priority_poor_website_radio.isChecked():
            self.settings.setValue("search/priority_focus", "poor_website")
        else:
            self.settings.setValue("search/priority_focus", "all")

        # Save business size filter
        self.settings.setValue("search/business_size", self.size_combo.currentText())

    def load_business_types(self):
        """Load business types into the category combo box"""
        # Load custom types from settings
        custom_types = self.settings.value("custom_business_types", [])
        if isinstance(custom_types, str):
            custom_types = [custom_types]
        
        # Combine popular types with custom types
        all_types = sorted(set(POPULAR_TYPES + custom_types))
        
        # Populate combo box
        self.category_input.clear()
        self.category_input.addItems(all_types)
        
        # Update auto-complete suggestions
        self.update_business_type_suggestions()

    def clear_form(self):
        """Clear the search form"""
        self.location_input.clear()
        self.category_input.setCurrentIndex(0)
        self.limit_input.setValue(20)
        self.analyze_websites_checkbox.setChecked(True)
        self.priority_all_radio.setChecked(True)
        self.status_label.clear()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)

    def update_status(self, message, progress):
        """Update status and progress from the background thread"""
        from PySide6.QtCore import QMetaObject, Qt, Q_ARG

        # Update status label
        QMetaObject.invokeMethod(
            self.status_label, "setText", Qt.QueuedConnection, Q_ARG(str, message)
        )

        # Update progress bar
        QMetaObject.invokeMethod(
            self.progress_bar, "setValue", Qt.QueuedConnection, Q_ARG(int, progress)
        )

    @Slot()
    def on_search_clicked(self):
        """Handle search button click with enhanced visual feedback"""
        # Get search parameters
        location = self.location_input.text().strip()

        # Validate location
        if not location:
            QMessageBox.warning(self, "Missing Location", "Please enter a location.")
            # Apply error styling through theme manager
            self.location_input.setProperty("error", True)
            self.location_input.style().unpolish(self.location_input)
            self.location_input.style().polish(self.location_input)
            return

        if not validate_uk_location(location):
            result = QMessageBox.question(
                self,
                "Confirm Location",
                f"The location '{location}' doesn't look like a standard UK location format. "
                "Are you sure this is a valid UK location?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if result != QMessageBox.Yes:
                return

        # Get other parameters
        category = self.category_input.currentText()
        if category == "All Businesses":
            category = None

        limit = self.limit_input.value()
        analyze_websites = self.analyze_websites_checkbox.isChecked()

        # Determine priority focus
        if self.priority_no_website_radio.isChecked():
            priority_focus = "no_website"
        elif self.priority_poor_website_radio.isChecked():
            priority_focus = "poor_website"
        else:
            priority_focus = "all"

        # Get business size filter
        business_size = self.size_combo.currentText()
        if business_size == "All Sizes":
            business_size = None

        # Save to search history
        self.search_history.add_search(location, category)
        
        # Update auto-complete suggestions with new search
        self.update_location_suggestions()
        self.update_business_type_suggestions()

        # Start visual feedback
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.5)
        self.fade_animation.start()
        
        self.search_button.setText("Searching...")
        self.loading_spinner.start()

        # Save settings
        self.save_settings()

        # Start search in a background thread
        self.start_search(location, category, limit, analyze_websites, priority_focus, business_size)

    def perform_search(
        self, location, category, limit, analyze_websites, priority_focus, business_size=None
    ):
        """Perform search operation in the background thread"""
        try:
            # Create database for this location
            db_dir = os.path.join(os.path.expanduser("~"), "UKLeadGen", "data")
            os.makedirs(db_dir, exist_ok=True)

            db_file = os.path.join(db_dir, f"leads_{location.replace(' ', '_')}.db")
            database = LeadDatabase(db_file)

            # Update status
            self.update_status("Initializing scraper...", 5)

            # Create scraper
            scraper = BusinessScraper(use_selenium=True)

            # Create analyzer if needed
            analyzer = None
            if analyze_websites:
                self.update_status("Initializing website analyzer...", 10)
                analyzer = WebsiteAnalyzer(use_lighthouse=True)

            # Start search
            self.update_status(f"Searching for businesses in {location}...", 15)

            businesses = scraper.find_businesses(location, category, limit)

            if not businesses:
                self.update_status("No businesses found.", 100)
                self.search_completed.emit(0)
                self.search_button.setEnabled(True)
                return

            # Update status
            self.update_status(f"Found {len(businesses)} businesses. Processing...", 35)

            # Keep track of businesses to add to database
            businesses_to_add = []

            # Process each business
            for i, business in enumerate(businesses):
                progress = 35 + int(55 * (i + 1) / len(businesses))
                self.update_status(
                    f"Processing {business['name']} ({i+1}/{len(businesses)})...",
                    progress,
                )

                # Set default priority (will be updated if we analyze the website)
                if "website" not in business or not business["website"]:
                    business["priority"] = 1  # No website
                    business["notes"] = "No website detected"

                    # If we're focusing on businesses with no websites, add this one
                    if priority_focus == "all" or priority_focus == "no_website":
                        businesses_to_add.append(business)
                else:
                    # For businesses with websites
                    try:
                        if analyze_websites:
                            # Analyze website
                            analysis_results = analyzer.analyze_website(
                                business["website"]
                            )

                            # Update business with analysis results
                            business.update(analysis_results)

                            # Check if we should include this business based on priority focus
                            if priority_focus == "all":
                                businesses_to_add.append(business)
                            elif (
                                priority_focus == "poor_website"
                                and business["priority"] == 2
                            ):
                                businesses_to_add.append(business)
                            elif (
                                priority_focus == "no_website"
                                and business["priority"] == 1
                            ):
                                businesses_to_add.append(business)
                        else:
                            # Default priority without analysis
                            business["priority"] = (
                                2  # Assume poor website until proven otherwise
                            )

                            # Check if we should include this business based on priority focus
                            if (
                                priority_focus == "all"
                                or priority_focus == "poor_website"
                            ):
                                businesses_to_add.append(business)
                    except Exception as e:
                        business["notes"] = f"Error analyzing website: {str(e)}"

                        # Set default priority for analysis failures
                        business["priority"] = 2  # Assume poor website

                        # Check if we should include this business based on priority focus
                        if priority_focus == "all" or priority_focus == "poor_website":
                            businesses_to_add.append(business)

            # Add all filtered businesses to database
            for business in businesses_to_add:
                database.add_business(business)

            # Final update
            businesses = database.get_all_businesses()
            self.update_status(
                f"Search completed. Found {len(businesses)} businesses.", 100
            )

            # Clean up
            database.close()
            if scraper:
                scraper.close()

            # Emit completed signal
            self.search_completed.emit(len(businesses))

        except Exception as e:
            # Log and emit error
            import traceback

            traceback.print_exc()
            self.search_error.emit(str(e))

        finally:
            # Update UI from main thread
            from PySide6.QtCore import QMetaObject, Qt, Q_ARG

            # Reset button state
            QMetaObject.invokeMethod(
                self.search_button, "setEnabled", Qt.QueuedConnection, Q_ARG(bool, True)
            )
            QMetaObject.invokeMethod(
                self.search_button, "setText", Qt.QueuedConnection, Q_ARG(str, "Search")
            )
            
            # Stop loading spinner
            QMetaObject.invokeMethod(
                self.loading_spinner, "stop", Qt.QueuedConnection
            )
            
            # Hide progress bar
            QMetaObject.invokeMethod(
                self.progress_bar, "setVisible", Qt.QueuedConnection, Q_ARG(bool, False)
            )
            
            # Reset fade animation
            QMetaObject.invokeMethod(
                self.fade_animation, "setStartValue", Qt.QueuedConnection, Q_ARG(float, 0.5)
            )
            QMetaObject.invokeMethod(
                self.fade_animation, "setEndValue", Qt.QueuedConnection, Q_ARG(float, 1.0)
            )
            QMetaObject.invokeMethod(
                self.fade_animation, "start", Qt.QueuedConnection
            )
