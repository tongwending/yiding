# ------------------------------------------------------------------------------------
# transform_progress_dialog
# ------------------------------------------------------------------------------------

from PySide6.QtCore import (
    QObject,
    Signal,
    Slot,
)

from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
)

from ..workflow_orchestrator import (
    TransformCancelled
)

# ------------------------------------------------------------------------------------

class TransformWorker(QObject):

    progress = Signal(dict)

    failed = Signal(
        str,
        str,
    )

    cancelled = Signal()
    finished = Signal()
    checkpoint = Signal()


    def __init__(
        self,
        orchestrator,
        operation
    ):

        super().__init__()

        self.orchestrator = orchestrator
        self.operation = operation

        self.orchestrator.progress_callback = (
            self.progress.emit
        )
        self.orchestrator.checkpoint_callback = (
            self.checkpoint.emit
        )


    @Slot()
    def run(self):

        try:

            if self.operation == "punctuation":

                self.orchestrator.resume_punctuation()

            elif self.operation == "translation":

                self.orchestrator.resume_translation()

            elif self.operation == "punctuation_translation":

                self.orchestrator.resume_punctuation()
                self.orchestrator._check_for_cancellation()
                self.orchestrator.resume_translation()

            elif self.operation == "term_extraction":

                self.orchestrator.resume_term_extraction()

            elif self.operation == "glossary_extraction":

                self.orchestrator.resume_glossary_extraction()

            else:

                raise ValueError(
                    f"Unknown transformation: "
                    f"{self.operation}"
                )
            
        except TransformCancelled:

            self.cancelled.emit()
    
        except AttributeError as exc:

            self.failed.emit(
                "unavailable",
                str(exc),
            )

        except Exception as exc:

            self.failed.emit(
                "error",
                str(exc),
            )

        finally:

            self.finished.emit()


