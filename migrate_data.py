"""
Script para migrar dados do SQLite para PostgreSQL
"""

import os
import sys
import pandas as pd
import logging
from datetime import datetime
from dotenv import load_dotenv

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.session import get_db_session as get_sqlite_session
from db.session_v2 import get_db_session_context
from db.crud_v2 import AssessmentCRUD, ParametersSetCRUD, ItemParameter, ExecutionCRUD, StudentResultCRUD
from db.models import ParametersSet as SQLiteParametersSet, Execution as SQLiteExecution, StudentResult as SQLiteStudentResult

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_parameters_sets():
    """Migra conjuntos de parâmetros do SQLite para PostgreSQL"""
    logger.info("Migrando conjuntos de parâmetros...")
    
    try:
        # Buscar dados do SQLite
        with get_sqlite_session() as sqlite_session:
            sqlite_params = sqlite_session.query(SQLiteParametersSet).all()
            
            if not sqlite_params:
                logger.info("Nenhum conjunto de parâmetros encontrado no SQLite")
                return 0
            
            # Migrar para PostgreSQL
            migrated_count = 0
            with get_db_session_context() as pg_session:
                for sqlite_param in sqlite_params:
                    # Verificar se já existe
                    existing = ParametersSetCRUD.get_parameters_set_by_id(pg_session, sqlite_param.id)
                    if existing:
                        logger.info(f"Conjunto de parâmetros {sqlite_param.id} já existe, pulando...")
                        continue
                    
                    # Criar novo conjunto
                    pg_param = ParametersSetCRUD.create_parameters_set(
                        pg_session,
                        name=sqlite_param.name,
                        is_anchor=sqlite_param.is_anchor
                    )
                    
                    # Migrar parâmetros dos itens
                    for item_param in sqlite_param.item_parameters:
                        ParametersSetCRUD.add_item_parameter(
                            pg_session,
                            pg_param.id,
                            item_param.questao,
                            item_param.a,
                            item_param.b,
                            item_param.c,
                            item_param.is_anchor
                        )
                    
                    migrated_count += 1
                    logger.info(f"Migrado conjunto de parâmetros: {sqlite_param.name}")
            
            logger.info(f"Migrados {migrated_count} conjuntos de parâmetros")
            return migrated_count
            
    except Exception as e:
        logger.error(f"Erro ao migrar conjuntos de parâmetros: {e}")
        return 0


def migrate_executions():
    """Migra execuções do SQLite para PostgreSQL"""
    logger.info("Migrando execuções...")
    
    try:
        # Buscar dados do SQLite
        with get_sqlite_session() as sqlite_session:
            sqlite_executions = sqlite_session.query(SQLiteExecution).all()
            
            if not sqlite_executions:
                logger.info("Nenhuma execução encontrada no SQLite")
                return 0
            
            # Criar avaliação padrão para migração
            with get_db_session_context() as pg_session:
                # Verificar se já existe avaliação de migração
                migration_assessment = None
                assessments = AssessmentCRUD.list_assessments(pg_session)
                for assessment in assessments:
                    if "Migração SQLite" in (assessment.description or ""):
                        migration_assessment = assessment
                        break
                
                if not migration_assessment:
                    migration_assessment = AssessmentCRUD.create_assessment(
                        pg_session,
                        year=datetime.now().year,
                        cicle="Migração",
                        level="Migração",
                        description="Migração SQLite - " + datetime.now().strftime("%d/%m/%Y")
                    )
                    logger.info("Criada avaliação de migração")
                
                # Migrar execuções
                migrated_count = 0
                for sqlite_exec in sqlite_executions:
                    # Verificar se já existe
                    existing = ExecutionCRUD.get_execution_by_id(pg_session, sqlite_exec.id)
                    if existing:
                        logger.info(f"Execução {sqlite_exec.id} já existe, pulando...")
                        continue
                    
                    # Criar nova execução
                    pg_exec = ExecutionCRUD.create_execution(
                        pg_session,
                        assessment_id=str(migration_assessment.id),
                        name=f"Migração - {sqlite_exec.id}",
                        notes=f"Migrado do SQLite em {datetime.now().strftime('%d/%m/%Y %H:%M')}"
                    )
                    
                    # Migrar resultados dos estudantes
                    for student_result in sqlite_exec.student_results:
                        StudentResultCRUD.create_student_result(
                            pg_session,
                            pg_exec.id,
                            student_result.cod_pessoa,
                            student_result.theta,
                            student_result.enem_score,
                            student_result.acertos,
                            student_result.total_itens
                        )
                    
                    migrated_count += 1
                    logger.info(f"Migrada execução: {sqlite_exec.id}")
                
                logger.info(f"Migradas {migrated_count} execuções")
                return migrated_count
                
    except Exception as e:
        logger.error(f"Erro ao migrar execuções: {e}")
        return 0


