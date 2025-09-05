"""
Módulo para equating de escalas TRI
Implementa métodos para manter consistência entre diferentes aplicações de testes
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
from scipy.optimize import minimize
from scipy import stats
import logging

from config.settings import TRI_CONFIG

logger = logging.getLogger(__name__)

class ScaleEquating:
    """
    Sistema de equating para manter consistência de escalas entre aplicações
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or TRI_CONFIG
        self.logger = logger
    
    def equate_scales(self, old_anchors: Dict, new_anchors: Dict,
                      old_params: pd.DataFrame, new_params: pd.DataFrame) -> Dict:
        """
        Equaciona escalas entre aplicações antiga e nova
        
        Args:
            old_anchors: Itens âncora da aplicação antiga
            new_anchors: Itens âncora da aplicação nova
            old_params: Parâmetros de todos os itens da aplicação antiga
            new_params: Parâmetros de todos os itens da aplicação nova
            
        Returns:
            Dicionário com transformações de escala
        """
        try:
            # Verificar se temos âncoras comuns
            common_anchors = self._find_common_anchors(old_anchors, new_anchors)
            
            if len(common_anchors) < 3:
                raise ValueError("Pelo menos 3 itens âncora comuns são necessários para equating")
            
            # Calcular transformação linear usando âncoras comuns
            transformation = self._calculate_linear_transformation(
                old_anchors, new_anchors, common_anchors
            )
            
            # Aplicar transformação aos novos parâmetros
            transformed_params = self._apply_transformation(new_params, transformation)
            
            # Validar equating
            validation = self._validate_equating(
                old_anchors, new_anchors, common_anchors, transformation
            )
            
            return {
                'transformation': transformation,
                'transformed_params': transformed_params,
                'common_anchors': common_anchors,
                'validation': validation,
                'success': validation['valid']
            }
            
        except Exception as e:
            self.logger.error(f"Erro no equating de escalas: {e}")
            raise
    
    def _find_common_anchors(self, old_anchors: Dict, new_anchors: Dict) -> List[str]:
        """
        Encontra itens âncora comuns entre aplicações
        """
        old_questions = set(old_anchors.keys())
        new_questions = set(new_anchors.keys())
        
        common = old_questions.intersection(new_questions)
        
        self.logger.info(f"Encontrados {len(common)} itens âncora comuns")
        return list(common)
    
    def _calculate_linear_transformation(self, old_anchors: Dict, new_anchors: Dict,
                                       common_anchors: List[str]) -> Dict:
        """
        Calcula transformação linear usando método de equating de âncoras
        """
        # Coletar parâmetros b (dificuldade) dos âncoras comuns
        old_b_values = []
        new_b_values = []
        
        for questao in common_anchors:
            old_b_values.append(old_anchors[questao]['b'])
            new_b_values.append(new_anchors[questao]['b'])
        
        old_b_values = np.array(old_b_values)
        new_b_values = np.array(new_b_values)
        
        # Calcular transformação linear: old_b = A * new_b + B
        # Usando regressão linear robusta
        slope, intercept, r_value, p_value, std_err = stats.linregress(new_b_values, old_b_values)
        
        # Calcular transformação para parâmetro a (discriminação)
        old_a_values = []
        new_a_values = []
        
        for questao in common_anchors:
            old_a_values.append(old_anchors[questao]['a'])
            new_a_values.append(new_anchors[questao]['a'])
        
        old_a_values = np.array(old_a_values)
        new_a_values = np.array(new_a_values)
        
        # Fator de escala para parâmetro a
        a_scale = np.median(old_a_values / new_a_values)
        
        transformation = {
            'slope': slope,
            'intercept': intercept,
            'a_scale': a_scale,
            'r_squared': r_value ** 2,
            'std_error': std_err
        }
        
        self.logger.info(f"Transformação calculada: b_old = {slope:.3f} * b_new + {intercept:.3f}")
        self.logger.info(f"Fator de escala para 'a': {a_scale:.3f}")
        self.logger.info(f"R² da transformação: {r_value**2:.3f}")
        
        return transformation
    
    def _apply_transformation(self, new_params: pd.DataFrame, transformation: Dict) -> pd.DataFrame:
        """
        Aplica transformação aos novos parâmetros
        """
        transformed_params = new_params.copy()
        
        # Transformar parâmetro b (dificuldade)
        transformed_params['b'] = (transformed_params['b'] * transformation['slope'] + 
                                 transformation['intercept'])
        
        # Transformar parâmetro a (discriminação)
        transformed_params['a'] = transformed_params['a'] * transformation['a_scale']
        
        # Parâmetro c permanece inalterado
        
        self.logger.info(f"Transformação aplicada a {len(transformed_params)} itens")
        return transformed_params
    
    def _validate_equating(self, old_anchors: Dict, new_anchors: Dict,
                          common_anchors: List[str], transformation: Dict) -> Dict:
        """
        Valida a qualidade do equating
        """
        validation = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'metrics': {}
        }
        
        # Verificar qualidade da transformação linear
        if transformation['r_squared'] < 0.8:
            validation['warnings'].append(f"R² baixo ({transformation['r_squared']:.3f}) - equating pode ser instável")
        
        if transformation['std_error'] > 0.5:
            validation['warnings'].append(f"Erro padrão alto ({transformation['std_error']:.3f})")
        
        # Verificar se a transformação é razoável
        if abs(transformation['slope']) < 0.5 or abs(transformation['slope']) > 2.0:
            validation['warnings'].append(f"Slope extremo ({transformation['slope']:.3f})")
        
        if abs(transformation['intercept']) > 3.0:
            validation['warnings'].append(f"Intercepto extremo ({transformation['intercept']:.3f})")
        
        # Calcular métricas de qualidade
        validation['metrics'] = {
            'r_squared': transformation['r_squared'],
            'std_error': transformation['std_error'],
            'num_common_anchors': len(common_anchors),
            'slope': transformation['slope'],
            'intercept': transformation['intercept']
        }
        
        return validation
    
    def equate_multiple_applications(self, applications: List[Dict]) -> Dict:
        """
        Equaciona múltiplas aplicações usando uma aplicação de referência
        
        Args:
            applications: Lista de aplicações com parâmetros e âncoras
            
        Returns:
            Dicionário com todas as transformações
        """
        try:
            if len(applications) < 2:
                raise ValueError("Pelo menos 2 aplicações são necessárias para equating")
            
            # Primeira aplicação como referência
            reference_app = applications[0]
            reference_anchors = reference_app['anchors']
            reference_params = reference_app['params']
            
            all_transformations = {}
            all_transformed_params = {}
            
            # Equacionar cada aplicação com a referência
            for i, app in enumerate(applications[1:], 1):
                app_name = app.get('name', f'application_{i}')
                
                self.logger.info(f"Equacionando aplicação {app_name} com referência")
                
                result = self.equate_scales(
                    reference_anchors, app['anchors'],
                    reference_params, app['params']
                )
                
                all_transformations[app_name] = result['transformation']
                all_transformed_params[app_name] = result['transformed_params']
                
                if not result['success']:
                    self.logger.warning(f"Equating falhou para aplicação {app_name}")
            
            return {
                'reference_application': reference_app['name'],
                'transformations': all_transformations,
                'transformed_params': all_transformed_params,
                'success': all(result['success'] for result in all_transformations.values())
            }
            
        except Exception as e:
            self.logger.error(f"Erro no equating múltiplo: {e}")
            raise
    
    def calculate_equating_quality(self, old_params: pd.DataFrame, new_params: pd.DataFrame,
                                 transformation: Dict) -> Dict:
        """
        Calcula métricas de qualidade do equating
        """
        try:
            # Aplicar transformação reversa para comparar
            reverse_transformation = {
                'slope': 1.0 / transformation['slope'],
                'intercept': -transformation['intercept'] / transformation['slope'],
                'a_scale': 1.0 / transformation['a_scale']
            }
            
            # Transformar novos parâmetros para escala antiga
            transformed_new = self._apply_transformation(new_params, reverse_transformation)
            
            # Calcular correlações entre parâmetros
            correlations = {}
            for param in ['a', 'b', 'c']:
                if param in old_params.columns and param in transformed_new.columns:
                    corr = np.corrcoef(old_params[param], transformed_new[param])[0, 1]
                    correlations[param] = corr
            
            # Calcular diferenças médias
            differences = {}
            for param in ['a', 'b', 'c']:
                if param in old_params.columns and param in transformed_new.columns:
                    diff = np.mean(np.abs(old_params[param] - transformed_new[param]))
                    differences[param] = diff
            
            quality_metrics = {
                'correlations': correlations,
                'mean_differences': differences,
                'transformation_quality': transformation['r_squared'],
                'overall_quality': np.mean(list(correlations.values())) if correlations else 0.0
            }
            
            return quality_metrics
            
        except Exception as e:
            self.logger.error(f"Erro no cálculo de qualidade: {e}")
            return {}
    
    def recommend_anchor_items(self, current_anchors: Dict, item_pool: pd.DataFrame,
                              target_count: int = 10) -> pd.DataFrame:
        """
        Recomenda itens para serem usados como âncoras
        
        Args:
            current_anchors: Âncoras atuais
            item_pool: Pool de itens disponíveis
            target_count: Número desejado de âncoras
            
        Returns:
            DataFrame com itens recomendados
        """
        try:
            # Filtrar itens que não são âncoras atuais
            current_anchor_questions = set(current_anchors.keys())
            available_items = item_pool[~item_pool['Questao'].isin(current_anchor_questions)]
            
            if len(available_items) == 0:
                return pd.DataFrame()
            
            # Calcular score de qualidade para cada item
            quality_scores = []
            
            for _, item in available_items.iterrows():
                score = self._calculate_item_quality_score(item)
                quality_scores.append({
                    'Questao': item['Questao'],
                    'a': item['a'],
                    'b': item['b'],
                    'c': item['c'],
                    'quality_score': score
                })
            
            quality_df = pd.DataFrame(quality_scores)
            
            # Ordenar por score de qualidade e selecionar os melhores
            quality_df = quality_df.sort_values('quality_score', ascending=False)
            recommended = quality_df.head(target_count)
            
            self.logger.info(f"Recomendados {len(recommended)} itens para âncoras")
            return recommended
            
        except Exception as e:
            self.logger.error(f"Erro na recomendação de âncoras: {e}")
            return pd.DataFrame()
    
    def _calculate_item_quality_score(self, item: pd.Series) -> float:
        """
        Calcula score de qualidade para um item
        """
        score = 0.0
        
        # Parâmetro a (discriminação) - quanto maior, melhor
        if item['a'] > 0:
            score += min(item['a'] / 2.0, 1.0)  # Máximo 1.0 para a
        
        # Parâmetro b (dificuldade) - preferir valores médios
        b_score = 1.0 - abs(item['b']) / 3.0  # Melhor próximo de 0
        score += max(b_score, 0.0)
        
        # Parâmetro c (acerto casual) - quanto menor, melhor
        if item['c'] <= 0.25:
            score += 1.0 - (item['c'] / 0.25)
        
        return score / 3.0  # Normalizar para 0-1
