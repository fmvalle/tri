#!/bin/bash

# Script de inicialização do Sistema TRI Dashboard
echo "🚀 Iniciando Sistema TRI Dashboard..."

set -e

# Detectar Python
if [ -d ".venv" ]; then
    # Se existir venv, usar o Python do venv
    source .venv/bin/activate
    PY="python"
else
    if command -v python3 &> /dev/null; then
        PY="python3"
    elif command -v python &> /dev/null; then
        PY="python"
    else
        echo "❌ Python não encontrado. Instale o Python 3.8+ primeiro."
        exit 1
    fi
fi

# Verificar se o Streamlit está instalado
if ! $PY - << 'PY'
try:
    import streamlit  # noqa: F401
    print('OK')
except Exception:
    pass
PY
then
    echo "📦 Instalando dependências..."
    $PY -m pip install --upgrade pip >/dev/null 2>&1 || true
    if [ -f "requirements.txt" ]; then
        $PY -m pip install -r requirements.txt
    else
        $PY -m pip install streamlit pandas numpy plotly matplotlib seaborn scipy tqdm openpyxl
    fi
fi

# Criar diretório de resultados se não existir
mkdir -p saved_results

# Configurar variáveis de ambiente
export STREAMLIT_SERVER_PORT=8501
export STREAMLIT_SERVER_ADDRESS=localhost

echo "✅ Configuração concluída!"
echo "🌐 Dashboard será aberto em: http://localhost:8501"
echo "👤 Usuário: admin"
echo "🔒 Senha: tri2025"
echo ""
echo "⏳ Iniciando dashboard..."

# Executar dashboard usando o mesmo interpretador
$PY -m streamlit run dashboard.py
