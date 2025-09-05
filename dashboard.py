"""
Dashboard Web para o Sistema TRI
Interface gráfica para visualização e análise
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import io
import base64

# Importar módulos do sistema
from core.tri_engine import TRIEngine
from core.data_processor import DataProcessor
from core.validators import DataValidator
from core.item_calibration import ItemCalibrator
from utils.visualizations import TRIVisualizer
from config.settings import get_config
from db.session import Base, engine, SessionLocal
from db import crud

# Configurar página
st.set_page_config(
    page_title="Sistema TRI - Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Configurar estilo
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)


class TRIDashboard:
    """
    Dashboard web para o sistema TRI
    """
    
    def __init__(self):
        self.tri_engine = TRIEngine()
        self.data_processor = DataProcessor()
        self.validator = DataValidator()
        self.calibrator = ItemCalibrator()
        self.visualizer = TRIVisualizer()
        self.config = get_config()
        self.chart_counter = 0
        
        # Garantir que as tabelas do banco existam
        try:
            Base.metadata.create_all(bind=engine)
        except Exception:
            pass
        
        # Inicializar contador global de gráficos no session state
        if 'global_chart_counter' not in st.session_state:
            st.session_state['global_chart_counter'] = 0
        
        # Configurar autenticação
        if 'authenticated' not in st.session_state:
            st.session_state['authenticated'] = False
        
        # Configurar diretório de salvamento (mantido para compatibilidade de download local)
        self.save_dir = Path("saved_results")
        self.save_dir.mkdir(exist_ok=True)
    
    def get_unique_key(self, prefix: str) -> str:
        """Gera uma chave única para elementos Streamlit"""
        st.session_state['global_chart_counter'] += 1
        return f"{prefix}_{st.session_state['global_chart_counter']}"
    
    def authenticate(self):
        """Sistema de autenticação simples"""
        if not st.session_state['authenticated']:
            st.markdown('<h1 class="main-header">🔐 Sistema TRI - Login</h1>', unsafe_allow_html=True)
            
            with st.form("login_form"):
                username = st.text_input("👤 Usuário")
                password = st.text_input("🔒 Senha", type="password")
                submit_button = st.form_submit_button("🚀 Entrar")
                
                if submit_button:
                    # Credenciais simples (em produção, usar hash e banco de dados)
                    if username == "admin" and password == "tri2025":
                        st.session_state['authenticated'] = True
                        st.success("✅ Login realizado com sucesso!")
                        st.rerun()
                    else:
                        st.error("❌ Usuário ou senha incorretos!")
            return False
        return True
    
    def run(self):
        """Executa o dashboard"""
        # Verificar autenticação
        if not self.authenticate():
            return
        
        # Header
        st.markdown('<h1 class="main-header">📊 Sistema TRI - Dashboard</h1>', unsafe_allow_html=True)
        st.markdown("### Teoria de Resposta ao Item - Modelo ENEM/SAEB")
        

        
        # Botão de logout
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🚪 Logout"):
                st.session_state['authenticated'] = False
                st.rerun()
        
        # Main content tab5,
        tab1, tab2, tab3, tab4, tab6, tab7 = st.tabs([
            "📁 Upload de Dados", 
            "🔧 Calibração de Itens", 
            "📊 Processamento TRI", 
            "📈 Visualizações",
            # "🔄 Equating de Escalas",
            "💾 Histórico",
            "📋 Parâmetros Salvos"
        ])
        
        # Aba 1: Upload de Dados
        with tab1:
            self.upload_data_tab()
        
        # Aba 2: Calibração de Itens
        with tab2:
            self.calibration_tab()
        
        # Aba 3: Processamento TRI
        with tab3:
            self.tri_processing_tab()
        
        # Aba 4: Visualizações
        with tab4:
            self.visualizations_tab()
        
        # Aba 5: Equating de Escalas
        # with tab5:
        #     self.equating_tab()
        
        # Aba 6: Histórico
        with tab6:
            self.history_tab()
        
        # Aba 7: Parâmetros Salvos
        with tab7:
            self.parameters_tab()
    
    def upload_data_tab(self):
        """Aba de upload de dados"""
        st.header("📁 Upload de Dados")
        
        # Upload de arquivo de respostas
        uploaded_file = st.file_uploader(
            "📄 Arquivo de Respostas dos Alunos",
            type=['csv', 'xlsx'],
            help="Suporte a CSV (separador ;) e Excel"
        )
        
        if uploaded_file is not None:
            try:
                # Detectar tipo de arquivo
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8')
                    st.success(f"✅ CSV carregado: {len(df)} linhas, {len(df.columns)} colunas")
                elif uploaded_file.name.endswith('.xlsx'):
                    # Processar Excel usando DataProcessor
                    try:
                        df = self.data_processor.load_responses_excel_from_streamlit(uploaded_file)
                        st.success(f"✅ Excel processado: {len(df)} linhas, {len(df.columns)} colunas")
                    except Exception as e:
                        st.error(f"❌ Erro ao processar Excel: {e}")
                        st.info("💡 Verifique se o arquivo tem as abas 'Datos' e 'Matriz'")
                        return
                
                # Mostrar preview
                st.subheader("👀 Preview dos Dados")
                st.dataframe(df.head(), use_container_width=True)
                
                # Validar dados
                st.info("🔍 Validando dados...")
                
                # Mostrar estrutura do arquivo
                st.write("**📋 Estrutura do arquivo:**")
                st.write(f"- **Colunas disponíveis:** {list(df.columns)}")
                st.write(f"- **Total de linhas:** {len(df)}")
                st.write(f"- **Primeiras linhas:**")
                st.dataframe(df.head(3), use_container_width=True)
                
                validation_result = self.data_processor.validate_data_quality(df)
                if validation_result and len(validation_result) > 0:
                    st.success("✅ Dados validados com sucesso!")
                    
                    # Mostrar métricas de qualidade
                    with st.expander("📊 Métricas de Qualidade dos Dados"):
                        if validation_result.get('format_type') == 'excel_cartao_resposta':
                            # Formato Excel original
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Formato", "Excel Cartão Resposta")
                                st.metric("Total de Alunos", validation_result.get('total_students', 0))
                            with col2:
                                st.metric("Total de Itens", validation_result.get('total_items', 0))
                                st.metric("Completude", f"{validation_result.get('completeness', 0):.1%}")
                            with col3:
                                st.metric("Total de Respostas", validation_result.get('total_responses', 0))
                                st.metric("Variedade de Respostas", validation_result.get('response_variety', 0))
                            
                            # Mostrar informações específicas do formato Excel
                            if 'unique_responses' in validation_result:
                                st.write("**🎯 Respostas possíveis:**", validation_result['unique_responses'])
                        else:
                            # Formato processado
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Total de Alunos", validation_result.get('total_students', 0))
                                st.metric("Total de Itens", validation_result.get('total_items', 0))
                            with col2:
                                st.metric("Completude", f"{validation_result.get('completeness', 0):.1%}")
                                st.metric("Acertos Médios", f"{validation_result.get('mean_accuracy', 0):.1%}")
                            with col3:
                                st.metric("Total de Respostas", validation_result.get('total_responses', 0))
                                st.metric("Alunos Incompletos", validation_result.get('incomplete_students', 0))
                    
                    st.session_state['uploaded_data'] = df
                    st.session_state['uploaded_filename'] = uploaded_file.name
                else:
                    st.error("❌ Dados não passaram na validação")
                    st.info("💡 **Formato Excel esperado:**")
                    st.info("   - Aba 'Datos' com colunas: CodPessoa, Ítem 1 ID 123, Ítem 2 ID 456, etc.")
                    st.info("   - Aba 'Matriz' com gabarito dos itens")
                    st.info("💡 **Formato alternativo:**")
                    st.info("   - Colunas: CodPessoa, Questao, RespostaAluno, Gabarito")
                    st.info("   - Uma linha por resposta (aluno + questão)")
                    
            except Exception as e:
                st.error(f"❌ Erro ao processar arquivo: {e}")
    
    def calibration_tab(self):
        """Aba de parâmetros: subir âncoras ou selecionar conjuntos salvos"""
        st.header("🔧 Calibração de Itens")
        
        if 'uploaded_data' not in st.session_state:
            st.warning("⚠️ Faça upload de dados primeiro na aba 'Upload de Dados'")
            return
        
        responses_df = st.session_state['uploaded_data']
        
        # Fonte dos parâmetros
        st.subheader("⚙️ Fonte dos Parâmetros")
        
        col1, col2 = st.columns(2)
        
        with col1:
            source = st.radio("Selecione a fonte:", ["Arquivo de Âncoras (CSV)", "Conjunto Salvo"], horizontal=True)
            anchor_file = None
            selected_param_set_id = None
            if source == "Arquivo de Âncoras (CSV)":
                anchor_file = st.file_uploader("Arquivo de itens âncora (CSV)", type=['csv'])
            else:
                try:
                    session = SessionLocal()
                    sets = crud.list_parameter_sets(session)
                finally:
                    session.close()
                if not sets:
                    st.info("Nenhum conjunto salvo. Faça upload de parâmetros ou calibre e salve.")
                else:
                    options = {f"#{s['id']} - {s['name']} ({s['num_items']} itens)": s['id'] for s in sets}
                    choice = st.selectbox("Conjuntos de parâmetros salvos:", list(options.keys()))
                    selected_param_set_id = options.get(choice)
        
        with col2:
            calibration_method = st.selectbox("Método de Calibração:", ["3PL - Máxima Verossimilhança"])        
        
        # Botão principal da aba: calibrar (a partir de âncoras opcionais) ou carregar conjunto salvo
        if st.button("Aplicar Parâmetros / Calibrar", type="primary"):
            with st.spinner("Calibrando parâmetros dos itens..."):
                try:
                    params_df = None
                    anchor_items = None
                    if source == "Arquivo de Âncoras (CSV)" and anchor_file is not None:
                        try:
                            try:
                                anchor_df = pd.read_csv(anchor_file)
                            except:
                                anchor_file.seek(0)
                                anchor_df = pd.read_csv(anchor_file, sep=';')
                            anchor_items = {}
                            for _, row in anchor_df.iterrows():
                                questao = int(row['Questao'])
                                anchor_items[questao] = {'a': float(row['a']), 'b': float(row['b']), 'c': float(row['c'])}
                            st.success(f"✅ {len(anchor_items)} itens âncora carregados")
                        except Exception as e:
                            st.error(f"❌ Erro ao carregar itens âncora: {e}")
                            st.info("💡 Dica: Use vírgula (,) ou ponto e vírgula (;) como separador")
                            anchor_items = None

                    if source == "Conjunto Salvo" and selected_param_set_id is not None:
                        # Carregar parâmetros salvos como params_df
                        try:
                            session = SessionLocal()
                            params_df = crud.get_parameter_set_items(session, selected_param_set_id)
                            st.session_state['parameters_set_id'] = selected_param_set_id
                            st.session_state['params_df'] = params_df
                            st.success(f"✅ Conjunto de parâmetros carregado (id={selected_param_set_id})")
                        finally:
                            session.close()

                    # Se não selecionou conjunto salvo, calibrar
                    if params_df is None:
                        calibrated_params = self.calibrator.calibrate_items_3pl(responses_df, anchor_items)
                        st.session_state['calibrated_params'] = calibrated_params
                        validation = self.calibrator.validate_calibration(calibrated_params)
                        if validation['valid']:
                            st.success("✅ Calibração concluída com sucesso!")
                            # Marcar âncoras
                            if anchor_items:
                                calibrated_params = calibrated_params.copy()
                                calibrated_params['is_anchor'] = calibrated_params['type'].eq('anchor') if 'type' in calibrated_params.columns else False
                            # Persistir
                            try:
                                session = SessionLocal()
                                required_cols = ['Questao','a','b','c']
                                calib_df = calibrated_params[required_cols + (['is_anchor'] if 'is_anchor' in calibrated_params.columns else [])] if all(col in calibrated_params.columns for col in required_cols) else calibrated_params
                                param_set = crud.create_parameters_set(session, name=f"calibrated:{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}", is_anchor=False, params_df=calib_df)
                                st.session_state['parameters_set_id'] = param_set.id
                                st.info(f"💾 Parâmetros calibrados persistidos (id={param_set.id})")
                            finally:
                                session.close()
                            # Mostrar resultados
                            self.show_calibration_results(calibrated_params, validation)
                            csv = calibrated_params.to_csv(index=False)
                            st.download_button(label="📥 Download Parâmetros Calibrados (CSV)", data=csv, file_name="parametros_calibrados.csv", mime="text/csv")
                        else:
                            st.error("❌ Problemas na calibração:")
                            for error in validation['errors']:
                                st.error(f"• {error}")
                            if validation['warnings']:
                                st.warning("⚠️ Avisos:")
                                for warning in validation['warnings']:
                                    st.warning(f"• {warning}")
                    
                except Exception as e:
                    st.error(f"❌ Erro na calibração: {e}")
        
        # Mostrar resultados se disponíveis
        if 'calibrated_params' in st.session_state:
            self.show_calibration_results(st.session_state['calibrated_params'])
    
    def tri_processing_tab(self):
        """Aba de processamento TRI"""
        st.header("📊 Processamento TRI")
        
        # Debug: verificar estado da sessão
        # st.write(f"uploaded_data presente: {'uploaded_data' in st.session_state}")
        # st.write(f"results_df presente: {'results_df' in st.session_state}")
        # st.write(f"params_df presente: {'params_df' in st.session_state}")
        # st.write(f"calibrated_params presente: {'calibrated_params' in st.session_state}")
        
        # Verificar se temos dados para processar
        has_uploaded_data = 'uploaded_data' in st.session_state
        has_results = 'results_df' in st.session_state
        has_params = 'params_df' in st.session_state or 'calibrated_params' in st.session_state
        
        if not has_uploaded_data and not has_results:
            st.warning("⚠️ Faça upload de dados primeiro na aba 'Upload de Dados' ou carregue resultados do histórico")
            return
        
        if not has_params and not has_results:
            st.warning("⚠️ Calibre itens ou carregue parâmetros primeiro na aba 'Calibração de Itens'")
            return
        
        # Mostrar informações sobre dados carregados
        if has_results:
            results_df = st.session_state['results_df']
            execution_info = ""
            if 'current_execution_id' in st.session_state:
                execution_info = f" (Execução #{st.session_state['current_execution_id']})"
            if 'current_execution_name' in st.session_state:
                execution_info = f" ({st.session_state['current_execution_name']})"
            
            st.success(f"✅ Visualizando resultados carregados: {len(results_df)} alunos{execution_info}")
            
            # Debug: mostrar informações dos dados
            # st.write(f"Colunas disponíveis: {list(results_df.columns)}")
            # st.write(f"Tamanho do DataFrame: {results_df.shape}")
            # st.write(f"Primeira linha: {results_df.iloc[0].to_dict()}")
            
            # Mostrar resultados
            self.show_tri_results(results_df)
            return
        
        responses_df = st.session_state['uploaded_data']
        
        # Selecionar parâmetros
        if 'params_df' in st.session_state:
            params_df = st.session_state['params_df']
            st.success("✅ Usando parâmetros carregados")
        elif 'calibrated_params' in st.session_state:
            params_df = st.session_state['calibrated_params']
            st.success("✅ Usando parâmetros calibrados")
        
        # Mostrar parâmetros
        st.subheader("📋 Parâmetros dos Itens")
        st.dataframe(params_df, use_container_width=True)
        
        # Processar TRI
        if st.button("🚀 Executar Processamento TRI", type="primary"):
            with st.spinner("Processando respostas com TRI..."):
                try:
                    # Processar respostas
                    results_df = self.tri_engine.process_responses(responses_df, params_df)
                    
                    # Salvar resultados
                    st.session_state['results_df'] = results_df
                    
                    # Persistir no banco
                    try:
                        session = SessionLocal()
                        
                        # Criar dataset
                        dataset = crud.create_dataset(
                            session, 
                            name=st.session_state.get('uploaded_filename', 'Dataset'),
                            source_type='csv',
                            file_name=st.session_state.get('uploaded_filename', 'unknown.csv')
                        )
                        
                        # Criar execução
                        execution = crud.create_execution(
                            session,
                            dataset_id=dataset.id,
                            parameters_set_id=st.session_state.get('parameters_set_id'),
                            status='completed'
                        )
                        
                        # Salvar resultados
                        crud.bulk_insert_results(session, execution.id, results_df)
                        
                        st.success(f"✅ Processamento concluído! {len(results_df)} alunos processados")
                        st.info(f"🔎 Resultados armazenados no banco para execução id={execution.id}")
                        
                    except Exception as e:
                        st.error(f"❌ Erro ao salvar no banco: {e}")
                    finally:
                        session.close()
                    
                    # Mostrar resultados
                    self.show_tri_results(results_df)
                    
                except Exception as e:
                    st.error(f"❌ Erro no processamento TRI: {e}")
        
        # Mostrar resultados se disponíveis (apenas se não foram processados agora)
        if 'results_df' in st.session_state and not has_results:
            self.show_tri_results(st.session_state['results_df'])
    
    def visualizations_tab(self):
        """Aba de análise e visualizações"""
        st.header("📈 Visualizações e Análises")
        
        # Debug: verificar estado da sessão
        # st.write(f"results_df presente: {'results_df' in st.session_state}")
        # st.write(f"current_execution_id presente: {'current_execution_id' in st.session_state}")
        # st.write(f"current_execution_name presente: {'current_execution_name' in st.session_state}")
        
        # Verificar se temos resultados para visualizar
        if 'results_df' not in st.session_state:
            st.warning("⚠️ Execute o processamento TRI primeiro ou carregue resultados do histórico")
            return
        
        results_df = st.session_state['results_df']
        
        # Mostrar informações sobre dados carregados
        execution_info = ""
        if 'current_execution_id' in st.session_state:
            execution_info = f" (Execução #{st.session_state['current_execution_id']})"
        if 'current_execution_name' in st.session_state:
            execution_info = f" ({st.session_state['current_execution_name']})"
        
        st.success(f"✅ Visualizando resultados: {len(results_df)} alunos{execution_info}")
        
        # Debug: mostrar informações dos dados
        # st.write(f"Colunas disponíveis: {list(results_df.columns)}")
        # st.write(f"Tamanho do DataFrame: {results_df.shape}")
        # st.write(f"Primeira linha: {results_df.iloc[0].to_dict()}")
        
        # Estatísticas básicas
        st.subheader("📊 Estatísticas Descritivas")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Alunos", len(results_df))
        
        with col2:
            theta_mean = results_df['theta'].mean()
            st.metric("Theta Médio", f"{theta_mean:.3f}")
        
        with col3:
            enem_mean = results_df['enem_score'].mean()
            st.metric("Nota ENEM Média", f"{enem_mean:.1f}")
        
        with col4:
            theta_std = results_df['theta'].std()
            st.metric("Desvio Padrão Theta", f"{theta_std:.3f}")
        
        # Gráficos
        st.subheader("📈 Gráficos")
        
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            # Distribuição de Theta
            fig_theta = px.histogram(
                results_df, 
                x='theta',
                title="Distribuição de Theta",
                nbins=20
            )
            st.plotly_chart(fig_theta, use_container_width=True)
        
        with col_chart2:
            # Distribuição de Notas ENEM
            fig_enem = px.histogram(
                results_df, 
                x='enem_score',
                title="Distribuição de Notas ENEM",
                nbins=20
            )
            st.plotly_chart(fig_enem, use_container_width=True)
        
        # Scatter plot Theta vs ENEM
        try:
            fig_scatter = px.scatter(
                results_df,
                x='theta',
                y='enem_score',
                title="Correlação: Theta vs Nota ENEM",
                trendline="ols"
            )
        except ImportError:
            # Fallback sem trendline se statsmodels não estiver disponível
            fig_scatter = px.scatter(
                results_df,
                x='theta',
                y='enem_score',
                title="Correlação: Theta vs Nota ENEM"
            )
            st.info("ℹ️ Linha de tendência não disponível (statsmodels não instalado)")
        
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        # Tabela de resultados
        st.subheader("📋 Tabela de Resultados")
        st.dataframe(results_df, use_container_width=True)
        
        # Download dos resultados
        csv_data = results_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Resultados (CSV)",
            data=csv_data,
            file_name=f"resultados_tri_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

    def show_calibration_results(self, calibrated_params, validation=None, show_validation=True):
        """Mostra resultados da calibração"""
        # Estatísticas básicas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Itens", len(calibrated_params))
        with col2:
            anchor_count = len(calibrated_params[calibrated_params['type'] == 'anchor']) if 'type' in calibrated_params.columns else 0
            st.metric("Itens Âncora", anchor_count)
        with col3:
            calibrated_count = len(calibrated_params[calibrated_params['type'] == 'calibrated']) if 'type' in calibrated_params.columns else len(calibrated_params)
            st.metric("Itens Calibrados", calibrated_count)
        with col4:
            st.metric("Parâmetro 'a' Médio", f"{calibrated_params['a'].mean():.3f}")
        
        # Gráficos dos parâmetros
        col1, col2 = st.columns(2)
        
        with col1:
            # Histograma do parâmetro 'a'
            fig_a = px.histogram(calibrated_params, x='a', nbins=20,
                               title="Distribuição do Parâmetro 'a' (Discriminação)")
            st.plotly_chart(fig_a, use_container_width=True, key=self.get_unique_key("hist_a_calibration"))
        
        with col2:
            # Histograma do parâmetro 'b'
            fig_b = px.histogram(calibrated_params, x='b', nbins=20,
                               title="Distribuição do Parâmetro 'b' (Dificuldade)")
            st.plotly_chart(fig_b, use_container_width=True, key=self.get_unique_key("hist_b_calibration"))
        
        # Scatter plot a vs b
        fig_scatter = px.scatter(calibrated_params, x='b', y='a', 
                               title="Parâmetro 'a' vs 'b'",
                               hover_data=['Questao'])
        st.plotly_chart(fig_scatter, use_container_width=True, key=self.get_unique_key("scatter_ab_calibration"))
        
        # Tabela de resultados
        st.subheader("📋 Parâmetros Calibrados")
        
        # Adicionar coluna de tipo se não existir
        display_df = calibrated_params.copy()
        if 'type' not in display_df.columns:
            display_df['type'] = 'calibrated'
        
        # Colorir itens âncora
        def color_anchor(val):
            if val == 'anchor':
                return 'background-color: lightblue'
            return ''
        
        st.dataframe(display_df.style.map(color_anchor, subset=['type']))
        
        # Validação se fornecida
        if validation and show_validation:
            if validation['warnings']:
                st.warning("⚠️ Avisos da Calibração:")
                for warning in validation['warnings']:
                    st.warning(f"• {warning}")
    
    def show_tri_results(self, results_df):
        """Mostra resultados do processamento"""
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total de Estudantes", len(results_df))
        with col2:
            theta_mean = results_df['theta'].mean()
            st.metric("Theta Médio", f"{theta_mean:.3f}")
        with col3:
            enem_mean = results_df['enem_score'].mean()
            st.metric("Nota ENEM Média", f"{enem_mean:.1f}")
        with col4:
            theta_std = results_df['theta'].std()
            st.metric("Desvio Padrão Theta", f"{theta_std:.3f}")
        
        col1, col2 = st.columns(2)
        with col1:
            fig_theta = px.histogram(results_df, x='theta', nbins=30, 
                                    title="Distribuição de Theta")
            st.plotly_chart(fig_theta, use_container_width=True, key=self.get_unique_key("hist_theta_processing"))
        with col2:
            fig_enem = px.histogram(results_df, x='enem_score', nbins=30,
                                   title="Distribuição de Notas ENEM")
            st.plotly_chart(fig_enem, use_container_width=True, key=self.get_unique_key("hist_enem_processing"))
        
        # Estatísticas detalhadas
        st.subheader("📊 Estatísticas Detalhadas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Estatísticas de Theta")
            theta_stats = results_df['theta'].describe()
            st.dataframe(theta_stats)
        
        with col2:
            st.subheader("📈 Estatísticas de Nota ENEM")
            enem_stats = results_df['enem_score'].describe()
            st.dataframe(enem_stats)
        
        # Gráficos adicionais
        st.subheader("📈 Gráficos Adicionais")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Boxplot de theta
            fig_box_theta = px.box(results_df, y='theta', title="Boxplot de Theta")
            st.plotly_chart(fig_box_theta, use_container_width=True, key=self.get_unique_key("box_theta_dist"))
        
        with col2:
            # Boxplot de ENEM
            fig_box_enem = px.box(results_df, y='enem_score', title="Boxplot de Notas ENEM")
            st.plotly_chart(fig_box_enem, use_container_width=True, key=self.get_unique_key("box_enem_dist"))
        
        # Gráfico de distribuição cumulativa
        st.subheader("📈 Distribuição Cumulativa")
        
        fig_cumulative = go.Figure()
        
        # Theta
        sorted_theta = np.sort(results_df['theta'])
        y_theta = np.arange(1, len(sorted_theta) + 1) / len(sorted_theta)
        fig_cumulative.add_trace(go.Scatter(x=sorted_theta, y=y_theta, 
                                           name='Theta', mode='lines'))
        
        # ENEM
        sorted_enem = np.sort(results_df['enem_score'])
        y_enem = np.arange(1, len(sorted_enem) + 1) / len(sorted_enem)
        fig_cumulative.add_trace(go.Scatter(x=sorted_enem, y=y_enem, 
                                           name='ENEM', mode='lines'))
        
        fig_cumulative.update_layout(
            title="Distribuição Cumulativa",
            xaxis_title="Valor",
            yaxis_title="Probabilidade Cumulativa"
        )
        
        st.plotly_chart(fig_cumulative, use_container_width=True, key=self.get_unique_key("cumulative_dist"))
        
        # Análises de correlação
        if 'uploaded_data' in st.session_state:
            responses_df = st.session_state['uploaded_data']
            
            if responses_df is not None and 'acertos' in results_df.columns:
                # Correlação theta vs acertos
                correlation = results_df['acertos'].corr(results_df['theta'])
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("🎯 Correlação Theta vs Acertos")
                    st.metric("Correlação", f"{correlation:.3f}")
                    
                    # Scatter plot
                    fig_scatter = px.scatter(results_df, x='acertos', y='theta',
                                            title=f"Theta vs Acertos (r = {correlation:.3f})")
                    st.plotly_chart(fig_scatter, use_container_width=True, key=self.get_unique_key("scatter_theta_acertos"))
                
                with col2:
                    # Correlação theta vs ENEM
                    corr_theta_enem = results_df['theta'].corr(results_df['enem_score'])
                    st.metric("Correlação Theta-ENEM", f"{corr_theta_enem:.3f}")
                    
                    # Scatter plot
                    fig_scatter2 = px.scatter(results_df, x='theta', y='enem_score',
                                             title=f"Theta vs ENEM (r = {corr_theta_enem:.3f})")
                    st.plotly_chart(fig_scatter2, use_container_width=True, key=self.get_unique_key("scatter_theta_enem"))
        
        # Percentis
        st.subheader("📊 Percentis")
        
        percentiles = [5, 10, 25, 50, 75, 90, 95]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Percentis de Theta")
            theta_percentiles = [np.percentile(results_df['theta'], p) for p in percentiles]
            percentiles_df = pd.DataFrame({
                'Percentil': [f'P{p}' for p in percentiles],
                'Valor': theta_percentiles
            })
            st.dataframe(percentiles_df, use_container_width=True)
        
        with col2:
            st.subheader("Percentis de Nota ENEM")
            enem_percentiles = [np.percentile(results_df['enem_score'], p) for p in percentiles]
            percentiles_df = pd.DataFrame({
                'Percentil': [f'P{p}' for p in percentiles],
                'Valor': enem_percentiles
            })
            st.dataframe(percentiles_df, use_container_width=True)
        
        # Gráfico completo
        st.subheader("📊 Dashboard Completo")
        
        fig_complete = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Distribuição de Theta', 'Distribuição de ENEM', 'Theta vs Acertos', 'Theta vs ENEM'),
            specs=[[{"type": "histogram"}, {"type": "histogram"}],
                   [{"type": "scatter"}, {"type": "scatter"}]]
        )
        
        # Distribuição de theta
        fig_complete.add_trace(go.Histogram(x=results_df['theta'], nbinsx=30), row=1, col=1)
        
        # Distribuição de ENEM
        fig_complete.add_trace(go.Histogram(x=results_df['enem_score'], nbinsx=30), row=1, col=2)
        
        # Theta vs acertos
        if 'acertos' in results_df.columns:
            fig_complete.add_trace(go.Scatter(x=results_df['acertos'], y=results_df['theta'],
                                             mode='markers'), row=2, col=1)
        
        # Theta vs ENEM
        fig_complete.add_trace(go.Scatter(x=results_df['theta'], y=results_df['enem_score'],
                                         mode='markers'), row=2, col=2)
        
        fig_complete.update_layout(height=800, title_text="Dashboard Completo de Resultados")
        st.plotly_chart(fig_complete, use_container_width=True, key=self.get_unique_key("complete_dashboard"))
        
        # Estatísticas resumidas
        st.subheader("📊 Resumo Estatístico")
        
        stats = {
            'theta_mean': results_df['theta'].mean(),
            'theta_std': results_df['theta'].std(),
            'theta_min': results_df['theta'].min(),
            'theta_max': results_df['theta'].max(),
            'enem_mean': results_df['enem_score'].mean(),
            'enem_std': results_df['enem_score'].std(),
            'enem_min': results_df['enem_score'].min(),
            'enem_max': results_df['enem_score'].max()
        }
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Estatísticas de Theta")
            st.metric("Média", f"{stats.get('theta_mean', 0):.3f}")
            st.metric("Mediana", f"{np.median(results_df['theta']):.3f}")
            st.metric("Desvio Padrão", f"{stats.get('theta_std', 0):.3f}")
            st.metric("Mínimo", f"{stats.get('theta_min', 0):.3f}")
            st.metric("Máximo", f"{stats.get('theta_max', 0):.3f}")
        
        with col2:
            st.subheader("📈 Estatísticas de Nota ENEM")
            st.metric("Média", f"{stats.get('enem_mean', 0):.1f}")
            st.metric("Mediana", f"{np.median(results_df['enem_score']):.1f}")
            st.metric("Desvio Padrão", f"{stats.get('enem_std', 0):.1f}")
            st.metric("Mínimo", f"{stats.get('enem_min', 0):.0f}")
            st.metric("Máximo", f"{stats.get('enem_max', 0):.0f}")
        
        # Percentis detalhados
        st.subheader("📊 Percentis Detalhados")
        
        percentiles = [1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 99]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Percentis de Theta")
            theta_percentiles = [np.percentile(results_df['theta'], p) for p in percentiles]
            percentiles_df = pd.DataFrame({
                'Percentil': [f'P{p}' for p in percentiles],
                'Valor': theta_percentiles
            })
            st.dataframe(percentiles_df, use_container_width=True)
        
        with col2:
            st.subheader("Percentis de Nota ENEM")
            enem_percentiles = [np.percentile(results_df['enem_score'], p) for p in percentiles]
            percentiles_df = pd.DataFrame({
                'Percentil': [f'P{p}' for p in percentiles],
                'Valor': enem_percentiles
            })
            st.dataframe(percentiles_df, use_container_width=True)

    def equating_tab(self):
        """Aba de equating de escalas"""
        st.header("🔄 Equating de Escalas")
        
        if 'results_df' not in st.session_state:
            st.warning("⚠️ Processe dados TRI primeiro para realizar equating.")
            return
        
        results_df = st.session_state['results_df']
        
        # Seleção de método de equating
        equating_method = st.selectbox(
            "Método de Equating:",
            ["Equating de Escalas", "Equating de Escalas de Razão", "Equating de Escalas de Razão de Razão"]
        )
        
        if st.button("🚀 Executar Equating"):
            with st.spinner("Executando equating..."):
                try:
                    # Processar equating
                    equated_results_df = self.tri_engine.equate_scales(results_df, equating_method)
                    
                    # Salvar resultados
                    st.session_state['equated_results_df'] = equated_results_df
                    
                    # Persistir no banco
                    try:
                        session = SessionLocal()
                        dataset_id = st.session_state.get('dataset_id') # Assuming dataset_id is set elsewhere or needs to be passed
                        execution = crud.create_execution(
                            session,
                            dataset_id=dataset_id,
                            parameters_set_id=st.session_state.get('parameters_set_id'),
                            status='completed'
                        )
                        crud.bulk_insert_results(session, execution.id, equated_results_df)
                        st.session_state['equated_execution_id'] = execution.id
                        st.info(f"💾 Equating salvo no banco (id={execution.id})")
                    except Exception as e:
                        st.error(f"❌ Erro ao salvar equating no banco: {e}")
                    finally:
                        session.close()
                    
                    # Mostrar resultados
                    self.show_equating_results(equated_results_df)
                    
                except Exception as e:
                    st.error(f"❌ Erro no equating: {e}")
        
        # Mostrar resultados se disponíveis
        if 'equated_results_df' in st.session_state:
            self.show_equating_results(st.session_state['equated_results_df'])
    
    def show_equating_results(self, equated_results_df):
        """Mostra resultados do equating"""
        st.subheader("📊 Resultados do Equating")
        
        # Estatísticas gerais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Estudantes", len(equated_results_df))
        with col2:
            theta_mean = equated_results_df['theta'].mean()
            st.metric("Theta Médio", f"{theta_mean:.3f}")
        with col3:
            enem_mean = equated_results_df['enem_score'].mean()
            st.metric("Nota ENEM Média", f"{enem_mean:.1f}")
        with col4:
            theta_std = equated_results_df['theta'].std()
            st.metric("Desvio Padrão Theta", f"{theta_std:.3f}")
        
        # Gráficos
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribuição de Theta
            fig_theta = px.histogram(
                equated_results_df, 
                x='Theta',
                title="Distribuição de Theta (Equated)",
                nbins=20
            )
            st.plotly_chart(fig_theta, use_container_width=True)
        
        with col2:
            # Distribuição de Notas ENEM
            fig_enem = px.histogram(
                equated_results_df, 
                x='enem_score',
                title="Distribuição de Notas ENEM (Equated)",
                nbins=20
            )
            st.plotly_chart(fig_enem, use_container_width=True)
        
        # Scatter plot Theta vs ENEM
        try:
            fig_scatter = px.scatter(
                equated_results_df,
                x='theta',
                y='enem_score',
                title="Correlação: Theta vs Nota ENEM (Equated)",
                trendline="ols"
            )
        except ImportError:
            # Fallback sem trendline se statsmodels não estiver disponível
            fig_scatter = px.scatter(
                equated_results_df,
                x='theta',
                y='enem_score',
                title="Correlação: Theta vs Nota ENEM (Equated)"
            )
            st.info("ℹ️ Linha de tendência não disponível (statsmodels não instalado)")
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        # Tabela de resultados
        st.subheader("📋 Tabela de Resultados Equatados")
        st.dataframe(equated_results_df, use_container_width=True)
        
        # Download dos resultados
        csv_data = equated_results_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Resultados Equatados (CSV)",
            data=csv_data,
            file_name=f"resultados_equatados_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

    def history_tab(self):
        """Aba de histórico de resultados (via banco)"""
        st.header("💾 Histórico de Resultados (Banco)")
        try:
            session = SessionLocal()
            executions = crud.list_executions(session)
        finally:
            session.close()
        
        if not executions:
            st.info("📝 Nenhuma execução salva no banco ainda.")
            return
        
        for exec_info in executions:
            # Usar o nome personalizado se disponível, senão usar o padrão
            display_name = exec_info['name'] or f"Execução {exec_info['id']}"
            
            # Verificar se esta execução está carregada
            is_currently_loaded = (
                'current_execution_id' in st.session_state and 
                st.session_state['current_execution_id'] == exec_info['id']
            )
            
            expander_title = f"📊 {display_name} - {str(exec_info['created_at'])[:19]}"
            if is_currently_loaded:
                expander_title += " 🟢 CARREGADA"
            
            with st.expander(expander_title):
                # Interface para renomear execução
                st.subheader("✏️ Renomear Execução")
                col_name1, col_name2 = st.columns([3, 1])
                
                with col_name1:
                    new_name = st.text_input(
                        f"Nome da Execução #{exec_info['id']}:",
                        value=exec_info['name'] or f"Execução {exec_info['id']}",
                        key=f"rename_input_{exec_info['id']}"
                    )
                
                with col_name2:
                    if st.button(f"💾 Salvar Nome", key=f"save_name_btn_{exec_info['id']}"):
                        try:
                            session = SessionLocal()
                            if crud.update_execution_name(session, exec_info['id'], new_name):
                                st.success(f"✅ Nome atualizado para: {new_name}")
                                st.rerun()
                            else:
                                st.error("❌ Erro ao atualizar nome")
                        except Exception as e:
                            st.error(f"❌ Erro: {e}")
                        finally:
                            session.close()
                
                # Métricas da execução
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Estudantes", exec_info['total_students'])
                with col2:
                    st.metric("Theta Médio", f"{exec_info['theta_mean']:.3f}")
                with col3:
                    st.metric("ENEM Médio", f"{exec_info['enem_mean']:.1f}")
                with col4:
                    st.metric("Status", exec_info['status'])
                
                # Botões de ação
                st.subheader("🔧 Ações")
                c1, c2, c3, c4 = st.columns([1,1,1,1])
                
                with c4:
                    if is_currently_loaded:
                        if st.button(f"🗑️ Descarregar", key=f"unload_btn_{exec_info['id']}"):
                            # Limpar dados carregados
                            if 'results_df' in st.session_state:
                                del st.session_state['results_df']
                            if 'current_execution_id' in st.session_state:
                                del st.session_state['current_execution_id']
                            if 'current_execution_name' in st.session_state:
                                del st.session_state['current_execution_name']
                            st.success("✅ Resultados descarregados")
                            st.rerun()
                with c1:
                    if st.button(f"🔄 Carregar resultados", key=f"load_btn_{exec_info['id']}"):
                        try:
                            session = SessionLocal()
                            df = crud.get_execution_results(session, exec_info['id'])
                            if df.empty:
                                st.warning("Sem resultados para esta execução.")
                            else:
                                # Debug: mostrar informações dos dados
                                # st.write(f"Colunas disponíveis: {list(df.columns)}")
                                # st.write(f"Primeira linha: {df.iloc[0].to_dict()}")
                                
                                # Carregar resultados em todas as abas relevantes
                                st.session_state['results_df'] = df.copy()  # Usar cópia para evitar referências
                                st.session_state['current_execution_id'] = exec_info['id']
                                st.session_state['current_execution_name'] = exec_info['name']
                                
                                # Verificar se foi salvo corretamente
                                st.write("🔍 **Verificação de salvamento:**")
                                st.write(f"results_df salvo: {'results_df' in st.session_state}")
                                st.write(f"current_execution_id salvo: {'current_execution_id' in st.session_state}")
                                st.write(f"current_execution_name salvo: {'current_execution_name' in st.session_state}")
                                
                                # Converter nomes das colunas para compatibilidade
                                if 'Theta' in df.columns and 'theta' not in df.columns:
                                    df['theta'] = df['Theta']
                                if 'Nota_ENEM' in df.columns and 'enem_score' not in df.columns:
                                    df['enem_score'] = df['Nota_ENEM']
                                
                                st.success(f"✅ Resultados carregados para todas as abas!")
                                st.info(f"📊 {len(df)} resultados da execução '{exec_info['name']}' carregados")
                                st.info("💡 Vá para as abas 'Processamento TRI' ou 'Visualizações' para ver os dados")
                                
                                # Debug: verificar estado da sessão
                                # st.write(f"results_df presente: {'results_df' in st.session_state}")
                                # st.write(f"current_execution_id: {st.session_state.get('current_execution_id', 'N/A')}")
                                # st.write(f"current_execution_name: {st.session_state.get('current_execution_name', 'N/A')}")
                                
                                # Botão para forçar atualização
                                if st.button("🔄 Atualizar Página", key=f"refresh_btn_{exec_info['id']}"):
                                    st.rerun()
                        finally:
                            session.close()
                with c2:
                    if st.button(f"📥 Download CSV", key=f"download_btn_{exec_info['id']}"):
                        try:
                            session = SessionLocal()
                            df = crud.get_execution_results(session, exec_info['id'])
                        finally:
                            session.close()
                        if df.empty:
                            st.warning("Sem resultados para exportar.")
                        else:
                            st.download_button(
                                label="Baixar CSV",
                                data=df.to_csv(index=False),
                                file_name=f"exec_{exec_info['id']}.csv",
                                mime="text/csv",
                                key=f"dbtn_exec_{exec_info['id']}"
                            )
                with c3:
                    if st.button(f"🗑️ Deletar", key=f"delete_btn_{exec_info['id']}"):
                        try:
                            session = SessionLocal()
                            ok = crud.delete_execution(session, exec_info['id'])
                        finally:
                            session.close()
                        if ok:
                            st.success("✅ Execução deletada.")
                            st.rerun()
                        else:
                            st.error("❌ Não foi possível deletar.")

    def parameters_tab(self):
        """Aba de parâmetros salvos (itens calibrados)"""
        st.header("📋 Parâmetros Salvos (Itens Calibrados)")
        
        try:
            session = SessionLocal()
            parameters_sets = crud.list_parameters_sets(session)
        finally:
            session.close()
        
        if not parameters_sets:
            st.info("📝 Nenhum conjunto de parâmetros salvo ainda.")
            return
        
        for params_info in parameters_sets:
            # Usar o nome personalizado se disponível, senão usar o padrão
            display_name = params_info['name'] or f"Conjunto {params_info['id']}"
            
            with st.expander(f"🔧 {display_name} - {str(params_info['created_at'])[:19]}"):
                # Interface para renomear conjunto
                st.subheader("✏️ Renomear Conjunto")
                col_name1, col_name2 = st.columns([3, 1])
                
                with col_name1:
                    new_name = st.text_input(
                        f"Nome do Conjunto #{params_info['id']}:",
                        value=params_info['name'] or f"Conjunto {params_info['id']}",
                        key=f"rename_params_input_{params_info['id']}"
                    )
                
                with col_name2:
                    if st.button(f"💾 Salvar Nome", key=f"save_params_name_btn_{params_info['id']}"):
                        try:
                            session = SessionLocal()
                            if crud.update_parameters_set_name(session, params_info['id'], new_name):
                                st.success(f"✅ Nome atualizado para: {new_name}")
                                st.rerun()
                            else:
                                st.error("❌ Erro ao atualizar nome")
                        except Exception as e:
                            st.error(f"❌ Erro: {e}")
                        finally:
                            session.close()
                
                # Métricas do conjunto
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total de Itens", params_info['total_items'])
                with col2:
                    st.metric("Data Criação", str(params_info['created_at'])[:10])
                with col3:
                    st.metric("ID", params_info['id'])
                
                # Botões de ação
                st.subheader("🔧 Ações")
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button(f"📊 Ver Parâmetros", key=f"view_params_btn_{params_info['id']}"):
                        try:
                            session = SessionLocal()
                            params_df = crud.get_parameters_set(session, params_info['id'])
                            session.close()
                            
                            st.subheader(f"📊 Parâmetros do Conjunto: {display_name}")
                            
                            # Estatísticas dos parâmetros
                            col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
                            with col_stats1:
                                st.metric("Parâmetro 'a' Médio", f"{params_df['a'].mean():.3f}")
                            with col_stats2:
                                st.metric("Parâmetro 'b' Médio", f"{params_df['b'].mean():.3f}")
                            with col_stats3:
                                st.metric("Parâmetro 'c' Médio", f"{params_df['c'].mean():.3f}")
                            with col_stats4:
                                anchor_count = params_df['is_anchor'].sum()
                                st.metric("Itens Âncora", anchor_count)
                            
                            # Tabela de parâmetros
                            st.dataframe(params_df, use_container_width=True)
                            
                            # Download CSV
                            csv_data = params_df.to_csv(index=False)
                            st.download_button(
                                label="📥 Download Parâmetros (CSV)",
                                data=csv_data,
                                file_name=f"parametros_conjunto_{params_info['id']}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                            
                        except Exception as e:
                            st.error(f"❌ Erro ao carregar parâmetros: {e}")
                
                with col2:
                    if st.button(f"📥 Download CSV", key=f"download_params_btn_{params_info['id']}"):
                        try:
                            session = SessionLocal()
                            params_df = crud.get_parameters_set(session, params_info['id'])
                            session.close()
                            
                            csv_data = params_df.to_csv(index=False)
                            file_name = f"parametros_conjunto_{params_info['id']}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
                            
                            st.download_button(
                                label="📥 Download Parâmetros (CSV)",
                                data=csv_data,
                                file_name=file_name,
                                mime="text/csv"
                            )
                            
                        except Exception as e:
                            st.error(f"❌ Erro ao gerar CSV: {e}")


def main():
    """Função principal do dashboard"""
    dashboard = TRIDashboard()
    dashboard.run()


if __name__ == "__main__":
    main()
