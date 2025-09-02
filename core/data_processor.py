"""
Processador de dados para o sistema TRI
Inclui ETL, validação e transformação de dados
"""
import pandas as pd
import numpy as np
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import warnings

from config.settings import FILE_CONFIG, VALIDATION_CONFIG
from utils.logger import get_logger

logger = get_logger("data_processor")


class DataProcessor:
    """
    Processador de dados para o sistema TRI
    """
    
    def __init__(self):
        self.logger = logger
        self.config = FILE_CONFIG
        
    def load_responses_csv(self, file_path: str) -> pd.DataFrame:
        """
        Carrega arquivo CSV de respostas
        
        Args:
            file_path: Caminho para o arquivo CSV
            
        Returns:
            DataFrame com as respostas
        """
        try:
            self.logger.info(f"Carregando arquivo CSV: {file_path}")
            
            df = pd.read_csv(
                file_path,
                sep=self.config["input_separator"],
                encoding=self.config["encoding"]
            )
            
            # Validar colunas obrigatórias
            required_cols = VALIDATION_CONFIG["required_columns"]
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                raise ValueError(f"Colunas obrigatórias ausentes: {missing_cols}")
            
            # Limpar dados
            df = self._clean_responses_data(df)
            
            self.logger.info(f"Arquivo carregado com sucesso: {len(df)} registros")
            return df
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar arquivo CSV: {e}")
            raise
    
    def load_responses_excel_from_streamlit(self, uploaded_file, sheet_name: str = "Datos") -> pd.DataFrame:
        """
        Carrega arquivo Excel de respostas do Streamlit (formato cartão de resposta)
        
        Args:
            uploaded_file: Objeto de arquivo do Streamlit
            sheet_name: Nome da aba com os dados
            
        Returns:
            DataFrame com as respostas processadas
        """
        try:
            self.logger.info(f"Carregando arquivo Excel do Streamlit: {uploaded_file.name}")
            
            # Carregar cabeçalho para identificar colunas de itens
            df_header = pd.read_excel(uploaded_file, sheet_name=sheet_name, nrows=1)
            
            # Identificar colunas de itens
            item_cols = self._extract_item_columns(df_header.columns)
            
            if not item_cols:
                raise ValueError("Nenhuma coluna de item encontrada no arquivo")
            
            # Carregar dados completos
            uploaded_file.seek(0)  # Reset file pointer
            df_datos = pd.read_excel(uploaded_file, sheet_name=sheet_name, header=0)
            
            # Carregar gabarito da aba Matriz
            uploaded_file.seek(0)  # Reset file pointer
            gabarito = self._load_gabarito_from_streamlit(uploaded_file)
            
            # Processar dados
            df_processed = self._process_excel_data(df_datos, item_cols, gabarito)
            
            self.logger.info(f"Arquivo Excel processado com sucesso: {len(df_processed)} registros")
            return df_processed
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar arquivo Excel: {e}")
            raise

    def load_responses_excel(self, file_path: str, sheet_name: str = "Datos") -> pd.DataFrame:
        """
        Carrega arquivo Excel de respostas (formato cartão de resposta)
        
        Args:
            file_path: Caminho para o arquivo Excel
            sheet_name: Nome da aba com os dados
            
        Returns:
            DataFrame com as respostas processadas
        """
        try:
            self.logger.info(f"Carregando arquivo Excel: {file_path}")
            
            # Carregar cabeçalho para identificar colunas de itens
            df_header = pd.read_excel(file_path, sheet_name=sheet_name, nrows=1)
            
            # Identificar colunas de itens
            item_cols = self._extract_item_columns(df_header.columns)
            
            if not item_cols:
                raise ValueError("Nenhuma coluna de item encontrada no arquivo")
            
            # Carregar dados completos
            df_datos = pd.read_excel(file_path, sheet_name=sheet_name, header=0)
            
            # Carregar gabarito da aba Matriz
            gabarito = self._load_gabarito(file_path)
            
            # Processar dados
            df_processed = self._process_excel_data(df_datos, item_cols, gabarito)
            
            self.logger.info(f"Arquivo Excel processado com sucesso: {len(df_processed)} registros")
            return df_processed
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar arquivo Excel: {e}")
            raise
    
    def load_parameters(self, file_path: str) -> pd.DataFrame:
        """
        Carrega arquivo de parâmetros dos itens
        
        Args:
            file_path: Caminho para o arquivo de parâmetros
            
        Returns:
            DataFrame com os parâmetros
        """
        try:
            self.logger.info(f"Carregando parâmetros: {file_path}")
            
            # Tentar diferentes formatos
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path, encoding=self.config["encoding"])
            elif file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path)
            else:
                raise ValueError("Formato de arquivo não suportado")
            
            # Validar parâmetros
            if not self._validate_parameters(df):
                raise ValueError("Parâmetros inválidos")
            
            self.logger.info(f"Parâmetros carregados: {len(df)} itens")
            return df
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar parâmetros: {e}")
            raise
    
    def _extract_item_columns(self, columns: pd.Index) -> Dict[str, int]:
        """
        Extrai colunas de itens do cabeçalho
        
        Args:
            columns: Índice das colunas
            
        Returns:
            Dicionário com nome da coluna e ID do item
        """
        item_cols = {}
        pattern = r"Ítem\s+\d+\s+ID\s+(\d+)"
        
        for col_name in columns:
            match = re.search(pattern, str(col_name))
            if match:
                item_id = int(match.group(1))
                item_cols[col_name] = item_id
        
        return item_cols
    
    def _load_gabarito_from_streamlit(self, uploaded_file) -> Dict[int, str]:
        """
        Carrega gabarito da aba Matriz do arquivo Streamlit
        
        Args:
            uploaded_file: Objeto de arquivo do Streamlit
            
        Returns:
            Dicionário com ID do item e resposta correta
        """
        try:
            df_matriz = pd.read_excel(uploaded_file, sheet_name='Matriz')
            
            gabarito = {}
            for _, row in df_matriz.iterrows():
                item_id = row.get('Ítem ID')
                clave = row.get('Clave correcta(s)')
                if pd.notna(item_id) and pd.notna(clave):
                    gabarito[int(item_id)] = str(clave)
            
            self.logger.info(f"Gabarito carregado: {len(gabarito)} itens")
            return gabarito
            
        except Exception as e:
            self.logger.warning(f"Erro ao carregar gabarito: {e}")
            return {}

    def _load_gabarito(self, file_path: str) -> Dict[int, str]:
        """
        Carrega gabarito da aba Matriz
        
        Args:
            file_path: Caminho para o arquivo Excel
            
        Returns:
            Dicionário com ID do item e resposta correta
        """
        try:
            df_matriz = pd.read_excel(file_path, sheet_name='Matriz')
            
            gabarito = {}
            for _, row in df_matriz.iterrows():
                item_id = row.get('Ítem ID')
                clave = row.get('Clave correcta(s)')
                if pd.notna(item_id) and pd.notna(clave):
                    gabarito[int(item_id)] = str(clave)
            
            self.logger.info(f"Gabarito carregado: {len(gabarito)} itens")
            return gabarito
            
        except Exception as e:
            self.logger.warning(f"Erro ao carregar gabarito: {e}")
            return {}
    
    def _process_excel_data(self, df_datos: pd.DataFrame, item_cols: Dict[str, int], 
                           gabarito: Dict[int, str]) -> pd.DataFrame:
        """
        Processa dados do Excel para formato padrão
        
        Args:
            df_datos: DataFrame com dados brutos
            item_cols: Dicionário com colunas de itens
            gabarito: Dicionário com gabarito
            
        Returns:
            DataFrame processado
        """
        data = []
        
        for index, row in df_datos.iterrows():
            # Extrair informações do aluno
            cod_pessoa = row.get("ID Usuario Curso")
            cod_campanha = row.get("ID Evaluación")
            inep = row.get("ID Colegio")
            
            if pd.isna(cod_pessoa) or pd.isna(cod_campanha):
                continue
            
            # Processar cada item
            for col_name, item_id in item_cols.items():
                resposta_aluno = row.get(col_name)
                gabarito_item = gabarito.get(item_id, "")
                
                if pd.notna(resposta_aluno):
                    data.append({
                        'CodPessoa': cod_pessoa,
                        'CodCampanha': cod_campanha,
                        'Inep': inep,
                        'Questao': list(item_cols.keys()).index(col_name) + 1,
                        'RespostaAluno': str(resposta_aluno),
                        'Gabarito': gabarito_item
                    })
        
        df_processed = pd.DataFrame(data)
        
        # Adicionar coluna de acerto
        df_processed['Acerto'] = (df_processed['RespostaAluno'] == df_processed['Gabarito']).astype(int)
        
        return df_processed
    
    def _clean_responses_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpa e valida dados de respostas
        
        Args:
            df: DataFrame com respostas
            
        Returns:
            DataFrame limpo
        """
        # Remover linhas com valores nulos
        initial_count = len(df)
        df = df.dropna(subset=['CodPessoa', 'Questao', 'RespostaAluno', 'Gabarito'])
        
        if len(df) < initial_count:
            self.logger.warning(f"Removidas {initial_count - len(df)} linhas com valores nulos")
        
        # Converter tipos
        df['CodPessoa'] = df['CodPessoa'].astype(str)
        df['Questao'] = df['Questao'].astype(int)
        df['RespostaAluno'] = df['RespostaAluno'].astype(str)
        df['Gabarito'] = df['Gabarito'].astype(str)
        
        # Adicionar coluna de acerto se não existir
        if 'Acerto' not in df.columns:
            df['Acerto'] = (df['RespostaAluno'] == df['Gabarito']).astype(int)
        
        return df
    
    def _validate_parameters(self, df: pd.DataFrame) -> bool:
        """
        Valida parâmetros dos itens
        
        Args:
            df: DataFrame com parâmetros
            
        Returns:
            True se válido
        """
        required_cols = VALIDATION_CONFIG["param_columns"]
        
        if not all(col in df.columns for col in required_cols):
            self.logger.error(f"Colunas obrigatórias ausentes: {required_cols}")
            return False
        
        # Validar valores
        if (df['a'] <= 0).any():
            self.logger.error("Valores de 'a' devem ser positivos")
            return False
        
        if (df['c'] < 0).any() or (df['c'] > 1).any():
            self.logger.error("Valores de 'c' devem estar entre 0 e 1")
            return False
        
        return True
    
    def validate_data_quality(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        Valida qualidade dos dados
        
        Args:
            df: DataFrame com respostas
            
        Returns:
            Dicionário com métricas de qualidade
        """
        try:
            metrics = {}
            
            # Estatísticas básicas
            metrics['total_students'] = df['CodPessoa'].nunique()
            metrics['total_items'] = df['Questao'].nunique()
            metrics['total_responses'] = len(df)
            
            # Verificar respostas completas
            expected_responses = metrics['total_students'] * metrics['total_items']
            metrics['completeness'] = metrics['total_responses'] / expected_responses
            
            # Verificar distribuição de acertos
            metrics['mean_accuracy'] = df['Acerto'].mean()
            metrics['std_accuracy'] = df['Acerto'].std()
            
            # Verificar estudantes com respostas incompletas
            responses_per_student = df.groupby('CodPessoa').size()
            incomplete_students = (responses_per_student != metrics['total_items']).sum()
            metrics['incomplete_students'] = incomplete_students
            
            # Log das métricas
            self.logger.info(f"Qualidade dos dados: {metrics}")
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Erro na validação de qualidade: {e}")
            return {}
    
    def save_results(self, results_df: pd.DataFrame, output_path: str, 
                    format: str = 'csv') -> None:
        """
        Salva resultados em diferentes formatos
        
        Args:
            results_df: DataFrame com resultados
            output_path: Caminho de saída
            format: Formato de saída ('csv', 'xlsx', 'json')
        """
        try:
            self.logger.info(f"Salvando resultados em: {output_path}")
            
            if format == 'csv':
                results_df.to_csv(output_path, index=False, encoding=self.config["encoding"])
            elif format == 'xlsx':
                results_df.to_excel(output_path, index=False)
            elif format == 'json':
                results_df.to_json(output_path, orient='records', indent=2)
            else:
                raise ValueError(f"Formato não suportado: {format}")
            
            self.logger.info(f"Resultados salvos com sucesso: {len(results_df)} registros")
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar resultados: {e}")
            raise
