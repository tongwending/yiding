# ------------------------------------------------------------------------------------------
# settings_widgets
# ------------------------------------------------------------------------------------------

from PySide6.QtCore import Qt

from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


# ------------------------------------------------------------------------------------------
# BASE
# ------------------------------------------------------------------------------------------

class BaseSettingsWidget(QWidget):

    def __init__(
        self,
        main_window
    ):

        super().__init__()

        self.main_window = main_window


    def create_spin(
        self,
        value,
        minimum=0,
        maximum=1000
    ):

        spin = QSpinBox()

        spin.setMinimum(
            minimum
        )

        spin.setMaximum(
            maximum
        )

        spin.setValue(
            value
        )

        spin.setFixedWidth(
            90
        )

        return spin


    def read_model_settings(
        self,
        controls
    ):

        settings = {}

        self.main_window.save_model_settings(
            settings,
            controls
        )

        return settings


    def build_cross_examination(
        self,
        settings,
        title="CROSS-EXAMINATION"
    ):

        widget = QWidget()

        layout = QVBoxLayout(
            widget
        )

        layout.setContentsMargins(
            0, 0, 0, 0
        )

        controls = {}

        # HEADER

        header = QHBoxLayout()

        header.setSpacing(
            8
        )

        header.addWidget(
            self.main_window.create_settings_heading(
                title
            )
        )

        controls["cross_check"] = (
            QCheckBox()
        )

        controls["cross_check"].setChecked(
            settings[
                "cross_check"
            ]["enabled"]
        )

        header.addWidget(
            controls["cross_check"]
        )

        header.addStretch()

        layout.addLayout(
            header
        )

        # MODELS

        models = QWidget()

        models_layout = QHBoxLayout(
            models
        )

        models_layout.setContentsMargins(
            0, 0, 0, 0
        )

        models_layout.setSpacing(
            35
        )

        (
            comparison_widget,
            controls["cross_examination"]
        ) = (
            self.main_window
            .create_model_settings_widget(
                settings[
                    "cross_examination"
                ],
                "Comparison Model:"
            )
        )

        (
            correction_widget,
            controls["cross_correction"]
        ) = (
            self.main_window
            .create_model_settings_widget(
                settings[
                    "cross_correction"
                ],
                "Correction Model:"
            )
        )

        models_layout.addWidget(
            comparison_widget,
            0,
            Qt.AlignTop
        )

        divider = QFrame()

        divider.setFixedWidth(
            1
        )

        divider.setStyleSheet(
            "background-color: #c7c7c7;"
        )

        models_layout.addWidget(
            divider
        )

        models_layout.addWidget(
            correction_widget,
            0,
            Qt.AlignTop
        )

        models_layout.addStretch()

        models.setVisible(
            controls[
                "cross_check"
            ].isChecked()
        )

        controls[
            "cross_check"
        ].toggled.connect(
            models.setVisible
        )

        layout.addWidget(
            models
        )

        return widget, controls


    def read_cross_settings(
        self,
        controls
    ):

        return {
            "cross_check": {
                "enabled":
                    controls[
                        "cross_check"
                    ].isChecked()
            },

            "cross_examination":
                self.read_model_settings(
                    controls[
                        "cross_examination"
                    ]
                ),

            "cross_correction":
                self.read_model_settings(
                    controls[
                        "cross_correction"
                    ]
                ),
        }


    def load_cross_settings(
        self,
        settings,
        controls
    ):

        controls[
            "cross_check"
        ].setChecked(
            settings[
                "cross_check"
            ]["enabled"]
        )

        self.main_window.reload_model_settings(
            settings[
                "cross_examination"
            ],
            controls[
                "cross_examination"
            ]
        )

        self.main_window.reload_model_settings(
            settings[
                "cross_correction"
            ],
            controls[
                "cross_correction"
            ]
        )


# ------------------------------------------------------------------------------------------
# PUNCTUATION
# ------------------------------------------------------------------------------------------

