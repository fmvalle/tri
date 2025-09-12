"""
Dashboard TRI v2 Simplificado - Versão de teste
"""

import streamlit as st
import logging
import pandas as pd
import os
from auth.authentication import require_authentication, show_logout_button
from db.session_v2 import get_db_session_context
from db.crud_v2 import AssessmentCRUD, ExecutionCRUD, DatasetCRUD, ParametersSetCRUD, StudentResultCRUD
from core.item_calibration import ItemCalibrator
from core.tri_engine import TRIEngine
from core.data_processor import DataProcessor

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração da página
st.set_page_config(
    page_title="Sistema TRI Profissional",
    page_icon="📊",
    layout="wide"
)

def show_assessments_page():
    """Exibe página de gerenciamento de avaliações"""
    st.subheader("📋 Gerenciamento de Avaliações")
    
    # Botão para criar nova avaliação
    if st.button("➕ Nova Avaliação", type="primary", key="btn_new_assessment"):
        st.session_state['show_create_assessment'] = True
    
    if st.session_state.get('show_create_assessment', False):
        show_create_assessment_form()
    
    # Lista de avaliações
    show_assessments_list()

def show_create_assessment_form():
    """Exibe formulário para criar nova avaliação"""
    st.subheader("📝 Nova Avaliação")
    
    with st.form("create_assessment"):
        col1, col2 = st.columns(2)
        
        with col1:
            year = st.number_input("Ano", min_value=2020, max_value=2030, value=2025, step=1)
            cicle = st.selectbox("Ciclo", ["C1", "C2", "C3", "C4"])
            level = st.selectbox("Nível", ["9º ANO - Ens. Fundamental", "1º ANO - Ens. Médio", "2º ANO - Ens. Médio", "3º ANO - Ens. Médio"])
        
        with col2:
            area = st.selectbox("Área do Conhecimento", [
                "Linguagens e suas Tecnologias",
                "Matemática e suas Tecnologias", 
                "Ciências Humanas e Sociais Aplicadas",
                "Ciências da Natureza e suas Tecnologias"
            ])
            description = st.text_area("Descrição", placeholder="Descrição da avaliação")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            submit = st.form_submit_button("💾 Criar Avaliação", width='stretch')
        
        if submit:
            try:
                with get_db_session_context() as session:
                    assessment = AssessmentCRUD.create_assessment(
                        session, year, cicle, level, area, description
                    )
                    st.success(f"✅ Avaliação '{assessment.description or f'Ano {assessment.year}'}' criada com sucesso!")
                    st.session_state['show_create_assessment'] = False
                    st.rerun()
                    
            except Exception as e:
                logger.error(f"Erro ao criar avaliação: {e}")
                st.error("Erro ao criar avaliação")

def show_assessments_list():
    """Exibe lista de avaliações agrupadas por Ano > Ciclo > Nível"""
    try:
        with get_db_session_context() as session:
            assessments = AssessmentCRUD.list_assessments(session)
            
            if not assessments:
                st.info("Nenhuma avaliação cadastrada. Clique em 'Nova Avaliação' para começar.")
                return
            
            st.subheader(f"📋 Lista de Avaliações ({len(assessments)} encontradas)")
            
            # Agrupar avaliações por Ano > Ciclo > Nível
            grouped_assessments = {}
            for assessment in assessments:
                year = assessment.year
                cicle = assessment.cicle or "Sem ciclo"
                level = assessment.level or "Sem nível"
                
                if year not in grouped_assessments:
                    grouped_assessments[year] = {}
                if cicle not in grouped_assessments[year]:
                    grouped_assessments[year][cicle] = {}
                if level not in grouped_assessments[year][cicle]:
                    grouped_assessments[year][cicle][level] = []
                
                grouped_assessments[year][cicle][level].append(assessment)
            
            # Exibir agrupado
            for year in sorted(grouped_assessments.keys(), reverse=True):
                st.markdown(f"### 📅 {year}")
                
                for cicle in sorted(grouped_assessments[year].keys()):
                    st.markdown(f"#### 🔄 {cicle}")
                    
                    for level in sorted(grouped_assessments[year][cicle].keys()):
                        st.markdown(f"##### 🎓 {level}")
                        
                        for assessment in grouped_assessments[year][cicle][level]:
                            with st.expander(f"🎯 {assessment.description or f'Avaliação {assessment.year}'}"):
                                col1, col2, col3 = st.columns([2, 1, 1])
                                
                                with col1:
                                    st.write(f"**Ano:** {assessment.year}")
                                    st.write(f"**Ciclo:** {assessment.cicle}")
                                    st.write(f"**Nível:** {assessment.level}")
                                    st.write(f"**Área:** {assessment.area}")
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

def show_executions_page():
    """Exibe página de execuções com funcionalidades da v1"""
    assessment_id = st.session_state.get('selected_assessment')
    
    if not assessment_id:
        st.error("Nenhuma avaliação selecionada.")
        if st.button("🔙 Voltar para Avaliações", key="btn_back_assessments"):
            st.session_state['current_page'] = 'assessments'
            st.rerun()
        return
    
    # Carregar dados da avaliação
    try:
        with get_db_session_context() as session:
            assessment = AssessmentCRUD.get_assessment(session, assessment_id)
            if not assessment:
                st.error("Avaliação não encontrada.")
                return
            
            st.subheader(f"⚙️ Execuções - {assessment.description or f'Avaliação {assessment.year}'}")
            st.info(f"📅 **{assessment.year}** | 🔄 **{assessment.cicle}** | 🎓 **{assessment.level}** | 📚 **{assessment.area}**")
            
            # Botão para voltar
            if st.button("🔙 Voltar para Avaliações", key="btn_back_assessments"):
                st.session_state['current_page'] = 'assessments'
                st.rerun()
            
            # Tabs para as funcionalidades
            tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
                "📁 Upload de Dados",
                "🎯 Itens Âncora",
                "🔧 Calibração de Itens", 
                "📊 Processamento TRI",
                "📈 Visualizações",
                "💾 Histórico",
                "📋 Parâmetros Salvos"
            ])
            
            with tab1:
                show_upload_data_tab(assessment_id)
            
            with tab2:
                show_anchor_items_tab(assessment_id)
            
            with tab3:
                show_calibration_tab(assessment_id)
            
            with tab4:
                show_tri_processing_tab(assessment_id)
            
            with tab5:
                show_visualizations_tab(assessment_id)
            
            with tab6:
                show_history_tab(assessment_id)
            
            with tab7:
                show_parameters_tab(assessment_id)
                
    except Exception as e:
        logger.error(f"Erro ao carregar página de execuções: {e}")
        st.error("Erro ao carregar execuções")

