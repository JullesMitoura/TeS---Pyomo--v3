from PyQt6.QtWidgets import QFrame, QVBoxLayout, QGridLayout, QLabel, QPushButton, QComboBox, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from app.graphs import plot_superficie
from app.graphs import linear_graph_maxs
from app.graphs import plot_correlation_matrix

class CheckableComboBox(QComboBox):
    def __init__(self, parent=None):
        super(CheckableComboBox, self).__init__(parent)
        self.view().pressed.connect(self.handleItemPressed)
        self.setModel(QStandardItemModel(self))
        self._set_combobox_style()

    def handleItemPressed(self, index):
        item = self.model().itemFromIndex(index)
        if item.checkState() == Qt.CheckState.Checked:
            item.setCheckState(Qt.CheckState.Unchecked)
        else:
            item.setCheckState(Qt.CheckState.Checked)

    def addItem(self, text):
        item = QStandardItem(text)
        item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
        item.setCheckState(Qt.CheckState.Unchecked)
        self.model().appendRow(item)

    def getCheckedItems(self):
        checkedItems = []
        for index in range(self.count()):
            item = self.model().item(index)
            if item.checkState() == Qt.CheckState.Checked:
                checkedItems.append(item.text())
        return checkedItems

    def _set_combobox_style(self):
        self.setStyleSheet("""
            QComboBox {
                border: 1px solid black;
                border-radius: 5px;
                padding: 1px 18px 1px 3px;
                color: black;
                background-color: white;
            }
            QComboBox QAbstractItemView {
                border: 1px solid darkgray;
                color: black;
                background-color: white;
                selection-background-color: #0078d7;
            }
            QComboBox::drop-down {
                border-radius: 5px;
            }
        """)

