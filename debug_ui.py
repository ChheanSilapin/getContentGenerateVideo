#!/usr/bin/env python3
"""
Debug script to test UI loading
"""
import sys
from PySide6.QtWidgets import QApplication, QDialog
from ui import Ui_dialog

class TestDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_dialog()
        self.ui.setupUi(self)

if __name__ == "__main__":
    print("Starting UI test...")
    app = QApplication(sys.argv)
    window = TestDialog()
    print("UI loaded successfully")
    window.show()
    sys.exit(app.exec())