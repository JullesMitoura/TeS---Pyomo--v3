from PyQt6.QtWidgets import QApplication, QFrame, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QMessageBox, QFileDialog, QHeaderView, QWidget
from PyQt6.QtCore import Qt
import sys
import pandas as pd

class Section4(QFrame):
    def __init__(self, dataframe, components, parent=None):
        super().__init__(parent)
        self.setMaximumHeight(200)
        section_layout = QVBoxLayout()

        self.original_data = dataframe
        results = []
        for component in components:
            if component in dataframe.columns:
                max_index = dataframe[component].idxmax()
                max_value = dataframe[component].max()

                # Verifica se max_value é um número
                if isinstance(max_value, (int, float)):
                    max_value_str = f"{max_value:.2f}"  # Formata para duas casas decimais
                else:
                    max_value_str = str(max_value)  # Se não for número, converte para string

                row_data = [max_value_str,
                            dataframe.at[max_index, 'Initial Temperature'], 
                            dataframe.at[max_index, 'Pressure']] + \
                           [dataframe.at[max_index, col] for col in dataframe.columns if col.endswith('Initial')]

                results.append([component] + row_data)  # Adiciona a linha aos resultados

        results_df = pd.DataFrame(results, columns=['Component', 'Max Value', 'Initial Temperature', 'Pressure'] + 
                                   [col for col in dataframe.columns if col.endswith('Initial')])

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(len(results_df.columns))
        self.results_table.setRowCount(len(results_df))
        self.results_table.setHorizontalHeaderLabels(results_df.columns.tolist())
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)


        self.results_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid black;
                background-color: #f5f5f5;
                gridline-color: black;  /* Black grid lines */
                font-size: 10px; /* Adjust font size here */
            }
            QTableWidget::item {
                border: 1px solid black;  /* Black border for each cell */
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
                border: 1px solid black;  /* Black border for header */
                padding: 5px;
                font-weight: bold;
                font-size: 10px; /* Adjust font size here */
            }
            QTableCornerButton::section {
                background-color: #3f51b5;
            }
        """)


        row_height = 20
        self.results_table.horizontalHeader().setFixedHeight(25)

        for row in range(len(results_df)):
            for col in range(len(results_df.columns)):
                item = QTableWidgetItem(str(results_df.iloc[row, col]))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.results_table.setItem(row, col, item)
                self.results_table.setRowHeight(row, row_height)

        self.save_button = QPushButton("Save Results")
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 12px;
                border: 2px solid #4CAF50;
                border-radius: 5px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.save_button.clicked.connect(self.save_results)

        section_layout.addWidget(self.results_table)
        section_layout.addWidget(self.save_button)
        self.setLayout(section_layout)
        self.setVisible(True)

    def save_results(self):
        if self.results_table.rowCount() > 0:
            file_name, _ = QFileDialog.getSaveFileName(
                self, 
                "Save results", 
                "", 
                "CSV Files (*.csv);;Excel Files (*.xlsx);;All Files (*)"
            )

            if file_name:
                if file_name.endswith('.csv'):
                    self.original_data.to_csv(file_name, index=False)
                elif file_name.endswith('.xlsx'):
                    self.original_data.to_excel(file_name, index=False)
                
                msg_box = QMessageBox(self)
                msg_box.setIcon(QMessageBox.Icon.Information)
                msg_box.setWindowTitle("Success")
                msg_box.setText("Results saved successfully!")
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
        else:
            msg_box_error = QMessageBox(self)
            msg_box_error.setIcon(QMessageBox.Icon.Warning)
            msg_box_error.setWindowTitle("Error")
            msg_box_error.setText("No data to save!")
            msg_box_error.setStyleSheet("""
                QLabel { color: black; }
                QPushButton { color: black; background-color: #E1E1E1; border: 1px solid #ADADAD; padding: 5px 15px; border-radius: 3px; }
                QPushButton:hover { background-color: #F0F0F0; }
            """)
            msg_box_error.exec()