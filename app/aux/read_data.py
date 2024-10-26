import pandas as pd
import os

class ReadData():
    def __init__(self, path):
        self.path = path
        self.data = self.read_file()

    def read_file(self):
        file_extension = os.path.splitext(self.path)[1].lower()
        if file_extension == '.csv':
            return pd.read_csv(self.path)
        elif file_extension in ['.xls', '.xlsx']:
            return pd.read_excel(self.path)
        elif file_extension == '.txt':
            return pd.read_csv(self.path, sep=',')
        else:
            raise ValueError("Unsupported file format. Please provide a CSV, Excel, or TXT file.")
        
    def get_infos(self):
        full_data = self.data
        initial = full_data['initial'].values 
        components = full_data['Component'].values 
        species = full_data.columns[full_data.columns.get_loc("C"):]
        data = full_data.to_dict(orient='index')
        return data, species, initial, components