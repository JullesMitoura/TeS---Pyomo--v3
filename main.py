import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QStackedWidget, QFrame
from PyQt6.QtGui import QFont
from app.screens.initial import InitialScreen
from app.screens.ming import MinG
from app.screens.maxs import MaxS
from app.screens.elv import ELVScreen
from app.screens.buttons import Button

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Thermodynamic Equilibrium Simulation 🌡️")
        self.setFixedSize(800, 800)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.central_widget.setStyleSheet("background-color: white;")

        self.main_layout = QVBoxLayout(self.central_widget)
        self.button_layout = QHBoxLayout()

        button_manager = Button()
        
        self.btn_initial = QPushButton("Initial")
        self.btn_ming = QPushButton("Gibbs Energy Minimization")
        self.btn_maxs = QPushButton("Entropy Maximization")
        self.btn_elv = QPushButton("ELV")

        self.btn_initial.setStyleSheet(button_manager.css())
        self.btn_ming.setStyleSheet(button_manager.css())
        self.btn_maxs.setStyleSheet(button_manager.css())
        self.btn_elv.setStyleSheet(button_manager.css())

        self.button_layout.addWidget(self.btn_initial)
        self.button_layout.addWidget(self.btn_ming)
        self.button_layout.addWidget(self.btn_maxs)
        self.button_layout.addWidget(self.btn_elv)

        self.main_layout.addLayout(self.button_layout)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        self.main_layout.addWidget(line)

        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)

        self.initial_screen = InitialScreen()
        self.ming_screen = MinG()
        self.maxs_screen = MaxS()
        self.elv_screen = ELVScreen()

        self.stacked_widget.addWidget(self.initial_screen)
        self.stacked_widget.addWidget(self.ming_screen)
        self.stacked_widget.addWidget(self.maxs_screen)
        self.stacked_widget.addWidget(self.elv_screen)

        self.btn_initial.clicked.connect(lambda: self.set_active_button(self.btn_initial, self.initial_screen))
        self.btn_ming.clicked.connect(lambda: self.set_active_button(self.btn_ming, self.ming_screen))
        self.btn_maxs.clicked.connect(lambda: self.set_active_button(self.btn_maxs, self.maxs_screen))
        self.btn_elv.clicked.connect(lambda: self.set_active_button(self.btn_elv, self.elv_screen))

        self.active_button = None

    def set_active_button(self, button, screen):
        if self.active_button:
            self.active_button.setFont(QFont())
            self.active_button.setStyleSheet(self.active_button.styleSheet().replace("font-weight: bold;", ""))
        button.setFont(QFont("", -1, QFont.Weight.Bold))
        button.setStyleSheet(button.styleSheet().replace("font-weight: normal;", "font-weight: bold;"))
        self.active_button = button
        self.stacked_widget.setCurrentWidget(screen)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())