def migrate_saved_results():
    """Migra resultados salvos do diretório saved_results"""
    logger.info("Migrando resultados salvos...")
    
    try:
        saved_results_dir = "saved_results"
        if not os.path.exists(saved_results_dir):
            logger.info("Diretório saved_results não encontrado")
            return 0
        
        # Listar arquivos CSV
        csv_files = [f for f in os.listdir(saved_results_dir) if f.endswith('.csv')]
        
        if not csv_files:
            logger.info("Nenhum arquivo CSV encontrado em saved_results")
            return 0
        
        # Criar avaliação para resultados salvos
        with get_db_session_context() as pg_session:
            # Verificar se já existe avaliação para resultados salvos
            saved_assessment = None
            assessments = AssessmentCRUD.list_assessments(pg_session)
            for assessment in assessments:
                if "Resultados Salvos" in (assessment.description or ""):
                    saved_assessment = assessment
                    break
            
            if not saved_assessment:
                saved_assessment = AssessmentCRUD.create_assessment(
                    pg_session,
                    year=datetime.now().year,
                    cicle="Resultados Salvos",
                    level="Migração",
                    description="Resultados Salvos - " + datetime.now().strftime("%d/%m/%Y")
                )
                logger.info("Criada avaliação para resultados salvos")
            
            migrated_count = 0
            for csv_file in csv_files:
                try:
                    # Ler arquivo CSV
                    df = pd.read_csv(os.path.join(saved_results_dir, csv_file))
                    
                    # Verificar se tem as colunas necessárias
                    required_cols = ['CodPessoa', 'theta', 'enem_score', 'acertos', 'total_itens']
                    if not all(col in df.columns for col in required_cols):
                        logger.warning(f"Arquivo {csv_file} não tem colunas necessárias, pulando...")
                        continue
                    
                    # Criar execução
                    execution = ExecutionCRUD.create_execution(
                        pg_session,
                        assessment_id=str(saved_assessment.id),
                        name=f"Resultado Salvo - {csv_file}",
                        notes=f"Migrado do arquivo {csv_file}"
                    )
                    
                    # Migrar resultados
                    for _, row in df.iterrows():
                        StudentResultCRUD.create_student_result(
                            pg_session,
                            execution.id,
                            str(row['CodPessoa']),
                            float(row['theta']),
                            float(row['enem_score']),
                            int(row['acertos']),
                            int(row['total_itens'])
                        )
                    
                    migrated_count += 1
                    logger.info(f"Migrado arquivo: {csv_file}")
                    
                except Exception as e:
                    logger.error(f"Erro ao migrar arquivo {csv_file}: {e}")
                    continue
            
            logger.info(f"Migrados {migrated_count} arquivos de resultados salvos")
            return migrated_count
                
    except Exception as e:
        logger.error(f"Erro ao migrar resultados salvos: {e}")
        return 0


def main():
    """Função principal de migração"""
    print("🔄 Iniciando migração de dados...")
    print("=" * 50)
    
    # Verificar se SQLite existe
    if not os.path.exists("tri.db"):
        print("❌ Arquivo tri.db não encontrado")
        print("Certifique-se de que o banco SQLite existe no diretório atual")
        return False
    
    # Migrar dados
    total_migrated = 0
    
    print("1. Migrando conjuntos de parâmetros...")
    total_migrated += migrate_parameters_sets()
    
    print("\n2. Migrando execuções...")
    total_migrated += migrate_executions()
    
    print("\n3. Migrando resultados salvos...")
    total_migrated += migrate_saved_results()
    
    print("\n" + "=" * 50)
    print(f"🎉 Migração concluída! {total_migrated} itens migrados.")
    print("\nPara iniciar o novo dashboard:")
    print("streamlit run dashboard_v2.py")
    
    return True


if __name__ == "__main__":
    main()