class PunctuationSettingsWidget(
    BaseSettingsWidget
):

    def __init__(
        self,
        main_window,
        settings
    ):

        super().__init__(
            main_window
        )

        self.controls = {}

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            10, 10, 10, 10
        )

        tabs = QTabWidget()

        # =========================================================
        # PHILOLOGICAL SETTINGS
        # =========================================================

        philological_tab = QWidget()

        philological_layout = QVBoxLayout(
            philological_tab
        )

        philological_layout.setContentsMargins(
            12, 12, 12, 12
        )

        philological_layout.addWidget(
            QLabel("Guidelines:")
        )

        self.controls[
            "guidelines"
        ] = QPlainTextEdit()

        self.controls[
            "guidelines"
        ].setPlainText(
            settings["guidelines"]
        )

        philological_layout.addWidget(
            self.controls[
                "guidelines"
            ]
        )

        philological_layout.addStretch()

        # =========================================================
        # LLM SETTINGS
        # =========================================================

        llm_tab = QWidget()

        llm_layout = QVBoxLayout(
            llm_tab
        )

        llm_layout.setContentsMargins(
            12, 12, 12, 12
        )

        llm_layout.setSpacing(
            12
        )

        # SPANS + MODEL

        options_row = QHBoxLayout()

        options_row.setSpacing(
            25
        )

        spans_widget = QWidget()

        spans_form = QFormLayout(
            spans_widget
        )

        spans_form.setContentsMargins(
            0, 0, 0, 0
        )

        self.controls[
            "facsimile_span"
        ] = self.create_spin(
            settings[
                "facsimile_span"
            ]
        )

        self.controls[
            "punctuation_span"
        ] = self.create_spin(
            settings[
                "punctuation_span"
            ]
        )

        self.controls[
            "max_unsegmented_span"
        ] = self.create_spin(
            settings[
                "max_unsegmented_span"
            ],
            maximum=100000
        )

        self.controls[
            "max_punctuation_attempts"
        ] = self.create_spin(
            settings[
                "max_punctuation_attempts"
            ]
        )

        spans_form.addRow(
            "Facsimile span:",
            self.controls[
                "facsimile_span"
            ]
        )

        spans_form.addRow(
            "Punctuation span:",
            self.controls[
                "punctuation_span"
            ]
        )

        spans_form.addRow(
            "Max. segment characters:",
            self.controls[
                "max_unsegmented_span"
            ]
        )

        spans_form.addRow(
            "Max. segment retries:",
            self.controls[
                "max_punctuation_attempts"
            ]
        )

        options_row.addWidget(
            spans_widget
        )

        divider = QFrame()

        divider.setFixedWidth(
            1
        )

        divider.setStyleSheet(
            "background-color: #c7c7c7;"
        )

        options_row.addWidget(
            divider
        )

        (
            punctuation_model_widget,
            self.controls["punctuation"]
        ) = (
            self.main_window
            .create_model_settings_widget(
                settings[
                    "punctuation"
                ],
                "Punctuation Model:"
            )
        )

        options_row.addWidget(
            punctuation_model_widget,
            0,
            Qt.AlignTop
        )

        options_row.addStretch()

        llm_layout.addLayout(
            options_row
        )

        # CROSS-EXAMINATION

        cross_line = QFrame()

        cross_line.setFixedHeight(
            3
        )

        cross_line.setStyleSheet(
            "background-color: #8f8f8f;"
        )

        llm_layout.addWidget(
            cross_line
        )

        (
            cross_widget,
            cross_controls
        ) = self.build_cross_examination(
            settings,
            "CROSS-EXAMINATION SETTINGS"
        )

        self.controls.update(
            cross_controls
        )

        llm_layout.addWidget(
            cross_widget
        )

        llm_layout.addStretch()

        # TABS

        tabs.addTab(
            philological_tab,
            "Philological Settings"
        )

        tabs.addTab(
            llm_tab,
            "LLM Settings"
        )

        layout.addWidget(
            tabs,
            1
        )


    def current_settings(self):

        result = {
            "guidelines":
                self.controls[
                    "guidelines"
                ].toPlainText(),

            "facsimile_span":
                self.controls[
                    "facsimile_span"
                ].value(),

            "punctuation_span":
                self.controls[
                    "punctuation_span"
                ].value(),

            "max_unsegmented_span":
                self.controls[
                    "max_unsegmented_span"
                ].value(),

            "max_punctuation_attempts":
                self.controls[
                    "max_punctuation_attempts"
                ].value(),

            "punctuation":
                self.read_model_settings(
                    self.controls[
                        "punctuation"
                    ]
                ),
        }

        result.update(
            self.read_cross_settings(
                self.controls
            )
        )

        return result


    def load_settings(
        self,
        settings
    ):

        self.controls[
            "guidelines"
        ].setPlainText(
            settings[
                "guidelines"
            ]
        )

        self.controls[
            "facsimile_span"
        ].setValue(
            settings[
                "facsimile_span"
            ]
        )

        self.controls[
            "punctuation_span"
        ].setValue(
            settings[
                "punctuation_span"
            ]
        )

        self.controls[
            "max_unsegmented_span"
        ].setValue(
            settings[
                "max_unsegmented_span"
            ]
        )

        self.controls[
            "max_punctuation_attempts"
        ].setValue(
            settings[
                "max_punctuation_attempts"
            ]
        )

        self.main_window.reload_model_settings(
            settings[
                "punctuation"
            ],
            self.controls[
                "punctuation"
            ]
        )

        self.load_cross_settings(
            settings,
            self.controls
        )


