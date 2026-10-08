# ------------------------------------------------------------------------------------------
# app
# ------------------------------------------------------------------------------------------

import sys
import ctypes
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen


def main():

    if sys.platform == "win32":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "yiding.desktop.app"
        )

    app = QApplication(sys.argv)

    # ---------------------------------------------------------
    # APP ICON
    # ---------------------------------------------------------

    icon_path = (
        Path(__file__).parent
        / "assets"
        / "app_icon.png"
    )

    app.setWindowIcon(
        QIcon(str(icon_path))
    )

    # ---------------------------------------------------------
    # SPLASH SCREEN
    # ---------------------------------------------------------

    logo_path = (
        Path(__file__).parent
        / "assets"
        / "logo_solid.png"
    )

    pixmap = QPixmap(str(logo_path))

    pixmap = pixmap.scaledToWidth(
        220,
        Qt.SmoothTransformation
    )

    splash = QSplashScreen(pixmap)
    splash.show()

    # Make sure the splash appears immediately.
    app.processEvents()

    # ---------------------------------------------------------
    # LOAD MAIN WINDOW
    # ---------------------------------------------------------

    # Import this only AFTER the splash is visible.
    from .main_window import MainWindow

    window = MainWindow()
    window.show()

    # Remove splash as soon as the GUI is ready.
    splash.finish(window)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
