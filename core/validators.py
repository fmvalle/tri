"""
Sistema de validação para o projeto TRI
Valida dados de entrada, parâmetros e resultados
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path

from config.settings import VALIDATION_CONFIG
from utils.logger import get_logger

logger = get_logger("validators")


class DataValidator:
    """
    Validador de dados para o sistema TRI
    """
    
    def __init__(self):
        self.logger = logger
        self.config = VALIDATION_CONFIG
    
    def validate_responses_file(self, file_path: str) -> Dict[str, any]:
        """
        Valida arquivo de respostas
        
        Args:
            file_path: Caminho para o arquivo
            
        Returns:
            Dicionário com resultados da validação
        """
        validation_result = {
            'valid': False,
            'errors': [],
            'warnings': [],
            'metrics': {}
        }
        
        try:
            # Verificar se arquivo existe
            if not Path(file_path).exists():
                validation_result['errors'].append(f"Arquivo não encontrado: {file_path}")
                return validation_result
            
            # Carregar dados
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path, sep=';', encoding='utf-8')
            elif file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path)
            else:
                validation_result['errors'].append("Formato de arquivo não suportado")
                return validation_result
            
            # Validar colunas obrigatórias
            required_cols = self.config["required_columns"]
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                validation_result['errors'].append(f"Colunas obrigatórias ausentes: {missing_cols}")
            else:
                validation_result['warnings'].append("Colunas obrigatórias presentes")
            
            # Validar dados
            if len(df) > 0:
                validation_result.update(self._validate_response_data(df))
            else:
                validation_result['errors'].append("Arquivo vazio")
            
            # Determinar se é válido
            validation_result['valid'] = len(validation_result['errors']) == 0
            
        except Exception as e:
            validation_result['errors'].append(f"Erro na validação: {str(e)}")
        
        return validation_result
    
    def validate_parameters_file(self, file_path: str, num_items: Optional[int] = None) -> Dict[str, any]:
        """
        Valida arquivo de parâmetros
        
        Args:
            file_path: Caminho para o arquivo
            num_items: Número esperado de itens (opcional)
            
        Returns:
            Dicionário com resultados da validação
        """
        validation_result = {
            'valid': False,
            'errors': [],
            'warnings': [],
            'metrics': {}
        }
        
        try:
            # Verificar se arquivo existe
            if not Path(file_path).exists():
                validation_result['errors'].append(f"Arquivo não encontrado: {file_path}")
                return validation_result
            
            # Carregar dados
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path, encoding='utf-8')
            elif file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path)
            else:
                validation_result['errors'].append("Formato de arquivo não suportado")
                return validation_result
            
            # Validar colunas
            param_cols = self.config["param_columns"]
            missing_cols = [col for col in param_cols if col not in df.columns]
            
            if missing_cols:
                validation_result['errors'].append(f"Colunas de parâmetros ausentes: {missing_cols}")
            else:
                validation_result['warnings'].append("Colunas de parâmetros presentes")
            
            # Validar valores
            if len(df) > 0:
                validation_result.update(self._validate_parameter_values(df))
                
                # Verificar número de itens
                if num_items is not None and len(df) != num_items:
                    validation_result['errors'].append(
                        f"Número de itens ({len(df)}) diferente do esperado ({num_items})"
                    )
            else:
                validation_result['errors'].append("Arquivo vazio")
            
            # Determinar se é válido
            validation_result['valid'] = len(validation_result['errors']) == 0
            
        except Exception as e:
            validation_result['errors'].append(f"Erro na validação: {str(e)}")
        
        return validation_result
    
    def validate_results(self, results_df: pd.DataFrame, 
                        input_df: Optional[pd.DataFrame] = None) -> Dict[str, any]:
        """
        Valida resultados da TRI
        
        Args:
            results_df: DataFrame com resultados
            input_df: DataFrame de entrada original (opcional)
            
        Returns:
            Dicionário com resultados da validação
        """
        validation_result = {
            'valid': False,
            'errors': [],
            'warnings': [],
            'metrics': {}
        }
        
        try:
            # Verificar colunas obrigatórias
            required_cols = ['CodPessoa', 'theta', 'enem_score']
            missing_cols = [col for col in required_cols if col not in results_df.columns]
            
            if missing_cols:
                validation_result['errors'].append(f"Colunas obrigatórias ausentes: {missing_cols}")
                return validation_result
            
            # Validar valores de theta
            theta_validation = self._validate_theta_values(results_df['theta'])
            validation_result['errors'].extend(theta_validation['errors'])
            validation_result['warnings'].extend(theta_validation['warnings'])
            
            # Validar valores de ENEM
            enem_validation = self._validate_enem_values(results_df['enem_score'])
            validation_result['errors'].extend(enem_validation['errors'])
            validation_result['warnings'].extend(enem_validation['warnings'])
            
            # Verificar consistência com dados de entrada
            if input_df is not None:
                consistency_validation = self._validate_consistency(results_df, input_df)
                validation_result['errors'].extend(consistency_validation['errors'])
                validation_result['warnings'].extend(consistency_validation['warnings'])
            
            # Calcular métricas
            validation_result['metrics'] = self._calculate_result_metrics(results_df)
            
            # Determinar se é válido
            validation_result['valid'] = len(validation_result['errors']) == 0
            
        except Exception as e:
            validation_result['errors'].append(f"Erro na validação: {str(e)}")
        
        return validation_result
    
    def _validate_response_data(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        Valida dados de respostas
        
        Args:
            df: DataFrame com respostas
            
        Returns:
            Dicionário com resultados da validação
        """
        result = {'errors': [], 'warnings': [], 'metrics': {}}
        
        # Verificar valores nulos
        null_counts = df[self.config["required_columns"]].isnull().sum()
        for col, count in null_counts.items():
            if count > 0:
                result['warnings'].append(f"Coluna {col} tem {count} valores nulos")
        
        # Verificar número de estudantes
        num_students = df['CodPessoa'].nunique()
        if num_students < self.config["min_students"]:
            result['warnings'].append(f"Poucos estudantes ({num_students})")
        elif num_students > self.config["max_students"]:
            result['warnings'].append(f"Muitos estudantes ({num_students})")
        
        # Verificar número de itens
        num_items = df['Questao'].nunique()
        if num_items < self.config["min_items"]:
            result['warnings'].append(f"Poucos itens ({num_items})")
        elif num_items > self.config["max_items"]:
            result['warnings'].append(f"Muitos itens ({num_items})")
        
        # Verificar respostas completas
        responses_per_student = df.groupby('CodPessoa').size()
        incomplete_students = (responses_per_student != num_items).sum()
        if incomplete_students > 0:
            result['warnings'].append(f"{incomplete_students} estudantes com respostas incompletas")
        
        # Calcular métricas
        result['metrics'] = {
            'total_students': num_students,
            'total_items': num_items,
            'total_responses': len(df),
            'incomplete_students': incomplete_students,
            'completeness': len(df) / (num_students * num_items)
        }
        
        return result
    
    def _validate_parameter_values(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        Valida valores dos parâmetros
        
        Args:
            df: DataFrame com parâmetros
            
        Returns:
            Dicionário com resultados da validação
        """
        result = {'errors': [], 'warnings': [], 'metrics': {}}
        
        # Validar parâmetro 'a' (discriminação)
        if 'a' in df.columns:
            if (df['a'] <= 0).any():
                result['errors'].append("Valores de 'a' devem ser positivos")
            else:
                result['metrics']['a_mean'] = df['a'].mean()
                result['metrics']['a_std'] = df['a'].std()
        
        # Validar parâmetro 'b' (dificuldade)
        if 'b' in df.columns:
            result['metrics']['b_mean'] = df['b'].mean()
            result['metrics']['b_std'] = df['b'].std()
            result['metrics']['b_range'] = (df['b'].min(), df['b'].max())
        
        # Validar parâmetro 'c' (acerto casual)
        if 'c' in df.columns:
            if (df['c'] < 0).any() or (df['c'] > 1).any():
                result['errors'].append("Valores de 'c' devem estar entre 0 e 1")
            else:
                result['metrics']['c_mean'] = df['c'].mean()
                result['metrics']['c_std'] = df['c'].std()
        
        return result
    
    def _validate_theta_values(self, theta_series: pd.Series) -> Dict[str, any]:
        """
        Valida valores de theta
        
        Args:
            theta_series: Série com valores de theta
            
        Returns:
            Dicionário com resultados da validação
        """
        result = {'errors': [], 'warnings': []}
        
        # Verificar limites
        bounds = (-4, 4)
        out_of_bounds = ((theta_series < bounds[0]) | (theta_series > bounds[1])).sum()
        
        if out_of_bounds > 0:
            result['warnings'].append(f"{out_of_bounds} valores de theta fora dos limites {bounds}")
        
        # Verificar valores extremos
        extreme_values = ((theta_series < -3) | (theta_series > 3)).sum()
        if extreme_values > 0:
            result['warnings'].append(f"{extreme_values} valores extremos de theta (< -3 ou > 3)")
        
        return result
    
    def _validate_enem_values(self, enem_series: pd.Series) -> Dict[str, any]:
        """
        Valida valores de nota ENEM
        
        Args:
            enem_series: Série com valores de nota ENEM
            
        Returns:
            Dicionário com resultados da validação
        """
        result = {'errors': [], 'warnings': []}
        
        # Verificar limites
        out_of_bounds = ((enem_series < 0) | (enem_series > 1000)).sum()
        
        if out_of_bounds > 0:
            result['errors'].append(f"{out_of_bounds} notas ENEM fora dos limites (0-1000)")
        
        # Verificar valores extremos
        extreme_values = ((enem_series < 100) | (enem_series > 1100)).sum()
        if extreme_values > 0:
            result['warnings'].append(f"{extreme_values} notas extremas (< 100 ou > 1100)")
        
        return result
    
    def _validate_consistency(self, results_df: pd.DataFrame, 
                            input_df: pd.DataFrame) -> Dict[str, any]:
        """
        Valida consistência entre resultados e dados de entrada
        
        Args:
            results_df: DataFrame com resultados
            input_df: DataFrame com dados de entrada
            
        Returns:
            Dicionário com resultados da validação
        """
        result = {'errors': [], 'warnings': []}
        
        # Verificar se todos os estudantes estão nos resultados
        input_students = set(input_df['CodPessoa'].unique())
        result_students = set(results_df['CodPessoa'].unique())
        
        missing_students = input_students - result_students
        extra_students = result_students - input_students
        
        if missing_students:
            result['errors'].append(f"{len(missing_students)} estudantes ausentes nos resultados")
        
        if extra_students:
            result['warnings'].append(f"{len(extra_students)} estudantes extras nos resultados")
        
        return result
    
    def _calculate_result_metrics(self, results_df: pd.DataFrame) -> Dict[str, any]:
        """
        Calcula métricas dos resultados
        
        Args:
            results_df: DataFrame com resultados
            
        Returns:
            Dicionário com métricas
        """
        metrics = {}
        
        # Estatísticas de theta
        metrics['theta_mean'] = results_df['theta'].mean()
        metrics['theta_std'] = results_df['theta'].std()
        metrics['theta_min'] = results_df['theta'].min()
        metrics['theta_max'] = results_df['theta'].max()
        
        # Estatísticas de ENEM
        metrics['enem_mean'] = results_df['enem_score'].mean()
        metrics['enem_std'] = results_df['enem_score'].std()
        metrics['enem_min'] = results_df['enem_score'].min()
        metrics['enem_max'] = results_df['enem_score'].max()
        
        # Distribuição
        metrics['total_students'] = len(results_df)
        
        return metrics
    
    def print_validation_report(self, validation_result: Dict[str, any]) -> None:
        """
        Imprime relatório de validação
        
        Args:
            validation_result: Resultado da validação
        """
        print("\n" + "="*50)
        print("RELATÓRIO DE VALIDAÇÃO")
        print("="*50)
        
        # Status geral
        status = "✅ VÁLIDO" if validation_result['valid'] else "❌ INVÁLIDO"
        print(f"Status: {status}")
        
        # Erros
        if validation_result['errors']:
            print(f"\n❌ ERROS ({len(validation_result['errors'])}):")
            for error in validation_result['errors']:
                print(f"  • {error}")
        
        # Avisos
        if validation_result['warnings']:
            print(f"\n⚠️ AVISOS ({len(validation_result['warnings'])}):")
            for warning in validation_result['warnings']:
                print(f"  • {warning}")
        
        # Métricas
        if validation_result['metrics']:
            print(f"\n📊 MÉTRICAS:")
            for key, value in validation_result['metrics'].items():
                if isinstance(value, float):
                    print(f"  • {key}: {value:.3f}")
                else:
                    print(f"  • {key}: {value}")
        
        print("="*50 + "\n")
