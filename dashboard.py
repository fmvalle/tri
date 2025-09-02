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
        if st.sidebar.button("🚪 Logout"):
            st.session_state['authenticated'] = False
            st.rerun()
        
        # Sidebar
        self.sidebar()
        
        # Main content
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "🏠 Início", 
            "📁 Upload de Dados", 
            "📋 Parâmetros",
            "⚙️ Processamento TRI", 
            "📈 Análise e Visualizações",
            "📋 Relatórios",
            "💾 Histórico"
        ])
        
        with tab1:
            self.home_tab()
        with tab2:
            self.upload_tab()
        with tab3:
            self.parameters_tab()
        with tab4:
            self.processing_tab()
        with tab5:
            self.analysis_tab()
        with tab6:
            self.reports_tab()
        with tab7:
            self.history_tab()
    
    def sidebar(self):
        """Configura a barra lateral"""
        st.sidebar.title("⚙️ Configurações")
        
        # Upload de arquivo de parâmetros
        st.sidebar.subheader("📋 Parâmetros dos Itens")
        
        param_source = st.sidebar.radio(
            "Fonte dos parâmetros:",
            ["Calibração Automática", "Arquivo Customizado"],
            help="Escolha entre calibrar automaticamente ou usar arquivo existente"
        )
        
        if param_source == "Arquivo Customizado":
            params_file = st.sidebar.file_uploader(
                "Carregar arquivo de parâmetros",
                type=['csv', 'xlsx'],
                help="Arquivo com parâmetros a, b, c dos itens"
            )
        else:
            params_file = None
            st.sidebar.info("ℹ️ Use a aba 'Calibração de Itens' para calibrar parâmetros")
        
        if params_file:
            try:
                if params_file.name.endswith('.csv'):
                    try:
                        params_df = pd.read_csv(params_file)
                    except:
                        # Tentar com ponto e vírgula
                        params_file.seek(0)
                        params_df = pd.read_csv(params_file, sep=';')
                else:
                    params_df = pd.read_excel(params_file)
                st.session_state['params_df'] = params_df
                st.sidebar.success(f"✅ Parâmetros carregados: {len(params_df)} itens")

                # Persistir parâmetros carregados automaticamente
                try:
                    session = SessionLocal()
                    # Garantir colunas esperadas
                    required_cols = ['Questao','a','b','c']
                    if all(col in params_df.columns for col in required_cols):
                        param_set = crud.create_parameters_set(
                            session,
                            name=f"uploaded:{params_file.name}",
                            is_anchor=False,
                            params_df=params_df[required_cols]
                        )
                        st.session_state['parameters_set_id'] = param_set.id
                        st.sidebar.info(f"💾 Parâmetros persistidos (id={param_set.id})")
                    else:
                        st.sidebar.warning("⚠️ Arquivo de parâmetros sem colunas obrigatórias: Questao,a,b,c")
                except Exception as e:
                    st.sidebar.warning(f"⚠️ Não foi possível persistir parâmetros: {e}")
                finally:
                    try:
                        session.close()
                    except Exception:
                        pass
            except Exception as e:
                st.sidebar.error(f"❌ Erro ao carregar parâmetros: {e}")
                st.sidebar.info("💡 Dica: Use vírgula (,) ou ponto e vírgula (;) como separador")
        
        # Configurações TRI
        st.sidebar.subheader("🔧 Configurações TRI")
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            default_a = st.number_input("a (discriminação)", value=1.0, step=0.1)
            default_b = st.number_input("b (dificuldade)", value=0.0, step=0.1)
        # with col2:
            default_c = st.number_input("c (acerto casual)", value=0.2, min_value=0.0, max_value=1.0, step=0.01)
            enem_base = st.number_input("Nota base ENEM", value=500, step=10)
        
        st.session_state['tri_config'] = {
            'default_a': default_a,
            'default_b': default_b,
            'default_c': default_c,
            'enem_base': enem_base
        }
        
        # Informações do sistema
        st.sidebar.subheader("ℹ️ Informações")
        st.sidebar.info(f"""
        **Sistema TRI v2.0**
        
        • Modelo: 3PL
        • Editoras: {len(self.config['publishers'])}
        • Séries: {len(self.config['grades'])}
        • Disciplinas: {len(self.config['subjects'])}
        """)
    
    def home_tab(self):
        """Aba inicial"""
        st.header("🏠 Bem-vindo ao Sistema TRI")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            ### 📚 Sobre o Sistema
            
            O **Sistema TRI** é uma ferramenta para análise de provas utilizando a 
            **Teoria de Resposta ao Item (TRI)** no modelo de 3 parâmetros (3PL), seguindo 
            os padrões utilizados no ENEM e SAEB.
            
            #### 🎯 Funcionalidades Principais:
            
            ✅ **Processamento de Dados**
            - Suporte a arquivos CSV e Excel
            - ETL automático para cartões de resposta
            - Validação robusta de dados
            
            ✅ **Análise TRI**
            - Estimação de proficiência (theta)
            - Conversão para escala ENEM
            - Parâmetros customizáveis
            
            ✅ **Visualizações**
            - Gráficos interativos
            - Relatórios completos
            - Dashboards em tempo real
            
            ✅ **Relatórios**
            - Estatísticas detalhadas
            - Exportação em múltiplos formatos
            - Análise de qualidade
            """)
        
        with col2:            
            st.markdown("### 🚀 Próximos Passos")
            st.markdown("""
            1. **Upload de Dados**: Carregue seus arquivos de respostas
            2. **Configuração**: Ajuste os parâmetros TRI se necessário
            3. **Processamento**: Execute a análise TRI
            4. **Visualização**: Explore os resultados
            5. **Relatórios**: Gere relatórios completos
            """)
    
    def upload_tab(self):
        """Aba de upload de dados"""
        st.header("📁 Upload de Dados")
        
        # Seleção do tipo de arquivo
        file_type = st.radio(
            "Tipo de arquivo:",
            ["Excel (Cartão de Resposta)", "CSV"],
            horizontal=True
        )
        
        if file_type == "CSV":
            self.upload_csv()
        else:
            self.upload_excel()
    
    def upload_csv(self):
        """Upload de arquivo CSV"""
        st.subheader("📄 Upload de Arquivo CSV")
        
        uploaded_file = st.file_uploader(
            "Selecione o arquivo CSV de respostas",
            type=['csv'],
            help="Arquivo deve conter colunas: CodPessoa, Questao, RespostaAluno, Gabarito"
        )
        
        if uploaded_file is not None:
            try:
                # Carregar dados
                df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8')
                st.session_state['responses_df'] = df
                # Persistir dataset
                try:
                    session = SessionLocal()
                    dataset = crud.create_dataset(
                        session,
                        name=uploaded_file.name,
                        source_type="csv",
                        file_name=uploaded_file.name,
                    )
                    st.session_state['dataset_id'] = dataset.id
                finally:
                    session.close()
                
                # Mostrar preview
                st.success(f"✅ Arquivo carregado com sucesso: {len(df)} registros")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📊 Preview dos Dados")
                    st.dataframe(df.head(10))
                
                with col2:
                    st.subheader("📈 Estatísticas Básicas")
                    
                    # Métricas
                    total_students = df['CodPessoa'].nunique()
                    total_items = df['Questao'].nunique()
                    total_responses = len(df)
                    
                    st.metric("Total de Estudantes", total_students)
                    st.metric("Total de Itens", total_items)
                    st.metric("Total de Respostas", total_responses)
                    
                    # Verificar completude
                    expected_responses = total_students * total_items
                    completeness = total_responses / expected_responses
                    st.metric("Completude", f"{completeness:.1%}")
                
                # Validar dados
                st.subheader("🔍 Validação dos Dados")
                # Observação: validação por caminho é opcional no upload via Streamlit
                validation = {"valid": True, "errors": [], "warnings": []}
                
                if validation['valid']:
                    st.success("✅ Dados válidos para processamento")
                else:
                    st.error("❌ Problemas encontrados nos dados")
                    for error in validation['errors']:
                        st.error(f"• {error}")
                
            except Exception as e:
                st.error(f"❌ Erro ao carregar arquivo: {e}")
    
    def upload_excel(self):
        """Upload de arquivo Excel"""
        st.subheader("📊 Upload de Arquivo Excel")
        
        uploaded_file = st.file_uploader(
            "Selecione o arquivo Excel de cartão de resposta",
            type=['xlsx', 'xls'],
            help="Arquivo deve conter abas 'Datos' e 'Matriz'"
        )
        
        if uploaded_file is not None:
            try:
                # Carregar dados
                df = self.data_processor.load_responses_excel_from_streamlit(uploaded_file)
                st.session_state['responses_df'] = df
                # Persistir dataset
                try:
                    session = SessionLocal()
                    dataset = crud.create_dataset(
                        session,
                        name=uploaded_file.name,
                        source_type="excel",
                        file_name=uploaded_file.name,
                    )
                    st.session_state['dataset_id'] = dataset.id
                finally:
                    session.close()
                
                # Mostrar preview
                st.success(f"✅ Arquivo processado com sucesso: {len(df)} registros")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📊 Preview dos Dados")
                    st.dataframe(df.head(10))
                
                with col2:
                    st.subheader("📈 Estatísticas Básicas")
                    
                    # Métricas
                    total_students = df['CodPessoa'].nunique()
                    total_items = df['Questao'].nunique()
                    total_responses = len(df)
                    
                    st.metric("Total de Estudantes", total_students)
                    st.metric("Total de Itens", total_items)
                    st.metric("Total de Respostas", total_responses)
                    
                    # Verificar completude
                    expected_responses = total_students * total_items
                    completeness = total_responses / expected_responses
                    st.metric("Completude", f"{completeness:.1%}")
                
                # Qualidade dos dados
                st.subheader("🔍 Qualidade dos Dados")
                quality_metrics = self.data_processor.validate_data_quality(df)
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Média de Acertos", f"{quality_metrics.get('mean_accuracy', 0):.2f}")
                with col2:
                    st.metric("Desvio Padrão", f"{quality_metrics.get('std_accuracy', 0):.2f}")
                with col3:
                    st.metric("Estudantes Incompletos", quality_metrics.get('incomplete_students', 0))
                with col4:
                    st.metric("Completude", f"{quality_metrics.get('completeness', 0):.1%}")
                
            except Exception as e:
                st.error(f"❌ Erro ao processar arquivo: {e}")
    
    def parameters_tab(self):
        """Aba de parâmetros: subir âncoras ou selecionar conjuntos salvos"""
        st.header("📋 Parâmetros dos Itens")
        
        if 'responses_df' not in st.session_state:
            st.warning("⚠️ Carregue dados primeiro na aba 'Upload de Dados'")
            return
        
        responses_df = st.session_state['responses_df']
        
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
            st.subheader("📊 Resultados da Calibração")
            self.show_calibration_results(st.session_state['calibrated_params'], show_validation=False)
            # Botão para persistir parâmetros calibrados
            with st.expander("💾 Persistir parâmetros calibrados no banco"):
                param_set_name = st.text_input("Nome do conjunto de parâmetros", value="calibrados")
                if st.button("Salvar parâmetros no banco"):
                    try:
                        session = SessionLocal()
                        param_set = crud.create_parameters_set(
                            session,
                            name=param_set_name,
                            is_anchor=False,
                            params_df=st.session_state['calibrated_params']
                        )
                        st.success(f"✅ Parâmetros salvos (id={param_set.id})")
                        st.session_state['parameters_set_id'] = param_set.id
                    except Exception as e:
                        st.error(f"❌ Erro ao salvar parâmetros: {e}")
                    finally:
                        session.close()
    
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
    
    def processing_tab(self):
        """Aba de processamento TRI"""
        st.header("⚙️ Processamento TRI")
        
        if 'responses_df' not in st.session_state:
            st.warning("⚠️ Carregue dados primeiro na aba 'Upload de Dados'")
            return
        
        responses_df = st.session_state['responses_df']
        
        # Configurações de processamento
        st.subheader("🔧 Configurações")
        
        col1, col2 = st.columns(2)
        
        with col1:
            use_custom_params = st.checkbox("Usar parâmetros customizados")
            if use_custom_params and ('params_df' in st.session_state or 'calibrated_params' in st.session_state):
                if 'calibrated_params' in st.session_state:
                    st.success("✅ Parâmetros calibrados disponíveis")
                else:
                    st.success("✅ Parâmetros customizados disponíveis")
            elif use_custom_params:
                st.warning("⚠️ Calibre parâmetros ou carregue arquivo customizado")
                use_custom_params = False
        
        with col2:
            show_progress = st.checkbox("Mostrar progresso detalhado", value=True)
        
        # Botão de processamento
        if st.button("🚀 Processar TRI", type="primary"):
            with st.spinner("Processando TRI..."):
                try:
                    # Configurar parâmetros
                    params_df = None
                    if use_custom_params:
                        if 'calibrated_params' in st.session_state:
                            params_df = st.session_state['calibrated_params']
                        elif 'params_df' in st.session_state:
                            params_df = st.session_state['params_df']
                    
                    # Processar TRI
                    results_df = self.tri_engine.process_responses(responses_df, params_df)
                    st.session_state['results_df'] = results_df
                    
                    # Persistir execução e resultados
                    try:
                        session = SessionLocal()
                        dataset_id = st.session_state.get('dataset_id')
                        parameters_set_id = None
                        if use_custom_params:
                            parameters_set_id = st.session_state.get('parameters_set_id')
                            # Se ainda não persistiu params, criar conjunto agora
                            if parameters_set_id is None and params_df is not None:
                                try:
                                    session_params = SessionLocal()
                                    required_cols = ['Questao','a','b','c']
                                    pdf = params_df[required_cols] if all(col in params_df.columns for col in required_cols) else params_df
                                    pset = crud.create_parameters_set(
                                        session_params,
                                        name=f"processing:{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}",
                                        is_anchor=False,
                                        params_df=pdf
                                    )
                                    parameters_set_id = pset.id
                                    st.session_state['parameters_set_id'] = pset.id
                                except Exception as e:
                                    st.warning(f"⚠️ Não foi possível persistir parâmetros antes da execução: {e}")
                                finally:
                                    try:
                                        session_params.close()
                                    except Exception:
                                        pass
                        execution = crud.create_execution(
                            session,
                            dataset_id=dataset_id,
                            parameters_set_id=parameters_set_id,
                            status="completed"
                        )
                        crud.bulk_insert_results(session, execution.id, results_df)
                        st.session_state['execution_id'] = execution.id
                        st.info(f"💾 Execução salva no banco (id={execution.id})")
                    except Exception as e:
                        st.warning(f"⚠️ Não foi possível persistir resultados: {e}")
                    finally:
                        try:
                            session.close()
                        except Exception:
                            pass
                    
                    st.success("✅ Processamento TRI concluído!")
                    
                except Exception as e:
                    st.error(f"❌ Erro no processamento: {e}")
        
        # Mostrar resultados se disponíveis
        if 'results_df' in st.session_state:
            st.subheader("📊 Resultados do Processamento")
            self.show_processing_results(st.session_state['results_df'])
    
    def show_processing_results(self, results_df):
        """Mostra resultados do processamento"""
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total de Estudantes", len(results_df))
        with col2:
            st.metric("Theta Médio", f"{results_df['theta'].mean():.3f}")
        with col3:
            st.metric("Nota ENEM Média", f"{results_df['enem_score'].mean():.1f}")
        with col4:
            st.metric("Desvio Padrão Theta", f"{results_df['theta'].std():.3f}")
        
        col1, col2 = st.columns(2)
        with col1:
            fig_theta = px.histogram(results_df, x='theta', nbins=30, 
                                   title="Distribuição de Theta")
            st.plotly_chart(fig_theta, use_container_width=True, key=self.get_unique_key("hist_theta_processing"))
        with col2:
            fig_enem = px.histogram(results_df, x='enem_score', nbins=30,
                                  title="Distribuição de Notas ENEM")
            st.plotly_chart(fig_enem, use_container_width=True, key=self.get_unique_key("hist_enem_processing"))
        
        st.subheader("📋 Resultados Detalhados")
        st.dataframe(results_df.head(20))
        
        csv = results_df.to_csv(index=False)
        st.download_button(
            label="📥 Download dos Resultados (CSV)",
            data=csv,
            file_name="resultados_tri.csv",
            mime="text/csv"
        )
        
        exec_id = st.session_state.get('execution_id')
        if exec_id:
            st.info(f"🔎 Resultados armazenados no banco para execução id={exec_id}")
    
    def analysis_tab(self):
        """Aba de análise e visualizações"""
        st.header("📈 Análise e Visualizações")
        
        if 'results_df' not in st.session_state:
            st.warning("⚠️ Processe dados TRI primeiro na aba 'Processamento TRI'")
            return
        
        results_df = st.session_state['results_df']
        responses_df = st.session_state.get('responses_df')
        params_df = st.session_state.get('params_df')
        
        # Seleção de análises
        analysis_type = st.selectbox(
            "Tipo de Análise:",
            ["Distribuições", "Correlações", "Parâmetros dos Itens", "Análise Comparativa"]
        )
        
        if analysis_type == "Distribuições":
            self.show_distributions_analysis(results_df)
        elif analysis_type == "Correlações":
            self.show_correlations_analysis(results_df, responses_df)
        elif analysis_type == "Parâmetros dos Itens":
            if params_df is not None:
                self.show_item_parameters_analysis(params_df)
            else:
                st.warning("⚠️ Carregue parâmetros dos itens para esta análise")
        elif analysis_type == "Análise Comparativa":
            self.show_comparative_analysis(results_df)
    
    def show_distributions_analysis(self, results_df):
        """Mostra análise de distribuições"""
        st.subheader("📊 Análise de Distribuições")
        
        # Estatísticas descritivas
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Estatísticas de Theta")
            theta_stats = results_df['theta'].describe()
            st.dataframe(theta_stats)
        
        with col2:
            st.subheader("📈 Estatísticas de Nota ENEM")
            enem_stats = results_df['enem_score'].describe()
            st.dataframe(enem_stats)
        
        # Gráficos de distribuição
        col1, col2 = st.columns(2)
        
        with col1:
            # Boxplot de theta
            fig_box_theta = px.box(results_df, y='theta', title="Boxplot de Theta")
            st.plotly_chart(fig_box_theta, use_container_width=True, key=self.get_unique_key("box_theta_dist"))
        
        with col2:
            # Boxplot de ENEM
            fig_box_enem = px.box(results_df, y='enem_score', title="Boxplot de Notas ENEM")
            st.plotly_chart(fig_box_enem, use_container_width=True, key=self.get_unique_key("box_enem_dist"))
        
        # Distribuição cumulativa
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
                                          name='ENEM Score', mode='lines'))
        
        fig_cumulative.update_layout(title="Distribuição Cumulativa", 
                                   xaxis_title="Valor", yaxis_title="Probabilidade")
        st.plotly_chart(fig_cumulative, use_container_width=True, key=self.get_unique_key("cumulative_dist"))
    
    def show_correlations_analysis(self, results_df, responses_df):
        """Mostra análise de correlações"""
        st.subheader("🔗 Análise de Correlações")
        
        if responses_df is not None and 'acertos' in results_df.columns:
            # Correlação theta vs acertos
            correlation = results_df['acertos'].corr(results_df['theta'])
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Correlação Theta-Acertos", f"{correlation:.3f}")
                
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
        else:
            st.warning("⚠️ Dados de acertos não disponíveis para análise de correlação")
    
    def show_item_parameters_analysis(self, params_df):
        """Mostra análise dos parâmetros dos itens"""
        st.subheader("📋 Análise dos Parâmetros dos Itens")
        
        # Estatísticas dos parâmetros
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("Parâmetro a (Discriminação)")
            st.dataframe(params_df['a'].describe())
        
        with col2:
            st.subheader("Parâmetro b (Dificuldade)")
            st.dataframe(params_df['b'].describe())
        
        with col3:
            st.subheader("Parâmetro c (Acerto Casual)")
            st.dataframe(params_df['c'].describe())
        
        # Gráficos dos parâmetros
        fig_params = make_subplots(rows=2, cols=2, 
                                  subplot_titles=('Parâmetro a', 'Parâmetro b', 
                                                'Parâmetro c', 'Distribuição'))
        
        # Parâmetro a
        fig_params.add_trace(go.Scatter(x=params_df.index, y=params_df['a'], 
                                       mode='lines+markers', name='a'), row=1, col=1)
        
        # Parâmetro b
        fig_params.add_trace(go.Scatter(x=params_df.index, y=params_df['b'], 
                                       mode='lines+markers', name='b'), row=1, col=2)
        
        # Parâmetro c
        fig_params.add_trace(go.Scatter(x=params_df.index, y=params_df['c'], 
                                       mode='lines+markers', name='c'), row=2, col=1)
        
        # Histograma
        fig_params.add_trace(go.Histogram(x=params_df['a'], name='a'), row=2, col=2)
        fig_params.add_trace(go.Histogram(x=params_df['b'], name='b'), row=2, col=2)
        fig_params.add_trace(go.Histogram(x=params_df['c'], name='c'), row=2, col=2)
        
        fig_params.update_layout(height=600, title_text="Análise dos Parâmetros dos Itens")
        st.plotly_chart(fig_params, use_container_width=True, key=self.get_unique_key("item_params_analysis"))
    
    def show_comparative_analysis(self, results_df):
        """Mostra análise comparativa"""
        st.subheader("📊 Análise Comparativa")
        
        # Percentis
        percentiles = [10, 25, 50, 75, 90]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Percentis de Theta")
            theta_percentiles = [np.percentile(results_df['theta'], p) for p in percentiles]
            percentiles_df = pd.DataFrame({
                'Percentil': [f'P{p}' for p in percentiles],
                'Theta': theta_percentiles
            })
            st.dataframe(percentiles_df)
        
        with col2:
            st.subheader("Percentis de Nota ENEM")
            enem_percentiles = [np.percentile(results_df['enem_score'], p) for p in percentiles]
            percentiles_df = pd.DataFrame({
                'Percentil': [f'P{p}' for p in percentiles],
                'ENEM Score': enem_percentiles
            })
            st.dataframe(percentiles_df)
        
        # Gráfico de percentis
        fig_percentiles = go.Figure()
        
        fig_percentiles.add_trace(go.Scatter(x=percentiles, y=theta_percentiles, 
                                           mode='lines+markers', name='Theta'))
        fig_percentiles.add_trace(go.Scatter(x=percentiles, y=enem_percentiles, 
                                           mode='lines+markers', name='ENEM Score'))
        
        fig_percentiles.update_layout(title="Distribuição por Percentis",
                                    xaxis_title="Percentil", yaxis_title="Valor")
        st.plotly_chart(fig_percentiles, use_container_width=True, key=self.get_unique_key("percentiles_comparative"))
    
    def reports_tab(self):
        """Aba de relatórios"""
        st.header("📋 Relatórios")
        
        if 'results_df' not in st.session_state:
            st.warning("⚠️ Processe dados TRI primeiro para gerar relatórios")
            return
        
        results_df = st.session_state['results_df']
        responses_df = st.session_state.get('responses_df')
        params_df = st.session_state.get('params_df')
        
        # Tipos de relatório
        report_type = st.selectbox(
            "Tipo de Relatório:",
            ["Relatório Completo", "Resumo Estatístico", "Relatório de Qualidade"]
        )
        
        if st.button("📊 Gerar Relatório", type="primary"):
            with st.spinner("Gerando relatório..."):
                try:
                    if report_type == "Relatório Completo":
                        self.generate_complete_report(results_df, responses_df, params_df)
                    elif report_type == "Resumo Estatístico":
                        self.generate_summary_report(results_df, responses_df)
                    elif report_type == "Relatório de Qualidade":
                        self.generate_quality_report(results_df, responses_df)
                    
                    st.success("✅ Relatório gerado com sucesso!")
                    
                except Exception as e:
                    st.error(f"❌ Erro ao gerar relatório: {e}")
    
    def generate_complete_report(self, results_df, responses_df, params_df):
        """Gera relatório completo"""
        st.subheader("📊 Relatório Completo")
        
        # Estatísticas gerais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Estudantes", len(results_df))
        with col2:
            st.metric("Theta Médio", f"{results_df['theta'].mean():.3f}")
        with col3:
            st.metric("Nota ENEM Média", f"{results_df['enem_score'].mean():.1f}")
        with col4:
            st.metric("Desvio Padrão", f"{results_df['theta'].std():.3f}")
        
        # Gráficos completos
        fig_complete = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Distribuição de Theta', 'Distribuição de Notas ENEM',
                          'Theta vs Acertos', 'Parâmetros dos Itens')
        )
        
        # Distribuição de theta
        fig_complete.add_trace(go.Histogram(x=results_df['theta'], nbinsx=30), row=1, col=1)
        
        # Distribuição de ENEM
        fig_complete.add_trace(go.Histogram(x=results_df['enem_score'], nbinsx=30), row=1, col=2)
        
        # Theta vs acertos
        if 'acertos' in results_df.columns:
            fig_complete.add_trace(go.Scatter(x=results_df['acertos'], y=results_df['theta'],
                                            mode='markers'), row=2, col=1)
        
        # Parâmetros dos itens
        if params_df is not None:
            fig_complete.add_trace(go.Scatter(x=params_df.index, y=params_df['a'],
                                            mode='lines+markers', name='a'), row=2, col=2)
        
        fig_complete.update_layout(height=800, title_text="Relatório Completo - Sistema TRI")
        st.plotly_chart(fig_complete, use_container_width=True, key=self.get_unique_key("complete_report"))
    
    def generate_summary_report(self, results_df, responses_df):
        """Gera relatório resumido"""
        st.subheader("📋 Resumo Estatístico")
        
        # Estatísticas detalhadas
        stats = self.visualizer.create_summary_statistics(results_df, responses_df)
        
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
        
        # Percentis
        st.subheader("📊 Percentis")
        percentiles = [5, 10, 25, 50, 75, 90, 95]
        
        theta_percentiles = [np.percentile(results_df['theta'], p) for p in percentiles]
        enem_percentiles = [np.percentile(results_df['enem_score'], p) for p in percentiles]
        
        percentiles_df = pd.DataFrame({
            'Percentil': [f'P{p}' for p in percentiles],
            'Theta': theta_percentiles,
            'ENEM Score': enem_percentiles
        })
        
        st.dataframe(percentiles_df)
    
    def generate_quality_report(self, results_df, responses_df):
        """Gera relatório de qualidade"""
        st.subheader("🔍 Relatório de Qualidade")
        
        # Validação dos resultados
        validation = self.validator.validate_results(results_df, responses_df)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("✅ Validação")
            if validation['valid']:
                st.success("Resultados válidos")
            else:
                st.error("Problemas encontrados")
                for error in validation['errors']:
                    st.error(f"• {error}")
        
        with col2:
            st.subheader("⚠️ Avisos")
            if validation['warnings']:
                for warning in validation['warnings']:
                    st.warning(f"• {warning}")
            else:
                st.success("Nenhum aviso")
        
        # Métricas de qualidade
        if responses_df is not None:
            quality_metrics = self.data_processor.validate_data_quality(responses_df)
            
            st.subheader("📊 Métricas de Qualidade")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Completude", f"{quality_metrics.get('completeness', 0):.1%}")
            with col2:
                st.metric("Média de Acertos", f"{quality_metrics.get('mean_accuracy', 0):.2f}")
            with col3:
                st.metric("Estudantes Incompletos", quality_metrics.get('incomplete_students', 0))
            with col4:
                st.metric("Total de Respostas", quality_metrics.get('total_responses', 0))
    
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
            with st.expander(f"📊 Execução #{exec_info['execution_id']} - {str(exec_info['created_at'])[:19]}"):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Estudantes", exec_info['total_students'])
                with col2:
                    st.metric("Theta Médio", f"{exec_info['theta_mean']:.3f}")
                with col3:
                    st.metric("ENEM Médio", f"{exec_info['enem_mean']:.1f}")
                with col4:
                    st.metric("Status", exec_info['status'])
                
                c1, c2, c3 = st.columns([1,1,1])
                with c1:
                    if st.button(f"🔄 Carregar resultados", key=f"load_exec_{exec_info['execution_id']}"):
                        try:
                            session = SessionLocal()
                            df = crud.get_execution_results(session, exec_info['execution_id'])
                            if df.empty:
                                st.warning("Sem resultados para esta execução.")
                            else:
                                st.session_state['results_df'] = df
                                st.success("✅ Resultados carregados na aba Processamento/Análise.")
                        finally:
                            session.close()
                with c2:
                    if st.button(f"📥 Download CSV", key=f"dl_exec_{exec_info['execution_id']}"):
                        try:
                            session = SessionLocal()
                            df = crud.get_execution_results(session, exec_info['execution_id'])
                        finally:
                            session.close()
                        if df.empty:
                            st.warning("Sem resultados para exportar.")
                        else:
                            st.download_button(
                                label="Baixar CSV",
                                data=df.to_csv(index=False),
                                file_name=f"exec_{exec_info['execution_id']}.csv",
                                mime="text/csv",
                                key=f"dbtn_exec_{exec_info['execution_id']}"
                            )
                with c3:
                    if st.button(f"🗑️ Deletar", key=f"del_exec_{exec_info['execution_id']}"):
                        try:
                            session = SessionLocal()
                            ok = crud.delete_execution(session, exec_info['execution_id'])
                        finally:
                            session.close()
                        if ok:
                            st.success("✅ Execução deletada.")
                            st.rerun()
                        else:
                            st.error("❌ Não foi possível deletar.")


def main():
    """Função principal do dashboard"""
    dashboard = TRIDashboard()
    dashboard.run()


if __name__ == "__main__":
    main()
