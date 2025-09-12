#!/bin/bash

# Script de inicialização do Sistema TRI Dashboard Profissional v2
echo "🚀 Iniciando Sistema TRI Dashboard Profissional v2..."

set -e

# Detectar Python
if [ -d "venv" ]; then
    # Se existir venv, usar o Python do venv
    source venv/bin/activate
    PY="python"
elif [ -d ".venv" ]; then
    # Se existir .venv, usar o Python do .venv
    source .venv/bin/activate
    PY="python"
else
    if command -v python3 &> /dev/null; then
        PY="python3"
    elif command -v python &> /dev/null; then
        PY="python"
    else
        echo "❌ Python não encontrado. Instale o Python 3.9+ primeiro."
        exit 1
    fi
fi

echo "🐍 Usando Python: $($PY --version)"

# Verificar se o arquivo .env existe
if [ ! -f ".env" ]; then
    echo "⚠️  Arquivo .env não encontrado!"
    echo "📝 Execute primeiro: python setup_env.py"
    echo "   ou crie manualmente o arquivo .env com as configurações do PostgreSQL"
    exit 1
fi

# Verificar se as dependências estão instaladas
echo "🔍 Verificando dependências..."
if ! $PY -c "import streamlit, psycopg2, dotenv" 2>/dev/null; then
    echo "📦 Instalando dependências..."
    $PY -m pip install --upgrade pip >/dev/null 2>&1 || true
    if [ -f "requirements.txt" ]; then
        $PY -m pip install -r requirements.txt
    else
        echo "❌ Arquivo requirements.txt não encontrado!"
        exit 1
    fi
fi

# Verificar conexão com PostgreSQL
echo "🗄️  Verificando conexão com PostgreSQL..."
if ! $PY -c "
import os
from dotenv import load_dotenv
load_dotenv()
from db.session_v2 import test_connection
if not test_connection():
    print('❌ Erro na conexão com PostgreSQL')
    exit(1)
else:
    print('✅ Conexão com PostgreSQL OK')
" 2>/dev/null; then
    echo "❌ Erro na conexão com PostgreSQL!"
    echo "🔧 Verifique se:"
    echo "   - PostgreSQL está rodando"
    echo "   - As credenciais no arquivo .env estão corretas"
    echo "   - O banco de dados 'tri_system' existe"
    echo ""
    echo "💡 Para configurar, execute: python setup_env.py"
    exit 1
fi

# Verificar se as tabelas existem
echo "📋 Verificando estrutura do banco..."
if ! $PY -c "
from db.session_v2 import get_db_session_context
from db.models_v2 import User
try:
    with get_db_session_context() as session:
        users = session.query(User).first()
    print('✅ Estrutura do banco OK')
except Exception as e:
    print('⚠️  Banco não inicializado. Execute: python init_database.py')
    exit(1)
" 2>/dev/null; then
    echo "⚠️  Banco de dados não inicializado!"
    echo "🔧 Execute primeiro: python init_database.py"
    exit 1
fi

# Criar diretórios necessários
mkdir -p saved_results
mkdir -p logs

# Configurar variáveis de ambiente
export STREAMLIT_SERVER_PORT=8501
export STREAMLIT_SERVER_ADDRESS=localhost

echo ""
echo "✅ Configuração concluída!"
echo "🌐 Dashboard será aberto em: http://localhost:8501"
echo ""
echo "🔐 Credenciais de acesso:"
echo "   👤 Usuário: admin"
echo "   🔑 Senha: admin123"
echo ""
echo "⚠️  IMPORTANTE: Altere a senha padrão após o primeiro login!"
echo ""
echo "⏳ Iniciando dashboard profissional..."

# Executar dashboard v2
$PY -m streamlit run dashboard_v2.py
