import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFrame, QPushButton, QLabel,
    QHBoxLayout, QTableWidget, QHeaderView
)
from PyQt6.QtGui import QFont
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

class MaxS(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        label = QLabel("Project in development...")
        label.setFont(QFont("Arial", 24))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(label)
        self.setLayout(layout)