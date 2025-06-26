import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFrame, QPushButton, QLabel,
    QHBoxLayout, QTableWidget, QHeaderView, QFileDialog, QTableWidgetItem,
    QScrollArea, QGridLayout, QLineEdit, QComboBox, QMessageBox
)
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt
from app.auxiliar_func.read_data import ReadData
from app.auxiliar_func.run_entropy import RunEntropy
from app.screens.entropy_aux.section03 import Section3
from app.screens.entropy_aux.section04 import Section4
from app.find_path import resource_path

class MaxS(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
    
        self.table = None
        layout.addWidget(self.create_section1())
        layout.addWidget(self.create_separator())
        layout.addWidget(self.create_section2())
        layout.addWidget(self.create_separator())

        # Initialize section3_container with a layout
        self.section3 = None  
        self.section3_container = QFrame()
        self.section3_container.setFixedHeight(210)
        section3_layout = QVBoxLayout()
        self.section3_container.setLayout(section3_layout)

        # Adiciona o container ao layout principal
        layout.addWidget(self.section3_container)

        layout.addWidget(self.create_separator())
        
        self.section4 = None  
        self.section4_container = QFrame()
        self.section4_container.setFixedHeight(200)
        section4_layout = QVBoxLayout()
        self.section4_container.setLayout(section4_layout)
        layout.addWidget(self.section4_container)

        self.setLayout(layout)
        self.setWindowTitle("TeSScreen")
        self.setGeometry(100, 100, 700, 700)

        self.file_path = ""
        self.document = None
        self.dataframe = None
        self.data = None
        self.species = None 
        self.initial = None
        self.components = []


        self.tmin = None
        self.tmax = None
        self.pmin = None
        self.pmax = None
        self.reference_componente = None
        self.reference_componente_min = None
        self.reference_componente_max= None
        self.n_temperature = 0
        self.n_pressure = 0
        self.n_component_values = 0
        self.state_equation = None
        self.total_simulations = None
        self.results = None
        

    def collect_input_values(self):
        missing_fields = []

        if not self.max_temp_input.text():
            missing_fields.append("Max. Temperature")
        else:
            self.tmax = float(self.max_temp_input.text())

        if not self.min_temp_input.text():
            missing_fields.append("Min. Temperature")
        else:
            self.tmin = float(self.min_temp_input.text())

        if not self.max_pressure_input.text():
            missing_fields.append("Max. Pressure")
        else:
            self.pmax = float(self.max_pressure_input.text())

        if not self.min_pressure_input.text():
            missing_fields.append("Min. Pressure")
        else:
            self.pmin = float(self.min_pressure_input.text())

        if not self.n_values_t_input.text():
            missing_fields.append("N. Values T")
        else:
            self.n_temperature = int(self.n_values_t_input.text())

        if not self.n_values_p_input.text():
            missing_fields.append("N. Values P")
        else:
            self.n_pressure = int(self.n_values_p_input.text())

        # Verificações para reference_componente_min, reference_componente_max e n_component_values
        if not self.min_value_input.text():
            missing_fields.append("Min. Value (Reference Component)")
        else:
            self.reference_componente_min = float(self.min_value_input.text())

        if not self.max_value_input.text():
            missing_fields.append("Max. Value (Reference Component)")
        else:
            self.reference_componente_max = float(self.max_value_input.text())

        if not self.n_values_n_input.text():
            missing_fields.append("N. Values n (Reference Component)")
        else:
            self.n_component_values = int(self.n_values_n_input.text())

        self.reference_componente = self.component_combobox.currentText()
        self.inhibit_component = self.inhibit_component_combox.currentText()
        self.state_equation = self.state_equation_combobox.currentText()
        self.total_simulations = self.n_temperature * self.n_pressure * self.n_component_values

        if missing_fields:
            text = "\n".join(f" * {field}" for field in missing_fields)
            QMessageBox.warning(self, "Input Error", f"Please fill in the following fields:\n{text}")
            return False
        else:
            return True
    
    def show_section3(self, results, components, reference_componente):
        if self.section3:
            self.section3_container.layout().removeWidget(self.section3)
            self.section3.deleteLater()

        self.section3 = Section3(results, components, reference_componente)
        self.section3.setMaximumHeight(175)
        self.section3_container.layout().addWidget(self.section3)
        self.section3.setVisible(True)

    def run_entropy(self):
        if self.collect_input_values():
            entropy = RunEntropy(data=self.data, species=self.species, initial=self.initial, 
                                 components=self.components, Tmin=self.tmin, Tmax=self.tmax,
                                 Pmin=self.pmin, Pmax=self.pmax, nT=self.n_temperature, nP=self.n_pressure, 
                                 reference_componente=self.reference_componente, reference_componente_min=self.reference_componente_min, 
                                 reference_componente_max=self.reference_componente_max, n_reference_componente=self.n_component_values, 
                                 inhibit_component=self.inhibit_component, state_equation=self.state_equation)
            
            self.results = entropy.run_entropy()

            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setWindowTitle("Simulation Complete")
            msg_box.setText("The Entropy simulation has been successfully completed!")
            msg_box.setStyleSheet("""
                                  QLabel { 
                                      color: black; 
                                  }
                                  QPushButton { 
                                      color: black;
                                      background-color: #E1E1E1;
                                      border: 1px solid #ADADAD;
                                      padding: 5px 15px;
                                      border-radius: 3px;
                                  }
                                  QPushButton:hover {
                                      background-color: #F0F0F0;
                                  }
                                  QPushButton:pressed {
                                      background-color: #C0C0C0;
                                  }
                                  """)
            msg_box.exec()
            self.show_section3(self.results, self.components, self.reference_componente)

            if self.section4 is not None:
                for i in reversed(range(self.section4_container.layout().count())): 
                    widget = self.section4_container.layout().itemAt(i).widget()
                    if widget is not None: 
                        widget.deleteLater()

            self.section4 = Section4(self.results, self.components)
            self.section4_container.layout().addWidget(self.section4)
            self.section4.setVisible(True)
        else:
            print("Simulation aborted due to missing input fields.")

    def create_separator(self):
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        return separator

    def create_section1(self):
        
        section = QFrame()
        section.setFixedHeight(125)
        section_layout = QHBoxLayout()

        # Coluna 1: Botões
        column1_layout = QVBoxLayout()
        
        button1 = QPushButton("Open File")
        button1.setFixedSize(130, 30)
        button1.setStyleSheet("""
            QPushButton {
                border-radius: 10px;
                background-color: white; 
                color: black;  
                padding: 5px;
                border: 1px solid black; 
            }
            QPushButton:hover {
                background-color: #e0e0e0; 
            }
            QPushButton:pressed {
                background-color: #0056b3;  
                color: white;  
            }
        """)
        button1.clicked.connect(self.open_file_dialog)
        
        button2 = QPushButton("Run Simulation")
        button2.setFixedSize(130, 30)
        button2.setStyleSheet("""
            QPushButton {
                border-radius: 10px;
                background-color: #28a745; 
                color: white;  
                padding: 5px;
                border: 1px solid #218838; 
            }
            QPushButton:hover {
                background-color: #e0e0e0; 
            }
            QPushButton:pressed {
                background-color: #218838;  
                color: white;  
            }
        """)
        button2.clicked.connect(self.collect_input_values)
        button2.clicked.connect(self.run_entropy)

        
        column1_layout.addWidget(button1, alignment=Qt.AlignmentFlag.AlignLeft)
        column1_layout.addWidget(button2, alignment=Qt.AlignmentFlag.AlignLeft)

        column2_layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Component", "Initial (mols)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setRowCount(0)

        header_font = QFont()
        header_font.setBold(True)
        header_font.setPointSize(10)
        self.table.horizontalHeader().setStyleSheet("background-color: #3f51b5;")
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid black;
                background-color: #f5f5f5;
                gridline-color: black;
                font-size: 10px;
            }
            QTableWidget::item {
                border: 1px solid black;
                padding: 5px;
                color: #333;
            }
            QTableWidget::item:selected {
                background-color: #d4e157;
                color: black;
            }
            QHeaderView::section {
                background-color: #3f51b5;
                color: white;
                border: 1px solid black;
                padding: 5px;
                font-weight: bold;
                font-size: 10px;
            }
            QTableCornerButton::section {
                background-color: #3f51b5;
            }
        """)
        self.table.horizontalHeader().setFixedHeight(20)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFixedSize(400, 110)
        scroll_area.setWidget(self.table)
        column2_layout.addWidget(scroll_area, alignment=Qt.AlignmentFlag.AlignCenter)

        column3_layout = QVBoxLayout()
        image_label = QLabel()
        pixmap = QPixmap(resource_path("app/imgs/maxS.png"))
        image_label.setPixmap(pixmap.scaled(150, 130, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        column3_layout.addWidget(image_label, alignment=Qt.AlignmentFlag.AlignCenter)

        section_layout.addLayout(column1_layout)
        section_layout.addLayout(column2_layout)
        section_layout.addLayout(column3_layout)

        section.setLayout(section_layout)
        return section

    def open_file_dialog(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, 
            "Open File", 
            "", 
            "CSV Files (*.csv);;Excel Files (*.xlsx; *.xls);;Text Files (*.txt);;All Files (*)"
        )
        if file_name:
            self.file_path = file_name
            self.document = ReadData(file_name)
            self.dataframe = self.document.data
            self.data, self.species, self.initial, self.components = self.document.get_infos()
            self.populate_table()
            
            self.component_combobox.addItem("---")
            self.component_combobox.addItems(self.components)
            self.inhibit_component_combox.addItem("---")
            self.inhibit_component_combox.addItems(self.components)
            self.component_combobox.setEnabled(True)
            self.inhibit_component_combox.setEnabled(True)
            self.state_equation_combobox.setEnabled(True)

    def populate_table(self):
        self.table.setRowCount(len(self.dataframe))

        for row in range(len(self.dataframe)):
            component_item = QTableWidgetItem(self.dataframe['Component'].iloc[row])
            initial_item = QTableWidgetItem(str(self.dataframe['initial'].iloc[row]))
            
            self.table.setItem(row, 0, component_item)
            self.table.setItem(row, 1, initial_item)

    def create_section2(self):
        section = QFrame()
        section.setFixedHeight(190)
        section_layout = QVBoxLayout()
        grid_layout = QGridLayout()

        line_edit_style = """
            QLineEdit {
                color: black;
                background-color: white;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 2px;
            }
        """

        grid_layout.addWidget(QLabel("Max. Temperature:"), 0, 0)
        self.max_temp_input = QLineEdit()
        self.max_temp_input.setStyleSheet(line_edit_style)
        grid_layout.addWidget(self.max_temp_input, 0, 1)

        grid_layout.addWidget(QLabel("Min. Temperature:"), 1, 0)
        self.min_temp_input = QLineEdit()
        self.min_temp_input.setStyleSheet(line_edit_style)
        grid_layout.addWidget(self.min_temp_input, 1, 1)

        grid_layout.addWidget(QLabel("Max. Pressure:"), 2, 0)
        self.max_pressure_input = QLineEdit()
        self.max_pressure_input.setStyleSheet(line_edit_style)
        grid_layout.addWidget(self.max_pressure_input, 2, 1)

        grid_layout.addWidget(QLabel("Min. Pressure:"), 3, 0)
        self.min_pressure_input = QLineEdit()
        self.min_pressure_input.setStyleSheet(line_edit_style)
        grid_layout.addWidget(self.min_pressure_input, 3, 1)

        grid_layout.addWidget(QLabel("Select a Component:"), 4, 0)
        self.component_combobox = QComboBox()

        self.component_combobox.setEnabled(False)
        self.component_combobox.setStyleSheet("""
        QComboBox {
            border: 1px solid black; border-radius: 5px; color: black;
            background-color: white; padding-left: 5px; font-size: 12px;
        }
        QComboBox QAbstractItemView {
            color: black; background-color: white;
            selection-background-color: lightgray; selection-color: black;
        }
        QComboBox::drop-down { border-radius: 5px; }
        QComboBox::item { color: black; }
        """)
        grid_layout.addWidget(self.component_combobox, 4, 1)


        grid_layout.addWidget(QLabel("Max. Value:"), 5, 0)
        self.max_value_input = QLineEdit()
        self.max_value_input.setStyleSheet(line_edit_style)
        grid_layout.addWidget(self.max_value_input, 5, 1)

        grid_layout.addWidget(QLabel("Min. Value:"), 6, 0)
        self.min_value_input = QLineEdit()
        self.min_value_input.setStyleSheet(line_edit_style)
        grid_layout.addWidget(self.min_value_input, 6, 1)

        # Coluna 3
        grid_layout.addWidget(QLabel("N. Values T:"), 0, 2)
        self.n_values_t_input = QLineEdit()
        self.n_values_t_input.setStyleSheet(line_edit_style)
        grid_layout.addWidget(self.n_values_t_input, 0, 3)

        grid_layout.addWidget(QLabel("N. Values P:"), 1, 2)
        self.n_values_p_input = QLineEdit()
        self.n_values_p_input.setStyleSheet(line_edit_style)
        grid_layout.addWidget(self.n_values_p_input, 1, 3)

        grid_layout.addWidget(QLabel("N. Values n:"), 2, 2)
        self.n_values_n_input = QLineEdit()
        self.n_values_n_input.setStyleSheet(line_edit_style)
        grid_layout.addWidget(self.n_values_n_input, 2, 3)

        grid_layout.addWidget(QLabel("State Equation:"), 3, 2)
        self.state_equation_combobox = QComboBox()
        self.state_equation_combobox.addItems(['Ideal Gas', 'Peng-Robinson', 'Soave-Redlich-Kwong', 'Redlich-Kwong', 'Virial'])
        self.state_equation_combobox.setStyleSheet("""
            QComboBox {
                border: 1px solid black; border-radius: 5px; color: black;
                background-color: white; padding-left: 5px; font-size: 12px;
            }
            QComboBox QAbstractItemView {
                color: black; background-color: white;
                selection-background-color: lightgray; selection-color: black;
            }
            QComboBox::drop-down { border-radius: 5px; }
            QComboBox::item { color: black; }
        """)
        grid_layout.addWidget(self.state_equation_combobox, 3, 3)

        grid_layout.addWidget(QLabel("Inhibit Component:"), 4, 2)
        self.inhibit_component_combox = QComboBox()
        self.inhibit_component_combox.setEnabled(False)
        self.inhibit_component_combox.setStyleSheet("""
            QComboBox {
                border: 1px solid black; border-radius: 5px; color: black;
                background-color: white; padding-left: 5px; font-size: 12px;
            }
            QComboBox QAbstractItemView {
                color: black; background-color: white;
                selection-background-color: lightgray; selection-color: black;
            }
            QComboBox::drop-down { border-radius: 5px; }
            QComboBox::item { color: black; }
        """)
        grid_layout.addWidget(self.inhibit_component_combox, 4, 3)


        section_layout.addLayout(grid_layout)
        section.setLayout(section_layout)

        for i in range(grid_layout.count()):
            widget = grid_layout.itemAt(i).widget()
            if isinstance(widget, QLabel):
                widget.setStyleSheet("color: black;")
        return section