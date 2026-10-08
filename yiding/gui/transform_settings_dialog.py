# ------------------------------------------------------------------------------------------
# transform_settings_dialog
# ------------------------------------------------------------------------------------------

from copy import deepcopy

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QFileDialog,
)
from PySide6.QtCore import Qt

from .settings_widgets import (
    PunctuationSettingsWidget,
    TranslationSettingsWidget,
    ExtractionSettingsWidget,
)

# ------------------------------------------------------------------------------------------

class TransformSettingsDialog(QDialog):

    def __init__(
        self,
        main_window,
        operation,
        default_settings,
        save_default_callback
    ):

        super().__init__(main_window)

        self.main_window = main_window
        self.operation = operation
        self.default_settings = deepcopy(
            default_settings
        )
        self.save_default_callback = (
            save_default_callback
        )

        self.sections = {}
        self.selected_settings = None

        titles = {
            "punctuation":
                "PUNCTUATION",

            "translation":
                "TRANSLATION",

            "punctuation_translation":
                "PUNCTUATE + TRANSLATE",

            "term_extraction":
                "TERM EXTRACTION",

            "glossary_extraction":
                "GLOSSARY EXTRACTION",
        }

        self.setWindowTitle(
            titles[operation].title()
        )

        self.resize(
            920,
            700
        )

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            20, 20, 20, 20
        )

        main_layout.setSpacing(12)

        # ---------------------------------------------------------
        # TITLE
        # ---------------------------------------------------------

        title = QLabel(
            titles[operation]
        )

        title.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #555555;
            }
        """)

        main_layout.addWidget(title)

        line = QFrame()
        line.setFixedHeight(2)
        line.setStyleSheet(
            "background-color: #681708;"
        )

        main_layout.addWidget(line)

        # ---------------------------------------------------------
        # SETTINGS BODY
        # ---------------------------------------------------------

        if operation == "punctuation_translation":

            tabs = QTabWidget()

            punctuation_widget = (
                self.build_settings_section(
                    "punctuation",
                    self.default_settings[
                        "punctuation"
                    ]
                )
            )

            translation_widget = (
                self.build_settings_section(
                    "translation",
                    self.default_settings[
                        "translation"
                    ]
                )
            )

            tabs.addTab(
                punctuation_widget,
                "Punctuation"
            )

            tabs.addTab(
                translation_widget,
                "Translation"
            )

            main_layout.addWidget(
                tabs,
                1
            )

        else:

            section_name = operation

            settings_widget = (
                self.build_settings_section(
                    section_name,
                    self.default_settings[
                        section_name
                    ]
                )
            )

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(
                QFrame.NoFrame
            )
            scroll.setWidget(
                settings_widget
            )

            main_layout.addWidget(
                scroll,
                1
            )

        # ---------------------------------------------------------
        # BUTTONS
        # ---------------------------------------------------------

        button_row = QHBoxLayout()

        button_row.addStretch()

        self.save_default_button = QPushButton(
            "Save as Default"
        )

        self.save_default_button.setEnabled(
            False
        )

        self.start_button = QPushButton(
            "Start"
        )

        self.start_button.setObjectName(
            "startTransformButton"
        )

        self.start_button.setStyleSheet("""
            QPushButton#startTransformButton {
                background-color: #681708;
                color: white;
                border: 1px solid #681708;
                border-radius: 4px;
                padding: 7px 22px;
                font-weight: bold;
            }

            QPushButton#startTransformButton:hover {
                background-color: #7d2111;
            }

            QPushButton#startTransformButton:pressed {
                background-color: #541206;
            }
        """)

        button_row.addWidget(
            self.save_default_button
        )

        button_row.addWidget(
            self.start_button
        )

        main_layout.addLayout(
            button_row
        )

        self.original_settings = deepcopy(
            self.current_settings()
        )

        self.watch_changes()

        self.save_default_button.clicked.connect(
            self.save_as_default
        )

        self.start_button.clicked.connect(
            self.start_transform
        )


    # --------------------------------------------------------------------------------------
    # GENERAL BUILDERS
    # --------------------------------------------------------------------------------------

    def build_settings_section(
        self,
        section_name,
        settings
    ):

        if section_name == "punctuation":

            widget = (
                PunctuationSettingsWidget(
                    self.main_window,
                    settings
                )
            )

        elif section_name == "translation":

            widget = (
                TranslationSettingsWidget(
                    self.main_window,
                    settings
                )
            )

        elif section_name in (
            "term_extraction",
            "glossary_extraction",
        ):

            widget = (
                ExtractionSettingsWidget(
                    self.main_window,
                    settings
                )
            )

        else:

            raise ValueError(
                f"Unknown transformation: {section_name}"
            )

        self.sections[
            section_name
        ] = widget

        return widget


    def current_settings(self):

        return {
            section_name:
                settings_widget.current_settings()

            for (
                section_name,
                settings_widget
            ) in self.sections.items()
        }


    # --------------------------------------------------------------------------------------
    # DIRTY TRACKING
    # --------------------------------------------------------------------------------------

    def watch_changes(self):

        for widget in self.findChildren(
            QLineEdit
        ):

            widget.textChanged.connect(
                self.update_dirty_state
            )

        for widget in self.findChildren(
            QPlainTextEdit
        ):

            widget.textChanged.connect(
                self.update_dirty_state
            )

        for widget in self.findChildren(
            QCheckBox
        ):

            widget.toggled.connect(
                self.update_dirty_state
            )

        for widget in self.findChildren(
            QComboBox
        ):

            widget.currentIndexChanged.connect(
                self.update_dirty_state
            )

        for widget in self.findChildren(
            QSpinBox
        ):

            widget.valueChanged.connect(
                self.update_dirty_state
            )

        for widget in self.findChildren(
            QSlider
        ):

            widget.valueChanged.connect(
                self.update_dirty_state
            )


    def update_dirty_state(
        self,
        *args
    ):

        dirty = (
            self.current_settings()
            != self.original_settings
        )

        self.save_default_button.setEnabled(
            dirty
        )


    # --------------------------------------------------------------------------------------
    # BUTTON ACTIONS
    # --------------------------------------------------------------------------------------

    def save_as_default(self):

        settings = self.current_settings()

        self.save_default_callback(
            settings
        )

        self.original_settings = deepcopy(
            settings
        )

        self.save_default_button.setEnabled(
            False
        )


    def start_transform(self):

        self.selected_settings = (
            self.current_settings()
        )

        self.accept()

# ------------------------------------------------------------------------------------------
