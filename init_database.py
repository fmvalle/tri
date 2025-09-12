"""
Script para inicializar o banco de dados PostgreSQL
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.session_v2 import test_connection, create_tables, drop_tables
from db.crud_v2 import UserCRUD
from auth.authentication import AuthenticationManager

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_admin_user():
    """Cria usuário administrador padrão"""
    try:
        from db.session_v2 import get_db_session_context
        
        with get_db_session_context() as session:
            # Verificar se já existe usuário admin
            admin_user = UserCRUD.get_user_by_username(session, "admin")
            
            if admin_user:
                logger.info("Usuário admin já existe")
                return admin_user
            
            # Criar usuário admin
            auth_manager = AuthenticationManager()
            password_hash = auth_manager.hash_password_md5("admin123")
            
            admin_user = UserCRUD.create_user(
                session, 
                name="Administrador",
                username="admin",
                password_hash=password_hash
            )
            
            logger.info(f"Usuário admin criado com sucesso: {admin_user.username}")
            return admin_user
            
    except Exception as e:
        logger.error(f"Erro ao criar usuário admin: {e}")
        return None


def init_database():
    """Inicializa o banco de dados"""
    print("🚀 Inicializando Sistema TRI Profissional...")
    print("=" * 50)
    
    # Testar conexão
    print("1. Testando conexão com PostgreSQL...")
    if not test_connection():
        print("❌ Erro: Não foi possível conectar ao PostgreSQL")
        print("Verifique se:")
        print("- PostgreSQL está rodando")
        print("- As credenciais no arquivo .env estão corretas")
        print("- O banco de dados 'tri_system' existe")
        return False
    
    print("✅ Conexão com PostgreSQL estabelecida")
    
    # Criar tabelas
    print("\n2. Criando tabelas...")
    if not create_tables():
        print("❌ Erro ao criar tabelas")
        return False
    
    print("✅ Tabelas criadas com sucesso")
    
    # Criar usuário admin
    print("\n3. Criando usuário administrador...")
    admin_user = create_admin_user()
    if not admin_user:
        print("❌ Erro ao criar usuário admin")
        return False
    
    print("✅ Usuário admin criado")
    print(f"   Username: admin")
    print(f"   Senha: admin123")
    print("   ⚠️  IMPORTANTE: Altere a senha após o primeiro login!")
    
    print("\n" + "=" * 50)
    print("🎉 Sistema inicializado com sucesso!")
    print("\nPara iniciar o dashboard:")
    print("streamlit run dashboard_v2.py")
    print("\nCredenciais de acesso:")
    print("Username: admin")
    print("Senha: admin123")
    
    return True


def reset_database():
    """Reseta o banco de dados (remove todas as tabelas)"""
    print("⚠️  ATENÇÃO: Esta operação irá remover TODAS as tabelas!")
    confirm = input("Digite 'CONFIRMAR' para continuar: ")
    
    if confirm != "CONFIRMAR":
        print("Operação cancelada.")
        return False
    
    print("🗑️  Removendo tabelas...")
    if drop_tables():
        print("✅ Tabelas removidas com sucesso")
        return True
    else:
        print("❌ Erro ao remover tabelas")
        return False


def main():
    """Função principal"""
    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        reset_database()
    else:
        init_database()


if __name__ == "__main__":
    main()
