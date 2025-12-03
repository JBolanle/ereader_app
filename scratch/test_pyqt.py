"""Test PyQt6 basic functionality."""
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit
from PyQt6.QtGui import QFont
import sys


def main():
    app = QApplication(sys.argv)

    window = QMainWindow()
    window.setWindowTitle("E-Reader Test")
    window.setGeometry(100, 100, 800, 600)

    text_edit = QTextEdit()
    text_edit.setFont(QFont("Georgia", 12))

    # Test HTML rendering (like EPUB content)
    html_content = """
     <h1>Chapter 1: The Beginning</h1>
     <p>This is a paragraph with <b>bold</b> and <i>italic</i> text.</p>
     <p>Here's another paragraph to test rendering.</p>
     """
    text_edit.setHtml(html_content)

    window.setCentralWidget(text_edit)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