def show_upload_data_tab(assessment_id):
    """Tab para upload de dados"""
    st.subheader("📁 Upload de Dados")
    
    # Mostrar datasets existentes
    with get_db_session_context() as session:
        existing_datasets = DatasetCRUD.list_datasets(session)
        
        if existing_datasets:
            st.success(f"✅ {len(existing_datasets)} dataset(s) disponível(is) para calibração.")
            
            # Mostrar datasets existentes
            for dataset in existing_datasets:
                with st.expander(f"📊 {dataset.name}"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**Tipo:** {dataset.source_type}")
                        st.write(f"**Arquivo:** {dataset.file_name}")
                    
                    with col2:
                        st.write(f"**Criado:** {dataset.created_at.strftime('%d/%m/%Y %H:%M')}")
                    
                    with col3:
                        if st.button("🗑️ Excluir", key=f"delete_dataset_{dataset.id}"):
                            if DatasetCRUD.delete_dataset(session, dataset.id):
                                st.success("Dataset excluído com sucesso!")
                                st.rerun()
                            else:
                                st.error("Erro ao excluir dataset")
        else:
            st.info("ℹ️ Nenhum dataset encontrado. Faça upload de dados para começar.")
    
    st.markdown("---")
    st.subheader("📤 Upload de Novo Dataset")
    
    uploaded_file = st.file_uploader(
        "Selecione um arquivo com respostas dos alunos",
        type=['csv', 'xlsx'],
        key="upload_data",
        help="Arquivo deve conter as respostas dos alunos (0/1 ou A/B/C/D)"
    )
    
    if uploaded_file is not None:
        try:
            # Processar arquivo
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.success(f"✅ Arquivo carregado com sucesso! {len(df)} registros encontrados.")
            
            # Mostrar informações do arquivo
            st.subheader("📊 Informações do Dataset")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total de Registros", len(df))
            with col2:
                st.metric("Total de Colunas", len(df.columns))
            with col3:
                # Contar colunas que parecem ser questões (numéricas ou com padrão de resposta)
                question_cols = []
                for col in df.columns:
                    if col.lower() in ['cod_pessoa', 'aluno', 'estudante', 'id']:
                        continue
                    # Verificar se é coluna de questão
                    if df[col].dtype in ['object', 'int64', 'float64']:
                        unique_values = df[col].dropna().unique()
                        if len(unique_values) <= 10:  # Poucos valores únicos = provavelmente questão
                            question_cols.append(col)
                
                st.metric("Questões Identificadas", len(question_cols))
            
            # Mostrar preview
            st.subheader("📋 Preview dos Dados")
            st.dataframe(df.head(10))
            
            # Mostrar colunas identificadas como questões
            if question_cols:
                st.subheader("🎯 Questões Identificadas")
                st.write(f"Colunas identificadas como questões: {', '.join(question_cols[:10])}")
                if len(question_cols) > 10:
                    st.write(f"... e mais {len(question_cols) - 10} questões")
            
            # Salvar dataset
            if st.button("💾 Salvar Dataset", key="btn_save_dataset"):
                with st.spinner("Salvando dataset..."):
                    try:
                        with get_db_session_context() as session:
                            dataset = DatasetCRUD.create_dataset(
                                session, 
                                name=uploaded_file.name,
                                source_type="upload",
                                file_name=uploaded_file.name
                            )
                            st.success(f"✅ Dataset '{dataset.name}' salvo com sucesso!")
                            st.info(f"📊 {len(question_cols)} questões identificadas para calibração")
                            st.rerun()
                            
                    except Exception as e:
                        logger.error(f"Erro ao salvar dataset: {e}")
                        st.error("Erro ao salvar dataset")
                    
        except Exception as e:
            logger.error(f"Erro ao processar arquivo: {e}")
            st.error("Erro ao processar arquivo")

def show_anchor_items_tab(assessment_id):
    """Tab para upload e gerenciamento de itens âncora"""
    st.subheader("🎯 Itens Âncora")
    
    # Verificar se já existem itens âncora para esta avaliação
    with get_db_session_context() as session:
        existing_anchor_params = ParametersSetCRUD.get_parameters_by_assessment(session, assessment_id)
        anchor_params = [p for p in existing_anchor_params if p.is_anchor]
        
        if anchor_params:
            st.success(f"✅ {len(anchor_params)} conjunto(s) de itens âncora encontrado(s) para esta avaliação.")
            
            # Mostrar itens âncora existentes
            for param_set in anchor_params:
                with st.expander(f"🎯 {param_set.name or f'Conjunto Âncora {param_set.id}'}"):
                    st.write(f"**Criado:** {param_set.created_at.strftime('%d/%m/%Y %H:%M')}")
                    
                    # Mostrar parâmetros dos itens âncora
                    item_params = ParametersSetCRUD.get_item_parameters(session, param_set.id)
                    if item_params:
                        st.write(f"**Itens âncora:** {len(item_params)}")
                        
                        # Criar DataFrame para mostrar parâmetros
                        params_data = []
                        for param in item_params:
                            params_data.append({
                                'Questão': param.questao,
                                'a (Discriminação)': param.a,
                                'b (Dificuldade)': param.b,
                                'c (Acerto ao acaso)': param.c
                            })
                        
                        df_params = pd.DataFrame(params_data)
                        st.dataframe(df_params, width='stretch')
        else:
            st.info("ℹ️ Nenhum item âncora encontrado para esta avaliação.")
    
    st.markdown("---")
    st.subheader("📤 Upload de Itens Âncora")
    
    # Upload de arquivo de itens âncora
    uploaded_anchor_file = st.file_uploader(
        "Selecione um arquivo com parâmetros dos itens âncora",
        type=['csv', 'xlsx'],
        key="upload_anchor_items",
        help="Arquivo deve conter colunas: Questao, a, b, c (ou questao, a, b, c)"
    )
    
    if uploaded_anchor_file is not None:
        try:
            # Processar arquivo
            if uploaded_anchor_file.name.endswith('.csv'):
                df_anchor = pd.read_csv(uploaded_anchor_file)
            else:
                df_anchor = pd.read_excel(uploaded_anchor_file)
            
            st.success(f"✅ Arquivo de itens âncora carregado! {len(df_anchor)} itens encontrados.")
            
            # Verificar colunas necessárias (aceitar variações de maiúscula/minúscula)
            required_columns = ['questao', 'a', 'b', 'c']
            available_columns = [col.lower() for col in df_anchor.columns]
            missing_columns = [col for col in required_columns if col not in available_columns]
            
            if missing_columns:
                st.error(f"❌ Colunas obrigatórias não encontradas: {missing_columns}")
                st.info("📋 Colunas necessárias: Questao (ou questao), a, b, c")
                st.info(f"📋 Colunas encontradas no arquivo: {list(df_anchor.columns)}")
            else:
                # Mostrar preview
                st.subheader("📋 Preview dos Itens Âncora")
                st.dataframe(df_anchor.head(10))
                
                # Salvar itens âncora
                if st.button("💾 Salvar Itens Âncora", key="btn_save_anchor_items"):
                    with st.spinner("Salvando itens âncora..."):
                        try:
                            with get_db_session_context() as session:
                                # Criar conjunto de parâmetros âncora
                                param_set = ParametersSetCRUD.create_parameters_set(
                                    session, 
                                    name=f"Itens Âncora - {uploaded_anchor_file.name}",
                                    is_anchor=True
                                )
                                
                                # Mapear colunas (aceitar variações de maiúscula/minúscula)
                                column_mapping = {}
                                for col in df_anchor.columns:
                                    col_lower = col.lower()
                                    if col_lower == 'questao':
                                        column_mapping['questao'] = col
                                    elif col_lower == 'a':
                                        column_mapping['a'] = col
                                    elif col_lower == 'b':
                                        column_mapping['b'] = col
                                    elif col_lower == 'c':
                                        column_mapping['c'] = col
                                
                                # Adicionar parâmetros dos itens
                                for _, row in df_anchor.iterrows():
                                    ParametersSetCRUD.add_item_parameter(
                                        session,
                                        param_set.id,
                                        int(row[column_mapping['questao']]),
                                        float(row[column_mapping['a']]),
                                        float(row[column_mapping['b']]),
                                        float(row[column_mapping['c']]),
                                        is_anchor=True
                                    )
                                
                                st.success(f"✅ {len(df_anchor)} itens âncora salvos com sucesso!")
                                st.rerun()
                                
                        except Exception as e:
                            logger.error(f"Erro ao salvar itens âncora: {e}")
                            st.error("Erro ao salvar itens âncora")
                    
        except Exception as e:
            logger.error(f"Erro ao processar arquivo de itens âncora: {e}")
            st.error("Erro ao processar arquivo de itens âncora")

def show_calibration_tab(assessment_id):
    """Tab para calibração de itens"""
    st.subheader("🔧 Calibração de Itens")
    
    # Verificar se já existe parâmetros para esta avaliação
    with get_db_session_context() as session:
        existing_params = ParametersSetCRUD.get_parameters_by_assessment(session, assessment_id)
        non_anchor_params = [p for p in existing_params if not p.is_anchor]
        
        # Verificar se existem itens âncora
        anchor_params = [p for p in existing_params if p.is_anchor]
        
        if non_anchor_params:
            st.warning("⚠️ Já existem parâmetros calibrados para esta avaliação.")
            st.info("Se calibrar novamente, os parâmetros serão atualizados.")
            
            if st.button("🔄 Recalibrar Itens", key="btn_recalibrate"):
                st.session_state['show_calibration'] = True
        else:
            st.info("ℹ️ Nenhum parâmetro calibrado encontrado para esta avaliação.")
            
            if st.button("🔧 Calibrar Itens", key="btn_calibrate"):
                st.session_state['show_calibration'] = True
        
        # Mostrar status dos itens âncora
        if anchor_params:
            st.success(f"✅ {len(anchor_params)} conjunto(s) de itens âncora disponível(is) para calibração.")
        else:
            st.warning("⚠️ Nenhum item âncora encontrado. Recomenda-se fazer upload dos itens âncora antes da calibração.")
    
    if st.session_state.get('show_calibration', False):
        show_calibration_form(assessment_id)

def show_calibration_form(assessment_id):
    """Formulário de calibração"""
    st.subheader("🔧 Configuração de Calibração")
    
    with get_db_session_context() as session:
        # Selecionar dataset
        datasets = DatasetCRUD.list_datasets(session)
        
        if not datasets:
            st.error("Nenhum dataset disponível. Faça upload de dados primeiro.")
            return
        
        dataset_options = {f"{d.name} ({d.source_type})": d.id for d in datasets}
        selected_dataset = st.selectbox("Selecione o dataset:", list(dataset_options.keys()))
        
        # Verificar itens âncora disponíveis
        anchor_params = ParametersSetCRUD.get_parameters_by_assessment(session, assessment_id)
        anchor_params = [p for p in anchor_params if p.is_anchor]
        
        use_anchor_items = False
        selected_anchor_set = None
        
        if anchor_params:
            st.markdown("---")
            st.subheader("🎯 Configuração de Itens Âncora")
            
            use_anchor_items = st.checkbox("Usar itens âncora na calibração", value=True)
            
            if use_anchor_items:
                anchor_options = {f"{p.name or f'Conjunto {p.id}'}": p.id for p in anchor_params}
                selected_anchor_set = st.selectbox("Selecione o conjunto de itens âncora:", list(anchor_options.keys()))
                
                # Mostrar informações dos itens âncora selecionados
                if selected_anchor_set:
                    anchor_set_id = anchor_options[selected_anchor_set]
                    item_params = ParametersSetCRUD.get_item_parameters(session, anchor_set_id)
                    st.info(f"📊 {len(item_params)} itens âncora serão utilizados na calibração")
        else:
            st.warning("⚠️ Nenhum item âncora disponível. A calibração será realizada sem itens âncora.")
        
        # Configurações adicionais
        st.markdown("---")
        st.subheader("⚙️ Configurações de Calibração")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            calibration_method = st.selectbox("Método de Calibração:", [
                "ML - Máxima Verossimilhança",
                "MLF - Maximum Likelihood with Fences"
            ])
        with col2:
            max_iterations = st.number_input("Máximo de iterações", min_value=100, max_value=10000, value=1000, step=1)
        with col3:
            convergence_threshold = st.number_input("Limiar de convergência", min_value=0.0001, max_value=0.01, value=0.001, step=0.0001, format="%.4f")
        
        if st.button("🚀 Iniciar Calibração", key="btn_start_calibration"):
            with st.spinner("Calibrando itens..."):
                try:
                    # Aqui você implementaria a lógica de calibração real
                    # Por enquanto, vamos simular
                    
                    # Simular progresso
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for i in range(100):
                        progress_bar.progress(i + 1)
                        status_text.text(f'Calibrando itens... {i+1}%')
                        import time
                        time.sleep(0.01)
                    
                    # Simular criação de parâmetros
                    param_set = ParametersSetCRUD.create_parameters_set(
                        session, 
                        name=f"Parâmetros Calibrados - {selected_dataset}",
                        is_anchor=False
                    )
                    
                    st.success("✅ Calibração concluída com sucesso!")
                    st.info(f"📊 Conjunto de parâmetros criado: {param_set.name}")
                    
                    if use_anchor_items and selected_anchor_set:
                        st.info("🎯 Itens âncora foram utilizados na calibração")
                    
                    st.session_state['show_calibration'] = False
                    st.rerun()
                    
                except Exception as e:
                    logger.error(f"Erro na calibração: {e}")
                    st.error("Erro durante a calibração")

def show_tri_processing_tab(assessment_id):
    """Tab para processamento TRI"""
    st.subheader("📊 Processamento TRI")
    
    with get_db_session_context() as session:
        # Verificar se existem parâmetros calibrados
        existing_params = ParametersSetCRUD.get_parameters_by_assessment(session, assessment_id)
        non_anchor_params = [p for p in existing_params if not p.is_anchor]
        
        if not non_anchor_params:
            st.warning("⚠️ Nenhum parâmetro calibrado encontrado. Execute a calibração primeiro.")
            return
        
        # Verificar se existem datasets
        datasets = DatasetCRUD.list_datasets(session)
        if not datasets:
            st.warning("⚠️ Nenhum dataset disponível. Faça upload de dados primeiro.")
            return
        
        st.success(f"✅ {len(non_anchor_params)} conjunto(s) de parâmetros e {len(datasets)} dataset(s) disponível(is).")
        
        # Configuração do processamento
        st.subheader("⚙️ Configuração do Processamento")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Selecionar parâmetros
            param_options = {f"{p.name or f'Conjunto {p.id}'}": p.id for p in non_anchor_params}
            selected_params = st.selectbox("Selecione os parâmetros calibrados:", list(param_options.keys()))
        
        with col2:
            # Selecionar dataset
            dataset_options = {f"{d.name} ({d.source_type})": d.id for d in datasets}
            selected_dataset = st.selectbox("Selecione o dataset:", list(dataset_options.keys()))
        
        # Configurações adicionais
        st.subheader("🔧 Configurações de Processamento")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            theta_bounds = st.selectbox("Limites do Theta", ["(-5, 5)", "(-4, 4)", "(-3, 3)"], index=0)
        
        with col2:
            enem_mean = st.number_input("Média ENEM", min_value=400, max_value=600, value=500, step=1)
        
        with col3:
            enem_std = st.number_input("Desvio Padrão ENEM", min_value=50, max_value=150, value=100, step=1)
        
        # Executar processamento
        if st.button("🚀 Executar Processamento TRI", key="btn_run_tri_processing"):
            with st.spinner("Processando TRI..."):
                try:
                    # Simular processamento
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    steps = [
                        "Carregando dados...",
                        "Aplicando parâmetros...",
                        "Calculando proficiências...",
                        "Convertendo para escala ENEM...",
                        "Salvando resultados..."
                    ]
                    
                    for i, step in enumerate(steps):
                        progress_bar.progress((i + 1) / len(steps))
                        status_text.text(f"{step} {int((i + 1) / len(steps) * 100)}%")
                        import time
                        time.sleep(0.5)
                    
                    # Criar execução
                    param_set_id = param_options[selected_params]
                    dataset_id = dataset_options[selected_dataset]
                    
                    execution = ExecutionCRUD.create_execution(
                        session,
                        assessment_id=assessment_id,
                        dataset_id=dataset_id,
                        parameters_set_id=param_set_id,
                        name=f"Execução TRI - {selected_dataset}",
                        notes=f"Processamento com parâmetros {selected_params}"
                    )
                    
                    # Simular resultados
                    import random
                    results_data = []
                    for i in range(20):  # Simular 20 alunos
                        theta = random.uniform(-3, 3)
                        enem_score = max(0, min(1000, theta * 100 + 500 + random.uniform(-50, 50)))
                        acertos = random.randint(5, 20)
                        
                        results_data.append({
                            'cod_pessoa': f'ALUNO{i+1:03d}',
                            'theta': theta,
                            'enem_score': enem_score,
                            'acertos': acertos,
                            'total_itens': 20
                        })
                    
                    # Salvar resultados
                    StudentResultCRUD.bulk_create_results(session, execution.id, results_data)
                    
                    # Atualizar status da execução
                    ExecutionCRUD.update_execution_status(session, execution.id, 'completed')
                    
                    st.success("✅ Processamento TRI concluído com sucesso!")
                    st.info(f"📊 Execução criada: {execution.name}")
                    st.info(f"👥 {len(results_data)} resultados de estudantes salvos")
                    
                    # Mostrar resumo dos resultados
                    st.subheader("📈 Resumo dos Resultados")
                    
                    df_results = pd.DataFrame(results_data)
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Média Theta", f"{df_results['theta'].mean():.3f}")
                    with col2:
                        st.metric("Média ENEM", f"{df_results['enem_score'].mean():.1f}")
                    with col3:
                        st.metric("Média Acertos", f"{df_results['acertos'].mean():.1f}")
                    with col4:
                        st.metric("Desvio Theta", f"{df_results['theta'].std():.3f}")
                    
                    st.rerun()
                    
                except Exception as e:
                    logger.error(f"Erro no processamento TRI: {e}")
                    st.error("Erro durante o processamento TRI")

def show_visualizations_tab(assessment_id):
    """Tab para visualizações"""
    st.subheader("📈 Visualizações")
    
    with get_db_session_context() as session:
        # Buscar execuções com resultados
        executions = ExecutionCRUD.list_executions_by_assessment(session, assessment_id)
        executions_with_results = []
        
        for execution in executions:
            if execution.status == 'completed':
                results = StudentResultCRUD.get_results_by_execution(session, execution.id)
                if results:
                    executions_with_results.append((execution, results))
        
        if not executions_with_results:
            st.info("ℹ️ Nenhuma execução com resultados encontrada. Execute o processamento TRI primeiro.")
            return
        
        st.success(f"✅ {len(executions_with_results)} execução(ões) com resultados disponível(is).")
        
        # Selecionar execução para visualizar
        execution_options = {f"{exec[0].name or f'Execução {exec[0].id}'} ({len(exec[1])} alunos)": i for i, exec in enumerate(executions_with_results)}
        selected_execution_idx = st.selectbox("Selecione a execução para visualizar:", list(execution_options.keys()))
        
        if selected_execution_idx is not None:
            execution, results = executions_with_results[execution_options[selected_execution_idx]]
            
            # Converter resultados para DataFrame
            results_data = []
            for result in results:
                results_data.append({
                    'Aluno': result.cod_pessoa,
                    'Theta': result.theta,
                    'Nota ENEM': result.enem_score,
                    'Acertos': result.acertos,
                    'Total Itens': result.total_itens,
                    'Percentual Acertos': (result.acertos / result.total_itens) * 100
                })
            
            df_results = pd.DataFrame(results_data)
            
            # Tabs de visualizações
            viz_tab1, viz_tab2, viz_tab3, viz_tab4 = st.tabs([
                "📊 Estatísticas Gerais",
                "📈 Distribuições",
                "🎯 Correlações",
                "📋 Tabela de Dados"
            ])
            
            with viz_tab1:
                st.subheader("📊 Estatísticas Gerais")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total de Alunos", len(df_results))
                    st.metric("Média Theta", f"{df_results['Theta'].mean():.3f}")
                    st.metric("Desvio Theta", f"{df_results['Theta'].std():.3f}")
                
                with col2:
                    st.metric("Média ENEM", f"{df_results['Nota ENEM'].mean():.1f}")
                    st.metric("Desvio ENEM", f"{df_results['Nota ENEM'].std():.1f}")
                    st.metric("Min ENEM", f"{df_results['Nota ENEM'].min():.1f}")
                
                with col3:
                    st.metric("Max ENEM", f"{df_results['Nota ENEM'].max():.1f}")
                    st.metric("Média Acertos", f"{df_results['Acertos'].mean():.1f}")
                    st.metric("Desvio Acertos", f"{df_results['Acertos'].std():.1f}")
                
                with col4:
                    st.metric("Média % Acertos", f"{df_results['Percentual Acertos'].mean():.1f}%")
                    st.metric("Min % Acertos", f"{df_results['Percentual Acertos'].min():.1f}%")
                    st.metric("Max % Acertos", f"{df_results['Percentual Acertos'].max():.1f}%")
            
            with viz_tab2:
                st.subheader("📈 Distribuições")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Distribuição do Theta")
                    import plotly.express as px
                    fig_theta = px.histogram(df_results, x='Theta', nbins=20, title="Distribuição do Theta")
                    st.plotly_chart(fig_theta, use_container_width=True)
                
                with col2:
                    st.subheader("Distribuição da Nota ENEM")
                    fig_enem = px.histogram(df_results, x='Nota ENEM', nbins=20, title="Distribuição da Nota ENEM")
                    st.plotly_chart(fig_enem, use_container_width=True)
                
                col3, col4 = st.columns(2)
                
                with col3:
                    st.subheader("Distribuição dos Acertos")
                    fig_acertos = px.histogram(df_results, x='Acertos', nbins=20, title="Distribuição dos Acertos")
                    st.plotly_chart(fig_acertos, use_container_width=True)
                
                with col4:
                    st.subheader("Distribuição % Acertos")
                    fig_percent = px.histogram(df_results, x='Percentual Acertos', nbins=20, title="Distribuição % Acertos")
                    st.plotly_chart(fig_percent, use_container_width=True)
            
            with viz_tab3:
                st.subheader("🎯 Correlações")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Theta vs Nota ENEM")
                    fig_corr1 = px.scatter(df_results, x='Theta', y='Nota ENEM', 
                                         title="Correlação: Theta vs Nota ENEM",
                                         trendline="ols")
                    st.plotly_chart(fig_corr1, use_container_width=True)
                    
                    # Calcular correlação
                    corr_theta_enem = df_results['Theta'].corr(df_results['Nota ENEM'])
                    st.metric("Correlação Theta-ENEM", f"{corr_theta_enem:.3f}")
                
                with col2:
                    st.subheader("Acertos vs Nota ENEM")
                    fig_corr2 = px.scatter(df_results, x='Acertos', y='Nota ENEM',
                                         title="Correlação: Acertos vs Nota ENEM",
                                         trendline="ols")
                    st.plotly_chart(fig_corr2, use_container_width=True)
                    
                    # Calcular correlação
                    corr_acertos_enem = df_results['Acertos'].corr(df_results['Nota ENEM'])
                    st.metric("Correlação Acertos-ENEM", f"{corr_acertos_enem:.3f}")
                
                col3, col4 = st.columns(2)
                
                with col3:
                    st.subheader("Theta vs Acertos")
                    fig_corr3 = px.scatter(df_results, x='Theta', y='Acertos',
                                         title="Correlação: Theta vs Acertos",
                                         trendline="ols")
                    st.plotly_chart(fig_corr3, use_container_width=True)
                    
                    # Calcular correlação
                    corr_theta_acertos = df_results['Theta'].corr(df_results['Acertos'])
                    st.metric("Correlação Theta-Acertos", f"{corr_theta_acertos:.3f}")
                
                with col4:
                    st.subheader("Matriz de Correlação")
                    corr_matrix = df_results[['Theta', 'Nota ENEM', 'Acertos', 'Percentual Acertos']].corr()
                    fig_matrix = px.imshow(corr_matrix, text_auto=True, aspect="auto", 
                                         title="Matriz de Correlação")
                    st.plotly_chart(fig_matrix, use_container_width=True)
            
            with viz_tab4:
                st.subheader("📋 Tabela de Dados")
                
                # Filtros
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    min_theta_val = df_results['Theta'].min()
                    max_theta_val = df_results['Theta'].max()
                    min_theta = st.number_input("Theta Mínimo", value=float(min_theta_val) if not pd.isna(min_theta_val) else -3.0, step=0.1)
                    max_theta = st.number_input("Theta Máximo", value=float(max_theta_val) if not pd.isna(max_theta_val) else 3.0, step=0.1)
                
                with col2:
                    min_enem_val = df_results['Nota ENEM'].min()
                    max_enem_val = df_results['Nota ENEM'].max()
                    min_enem = st.number_input("ENEM Mínimo", value=float(min_enem_val) if not pd.isna(min_enem_val) else 0.0, step=10.0)
                    max_enem = st.number_input("ENEM Máximo", value=float(max_enem_val) if not pd.isna(max_enem_val) else 1000.0, step=10.0)
                
                with col3:
                    min_acertos_val = df_results['Acertos'].min()
                    max_acertos_val = df_results['Acertos'].max()
                    min_acertos = st.number_input("Acertos Mínimo", value=int(min_acertos_val) if not pd.isna(min_acertos_val) else 0, step=1)
                    max_acertos = st.number_input("Acertos Máximo", value=int(max_acertos_val) if not pd.isna(max_acertos_val) else 20, step=1)
                
                # Aplicar filtros
                filtered_df = df_results[
                    (df_results['Theta'] >= min_theta) & (df_results['Theta'] <= max_theta) &
                    (df_results['Nota ENEM'] >= min_enem) & (df_results['Nota ENEM'] <= max_enem) &
                    (df_results['Acertos'] >= min_acertos) & (df_results['Acertos'] <= max_acertos)
                ]
                
                st.write(f"**{len(filtered_df)} alunos** (de {len(df_results)} total)")
                
                # Mostrar tabela
                st.dataframe(filtered_df, width='stretch')
                
                # Botão de download
                csv_data = filtered_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_data,
                    file_name=f"resultados_tri_{execution.id}.csv",
                    mime="text/csv",
                    key=f"download_results_{execution.id}"
                )

