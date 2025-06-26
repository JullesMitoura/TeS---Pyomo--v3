import pandas as pd
import os

class ReadData():
    def __init__(self, path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"O arquivo especificado não foi encontrado em: {path}")
        
        self.path = path
        self.file_extension = os.path.splitext(self.path)[1].lower()
        
        self.dataframe = None 
        self.data, self.species, self.initial, self.components = self.get_infos()
        
        self.kij = self.load_kij()

    def get_infos(self):
        try:
            if self.file_extension in ['.xls', '.xlsx']:
                full_data = pd.read_excel(self.path, sheet_name='Informations')
            else:
                full_data = pd.read_csv(self.path)
        except Exception as e:
            raise ValueError(f"Não foi possível ler os dados principais do arquivo: {e}")

        self.dataframe = full_data
        required_columns = ['Component', 'initial', 'C']
        for col in required_columns:
            if col not in full_data.columns:
                raise KeyError(f"Coluna obrigatória '{col}' não encontrada no arquivo de entrada.")

        initial = full_data['initial'].values 
        components = full_data['Component'].values 
        species = full_data.columns[full_data.columns.get_loc("C"):]
        
        data_dict = {row['Component']: row.to_dict() for index, row in full_data.iterrows()}

        return data_dict, species, initial, components

    def load_kij(self):
        if self.file_extension in ['.xls', '.xlsx']:
            try:
                df_kij = pd.read_excel(self.path, sheet_name='kij', index_col=0)
                
                df_kij = df_kij.reindex(index=self.components, columns=self.components, fill_value=0)
                return df_kij

            except ValueError:
                print("Aviso: Aba 'kij' não encontrada no arquivo Excel. Assumindo todos os kij = 0.")
                return pd.DataFrame(0, index=self.components, columns=self.components)
            except Exception as e:
                print(f"Erro ao ler a aba 'kij': {e}. Assumindo todos os kij = 0.")
                return pd.DataFrame(0, index=self.components, columns=self.components)
        else:
            print("Aviso: O arquivo não é um Excel, portanto não há aba 'kij'. Assumindo todos os kij = 0.")
            return pd.DataFrame(0, index=self.components, columns=self.components)