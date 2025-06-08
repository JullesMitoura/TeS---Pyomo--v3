import sys
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFrame, QPushButton, QLabel,
    QGridLayout, QComboBox, QMessageBox, QGroupBox, QTabWidget,
    QTableWidget, QHeaderView, QHBoxLayout, QFileDialog, QTableWidgetItem
)
from PyQt6.QtGui import QPixmap, QPalette, QColor
from PyQt6.QtCore import Qt

from app.auxiliar_func.elv_solver import VLE_Model
from app.auxiliar_func.elv_plot import calculate_vle, create_vle_plot
from app.auxiliar_func.r2_score import calculate_r2
from app.find_path import resource_path

IMG_PATH = resource_path("./app/imgs/elv.png")
WINDOW_TITLE = "ELV Module – Thermodynamic Equilibrium Simulation"
WINDOW_GEOMETRY = (100, 100, 785, 650)

STYLESHEET = """
    QGroupBox {
        font-weight: bold; color: #333; border: 1px solid #ccc;
        border-radius: 8px; margin-top: 10px;
    }
    QGroupBox::title {
        subcontrol-origin: margin; subcontrol-position: top center;
        padding: 0 10px; background-color: #F8F9FA;
    }
    QLabel { color: black; font-weight: normal; }
    QLineEdit, QComboBox {
        color: black; background-color: white; border: 1px solid #aaa;
        border-radius: 5px; padding: 5px;
    }
    QComboBox QAbstractItemView {
        color: black; background-color: white;
        selection-background-color: #0078d7; selection-color: white;
    }
    QPushButton#ActionButton {
        background-color: #007BFF; color: white; font-weight: bold;
        border-radius: 5px; padding: 8px 15px; border: 1px solid #0069D9;
    }
    QPushButton#ActionButton:hover { background-color: #0069D9; }
    QPushButton#RunButton {
        background-color: #28a745; color: white; font-weight: bold;
        border-radius: 5px; padding: 8px 15px; border: 1px solid #218838; 
    }
    QPushButton#RunButton:hover { background-color: #218838; }
    
    QPushButton#SecondaryButton {
        background-color: #E9ECEF; color: #212529; font-weight: bold;
        border-radius: 5px; padding: 8px 15px; border: 1px solid #CED4DA;
    }
    QPushButton#SecondaryButton:hover { background-color: #DEE2E6; }
    QPushButton#SecondaryButton:pressed { background-color: #CED4DA; }

    /* --- ESTILOS ADICIONADOS PARA A CAIXA DE MENSAGEM --- */
    QMessageBox {
        background-color: #F8F9FA; /* Fundo igual ao da janela principal */
    }
    /* Garante que o texto da mensagem seja preto */
    QMessageBox QLabel {
        color: black;
        font-size: 13px;
    }
    QMessageBox QPushButton {
        background-color: #E1E1E1; 
        color: black;             
        border: 1px solid #ADADAD;
        padding: 5px 20px;         
        border-radius: 3px;
        min-width: 80px;          
    }
    QMessageBox QPushButton:hover {
        background-color: #D1D1D1;
    }
    QMessageBox QPushButton:pressed {
        background-color: #C0C0C0;
    }
"""
class ELVScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.experimental_data = None
        self.component_properties = None
        self.calculated_data = None
        self.kij = None
        self.current_plot = None
        self.init_ui()

    def init_ui(self):
        # ... (sem alterações) ...
        self.setWindowTitle(WINDOW_TITLE)
        self.setFixedSize(WINDOW_GEOMETRY[2], WINDOW_GEOMETRY[3])
        self.move(WINDOW_GEOMETRY[0], WINDOW_GEOMETRY[1])
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#F8F9FA"))
        self.setPalette(palette)
        self.setStyleSheet(STYLESHEET)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 10, 15, 15)
        main_layout.setSpacing(5)
        main_layout.addWidget(self.create_header_section())
        main_layout.addWidget(self.create_controls_section())
        main_layout.addWidget(self.create_output_section())
        main_layout.addStretch()

    def display_plot(self, fig):
        # ... (sem alterações) ...
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        self.current_plot = QPixmap()
        self.current_plot.loadFromData(buf.getvalue())
        self.graph_label.setPixmap(self.current_plot)
        plt.close(fig)

    def create_header_section(self):
        # ... (sem alterações) ...
        header_frame = QFrame()
        layout = QVBoxLayout(header_frame)
        layout.setContentsMargins(0, 0, 0, 0)
        image_label = QLabel()
        try:
            pixmap = QPixmap(IMG_PATH)
            scaled_pixmap = pixmap.scaledToWidth(200, Qt.TransformationMode.SmoothTransformation)
            image_label.setPixmap(scaled_pixmap)
        except Exception as e:
            image_label.setText(f"Erro ao carregar imagem: {IMG_PATH}\n{e}")
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(image_label)
        return header_frame
    
    def create_controls_section(self):
        # ... (sem alterações) ...
        controls_groupbox = QGroupBox("Controls and Configuration")
        main_hbox = QHBoxLayout(controls_groupbox)
        main_hbox.setSpacing(20)
        buttons_vbox = QVBoxLayout()
        buttons_vbox.setSpacing(10)
        load_data_button = QPushButton("Load Data")
        load_data_button.setObjectName("ActionButton")
        load_data_button.clicked.connect(self.load_data_from_file)
        run_simulation_button = QPushButton("Run Simulation")
        run_simulation_button.setObjectName("RunButton")
        run_simulation_button.clicked.connect(self.run_simulation)
        buttons_vbox.addWidget(load_data_button)
        buttons_vbox.addWidget(run_simulation_button)
        buttons_vbox.addStretch()
        config_grid = QGridLayout()
        config_grid.setSpacing(10)
        config_grid.addWidget(QLabel("System Type:"), 0, 0)
        self.system_type_combobox = QComboBox()
        self.system_type_combobox.addItems(["Isothermal", "Isobaric"])
        config_grid.addWidget(self.system_type_combobox, 0, 1)
        config_grid.addWidget(QLabel("EoS:"), 1, 0)
        self.eos_combobox = QComboBox()
        self.eos_combobox.addItems(['Peng-Robinson', 'Soave-Redlich-Kwong', 'Redlich-Kwong'])
        config_grid.addWidget(self.eos_combobox, 1, 1)
        config_grid.setColumnStretch(1, 1)
        main_hbox.addLayout(buttons_vbox, 1)
        main_hbox.addLayout(config_grid, 2)
        return controls_groupbox

    def create_output_section(self):
        # --- MÉTODO MODIFICADO ---
        output_groupbox = QGroupBox("Results")
        output_layout = QVBoxLayout(output_groupbox)
        output_layout.setContentsMargins(5, 10, 5, 5)

        self.graph_label = QLabel("Execute a simulação para gerar o gráfico.")
        self.graph_label.setScaledContents(True)
        self.graph_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.graph_label.setMinimumHeight(300)
        self.graph_label.setStyleSheet("color: #888; font-style: italic;")
        output_layout.addWidget(self.graph_label)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        output_layout.addWidget(separator)

        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 5, 0, 0)
        
        self.r2_vapor_label = QLabel("<b>R² (Vapor):</b> --")
        self.kij_label = QLabel("<b>kij:</b> --")
        
        self.save_plot_button = QPushButton("Salvar Gráfico")
        self.save_data_button = QPushButton("Salvar Dados")

        # --- ADICIONADO: Aplica o novo estilo aos botões ---
        self.save_plot_button.setObjectName("SecondaryButton")
        self.save_data_button.setObjectName("SecondaryButton")
        
        self.save_plot_button.setEnabled(False)
        self.save_data_button.setEnabled(False)
        self.save_plot_button.clicked.connect(self.save_plot)
        self.save_data_button.clicked.connect(self.save_data)
        
        footer_layout.addWidget(self.r2_vapor_label)
        footer_layout.addWidget(self.kij_label)
        footer_layout.addStretch()
        footer_layout.addWidget(self.save_plot_button)
        footer_layout.addWidget(self.save_data_button)
        
        output_layout.addLayout(footer_layout)
        output_groupbox.setLayout(output_layout)
        return output_groupbox

    def load_data_from_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Selecionar Arquivo de Dados", "", "Excel Files (*.xlsx *.xls)")
        if path:
            try:
                self.experimental_data = pd.read_excel(path, sheet_name=0)
                props_df = pd.read_excel(path, sheet_name=1, index_col=0)
                self.component_properties = {index: row.tolist() for index, row in props_df.iterrows()}
            except Exception as e:
                self.experimental_data = None; self.component_properties = None
                QMessageBox.critical(self, "Erro de Leitura", f"Não foi possível ler o arquivo.\n\nErro: {e}")

    def save_plot(self):
        if self.current_plot is None or self.current_plot.isNull():
            QMessageBox.warning(self, "Sem Gráfico", "Execute uma simulação para gerar um gráfico antes de salvar.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Salvar Gráfico", "", "PNG Image (*.png);;JPEG Image (*.jpg)")
        if path:
            if self.current_plot.save(path):
                QMessageBox.information(self, "Sucesso", f"Gráfico salvo em:\n{path}")
            else:
                QMessageBox.critical(self, "Erro ao Salvar", "Não foi possível salvar a imagem.")

    def save_data(self):
        if self.calculated_data is None:
            QMessageBox.warning(self, "Sem Dados", "Execute uma simulação para gerar os dados antes de salvar.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Salvar Dados Calculados", "", "Excel Files (*.xlsx)")
        if path:
            try:
                final_df = self.experimental_data.join(self.calculated_data)
                final_df['kij'] = self.kij
                final_df.to_excel(path, index=False, sheet_name="Resultados_Calculados")
                QMessageBox.information(self, "Sucesso", f"Dados salvos em:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Erro ao Salvar", f"Não foi possível salvar o arquivo.\n\nErro: {e}")

    def run_simulation(self):
        if self.experimental_data is None:
            QMessageBox.warning(self, "Dados Ausentes", "Por favor, carregue um arquivo de dados antes.")
            return
        system_type = self.system_type_combobox.currentText()
        eos_model_name = self.eos_combobox.currentText()
        components = list(self.component_properties.keys())
        self.r2_vapor_label.setText("<b>R² (Vapor):</b> --")
        self.kij_label.setText("<b>kij:</b> --")
        self.save_plot_button.setEnabled(False)
        self.save_data_button.setEnabled(False)
        try:
            model = VLE_Model(component_props=self.component_properties, components=components, eos_name=eos_model_name)
            self.kij = model.run(experimental_data=self.experimental_data, mode=system_type.lower())
            self.calculated_data = calculate_vle(model=model, experimental_data=self.experimental_data, kij=self.kij, mode=system_type.lower())
            r2_vapor = calculate_r2(self.experimental_data['y1'], self.calculated_data['y1_calc'])
            self.r2_vapor_label.setText(f"<b>R² (Vapor):</b> {r2_vapor:.4f}" if pd.notna(r2_vapor) else "<b>R² (Vapor):</b> --")
            self.kij_label.setText(f"<b>kij:</b> {self.kij:.4f}" if pd.notna(self.kij) else "<b>kij:</b> --")
            fig = create_vle_plot(components=components, experimental_data=self.experimental_data, calculated_data=self.calculated_data, kij=self.kij, eos_name=eos_model_name, mode=system_type.lower())
            self.display_plot(fig)
            self.save_plot_button.setEnabled(True)
            self.save_data_button.setEnabled(True)
            QMessageBox.information(self, "Cálculo Concluído", "A simulação foi executada com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro na Simulação", f"Ocorreu um erro ao executar os cálculos.\n\nErro: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    screen = ELVScreen()
    screen.show()
    sys.exit(app.exec())