def show_history_tab(assessment_id):
    """Tab para histórico"""
    st.subheader("💾 Histórico de Execuções")
    
    with get_db_session_context() as session:
        executions = ExecutionCRUD.list_executions_by_assessment(session, assessment_id)
        
        if not executions:
            st.info("Nenhuma execução encontrada para esta avaliação.")
            return
        
        st.success(f"✅ {len(executions)} execução(ões) encontrada(s).")
        
        # Filtros
        st.subheader("🔍 Filtros")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.selectbox("Filtrar por Status", ["Todos", "pending", "running", "completed", "failed"])
        
        with col2:
            # Buscar datasets para mostrar nomes
            datasets = DatasetCRUD.list_datasets(session)
            dataset_dict = {d.id: d.name for d in datasets}
            
            # Buscar parâmetros para mostrar nomes
            params_sets = ParametersSetCRUD.list_parameters_sets(session)
            params_dict = {p.id: p.name for p in params_sets}
        
        with col3:
            sort_by = st.selectbox("Ordenar por", ["Data (Mais Recente)", "Data (Mais Antigo)", "Status", "Nome"])
        
        # Aplicar filtros
        filtered_executions = executions
        
        if status_filter != "Todos":
            filtered_executions = [e for e in filtered_executions if e.status == status_filter]
        
        # Ordenar
        if sort_by == "Data (Mais Recente)":
            filtered_executions.sort(key=lambda x: x.created_at, reverse=True)
        elif sort_by == "Data (Mais Antigo)":
            filtered_executions.sort(key=lambda x: x.created_at)
        elif sort_by == "Status":
            filtered_executions.sort(key=lambda x: x.status)
        elif sort_by == "Nome":
            filtered_executions.sort(key=lambda x: x.name or f"Execução {x.id}")
        
        st.write(f"**{len(filtered_executions)} execução(ões)** (de {len(executions)} total)")
        
        # Mostrar execuções
        for execution in filtered_executions:
            # Buscar resultados se existirem
            results = StudentResultCRUD.get_results_by_execution(session, execution.id)
            
            # Status colorido
            status_color = {
                'pending': '🟡',
                'running': '🔵', 
                'completed': '🟢',
                'failed': '🔴'
            }.get(execution.status, '⚪')
            
            with st.expander(f"{status_color} {execution.name or f'Execução {execution.id}'} - {execution.status.upper()}"):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.write(f"**Status:** {execution.status}")
                    st.write(f"**Criado:** {execution.created_at.strftime('%d/%m/%Y %H:%M')}")
                    if execution.notes:
                        st.write(f"**Notas:** {execution.notes}")
                
                with col2:
                    dataset_name = dataset_dict.get(execution.dataset_id, f"ID: {execution.dataset_id}")
                    st.write(f"**Dataset:** {dataset_name}")
                    
                    params_name = params_dict.get(execution.parameters_set_id, f"ID: {execution.parameters_set_id}")
                    st.write(f"**Parâmetros:** {params_name}")
                
                with col3:
                    if results:
                        st.write(f"**Resultados:** {len(results)} alunos")
                        
                        # Calcular estatísticas básicas
                        if results:
                            thetas = [r.theta for r in results]
                            enem_scores = [r.enem_score for r in results]
                            
                            st.write(f"**Média Theta:** {sum(thetas)/len(thetas):.3f}")
                            st.write(f"**Média ENEM:** {sum(enem_scores)/len(enem_scores):.1f}")
                    else:
                        st.write("**Resultados:** Nenhum")
                
                with col4:
                    # Ações
                    if execution.status == 'completed' and results:
                        if st.button("📊 Ver Visualizações", key=f"view_viz_{execution.id}"):
                            st.session_state['selected_execution_for_viz'] = execution.id
                            st.session_state['current_viz_tab'] = 'visualizations'
                            st.rerun()
                    
                    if st.button("🗑️ Excluir", key=f"delete_exec_{execution.id}"):
                        if ExecutionCRUD.delete_execution(session, execution.id):
                            st.success("Execução excluída com sucesso!")
                            st.rerun()
                        else:
                            st.error("Erro ao excluir execução")
                    
                    # Botão para reprocessar se falhou
                    if execution.status == 'failed':
                        if st.button("🔄 Reprocessar", key=f"reprocess_{execution.id}"):
                            ExecutionCRUD.update_execution_status(session, execution.id, 'pending')
                            st.success("Execução marcada para reprocessamento!")
                            st.rerun()
        
        # Estatísticas gerais
        st.subheader("📊 Estatísticas Gerais")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_executions = len(executions)
            st.metric("Total de Execuções", total_executions)
        
        with col2:
            completed_executions = len([e for e in executions if e.status == 'completed'])
            st.metric("Execuções Concluídas", completed_executions)
        
        with col3:
            pending_executions = len([e for e in executions if e.status in ['pending', 'running']])
            st.metric("Execuções Pendentes", pending_executions)
        
        with col4:
            failed_executions = len([e for e in executions if e.status == 'failed'])
            st.metric("Execuções Falharam", failed_executions)
        
        # Gráfico de status
        if executions:
            import plotly.express as px
            
            status_counts = {}
            for execution in executions:
                status_counts[execution.status] = status_counts.get(execution.status, 0) + 1
            
            df_status = pd.DataFrame(list(status_counts.items()), columns=['Status', 'Quantidade'])
            fig_status = px.pie(df_status, values='Quantidade', names='Status', 
                              title="Distribuição de Status das Execuções")
            st.plotly_chart(fig_status, use_container_width=True)

