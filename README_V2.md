# 📊 Sistema TRI Profissional v3.0

## 🎯 Visão Geral

O Sistema TRI Profissional é uma aplicação web completa para análise de dados educacionais utilizando a Teoria de Resposta ao Item (TRI) com modelo de 3 parâmetros (3PL). A versão profissional inclui autenticação, gerenciamento hierárquico de avaliações e execuções, e interface moderna com PostgreSQL.

## ✨ Principais Características

### 🔐 **Autenticação e Segurança**
- Sistema de login com usuários e senhas
- Senhas criptografadas com MD5
- Sessões com timeout configurável
- Controle de acesso por usuário

### 📋 **Gerenciamento Hierárquico**
- **Avaliações**: Nível superior para organizar execuções
- **Execuções**: Processamentos TRI específicos
- **Resultados**: Dados dos estudantes por execução
- **Datasets**: Gerenciamento de arquivos de dados
- **Parâmetros**: Conjuntos de parâmetros calibrados

### 🎨 **Interface Moderna**
- Dashboard analítico com métricas
- Navegação intuitiva com sidebar
- Sub-abas organizadas
- Visualizações interativas com Plotly
- Design responsivo e profissional

### 🗄️ **Banco de Dados PostgreSQL**
- Schema robusto e normalizado
- Relacionamentos bem definidos
- Suporte a UUIDs para chaves primárias
- Migração automática de dados existentes

## 🚀 Instalação e Configuração

### **Pré-requisitos**
- Python 3.9+
- PostgreSQL 12+
- pip (gerenciador de pacotes Python)

### **1. Clone o Repositório**
```bash
git clone <repository-url>
cd tri
```

### **2. Criar Ambiente Virtual**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

### **3. Instalar Dependências**
```bash
pip install -r requirements.txt
```

### **4. Configurar PostgreSQL**
```bash
# Criar banco de dados
createdb tri_system

# Configurar usuário (opcional)
psql -c "CREATE USER tri_user WITH PASSWORD 'tri_password';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE tri_system TO tri_user;"
```

### **5. Configurar Variáveis de Ambiente**
```bash
# Copiar arquivo de exemplo
cp config.env.example .env

# Editar configurações
nano .env
```

**Exemplo de configuração (.env):**
```env
# Banco de Dados PostgreSQL
DATABASE_URL=postgresql://tri_user:tri_password@localhost:5432/tri_system
DB_HOST=localhost
DB_PORT=5432
DB_NAME=tri_system
DB_USER=tri_user
DB_PASSWORD=tri_password

# Chave Secreta (altere em produção)
SECRET_KEY=sua-chave-secreta-aqui

# Configurações do Streamlit
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=localhost
```

### **6. Inicializar Banco de Dados**
```bash
python init_database.py
```

### **7. Migrar Dados Existentes (Opcional)**
```bash
# Se você tem dados no SQLite antigo
python migrate_data.py
```

### **8. Iniciar Aplicação**
```bash
streamlit run dashboard_v2.py
```

## 🔑 Acesso Inicial

Após a inicialização, use as credenciais padrão:

- **Username:** `admin`
- **Senha:** `admin123`

⚠️ **IMPORTANTE:** Altere a senha padrão após o primeiro login!

## 📊 Estrutura do Banco de Dados

### **Tabelas Principais**

#### **`user`**
- Armazena informações dos usuários
- Autenticação com username/password

#### **`assessment`**
- Avaliações (nível hierárquico superior)
- Campos: ano, ciclo, nível, descrição

#### **`executions`**
- Execuções de processamento TRI
- Relacionada a uma avaliação
- Status: pending, running, completed, failed

#### **`student_results`**
- Resultados dos estudantes
- Theta, nota ENEM, acertos, total de itens

#### **`parameters_sets`**
- Conjuntos de parâmetros calibrados
- Suporte a itens âncora

#### **`item_parameters`**
- Parâmetros individuais dos itens (a, b, c)
- Relacionados a um conjunto de parâmetros

#### **`datasets`**
- Metadados de arquivos de dados
- Tipos: CSV, Excel, âncoras

## 🎯 Fluxo de Trabalho

### **1. Criar Avaliação**
- Acesse "📋 Avaliações"
- Clique em "➕ Nova Avaliação"
- Preencha: ano, ciclo, nível, descrição

### **2. Criar Execução**
- Selecione uma avaliação
- Clique em "➕ Nova Execução"
- Defina nome e observações

### **3. Processar Dados**
- Selecione a execução
- Clique em "▶️ Executar"
- Faça upload dos dados
- Execute calibração e processamento TRI

### **4. Analisar Resultados**
- Visualize resultados na execução
- Acesse relatórios e análises
- Exporte dados em CSV

## 🔧 Funcionalidades Técnicas

### **Algoritmo TRI Otimizado**
- Modelo 3PL com constante 1.7
- Múltiplos pontos iniciais para otimização
- Escala theta expandida (-5 a +5)
- Conversão ENEM sem limite máximo

### **Interface Melhorada**
- Sub-abas organizadas
- Percentual de acertos calculado
- IDs únicos para elementos Streamlit
- Mensagens explicativas

### **Sistema de Autenticação**
- Hash MD5 para senhas
- Sessões com timeout
- Controle de acesso por página

## 📈 Dashboard Analítico

### **Métricas Principais**
- Total de avaliações
- Número de execuções
- Estudantes processados
- Taxa de sucesso

### **Visualizações**
- Gráficos de distribuição
- Análises de correlação
- Estatísticas descritivas
- Relatórios personalizados

## 🛠️ Manutenção

### **Backup do Banco**
```bash
pg_dump tri_system > backup_$(date +%Y%m%d).sql
```

### **Restaurar Backup**
```bash
psql tri_system < backup_20250101.sql
```

### **Reset do Sistema**
```bash
python init_database.py reset
```

### **Logs**
- Logs do sistema em `logs/tri_system.log`
- Logs do Streamlit no console
- Logs do PostgreSQL em `/var/log/postgresql/`

## 🔍 Troubleshooting

### **Erro de Conexão PostgreSQL**
- Verifique se PostgreSQL está rodando
- Confirme credenciais no arquivo .env
- Teste conexão: `psql -h localhost -U tri_user -d tri_system`

### **Erro de Autenticação**
- Verifique se usuário admin foi criado
- Execute: `python init_database.py`
- Confirme credenciais padrão

### **Erro de Migração**
- Verifique se arquivo `tri.db` existe
- Confirme permissões de leitura
- Execute migração: `python migrate_data.py`

## 📚 Documentação Adicional

- **Documentação Técnica:** `DOCUMENTACAO_TECNICA.md`
- **Guia de Itens Âncora:** `GUIA_ITENS_ANCORA.md`
- **Guia do Dashboard:** `DASHBOARD_GUIDE.md`

## 🤝 Suporte

Para suporte técnico ou dúvidas:
- Consulte a documentação técnica
- Verifique os logs do sistema
- Entre em contato com a equipe de desenvolvimento

## 📄 Licença

Este projeto é desenvolvido para uso educacional e de pesquisa.

---

**Sistema TRI Profissional v3.0**  
*Desenvolvido para análise de dados educacionais com Teoria de Resposta ao Item*

*Última atualização: Janeiro 2025*
