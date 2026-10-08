# ------------------------------------------------------------------------------------------
# main_window
# ------------------------------------------------------------------------------------------

from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QStackedWidget,
    QTabWidget,
    QTableWidget,
    QVBoxLayout,
    QWidget,
    QScrollArea,
    QFormLayout,
    QLineEdit,
    QCheckBox,
    QComboBox,
    QSpinBox,
    QMessageBox,
    QSlider,
    QDialog,
    QFileDialog,
    QTableWidgetItem,
    QInputDialog,
)
from PySide6.QtCore import Qt, QSize, QThread
from PySide6.QtGui import QPixmap, QPainter, QFont, QColor, QIcon

from pathlib import Path
import keyring

from ..workflow_orchestrator import WorkflowOrchestrator
from ..settings_manager import load_settings, save_settings
from ..segmented_text import SegmentedText
from ..raw_text import RawText
from ..kanripo_text import KanripoText
from ..llm_lists import (
    GPT_MODELS,
    GEMINI_MODELS,
    is_open_ai,
    is_google,
)
from ..glossary_dictate import (
    load_glossary,
    unite_glossaries,
    intersect_glossaries,
    differentiate_glossaries,
)
from ..yiding_file_io import (
    save_project,
    load_project,
    apply_project_to_text,
    export_glossary_csv,
    export_log_txt,
    export_text_txt,
    export_text_docx,
    finish_run,
)
from .new_project_dialog import NewProjectDialog
from .transform_settings_dialog import (
    TransformSettingsDialog
)
from .transform_progress_dialog import (
    TransformProgressDialog,
    TransformWorker,
)
from .settings_widgets import (
    PunctuationSettingsWidget,
    TranslationSettingsWidget,
    ExtractionSettingsWidget,
)
        
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.settings = load_settings()
        
        self.text = None
        self.orchestrator = None
        self.project_file = None
        
        self.settings_dirty = False
        self.settings_save_buttons = []
        self.api_keys_to_delete = set()

        self.transform_thread = None
        self.transform_worker = None
        self.transform_progress_dialog = None

        self.setWindowTitle("Yiding 譯鼎")
        self.resize(1200, 750)

        self.create_workspace()

    # ---------------------------------------------------------
    # WORKSPACE
    # ---------------------------------------------------------

    def create_workspace(self):

        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)

        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)

        # Left side
        left_column = self.create_left_column()

        # ---------------------------------------------------------
        # MAIN CONTENT PAGES
        # ---------------------------------------------------------

        self.main_stack = QStackedWidget()

        # Normal text workspace
        self.text_workspace = self.create_text_workspace()

        # Settings workspaces
        self.api_services_workspace = self.create_api_services_page()
        self.punctuation_workspace = self.create_punctuation_page()
        self.translation_workspace = self.create_translation_page()
        self.term_extraction_workspace = self.create_term_extraction_page()
        self.glossary_extraction_workspace = self.create_glossary_extraction_page()

        self.settings_pages = [
            self.api_services_workspace,
            self.punctuation_workspace,
            self.translation_workspace,
            self.term_extraction_workspace,
            self.glossary_extraction_workspace,
        ]

        # Add all workspaces to the main stack
        self.main_stack.addWidget(self.text_workspace)
        self.main_stack.addWidget(self.api_services_workspace)
        self.main_stack.addWidget(self.punctuation_workspace)
        self.main_stack.addWidget(self.translation_workspace)
        self.main_stack.addWidget(self.term_extraction_workspace)
        self.main_stack.addWidget(self.glossary_extraction_workspace)

        # Text workspace shown by default
        self.main_stack.setCurrentWidget(self.text_workspace)

        main_layout.addWidget(left_column)
        main_layout.addWidget(self.main_stack, 1)

        self.setCentralWidget(main_widget)
        
    # ---------------------------------------------------------
    # TEXT WORKSPACE
    # ---------------------------------------------------------

    def create_text_workspace(self):

        workspace = QWidget()
        layout = QVBoxLayout(workspace)

        layout.setContentsMargins(0, 15, 20, 15)
        layout.setSpacing(8)

        # ---------------------------------------------------------
        # WORKSPACE HEADER
        # ---------------------------------------------------------

        self.workspace_title = QLabel("")

        self.workspace_title.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #555555;
            }
        """)

        self.workspace_title.hide()

        layout.addWidget(
            self.workspace_title
        )

        # ---------------------------------------------------------
        # WORKSPACE STACK
        # ---------------------------------------------------------

        self.workspace_stack = QStackedWidget()

        # =========================================================
        # EMPTY WORKSPACE
        # =========================================================

        self.empty_workspace = QWidget()

        empty_layout = QVBoxLayout(
            self.empty_workspace
        )

        empty_layout.setContentsMargins(
            0, 0, 0, 0
        )

        empty_layout.addStretch()

        empty_logo = QLabel()
        empty_logo.setAlignment(Qt.AlignCenter)

        logo_path = (
            Path(__file__).parent
            / "assets"
            / "logo_half_thinnest_shortened.png"
        )

        pixmap = QPixmap(
            str(logo_path)
        )

        if not pixmap.isNull():

            empty_logo.setPixmap(
                pixmap.scaledToWidth(
                    260,
                    Qt.SmoothTransformation
                )
            )

        empty_layout.addWidget(
            empty_logo,
            0,
            Qt.AlignCenter
        )

        empty_layout.addStretch()

        # =========================================================
        # TEXT TABS
        # =========================================================

        self.text_tabs = QTabWidget()

        self.text_tabs.setTabPosition(
            QTabWidget.South
        )

        # ---------------------------------------------------------
        # TEXT WIDGETS
        # ---------------------------------------------------------

        self.unpunctuated_editor = QPlainTextEdit()
        self.unpunctuated_editor.setReadOnly(True)

        self.punctuated_editor = QPlainTextEdit()
        self.punctuated_editor.setReadOnly(True)

        self.translated_editor = QPlainTextEdit()
        self.translated_editor.setReadOnly(True)

        self.text_display_font = QFont(
            "PMingLiU",
            14
        )
        
        self.unpunctuated_editor.setFont(
            self.text_display_font
        )

        self.punctuated_editor.setFont(
            self.text_display_font
        )

        self.translated_editor.setFont(
            self.text_display_font
        )

        # ---------------------------------------------------------
        # COMPARISON TABLES
        # ---------------------------------------------------------

        self.unpunctuated_punctuated_table = (
            self.create_comparison_table(
                "Unpunctuated Text",
                "Punctuated Text"
            )
        )

        self.punctuated_translation_table = (
            self.create_comparison_table(
                "Punctuated Text",
                "Translation"
            )
        )

        # ---------------------------------------------------------
        # GLOSSARY TABLES
        # ---------------------------------------------------------

        self.translation_glossary_table = (
            self.create_glossary_table()
        )
        
        self.new_glossary_table = (
            self.create_glossary_table()
        )

        self.extracted_terms_table = (
            self.create_glossary_table()
        )

        self.extracted_glossary_table = (
            self.create_glossary_table()
        )

        # ---------------------------------------------------------
        # TAB CHANGE
        # ---------------------------------------------------------

        self.text_tabs.currentChanged.connect(
            self.change_text_tab
        )

        # ---------------------------------------------------------
        # TAB APPEARANCE
        # ---------------------------------------------------------

        self.text_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #d6d2c8;
                background: white;
            }

            QTabBar::tab {
                color: #681708;
                background: #e9e6df;
                border: 1px solid #c9c5bc;
                border-top: none;

                padding: 8px 24px;
                margin-right: 2px;
            }

            QTabBar::tab:hover {
                background: #f3f1ec;
            }

            QTabBar::tab:selected {
                background: white;
                font-weight: bold;
                border-top: 2px solid #681708;
            }
        """)

        # ---------------------------------------------------------
        # ADD STACK PAGES
        # ---------------------------------------------------------

        self.workspace_stack.addWidget(
            self.empty_workspace
        )

        self.workspace_stack.addWidget(
            self.text_tabs
        )

        self.workspace_stack.setCurrentWidget(
            self.empty_workspace
        )

        layout.addWidget(
            self.workspace_stack,
            1
        )

        return workspace


    # =========================================================
    # SETTINGS PAGE
    # =========================================================

    def create_settings_page(self):

        page = QWidget()
        layout = QVBoxLayout(page)

        layout.setContentsMargins(9, 9, 9, 9)
        layout.setSpacing(8)

        # Back
        back_button = self.create_back_button()

        back_button.clicked.connect(
            lambda: self.leave_settings()
        )

        layout.addWidget(back_button)
        layout.addSpacing(10)

        # SETTINGS heading
        title = self.create_sidebar_heading("SETTINGS")

        layout.addWidget(title)
        layout.addSpacing(10)

        # Options
        api_button = QPushButton("API Access")
        punctuation_button = QPushButton("Punctuation")
        translation_button = QPushButton("Translation")
        term_extraction_button = QPushButton("Term Extraction")
        glossary_extraction_button = QPushButton("Glossary Extraction")

        layout.addWidget(api_button)

        layout.addSpacing(5)
        layout.addWidget(self.create_sidebar_separator())
        layout.addSpacing(5)

        layout.addWidget(punctuation_button)
        layout.addWidget(translation_button)

        layout.addSpacing(5)
        layout.addWidget(self.create_sidebar_separator())
        layout.addSpacing(5)

        layout.addWidget(term_extraction_button)
        layout.addWidget(glossary_extraction_button)

        layout.addStretch()

        # Main workspace navigation
        api_button.clicked.connect(
            lambda: self.switch_settings_page(
                self.api_services_workspace
            )
        )

        punctuation_button.clicked.connect(
            lambda: self.switch_settings_page(
                self.punctuation_workspace
            )
        )

        translation_button.clicked.connect(
            lambda: self.switch_settings_page(
                self.translation_workspace
            )
        )

        term_extraction_button.clicked.connect(
            lambda: self.switch_settings_page(
                self.term_extraction_workspace
            )
        )

        glossary_extraction_button.clicked.connect(
            lambda: self.switch_settings_page(
                self.glossary_extraction_workspace
            )
        )

        return page

    # =========================================================
    # SETTINGS PAGE: API 
    # =========================================================

    def create_api_services_page(self):

        page = QWidget()
        layout = QVBoxLayout(page)

        layout.setContentsMargins(15, 15, 15, 15)

        # Fixed vertical position.
        # Change 110 if you ever want the whole section higher/lower.
        layout.addSpacing(110)

        title = QLabel("API ACCESS")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: bold;
                color: #555555;
            }
        """)

        layout.addWidget(title)
        layout.addSpacing(20)

        # Existing API keys
        self.api_keys_layout = QVBoxLayout()
        self.api_keys_layout.setSpacing(8)

        layout.addLayout(self.api_keys_layout)

        self.load_api_keys()

        # Add button comes AFTER the keys
        layout.addSpacing(15)

        add_key_button = QPushButton("Add New Key")
        add_key_button.setFixedWidth(180)

        add_key_button.clicked.connect(
            lambda: self.add_api_key_row()
        )

        layout.addWidget(
            add_key_button,
            0,
            Qt.AlignHCenter
        )

        layout.addStretch()

        self.add_settings_save_button(layout)

        return page


    # =========================================================
    # SETTINGS PAGE: PUNCTUATION SETTINGS
    # =========================================================

    def create_punctuation_page(self):

        page = QWidget()
        layout = QVBoxLayout(page)

        layout.setContentsMargins(
            15, 15, 15, 15
        )

        layout.addWidget(
            self.create_settings_heading(
                "PUNCTUATION SETTINGS"
            )
        )

        self.punctuation_settings_widget = (
            PunctuationSettingsWidget(
                self,
                self.settings[
                    "punctuation"
                ]
            )
        )

        layout.addWidget(
            self.punctuation_settings_widget,
            1
        )

        self.add_settings_save_button(
            layout
        )

        self.watch_settings_page(
            page
        )

        return page


    # =========================================================
    # SETTINGS PAGE: TRANSLATION
    # =========================================================

    def create_translation_page(self):

        page = QWidget()
        layout = QVBoxLayout(page)

        layout.setContentsMargins(
            15, 15, 15, 15
        )

        layout.addWidget(
            self.create_settings_heading(
                "TRANSLATION SETTINGS"
            )
        )

        self.translation_settings_widget = (
            TranslationSettingsWidget(
                self,
                self.settings[
                    "translation"
                ]
            )
        )

        layout.addWidget(
            self.translation_settings_widget,
            1
        )

        self.add_settings_save_button(
            layout
        )

        self.watch_settings_page(
            page
        )

        return page


    # =========================================================
    # SETTINGS PAGE: TERM EXTRACTION
    # =========================================================

    def create_term_extraction_page(self):

        page = QWidget()
        layout = QVBoxLayout(page)

        layout.setContentsMargins(
            15, 15, 15, 15
        )

        layout.addWidget(
            self.create_settings_heading(
                "TERM EXTRACTION SETTINGS"
            )
        )

        self.term_extraction_settings_widget = (
            ExtractionSettingsWidget(
                self,
                self.settings[
                    "term_extraction"
                ]
            )
        )

        layout.addWidget(
            self.term_extraction_settings_widget,
            1
        )

        self.add_settings_save_button(
            layout
        )

        self.watch_settings_page(
            page
        )

        return page


    # =========================================================
    # SETTINGS PAGE: GLOSSARY EXTRACTION
    # =========================================================

    def create_glossary_extraction_page(self):

        page = QWidget()
        layout = QVBoxLayout(page)

        layout.setContentsMargins(
            15, 15, 15, 15
        )

        layout.addWidget(
            self.create_settings_heading(
                "GLOSSARY EXTRACTION SETTINGS"
            )
        )

        self.glossary_extraction_settings_widget = (
            ExtractionSettingsWidget(
                self,
                self.settings[
                    "glossary_extraction"
                ]
            )
        )

        layout.addWidget(
            self.glossary_extraction_settings_widget,
            1
        )

        self.add_settings_save_button(
            layout
        )

        self.watch_settings_page(
            page
        )

        return page


    # ---------------------------------------------------------
    # CREATE TABLE
    # ---------------------------------------------------------

    def create_readonly_table(
        self,
        headers
    ):

        table = QTableWidget()

        table.setFont(
            self.text_display_font
        )

        table.setRowCount(0)
        table.setColumnCount(
            len(headers)
        )

        table.setHorizontalHeaderLabels(
            headers
        )

        table.setShowGrid(False)
        table.setFrameShape(
            QFrame.NoFrame
        )

        table.setStyleSheet("""
            QTableWidget {
                border: none;
                background-color: white;
            }

            QTableWidget::item {
                border: none;
                padding: 4px;
            }

            QHeaderView::section {
                background-color: #eeeae1;
                border: none;
                padding: 6px;
                font-weight: bold;
            }
        """)

        table.verticalHeader().setVisible(
            False
        )

        table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        table.setSelectionMode(
            QAbstractItemView.NoSelection
        )

        table.setFocusPolicy(
            Qt.NoFocus
        )

        table.setWordWrap(True)

        table.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )

        return table


    def create_comparison_table(
        self,
        left_title,
        right_title
    ):

        table = self.create_readonly_table([
            left_title,
            right_title,
        ])

        table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        return table


    def create_glossary_table(self):

        table = self.create_readonly_table([
            "Chinese",
            "Pinyin",
            "Translations",
        ])

        header = table.horizontalHeader()

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeToContents
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeToContents
        )

        header.setSectionResizeMode(
            2,
            QHeaderView.Stretch
        )

        return table


    def format_labeled_text(
        self,
        segments,
        labels
    ):

        parts = []

        for i, segment in enumerate(segments):

            if i < len(labels) and labels[i]:

                parts.append(
                    f"{labels[i]}\n{segment}"
                )

            else:

                parts.append(
                    segment
                )

        return "\n".join(parts)


    def populate_comparison_table(
        self,
        table,
        left_segments,
        right_segments,
        labels
    ):

        table.clearContents()

        row_count = max(
            len(left_segments),
            len(right_segments)
        )

        table.setRowCount(
            row_count
        )

        for i in range(row_count):

            if i < len(left_segments):

                if i < len(labels) and labels[i]:

                    left_text = (
                        f"{labels[i]}\n"
                        f"{left_segments[i]}"
                    )
                else:
                    left_text = left_segments[i]

                left_item = QTableWidgetItem(
                    left_text
                )

                left_item.setTextAlignment(
                    Qt.AlignJustify | Qt.AlignTop
                )

                table.setItem(
                    i,
                    0,
                    left_item
                )

            if i < len(right_segments):

                if i < len(labels) and labels[i]:

                    right_text = (
                        f"{labels[i]}\n"
                        f"{right_segments[i]}"
                    )
                else:
                    right_text = right_segments[i]

                right_item = QTableWidgetItem(
                    right_text
                )

                right_item.setTextAlignment(
                    Qt.AlignJustify | Qt.AlignTop
                )

                table.setItem(
                    i,
                    1,
                    right_item
                )


    def populate_glossary_table(
        self,
        table,
        glossary
    ):

        table.clearContents()

        table.setRowCount(
            len(glossary)
        )

        for row, (
            chinese,
            value
        ) in enumerate(
            glossary.items()
        ):

            pinyin = (
                value[0]
                if value
                else ""
            )

            translations = (
                value[1]
                if len(value) > 1
                else []
            )

            chinese_item = QTableWidgetItem(
                str(chinese)
            )

            chinese_item.setTextAlignment(
                Qt.AlignJustify | Qt.AlignTop
            )

            table.setItem(
                row,
                0,
                chinese_item
            )


            pinyin_item = QTableWidgetItem(
                str(pinyin)
            )

            pinyin_item.setTextAlignment(
                Qt.AlignJustify | Qt.AlignTop
            )

            table.setItem(
                row,
                1,
                pinyin_item
            )


            translations_item = QTableWidgetItem(
                ", ".join(
                    str(translation)
                    for translation
                    in translations
                )
            )

            translations_item.setTextAlignment(
                Qt.AlignJustify | Qt.AlignTop
            )

            table.setItem(
                row,
                2,
                translations_item
            )

        
    # ---------------------------------------------------------
    # TEXT TAB
    # ---------------------------------------------------------

    def change_text_tab(self, index):

        if index < 0:
            return

        title = (
            self.text_tabs
            .tabBar()
            .tabData(index)
        )

        if title:

            self.workspace_title.setText(
                title
            )

        
    # ---------------------------------------------------------
    # SUBMENU PAGE
    # ---------------------------------------------------------
    
    def create_submenu_page(self, title, options, back_action=None):

        page = QWidget()
        layout = QVBoxLayout(page)

        # Back button
        back_button = self.create_back_button()

        if back_action is None:
            back_button.clicked.connect(
                lambda: self.sidebar_stack.setCurrentIndex(0)
            )
        else:
            back_button.clicked.connect(back_action)

        section_title = self.create_sidebar_heading(
            title.upper()
        )

        layout.addWidget(back_button)
        layout.addSpacing(15)
        layout.addWidget(section_title)
        layout.addSpacing(10)

        for option in options:
            button = QPushButton(option)
            layout.addWidget(button)

        layout.addStretch()

        return page

    # ---------------------------------------------------------
    # FILE PAGE
    # ---------------------------------------------------------

    def create_file_page(self):

        page = QWidget()
        layout = QVBoxLayout(page)

        back_button = self.create_back_button()

        back_button.clicked.connect(
            lambda:
                self.sidebar_stack.setCurrentIndex(0)
        )

        title = self.create_sidebar_heading(
            "FILE"
        )

        # ---------------------------------------------------------
        # PROJECT
        # ---------------------------------------------------------

        new_button = QPushButton(
            "New"
        )

        open_button = QPushButton(
            "Open"
        )

        new_button.clicked.connect(
            self.create_new_project
        )

        open_button.clicked.connect(
            self.open_project
        )

        # ---------------------------------------------------------
        # EXPORT
        # ---------------------------------------------------------

        self.export_docx_button = QPushButton(
            "DOCX"
        )

        self.export_txt_button = QPushButton(
            "TXT"
        )

        self.export_log_button = QPushButton(
            "Log"
        )

        self.export_docx_button.clicked.connect(
            self.export_docx
        )

        self.export_txt_button.clicked.connect(
            self.export_txt
        )

        self.export_log_button.clicked.connect(
            self.export_log
        )

        self.set_export_buttons_enabled(
            self.text is not None
        )

        # ---------------------------------------------------------
        # LAYOUT
        # ---------------------------------------------------------

        layout.addWidget(back_button)
        layout.addSpacing(15)

        layout.addWidget(title)
        layout.addSpacing(10)

        layout.addWidget(new_button)
        layout.addWidget(open_button)

        layout.addSpacing(8)

        layout.addWidget(
            self.create_sidebar_heading(
                "EXPORT"
            )
        )

        layout.addSpacing(3)

        layout.addWidget(
            self.export_docx_button
        )

        layout.addWidget(
            self.export_txt_button
        )

        layout.addWidget(
            self.export_log_button
        )

        layout.addStretch()

        return page


    def set_export_buttons_enabled(
        self,
        enabled
    ):

        self.export_docx_button.setEnabled(
            enabled
        )

        self.export_txt_button.setEnabled(
            enabled
        )

        self.export_log_button.setEnabled(
            enabled
        )


    # ---------------------------------------------------------

    def block_project_change_during_transform(
        self
    ):

        if self.transform_thread is None:
            return False

        QMessageBox.information(
            self,
            "Transformation Running",
            "The current project cannot be replaced "
            "while a transformation is in progress."
        )

        if (
            self.transform_progress_dialog
            is not None
        ):
            self.transform_progress_dialog.show()
            self.transform_progress_dialog.raise_()
            self.transform_progress_dialog.activateWindow()

        return True


    # ---------------------------------------------------------
    # NEW PROJECT
    # ---------------------------------------------------------

    def create_new_project(self):

        if self.block_project_change_during_transform():
            return

        dialog = NewProjectDialog(self)

        while True:

            if dialog.exec() != QDialog.DialogCode.Accepted:
                return

            # ---------------------------------------------------------
            # CREATE TEXT OBJECT FIRST
            # ---------------------------------------------------------

            try:

                if dialog.source_type() == "raw":

                    text = RawText(
                        unpunctuated_text=(
                            dialog.user_text()
                            if dialog.includes_unpunctuated()
                            else None
                        ),
                        unpunctuated_divider=(
                            dialog.divider()
                            if dialog.includes_unpunctuated()
                            else None
                        ),
                        unpunctuated_keep_divider=(
                            dialog.keep_divider()
                            if dialog.includes_unpunctuated()
                            else False
                        ),
                        unpunctuated_divider_is_whole_line=(
                            dialog.divider_is_whole_line()
                            if dialog.includes_unpunctuated()
                            else False
                        ),

                        punctuated_text=(
                            dialog.punctuated_text()
                            if dialog.includes_punctuated()
                            else None
                        ),
                        punctuated_divider=(
                            dialog.punctuated_divider()
                            if dialog.includes_punctuated()
                            else None
                        ),
                        punctuated_keep_divider=(
                            dialog.punctuated_keep_divider()
                            if dialog.includes_punctuated()
                            else False
                        ),
                        punctuated_divider_is_whole_line=(
                            dialog.punctuated_divider_is_whole_line()
                            if dialog.includes_punctuated()
                            else False
                        ),

                        translated_text=(
                            dialog.translation_text()
                            if dialog.includes_translation()
                            else None
                        ),
                        translation_divider=(
                            dialog.translation_divider()
                            if dialog.includes_translation()
                            else None
                        ),
                        translation_keep_divider=(
                            dialog.translation_keep_divider()
                            if dialog.includes_translation()
                            else False
                        ),
                        translation_divider_is_whole_line=(
                            dialog.translation_divider_is_whole_line()
                            if dialog.includes_translation()
                            else False
                        ),

                        original_title=dialog.original_title(),

                        translated_title=(
                            dialog.translated_title()
                            if dialog.includes_translation()
                            else None
                        ),

                        translation_language=(
                            dialog.translation_language()
                            if dialog.includes_translation()
                            else None
                        ),

                        structured=(
                            dialog.includes_unpunctuated()
                            and dialog.segments_are_paragraphs()
                        ),
                    )

                else:

                    text = KanripoText(
                        dialog.kanripo_code(),
                        glosses_on=dialog.glosses_on(),
                    )

            except Exception as exc:

                QMessageBox.warning(
                    self,
                    "Could Not Create Project",
                    str(exc),
                )

                # Same dialog opens again.
                # All entered text/settings remain.
                continue

            break

        # ---------------------------------------------------------
        # DEFAULT FILE NAME
        # ---------------------------------------------------------

        if dialog.source_type() == "raw":
            default_name = (
                dialog.original_title()
                or "Untitled"
            )
        else:
            default_name = dialog.kanripo_code()

        # ---------------------------------------------------------
        # ASK WHERE TO SAVE
        # ---------------------------------------------------------

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Create Yiding Project",
            f"{default_name}.yiding",
            "Yiding Project (*.yiding)",
        )

        if not filename:
            return

        if not filename.lower().endswith(".yiding"):
            filename += ".yiding"

        # ---------------------------------------------------------
        # SAVE PROJECT
        # ---------------------------------------------------------

        try:

            saved_path = save_project(
                filename,
                text,
                self.settings,
            )

        except Exception as exc:

            QMessageBox.critical(
                self,
                "Could Not Save Project",
                str(exc),
            )

            return

        # ---------------------------------------------------------
        # OPEN NEW PROJECT IN GUI
        # ---------------------------------------------------------

        self.text = text
        self.set_export_buttons_enabled(True)
        self.project_file = str(saved_path)
        
        self.refresh_transform_buttons()
        self.refresh_glossary_buttons()
        self.refresh_text_workspace()

        self.sidebar_stack.setCurrentIndex(0)

        self.main_stack.setCurrentWidget(
            self.text_workspace
        )

        self.setWindowTitle(
            f"Yiding 譯鼎 — {Path(self.project_file).stem}"
        )
    
    
    # ---------------------------------------------------------
    # OPEN PROJECT
    # ---------------------------------------------------------

    def open_project(self):

        if self.block_project_change_during_transform():
            return

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open Yiding Project",
            "",
            "Yiding Project (*.yiding)",
        )

        if not filename:
            return

        try:

            project = load_project(
                filename
            )

            # -------------------------------------------------
            # CREATE EMPTY TEXT OBJECT OF THE CORRECT TYPE
            # -------------------------------------------------

            if project["text_type"] == "raw":

                text = RawText()

            elif project["text_type"] == "kanripo":

                # Do NOT call KanripoText.__init__ here,
                # because that would download the source again.
                text = KanripoText.__new__(
                    KanripoText
                )

                SegmentedText.__init__(
                    text
                )

            else:

                raise ValueError(
                    "Unknown Yiding text type."
                )

            # -------------------------------------------------
            # RESTORE PROJECT DATA
            # -------------------------------------------------

            apply_project_to_text(
                project,
                text
            )

        except Exception as exc:

            QMessageBox.critical(
                self,
                "Could Not Open Project",
                str(exc),
            )

            return

        # -------------------------------------------------
        # MAKE THIS THE CURRENT PROJECT
        # -------------------------------------------------

        self.text = text
        self.set_export_buttons_enabled(True)
        self.project_file = str(
            Path(filename).resolve()
        )
        self.refresh_transform_buttons()
        self.refresh_glossary_buttons()

        # A newly opened project should not keep API/workflow
        # objects belonging to a previously open project.
        self.orchestrator = None

        # -------------------------------------------------
        # REFRESH GUI
        # -------------------------------------------------

        self.refresh_text_workspace()

        self.sidebar_stack.setCurrentIndex(0)

        self.main_stack.setCurrentWidget(
            self.text_workspace
        )

        self.setWindowTitle(
            f"Yiding 譯鼎 — {Path(self.project_file).stem}"
        )


    # ---------------------------------------------------------
    # EXPORT AS DOCX
    # ---------------------------------------------------------

    def export_docx(self):

        if (
            self.text is None
            or self.project_file is None
        ):
            return

        # ---------------------------------------------------------
        # LOAD CURRENT PROJECT
        # ---------------------------------------------------------

        try:

            project = load_project(
                self.project_file
            )

        except Exception as exc:

            QMessageBox.critical(
                self,
                "Could Not Export DOCX",
                str(exc),
            )

            return

        text_data = project["text"]

        unpunctuated = (
            text_data["unpunctuated_segments"]
            or text_data["segments"]
        )

        punctuated = (
            text_data["punctuated_segments"]
        )

        translated = (
            text_data["translated_segments"]
        )

        # ---------------------------------------------------------
        # AVAILABLE EXPORTS
        # ---------------------------------------------------------

        choices = []

        if unpunctuated:

            choices.append(
                (
                    "Unpunctuated Text",
                    "unpunctuated",
                )
            )

        if punctuated:

            choices.append(
                (
                    "Punctuated Text",
                    "punctuated",
                )
            )

        if translated:

            choices.append(
                (
                    "Translation",
                    "translation",
                )
            )

        if (
            punctuated
            and translated
            and len(punctuated)
            == len(translated)
        ):

            choices.append(
                (
                    "Punctuated Text + Translation",
                    "punctuated_translation",
                )
            )

        if not choices:

            QMessageBox.information(
                self,
                "Export as DOCX",
                "There is no text to export.",
            )

            return

        # ---------------------------------------------------------
        # ASK WHAT TO EXPORT
        # ---------------------------------------------------------

        display_choices = [
            name
            for name, _ in choices
        ]

        selected, accepted = (
            QInputDialog.getItem(
                self,
                "Export as DOCX",
                "Text to export:",
                display_choices,
                0,
                False,
            )
        )

        if not accepted:
            return

        export_kind = dict(choices)[
            selected
        ]

        # ---------------------------------------------------------
        # DEFAULT FILE NAME
        # ---------------------------------------------------------

        project_name = Path(
            self.project_file
        ).stem

        suffixes = {
            "unpunctuated":
                "_unpunctuated",

            "punctuated":
                "_punctuated",

            "translation":
                "_translation",

            "punctuated_translation":
                "",
        }

        default_name = (
            project_name
            + suffixes[export_kind]
            + ".docx"
        )

        # ---------------------------------------------------------
        # ASK WHERE TO SAVE
        # ---------------------------------------------------------

        filename, _ = (
            QFileDialog.getSaveFileName(
                self,
                "Export as DOCX",
                default_name,
                "Word Document (*.docx)",
            )
        )

        if not filename:
            return

        if not filename.lower().endswith(
            ".docx"
        ):
            filename += ".docx"

        # ---------------------------------------------------------
        # EXPORT
        # ---------------------------------------------------------

        try:

            export_text_docx(
                project,
                export_kind,
                filename,
            )

        except Exception as exc:

            QMessageBox.critical(
                self,
                "Could Not Export DOCX",
                str(exc),
            )

        
    # ---------------------------------------------------------
    # EXPORT AS TXT
    # ---------------------------------------------------------

    def export_txt(self):

        if (
            self.text is None
            or self.project_file is None
        ):
            return

        # ---------------------------------------------------------
        # LOAD CURRENT PROJECT DATA
        # ---------------------------------------------------------

        try:

            project = load_project(
                self.project_file
            )

        except Exception as exc:

            QMessageBox.critical(
                self,
                "Could Not Export TXT",
                str(exc),
            )

            return

        text_data = project["text"]

        # ---------------------------------------------------------
        # AVAILABLE TEXT TYPES
        # ---------------------------------------------------------

        choices = []

        unpunctuated = (
            text_data["unpunctuated_segments"]
            or text_data["segments"]
        )

        if unpunctuated:

            choices.append(
                (
                    "Unpunctuated Text",
                    "unpunctuated",
                )
            )

        if text_data["punctuated_segments"]:

            choices.append(
                (
                    "Punctuated Text",
                    "punctuated",
                )
            )

        if text_data["translated_segments"]:

            choices.append(
                (
                    "Translation",
                    "translation",
                )
            )

        if not choices:

            QMessageBox.information(
                self,
                "Export as TXT",
                "There is no text to export.",
            )

            return

        # ---------------------------------------------------------
        # ASK WHICH TEXT
        # ---------------------------------------------------------

        display_choices = [
            name
            for name, _ in choices
        ]

        selected, accepted = (
            QInputDialog.getItem(
                self,
                "Export as TXT",
                "Text to export:",
                display_choices,
                0,
                False,
            )
        )

        if not accepted:
            return

        text_kind = dict(choices)[
            selected
        ]

        # ---------------------------------------------------------
        # ASK WHERE TO SAVE
        # ---------------------------------------------------------

        project_name = Path(
            self.project_file
        ).stem

        suffix = {
            "unpunctuated":
                "unpunctuated",

            "punctuated":
                "punctuated",

            "translation":
                "translation",
        }[text_kind]

        filename, _ = (
            QFileDialog.getSaveFileName(
                self,
                "Export as TXT",
                f"{project_name}_{suffix}.txt",
                "Text File (*.txt)",
            )
        )

        if not filename:
            return

        if not filename.lower().endswith(
            ".txt"
        ):
            filename += ".txt"

        # ---------------------------------------------------------
        # EXPORT
        # ---------------------------------------------------------

        try:

            export_text_txt(
                project,
                text_kind,
                filename,
            )

        except Exception as exc:

            QMessageBox.critical(
                self,
                "Could Not Export TXT",
                str(exc),
            )

        
    # ---------------------------------------------------------
    # EXPORT GLOSSARY
    # ---------------------------------------------------------

    def _export_glossary(
        self,
        glossary,
        title,
        suffix
    ):

        if not glossary:
            return

        project_name = (
            Path(self.project_file).stem
            if self.project_file
            else "Yiding"
        )

        filename, _ = QFileDialog.getSaveFileName(
            self,
            title,
            f"{project_name}_{suffix}.csv",
            "CSV File (*.csv)",
        )

        if not filename:
            return

        if not filename.lower().endswith(
            ".csv"
        ):
            filename += ".csv"

        try:

            export_glossary_csv(
                glossary,
                filename,
            )

        except Exception as exc:

            QMessageBox.critical(
                self,
                f"Could Not {title}",
                str(exc),
            )


    def export_glossary(self):

        if self.text is None:
            return

        choices = []

        if self.text.translation_glossary:
            choices.append(
                (
                    "Translation Glossary",
                    self.text.translation_glossary,
                    "translation_glossary",
                )
            )

        if self.text.new_glossary:
            choices.append(
                (
                    "New Glossary",
                    self.text.new_glossary,
                    "new_glossary",
                )
            )

        if self.text.extracted_terms:
            choices.append(
                (
                    "Extracted Terms",
                    self.text.extracted_terms,
                    "extracted_terms",
                )
            )

        if self.text.extracted_glossary:
            choices.append(
                (
                    "Extracted Glossary",
                    self.text.extracted_glossary,
                    "extracted_glossary",
                )
            )

        if not choices:
            return

        names = [
            name
            for name, _, _ in choices
        ]

        selected, accepted = QInputDialog.getItem(
            self,
            "Export Glossary",
            "Glossary to export:",
            names,
            0,
            False,
        )

        if not accepted:
            return

        choice_map = {
            name: (
                glossary,
                suffix,
            )
            for name, glossary, suffix
            in choices
        }

        glossary, suffix = choice_map[selected]

        self._export_glossary(
            glossary,
            f"Export {selected}",
            suffix,
        )
    

    # ---------------------------------------------------------
    # EXPORT LOG
    # ---------------------------------------------------------

    def export_log(self):

        if self.text is None:
            return

        project_name = (
            Path(self.project_file).stem
            if self.project_file
            else "Yiding"
        )

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Log",
            f"{project_name}_log.txt",
            "Text File (*.txt)",
        )

        if not filename:
            return

        if not filename.lower().endswith(".txt"):
            filename += ".txt"

        try:

            export_log_txt(
                self.text.log,
                filename,
            )

        except Exception as exc:

            QMessageBox.critical(
                self,
                "Could Not Export Log",
                str(exc),
            )

        
    # ---------------------------------------------------------
    # TRANSFORM PAGE
    # ---------------------------------------------------------

    def create_transform_page(self):

        page = QWidget()
        layout = QVBoxLayout(page)

        layout.setContentsMargins(9, 9, 9, 9)
        layout.setSpacing(8)

        # ---------------------------------------------------------
        # BACK
        # ---------------------------------------------------------

        back_button = self.create_back_button()

        back_button.clicked.connect(
            lambda:
                self.sidebar_stack.setCurrentIndex(0)
        )

        layout.addWidget(back_button)
        layout.addSpacing(10)

        title = self.create_sidebar_heading(
            "TRANSFORM"
        )

        layout.addWidget(title)
        layout.addSpacing(10)

        # ---------------------------------------------------------
        # TRANSFORM TEXT
        # ---------------------------------------------------------

        self.punctuate_transform_button = QPushButton(
            "Punctuate"
        )

        self.translate_transform_button = QPushButton(
            "Translate"
        )

        self.punctuate_translate_transform_button = (
            QPushButton(
                "Punctuate\n"
                "──────────────── + ────────────────\n"
                "Translate"
            )
        )

        layout.addWidget(
            self.punctuate_transform_button
        )

        layout.addWidget(
            self.translate_transform_button
        )

        layout.addWidget(
            self.punctuate_translate_transform_button
        )

        layout.addSpacing(5)

        layout.addWidget(
            self.create_sidebar_separator()
        )

        layout.addSpacing(5)

        self.resume_transform_button = QPushButton(
            "Resume"
        )

        layout.addWidget(
            self.resume_transform_button
        )

        layout.addStretch()

        self.refresh_transform_buttons()

        self.resume_transform_button.clicked.connect(
            self.request_resume_transform
        )

        self.punctuate_transform_button.clicked.connect(
            lambda:
                self.request_transform(
                    "punctuation"
                )
        )

        self.translate_transform_button.clicked.connect(
            lambda:
                self.request_transform(
                    "translation"
                )
        )

        self.punctuate_translate_transform_button.clicked.connect(
            lambda:
                self.request_transform(
                    "punctuation_translation"
                )
        )

        return page


    def unfinished_transform(self):

        if (
            self.text is None
            or self.project_file is None
        ):
            return None

        try:

            project = load_project(
                self.project_file
            )

        except Exception:
            return None

        workflow = project.get(
            "workflow",
            {}
        )

        if (
            workflow.get("status")
            != "in_progress"
        ):
            return None

        if not workflow.get("operation"):
            return None

        if not workflow.get("active_run_id"):
            return None

        return workflow


    def refresh_transform_buttons(self):

        has_text = (
            self.text is not None
        )

        self.punctuate_transform_button.setEnabled(
            has_text
        )

        self.translate_transform_button.setEnabled(
            has_text
        )

        self.punctuate_translate_transform_button.setEnabled(
            has_text
        )

        unfinished = (
            self.unfinished_transform()
        )

        can_resume = (
            unfinished is not None
            and unfinished["operation"] in (
                "punctuation",
                "translation",
            )
        )

        self.resume_transform_button.setEnabled(
            can_resume
        )
    

    def transform_operation_name(
        self,
        operation
    ):

        names = {
            "punctuation":
                "Punctuation",

            "translation":
                "Translation",

            "term_extraction":
                "Term Extraction",

            "glossary_extraction":
                "Glossary Extraction",
        }

        return names.get(
            operation,
            operation
        )


    def open_transform_menu(
        self,
        page
    ):

        self.refresh_transform_buttons()

        self.sidebar_stack.setCurrentWidget(
            page
        )

        self.main_stack.setCurrentWidget(
            self.text_workspace
        )


    # ---------------------------------------------------------
    # GLOSSARY PAGE
    # ---------------------------------------------------------

    def create_glossary_page(self):

        page = QWidget()
        layout = QVBoxLayout(page)

        layout.setContentsMargins(
            9, 9, 9, 9
        )

        layout.setSpacing(8)

        # ---------------------------------------------------------
        # BACK
        # ---------------------------------------------------------

        back_button = self.create_back_button()

        back_button.clicked.connect(
            lambda:
                self.sidebar_stack.setCurrentIndex(0)
        )

        layout.addWidget(back_button)
        layout.addSpacing(10)

        title = self.create_sidebar_heading(
            "GLOSS. TOOLS"
        )

        layout.addWidget(title)
        layout.addSpacing(10)

        # ---------------------------------------------------------
        # GLOSSARY TOOLS
        # ---------------------------------------------------------

        self.export_glossary_button = QPushButton(
            "Export Glossary"
        )

        self.union_glossaries_button = QPushButton(
            "Merge"
        )

        self.intersection_glossaries_button = QPushButton(
            "Intersect"
        )

        self.difference_glossaries_button = QPushButton(
            "Subtract"
        )

        layout.addWidget(
            self.export_glossary_button
        )

        layout.addSpacing(5)

        layout.addWidget(
            self.create_sidebar_separator()
        )

        layout.addSpacing(5)

        layout.addWidget(
            self.union_glossaries_button
        )

        layout.addWidget(
            self.intersection_glossaries_button
        )

        layout.addWidget(
            self.difference_glossaries_button
        )

        layout.addSpacing(8)

        layout.addWidget(
            self.create_sidebar_heading(
                "LLM TASKS"
            )
        )

        layout.addSpacing(5)

        # ---------------------------------------------------------
        # LLM EXTRACTION
        # ---------------------------------------------------------

        self.extract_terms_glossary_button = (
            QPushButton(
                "Extract Terms"
            )
        )

        self.extract_glossary_glossary_button = (
            QPushButton(
                "Extract Glossary"
            )
        )

        self.resume_extraction_button = (
            QPushButton(
                "Resume Extraction"
            )
        )

        layout.addWidget(
            self.extract_terms_glossary_button
        )

        layout.addWidget(
            self.extract_glossary_glossary_button
        )

        layout.addWidget(
            self.resume_extraction_button
        )

        layout.addStretch()

        # ---------------------------------------------------------
        # EXTRACTION ACTIONS
        # ---------------------------------------------------------

        self.extract_terms_glossary_button.clicked.connect(
            lambda:
                self.request_transform(
                    "term_extraction"
                )
        )

        self.extract_glossary_glossary_button.clicked.connect(
            lambda:
                self.request_transform(
                    "glossary_extraction"
                )
        )

        self.resume_extraction_button.clicked.connect(
            self.request_resume_transform
        )

        # ---------------------------------------------------------
        # EXPORT ACTIONS
        # ---------------------------------------------------------

        self.export_glossary_button.clicked.connect(
            self.export_glossary
        )

        # ---------------------------------------------------------
        # GLOSSARY TOOLS
        # ---------------------------------------------------------

        self.union_glossaries_button.clicked.connect(
            lambda:
                self.open_glossary_operation_dialog(
                    "union"
                )
        )

        self.intersection_glossaries_button.clicked.connect(
            lambda:
                self.open_glossary_operation_dialog(
                    "intersection"
                )
        )

        self.difference_glossaries_button.clicked.connect(
            lambda:
                self.open_glossary_operation_dialog(
                    "difference"
                )
        )

        self.refresh_glossary_buttons()

        return page


    def open_glossary_operation_dialog(
        self,
        operation
    ):

        operations = {
            "union": {
                "title": "Union Glossaries",
                "left_label": "Glossary A:",
                "right_label": "Glossary B:",
                "function": unite_glossaries,
                "export_title": "Export Union",
                "suffix": "union",
            },

            "intersection": {
                "title": "Intersection Glossaries",
                "left_label": "Glossary A:",
                "right_label": "Glossary B:",
                "function": intersect_glossaries,
                "export_title": "Export Intersection",
                "suffix": "intersection",
            },

            "difference": {
                "title": "Difference Glossaries",
                "left_label": "Minuend:",
                "right_label": "Subtrahend:",
                "function": differentiate_glossaries,
                "export_title": "Export Difference",
                "suffix": "difference",
            },
        }

        config = operations[operation]

        dialog = QDialog(self)

        dialog.setWindowTitle(
            config["title"]
        )

        layout = QVBoxLayout(dialog)

        # ---------------------------------------------------------
        # GLOSSARY INPUTS
        # ---------------------------------------------------------

        left_row = QHBoxLayout()
        right_row = QHBoxLayout()

        left_label = QLabel(
            config["left_label"]
        )

        right_label = QLabel(
            config["right_label"]
        )

        left_combo = QComboBox()
        right_combo = QComboBox()

        left_combo.setMinimumWidth(260)
        right_combo.setMinimumWidth(260)

        left_combo.addItem(
            "Select glossary...",
            None,
        )

        right_combo.addItem(
            "Select glossary...",
            None,
        )

        left_browse = QPushButton(
            "Browse CSV..."
        )

        right_browse = QPushButton(
            "Browse CSV..."
        )

        left_row.addWidget(
            left_label
        )

        left_row.addWidget(
            left_combo,
            1,
        )

        left_row.addWidget(
            left_browse
        )

        right_row.addWidget(
            right_label
        )

        right_row.addWidget(
            right_combo,
            1,
        )

        right_row.addWidget(
            right_browse
        )

        # ---------------------------------------------------------
        # OPEN PROJECT GLOSSARIES
        # ---------------------------------------------------------

        if self.text is not None:

            project_glossaries = (
                (
                    "Translation Glossary",
                    self.text.translation_glossary,
                ),
                (
                    "New Glossary",
                    self.text.new_glossary,
                ),                
                (
                    "Extracted Terms",
                    self.text.extracted_terms,
                ),
                (
                    "Extracted Glossary",
                    self.text.extracted_glossary,
                ),
            )

            for name, glossary in project_glossaries:

                if glossary:

                    left_combo.addItem(
                        name,
                        glossary,
                    )

                    right_combo.addItem(
                        name,
                        glossary,
                    )

        # ---------------------------------------------------------
        # BROWSE CSV
        # ---------------------------------------------------------

        def browse_glossary(combo):

            filename, _ = (
                QFileDialog.getOpenFileName(
                    dialog,
                    "Select Glossary",
                    "",
                    "CSV File (*.csv)",
                )
            )

            if not filename:
                return

            try:

                glossary = load_glossary(
                    filename
                )

            except Exception as exc:

                QMessageBox.critical(
                    dialog,
                    "Could Not Load Glossary",
                    str(exc),
                )

                return

            if not glossary:

                QMessageBox.warning(
                    dialog,
                    "Empty Glossary",
                    "The selected CSV contains no glossary entries.",
                )

                return

            combo.addItem(
                f"CSV: {Path(filename).name}",
                glossary,
            )

            combo.setCurrentIndex(
                combo.count() - 1
            )

        left_browse.clicked.connect(
            lambda:
                browse_glossary(
                    left_combo
                )
        )

        right_browse.clicked.connect(
            lambda:
                browse_glossary(
                    right_combo
                )
        )

        # ---------------------------------------------------------
        # EXPORT / CANCEL
        # ---------------------------------------------------------

        buttons_row = QHBoxLayout()

        export_button = QPushButton(
            "Export"
        )

        cancel_button = QPushButton(
            "Cancel"
        )

        export_button.setEnabled(
            False
        )

        buttons_row.addStretch()

        buttons_row.addWidget(
            export_button
        )

        buttons_row.addWidget(
            cancel_button
        )

        def update_export_button():

            export_button.setEnabled(
                left_combo.currentData()
                is not None
                and
                right_combo.currentData()
                is not None
            )

        left_combo.currentIndexChanged.connect(
            update_export_button
        )

        right_combo.currentIndexChanged.connect(
            update_export_button
        )

        # ---------------------------------------------------------
        # PERFORM OPERATION + EXPORT
        # ---------------------------------------------------------

        def export_result():

            left_glossary = (
                left_combo.currentData()
            )

            right_glossary = (
                right_combo.currentData()
            )

            if (
                left_glossary is None
                or right_glossary is None
            ):
                return

            # ---------------------------------------------------------
            # PERFORM GLOSSARY OPERATION
            # ---------------------------------------------------------

            try:

                result = config["function"](
                    left_glossary,
                    right_glossary,
                )

            except Exception as exc:

                QMessageBox.critical(
                    dialog,
                    f"{config['title']} Failed",
                    str(exc),
                )

                return

            # ---------------------------------------------------------
            # EXPORT RESULT
            # ---------------------------------------------------------

            project_name = (
                Path(self.project_file).stem
                if self.project_file
                else "Yiding"
            )

            filename, _ = (
                QFileDialog.getSaveFileName(
                    dialog,
                    config["export_title"],
                    (
                        f"{project_name}_"
                        f"{config['suffix']}.csv"
                    ),
                    "CSV File (*.csv)",
                )
            )

            if not filename:
                return

            if not filename.lower().endswith(
                ".csv"
            ):
                filename += ".csv"

            try:

                export_glossary_csv(
                    result,
                    filename,
                )

            except Exception as exc:

                QMessageBox.critical(
                    dialog,
                    f"Could Not {config['export_title']}",
                    str(exc),
                )

                return

            dialog.accept()

        # ---------------------------------------------------------
    
        export_button.clicked.connect(
            export_result
        )

        cancel_button.clicked.connect(
            dialog.reject
        )

        # ---------------------------------------------------------
        # LAYOUT
        # ---------------------------------------------------------

        layout.addLayout(
            left_row
        )

        layout.addLayout(
            right_row
        )

        layout.addSpacing(10)

        layout.addLayout(
            buttons_row
        )

        dialog.exec()
    
    
    def refresh_glossary_buttons(self):

        has_text = (
            self.text is not None
        )

        # ---------------------------------------------------------
        # EXPORT
        # ---------------------------------------------------------

        self.export_glossary_button.setEnabled(
            has_text
            and any(
                (
                    bool(
                        self.text.translation_glossary
                    ),
                    bool(
                        self.text.new_glossary
                    ),
                    bool(
                        self.text.extracted_terms
                    ),
                    bool(
                        self.text.extracted_glossary
                    ),
                )
            )
        )

        # ---------------------------------------------------------
        # EXTRACTION
        # ---------------------------------------------------------

        self.extract_terms_glossary_button.setEnabled(
            has_text
            and self.text.is_punctuated
        )

        self.extract_glossary_glossary_button.setEnabled(
            has_text
            and self.text.is_translated
        )

        unfinished = (
            self.unfinished_transform()
        )

        can_resume = (
            unfinished is not None
            and unfinished["operation"] in (
                "term_extraction",
                "glossary_extraction",
            )
        )

        self.resume_extraction_button.setEnabled(
            can_resume
        )
        

    def open_glossary_menu(
        self,
        page
    ):

        self.refresh_glossary_buttons()

        self.sidebar_stack.setCurrentWidget(
            page
        )

        self.main_stack.setCurrentWidget(
            self.text_workspace
        )

    
    # ---------------------------------------------------------
    # LEFT COLUMN
    # ---------------------------------------------------------

    def create_left_column(self):

        left_column = QWidget()
        left_column.setFixedWidth(150)

        layout = QVBoxLayout(left_column)
        layout.setContentsMargins(10, 15, 0, 10)

        sidebar = self.create_sidebar()

        layout.addWidget(sidebar, 1)

        return left_column

    # ---------------------------------------------------------
    # SIDEBAR
    # ---------------------------------------------------------

    def create_sidebar(self):

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")

        sidebar.setStyleSheet("""
            QFrame#sidebar {
                background-color: #eeeae1;
                border: 1px solid #ddd8cf;
                border-radius: 6px;
            }

            QPushButton {
                color: #681708;
                background-color: #eeeae1;
                border: 1px solid #681708;
                border-radius: 4px;
                padding: 6px;
            }

            QPushButton:hover {
                background-color: #f8f6f1;
                border: 1px solid #681708;
            }

            QPushButton:pressed {
                background-color: #e2ddd3;
                border: 1px solid #681708;
            }

            QPushButton:disabled {
                color: #999999;
                border: 1px solid #bbbbbb;
                background-color: #e5e2dc;
            }

            QPushButton#backButton {
                color: #681708;
                background: transparent;
                border: none;
                font-family: Arial;
                font-size: 28px;
                font-weight: 400;
                padding: 0px;
                text-align: left;
            }

            QPushButton#backButton:hover {
                background: transparent;
                border: none;
                font-weight: 900;
            }

            QPushButton#backButton:pressed {
                background: transparent;
                border: none;
                font-weight: 900;
            }
        """)

        outer_layout = QVBoxLayout(sidebar)
        outer_layout.setContentsMargins(3, 12, 3, 9)
        outer_layout.setSpacing(8)

        # ---------------------------------------------------------
        # PERMANENT LOGO
        # ---------------------------------------------------------

        logo = QLabel()
        logo.setAlignment(Qt.AlignCenter)

        logo_path = Path(__file__).parent / "assets" / "logo_half_thinnest_shortened.png"
        pixmap = QPixmap(str(logo_path))

        logo.setPixmap(
            pixmap.scaledToWidth(
                114,
                Qt.SmoothTransformation
            )
        )

        outer_layout.addWidget(
            logo,
            0,
            Qt.AlignTop | Qt.AlignHCenter
        )

        # ---------------------------------------------------------
        # SIDEBAR PAGES
        # ---------------------------------------------------------

        self.sidebar_stack = QStackedWidget()

        self.sidebar_stack.setStyleSheet("""
            QStackedWidget {
                border: none;
                background: transparent;
            }
        """)

        outer_layout.addWidget(self.sidebar_stack, 1)

        # =========================================================
        # MAIN SIDEBAR
        # =========================================================

        main_page = QWidget()
        main_layout = QVBoxLayout(main_page)

        file_button = QPushButton("File")
        transform_button = QPushButton("Transform Text")
        glossary_button = QPushButton("Glossary Tools")
        settings_button = QPushButton("Settings")

        main_layout.addWidget(file_button)
        main_layout.addWidget(transform_button)
        main_layout.addWidget(glossary_button)
        main_layout.addWidget(settings_button)

        main_layout.addStretch()

        # Main page must be index 0.
        self.sidebar_stack.addWidget(main_page)
        
        file_page = self.create_file_page()

        transform_page = self.create_transform_page()

        glossary_page = self.create_glossary_page()

        settings_page = self.create_settings_page()
        
        # Add those pages to the stack.
        self.sidebar_stack.addWidget(file_page)
        self.sidebar_stack.addWidget(transform_page)
        self.sidebar_stack.addWidget(glossary_page)
        self.sidebar_stack.addWidget(settings_page)

        # =========================================================
        # MAIN MENU NAVIGATION
        # =========================================================

        file_button.clicked.connect(
            lambda: self.sidebar_stack.setCurrentWidget(
                file_page
            )
        )

        file_button.clicked.connect(
            lambda: self.main_stack.setCurrentWidget(
                self.text_workspace
            )
        )

        transform_button.clicked.connect(
            lambda:
                self.open_transform_menu(
                    transform_page
                )
        )
        
        glossary_button.clicked.connect(
            lambda:
                self.open_glossary_menu(
                    glossary_page
                )
        )

        settings_button.clicked.connect(
            lambda: self.sidebar_stack.setCurrentWidget(
                settings_page
            )
        )

        return sidebar

    # =========================================================
    # HELPERS
    # =========================================================


    def create_settings_heading(self, text):

        label = QLabel(text)

        label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: bold;
                padding-top: 6px;
                padding-bottom: 4px;
            }
        """)

        return label


    def create_settings_separator(self):

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Plain)

        line.setStyleSheet("""
            QFrame {
                color: #8f8f8f;
                background-color: #8f8f8f;
                min-height: 1px;
                max-height: 1px;
                margin-top: 15px;
                margin-bottom: 15px;
            }
        """)

        return line


    def create_sidebar_heading(self, text):

        container = QWidget()
        layout = QHBoxLayout(container)

        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        left_line = QWidget()
        left_line.setFixedHeight(1)
        left_line.setStyleSheet(
            "background-color: #681708;"
        )

        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                color: #681708;
                background: transparent;
                border: none;
                font-size: 12px;
            }
        """)

        right_line = QWidget()
        right_line.setFixedHeight(1)
        right_line.setStyleSheet(
            "background-color: #681708;"
        )

        layout.addWidget(left_line, 1)
        layout.addWidget(label)
        layout.addWidget(right_line, 1)

        return container


    def create_back_button(self):

        back_button = QPushButton("←")
        back_button.setObjectName("backButton")
        back_button.setFixedSize(40, 30)

        return back_button


    def create_sidebar_separator(self):

        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet(
            "background-color: rgba(104, 23, 8, 0.30);"
        )

        return line

    
    def add_api_key_row(
        self,
        provider_name=None,
        key_value=None,
        mark_dirty=True
    ):

        row = QWidget()
        row_layout = QHBoxLayout(row)

        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)

        provider = QComboBox()
        provider.addItems([
            "OpenAI",
            "Google"
        ])
        provider.setPlaceholderText("API Provider")
        provider.setCurrentIndex(-1)
        provider.setFixedWidth(120)

        api_key = QLineEdit()
        api_key.setPlaceholderText("API Key")
        api_key.setEchoMode(QLineEdit.Password)
        api_key.setFixedWidth(300)

        provider.setStyleSheet("font-size: 9pt;")
        api_key.setStyleSheet("font-size: 9pt;")

        delete_button = QPushButton()
        delete_button.setObjectName("trashButton")
        delete_button.setFixedSize(26, 26)

        trash_path = Path(__file__).parent / "assets" / "trash.svg"

        delete_button.setIcon(
            QIcon(str(trash_path))
        )

        delete_button.setIconSize(
            QSize(16, 16)
        )

        delete_button.setToolTip("Delete")
        delete_button.setCursor(Qt.PointingHandCursor)

        delete_button.setStyleSheet("""
            QPushButton#trashButton {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 2px;
                padding: 0px;
            }

            QPushButton#trashButton:hover {
                background-color: #eeeae1;
                border: 1px solid #b98a80;
            }

            QPushButton#trashButton:pressed {
                background-color: #ddd8cf;
                border: 1px solid #681708;
            }
        """)

        if provider_name:
            provider.setCurrentText(provider_name)

        if key_value:
            api_key.setText(key_value)

        # Remember whether this row represents an already-saved key.
        row.setProperty(
            "saved_provider",
            provider_name if key_value else ""
        )

        delete_button.clicked.connect(
            lambda checked=False, row=row:
                self.remove_api_key_row(row)
        )

        row_layout.addWidget(provider)
        row_layout.addWidget(api_key)
        row_layout.addWidget(delete_button)

        self.api_keys_layout.addWidget(
            row,
            0,
            Qt.AlignHCenter
        )

        self.watch_setting(provider)
        self.watch_setting(api_key)

        if mark_dirty:
            self.mark_settings_dirty()


    def remove_api_key_row(self, row):

        saved_provider = row.property("saved_provider")

        if saved_provider:
            self.api_keys_to_delete.add(saved_provider)

        self.api_keys_layout.removeWidget(row)
        row.deleteLater()

        self.mark_settings_dirty()


    def clear_api_key_rows(self):

        while self.api_keys_layout.count():

            item = self.api_keys_layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()


    def load_api_keys(self):

        self.api_keys_to_delete.clear()
        self.clear_api_key_rows()

        for provider_name in (
            "OpenAI",
            "Google"
        ):

            key_value = keyring.get_password(
                "Yiding",
                provider_name
            )

            if key_value:

                self.add_api_key_row(
                    provider_name=provider_name,
                    key_value=key_value,
                    mark_dirty=False
                )

        self.settings_dirty = False

    
    def mark_settings_dirty(self, *args):

        self.settings_dirty = True

        for save_button in self.settings_save_buttons:
            save_button.setEnabled(True)
        

    def watch_setting(self, widget):

        if isinstance(widget, QLineEdit):
            widget.textChanged.connect(self.mark_settings_dirty)

        elif isinstance(widget, QPlainTextEdit):
            widget.textChanged.connect(self.mark_settings_dirty)

        elif isinstance(widget, QCheckBox):
            widget.toggled.connect(self.mark_settings_dirty)

        elif isinstance(widget, QComboBox):
            widget.currentIndexChanged.connect(self.mark_settings_dirty)

        elif isinstance(widget, QSpinBox):
            widget.valueChanged.connect(self.mark_settings_dirty)

        elif isinstance(widget, QSlider):
            widget.valueChanged.connect(self.mark_settings_dirty)


    def watch_settings_page(self, page):

        for widget_type in (
            QLineEdit,
            QPlainTextEdit,
            QCheckBox,
            QComboBox,
            QSpinBox,
            QSlider,
        ):

            for widget in page.findChildren(widget_type):
                self.watch_setting(widget)


    def confirm_settings_changes(self):

        if not self.settings_dirty:
            return True

        msg = QMessageBox(self)
        msg.setWindowTitle("Unsaved Changes")
        msg.setText("Do you want to save your changes?")
        msg.setIconPixmap(self.create_red_question_icon())

        msg.setStandardButtons(
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel
        )

        msg.setDefaultButton(QMessageBox.StandardButton.Save)

        choice = msg.exec()

        if choice == QMessageBox.StandardButton.Save:
            return self.save_current_settings()

        if choice == QMessageBox.StandardButton.Discard:
            self.reload_current_settings()
            self.settings_dirty = False
            return True

        return False


    def save_current_settings(self):

        current_page = self.main_stack.currentWidget()

        if current_page is self.api_services_workspace:
            result = self.save_api_access()

        elif current_page is self.punctuation_workspace:
            result = self.save_punctuation_settings()

        elif current_page is self.translation_workspace:
            result = self.save_translation_settings()

        elif current_page is self.term_extraction_workspace:
            result = self.save_term_extraction_settings()
    
        elif current_page is self.glossary_extraction_workspace:
            result = self.save_glossary_extraction_settings()

        else:
            return True

        if result:

            self.settings_dirty = False

            for save_button in self.settings_save_buttons:
                save_button.setEnabled(False)

        return result


    def save_api_access(self):

        active_providers = set()

        for i in range(self.api_keys_layout.count()):

            item = self.api_keys_layout.itemAt(i)
            row = item.widget()

            if row is None:
                continue

            provider = row.findChild(QComboBox)
            api_key = row.findChild(QLineEdit)

            if provider is None or api_key is None:
                continue

            provider_name = provider.currentText().strip()
            key_value = api_key.text().strip()

            # Ignore completely empty rows
            if not provider_name and not key_value:
                continue

            # Incomplete row
            if not provider_name or not key_value:
                QMessageBox.warning(
                    self,
                    "Incomplete API Key",
                    "Each API entry needs both a provider and an API key."
                )
                return False

            saved_provider = row.property("saved_provider")

            # Provider was changed on an existing saved row.
            if (
                saved_provider
                and saved_provider != provider_name
            ):
                self.api_keys_to_delete.add(
                    saved_provider
                )

            keyring.set_password(
                "Yiding",
                provider_name,
                key_value
            )

            active_providers.add(provider_name)

            row.setProperty(
                "saved_provider",
                provider_name
            )

        # Delete keys whose rows were removed.
        for provider_name in self.api_keys_to_delete:

            if provider_name in active_providers:
                continue

            try:
                keyring.delete_password(
                    "Yiding",
                    provider_name
                )
            except keyring.errors.PasswordDeleteError:
                pass

        self.api_keys_to_delete.clear()
        self.settings_dirty = False

        return True


    def switch_settings_page(self, target_page):

        current_page = self.main_stack.currentWidget()

        if current_page is target_page:
            return

        if current_page in self.settings_pages:

            if not self.confirm_settings_changes():
                return

        self.main_stack.setCurrentWidget(target_page)


    def closeEvent(self, event):

        if self.confirm_settings_changes():
            event.accept()
        else:
            event.ignore()


    def leave_settings(self):

        if not self.confirm_settings_changes():
            return

        self.sidebar_stack.setCurrentIndex(0)
        self.main_stack.setCurrentWidget(
            self.text_workspace
        )


    def add_settings_save_button(self, layout):

        save_row = QHBoxLayout()
        save_row.addStretch()

        save_button = QPushButton("Save")
        save_button.setFixedWidth(90)
        save_button.setEnabled(False)

        save_button.setStyleSheet("""
            QPushButton {
                color: #888888;
                background-color: #f2f2f2;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                padding: 5px 12px;
            }

            QPushButton:enabled {
                color: white;
                background-color: #681708;
                border: 1px solid #681708;
            }

            QPushButton:enabled:hover {
                background-color: #852515;
                border: 1px solid #852515;
            }

            QPushButton:enabled:pressed {
                background-color: #4f1106;
                border: 1px solid #4f1106;
            }

            QPushButton:disabled {
                color: #999999;
                background-color: #f2f2f2;
                border: 1px solid #d0d0d0;
            }
        """)

        save_button.clicked.connect(
            self.save_current_settings
        )

        self.settings_save_buttons.append(
            save_button
        )

        save_row.addWidget(save_button)
        layout.addLayout(save_row)
    
    
    def create_red_question_icon(self):

        pixmap = QPixmap(48, 48)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        font = QFont("Microsoft YaHei UI", 28)
        font.setBold(True)
        painter.setFont(font)

        painter.setPen(QColor("#681708"))
        painter.drawText(
            pixmap.rect(),
            Qt.AlignCenter,
            "？"
        )

        painter.end()

        return pixmap


    def save_punctuation_settings(self):

        self.update_settings_tree(
            self.settings[
                "punctuation"
            ],
            self.punctuation_settings_widget
            .current_settings()
        )

        save_settings(
            self.settings
        )

        self.settings_dirty = False

        return True


    def save_translation_settings(self):

        self.update_settings_tree(
            self.settings[
                "translation"
            ],
            self.translation_settings_widget
            .current_settings()
        )

        save_settings(
            self.settings
        )

        self.settings_dirty = False

        return True


    def save_term_extraction_settings(self):

        self.update_settings_tree(
            self.settings[
                "term_extraction"
            ],
            self.term_extraction_settings_widget
            .current_settings()
        )

        save_settings(
            self.settings
        )

        self.settings_dirty = False

        return True


    def save_glossary_extraction_settings(self):

        self.update_settings_tree(
            self.settings[
                "glossary_extraction"
            ],
            self.glossary_extraction_settings_widget
            .current_settings()
        )

        save_settings(
            self.settings
        )

        self.settings_dirty = False

        return True


    def save_model_settings(
        self,
        settings,
        controls
    ):

        settings["model"] = (
            self.model_name_from_controls(controls)
        )

        settings["reasoning"] = (
            controls["reasoning_levels"][
                controls["reasoning"].value()
            ]
        )

        if controls["verbosity_enabled"].isChecked():

            settings["verbosity"] = (
                controls["verbosity_levels"][
                    controls["verbosity"].value()
                ]
            )

        else:

            settings["verbosity"] = False

        if controls["temperature_enabled"].isChecked():

            settings["temperature"] = (
                controls["temperature"].value()
                / 100
            )

        else:

            settings["temperature"] = False

        if controls["top_p_enabled"].isChecked():

            settings["top_p"] = (
                controls["top_p"].value()
                / 100
            )

        else:

            settings["top_p"] = False


    def reload_model_settings(
        self,
        model_settings,
        controls
    ):

        # MODEL

        model_choices = (
            list(GPT_MODELS)
            + list(GEMINI_MODELS)
        )

        model_name = (
            model_settings["model"]
        )

        controls["model"].blockSignals(True)
        controls["other_model"].blockSignals(True)

        if model_name in model_choices:

            controls["model"].setCurrentText(
                model_name
            )

            controls["model"].setFixedWidth(
                controls["model_full_width"]
            )

            controls["other_model"].clear()

            controls["other_model"].setVisible(
                False
            )

        else:

            controls["model"].setCurrentText(
                "Other"
            )

            controls["model"].setFixedWidth(
                controls["model_half_width"]
            )

            controls["other_model"].setFixedWidth(
                controls["model_half_width"]
            )

            controls["other_model"].setText(
                model_name
            )

            controls["other_model"].setVisible(
                True
            )

        controls["model"].blockSignals(False)
        controls["other_model"].blockSignals(False)
        
        # REASONING
        reasoning_value = model_settings["reasoning"]

        if reasoning_value is False:
            reasoning_value = "none"

        controls["reasoning"].setValue(
            controls["reasoning_levels"].index(
                reasoning_value
            )
        )

        # VERBOSITY
        verbosity_value = model_settings["verbosity"]
        verbosity_enabled = verbosity_value is not False

        controls["verbosity_enabled"].setChecked(
            verbosity_enabled
        )

        if verbosity_enabled:
            controls["verbosity"].setValue(
                controls["verbosity_levels"].index(
                    verbosity_value
                )
            )

        # TEMPERATURE
        temperature_value = model_settings["temperature"]
        temperature_enabled = temperature_value is not False

        controls["temperature_enabled"].setChecked(
            temperature_enabled
        )

        if temperature_enabled:
            controls["temperature"].setValue(
                round(float(temperature_value) * 100)
            )

        # TOP P
        top_p_value = model_settings["top_p"]
        top_p_enabled = top_p_value is not False

        controls["top_p_enabled"].setChecked(
            top_p_enabled
        )

        if top_p_enabled:
            controls["top_p"].setValue(
                round(float(top_p_value) * 100)
            )
        
        
    def reload_current_settings(self):

        self.settings = load_settings()

        current_page = (
            self.main_stack.currentWidget()
        )

        if current_page is self.api_services_workspace:

            self.load_api_keys()

            self.settings_dirty = False

            return True

        elif current_page is self.punctuation_workspace:

            self.punctuation_settings_widget.load_settings(
                self.settings[
                    "punctuation"
                ]
            )

        elif current_page is self.translation_workspace:

            self.translation_settings_widget.load_settings(
                self.settings[
                    "translation"
                ]
            )

        elif current_page is self.term_extraction_workspace:

            self.term_extraction_settings_widget.load_settings(
                self.settings[
                    "term_extraction"
                ]
            )

        elif current_page is self.glossary_extraction_workspace:

            self.glossary_extraction_settings_widget.load_settings(
                self.settings[
                    "glossary_extraction"
                ]
            )

        self.settings_dirty = False

        for save_button in self.settings_save_buttons:

            save_button.setEnabled(
                False
            )

        return True


    def create_level_slider(
        self,
        levels,
        current_value,
        width=270
    ):

        widget = QWidget()
        widget.setFixedSize(width, 40)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, len(levels) - 1)
        slider.setSingleStep(1)
        slider.setTickInterval(1)
        slider.setTickPosition(QSlider.TicksBelow)
        slider.setFixedWidth(width)

        if current_value not in levels:
            current_value = levels[0]

        slider.setValue(
            levels.index(current_value)
        )

        layout.addWidget(slider)

        labels = QHBoxLayout()
        labels.setContentsMargins(8, 0, 8, 0)
        labels.setSpacing(0)

        for index, text in enumerate(levels):

            label = QLabel(text)

            if index == 0:
                label.setAlignment(Qt.AlignLeft)

            elif index == len(levels) - 1:
                label.setAlignment(Qt.AlignRight)

            else:
                label.setAlignment(Qt.AlignCenter)

            labels.addWidget(label, 1)

        layout.addLayout(labels)

        return widget, slider


    def create_numeric_slider(
        self,
        minimum,
        maximum,
        current_value,
        width=270
    ):

        widget = QWidget()
        widget.setFixedSize(width, 40)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        slider = QSlider(Qt.Horizontal)

        slider.setRange(
            round(minimum * 100),
            round(maximum * 100)
        )

        slider.setSingleStep(1)
        slider.setFixedWidth(width)

        slider.setValue(
            round(float(current_value) * 100)
        )

        layout.addWidget(slider)

        value_label = QLabel(
            f"{slider.value() / 100:.2f}"
        )
        value_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(value_label)

        slider.valueChanged.connect(
            lambda value:
                value_label.setText(
                    f"{value / 100:.2f}"
                )
        )

        return widget, slider


    def create_model_settings_widget(
        self,
        model_settings,
        model_label
    ):

        widget = QWidget()

        form = QFormLayout(widget)
        form.setContentsMargins(0, 0, 0, 0)
        form.setHorizontalSpacing(15)
        form.setVerticalSpacing(6)

        control_width = 165

        controls = {}

        # MODEL

        model_choices = (
            list(GPT_MODELS)
            + list(GEMINI_MODELS)
        )

        model_spacing = 6
        model_half_width = (
            control_width - model_spacing
        ) // 2

        controls["model_full_width"] = (
            control_width
        )

        controls["model_half_width"] = (
            model_half_width
        )

        controls["model"] = QComboBox()
        controls["model"].addItems(
            model_choices
            + ["Other"]
        )

        controls["other_model"] = QLineEdit()
        controls["other_model"].setPlaceholderText(
            "Model name"
        )

        model_container = QWidget()
        model_container.setFixedWidth(
            control_width
        )

        model_layout = QHBoxLayout(
            model_container
        )

        model_layout.setContentsMargins(
            0, 0, 0, 0
        )

        model_layout.setSpacing(
            model_spacing
        )

        model_layout.addWidget(
            controls["model"]
        )

        model_layout.addWidget(
            controls["other_model"]
        )

        current_model = (
            model_settings["model"]
        )

        if current_model in model_choices:

            controls["model"].setCurrentText(
                current_model
            )

            controls["model"].setFixedWidth(
                control_width
            )

            controls["other_model"].setVisible(
                False
            )

        else:

            controls["model"].setCurrentText(
                "Other"
            )

            controls["model"].setFixedWidth(
                model_half_width
            )

            controls["other_model"].setFixedWidth(
                model_half_width
            )

            controls["other_model"].setText(
                current_model
            )

            controls["other_model"].setVisible(
                True
            )

        model_label_widget = QLabel(
            model_label
        )

        model_label_widget.setStyleSheet(
            "font-weight: bold;"
        )

        form.addRow(
            model_label_widget,
            model_container
        )

        controls["model"].currentTextChanged.connect(
            lambda:
                self.model_selection_changed(
                    controls
                )
        )

        controls["other_model"].editingFinished.connect(
            lambda:
                self.other_model_finished(
                    controls
                )
        )
        
        # REASONING
        controls["reasoning_levels"] = [
            "none",
            "low",
            "medium",
            "high"
        ]

        reasoning_value = model_settings["reasoning"]

        if reasoning_value is False:
            reasoning_value = "none"

        reasoning_widget, controls["reasoning"] = (
            self.create_level_slider(
                controls["reasoning_levels"],
                reasoning_value,
                control_width
            )
        )

        form.addRow(
            "Reasoning:",
            reasoning_widget
        )

        # VERBOSITY
        controls["verbosity_levels"] = [
            "low",
            "medium",
            "high"
        ]

        verbosity_value = model_settings["verbosity"]
        verbosity_enabled = verbosity_value is not False

        controls["verbosity_enabled"] = QCheckBox(
            "Verbosity:"
        )
        controls["verbosity_enabled"].setChecked(
            verbosity_enabled
        )

        if not verbosity_enabled:
            verbosity_value = "medium"

        verbosity_content, controls["verbosity"] = (
            self.create_level_slider(
                controls["verbosity_levels"],
                verbosity_value,
                control_width
            )
        )

        verbosity_container = QWidget()
        verbosity_container.setFixedHeight(40)

        verbosity_container_layout = QVBoxLayout(
            verbosity_container
        )
        verbosity_container_layout.setContentsMargins(
            0, 0, 0, 0
        )
        verbosity_container_layout.addWidget(
            verbosity_content
        )

        verbosity_content.setVisible(
            verbosity_enabled
        )

        controls["verbosity_enabled"].toggled.connect(
            verbosity_content.setVisible
        )

        form.addRow(
            controls["verbosity_enabled"],
            verbosity_container
        )

        # TEMPERATURE
        temperature_value = model_settings["temperature"]
        temperature_enabled = temperature_value is not False

        controls["temperature_enabled"] = QCheckBox(
            "Temperature:"
        )
        controls["temperature_enabled"].setChecked(
            temperature_enabled
        )

        if not temperature_enabled:
            temperature_value = 1.0

        temperature_content, controls["temperature"] = (
            self.create_numeric_slider(
                0.0,
                2.0,
                temperature_value,
                control_width
            )
        )

        temperature_container = QWidget()
        temperature_container.setFixedHeight(40)

        temperature_container_layout = QVBoxLayout(
            temperature_container
        )
        temperature_container_layout.setContentsMargins(
            0, 0, 0, 0
        )
        temperature_container_layout.addWidget(
            temperature_content
        )

        temperature_content.setVisible(
            temperature_enabled
        )

        controls["temperature_enabled"].toggled.connect(
            temperature_content.setVisible
        )

        form.addRow(
            controls["temperature_enabled"],
            temperature_container
        )

        # TOP P
        top_p_value = model_settings["top_p"]
        top_p_enabled = top_p_value is not False

        controls["top_p_enabled"] = QCheckBox(
            "Top P:"
        )
        controls["top_p_enabled"].setChecked(
            top_p_enabled
        )

        if not top_p_enabled:
            top_p_value = 1.0

        top_p_content, controls["top_p"] = (
            self.create_numeric_slider(
                0.0,
                1.0,
                top_p_value,
                control_width
            )
        )

        top_p_container = QWidget()
        top_p_container.setFixedHeight(40)

        top_p_container_layout = QVBoxLayout(
            top_p_container
        )
        top_p_container_layout.setContentsMargins(
            0, 0, 0, 0
        )
        top_p_container_layout.addWidget(
            top_p_content
        )

        top_p_content.setVisible(
            top_p_enabled
        )

        controls["top_p_enabled"].toggled.connect(
            top_p_content.setVisible
        )

        form.addRow(
            controls["top_p_enabled"],
            top_p_container
        )

        return widget, controls

    
    def refresh_text_workspace(self):

        # ---------------------------------------------------------
        # NO PROJECT
        # ---------------------------------------------------------

        if self.text is None:

            self.text_tabs.clear()

            self.workspace_title.hide()

            self.workspace_stack.setCurrentWidget(
                self.empty_workspace
            )

            return

        # ---------------------------------------------------------
        # GET AVAILABLE TEXT
        # ---------------------------------------------------------

        segments = (
            self.text.segments
        )

        page_labels = (
            self.text.page_labels
        )

        unpunctuated = (
            self.text.unpunctuated_segments
        )

        punctuated = (
            self.text.punctuated_segments
        )

        translated = (
            self.text.translated_segments
        )

        segment_labels = (
            self.text.segment_labels
        )

        translation_glossary = (
            self.text.translation_glossary
        )

        new_glossary = (
            self.text.new_glossary
        )

        extracted_terms = (
            self.text.extracted_terms
        )

        extracted_glossary = (
            self.text.extracted_glossary
        )

        # ---------------------------------------------------------
        # FILL TEXT WIDGETS
        # ---------------------------------------------------------

        self.unpunctuated_editor.setPlainText(
            self.format_labeled_text(
                segments,
                page_labels
            )
        )

        self.punctuated_editor.setPlainText(
            self.format_labeled_text(
                punctuated,
                segment_labels
            )
        )

        self.translated_editor.setPlainText(
            self.format_labeled_text(
                translated,
                segment_labels
            )
        )

        # ---------------------------------------------------------
        # FILL COMPARISON TABLES
        # ---------------------------------------------------------

        self.populate_comparison_table(
            self.unpunctuated_punctuated_table,
            unpunctuated,
            punctuated,
            segment_labels
        )

        self.populate_comparison_table(
            self.punctuated_translation_table,
            punctuated,
            translated,
            segment_labels
        )

        # ---------------------------------------------------------
        # FILL GLOSSARY TABLES
        # ---------------------------------------------------------

        self.populate_glossary_table(
            self.translation_glossary_table,
            translation_glossary
        )

        self.populate_glossary_table(
            self.new_glossary_table,
            new_glossary
        )

        self.populate_glossary_table(
            self.extracted_terms_table,
            extracted_terms
        )

        self.populate_glossary_table(
            self.extracted_glossary_table,
            extracted_glossary
        )

        # ---------------------------------------------------------

        selected_tab_data = None

        current_index = self.text_tabs.currentIndex()

        if current_index >= 0:

            selected_tab_data = (
                self.text_tabs
                .tabBar()
                .tabData(current_index)
            )

        # ---------------------------------------------------------
        # REBUILD TABS
        # ---------------------------------------------------------

        self.text_tabs.clear()

        # UNPUNCTUATED

        if segments:

            index = self.text_tabs.addTab(
                self.unpunctuated_editor,
                "Unpunctuated"
            )

            self.text_tabs.tabBar().setTabData(
                index,
                "UNPUNCTUATED TEXT"
            )

        # UNPUNCTUATED / PUNCTUATED

        if unpunctuated and punctuated:

            index = self.text_tabs.addTab(
                self.unpunctuated_punctuated_table,
                "U || P"
            )

            self.text_tabs.tabBar().setTabData(
                index,
                "UNPUNCTUATED / PUNCTUATED COMPARISON"
            )

            self.text_tabs.setTabToolTip(
                index,
                "Unpunctuated / Punctuated"
            )

        # PUNCTUATED

        if punctuated:

            index = self.text_tabs.addTab(
                self.punctuated_editor,
                "Punctuated"
            )

            self.text_tabs.tabBar().setTabData(
                index,
                "PUNCTUATED TEXT"
            )

        # PUNCTUATED / TRANSLATION

        if punctuated and translated:

            index = self.text_tabs.addTab(
                self.punctuated_translation_table,
                "P || T"
            )

            self.text_tabs.tabBar().setTabData(
                index,
                "PUNCTUATED / TRANSLATION COMPARISON"
            )

            self.text_tabs.setTabToolTip(
                index,
                "Punctuated / Translation"
            )

        # TRANSLATION

        if translated:

            index = self.text_tabs.addTab(
                self.translated_editor,
                "Translation"
            )

            self.text_tabs.tabBar().setTabData(
                index,
                "TRANSLATION"
            )

        # TRANSLATION GLOSSARY

        if translation_glossary:

            index = self.text_tabs.addTab(
                self.translation_glossary_table,
                "Translation Glossary"
            )

            self.text_tabs.tabBar().setTabData(
                index,
                "TRANSLATION GLOSSARY"
            )

        # NEW GLOSSARY

        if new_glossary:

            index = self.text_tabs.addTab(
                self.new_glossary_table,
                "New Glossary"
            )

            self.text_tabs.tabBar().setTabData(
                index,
                "NEW GLOSSARY"
            )

        # EXTRACTED TERMS

        if extracted_terms:

            index = self.text_tabs.addTab(
                self.extracted_terms_table,
                "Extracted Terms"
            )

            self.text_tabs.tabBar().setTabData(
                index,
                "EXTRACTED TERMS"
            )


        # EXTRACTED GLOSSARY

        if extracted_glossary:

            index = self.text_tabs.addTab(
                self.extracted_glossary_table,
                "Extracted Glossary"
            )

            self.text_tabs.tabBar().setTabData(
                index,
                "EXTRACTED GLOSSARY"
            )
    
        # ---------------------------------------------------------
        # SHOW CORRECT WORKSPACE
        # ---------------------------------------------------------

        if self.text_tabs.count() == 0:

            self.workspace_title.hide()

            self.workspace_stack.setCurrentWidget(
                self.empty_workspace
            )

            return

        self.workspace_stack.setCurrentWidget(
            self.text_tabs
        )

        self.workspace_title.show()

        restore_index = 0

        if selected_tab_data is not None:

            for i in range(
                self.text_tabs.count()
            ):

                if (
                    self.text_tabs
                    .tabBar()
                    .tabData(i)
                    == selected_tab_data
                ):

                    restore_index = i
                    break

        self.text_tabs.setCurrentIndex(
            restore_index
        )

        self.change_text_tab(
            restore_index
        )


    def select_translation_glossary(self):

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

        self.translation_glossary.setText(
            filename
        )
    

    def model_provider(self, model_name):

        if is_open_ai(model_name):
            return "OpenAI"

        if is_google(model_name):
            return "Google"

        return None


    def model_name_from_controls(self, controls):

        if controls["model"].currentText() == "Other":
            return controls["other_model"].text().strip()

        return controls["model"].currentText().strip()


    def check_model_api_key(self, model_name):

        provider = self.model_provider(model_name)

        if provider is None:
            return

        api_key = keyring.get_password(
            "Yiding",
            provider
        )

        if api_key:
            return

        self.prompt_for_api_key(provider)


    def prompt_for_api_key(self, provider_name):

        dialog = QDialog(self)
        dialog.setWindowTitle("API Key Required")
        dialog.setModal(True)
        dialog.setFixedWidth(430)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        message = QLabel(
            f"No API keys stored for {provider_name}."
        )

        layout.addWidget(message)

        form = QFormLayout()
        form.setHorizontalSpacing(15)
        form.setVerticalSpacing(10)

        provider = QComboBox()
        provider.addItems([
            "OpenAI",
            "Google",
        ])
        provider.setCurrentText(provider_name)

        api_key = QLineEdit()
        api_key.setPlaceholderText("API Key")
        api_key.setEchoMode(QLineEdit.Password)

        form.addRow(
            "Provider:",
            provider
        )

        form.addRow(
            "API Key:",
            api_key
        )

        layout.addLayout(form)

        button_row = QHBoxLayout()
        button_row.addStretch()

        cancel_button = QPushButton("Cancel")
        save_button = QPushButton("Save Key")

        save_button.setEnabled(False)

        button_row.addWidget(cancel_button)
        button_row.addWidget(save_button)

        layout.addLayout(button_row)

        api_key.textChanged.connect(
            lambda text:
                save_button.setEnabled(
                    bool(text.strip())
                )
        )

        cancel_button.clicked.connect(
            dialog.reject
        )

        def save_key():

            provider_name = (
                provider.currentText()
                .strip()
            )

            key_value = (
                api_key.text()
                .strip()
            )

            keyring.set_password(
                "Yiding",
                provider_name,
                key_value
            )

            self.add_api_key_row(
                provider_name=provider_name,
                key_value=key_value,
                mark_dirty=False
            )

            dialog.accept()

        save_button.clicked.connect(
            save_key
        )

        dialog.exec()


    def model_selection_changed(
        self,
        controls
    ):

        other_selected = (
            controls["model"].currentText()
            == "Other"
        )

        if other_selected:

            controls["model"].setFixedWidth(
                controls["model_half_width"]
            )

            controls["other_model"].setFixedWidth(
                controls["model_half_width"]
            )

            controls["other_model"].setVisible(
                True
            )

            controls["other_model"].setFocus()

            model_name = (
                controls["other_model"]
                .text()
                .strip()
            )

        else:

            controls["other_model"].setVisible(
                False
            )

            controls["model"].setFixedWidth(
                controls["model_full_width"]
            )

            model_name = (
                controls["model"]
                .currentText()
                .strip()
            )

        if model_name:
            self.check_model_api_key(
                model_name
            )
            

    def other_model_finished(
        self,
        controls
    ):

        if (
            controls["model"].currentText()
            != "Other"
        ):
            return

        model_name = (
            controls["other_model"]
            .text()
            .strip()
        )

        if model_name:
            self.check_model_api_key(
                model_name
            )


    def update_settings_tree(
        self,
        target,
        source
    ):

        for key, value in source.items():

            if (
                isinstance(value, dict)
                and key in target
                and hasattr(
                    target[key],
                    "items"
                )
            ):

                self.update_settings_tree(
                    target[key],
                    value
                )

            else:

                target[key] = value


    def save_transform_defaults(
        self,
        transform_settings
    ):

        settings = load_settings()

        for (
            section_name,
            section_settings
        ) in transform_settings.items():

            self.update_settings_tree(
                settings[
                    section_name
                ],
                section_settings
            )

        save_settings(
            settings
        )

        self.settings = settings


    def open_transform_settings(
        self,
        operation
    ):

        defaults = load_settings()

        dialog = TransformSettingsDialog(
            self,
            operation,
            defaults,
            self.save_transform_defaults
        )

        if (
            dialog.exec()
            != QDialog.DialogCode.Accepted
        ):
            return None

        return dialog.selected_settings
    

    def reset_transform_progress(
        self,
        operation,
        project
    ):

        # ---------------------------------------------------------
        # PUNCTUATION
        # ---------------------------------------------------------

        if operation == "punctuation":

            self.text.working_i = 0
            self.text.working_text = ""
            self.text.working_labels = []

            self.text.unpunctuated_segments = []
            self.text.punctuated_segments = []
            self.text.segment_labels = []
            self.text.punctuated_glosses = []

            self.text.is_punctuated = False

            project["provenance"][
                "punctuated_segment_run_ids"
            ] = []

        # ---------------------------------------------------------
        # TRANSLATION
        # ---------------------------------------------------------

        elif operation == "translation":

            self.text.empty_translation()

            project["provenance"][
                "translated_segment_run_ids"
            ] = []

        # ---------------------------------------------------------
        # TERM EXTRACTION
        # ---------------------------------------------------------

        elif operation == "term_extraction":

            self.text.term_extraction_i = 0
            self.text.extracted_terms = set()
            self.text.is_term_extracted = False

        # ---------------------------------------------------------
        # GLOSSARY EXTRACTION
        # ---------------------------------------------------------

        elif operation == "glossary_extraction":

            self.text.glossary_extraction_i = 0
            self.text.extracted_glossary = {}
            self.text.is_glossary_extracted = False

        else:

            raise ValueError(
                f"Unknown transformation: {operation}"
            )
    

    def discard_unfinished_transform(self):

        if (
            self.text is None
            or self.project_file is None
        ):
            return False

        project = load_project(
            self.project_file
        )

        workflow = project["workflow"]

        if workflow["status"] != "in_progress":
            return True

        operation = workflow["operation"]
        active_run_id = workflow[
            "active_run_id"
        ]

        self.reset_transform_progress(
            operation,
            project
        )

        for run in project["runs"]:

            if (
                run["id"] == active_run_id
                and run["status"] == "in_progress"
            ):

                finish_run(
                    run,
                    status="cancelled"
                )

                break

        new_workflow = {
            "status": "idle",
            "operation": None,
            "active_run_id": None,

            "working_i":
                self.text.working_i,

            "working_text":
                self.text.working_text,

            "working_labels":
                self.text.working_labels,

            "translation_i":
                self.text.translation_i,

            "term_extraction_i":
                self.text.term_extraction_i,

            "glossary_extraction_i":
                self.text.glossary_extraction_i,
        }

        self.text.yiding_runs = (
            project["runs"]
        )

        self.text.yiding_provenance = (
            project["provenance"]
        )

        save_project(
            self.project_file,
            self.text,
            project["settings"],

            workflow=new_workflow,

            runs=project["runs"],

            provenance=project[
                "provenance"
            ],

            glossary_source_path=(
                project["settings"]
                ["translation"]
                ["glossary"]
            ),
        )

        self.orchestrator = None

        self.refresh_text_workspace()
        self.refresh_transform_buttons()
        self.refresh_glossary_buttons()

        return True


    def transform_runtime_settings(
        self,
        selected_settings
    ):

        settings = load_settings()

        for (
            section_name,
            section_settings
        ) in selected_settings.items():

            self.update_settings_tree(
                settings[section_name],
                section_settings
            )

        return settings


    def request_transform(
        self,
        operation
    ):

        unfinished = (
            self.unfinished_transform()
        )

        # ---------------------------------------------------------
        # EXISTING UNFINISHED TRANSFORMATION
        # ---------------------------------------------------------

        if unfinished is not None:

            old_operation = (
                unfinished["operation"]
            )

            old_name = (
                self.transform_operation_name(
                    old_operation
                )
            )

            message = QMessageBox(self)

            message.setWindowTitle(
                "Unfinished Transformation"
            )

            message.setText(
                f"An unfinished {old_name} "
                "transformation is stored "
                "in this project."
            )

            message.setInformativeText(
                "Starting a new transformation "
                "will erase all unfinished "
                f"{old_name} progress.\n\n"
                "Do you want to continue?"
            )

            message.setIconPixmap(
                self.create_red_question_icon()
            )

            erase_button = (
                message.addButton(
                    "Erase Progress",
                    QMessageBox.ButtonRole.AcceptRole
                )
            )

            cancel_button = (
                message.addButton(
                    "Cancel",
                    QMessageBox.ButtonRole.RejectRole
                )
            )

            message.setDefaultButton(
                cancel_button
            )

            message.exec()

            if (
                message.clickedButton()
                is not erase_button
            ):
                return

            try:

                if not self.discard_unfinished_transform():
                    return

            except Exception as exc:

                QMessageBox.critical(
                    self,
                    "Could Not Erase Progress",
                    str(exc)
                )

                return

        # ---------------------------------------------------------
        # OPEN TRANSFORMATION SETTINGS
        # ---------------------------------------------------------

        selected_settings = (
            self.open_transform_settings(
                operation
            )
        )

        if selected_settings is None:
            return

        self.start_transform(
            operation,
            selected_settings
        )


    def restore_project_after_cancel(
        self
    ):

        project = load_project(
            self.project_file
        )

        workflow = project["workflow"]

        active_run_id = workflow[
            "active_run_id"
        ]

        if not active_run_id:
            return True

        for run in project["runs"]:

            if (
                run["id"] == active_run_id
                and run["status"] == "in_progress"
            ):

                finish_run(
                    run,
                    status="cancelled"
                )

                break

        new_workflow = {
            "status": "idle",
            "operation": None,
            "active_run_id": None,

            "working_i":
                self.text.working_i,

            "working_text":
                self.text.working_text,

            "working_labels":
                self.text.working_labels,

            "translation_i":
                self.text.translation_i,

            "term_extraction_i":
                self.text.term_extraction_i,

            "glossary_extraction_i":
                self.text.glossary_extraction_i,
        }

        self.text.yiding_runs = (
            project["runs"]
        )

        self.text.yiding_provenance = (
            project["provenance"]
        )

        save_project(
            self.project_file,
            self.text,
            project["settings"],

            workflow=new_workflow,

            runs=project["runs"],

            provenance=project[
                "provenance"
            ],

            glossary_source_path=(
                project["settings"]
                ["translation"]
                ["glossary"]
            ),
        )

        self.orchestrator = None

        self.refresh_transform_buttons()
        self.refresh_glossary_buttons()

        return True


    def request_resume_transform(
        self
    ):

        unfinished = (
            self.unfinished_transform()
        )

        if unfinished is None:

            self.refresh_transform_buttons()
            self.refresh_glossary_buttons()
            return

        project = load_project(
            self.project_file
        )

        operation = (
            unfinished["operation"]
        )

        active_run_id = (
            unfinished["active_run_id"]
        )

        operation_name = (
            self.transform_operation_name(
                operation
            )
        )

        # ---------------------------------------------------------
        # ASK SAME SETTINGS?
        # ---------------------------------------------------------

        message = QMessageBox(self)

        message.setWindowTitle(
            f"Resume {operation_name}"
        )

        message.setText(
            f"Resume the unfinished "
            f"{operation_name} transformation "
            "with the same settings?"
        )

        message.setIconPixmap(
            self.create_red_question_icon()
        )

        same_button = (
            message.addButton(
                "Same Settings",
                QMessageBox.ButtonRole.AcceptRole
            )
        )

        change_button = (
            message.addButton(
                "Change Settings",
                QMessageBox.ButtonRole.ActionRole
            )
        )

        cancel_button = (
            message.addButton(
                "Cancel",
                QMessageBox.ButtonRole.RejectRole
            )
        )

        message.setDefaultButton(
            same_button
        )

        message.exec()

        clicked = (
            message.clickedButton()
        )

        # ---------------------------------------------------------
        # CANCEL
        # ---------------------------------------------------------

        if clicked is cancel_button:
            return

        # ---------------------------------------------------------
        # SAME SETTINGS
        # ---------------------------------------------------------

        if clicked is same_button:

            active_run = None

            for run in project["runs"]:

                if run["id"] == active_run_id:

                    active_run = run
                    break

            if active_run is None:

                QMessageBox.critical(
                    self,
                    "Cannot Resume",
                    "The active transformation run "
                    "could not be found."
                )

                return

            settings = project["settings"]

            settings[operation] = active_run["settings"]

            self.start_transform(
                operation,
                settings,
                settings_are_full=True
            )

            return

        # ---------------------------------------------------------
        # CHANGE SETTINGS
        # ---------------------------------------------------------

        if clicked is change_button:

            selected_settings = (
                self.open_transform_settings(
                    operation
                )
            )

            if selected_settings is None:
                return

            try:

                self.restore_project_after_cancel()

            except Exception as exc:

                QMessageBox.critical(
                    self,
                    "Cannot Resume",
                    str(exc)
                )

                return

            self.start_transform(
                operation,
                selected_settings
            )


    def start_transform(
        self,
        operation,
        settings,
        settings_are_full=False
    ):

        if self.transform_thread is not None:

            QMessageBox.information(
                self,
                "Transformation Running",
                "Another transformation is already in progress."
            )

            return

        if (
            self.text is None
            or self.project_file is None
        ):
            return

        if settings_are_full:

            runtime_settings = settings

        else:

            runtime_settings = (
                self.transform_runtime_settings(
                    settings
                )
            )

        # ---------------------------------------------------------
        # ORCHESTRATOR
        # ---------------------------------------------------------

        self.orchestrator = (
            WorkflowOrchestrator(
                self.text,
                runtime_settings
            )
        )

        self.orchestrator.project_file = (
            self.project_file
        )

        # ---------------------------------------------------------
        # PROGRESS DIALOG
        # ---------------------------------------------------------

        progress_dialog = (
            TransformProgressDialog(
                operation,
                runtime_settings,
                self.text,
                self,
            )
        )

        # ---------------------------------------------------------
        # WORKER THREAD
        # ---------------------------------------------------------

        thread = QThread(self)

        worker = TransformWorker(
            self.orchestrator,
            operation,
        )

        self.transform_thread = thread
        self.transform_worker = worker
        
        self.transform_progress_dialog = (
            progress_dialog
        )

        self.orchestrator.cancel_check = (
            thread.isInterruptionRequested
        )

        progress_dialog.cancel_requested.connect(
            thread.requestInterruption
        )

        worker.moveToThread(
            thread
        )

        error_state = {
            "kind": None,
            "message": None,
        }

        cancel_state = {
            "cancelled": False
        }

        def store_cancelled():

            cancel_state["cancelled"] = True
    
        def store_error(
            kind,
            message
        ):

            error_state["kind"] = kind
            error_state["message"] = message

        thread.started.connect(
            worker.run
        )

        worker.progress.connect(
            progress_dialog.update_progress
        )

        worker.checkpoint.connect(
            self.refresh_text_workspace
        )

        worker.failed.connect(
            store_error
        )

        worker.finished.connect(
            thread.quit
        )

        worker.finished.connect(
            progress_dialog.complete
        )

        worker.finished.connect(
            worker.deleteLater
        )

        worker.cancelled.connect(
            store_cancelled
        )

        def finish_transform():

            # ---------------------------------------------------------
            # COPY RUN / PROVENANCE STATE BACK
            # ---------------------------------------------------------

            if cancel_state["cancelled"]:

                try:

                    project = load_project(
                        self.project_file
                    )

                    apply_project_to_text(
                        project,
                        self.text
                    )

                except Exception as exc:

                    QMessageBox.critical(
                        self,
                        "Could Not Restore Project",
                        str(exc)
                    )

            else:

                if self.orchestrator is not None:

                    self.text.yiding_runs = (
                        self.orchestrator.runs
                    )

                    self.text.yiding_provenance = (
                        self.orchestrator.provenance
                    )
        
            # ---------------------------------------------------------
            # ERROR MESSAGE
            # ---------------------------------------------------------

            if error_state["message"]:

                if (
                    error_state["kind"]
                    == "unavailable"
                ):

                    QMessageBox.warning(
                        self,
                        "Transformation Not Yet Available",
                        error_state["message"],
                    )

                else:

                    QMessageBox.critical(
                        self,
                        "Transformation Error",
                        error_state["message"],
                    )

            # ---------------------------------------------------------
            # REFRESH GUI
            # ---------------------------------------------------------

            self.refresh_text_workspace()
            self.refresh_transform_buttons()
            self.refresh_glossary_buttons()

            # ---------------------------------------------------------
            # CLEAN UP ACTIVE TRANSFORM REFERENCES
            # ---------------------------------------------------------

            self.transform_thread = None
            self.transform_worker = None
            self.transform_progress_dialog = None


        thread.finished.connect(
            finish_transform
        )

        thread.finished.connect(
            thread.deleteLater
        )

        thread.start()

        progress_dialog.show()


# ---------------------------------------------------------