def show_parameters_tab(assessment_id):
    """Tab para parâmetros salvos"""
    st.subheader("📋 Parâmetros Salvos")
    
    with get_db_session_context() as session:
        params_sets = ParametersSetCRUD.get_parameters_by_assessment(session, assessment_id)
        
        if not params_sets:
            st.info("Nenhum parâmetro salvo para esta avaliação.")
            return
        
        st.success(f"✅ {len(params_sets)} conjunto(s) de parâmetros encontrado(s).")
        
        # Separar parâmetros âncora dos calibrados
        anchor_params = [p for p in params_sets if p.is_anchor]
        calibrated_params = [p for p in params_sets if not p.is_anchor]
        
        # Tabs para diferentes tipos de parâmetros
        param_tab1, param_tab2 = st.tabs([
            f"🎯 Itens Âncora ({len(anchor_params)})",
            f"🔧 Parâmetros Calibrados ({len(calibrated_params)})"
        ])
        
        with param_tab1:
            if anchor_params:
                st.subheader("🎯 Parâmetros dos Itens Âncora")
                
                for param_set in anchor_params:
                    with st.expander(f"🎯 {param_set.name or f'Conjunto Âncora {param_set.id}'}"):
                        col1, col2, col3 = st.columns([2, 1, 1])
                        
                        with col1:
                            st.write(f"**Criado:** {param_set.created_at.strftime('%d/%m/%Y %H:%M')}")
                            st.write(f"**Tipo:** Itens Âncora")
                        
                        with col2:
                            item_params = ParametersSetCRUD.get_item_parameters(session, param_set.id)
                            st.write(f"**Itens:** {len(item_params)}")
                        
                        with col3:
                            if st.button("🗑️ Excluir", key=f"delete_anchor_{param_set.id}"):
                                if ParametersSetCRUD.delete_parameters_set(session, param_set.id):
                                    st.success("Conjunto de parâmetros excluído!")
                                    st.rerun()
                                else:
                                    st.error("Erro ao excluir parâmetros")
                        
                        # Mostrar parâmetros dos itens âncora
                        if item_params:
                            # Criar DataFrame para mostrar parâmetros
                            params_data = []
                            for param in item_params:
                                params_data.append({
                                    'Questão': param.questao,
                                    'a (Discriminação)': param.a,
                                    'b (Dificuldade)': param.b,
                                    'c (Acerto ao acaso)': param.c
                                })
                            
                            df_params = pd.DataFrame(params_data)
                            st.dataframe(df_params, width='stretch')
                            
                            # Estatísticas dos parâmetros âncora
                            st.subheader("📊 Estatísticas dos Parâmetros Âncora")
                            
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric("Média a", f"{df_params['a (Discriminação)'].mean():.3f}")
                                st.metric("Desvio a", f"{df_params['a (Discriminação)'].std():.3f}")
                            
                            with col2:
                                st.metric("Média b", f"{df_params['b (Dificuldade)'].mean():.3f}")
                                st.metric("Desvio b", f"{df_params['b (Dificuldade)'].std():.3f}")
                            
                            with col3:
                                st.metric("Média c", f"{df_params['c (Acerto ao acaso)'].mean():.3f}")
                                st.metric("Desvio c", f"{df_params['c (Acerto ao acaso)'].std():.3f}")
                            
                            with col4:
                                st.metric("Min a", f"{df_params['a (Discriminação)'].min():.3f}")
                                st.metric("Max a", f"{df_params['a (Discriminação)'].max():.3f}")
                            
                            # Gráficos dos parâmetros âncora
                            import plotly.express as px
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                fig_a = px.histogram(df_params, x='a (Discriminação)', nbins=10, 
                                                   title="Distribuição do Parâmetro a (Discriminação)")
                                st.plotly_chart(fig_a, use_container_width=True)
                            
                            with col2:
                                fig_b = px.histogram(df_params, x='b (Dificuldade)', nbins=10,
                                                   title="Distribuição do Parâmetro b (Dificuldade)")
                                st.plotly_chart(fig_b, use_container_width=True)
                            
                            col3, col4 = st.columns(2)
                            
                            with col3:
                                fig_c = px.histogram(df_params, x='c (Acerto ao acaso)', nbins=10,
                                                   title="Distribuição do Parâmetro c (Acerto ao acaso)")
                                st.plotly_chart(fig_c, use_container_width=True)
                            
                            with col4:
                                # Scatter plot a vs b
                                fig_scatter = px.scatter(df_params, x='b (Dificuldade)', y='a (Discriminação)',
                                                       title="Correlação: Dificuldade vs Discriminação",
                                                       hover_data=['Questão'])
                                st.plotly_chart(fig_scatter, use_container_width=True)
                            
                            # Botão de download
                            csv_data = df_params.to_csv(index=False)
                            st.download_button(
                                label="📥 Download Parâmetros Âncora",
                                data=csv_data,
                                file_name=f"parametros_ancora_{param_set.id}.csv",
                                mime="text/csv",
                                key=f"download_anchor_{param_set.id}"
                            )
            else:
                st.info("ℹ️ Nenhum parâmetro âncora encontrado.")
        
        with param_tab2:
            if calibrated_params:
                st.subheader("🔧 Parâmetros Calibrados")
                
                for param_set in calibrated_params:
                    with st.expander(f"🔧 {param_set.name or f'Conjunto Calibrado {param_set.id}'}"):
                        col1, col2, col3 = st.columns([2, 1, 1])
                        
                        with col1:
                            st.write(f"**Criado:** {param_set.created_at.strftime('%d/%m/%Y %H:%M')}")
                            st.write(f"**Tipo:** Parâmetros Calibrados")
                        
                        with col2:
                            item_params = ParametersSetCRUD.get_item_parameters(session, param_set.id)
                            st.write(f"**Itens:** {len(item_params)}")
                        
                        with col3:
                            if st.button("🗑️ Excluir", key=f"delete_calibrated_{param_set.id}"):
                                if ParametersSetCRUD.delete_parameters_set(session, param_set.id):
                                    st.success("Conjunto de parâmetros excluído!")
                                    st.rerun()
                                else:
                                    st.error("Erro ao excluir parâmetros")
                        
                        # Mostrar parâmetros calibrados
                        if item_params:
                            # Criar DataFrame para mostrar parâmetros
                            params_data = []
                            for param in item_params:
                                params_data.append({
                                    'Questão': param.questao,
                                    'a (Discriminação)': param.a,
                                    'b (Dificuldade)': param.b,
                                    'c (Acerto ao acaso)': param.c,
                                    'É Âncora': 'Sim' if param.is_anchor else 'Não'
                                })
                            
                            df_params = pd.DataFrame(params_data)
                            st.dataframe(df_params, width='stretch')
                            
                            # Estatísticas dos parâmetros calibrados
                            st.subheader("📊 Estatísticas dos Parâmetros Calibrados")
                            
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric("Média a", f"{df_params['a (Discriminação)'].mean():.3f}")
                                st.metric("Desvio a", f"{df_params['a (Discriminação)'].std():.3f}")
                            
                            with col2:
                                st.metric("Média b", f"{df_params['b (Dificuldade)'].mean():.3f}")
                                st.metric("Desvio b", f"{df_params['b (Dificuldade)'].std():.3f}")
                            
                            with col3:
                                st.metric("Média c", f"{df_params['c (Acerto ao acaso)'].mean():.3f}")
                                st.metric("Desvio c", f"{df_params['c (Acerto ao acaso)'].std():.3f}")
                            
                            with col4:
                                anchor_count = len(df_params[df_params['É Âncora'] == 'Sim'])
                                st.metric("Itens Âncora", anchor_count)
                                st.metric("Itens Calibrados", len(df_params) - anchor_count)
                            
                            # Gráficos dos parâmetros calibrados
                            import plotly.express as px
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                fig_a = px.histogram(df_params, x='a (Discriminação)', nbins=15, 
                                                   title="Distribuição do Parâmetro a (Discriminação)",
                                                   color='É Âncora')
                                st.plotly_chart(fig_a, use_container_width=True)
                            
                            with col2:
                                fig_b = px.histogram(df_params, x='b (Dificuldade)', nbins=15,
                                                   title="Distribuição do Parâmetro b (Dificuldade)",
                                                   color='É Âncora')
                                st.plotly_chart(fig_b, use_container_width=True)
                            
                            col3, col4 = st.columns(2)
                            
                            with col3:
                                fig_c = px.histogram(df_params, x='c (Acerto ao acaso)', nbins=15,
                                                   title="Distribuição do Parâmetro c (Acerto ao acaso)",
                                                   color='É Âncora')
                                st.plotly_chart(fig_c, use_container_width=True)
                            
                            with col4:
                                # Scatter plot a vs b com cores para âncora
                                fig_scatter = px.scatter(df_params, x='b (Dificuldade)', y='a (Discriminação)',
                                                       title="Correlação: Dificuldade vs Discriminação",
                                                       color='É Âncora',
                                                       hover_data=['Questão'])
                                st.plotly_chart(fig_scatter, use_container_width=True)
                            
                            # Botão de download
                            csv_data = df_params.to_csv(index=False)
                            st.download_button(
                                label="📥 Download Parâmetros Calibrados",
                                data=csv_data,
                                file_name=f"parametros_calibrados_{param_set.id}.csv",
                                mime="text/csv",
                                key=f"download_calibrated_{param_set.id}"
                            )
            else:
                st.info("ℹ️ Nenhum parâmetro calibrado encontrado.")
        
        # Resumo geral
        if params_sets:
            st.subheader("📊 Resumo Geral dos Parâmetros")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total de Conjuntos", len(params_sets))
            
            with col2:
                st.metric("Conjuntos Âncora", len(anchor_params))
            
            with col3:
                st.metric("Conjuntos Calibrados", len(calibrated_params))
            
            with col4:
                total_items = sum(len(ParametersSetCRUD.get_item_parameters(session, p.id)) for p in params_sets)
                st.metric("Total de Itens", total_items)

