"""
Configuração de sessão do banco de dados PostgreSQL
"""

import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from dotenv import load_dotenv
import logging

# Carregar variáveis de ambiente
load_dotenv()

logger = logging.getLogger(__name__)

# Configurações do banco de dados
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://username:password@localhost:5432/tri_system"
)

# Configurações alternativas se DATABASE_URL não estiver definida
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "tri_system")
DB_USER = os.getenv("DB_USER", "username")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")

# Construir URL se não estiver definida
if DATABASE_URL == "postgresql://username:password@localhost:5432/tri_system":
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Configurar engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False  # Mude para True para ver queries SQL
)

# Configurar session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session() -> Session:
    """Retorna uma sessão do banco de dados"""
    return SessionLocal()


@contextmanager
def get_db_session_context():
    """Context manager para sessão do banco de dados"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Erro na sessão do banco: {e}")
        raise
    finally:
        session.close()


def test_connection() -> bool:
    """Testa conexão com o banco de dados"""
    try:
        with get_db_session_context() as session:
            from sqlalchemy import text
            session.execute(text("SELECT 1"))
            logger.info("Conexão com PostgreSQL estabelecida com sucesso")
            return True
    except Exception as e:
        logger.error(f"Erro na conexão com PostgreSQL: {e}")
        return False


def create_tables():
    """Cria todas as tabelas no banco de dados"""
    try:
        from db.models_v2 import Base
        Base.metadata.create_all(bind=engine)
        logger.info("Tabelas criadas com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao criar tabelas: {e}")
        return False


def drop_tables():
    """Remove todas as tabelas do banco de dados"""
    try:
        from db.models_v2 import Base
        Base.metadata.drop_all(bind=engine)
        logger.info("Tabelas removidas com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao remover tabelas: {e}")
        return False
