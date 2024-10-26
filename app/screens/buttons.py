from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QPushButton

class Button:
    def __init__(self):
        self.active_button = None

    @classmethod
    def css(cls):
        return """
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 10px;
                padding: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
            QPushButton:pressed {
                background-color: #a0a0a0;
            }
            QPushButton:checked {
                font-weight: bold;
                background-color: #87CEEB;
            }
        """

    def set_active_button(self, button, stacked_widget):
        if self.active_button:
            self.active_button.setFont(QFont())
            self.active_button.setStyleSheet(self.active_button.styleSheet().replace("font-weight: bold;", ""))
        
        button.setFont(QFont("", -1, QFont.Weight.Bold))
        button.setStyleSheet(button.styleSheet().replace("font-weight: normal;", "font-weight: bold;"))
        
        self.active_button = button
        stacked_widget.setCurrentWidget(button)