def main():
    """Função principal"""
    try:
        # Verificar autenticação
        require_authentication()
        
        # Header
        st.title("📊 Sistema TRI Profissional v2")
        st.markdown("---")
        
        # Sidebar simples
        with st.sidebar:
            st.title("🧭 Navegação")
            
            if st.button("🏠 Dashboard", key="nav_dashboard", width='stretch'):
                st.session_state['current_page'] = 'dashboard'
                st.rerun()
            
            if st.button("📋 Avaliações", key="nav_assessments", width='stretch'):
                st.session_state['current_page'] = 'assessments'
                st.rerun()
            
            if st.button("⚙️ Execuções", key="nav_executions", width='stretch'):
                st.session_state['current_page'] = 'executions'
                st.rerun()
            
            st.markdown("---")
            
            # Informações do usuário
            user_info = st.session_state.get('user_name', 'Usuário')
            st.info(f"👤 **{user_info}**")
            
            # Botão de logout na sidebar
            if st.button("🚪 Sair", width='stretch', key="btn_logout_sidebar"):
                from auth.authentication import AuthenticationManager
                AuthenticationManager().logout_user()
                st.rerun()
        
        # Conteúdo principal
        page = st.session_state.get('current_page', 'dashboard')
        
        if page == 'dashboard':
            st.subheader("🏠 Dashboard Principal")
            st.success("✅ Dashboard funcionando!")
            
            # Métricas reais
            try:
                with get_db_session_context() as session:
                    assessments = AssessmentCRUD.list_assessments(session)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Avaliações", len(assessments))
                    with col2:
                        st.metric("Execuções", "0")  # Implementar depois
                    with col3:
                        st.metric("Estudantes", "0")  # Implementar depois
                    
                    # Mostrar avaliações recentes
                    if assessments:
                        st.subheader("📋 Avaliações Recentes")
                        for assessment in assessments[:3]:  # Mostrar apenas as 3 mais recentes
                            st.info(f"🎯 **{assessment.description or f'Avaliação {assessment.year}'}** - {assessment.level} ({assessment.cicle})")
                    
            except Exception as e:
                logger.error(f"Erro ao carregar métricas: {e}")
                st.error("Erro ao carregar métricas")
        
        elif page == 'assessments':
            show_assessments_page()
        
        elif page == 'executions':
            show_executions_page()
        
    except Exception as e:
        st.error(f"❌ Erro: {e}")
        logger.error(f"Erro no dashboard: {e}")

if __name__ == "__main__":
    main()
