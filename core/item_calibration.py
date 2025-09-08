"""
Módulo para calibração de parâmetros dos itens TRI
Usa pyirt para estimar parâmetros a, b, c dos itens
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import warnings
from scipy.optimize import minimize
from sklearn.metrics import log_loss
import logging

logger = logging.getLogger(__name__)

class ItemCalibrator:
    """
    Calibrador de parâmetros dos itens TRI
    """
    
    def __init__(self):
        self.logger = logger
        
    def prepare_response_matrix(self, responses_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """
        Prepara matriz de respostas para calibração
        
        Args:
            responses_df: DataFrame com respostas dos alunos
            
        Returns:
            Matriz de respostas e mapeamento de itens
        """
        try:
            # Criar matriz de respostas (alunos x itens)
            response_matrix = responses_df.pivot_table(
                index='CodPessoa',
                columns='Questao',
                values='Acerto',
                fill_value=np.nan
            )
            
            # Mapeamento de itens
            item_mapping = {col: idx + 1 for idx, col in enumerate(response_matrix.columns)}
            
            self.logger.info(f"Matriz de respostas criada: {response_matrix.shape}")
            return response_matrix, item_mapping
            
        except Exception as e:
            self.logger.error(f"Erro ao preparar matriz de respostas: {e}")
            raise
    
    def calibrate_items_3pl(self, responses_df: pd.DataFrame, 
                           anchor_items: Optional[Dict] = None) -> pd.DataFrame:
        """
        Calibra parâmetros dos itens usando modelo 3PL
        
        Args:
            responses_df: DataFrame com respostas dos alunos
            anchor_items: Dicionário com itens âncora {questao: {'a': val, 'b': val, 'c': val}}
            
        Returns:
            DataFrame com parâmetros calibrados
        """
        try:
            # Preparar matriz de respostas
            response_matrix, item_mapping = self.prepare_response_matrix(responses_df)
            
            # Converter para numpy array
            response_array = response_matrix.values
            
            # Identificar itens âncora
            anchor_mask = np.zeros(len(response_matrix.columns), dtype=bool)
            if anchor_items:
                for questao, params in anchor_items.items():
                    if questao in item_mapping:
                        idx = item_mapping[questao] - 1
                        anchor_mask[idx] = True
            
            # Se temos âncoras, usar calibração relativa
            if anchor_items and np.sum(anchor_mask) > 0:
                self.logger.info("Usando calibração relativa com itens âncora")
                calibrated_params = self._calibrate_relative_to_anchors(
                    response_array, anchor_mask, anchor_items, item_mapping
                )
            else:
                self.logger.info("Usando calibração independente (sem âncoras)")
                calibrated_params = self._calibrate_independent_items(
                    response_array, anchor_mask, item_mapping
                )
            
            # Combinar com itens âncora
            final_params = self._combine_anchor_and_calibrated(
                calibrated_params, anchor_items, item_mapping
            )
            
            self.logger.info(f"Calibração concluída: {len(final_params)} itens")
            return final_params
            
        except Exception as e:
            self.logger.error(f"Erro na calibração: {e}")
            raise
    
    def _calibrate_relative_to_anchors(self, response_array: np.ndarray,
                                      anchor_mask: np.ndarray,
                                      anchor_items: Dict,
                                      item_mapping: Dict) -> pd.DataFrame:
        """
        Calibra itens usando âncoras como referência para manter escala
        """
        calibrated_params = []
        
        # Primeiro, estimar theta dos alunos usando apenas itens âncora
        anchor_thetas = self._estimate_theta_from_anchors(
            response_array, anchor_mask, anchor_items, item_mapping
        )
        
        self.logger.info(f"Theta estimado para {len(anchor_thetas)} alunos usando âncoras")
        
        # Calibrar novos itens usando theta estimado dos âncoras
        for item_idx in range(response_array.shape[1]):
            if not anchor_mask[item_idx]:
                questao = list(item_mapping.keys())[item_idx]
                item_responses = response_array[:, item_idx]
                
                # Remover respostas nulas
                valid_mask = ~np.isnan(item_responses)
                if np.sum(valid_mask) < 10:
                    self.logger.warning(f"Item {questao}: poucas respostas válidas")
                    params = {'a': 1.0, 'b': 0.0, 'c': 0.2}
                else:
                    # Usar theta estimado dos âncoras para calibração
                    valid_thetas = anchor_thetas[valid_mask]
                    valid_responses = item_responses[valid_mask]
                    
                    params = self._estimate_item_parameters_with_theta(
                        valid_responses, valid_thetas
                    )
                
                calibrated_params.append({
                    'Questao': questao,
                    'a': params['a'],
                    'b': params['b'],
                    'c': params['c'],
                    'calibrated': True,
                    'method': 'relative_to_anchors'
                })
        
        return pd.DataFrame(calibrated_params)
    
    def _estimate_theta_from_anchors(self, response_array: np.ndarray,
                                   anchor_mask: np.ndarray,
                                   anchor_items: Dict,
                                   item_mapping: Dict) -> np.ndarray:
        """
        Estima theta dos alunos usando apenas itens âncora
        """
        from core.tri_engine import TRIEngine
        
        tri_engine = TRIEngine()
        thetas = np.zeros(response_array.shape[0])
        
        # Para cada aluno, estimar theta usando âncoras
        for student_idx in range(response_array.shape[0]):
            student_responses = []
            a_params = []
            b_params = []
            c_params = []
            
            # Coletar respostas e parâmetros dos âncoras
            for item_idx in range(response_array.shape[1]):
                if anchor_mask[item_idx]:
                    questao = list(item_mapping.keys())[item_idx]
                    if questao in anchor_items:
                        response = response_array[student_idx, item_idx]
                        if not np.isnan(response):
                            student_responses.append(response)
                            a_params.append(anchor_items[questao]['a'])
                            b_params.append(anchor_items[questao]['b'])
                            c_params.append(anchor_items[questao]['c'])
            
            # Estimar theta se temos respostas suficientes
            if len(student_responses) >= 3:  # Mínimo de 3 âncoras
                try:
                    theta = tri_engine.estimate_theta(
                        np.array(student_responses),
                        np.array(a_params),
                        np.array(b_params),
                        np.array(c_params)
                    )
                    thetas[student_idx] = theta
                except Exception as e:
                    self.logger.warning(f"Falha na estimação de theta para aluno {student_idx}: {e}")
                    thetas[student_idx] = 0.0  # Valor padrão
            else:
                thetas[student_idx] = 0.0  # Valor padrão
        
        return thetas
    
    def _estimate_item_parameters_with_theta(self, responses: np.ndarray,
                                           thetas: np.ndarray) -> Dict:
        """
        Estima parâmetros de um item usando theta conhecido dos âncoras
        """
        # Valores iniciais
        initial_params = [1.0, 0.0, 0.2]  # a, b, c
        
        # Função objetivo: log-likelihood com theta conhecido
        def objective(params):
            a, b, c = params
            if a <= 0 or c < 0 or c > 1:
                return 1e6  # Penalidade para parâmetros inválidos
            
            # Calcular probabilidades esperadas para cada theta
            probs = []
            for theta in thetas:
                p = c + (1 - c) / (1 + np.exp(-1.7 * a * (theta - b)))
                probs.append(p)
            
            probs = np.array(probs)
            probs = np.clip(probs, 1e-6, 1 - 1e-6)
            
            # Log-likelihood
            ll = np.sum(responses * np.log(probs) + (1 - responses) * np.log(1 - probs))
            return -ll  # Minimizar -log-likelihood
        
        # Otimização com restrições
        try:
            result = minimize(objective, initial_params, method='L-BFGS-B',
                            bounds=[(0.1, 5.0), (-3.0, 3.0), (0.0, 0.5)])
            
            if result.success:
                return {'a': result.x[0], 'b': result.x[1], 'c': result.x[2]}
            else:
                self.logger.warning("Otimização falhou, usando valores padrão")
                return {'a': 1.0, 'b': 0.0, 'c': 0.2}
                
        except Exception as e:
            self.logger.warning(f"Erro na otimização: {e}")
            return {'a': 1.0, 'b': 0.0, 'c': 0.2}
    
    def _calibrate_independent_items(self, response_array: np.ndarray,
                                   anchor_mask: np.ndarray,
                                   item_mapping: Dict) -> pd.DataFrame:
        """
        Calibra itens independentemente (método original)
        """
        calibrated_params = []
        
        for item_idx in range(response_array.shape[1]):
            if not anchor_mask[item_idx]:
                questao = list(item_mapping.keys())[item_idx]
                item_responses = response_array[:, item_idx]
                
                valid_mask = ~np.isnan(item_responses)
                if np.sum(valid_mask) < 10:
                    self.logger.warning(f"Item {questao}: poucas respostas válidas")
                    params = {'a': 1.0, 'b': 0.0, 'c': 0.2}
                else:
                    params = self._estimate_item_parameters(item_responses[valid_mask])
                
                calibrated_params.append({
                    'Questao': questao,
                    'a': params['a'],
                    'b': params['b'],
                    'c': params['c'],
                    'calibrated': True,
                    'method': 'independent'
                })
        
        return pd.DataFrame(calibrated_params)
    
    def _estimate_item_parameters(self, responses: np.ndarray) -> Dict:
        """
        Estima parâmetros de um item usando otimização CORRIGIDA
        """
        # Valores iniciais
        initial_params = [1.0, 0.0, 0.2]  # a, b, c
        
        # Função objetivo corrigida
        def objective(params):
            a, b, c = params
            if a <= 0 or c < 0 or c > 1:
                return 1e6  # Penalidade para parâmetros inválidos
            
            # CORREÇÃO: Usar estimativa mais robusta de theta
            p_observed = np.mean(responses)
            
            # Estimativa inicial de theta baseada na proporção observada
            if p_observed > c and p_observed < 1.0:
                theta_est = b + (1 / (1.7 * a)) * np.log((p_observed - c) / (1 - c))
            else:
                theta_est = 2 * (p_observed - 0.5)  # Mapear [0,1] para [-1,1]
            
            # CORREÇÃO: Incluir constante 1.7 do modelo 3PL
            p_correct = c + (1 - c) / (1 + np.exp(-1.7 * a * (theta_est - b)))
            
            # Evitar problemas numéricos
            p_correct = np.clip(p_correct, 1e-6, 1 - 1e-6)
            
            # Log-likelihood
            ll = np.sum(responses * np.log(p_correct) + (1 - responses) * np.log(1 - p_correct))
            return -ll  # Minimizar -log-likelihood
        
        # Otimização com múltiplos pontos iniciais
        best_params = None
        best_value = float('inf')
        
        # Diferentes pontos iniciais para evitar mínimos locais
        initial_points = [
            [1.0, 0.0, 0.2],   # Padrão
            [0.8, -0.5, 0.15], # Alternativo 1
            [1.2, 0.5, 0.25],  # Alternativo 2
            [0.6, -1.0, 0.1],  # Alternativo 3
            [1.5, 1.0, 0.3],   # Alternativo 4
        ]
        
        for initial_point in initial_points:
            try:
                result = minimize(objective, initial_point, method='L-BFGS-B',
                                bounds=[(0.1, 5.0), (-3.0, 3.0), (0.0, 0.5)])
                
                if result.success and result.fun < best_value:
                    best_params = result.x
                    best_value = result.fun
                    
            except Exception as e:
                self.logger.warning(f"Falha na otimização com ponto inicial {initial_point}: {e}")
                continue
        
        if best_params is not None:
            return {'a': best_params[0], 'b': best_params[1], 'c': best_params[2]}
        else:
            self.logger.warning("Todas as otimizações falharam, usando valores padrão")
            return {'a': 1.0, 'b': 0.0, 'c': 0.2}
    
    def _combine_anchor_and_calibrated(self, calibrated_params: pd.DataFrame,
                                      anchor_items: Optional[Dict],
                                      item_mapping: Dict) -> pd.DataFrame:
        """
        Combina parâmetros de itens âncora e calibrados
        """
        all_params = []
        
        # Adicionar itens calibrados
        for _, row in calibrated_params.iterrows():
            all_params.append({
                'Questao': row['Questao'],
                'a': row['a'],
                'b': row['b'],
                'c': row['c'],
                'type': 'calibrated'
            })
        
        # Adicionar itens âncora
        if anchor_items:
            for questao, params in anchor_items.items():
                all_params.append({
                    'Questao': questao,
                    'a': params['a'],
                    'b': params['b'],
                    'c': params['c'],
                    'type': 'anchor'
                })
        
        return pd.DataFrame(all_params)
    
    def validate_calibration(self, params_df: pd.DataFrame) -> Dict:
        """
        Valida parâmetros calibrados
        """
        validation = {
            'valid': True,
            'warnings': [],
            'errors': []
        }
        
        # Verificar valores dos parâmetros
        if (params_df['a'] <= 0).any():
            validation['errors'].append("Parâmetros 'a' devem ser positivos")
            validation['valid'] = False
        
        if (params_df['c'] < 0).any() or (params_df['c'] > 1).any():
            validation['errors'].append("Parâmetros 'c' devem estar entre 0 e 1")
            validation['valid'] = False
        
        # Verificar valores extremos
        if (params_df['a'] > 10).any():
            validation['warnings'].append("Alguns parâmetros 'a' são muito altos")
        
        if (params_df['b'] < -5).any() or (params_df['b'] > 5).any():
            validation['warnings'].append("Alguns parâmetros 'b' são extremos")
        
        return validation
    
    def load_anchor_items(self, file_path: str) -> Dict:
        """
        Carrega itens âncora de arquivo CSV
        """
        try:
            anchor_df = pd.read_csv(file_path)
            anchor_items = {}
            
            for _, row in anchor_df.iterrows():
                questao = int(row['Questao'])
                anchor_items[questao] = {
                    'a': float(row['a']),
                    'b': float(row['b']),
                    'c': float(row['c'])
                }
            
            self.logger.info(f"Itens âncora carregados: {len(anchor_items)}")
            return anchor_items
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar itens âncora: {e}")
            return {}
    
    def save_calibrated_params(self, params_df: pd.DataFrame, file_path: str):
        """
        Salva parâmetros calibrados em arquivo CSV
        """
        try:
            # Selecionar apenas colunas necessárias
            output_df = params_df[['Questao', 'a', 'b', 'c']].copy()
            output_df = output_df.sort_values('Questao')
            output_df.to_csv(file_path, index=False)
            
            self.logger.info(f"Parâmetros salvos em: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar parâmetros: {e}")
            raise