# ------------------------------------------------------------------------------------------
# TRANSLATION
# ------------------------------------------------------------------------------------------

class TranslationSettingsWidget(
    BaseSettingsWidget
):

    def __init__(
        self,
        main_window,
        settings
    ):

        super().__init__(
            main_window
        )

        self.controls = {}

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            10, 10, 10, 10
        )

        tabs = QTabWidget()

        # =========================================================
        # PHILOLOGICAL SETTINGS
        # =========================================================

        philological_tab = QWidget()

        philological_layout = QVBoxLayout(
            philological_tab
        )

        philological_layout.setContentsMargins(
            12, 12, 12, 12
        )

        philological_layout.setSpacing(
            12
        )

        # GUIDELINES

        philological_layout.addWidget(
            QLabel("Guidelines:")
        )

        self.controls[
            "guidelines"
        ] = QPlainTextEdit()

        self.controls[
            "guidelines"
        ].setPlainText(
            settings[
                "guidelines"
            ]
        )

        philological_layout.addWidget(
            self.controls[
                "guidelines"
            ]
        )

        # LANGUAGE + GLOSSARY

        options_widget = QWidget()

        options_form = QFormLayout(
            options_widget
        )

        options_form.setContentsMargins(
            0, 0, 0, 0
        )

        self.controls[
            "language"
        ] = QLineEdit(
            settings[
                "language"
            ]
        )

        self.controls[
            "language"
        ].setFixedWidth(
            165
        )

        self.controls[
            "glossary"
        ] = QLineEdit(
            settings[
                "glossary"
            ]
        )

        self.controls[
            "glossary"
        ].setFixedWidth(
            260
        )

        glossary_browse_button = QPushButton(
            "Browse..."
        )

        glossary_browse_button.setFixedWidth(
            80
        )

        glossary_browse_button.setStyleSheet("""
            QPushButton {
                color: #681708;
                background-color: #eeeae1;
                border: 1px solid #681708;
                border-radius: 4px;
                padding: 4px 8px;
            }

            QPushButton:hover {
                background-color: #f8f6f1;
                border: 1px solid #681708;
            }

            QPushButton:pressed {
                background-color: #e2ddd3;
                border: 1px solid #681708;
            }
        """)

        glossary_browse_button.clicked.connect(
            self.select_glossary_file
        )

        glossary_row = QWidget()

        glossary_row_layout = QHBoxLayout(
            glossary_row
        )

        glossary_row_layout.setContentsMargins(
            0, 0, 0, 0
        )

        glossary_row_layout.setSpacing(
            6
        )

        glossary_row_layout.addWidget(
            self.controls[
                "glossary"
            ]
        )

        glossary_row_layout.addWidget(
            glossary_browse_button
        )

        options_form.addRow(
            "Language:",
            self.controls[
                "language"
            ]
        )

        options_form.addRow(
            "Glossary:",
            glossary_row
        )

        philological_layout.addWidget(
            options_widget,
            0,
            Qt.AlignLeft
        )

        philological_layout.addStretch()

        # =========================================================
        # LLM SETTINGS
        # =========================================================

        llm_tab = QWidget()

        llm_layout = QVBoxLayout(
            llm_tab
        )

        llm_layout.setContentsMargins(
            12, 12, 12, 12
        )

        llm_layout.setSpacing(
            12
        )

        top_row = QHBoxLayout()

        top_row.setSpacing(
            25
        )

        # LEFT SIDE

        translation_section = QWidget()

        translation_section_layout = QVBoxLayout(
            translation_section
        )

        translation_section_layout.setContentsMargins(
            0, 0, 0, 0
        )

        translation_section_layout.setSpacing(
            12
        )

        # SPAN

        span_widget = QWidget()

        span_form = QFormLayout(
            span_widget
        )

        span_form.setContentsMargins(
            0, 0, 0, 0
        )

        self.controls[
            "translation_span"
        ] = self.create_spin(
            settings[
                "translation_span"
            ]
        )

        span_form.addRow(
            "Translation span:",
            self.controls[
                "translation_span"
            ]
        )

        translation_section_layout.addWidget(
            span_widget,
            0,
            Qt.AlignLeft
        )

        span_separator = QFrame()

        span_separator.setFixedHeight(
            1
        )

        span_separator.setStyleSheet(
            "background-color: #c7c7c7;"
        )

        translation_section_layout.addSpacing(
            4
        )

        translation_section_layout.addWidget(
            span_separator
        )

        translation_section_layout.addSpacing(
            8
        )

        # TWO MODELS SIDE BY SIDE

        models_row = QHBoxLayout()

        models_row.setSpacing(
            35
        )

        (
            translation_widget,
            self.controls["translation"]
        ) = (
            self.main_window
            .create_model_settings_widget(
                settings[
                    "translation"
                ],
                "Translation Model:"
            )
        )

        models_row.addWidget(
            translation_widget,
            0,
            Qt.AlignTop
        )

        models_divider = QFrame()

        models_divider.setFixedWidth(
            1
        )

        models_divider.setStyleSheet(
            "background-color: #c7c7c7;"
        )

        models_row.addWidget(
            models_divider
        )

        (
            glossary_widget,
            self.controls[
                "glossary_extraction"
            ]
        ) = (
            self.main_window
            .create_model_settings_widget(
                settings[
                    "glossary_extraction"
                ],
                "Glossary Extraction Model:"
            )
        )

        models_row.addWidget(
            glossary_widget,
            0,
            Qt.AlignTop
        )

        models_row.addStretch()

        translation_section_layout.addLayout(
            models_row
        )

        translation_section_layout.addStretch()

        top_row.addWidget(
            translation_section,
            2,
            Qt.AlignTop
        )

        # THICK DIVIDER

        term_divider = QFrame()

        term_divider.setFixedWidth(
            3
        )

        term_divider.setStyleSheet(
            "background-color: #8f8f8f;"
        )

        top_row.addWidget(
            term_divider
        )

        # TERM SELECTION

        term_section = QWidget()

        term_section_layout = QVBoxLayout(
            term_section
        )

        term_section_layout.setContentsMargins(
            0, 0, 0, 0
        )

        term_section_layout.setSpacing(
            8
        )

        term_header = QHBoxLayout()

        term_header.setSpacing(
            8
        )

        term_header.addWidget(
            self.main_window.create_settings_heading(
                "LLM TERM SELECTION"
            )
        )

        self.controls[
            "llm_glossary_selection"
        ] = QCheckBox()

        self.controls[
            "llm_glossary_selection"
        ].setChecked(
            settings[
                "llm_glossary_selection"
            ]["enabled"]
        )

        term_header.addWidget(
            self.controls[
                "llm_glossary_selection"
            ]
        )

        term_header.addStretch()

        term_section_layout.addLayout(
            term_header
        )

        (
            term_widget,
            self.controls[
                "glossary_selection"
            ]
        ) = (
            self.main_window
            .create_model_settings_widget(
                settings[
                    "glossary_selection"
                ],
                "Term Selection Model:"
            )
        )

        term_widget.setVisible(
            self.controls[
                "llm_glossary_selection"
            ].isChecked()
        )

        self.controls[
            "llm_glossary_selection"
        ].toggled.connect(
            term_widget.setVisible
        )

        term_section_layout.addWidget(
            term_widget,
            0,
            Qt.AlignTop
        )

        term_section_layout.addStretch()

        top_row.addWidget(
            term_section,
            1,
            Qt.AlignTop
        )

        llm_layout.addLayout(
            top_row
        )

        # CROSS-EXAMINATION

        review_line = QFrame()

        review_line.setFixedHeight(
            3
        )

        review_line.setStyleSheet(
            "background-color: #8f8f8f;"
        )

        llm_layout.addWidget(
            review_line
        )

        (
            cross_widget,
            cross_controls
        ) = self.build_cross_examination(
            settings
        )

        self.controls.update(
            cross_controls
        )

        llm_layout.addWidget(
            cross_widget
        )

        llm_layout.addStretch()

        # TABS

        tabs.addTab(
            philological_tab,
            "Philological Settings"
        )

        tabs.addTab(
            llm_tab,
            "LLM Settings"
        )

        layout.addWidget(
            tabs,
            1
        )


    def select_glossary_file(self):

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select Glossary",
            "",
            "Glossary Files (*.csv *.txt);;"
            "CSV Files (*.csv);;"
            "Text Files (*.txt);;"
            "All Files (*)"
        )

        if not filename:
            return

        self.controls[
            "glossary"
        ].setText(
            filename
        )


    def current_settings(self):

        result = {
            "guidelines":
                self.controls[
                    "guidelines"
                ].toPlainText(),

            "language":
                self.controls[
                    "language"
                ].text().strip(),

            "glossary":
                self.controls[
                    "glossary"
                ].text().strip(),

            "translation_span":
                self.controls[
                    "translation_span"
                ].value(),

            "translation":
                self.read_model_settings(
                    self.controls[
                        "translation"
                    ]
                ),

            "glossary_extraction":
                self.read_model_settings(
                    self.controls[
                        "glossary_extraction"
                    ]
                ),

            "llm_glossary_selection": {
                "enabled":
                    self.controls[
                        "llm_glossary_selection"
                    ].isChecked()
            },

            "glossary_selection":
                self.read_model_settings(
                    self.controls[
                        "glossary_selection"
                    ]
                ),
        }

        result.update(
            self.read_cross_settings(
                self.controls
            )
        )

        return result


    def load_settings(
        self,
        settings
    ):

        self.controls[
            "guidelines"
        ].setPlainText(
            settings[
                "guidelines"
            ]
        )

        self.controls[
            "language"
        ].setText(
            settings[
                "language"
            ]
        )

        self.controls[
            "glossary"
        ].setText(
            settings[
                "glossary"
            ]
        )

        self.controls[
            "translation_span"
        ].setValue(
            settings[
                "translation_span"
            ]
        )

        self.main_window.reload_model_settings(
            settings[
                "translation"
            ],
            self.controls[
                "translation"
            ]
        )

        self.main_window.reload_model_settings(
            settings[
                "glossary_extraction"
            ],
            self.controls[
                "glossary_extraction"
            ]
        )

        self.controls[
            "llm_glossary_selection"
        ].setChecked(
            settings[
                "llm_glossary_selection"
            ]["enabled"]
        )

        self.main_window.reload_model_settings(
            settings[
                "glossary_selection"
            ],
            self.controls[
                "glossary_selection"
            ]
        )

        self.load_cross_settings(
            settings,
            self.controls
        )


