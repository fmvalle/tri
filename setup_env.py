"""
Script para configurar variáveis de ambiente do Sistema TRI Profissional
"""

import os
import getpass

def create_env_file():
    """Cria arquivo .env com configurações do PostgreSQL"""
    
    print("🔧 Configuração do Sistema TRI Profissional")
    print("=" * 50)
    
    # Configurações do PostgreSQL
    print("\n📊 Configurações do PostgreSQL:")
    db_host = input("Host do PostgreSQL [localhost]: ").strip() or "localhost"
    db_port = input("Porta do PostgreSQL [5432]: ").strip() or "5432"
    db_name = input("Nome do banco de dados [tri_system]: ").strip() or "tri_system"
    db_user = input("Usuário do PostgreSQL [postgres]: ").strip() or "postgres"
    db_password = getpass.getpass("Senha do PostgreSQL: ")
    
    # Configurações do Streamlit
    print("\n🌐 Configurações do Streamlit:")
    streamlit_port = input("Porta do Streamlit [8501]: ").strip() or "8501"
    streamlit_address = input("Endereço do Streamlit [localhost]: ").strip() or "localhost"
    
    # Gerar chave secreta
    import secrets
    secret_key = secrets.token_hex(32)
    
    # Conteúdo do arquivo .env
    env_content = f"""# Configurações do Sistema TRI - Versão Profissional
# Gerado automaticamente em {os.popen('date').read().strip()}

# Ambiente
ENVIRONMENT=development

# Banco de Dados PostgreSQL
DATABASE_URL=postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}
DB_HOST={db_host}
DB_PORT={db_port}
DB_NAME={db_name}
DB_USER={db_user}
DB_PASSWORD={db_password}

# Chave Secreta para Sessões
SECRET_KEY={secret_key}

# Configurações de Log
LOG_LEVEL=INFO

# Configurações do Dashboard Streamlit
STREAMLIT_SERVER_PORT={streamlit_port}
STREAMLIT_SERVER_ADDRESS={streamlit_address}

# Configurações de Autenticação
SESSION_TIMEOUT=3600
PASSWORD_MIN_LENGTH=6
"""
    
    # Escrever arquivo .env
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print("\n✅ Arquivo .env criado com sucesso!")
        print(f"📁 Localização: {os.path.abspath('.env')}")
        
        # Testar conexão
        print("\n🔍 Testando conexão com PostgreSQL...")
        test_connection(db_host, db_port, db_name, db_user, db_password)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erro ao criar arquivo .env: {e}")
        return False

def test_connection(host, port, db_name, user, password):
    """Testa conexão com PostgreSQL"""
    try:
        import psycopg2
        
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=db_name,
            user=user,
            password=password
        )
        
        conn.close()
        print("✅ Conexão com PostgreSQL estabelecida com sucesso!")
        return True
        
    except ImportError:
        print("⚠️  psycopg2 não instalado. Execute: pip install psycopg2-binary")
        return False
        
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        print("\n🔧 Verifique se:")
        print("- PostgreSQL está rodando")
        print("- As credenciais estão corretas")
        print("- O banco de dados existe")
        print(f"- O usuário tem permissões no banco '{db_name}'")
        return False

def create_database_if_not_exists():
    """Cria banco de dados se não existir"""
    print("\n🗄️  Verificando banco de dados...")
    
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        
        # Conectar ao PostgreSQL (sem especificar banco)
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            database='postgres',  # Banco padrão
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', '')
        )
        
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Verificar se banco existe
        db_name = os.getenv('DB_NAME', 'tri_system')
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        
        if not cursor.fetchone():
            print(f"📝 Criando banco de dados '{db_name}'...")
            cursor.execute(f'CREATE DATABASE "{db_name}"')
            print(f"✅ Banco '{db_name}' criado com sucesso!")
        else:
            print(f"✅ Banco '{db_name}' já existe")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar/criar banco: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 Setup do Sistema TRI Profissional")
    print("Este script irá configurar as variáveis de ambiente necessárias.")
    print()
    
    # Verificar se .env já existe
    if os.path.exists('.env'):
        overwrite = input("Arquivo .env já existe. Deseja sobrescrever? (s/N): ").strip().lower()
        if overwrite not in ['s', 'sim', 'y', 'yes']:
            print("Operação cancelada.")
            return
    
    # Criar arquivo .env
    if create_env_file():
        print("\n🎉 Configuração concluída!")
        print("\n📋 Próximos passos:")
        print("1. python init_database.py  # Inicializar banco de dados")
        print("2. python migrate_data.py   # Migrar dados existentes (opcional)")
        print("3. streamlit run dashboard_v2.py  # Iniciar dashboard")
    else:
        print("\n❌ Configuração falhou. Verifique os erros acima.")

if __name__ == "__main__":
    main()
