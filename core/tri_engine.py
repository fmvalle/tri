"""
Motor principal do sistema TRI (Teoria de Resposta ao Item)
Implementa o modelo de 3 parâmetros (3PL) para estimação de proficiência
"""
import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from typing import Dict, List, Tuple, Optional, Union
from tqdm import tqdm
import warnings

from config.settings import TRI_CONFIG
from utils.logger import get_logger

logger = get_logger("tri_engine")


class TRIEngine:
    """
    Motor principal para cálculos TRI usando modelo de 3 parâmetros
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Inicializa o motor TRI
        
        Args:
            config: Configurações personalizadas (opcional)
        """
        self.config = config or TRI_CONFIG
        self.logger = logger
        
    def prob_3pl(self, theta: float, a: float, b: float, c: float) -> float:
        """
        Calcula a probabilidade de acerto usando modelo 3PL
        
        Args:
            theta: Proficiência do aluno
            a: Parâmetro de discriminação
            b: Parâmetro de dificuldade
            c: Parâmetro de acerto casual
            
        Returns:
            Probabilidade de acerto
        """
        try:
            constant = self.config["constant"]
            prob = c + (1 - c) / (1 + np.exp(-constant * a * (theta - b)))
            return np.clip(prob, 1e-6, 1 - 1e-6)
        except Exception as e:
            self.logger.error(f"Erro no cálculo da probabilidade 3PL: {e}")
            return 0.5
    
    def log_likelihood(self, theta: float, responses: np.ndarray, 
                      a_params: np.ndarray, b_params: np.ndarray, 
                      c_params: np.ndarray) -> float:
        """
        Calcula a log-verossimilhança para estimação de theta
        
        Args:
            theta: Proficiência a ser estimada
            responses: Vetor de respostas (0 ou 1)
            a_params: Parâmetros de discriminação
            b_params: Parâmetros de dificuldade
            c_params: Parâmetros de acerto casual
            
        Returns:
            Log-verossimilhança negativa
        """
        try:
            probs = np.array([self.prob_3pl(theta, a, b, c) 
                             for a, b, c in zip(a_params, b_params, c_params)])
            
            # Evitar problemas numéricos
            probs = np.clip(probs, 1e-6, 1 - 1e-6)
            
            ll = responses * np.log(probs) + (1 - responses) * np.log(1 - probs)
            return -np.sum(ll)
        except Exception as e:
            self.logger.error(f"Erro no cálculo da log-verossimilhança: {e}")
            return float('inf')
    
    def estimate_theta(self, responses: np.ndarray, a_params: np.ndarray, 
                      b_params: np.ndarray, c_params: np.ndarray) -> float:
        """
        Estima a proficiência (theta) de um aluno
        
        Args:
            responses: Vetor de respostas do aluno
            a_params: Parâmetros de discriminação dos itens
            b_params: Parâmetros de dificuldade dos itens
            c_params: Parâmetros de acerto casual dos itens
            
        Returns:
            Theta estimado
        """
        try:
            bounds = self.config["theta_bounds"]
            
            # Otimização com diferentes pontos iniciais para evitar mínimos locais
            initial_points = [-2, -1, 0, 1, 2]
            best_result = None
            best_value = float('inf')
            
            for initial_point in initial_points:
                try:
                    result = minimize_scalar(
                        self.log_likelihood,
                        bounds=bounds,
                        method='bounded',
                        args=(responses, a_params, b_params, c_params),
                        options={'maxiter': self.config["max_iterations"]}
                    )
                    
                    if result.success and result.fun < best_value:
                        best_result = result
                        best_value = result.fun
                        
                except Exception as e:
                    self.logger.warning(f"Falha na otimização com ponto inicial {initial_point}: {e}")
                    continue
            
            if best_result is None:
                self.logger.warning("Falha na estimação de theta, usando valor padrão")
                return 0.0
                
            return best_result.x
            
        except Exception as e:
            self.logger.error(f"Erro na estimação de theta: {e}")
            return 0.0
    
    def estimate_theta_with_anchors(self, responses: np.ndarray, a_params: np.ndarray,
                                   b_params: np.ndarray, c_params: np.ndarray,
                                   anchor_mask: np.ndarray = None) -> float:
        """
        Estima theta usando itens âncora como referência prioritária
        
        Args:
            responses: Vetor de respostas do aluno
            a_params: Parâmetros de discriminação dos itens
            b_params: Parâmetros de dificuldade dos itens
            c_params: Parâmetros de acerto casual dos itens
            anchor_mask: Máscara booleana indicando itens âncora
            
        Returns:
            Theta estimado
        """
        try:
            # Se temos máscara de âncoras, priorizar itens âncora
            if anchor_mask is not None and np.sum(anchor_mask) > 0:
                return self._estimate_theta_anchors_priority(
                    responses, a_params, b_params, c_params, anchor_mask
                )
            else:
                # Fallback para estimação padrão
                return self.estimate_theta(responses, a_params, b_params, c_params)
                
        except Exception as e:
            self.logger.error(f"Erro na estimação de theta com âncoras: {e}")
            return self.estimate_theta(responses, a_params, b_params, c_params)
    
    def _estimate_theta_anchors_priority(self, responses: np.ndarray, a_params: np.ndarray,
                                        b_params: np.ndarray, c_params: np.ndarray,
                                        anchor_mask: np.ndarray) -> float:
        """
        Estima theta priorizando itens âncora para maior estabilidade
        """
        # Separar respostas e parâmetros de âncoras e não-âncoras
        anchor_responses = responses[anchor_mask]
        anchor_a = a_params[anchor_mask]
        anchor_b = b_params[anchor_mask]
        anchor_c = c_params[anchor_mask]
        
        non_anchor_responses = responses[~anchor_mask]
        non_anchor_a = a_params[~anchor_mask]
        non_anchor_b = b_params[~anchor_mask]
        non_anchor_c = c_params[~anchor_mask]
        
        # Se temos âncoras suficientes, usar apenas elas
        if len(anchor_responses) >= 3:
            self.logger.debug(f"Estimando theta usando {len(anchor_responses)} itens âncora")
            return self.estimate_theta(anchor_responses, anchor_a, anchor_b, anchor_c)
        
        # Se temos poucos âncoras, usar todos os itens mas com peso maior para âncoras
        elif len(anchor_responses) > 0:
            self.logger.debug(f"Estimando theta com {len(anchor_responses)} âncoras + {len(non_anchor_responses)} outros itens")
            return self._estimate_theta_weighted(
                anchor_responses, anchor_a, anchor_b, anchor_c,
                non_anchor_responses, non_anchor_a, non_anchor_b, non_anchor_c
            )
        
        # Se não temos âncoras, usar estimação padrão
        else:
            self.logger.debug("Nenhum item âncora disponível, usando estimação padrão")
            return self.estimate_theta(responses, a_params, b_params, c_params)
    
    def _estimate_theta_weighted(self, anchor_responses: np.ndarray, anchor_a: np.ndarray,
                                anchor_b: np.ndarray, anchor_c: np.ndarray,
                                other_responses: np.ndarray, other_a: np.ndarray,
                                other_b: np.ndarray, other_c: np.ndarray) -> float:
        """
        Estima theta com peso maior para itens âncora
        """
        bounds = self.config["theta_bounds"]
        
        # Função objetivo com peso maior para âncoras
        def weighted_objective(theta):
            # Log-likelihood dos âncoras (peso 2.0)
            anchor_ll = self.log_likelihood(theta, anchor_responses, anchor_a, anchor_b, anchor_c)
            
            # Log-likelihood dos outros itens (peso 1.0)
            if len(other_responses) > 0:
                other_ll = self.log_likelihood(theta, other_responses, other_a, other_b, other_c)
                total_ll = 2.0 * anchor_ll + 1.0 * other_ll
            else:
                total_ll = 2.0 * anchor_ll
            
            return total_ll
        
        # Otimização com diferentes pontos iniciais
        initial_points = [-2.0, -1.0, 0.0, 1.0, 2.0]
        best_theta = 0.0
        best_ll = float('inf')
        
        for initial_theta in initial_points:
            try:
                result = minimize_scalar(
                    weighted_objective,
                    bounds=bounds,
                    method='bounded',
                    options={'xatol': 1e-6}
                )
                
                if result.success and result.fun < best_ll:
                    best_theta = result.x
                    best_ll = result.fun
                    
            except Exception:
                continue
        
        return best_theta
    
    def calculate_enem_score(self, theta: float) -> float:
        """
        Converte theta para escala ENEM usando distribuição N(500, 100)
        
        Args:
            theta: Proficiência estimada (escala logística -5 a +5)
            
        Returns:
            Nota na escala ENEM (sem limite máximo)
        """
        try:
            base = self.config["enem_base"]  # 500 (média)
            scale = self.config["enem_scale"]  # 100 (desvio padrão)
            enem_score = base + scale * theta
            # Apenas limitar o mínimo a 0, sem limite máximo
            return max(0, enem_score)
        except Exception as e:
            self.logger.error(f"Erro no cálculo da nota ENEM: {e}")
            return 500.0
    
    def process_responses(self, responses_df: pd.DataFrame, 
                         params_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Processa as respostas e estima proficiências
        
        Args:
            responses_df: DataFrame com respostas dos alunos
            params_df: DataFrame com parâmetros dos itens (opcional)
            
        Returns:
            DataFrame com resultados (theta e nota ENEM)
        """
        try:
            # Preparar dados
            pivot_df = responses_df.pivot_table(
                index='CodPessoa', 
                columns='Questao', 
                values='Acerto'
            ).fillna(0).astype(int)
            
            num_items = pivot_df.shape[1]
            num_students = pivot_df.shape[0]
            
            self.logger.info(f"Processando {num_students} estudantes com {num_items} itens")
            
            # Configurar parâmetros
            if params_df is not None:
                a_params = params_df['a'].values
                b_params = params_df['b'].values
                c_params = params_df['c'].values
                
                if len(a_params) != num_items:
                    raise ValueError(f"Número de itens nos parâmetros ({len(a_params)}) "
                                   f"diferente do número de questões ({num_items})")
            else:
                # Usar parâmetros padrão
                a_params = np.array([self.config["default_a"]] * num_items)
                b_params = np.array([self.config["default_b"]] * num_items)
                c_params = np.array([self.config["default_c"]] * num_items)
            
            # Processar cada estudante
            results = []
            
            for cod_pessoa, row in tqdm(pivot_df.iterrows(), 
                                       total=num_students, 
                                       desc="Estimando proficiências"):
                try:
                    responses = row.values
                    theta = self.estimate_theta(responses, a_params, b_params, c_params)
                    enem_score = self.calculate_enem_score(theta)
                    
                    acertos = int(np.sum(responses))
                    percentual_acertos = round((acertos / num_items) * 100, 1)
                    
                    results.append({
                        'CodPessoa': cod_pessoa,
                        'theta': round(theta, 3),
                        'enem_score': round(enem_score),
                        'acertos': acertos,
                        'total_itens': num_items,
                        'percentual_acertos': percentual_acertos
                    })
                    
                    self.logger.debug(f"Estudante {cod_pessoa}: theta={theta:.3f}, "
                                    f"ENEM={enem_score:.0f}, acertos={np.sum(responses)}")
                    
                except Exception as e:
                    self.logger.error(f"Erro ao processar estudante {cod_pessoa}: {e}")
                    # Adicionar resultado com valores padrão
                    results.append({
                        'CodPessoa': cod_pessoa,
                        'theta': 0.0,
                        'enem_score': 500,
                        'acertos': 0,
                        'total_itens': num_items,
                        'percentual_acertos': 0.0
                    })
            
            results_df = pd.DataFrame(results)
            self.logger.info(f"Processamento concluído. {len(results_df)} estudantes processados")
            
            return results_df
            
        except Exception as e:
            self.logger.error(f"Erro no processamento das respostas: {e}")
            raise
    
    def validate_parameters(self, params_df: pd.DataFrame) -> bool:
        """
        Valida os parâmetros dos itens
        
        Args:
            params_df: DataFrame com parâmetros
            
        Returns:
            True se válido, False caso contrário
        """
        try:
            # Verificar colunas obrigatórias
            required_cols = ['a', 'b', 'c']
            if not all(col in params_df.columns for col in required_cols):
                self.logger.error("Parâmetros devem conter colunas: a, b, c")
                return False
            
            # Validar valores
            if (params_df['a'] <= 0).any():
                self.logger.error("Todos os valores de 'a' devem ser positivos")
                return False
            
            if (params_df['c'] < 0).any() or (params_df['c'] > 1).any():
                self.logger.error("Valores de 'c' devem estar entre 0 e 1")
                return False
            
            self.logger.info("Parâmetros validados com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na validação dos parâmetros: {e}")
            return False