# ------------------------------------------------------------------------------------------
# EXTRACTION
# ------------------------------------------------------------------------------------------

class ExtractionSettingsWidget(
    BaseSettingsWidget
):

    def __init__(
        self,
        main_window,
        settings
    ):

        super().__init__(
            main_window
        )

        self.controls = {}

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            10, 10, 10, 10
        )

        # MODEL

        (
            extraction_widget,
            self.controls["extraction"]
        ) = (
            self.main_window
            .create_model_settings_widget(
                settings[
                    "extraction"
                ],
                "Extraction Model:"
            )
        )

        layout.addWidget(
            extraction_widget,
            0,
            Qt.AlignLeft
        )

        # SOFT LINE

        model_separator = QFrame()

        model_separator.setFixedHeight(
            1
        )

        model_separator.setStyleSheet(
            "background-color: #c7c7c7;"
        )

        layout.addSpacing(
            4
        )

        layout.addWidget(
            model_separator
        )

        layout.addSpacing(
            8
        )

        # SPAN

        span_form = QFormLayout()

        self.controls[
            "span"
        ] = self.create_spin(
            settings[
                "span"
            ],
            minimum=1,
            maximum=100000
        )

        span_form.addRow(
            "Span:",
            self.controls[
                "span"
            ]
        )

        layout.addLayout(
            span_form
        )

        layout.addSpacing(
            12
        )

        # GUIDELINES

        layout.addWidget(
            QLabel(
                "Additional Guidelines (optional):"
            )
        )

        self.controls[
            "guidelines"
        ] = QPlainTextEdit()

        self.controls[
            "guidelines"
        ].setFixedHeight(
            100
        )

        self.controls[
            "guidelines"
        ].setPlainText(
            settings.get(
                "guidelines",
                ""
            )
        )

        layout.addWidget(
            self.controls[
                "guidelines"
            ]
        )

        layout.addStretch()


    def current_settings(self):

        return {
            "guidelines":
                self.controls[
                    "guidelines"
                ].toPlainText(),

            "span":
                self.controls[
                    "span"
                ].value(),

            "extraction":
                self.read_model_settings(
                    self.controls[
                        "extraction"
                    ]
                ),
        }


    def load_settings(
        self,
        settings
    ):

        self.controls[
            "guidelines"
        ].setPlainText(
            settings.get(
                "guidelines",
                ""
            )
        )

        self.controls[
            "span"
        ].setValue(
            settings[
                "span"
            ]
        )

        self.main_window.reload_model_settings(
            settings[
                "extraction"
            ],
            self.controls[
                "extraction"
            ]
        )
