import sys
import os
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QHBoxLayout, QFrame, QMessageBox
from PyQt6.QtGui import QPixmap, QPalette, QColor
from PyQt6.QtCore import Qt
from app.screens.buttons import Button
import subprocess
import platform

class InitialScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(255, 255, 255))
        self.setPalette(palette)

        layout = QVBoxLayout()

        image_label = QLabel()
        pixmap = QPixmap("./app/imgs/initial.png")
        scaled_pixmap = pixmap.scaled(700, 800, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        image_label.setPixmap(scaled_pixmap)
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(image_label)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        button_layout = QHBoxLayout()
        button_manager = Button()
        
        doc_button = QPushButton("Documentation")
        doc_button.setStyleSheet(button_manager.css())
        doc_button.clicked.connect(self.open_documentation)  # Conectar ao slot
        
        contact_button = QPushButton("Contact")
        contact_button.setStyleSheet(button_manager.css())
        contact_button.clicked.connect(self.show_contact_message)  # Conectar ao slot
        
        button_layout.addWidget(doc_button)
        button_layout.addWidget(contact_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def open_documentation(self):
        pdf_path = "./app/files/TeS.pdf"
        if os.path.exists(pdf_path):
            if platform.system() == "Windows":
                os.startfile(pdf_path)
            elif platform.system() == "Darwin":
                subprocess.run(["open", pdf_path])
            else:
                subprocess.run(["xdg-open", pdf_path])
        else:
            QMessageBox.warning(self, "Erro", "Arquivo TeS.pdf não encontrado.")

    def show_contact_message(self):
        try:
            with open("./app/files/msg.txt", "r") as file:
                message = file.read()
                QMessageBox.information(self, "Contact", message)
        except FileNotFoundError:
            QMessageBox.warning(self, "Erro", "Arquivo msg.txt não encontrado.")