class Section3(QFrame):
    def __init__(self, dataframe, components, reference_componente, parent=None):
        super().__init__(parent)
        self.setMaximumHeight(180)
        self.setStyleSheet("""
            QLabel {
                color: black;
                font-size: 10px;
            }
        """)

        section_layout = QVBoxLayout()
        grid_layout = QGridLayout()

        self.surface_button = self._create_button("Surface Response", "#4CAF50", 12)
        self.surface_button.clicked.connect(lambda: self.plot_surface_response(dataframe))
        grid_layout.addWidget(self.surface_button, 0, 0, 1, 2, alignment=Qt.AlignmentFlag.AlignCenter)

        # X Value
        self.x_value_combobox = self._add_labeled_combobox(grid_layout, dataframe.columns, "X Value:", 1, 0)

        # Y Value
        self.y_value_combobox = self._add_labeled_combobox(grid_layout, dataframe.columns, "Y Value:", 2, 0)

        # Z Value
        self.z_value_combobox = self._add_labeled_combobox(grid_layout, dataframe.columns, "Z Value:", 3, 0)

        # Component
        self.component_combobox = CheckableComboBox()
        for component in components:
            self.component_combobox.addItem(component)
        grid_layout.addWidget(QLabel("Component:"), 0, 2, 1, 1)
        grid_layout.addWidget(self.component_combobox, 0, 3, 1, 4)

        # Composition Buttons
        self.composition_t_button = self._create_button("Composition T", "#2196F3", 12, row=1, col=2, layout=grid_layout)
        self.composition_t_button.clicked.connect(lambda: self.plot_linear_graphs(dataframe, reference_componente, 'T', components))

        self.composition_p_button = self._create_button("Composition P", "#2196F3", 12, row=2, col=2, layout=grid_layout)
        self.composition_p_button.clicked.connect(lambda: self.plot_linear_graphs(dataframe, reference_componente, 'P',components))

        self.composition_n_button = self._create_button("Composition N", "#2196F3", 12, row=3, col=2, layout=grid_layout)
        self.composition_n_button.clicked.connect(lambda: self.plot_linear_graphs(dataframe, reference_componente, 'N',components))

        # N Value graph T
        name_colum = reference_componente + " Initial"
        self.n_value_combobox_graphT = self._add_labeled_combobox(grid_layout, dataframe[name_colum].unique().astype(str), "N Value:", 1, 3)
        self.p_value_combobox_graphT = self._add_labeled_combobox(grid_layout, dataframe['Pressure'].unique().astype(str), "P Value:", 1, 5)

        # N Value graph P
        self.n_value_combobox_graphP = self._add_labeled_combobox(grid_layout, dataframe[name_colum].unique().astype(str), "N Value:", 2, 3)
        self.t_value_combobox_graphP = self._add_labeled_combobox(grid_layout, dataframe['Initial Temperature'].unique().astype(str), "T Value:", 2, 5)

        # P Value graph N
        self.p_value_combobox_graphN = self._add_labeled_combobox(grid_layout, dataframe['Pressure'].unique().astype(str), "P Value:", 3, 3)
        self.t_value_combobox_graphN = self._add_labeled_combobox(grid_layout, dataframe['Initial Temperature'].unique().astype(str), "T Value:", 3, 5)

        # Correlation Matrix Button
        self.correlation_matrix_button = self._create_button("Correlation Matrix", "#F44336", 10, row=0, col=7, layout=grid_layout)
        self.correlation_matrix_button.clicked.connect(lambda: self.plot_correlation(dataframe))

        grid_layout.setColumnStretch(1, 2)
        grid_layout.setColumnStretch(4, 2)

        section_layout.addLayout(grid_layout)
        self.setLayout(section_layout)
        self.setVisible(False)

    def _create_button(self, text, color, font_size, row=None, col=None, layout=None):
        button = QPushButton(text)
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                font-size: {font_size}px;
                border: 2px solid {color};
                border-radius: 5px;
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: {self._darken_color(color)};
            }}
            QPushButton:pressed {{
                background-color: {self._lighten_color(color)};
            }}
        """)
        if layout is not None and row is not None and col is not None:
            layout.addWidget(button, row, col)
        return button

    def _darken_color(self, color):
        """Reduz o brilho da cor fornecida"""
        r, g, b = self._hex_to_rgb(color)
        darkened = (max(r - 50, 0), max(g - 50, 0), max(b - 50, 0))
        return self._rgb_to_hex(darkened)

    def _lighten_color(self, color):
        """Aumenta o brilho da cor fornecida"""
        r, g, b = self._hex_to_rgb(color)
        lightened = (min(r + 50, 255), min(g + 50, 255), min(b + 50, 255))
        return self._rgb_to_hex(lightened)

    def _hex_to_rgb(self, hex_color):
        """Converte cor hex (#RRGGBB) para RGB (r, g, b)"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _rgb_to_hex(self, rgb_color):
        """Converte cor RGB (r, g, b) para hex (#RRGGBB)"""
        return '#{:02x}{:02x}{:02x}'.format(*rgb_color)

    def _add_labeled_combobox(self, layout, items, label_text, row, col):
        label = QLabel(label_text)
        label.setStyleSheet("color: black; background-color: transparent; font-size: 10px;")
        layout.addWidget(label, row, col)
        
        combobox = self._create_combobox(items, row, col + 1)
        layout.addWidget(combobox, row, col + 1)
        return combobox

    def _create_combobox(self, items, row, col):
        combobox = QComboBox()
        combobox.addItems([str(item) for item in items])
        combobox.setMinimumWidth(100)
        self._set_combobox_style(combobox)
        return combobox

    def _set_combobox_style(self, combobox):
        combobox.setStyleSheet("""
            QComboBox {
                color: black;
                background-color: white;
                border: 1px solid #555;
                border-radius: 5px;
                padding-left: 5px;
                font-size: 10px;
            }
            QComboBox QAbstractItemView {
                color: black;
                background-color: white;
                border: 1px solid #999;
                selection-background-color: #0078d7;
                selection-color: white;
            }
            QComboBox::drop-down {
                border-radius: 5px;
            }
        """)

    def plot_surface_response(self, dataframe):
        x_value = self.x_value_combobox.currentText()
        y_value = self.y_value_combobox.currentText()
        z_value = self.z_value_combobox.currentText()

        if dataframe[x_value].nunique() < 5 or dataframe[y_value].nunique() < 5:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setText("Pontos Insuficientes para Plotagem")
            msg.setInformativeText(
                "Parece que não foram simulados pontos suficientes para gerar uma "
                "superfície de resposta. Realize uma simulação do tipo 5 x 5 x 5."
            )
            msg.setWindowTitle("Erro de Plotagem")
            msg.exec()
            return
        plot_superficie(dataframe, x_value, y_value, z_value)

    def plot_linear_graphs(self, dataframe, reference_componente, graph_type, components):
        name_colum = reference_componente + " Initial"

        if graph_type == 'T':
            n_value_t = float(self.n_value_combobox_graphT.currentText())
            p_value_t = float(self.p_value_combobox_graphT.currentText())
            label1, label2 = name_colum, 'Pressure'
            value1, value2 = n_value_t, p_value_t

        elif graph_type == 'P':
            n_value_p = float(self.n_value_combobox_graphP.currentText())
            t_value_p = float(self.t_value_combobox_graphP.currentText())
            label1, label2 = name_colum, 'Initial Temperature'
            value1, value2 = n_value_p, t_value_p

        elif graph_type == 'N':
            p_value_n = float(self.p_value_combobox_graphN.currentText())
            t_value_n = float(self.t_value_combobox_graphN.currentText())
            label1, label2 = 'Pressure', 'Initial Temperature'
            value1, value2 = p_value_n, t_value_n

        selected_components = self.component_combobox.getCheckedItems()
        
        linear_graph_maxs(dataframe=dataframe, label1=label1, label2=label2, value1=value1, value2=value2, components=components, selected_components=selected_components, name_colum=name_colum, graph_type = graph_type)

    def plot_correlation(self, dataframe):
        numeric_df = dataframe.select_dtypes(include='number')
        if len(numeric_df.columns) < 2:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setText("Dados Insuficientes para Plotagem")
            msg.setInformativeText(
                "Não há colunas numéricas suficientes para gerar uma matriz de correlação. "
                "São necessárias pelo menos duas variáveis numéricas."
            )
            msg.setWindowTitle("Erro de Plotagem")
            msg.exec()
            return
        plot_correlation_matrix(df=dataframe)