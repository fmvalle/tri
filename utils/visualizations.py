"""
Sistema de visualizações para o projeto TRI
Gera gráficos, relatórios e dashboards
"""
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import warnings

from config.settings import VISUALIZATION_CONFIG, REPORTS_DIR
from utils.logger import get_logger

logger = get_logger("visualizations")

# Configurar estilo
plt.style.use(VISUALIZATION_CONFIG["style"])
sns.set_palette(VISUALIZATION_CONFIG["color_palette"])


class TRIVisualizer:
    """
    Gerador de visualizações para o sistema TRI
    """
    
    def __init__(self):
        self.logger = logger
        self.config = VISUALIZATION_CONFIG
        self.reports_dir = REPORTS_DIR
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def create_comprehensive_report(self, results_df: pd.DataFrame, 
                                  input_df: Optional[pd.DataFrame] = None,
                                  params_df: Optional[pd.DataFrame] = None,
                                  output_name: str = "relatorio_tri") -> str:
        """
        Cria relatório completo com todas as visualizações
        
        Args:
            results_df: DataFrame com resultados
            input_df: DataFrame com dados de entrada (opcional)
            params_df: DataFrame com parâmetros (opcional)
            output_name: Nome do arquivo de saída
            
        Returns:
            Caminho do arquivo HTML gerado
        """
        try:
            self.logger.info("Criando relatório completo")
            
            # Criar figura com subplots
            fig = make_subplots(
                rows=3, cols=2,
                subplot_titles=(
                    'Distribuição de Theta', 'Distribuição de Notas ENEM',
                    'Theta vs Acertos', 'Distribuição de Acertos',
                    'Parâmetros dos Itens', 'Correlação Theta-ENEM'
                ),
                specs=[[{"secondary_y": False}, {"secondary_y": False}],
                       [{"secondary_y": False}, {"secondary_y": False}],
                       [{"secondary_y": False}, {"secondary_y": False}]]
            )
            
            # 1. Distribuição de Theta
            fig.add_trace(
                go.Histogram(x=results_df['theta'], name='Theta', nbinsx=30),
                row=1, col=1
            )
            
            # 2. Distribuição de Notas ENEM
            fig.add_trace(
                go.Histogram(x=results_df['enem_score'], name='ENEM Score', nbinsx=30),
                row=1, col=2
            )
            
            # 3. Theta vs Acertos
            if 'acertos' in results_df.columns:
                fig.add_trace(
                    go.Scatter(x=results_df['acertos'], y=results_df['theta'], 
                              mode='markers', name='Theta vs Acertos'),
                    row=2, col=1
                )
            
            # 4. Distribuição de Acertos
            if 'acertos' in results_df.columns:
                fig.add_trace(
                    go.Histogram(x=results_df['acertos'], name='Acertos', nbinsx=20),
                    row=2, col=2
                )
            
            # 5. Parâmetros dos Itens
            if params_df is not None:
                fig.add_trace(
                    go.Scatter(x=params_df.index, y=params_df['a'], 
                              mode='lines+markers', name='Parâmetro a'),
                    row=3, col=1
                )
                fig.add_trace(
                    go.Scatter(x=params_df.index, y=params_df['b'], 
                              mode='lines+markers', name='Parâmetro b'),
                    row=3, col=1
                )
            
            # 6. Correlação Theta-ENEM
            fig.add_trace(
                go.Scatter(x=results_df['theta'], y=results_df['enem_score'], 
                          mode='markers', name='Theta vs ENEM'),
                row=3, col=2
            )
            
            # Atualizar layout
            fig.update_layout(
                height=1200,
                width=1200,
                title_text="Relatório Completo - Sistema TRI",
                showlegend=True
            )
            
            # Salvar como HTML
            output_path = self.reports_dir / f"{output_name}.html"
            fig.write_html(str(output_path))
            
            self.logger.info(f"Relatório salvo em: {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"Erro ao criar relatório completo: {e}")
            raise
    
    def plot_theta_distribution(self, results_df: pd.DataFrame, 
                              save_path: Optional[str] = None) -> None:
        """
        Plota distribuição de theta
        
        Args:
            results_df: DataFrame com resultados
            save_path: Caminho para salvar (opcional)
        """
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=self.config["figure_size"])
            
            # Histograma
            ax1.hist(results_df['theta'], bins=30, edgecolor='black', alpha=0.7)
            ax1.set_title('Distribuição de Theta')
            ax1.set_xlabel('Theta')
            ax1.set_ylabel('Frequência')
            ax1.grid(True, alpha=0.3)
            
            # Boxplot
            ax2.boxplot(results_df['theta'])
            ax2.set_title('Boxplot de Theta')
            ax2.set_ylabel('Theta')
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=self.config["dpi"], bbox_inches='tight')
                self.logger.info(f"Gráfico salvo em: {save_path}")
            else:
                plt.show()
            
            plt.close()
            
        except Exception as e:
            self.logger.error(f"Erro ao plotar distribuição de theta: {e}")
    
    def plot_enem_distribution(self, results_df: pd.DataFrame, 
                             save_path: Optional[str] = None) -> None:
        """
        Plota distribuição de notas ENEM
        
        Args:
            results_df: DataFrame com resultados
            save_path: Caminho para salvar (opcional)
        """
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=self.config["figure_size"])
            
            # Histograma
            ax1.hist(results_df['enem_score'], bins=30, edgecolor='black', alpha=0.7)
            ax1.set_title('Distribuição de Notas ENEM')
            ax1.set_xlabel('Nota ENEM')
            ax1.set_ylabel('Frequência')
            ax1.grid(True, alpha=0.3)
            
            # Boxplot
            ax2.boxplot(results_df['enem_score'])
            ax2.set_title('Boxplot de Notas ENEM')
            ax2.set_ylabel('Nota ENEM')
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=self.config["dpi"], bbox_inches='tight')
                self.logger.info(f"Gráfico salvo em: {save_path}")
            else:
                plt.show()
            
            plt.close()
            
        except Exception as e:
            self.logger.error(f"Erro ao plotar distribuição ENEM: {e}")
    
    def plot_theta_vs_acertos(self, results_df: pd.DataFrame, 
                            save_path: Optional[str] = None) -> None:
        """
        Plota relação entre theta e acertos
        
        Args:
            results_df: DataFrame com resultados
            save_path: Caminho para salvar (opcional)
        """
        try:
            if 'acertos' not in results_df.columns:
                self.logger.warning("Coluna 'acertos' não encontrada")
                return
            
            fig, ax = plt.subplots(figsize=self.config["figure_size"])
            
            # Scatter plot
            scatter = ax.scatter(results_df['acertos'], results_df['theta'], 
                               alpha=0.6, s=30)
            
            # Linha de tendência
            z = np.polyfit(results_df['acertos'], results_df['theta'], 1)
            p = np.poly1d(z)
            ax.plot(results_df['acertos'], p(results_df['acertos']), 
                   "r--", alpha=0.8, linewidth=2)
            
            # Calcular correlação
            correlation = results_df['acertos'].corr(results_df['theta'])
            
            ax.set_title(f'Theta vs Acertos (r = {correlation:.3f})')
            ax.set_xlabel('Número de Acertos')
            ax.set_ylabel('Theta')
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=self.config["dpi"], bbox_inches='tight')
                self.logger.info(f"Gráfico salvo em: {save_path}")
            else:
                plt.show()
            
            plt.close()
            
        except Exception as e:
            self.logger.error(f"Erro ao plotar theta vs acertos: {e}")
    
    def plot_item_parameters(self, params_df: pd.DataFrame, 
                           save_path: Optional[str] = None) -> None:
        """
        Plota parâmetros dos itens
        
        Args:
            params_df: DataFrame com parâmetros
            save_path: Caminho para salvar (opcional)
        """
        try:
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            
            # Parâmetro a (discriminação)
            ax1.plot(params_df.index, params_df['a'], 'o-', alpha=0.7)
            ax1.set_title('Parâmetro a (Discriminação)')
            ax1.set_xlabel('Item')
            ax1.set_ylabel('Valor')
            ax1.grid(True, alpha=0.3)
            
            # Parâmetro b (dificuldade)
            ax2.plot(params_df.index, params_df['b'], 's-', alpha=0.7, color='orange')
            ax2.set_title('Parâmetro b (Dificuldade)')
            ax2.set_xlabel('Item')
            ax2.set_ylabel('Valor')
            ax2.grid(True, alpha=0.3)
            
            # Parâmetro c (acerto casual)
            ax3.plot(params_df.index, params_df['c'], '^-', alpha=0.7, color='green')
            ax3.set_title('Parâmetro c (Acerto Casual)')
            ax3.set_xlabel('Item')
            ax3.set_ylabel('Valor')
            ax3.grid(True, alpha=0.3)
            
            # Distribuição dos parâmetros
            ax4.hist(params_df['a'], bins=15, alpha=0.7, label='a', edgecolor='black')
            ax4.hist(params_df['b'], bins=15, alpha=0.7, label='b', edgecolor='black')
            ax4.hist(params_df['c'], bins=15, alpha=0.7, label='c', edgecolor='black')
            ax4.set_title('Distribuição dos Parâmetros')
            ax4.set_xlabel('Valor')
            ax4.set_ylabel('Frequência')
            ax4.legend()
            ax4.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=self.config["dpi"], bbox_inches='tight')
                self.logger.info(f"Gráfico salvo em: {save_path}")
            else:
                plt.show()
            
            plt.close()
            
        except Exception as e:
            self.logger.error(f"Erro ao plotar parâmetros dos itens: {e}")
    
    def create_summary_statistics(self, results_df: pd.DataFrame, 
                                input_df: Optional[pd.DataFrame] = None) -> Dict[str, any]:
        """
        Cria estatísticas resumidas
        
        Args:
            results_df: DataFrame com resultados
            input_df: DataFrame com dados de entrada (opcional)
            
        Returns:
            Dicionário com estatísticas
        """
        try:
            stats = {}
            
            # Estatísticas básicas
            stats['total_students'] = len(results_df)
            stats['theta_mean'] = results_df['theta'].mean()
            stats['theta_std'] = results_df['theta'].std()
            stats['theta_min'] = results_df['theta'].min()
            stats['theta_max'] = results_df['theta'].max()
            
            stats['enem_mean'] = results_df['enem_score'].mean()
            stats['enem_std'] = results_df['enem_score'].std()
            stats['enem_min'] = results_df['enem_score'].min()
            stats['enem_max'] = results_df['enem_score'].max()
            
            # Percentis
            percentiles = [10, 25, 50, 75, 90]
            stats['theta_percentiles'] = {
                f'p{p}': np.percentile(results_df['theta'], p) 
                for p in percentiles
            }
            stats['enem_percentiles'] = {
                f'p{p}': np.percentile(results_df['enem_score'], p) 
                for p in percentiles
            }
            
            # Se tiver dados de entrada
            if input_df is not None:
                stats['total_items'] = input_df['Questao'].nunique()
                stats['total_responses'] = len(input_df)
                
                if 'acertos' in results_df.columns:
                    stats['acertos_mean'] = results_df['acertos'].mean()
                    stats['acertos_std'] = results_df['acertos'].std()
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Erro ao criar estatísticas: {e}")
            return {}
    
    def save_summary_report(self, results_df: pd.DataFrame, 
                          stats: Dict[str, any], 
                          output_name: str = "resumo_estatistico") -> str:
        """
        Salva relatório resumido em HTML
        
        Args:
            results_df: DataFrame com resultados
            stats: Dicionário com estatísticas
            output_name: Nome do arquivo
            
        Returns:
            Caminho do arquivo gerado
        """
        try:
            # Criar HTML
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Relatório Resumido - Sistema TRI</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                    .stats {{ margin: 20px 0; }}
                    .stat-item {{ margin: 10px 0; }}
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Relatório Resumido - Sistema TRI</h1>
                    <p>Data de geração: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <div class="stats">
                    <h2>Estatísticas Gerais</h2>
                    <div class="stat-item"><strong>Total de Estudantes:</strong> {stats.get('total_students', 'N/A')}</div>
                    <div class="stat-item"><strong>Total de Itens:</strong> {stats.get('total_items', 'N/A')}</div>
                    <div class="stat-item"><strong>Total de Respostas:</strong> {stats.get('total_responses', 'N/A')}</div>
                </div>
                
                <div class="stats">
                    <h2>Estatísticas de Theta</h2>
                    <div class="stat-item"><strong>Média:</strong> {stats.get('theta_mean', 'N/A'):.3f}</div>
                    <div class="stat-item"><strong>Desvio Padrão:</strong> {stats.get('theta_std', 'N/A'):.3f}</div>
                    <div class="stat-item"><strong>Mínimo:</strong> {stats.get('theta_min', 'N/A'):.3f}</div>
                    <div class="stat-item"><strong>Máximo:</strong> {stats.get('theta_max', 'N/A'):.3f}</div>
                </div>
                
                <div class="stats">
                    <h2>Estatísticas de Nota ENEM</h2>
                    <div class="stat-item"><strong>Média:</strong> {stats.get('enem_mean', 'N/A'):.1f}</div>
                    <div class="stat-item"><strong>Desvio Padrão:</strong> {stats.get('enem_std', 'N/A'):.1f}</div>
                    <div class="stat-item"><strong>Mínimo:</strong> {stats.get('enem_min', 'N/A'):.0f}</div>
                    <div class="stat-item"><strong>Máximo:</strong> {stats.get('enem_max', 'N/A'):.0f}</div>
                </div>
            </body>
            </html>
            """
            
            # Salvar arquivo
            output_path = self.reports_dir / f"{output_name}.html"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"Relatório resumido salvo em: {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar relatório resumido: {e}")
            raise