class TransformProgressDialog(QDialog):

    cancel_requested = Signal()
    
    def __init__(
        self,
        operation,
        settings,
        text,
        parent=None
    ):

        super().__init__(parent)

        self.running = True

        self.progress_labels = {}
        self.progress_bars = {}

        self.cross_labels = {}
        self.cross_bars = {}

        self.setModal(False)
        self.setMinimumWidth(440)

        title_names = {
            "punctuation":
                "Punctuation Progress",

            "translation":
                "Translation Progress",

            "punctuation_translation":
                "Transformation Progress",

            "term_extraction":
                "Term Extraction Progress",

            "glossary_extraction":
                "Glossary Extraction Progress",
        }

        self.setWindowTitle(
            title_names.get(
                operation,
                "Transformation Progress"
            )
        )

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            20, 20, 20, 20
        )

        layout.setSpacing(10)

        # -----------------------------------------------------
        # WHICH SECTIONS ARE NEEDED?
        # -----------------------------------------------------

        phases = []

        if operation == "punctuation":

            phases.append(
                "punctuation"
            )

        elif operation == "translation":

            # Translation currently punctuates first if needed.
            if not text.is_punctuated:
                phases.append(
                    "punctuation"
                )

            phases.append(
                "translation"
            )

        elif operation == "punctuation_translation":

            phases.extend([
                "punctuation",
                "translation",
            ])

        elif operation == "term_extraction":

            phases.append(
                "term_extraction"
            )

        elif operation == "glossary_extraction":

            phases.append(
                "glossary_extraction"
            )

        # -----------------------------------------------------
        # BUILD SECTIONS
        # -----------------------------------------------------

        for index, phase in enumerate(phases):

            if index > 0:

                separator = QFrame()

                separator.setFrameShape(
                    QFrame.HLine
                )

                separator.setFrameShadow(
                    QFrame.Plain
                )

                layout.addSpacing(8)
                layout.addWidget(separator)
                layout.addSpacing(8)

            cross_check = False

            if phase == "punctuation":

                heading = (
                    "PUNCTUATION PROGRESS"
                )

                cross_check = bool(
                    settings[
                        "punctuation"
                    ]["cross_check"]["enabled"]
                )

            elif phase == "translation":

                heading = (
                    "TRANSLATION PROGRESS"
                )

                cross_check = bool(
                    settings[
                        "translation"
                    ]["cross_check"]["enabled"]
                )

            elif phase == "term_extraction":

                heading = (
                    "TERM EXTRACTION PROGRESS"
                )

            else:

                heading = (
                    "GLOSSARY EXTRACTION PROGRESS"
                )

            heading_label = QLabel(
                heading
            )

            heading_label.setStyleSheet(
                "font-weight: bold;"
            )

            layout.addWidget(
                heading_label
            )

            progress_label = QLabel(
                self._waiting_text(
                    phase
                )
            )

            progress_bar = QProgressBar()

            progress_bar.setFixedHeight(40)

            progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #c9c5bc;
                    border-radius: 6px;
                    background-color: #eeeae1;
                }

                QProgressBar::chunk {
                    background-color: #681708;
                    border-radius: 5px;
                }
            """)

            progress_bar.setRange(
                0, 1
            )

            progress_bar.setValue(0)

            progress_bar.setTextVisible(
                False
            )

            self.progress_labels[
                phase
            ] = progress_label

            self.progress_bars[
                phase
            ] = progress_bar

            layout.addWidget(
                progress_label
            )

            layout.addWidget(
                progress_bar
            )

            if cross_check:

                cross_label = QLabel(
                    "Cross-check: waiting"
                )

                cross_bar = QProgressBar()

                cross_bar.setFixedHeight(20)

                cross_bar.setStyleSheet("""
                    QProgressBar {
                        border: 1px solid #c9c5bc;
                        border-radius: 5px;
                        background-color: #eeeae1;
                    }

                    QProgressBar::chunk {
                        background-color: #681708;
                        border-radius: 4px;
                    }
                """)

                cross_bar.setRange(
                    0, 1
                )

                cross_bar.setValue(0)

                cross_bar.setTextVisible(
                    False
                )

                self.cross_labels[
                    phase
                ] = cross_label

                self.cross_bars[
                    phase
                ] = cross_bar

                layout.addSpacing(4)

                layout.addWidget(
                    cross_label
                )

                layout.addWidget(
                    cross_bar
                )
                
        # -----------------------------------------------------
        # CANCEL TRANSFORMATION
        # -----------------------------------------------------

        button_row = QHBoxLayout()

        button_row.addStretch()

        self.cancel_button = QPushButton(
            "Cancel"
        )

        self.cancel_button.clicked.connect(
            self.request_cancel
        )

        button_row.addWidget(
            self.cancel_button
        )

        layout.addSpacing(8)

        layout.addLayout(
            button_row
        )


    def _waiting_text(
        self,
        phase
    ):

        names = {
            "punctuation":
                "Punctuation: waiting",

            "translation":
                "Translation: waiting",

            "term_extraction":
                "Extracting terms: waiting",

            "glossary_extraction":
                "Extracting glossary: waiting",
        }

        return names[phase]


    def _progress_text(
        self,
        phase,
        current,
        total
    ):

        names = {
            "punctuation":
                "Punctuation",

            "translation":
                "Translation",

            "term_extraction":
                "Extracting terms",

            "glossary_extraction":
                "Extracting glossary",
        }

        return (
            f"{names[phase]}: "
            f"{current} / {total}"
        )


    @Slot(dict)
    def update_progress(
        self,
        data
    ):

        phase = data["phase"]

        # -----------------------------------------------------
        # TITLE TRANSLATION
        # -----------------------------------------------------

        if phase == "translation_title":

            label = self.progress_labels[
                "translation"
            ]

            bar = self.progress_bars[
                "translation"
            ]

            label.setText(
                "Translating title"
            )

            # Indeterminate / moving bar because
            # an LLM request has no measurable percentage.
            bar.setRange(
                0, 0
            )

            return

        # -----------------------------------------------------
        # MAIN PROGRESS
        # -----------------------------------------------------

        if phase in self.progress_bars:

            current = data["current"]
            total = data["total"]

            bar = self.progress_bars[
                phase
            ]

            label = self.progress_labels[
                phase
            ]

            label.setText(
                self._progress_text(
                    phase,
                    current,
                    total,
                )
            )

            if total > 0:

                bar.setRange(
                    0,
                    total
                )

                bar.setValue(
                    min(
                        current,
                        total
                    )
                )

            else:

                bar.setRange(
                    0, 1
                )

                bar.setValue(0)

            return

        # -----------------------------------------------------
        # CROSS-CHECK PROGRESS
        # -----------------------------------------------------

        cross_phases = {
            "punctuation_cross_check":
                "punctuation",

            "translation_cross_check":
                "translation",
        }

        parent_phase = (
            cross_phases.get(
                phase
            )
        )

        if (
            parent_phase is None
            or parent_phase
            not in self.cross_bars
        ):
            return

        current = data["current"]
        total = data["total"]
        segment = data["segment"]

        label = self.cross_labels[
            parent_phase
        ]

        bar = self.cross_bars[
            parent_phase
        ]

        label.setText(
            f"Cross-checking segment "
            f"{segment}: "
            f"{current} / {total}"
        )

        if total > 0:

            bar.setRange(
                0,
                total
            )

            bar.setValue(
                min(
                    current,
                    total
                )
            )

        else:

            bar.setRange(
                0, 1
            )

            bar.setValue(0)


    @Slot()
    def request_cancel(self):

        if not self.running:
            return

        self.cancel_button.setEnabled(
            False
        )

        self.cancel_button.setText(
            "Cancelling..."
        )

        self.cancel_requested.emit()
        

    @Slot()
    def complete(self):

        self.running = False
        self.accept()


    def closeEvent(
        self,
        event
    ):

        if self.running:

            event.ignore()
            return

        super().closeEvent(
            event
        )
