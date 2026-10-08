# ------------------------------------------------------------------------------------------
# new_project_dialog
# ------------------------------------------------------------------------------------------

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class NewProjectDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("New Yiding Project")
        self.setMinimumWidth(560)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # ---------------------------------------------------------
        # SOURCE
        # ---------------------------------------------------------

        source_row = QHBoxLayout()

        source_label = QLabel("Source:")

        self.source_combo = QComboBox()
        self.source_combo.addItems([
            "Create text",
            "Download from Kanseki Repository",
        ])
        self.source_combo.setFixedWidth(260)

        source_row.addWidget(source_label)
        source_row.addWidget(self.source_combo)
        source_row.addStretch()

        layout.addLayout(source_row)

        # ---------------------------------------------------------
        # SOURCE-SPECIFIC PAGES
        # ---------------------------------------------------------

        self.source_stack = QStackedWidget()

        self.user_page = self.create_user_page()
        self.kanripo_page = self.create_kanripo_page()

        self.source_stack.addWidget(self.user_page)
        self.source_stack.addWidget(self.kanripo_page)

        layout.addWidget(self.source_stack)

        self.source_combo.currentIndexChanged.connect(
            self.source_stack.setCurrentIndex
        )

        # ---------------------------------------------------------
        # BUTTONS
        # ---------------------------------------------------------

        button_row = QHBoxLayout()
        button_row.addStretch()

        cancel_button = QPushButton("Cancel")
        create_button = QPushButton("Create")

        create_button.setStyleSheet("""
            QPushButton {
                color: white;
                background-color: #681708;
                border: 1px solid #681708;
                border-radius: 4px;
                padding: 6px 16px;
            }

            QPushButton:hover {
                background-color: #7d2112;
            }
        """)

        cancel_button.clicked.connect(self.reject)
        create_button.clicked.connect(self.validate_and_accept)

        button_row.addWidget(cancel_button)
        button_row.addWidget(create_button)

        layout.addLayout(button_row)

    # --------------------------------------------------------------------------------------

    def create_user_page(self):

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(10)

        # ---------------------------------------------------------
        # ORIGINAL TITLE
        # ---------------------------------------------------------

        title_form = QFormLayout()

        self.original_title_edit = QLineEdit()

        title_form.addRow(
            "Original title:",
            self.original_title_edit,
        )

        layout.addLayout(title_form)

        # ---------------------------------------------------------
        # INCLUDE
        # ---------------------------------------------------------

        include_row = QHBoxLayout()

        include_label = QLabel("Include:")
        include_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
            }
        """)

        self.include_unpunctuated_checkbox = QCheckBox(
            "Unpunctuated Text"
        )
        self.include_punctuated_checkbox = QCheckBox(
            "Punctuated Text"
        )
        self.include_translation_checkbox = QCheckBox(
            "Translation"
        )

        include_row.addWidget(include_label)
        include_row.addSpacing(10)

        include_row.addWidget(
            self.include_unpunctuated_checkbox
        )

        include_row.addSpacing(15)

        include_row.addWidget(
            self.include_punctuated_checkbox
        )

        include_row.addSpacing(15)

        include_row.addWidget(
            self.include_translation_checkbox
        )

        include_row.addStretch()

        layout.addLayout(include_row)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)

        layout.addWidget(separator)

        # ---------------------------------------------------------
        # TEXT TYPE TABS
        # ---------------------------------------------------------

        self.input_tabs = QTabWidget()

        self.unpunctuated_input_page = (
            self.create_unpunctuated_input_page()
        )

        self.punctuated_input_page = (
            self.create_punctuated_input_page()
        )

        self.translation_input_page = (
            self.create_translation_input_page()
        )

        layout.addWidget(self.input_tabs, 1)

        # Checkbox → tab visibility
        self.include_unpunctuated_checkbox.toggled.connect(
            self.update_input_tabs
        )

        self.include_punctuated_checkbox.toggled.connect(
            self.update_input_tabs
        )

        self.include_translation_checkbox.toggled.connect(
            self.update_input_tabs
        )

        self.update_input_tabs()

        return page

    # --------------------------------------------------------------------------------------

    def create_unpunctuated_input_page(self):

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(10)

        # ---------------------------------------------------------
        # SEGMENT DIVISION
        # ---------------------------------------------------------

        segment_title = QLabel("Segment Division")
        segment_title.setStyleSheet("""
            QLabel {
                font-weight: bold;
            }
        """)

        segment_note = QLabel(
            "The text must be divisible into segments."
        )
        segment_note.setStyleSheet("""
            QLabel {
                color: #666666;
            }
        """)

        layout.addWidget(segment_title)
        layout.addWidget(segment_note)

        # Delimiter + preserve
        divider_row = QHBoxLayout()

        divider_label = QLabel("Segment delimiter:")

        self.unpunctuated_divider_edit = QLineEdit(r"\n\n")
        self.unpunctuated_divider_edit.setFixedWidth(100)

        self.unpunctuated_keep_divider_checkbox = QCheckBox(
            "Preserve delimiter"
        )

        divider_row.addWidget(divider_label)
        divider_row.addWidget(
            self.unpunctuated_divider_edit
        )
        divider_row.addSpacing(12)
        divider_row.addWidget(
            self.unpunctuated_keep_divider_checkbox
        )
        divider_row.addStretch()

        layout.addLayout(divider_row)

        # Whole-line option underneath
        self.unpunctuated_whole_line_checkbox = QCheckBox(
            "If a line starts with the delimiter, use the entire line as the delimiter"
        )

        layout.addWidget(
            self.unpunctuated_whole_line_checkbox
        )

        # Paragraph option underneath that
        self.segments_are_paragraphs_checkbox = QCheckBox(
            "Segments represent paragraphs"
        )

        layout.addWidget(
            self.segments_are_paragraphs_checkbox
        )

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)

        layout.addWidget(separator)

        # ---------------------------------------------------------
        # TEXT
        # ---------------------------------------------------------

        text_label = QLabel("Text:")
        text_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
            }
        """)

        layout.addWidget(text_label)

        self.unpunctuated_text_edit = QPlainTextEdit()
        self.unpunctuated_text_edit.setMinimumHeight(220)

        layout.addWidget(
            self.unpunctuated_text_edit,
            1,
        )

        return page


    def create_punctuated_input_page(self):

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(10)

        # ---------------------------------------------------------
        # SEGMENT DIVISION
        # ---------------------------------------------------------

        segment_title = QLabel("Segment Division")
        segment_title.setStyleSheet("""
            QLabel {
                font-weight: bold;
            }
        """)

        segment_note = QLabel(
            "The text must be divisible into segments."
        )
        segment_note.setStyleSheet("""
            QLabel {
                color: #666666;
            }
        """)

        layout.addWidget(segment_title)
        layout.addWidget(segment_note)

        # Delimiter + preserve
        divider_row = QHBoxLayout()

        divider_label = QLabel("Segment delimiter:")

        self.punctuated_divider_edit = QLineEdit(r"\n\n")
        self.punctuated_divider_edit.setFixedWidth(100)

        self.punctuated_keep_divider_checkbox = QCheckBox(
            "Preserve delimiter"
        )

        divider_row.addWidget(divider_label)
        divider_row.addWidget(
            self.punctuated_divider_edit
        )
        divider_row.addSpacing(12)
        divider_row.addWidget(
            self.punctuated_keep_divider_checkbox
        )
        divider_row.addStretch()

        layout.addLayout(divider_row)

        # Whole-line option underneath
        self.punctuated_whole_line_checkbox = QCheckBox(
            "If a line starts with the delimiter, use the entire line as the delimiter"
        )

        layout.addWidget(
            self.punctuated_whole_line_checkbox
        )

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)

        layout.addWidget(separator)

        # ---------------------------------------------------------
        # TEXT
        # ---------------------------------------------------------

        text_label = QLabel("Text:")
        text_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
            }
        """)

        layout.addWidget(text_label)

        self.punctuated_text_edit = QPlainTextEdit()
        self.punctuated_text_edit.setMinimumHeight(220)

        layout.addWidget(
            self.punctuated_text_edit,
            1,
        )

        return page


    def create_translation_input_page(self):

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(10)

        # ---------------------------------------------------------
        # TRANSLATED TITLE
        # ---------------------------------------------------------

        translated_title_row = QHBoxLayout()

        translated_title_label = QLabel(
            "Translated title:"
        )

        self.translated_title_edit = QLineEdit()

        translated_title_row.addWidget(
            translated_title_label
        )
        translated_title_row.addWidget(
            self.translated_title_edit,
            1,
        )

        layout.addLayout(translated_title_row)

        # ---------------------------------------------------------
        # TRANSLATION LANGUAGE
        # ---------------------------------------------------------

        language_row = QHBoxLayout()

        language_label = QLabel(
            "Translation language:"
        )

        self.translation_language_edit = QLineEdit(
            "English"
        )
        self.translation_language_edit.setFixedWidth(180)

        language_row.addWidget(language_label)
        language_row.addWidget(
            self.translation_language_edit
        )
        language_row.addStretch()

        layout.addLayout(language_row)

        # Separator between translation metadata and division
        metadata_separator = QFrame()
        metadata_separator.setFrameShape(QFrame.HLine)
        metadata_separator.setFrameShadow(QFrame.Sunken)

        layout.addWidget(metadata_separator)

        # ---------------------------------------------------------
        # SEGMENT DIVISION
        # ---------------------------------------------------------

        segment_title = QLabel("Segment Division")
        segment_title.setStyleSheet("""
            QLabel {
                font-weight: bold;
            }
        """)

        segment_note = QLabel(
            "The text must be divisible into segments."
        )
        segment_note.setStyleSheet("""
            QLabel {
                color: #666666;
            }
        """)

        layout.addWidget(segment_title)
        layout.addWidget(segment_note)

        # Delimiter + preserve
        divider_row = QHBoxLayout()

        divider_label = QLabel("Segment delimiter:")

        self.translation_divider_edit = QLineEdit(
            r"\n\n"
        )
        self.translation_divider_edit.setFixedWidth(100)

        self.translation_keep_divider_checkbox = QCheckBox(
            "Preserve delimiter"
        )

        divider_row.addWidget(divider_label)
        divider_row.addWidget(
            self.translation_divider_edit
        )
        divider_row.addSpacing(12)
        divider_row.addWidget(
            self.translation_keep_divider_checkbox
        )
        divider_row.addStretch()

        layout.addLayout(divider_row)

        # Whole-line option underneath
        self.translation_whole_line_checkbox = QCheckBox(
            "If a line starts with the delimiter, use the entire line as the delimiter"
        )

        layout.addWidget(
            self.translation_whole_line_checkbox
        )

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)

        layout.addWidget(separator)

        # ---------------------------------------------------------
        # TEXT
        # ---------------------------------------------------------

        text_label = QLabel("Text:")
        text_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
            }
        """)

        layout.addWidget(text_label)

        self.translation_text_edit = QPlainTextEdit()
        self.translation_text_edit.setMinimumHeight(220)

        layout.addWidget(
            self.translation_text_edit,
            1,
        )

        return page

    # --------------------------------------------------------------------------------------

    def update_input_tabs(self):

        current_widget = self.input_tabs.currentWidget()

        while self.input_tabs.count():
            self.input_tabs.removeTab(0)

        if self.include_unpunctuated_checkbox.isChecked():

            self.input_tabs.addTab(
                self.unpunctuated_input_page,
                "Unpunctuated Text",
            )

        if self.include_punctuated_checkbox.isChecked():

            self.input_tabs.addTab(
                self.punctuated_input_page,
                "Punctuated Text",
            )

        if self.include_translation_checkbox.isChecked():

            self.input_tabs.addTab(
                self.translation_input_page,
                "Translation",
            )

        if current_widget is not None:

            index = self.input_tabs.indexOf(
                current_widget
            )

            if index != -1:
                self.input_tabs.setCurrentIndex(index)

    # --------------------------------------------------------------------------------------

    def create_kanripo_page(self):

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 10, 0, 0)

        form = QFormLayout()

        self.kanripo_code_edit = QLineEdit()
        self.kanripo_code_edit.setPlaceholderText(
            "e.g. KR5h0008"
        )
        self.kanripo_code_edit.setMaximumWidth(220)

        self.glosses_checkbox = QCheckBox()
        self.glosses_checkbox.setChecked(True)

        form.addRow(
            "Kanripo code:",
            self.kanripo_code_edit,
        )

        form.addRow(
            "Include glosses:",
            self.glosses_checkbox,
        )

        layout.addLayout(form)
        layout.addStretch()

        return page

    # --------------------------------------------------------------------------------------

    def validate_and_accept(self):

        if self.source_type() == "raw":

            if not (
                self.includes_unpunctuated()
                or self.includes_punctuated()
                or self.includes_translation()
            ):
                QMessageBox.warning(
                    self,
                    "Text Required",
                    "Select at least one text type to include.",
                )
                return

            if (
                self.includes_unpunctuated()
                and not self.unpunctuated_text_edit.toPlainText().strip()
            ):
                QMessageBox.warning(
                    self,
                    "Unpunctuated Text Required",
                    "Enter the unpunctuated text.",
                )
                return

            if (
                self.includes_punctuated()
                and not self.punctuated_text_edit.toPlainText().strip()
            ):
                QMessageBox.warning(
                    self,
                    "Punctuated Text Required",
                    "Enter the punctuated text.",
                )
                return

            if (
                self.includes_translation()
                and not self.translation_text_edit.toPlainText().strip()
            ):
                QMessageBox.warning(
                    self,
                    "Translation Required",
                    "Enter the translation.",
                )
                return

            if (
                self.includes_translation()
                and not self.translation_language()
            ):
                QMessageBox.warning(
                    self,
                    "Translation Language Required",
                    "Enter the translation language.",
                )
                return
    
        else:

            if not self.kanripo_code_edit.text().strip():
                QMessageBox.warning(
                    self,
                    "Kanripo Code Required",
                    "Enter a Kanripo code.",
                )
                return

        self.accept()

    # --------------------------------------------------------------------------------------

    def source_type(self):
        return (
            "raw"
            if self.source_combo.currentIndex() == 0
            else "kanripo"
        )


    def original_title(self):
        return self.original_title_edit.text().strip() or None


    def user_text(self):
        return self.unpunctuated_text_edit.toPlainText()


    def divider(self):

        value = self.unpunctuated_divider_edit.text()

        return (
            value
            .replace(r"\n", "\n")
            .replace(r"\t", "\t")
        )


    def keep_divider(self):
        return (
            self
            .unpunctuated_keep_divider_checkbox
            .isChecked()
        )


    def divider_is_whole_line(self):
        return (
            self
            .unpunctuated_whole_line_checkbox
            .isChecked()
        )


    def includes_unpunctuated(self):
        return self.include_unpunctuated_checkbox.isChecked()


    def includes_punctuated(self):
        return self.include_punctuated_checkbox.isChecked()


    def includes_translation(self):
        return self.include_translation_checkbox.isChecked()


    def segments_are_paragraphs(self):
        return self.segments_are_paragraphs_checkbox.isChecked()


    def punctuated_text(self):
        return self.punctuated_text_edit.toPlainText()


    def translation_text(self):
        return self.translation_text_edit.toPlainText()


    def translated_title(self):
        return self.translated_title_edit.text().strip() or None


    def translation_language(self):
        return self.translation_language_edit.text().strip()


    def kanripo_code(self):
        return self.kanripo_code_edit.text().strip()


    def glosses_on(self):
        return self.glosses_checkbox.isChecked()


    def punctuated_divider(self):

        value = self.punctuated_divider_edit.text()

        return (
            value
            .replace(r"\n", "\n")
            .replace(r"\t", "\t")
        )


    def punctuated_keep_divider(self):
        return (
            self
            .punctuated_keep_divider_checkbox
            .isChecked()
        )


    def punctuated_divider_is_whole_line(self):
        return (
            self
            .punctuated_whole_line_checkbox
            .isChecked()
        )


    def translation_divider(self):

        value = self.translation_divider_edit.text()

        return (
            value
            .replace(r"\n", "\n")
            .replace(r"\t", "\t")
        )


    def translation_keep_divider(self):
        return (
            self
            .translation_keep_divider_checkbox
            .isChecked()
        )


    def translation_divider_is_whole_line(self):
        return (
            self
            .translation_whole_line_checkbox
            .isChecked()
        )
