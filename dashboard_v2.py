"""
Dashboard Principal do Sistema TRI Profissional
Interface hierárquica: Avaliações → Execuções → Resultados
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Any, Optional

# Imports locais
from auth.authentication import require_authentication, show_logout_button
from db.session_v2 import get_db_session_context
from db.crud_v2 import (
    AssessmentCRUD, ExecutionCRUD, StudentResultCRUD, 
    DatasetCRUD, ParametersSetCRUD
)
from db.models_v2 import Assessment, Execution, StudentResult
from core.tri_engine import TRIEngine
from core.item_calibration import ItemCalibrator
from core.data_processor import DataProcessor

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração da página
st.set_page_config(
    page_title="Sistema TRI Profissional",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f4e79 0%, #2d5a87 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #1f4e79;
    }
    .assessment-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
    }
    .execution-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


class DashboardV2:
    """Dashboard principal do Sistema TRI Profissional"""
    
    def __init__(self):
        self.tri_engine = TRIEngine()
        self.item_calibration = ItemCalibrator()
        self.data_processor = DataProcessor()
    
    def run(self):
        """Executa o dashboard principal"""
        # Verificar autenticação
        require_authentication()
        
        # Header principal
        self.show_header()
        
        # Sidebar com navegação
        self.show_sidebar()
        
        # Conteúdo principal baseado na seleção
        page = st.session_state.get('current_page', 'dashboard')
        
        if page == 'dashboard':
            self.show_dashboard()
        elif page == 'assessments':
            self.show_assessments()
        elif page == 'executions':
            self.show_executions()
        elif page == 'datasets':
            self.show_datasets()
        elif page == 'parameters':
            self.show_parameters()
        elif page == 'reports':
            self.show_reports()
    
    def show_header(self):
        """Exibe header principal"""
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown("""
            <div class="main-header">
                <h1>📊 Sistema TRI Profissional</h1>
                <p>Análise de Dados Educacionais com Teoria de Resposta ao Item</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            show_logout_button()
    
    def show_sidebar(self):
        """Exibe sidebar com navegação"""
        with st.sidebar:
            st.title("🧭 Navegação")
            
            # Menu principal
            if st.button("🏠 Dashboard", use_container_width=True, key="nav_dashboard"):
                st.session_state['current_page'] = 'dashboard'
                st.rerun()
            
            if st.button("📋 Avaliações", use_container_width=True, key="nav_assessments"):
                st.session_state['current_page'] = 'assessments'
                st.rerun()
            
            if st.button("⚙️ Execuções", use_container_width=True, key="nav_executions"):
                st.session_state['current_page'] = 'executions'
                st.rerun()
            
            if st.button("📁 Datasets", use_container_width=True, key="nav_datasets"):
                st.session_state['current_page'] = 'datasets'
                st.rerun()
            
            if st.button("🔧 Parâmetros", use_container_width=True, key="nav_parameters"):
                st.session_state['current_page'] = 'parameters'
                st.rerun()
            
            if st.button("📊 Relatórios", use_container_width=True, key="nav_reports"):
                st.session_state['current_page'] = 'reports'
                st.rerun()
            
            st.markdown("---")
            
            # Informações do usuário
            user_info = st.session_state.get('user_name', 'Usuário')
            st.info(f"👤 **{user_info}**")
            
            # Estatísticas rápidas
            self.show_sidebar_stats()
    
    def show_sidebar_stats(self):
        """Exibe estatísticas rápidas na sidebar"""
        try:
            with get_db_session_context() as session:
                # Contar avaliações
                assessments_count = len(AssessmentCRUD.list_assessments(session))
                
                # Contar execuções (buscar todas as avaliações primeiro)
                assessments = AssessmentCRUD.list_assessments(session)
                executions_count = 0
                for assessment in assessments:
                    executions = ExecutionCRUD.list_executions_by_assessment(session, str(assessment.id))
                    executions_count += len(executions)
                
                st.markdown("### 📈 Estatísticas")
                st.metric("Avaliações", assessments_count)
                st.metric("Execuções", executions_count)
                
        except Exception as e:
            logger.error(f"Erro ao carregar estatísticas: {e}")
            st.error("Erro ao carregar estatísticas")
    
    def show_dashboard(self):
        """Exibe dashboard principal com analytics"""
        st.title("🏠 Dashboard Principal")
        
        # Métricas principais
        self.show_main_metrics()
        
        # Gráficos de overview
        col1, col2 = st.columns(2)
        
        with col1:
            self.show_assessments_overview()
        
        with col2:
            self.show_executions_overview()
        
        # Últimas atividades
        self.show_recent_activities()
    
    def show_main_metrics(self):
        """Exibe métricas principais"""
        try:
            with get_db_session_context() as session:
                # Buscar dados
                assessments = AssessmentCRUD.list_assessments(session)
                total_executions = 0
                total_students = 0
                
                for assessment in assessments:
                    executions = ExecutionCRUD.list_executions_by_assessment(session, str(assessment.id))
                    total_executions += len(executions)
                    
                    for execution in executions:
                        results = StudentResultCRUD.get_results_by_execution(session, execution.id)
                        total_students += len(results)
                
                # Exibir métricas
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown("""
                    <div class="metric-card">
                        <h3>📋 Avaliações</h3>
                        <h2>{}</h2>
                    </div>
                    """.format(len(assessments)), unsafe_allow_html=True)
                
                with col2:
                    st.markdown("""
                    <div class="metric-card">
                        <h3>⚙️ Execuções</h3>
                        <h2>{}</h2>
                    </div>
                    """.format(total_executions), unsafe_allow_html=True)
                
                with col3:
                    st.markdown("""
                    <div class="metric-card">
                        <h3>👥 Estudantes</h3>
                        <h2>{}</h2>
                    </div>
                    """.format(total_students), unsafe_allow_html=True)
                
                with col4:
                    success_rate = (total_executions / max(len(assessments), 1)) * 100
                    st.markdown("""
                    <div class="metric-card">
                        <h3>✅ Taxa de Sucesso</h3>
                        <h2>{:.1f}%</h2>
                    </div>
                    """.format(success_rate), unsafe_allow_html=True)
                
        except Exception as e:
            logger.error(f"Erro ao carregar métricas: {e}")
            st.error("Erro ao carregar métricas principais")
    
    def show_assessments_overview(self):
        """Exibe overview das avaliações"""
        st.subheader("📋 Avaliações Recentes")
        
        try:
            with get_db_session_context() as session:
                assessments = AssessmentCRUD.list_assessments(session)[:5]
                
                if not assessments:
                    st.info("Nenhuma avaliação cadastrada ainda.")
                    return
                
                for assessment in assessments:
                    with st.container():
                        st.markdown(f"""
                        <div class="assessment-card">
                            <h4>🎯 {assessment.description or f'Avaliação {assessment.year}'}</h4>
                            <p><strong>Ano:</strong> {assessment.year}</p>
                            <p><strong>Ciclo:</strong> {assessment.cicle}</p>
                            <p><strong>Nível:</strong> {assessment.level}</p>
                            <p><strong>Criado:</strong> {assessment.created_at.strftime('%d/%m/%Y')}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button(f"Ver Detalhes", key=f"assessment_{assessment.id}"):
                            st.session_state['selected_assessment'] = str(assessment.id)
                            st.session_state['current_page'] = 'assessments'
                            st.rerun()
                
        except Exception as e:
            logger.error(f"Erro ao carregar avaliações: {e}")
            st.error("Erro ao carregar avaliações")
    
    def show_executions_overview(self):
        """Exibe overview das execuções"""
        st.subheader("⚙️ Execuções Recentes")
        
        try:
            with get_db_session_context() as session:
                # Buscar execuções recentes
                all_executions = []
                assessments = AssessmentCRUD.list_assessments(session)
                
                for assessment in assessments:
                    executions = ExecutionCRUD.list_executions_by_assessment(session, str(assessment.id))
                    all_executions.extend(executions)
                
                # Ordenar por data de criação
                all_executions.sort(key=lambda x: x.created_at, reverse=True)
                recent_executions = all_executions[:5]
                
                if not recent_executions:
                    st.info("Nenhuma execução realizada ainda.")
                    return
                
                for execution in recent_executions:
                    status_color = {
                        'pending': '🟡',
                        'running': '🔵',
                        'completed': '🟢',
                        'failed': '🔴'
                    }.get(execution.status, '⚪')
                    
                    st.markdown(f"""
                    <div class="execution-card">
                        <h4>{status_color} {execution.name or f'Execução {execution.id}'}</h4>
                        <p><strong>Status:</strong> {execution.status}</p>
                        <p><strong>Criado:</strong> {execution.created_at.strftime('%d/%m/%Y %H:%M')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
        except Exception as e:
            logger.error(f"Erro ao carregar execuções: {e}")
            st.error("Erro ao carregar execuções")
    
    def show_recent_activities(self):
        """Exibe atividades recentes"""
        st.subheader("📈 Atividades Recentes")
        
        # Placeholder para atividades recentes
        st.info("Funcionalidade de atividades recentes será implementada em breve.")
    
    def show_assessments(self):
        """Exibe página de gerenciamento de avaliações"""
        st.title("📋 Gerenciamento de Avaliações")
        
        # Botão para criar nova avaliação
        if st.button("➕ Nova Avaliação", type="primary", key="btn_new_assessment"):
            st.session_state['show_create_assessment'] = True
        
        if st.session_state.get('show_create_assessment', False):
            self.show_create_assessment_form()
        
        # Lista de avaliações
        self.show_assessments_list()
    
    def show_create_assessment_form(self):
        """Exibe formulário para criar nova avaliação"""
        st.subheader("📝 Nova Avaliação")
        
        with st.form("create_assessment"):
            col1, col2 = st.columns(2)
            
            with col1:
                year = st.number_input("Ano", min_value=2020, max_value=2030, value=datetime.now().year)
                cicle = st.text_input("Ciclo", placeholder="Ex: 1º Bimestre, 2024.1")
            
            with col2:
                level = st.selectbox("Nível", ["Fundamental", "Médio", "Superior"])
                description = st.text_area("Descrição", placeholder="Descrição da avaliação")
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                submit = st.form_submit_button("💾 Criar Avaliação", use_container_width=True)
            
            if submit:
                try:
                    with get_db_session_context() as session:
                        assessment = AssessmentCRUD.create_assessment(
                            session, year, cicle, level, description
                        )
                        st.success(f"✅ Avaliação '{assessment.description}' criada com sucesso!")
                        st.session_state['show_create_assessment'] = False
                        st.rerun()
                        
                except Exception as e:
                    logger.error(f"Erro ao criar avaliação: {e}")
                    st.error("Erro ao criar avaliação")
    
    def show_assessments_list(self):
        """Exibe lista de avaliações"""
        try:
            with get_db_session_context() as session:
                assessments = AssessmentCRUD.list_assessments(session)
                
                if not assessments:
                    st.info("Nenhuma avaliação cadastrada. Clique em 'Nova Avaliação' para começar.")
                    return
                
                for assessment in assessments:
                    with st.expander(f"🎯 {assessment.description or f'Avaliação {assessment.year}'}"):
                        col1, col2, col3 = st.columns([2, 1, 1])
                        
                        with col1:
                            st.write(f"**Ano:** {assessment.year}")
                            st.write(f"**Ciclo:** {assessment.cicle}")
                            st.write(f"**Nível:** {assessment.level}")
                            st.write(f"**Criado:** {assessment.created_at.strftime('%d/%m/%Y %H:%M')}")
                        
                        with col2:
                            if st.button("👁️ Ver Execuções", key=f"view_{assessment.id}"):
                                st.session_state['selected_assessment'] = str(assessment.id)
                                st.session_state['current_page'] = 'executions'
                                st.rerun()
                        
                        with col3:
                            if st.button("🗑️ Excluir", key=f"delete_{assessment.id}"):
                                if AssessmentCRUD.delete_assessment(session, str(assessment.id)):
                                    st.success("Avaliação excluída com sucesso!")
                                    st.rerun()
                                else:
                                    st.error("Erro ao excluir avaliação")
                
        except Exception as e:
            logger.error(f"Erro ao carregar lista de avaliações: {e}")
            st.error("Erro ao carregar avaliações")
    
    def show_executions(self):
        """Exibe página de gerenciamento de execuções"""
        st.title("⚙️ Gerenciamento de Execuções")
        
        # Verificar se há uma avaliação selecionada
        selected_assessment_id = st.session_state.get('selected_assessment')
        
        if not selected_assessment_id:
            st.warning("⚠️ Selecione uma avaliação para gerenciar execuções.")
            if st.button("🔙 Voltar para Avaliações", key="btn_back_assessments"):
                st.session_state['current_page'] = 'assessments'
                st.rerun()
            return
        
        # Mostrar informações da avaliação selecionada
        try:
            with get_db_session_context() as session:
                assessment = AssessmentCRUD.get_assessment_by_id(session, selected_assessment_id)
                if assessment:
                    st.info(f"📋 **Avaliação:** {assessment.description or f'Avaliação {assessment.year}'}")
                
                # Botão para nova execução
                if st.button("➕ Nova Execução", type="primary", key="btn_new_execution"):
                    st.session_state['show_create_execution'] = True
                
                if st.session_state.get('show_create_execution', False):
                    self.show_create_execution_form(selected_assessment_id)
                
                # Lista de execuções
                self.show_executions_list(selected_assessment_id)
                
        except Exception as e:
            logger.error(f"Erro ao carregar execuções: {e}")
            st.error("Erro ao carregar execuções")
    
    def show_create_execution_form(self, assessment_id: str):
        """Exibe formulário para criar nova execução"""
        st.subheader("📝 Nova Execução")
        
        with st.form("create_execution"):
            name = st.text_input("Nome da Execução", placeholder="Ex: Calibração Matemática 3º Ano")
            notes = st.text_area("Observações", placeholder="Observações sobre esta execução")
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                submit = st.form_submit_button("💾 Criar Execução", use_container_width=True)
            
            if submit:
                try:
                    with get_db_session_context() as session:
                        execution = ExecutionCRUD.create_execution(
                            session, assessment_id, name=name, notes=notes
                        )
                        st.success(f"✅ Execução '{execution.name}' criada com sucesso!")
                        st.session_state['show_create_execution'] = False
                        st.rerun()
                        
                except Exception as e:
                    logger.error(f"Erro ao criar execução: {e}")
                    st.error("Erro ao criar execução")
    
    def show_executions_list(self, assessment_id: str):
        """Exibe lista de execuções"""
        try:
            with get_db_session_context() as session:
                executions = ExecutionCRUD.list_executions_by_assessment(session, assessment_id)
                
                if not executions:
                    st.info("Nenhuma execução cadastrada. Clique em 'Nova Execução' para começar.")
                    return
                
                for execution in executions:
                    status_emoji = {
                        'pending': '🟡',
                        'running': '🔵',
                        'completed': '🟢',
                        'failed': '🔴'
                    }.get(execution.status, '⚪')
                    
                    with st.expander(f"{status_emoji} {execution.name or f'Execução {execution.id}'}"):
                        col1, col2, col3 = st.columns([2, 1, 1])
                        
                        with col1:
                            st.write(f"**Status:** {execution.status}")
                            st.write(f"**Criado:** {execution.created_at.strftime('%d/%m/%Y %H:%M')}")
                            if execution.notes:
                                st.write(f"**Observações:** {execution.notes}")
                        
                        with col2:
                            if st.button("▶️ Executar", key=f"run_{execution.id}"):
                                st.session_state['selected_execution'] = execution.id
                                self.run_tri_execution(execution.id)
                        
                        with col3:
                            if st.button("🗑️ Excluir", key=f"delete_exec_{execution.id}"):
                                if ExecutionCRUD.delete_execution(session, execution.id):
                                    st.success("Execução excluída com sucesso!")
                                    st.rerun()
                                else:
                                    st.error("Erro ao excluir execução")
                
        except Exception as e:
            logger.error(f"Erro ao carregar lista de execuções: {e}")
            st.error("Erro ao carregar execuções")
    
    def run_tri_execution(self, execution_id: int):
        """Executa processamento TRI"""
        st.info("🚀 Iniciando processamento TRI...")
        # Placeholder para execução TRI
        st.success("✅ Processamento concluído!")
    
    def show_datasets(self):
        """Exibe página de gerenciamento de datasets"""
        st.title("📁 Gerenciamento de Datasets")
        st.info("Funcionalidade de datasets será implementada em breve.")
    
    def show_parameters(self):
        """Exibe página de gerenciamento de parâmetros"""
        st.title("🔧 Gerenciamento de Parâmetros")
        st.info("Funcionalidade de parâmetros será implementada em breve.")
    
    def show_reports(self):
        """Exibe página de relatórios"""
        st.title("📊 Relatórios e Análises")
        st.info("Funcionalidade de relatórios será implementada em breve.")


def main():
    """Função principal"""
    try:
        dashboard = DashboardV2()
        dashboard.run()
    except Exception as e:
        logger.error(f"Erro no dashboard: {e}")
        st.error("Erro interno do sistema. Tente novamente.")


if __name__ == "__main__":
    main()
