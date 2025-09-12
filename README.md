# 🎯 Sistema TRI - Teoria de Resposta ao Item

## 📋 Descrição

Sistema completo e profissional para correção de provas utilizando a **Teoria de Resposta ao Item (TRI)** no modelo de 3 parâmetros (3PL), seguindo os padrões utilizados no ENEM/SAEB.

### ✨ Características Principais

- 🚀 **Interface Unificada**: Menu interativo e dashboard web
- 📊 **Processamento Robusto**: ETL, validação e análise completa
- 📈 **Visualizações Avançadas**: Gráficos interativos e relatórios
- 🔧 **Configurável**: Parâmetros personalizáveis via YAML
- 📝 **Logging Completo**: Rastreamento detalhado de operações
- 🎨 **Dashboard Web**: Interface gráfica moderna com Streamlit
- 🐳 **Containerizado**: Docker para fácil implantação
- 🎯 **Itens Âncora**: Suporte completo para calibração com itens de referência
- 🔄 **Equating de Escalas**: Manutenção de consistência entre aplicações
- 📊 **Calibração Relativa**: Calibração de novos itens usando âncoras como referência
- 🔬 **Métodos de Calibração**: ML (Máxima Verossimilhança) e MLF (Maximum Likelihood with Fences)
- 🛡️ **Fences Adaptativos**: Controle de estimativas extremas baseado no tamanho da amostra

## 🏗️ Arquitetura do Sistema

```
tri_app/
├── 📁 core/                    # Módulos principais
│   ├── tri_engine.py          # Motor TRI (3PL)
│   ├── data_processor.py      # ETL e processamento
│   └── validators.py          # Validação de dados
├── 📁 utils/                   # Utilitários
│   ├── logger.py              # Sistema de logging
│   └── visualizations.py      # Visualizações
├── 📁 config/                  # Configurações
│   └── settings.py            # Configurações centralizadas
├── 📁 data/                    # Dados
│   ├── input/                 # Arquivos de entrada
│   └── output/                # Arquivos de saída
├── 📁 reports/                 # Relatórios gerados
├── 📁 logs/                    # Logs do sistema
├── 📁 scripts/                 # Scripts de automação
├── main.py                    # Interface principal
├── dashboard.py               # Dashboard web
├── config.yaml                # Configurações YAML
├── Dockerfile                 # Container Docker
├── docker-compose.yml         # Orquestração Docker
├── setup.py                   # Script de instalação
├── test_system.py             # Testes automatizados
└── requirements.txt           # Dependências
```

## 🚀 Instalação

### 🐳 **Opção 1: Docker (Recomendado)**

#### Pré-requisitos
- Docker Desktop (macOS/Windows) ou Docker Engine (Linux)
- Docker Compose

#### Instalação Rápida com Docker

```bash
# 1. Clonar o repositório
git clone <seu-repositorio>
cd tri

# 2. Executar inicialização rápida
./scripts/quick-start.sh
```

#### Instalação Manual com Docker

```bash
# 1. Construir a imagem
docker-compose build

# 2. Executar setup inicial
docker-compose run --rm tri-system python setup.py

# 3. Executar testes
docker-compose run --rm tri-system python test_system.py

# 4. Iniciar dashboard
docker-compose up tri-system
```

#### Scripts de Automação

```bash
# Inicialização rápida (recomendado para iniciantes)
./scripts/quick-start.sh

# Gerenciamento do container
./scripts/docker-run.sh dashboard    # Iniciar dashboard
./scripts/docker-run.sh cli          # Iniciar interface CLI
./scripts/docker-run.sh build        # Construir imagem
./scripts/docker-run.sh stop         # Parar containers
./scripts/docker-run.sh logs         # Ver logs
./scripts/docker-run.sh test         # Executar testes

# Instalar Docker (se necessário)
./scripts/install-docker.sh
```

### 🐍 **Opção 2: Instalação Local**

#### Pré-requisitos
- Python 3.8+
- pip

#### Instalação Local

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Executar setup
python setup.py

# 3. Testar instalação
python test_system.py

# 4. Executar aplicação
python main.py                    # Interface CLI
streamlit run dashboard.py        # Dashboard web

## 🌐 API (FastAPI)

### Iniciar API localmente
```bash
./start_api.sh
# Docs: http://127.0.0.1:8000/docs
```

### Endpoints
- `POST /upload`: Envia CSV de respostas e processa TRI opcionalmente com parâmetros. Retorna `execution_id`.
- `GET /executions/{execution_id}/results`: Retorna resultados persistidos.
- `POST /calibrate`: Envia CSV e retorna `execution_id` da calibração com parâmetros persistidos.

### Persistência em Banco
- Banco padrão: SQLite (`tri.db`). Configure `DATABASE_URL` para Postgres/MySQL em `config/settings.py`.
- ORM: SQLAlchemy 2.0. Modelos em `db/models.py`. CRUD em `db/crud.py`.

```

## 📖 Como Usar

### 🐳 **Com Docker**

#### Dashboard Web
```bash
# Iniciar dashboard
./scripts/docker-run.sh dashboard

# Acessar no navegador
# http://localhost:8501
```

#### Interface de Linha de Comando
```bash
# Iniciar CLI
./scripts/docker-run.sh cli

# Ou executar comandos específicos
docker-compose run --rm tri-system python main.py --input data/input/respostas.csv
```

#### Processamento em Lote
```bash
# Processar múltiplos arquivos
docker-compose run --rm tri-system python main.py --batch data/input/
```

### 🐍 **Localmente**

#### Menu Interativo
```bash
python main.py
```

#### Linha de Comando Direta
```bash
# Processar arquivo CSV
python main.py --input respostas.csv --params parametros.csv --output resultados.csv

# Processar em lote
python main.py --batch /caminho/para/arquivos/

# Validar arquivo
python main.py --validate arquivo.csv

# Gerar relatório
python main.py --report resultados.csv
```

#### Dashboard Web
```bash
streamlit run dashboard.py
# Acesse: http://localhost:8501
```

## 📁 Formatos de Arquivo Suportados

### 📄 Arquivo de Respostas (CSV)

```csv
CodPessoa;Questao;RespostaAluno;Gabarito
12345;1;A;A
12345;2;B;B
12345;3;C;A
```

**Colunas obrigatórias:**
- `CodPessoa`: Identificador único do aluno
- `Questao`: Número da questão
- `RespostaAluno`: Resposta marcada pelo aluno
- `Gabarito`: Resposta correta

### 📊 Arquivo Excel (Cartão de Resposta)

Formato específico com abas:
- **Datos**: Respostas dos alunos
- **Matriz**: Gabarito dos itens

### 📋 Arquivo de Parâmetros (Opcional)

```csv
Questao,a,b,c
1,1.0,0.0,0.2
2,1.5,-0.5,0.15
3,2.0,1.0,0.1
```

**Colunas:**
- `Questao`: Número da questão
- `a`: Parâmetro de discriminação
- `b`: Parâmetro de dificuldade
- `c`: Parâmetro de acerto casual

## ⚙️ Configurações

### Arquivo YAML (`config.yaml`)

```yaml
# Configurações TRI
tri:
  default_a: 1.0          # Discriminação padrão
  default_b: 0.0          # Dificuldade padrão
  default_c: 0.2          # Acerto casual padrão
  theta_bounds: [-4, 4]   # Limites para theta
  enem_base: 500          # Nota base ENEM
  enem_scale: 100         # Escala ENEM

# Configurações de validação
validation:
  min_students: 10
  max_students: 100000
  min_items: 5
  max_items: 100
```

## 📊 Funcionalidades

### 🔧 Processamento TRI

- **Modelo 3PL**: `P(θ) = c + (1-c)/(1 + e^(-1.7*a*(θ-b)))`
- **Estimação de Theta**: Otimização por máxima verossimilhança
- **Escala ENEM**: Conversão automática (500 + 100*theta)
- **Parâmetros Customizáveis**: Suporte a parâmetros calibrados
- **Itens Âncora**: Calibração de novos itens usando itens de referência pré-calibrados

### 🔬 **Métodos de Calibração**

#### **ML - Máxima Verossimilhança**
- Método clássico de estimação de parâmetros
- Ideal para amostras grandes (>500 respondentes)
- Estimativas não-viesadas para dados bem comportados
- Pode produzir estimativas extremas em amostras pequenas

#### **MLF - Maximum Likelihood with Fences**
- Extensão do ML com restrições adaptativas
- Fences baseados no tamanho da amostra e padrões de resposta
- Ideal para amostras pequenas (<100 respondentes)
- Estimativas mais estáveis e interpretáveis
- Controle de estimativas extremas problemáticas

**Recomendação**: Use MLF como método padrão, reservando ML para casos específicos com amostras grandes.

### 🎯 **Sistema de Itens Âncora**

O sistema suporta o uso de **itens âncora** para calibração de novos itens, garantindo consistência entre diferentes aplicações da prova.

#### **Como Funciona:**

1. **Itens Âncora**: Questões com parâmetros já calibrados e validados
2. **Calibração Relativa**: Novos itens são calibrados em relação aos âncoras
3. **Equating**: Mantém a escala consistente entre diferentes aplicações
4. **Qualidade**: Validação automática dos parâmetros calibrados

#### **Formato dos Itens Âncora:**

```csv
Questao,a,b,c
1,1.23614,3.66465,0.19831
5,0.93375,2.50839,0.21717
9,1.73057,-1.06602,0.16058
```

#### **Uso no Dashboard:**

1. **Upload de Âncoras**: Selecione "Arquivo de Âncoras (CSV)" como fonte
2. **Calibração Automática**: O sistema usa os âncoras para calibrar novos itens
3. **Validação**: Verificação automática da qualidade dos parâmetros
4. **Resultados**: Parâmetros calibrados com indicação de tipo (âncora vs. calibrado)

#### **Vantagens:**

- ✅ **Consistência**: Mesma escala entre aplicações
- ✅ **Qualidade**: Validação baseada em itens conhecidos
- ✅ **Eficiência**: Menos itens precisam ser calibrados
- ✅ **Padrão ENEM**: Segue metodologia oficial

### 🔄 **Equating de Escalas**

Sistema profissional para manter a consistência de escalas entre diferentes aplicações de testes.

#### **Funcionalidades:**

1. **Equating entre Duas Aplicações**: Alinhamento de escalas usando âncoras comuns
2. **Equating Múltiplas Aplicações**: Alinhamento de várias aplicações com uma referência
3. **Recomendação de Âncoras**: Sugestão automática dos melhores itens para serem âncoras
4. **Validação de Qualidade**: Métricas para verificar a qualidade do equating

#### **Métodos Implementados:**

- **Equating de Âncoras**: Usa itens comuns entre aplicações
- **Transformação Linear**: Aplica transformações para alinhar escalas
- **Validação Cruzada**: Verifica a estabilidade das transformações
- **Métricas de Qualidade**: R², erro padrão, correlações

#### **Interface no Dashboard:**

- **Aba "Equating de Escalas"**: Acesso direto às funcionalidades
- **Upload de Arquivos**: Suporte a múltiplos formatos
- **Visualizações**: Gráficos e métricas de qualidade
- **Download de Resultados**: Parâmetros transformados em CSV

### 📈 Visualizações

- **Distribuições**: Histogramas e boxplots
- **Correlações**: Scatter plots interativos
- **Parâmetros dos Itens**: Análise detalhada
- **Relatórios HTML**: Relatórios completos e interativos

### 🔍 Validação

- **Dados de Entrada**: Verificação de integridade
- **Parâmetros**: Validação de valores
- **Resultados**: Consistência e limites
- **Qualidade**: Métricas de completude

### 📋 Relatórios

- **Estatísticas Descritivas**: Médias, medianas, percentis
- **Análise de Qualidade**: Completude e distribuições
- **Exportação**: CSV, Excel, JSON, HTML
- **Gráficos**: PNG, PDF, HTML interativo

## 🐳 Docker

### Estrutura do Container

```
Container TRI System
├── 📁 /app/                    # Aplicação
│   ├── core/                  # Módulos principais
│   ├── utils/                 # Utilitários
│   ├── config/                # Configurações
│   ├── main.py               # Interface principal
│   └── dashboard.py          # Dashboard web
├── 📁 /app/data/              # Dados (volumes)
│   ├── input/                # Arquivos de entrada
│   └── output/               # Resultados
├── 📁 /app/reports/           # Relatórios (volume)
└── 📁 /app/logs/              # Logs (volume)
```

### Volumes Docker

- `./data/input` → `/app/data/input` - Arquivos de entrada
- `./data/output` → `/app/data/output` - Resultados processados
- `./reports` → `/app/reports` - Relatórios gerados
- `./logs` → `/app/logs` - Logs do sistema
- `./config.yaml` → `/app/config.yaml` - Configurações

### Comandos Docker Úteis

```bash
# Construir imagem
docker-compose build

# Iniciar dashboard
docker-compose up tri-system

# Executar CLI
docker-compose run --rm tri-system python main.py

# Executar testes
docker-compose run --rm tri-system python test_system.py

# Ver logs
docker-compose logs -f tri-system

# Parar containers
docker-compose down

# Reconstruir imagem
docker-compose build --no-cache

# Executar com arquivo específico
docker-compose run --rm tri-system python main.py --input data/input/meu_arquivo.csv
```

## 🎯 Exemplos de Uso

### Exemplo 1: Processamento Básico com Docker

```bash
# 1. Colocar arquivo de respostas
cp meu_arquivo.csv data/input/

# 2. Iniciar dashboard
./scripts/docker-run.sh dashboard

# 3. Acessar http://localhost:8501
# 4. Fazer upload e processar
```

### Exemplo 2: Processamento em Lote

```bash
# 1. Colocar múltiplos arquivos
cp *.csv data/input/

# 2. Processar em lote
docker-compose run --rm tri-system python main.py --batch data/input/

# 3. Verificar resultados
ls data/output/
```

### Exemplo 3: Interface CLI

```bash
# 1. Iniciar CLI
./scripts/docker-run.sh cli

# 2. Seguir menu interativo
# 3. Selecionar arquivos e opções
```

## 🔧 Configuração Avançada

### Logging

```python
from utils.logger import get_logger

logger = get_logger("meu_modulo")
logger.info("Mensagem de informação")
logger.error("Mensagem de erro")
```

### Visualizações Customizadas

```python
from utils.visualizations import TRIVisualizer

visualizer = TRIVisualizer()

# Gráfico personalizado
visualizer.plot_theta_distribution(results_df, "meu_grafico.png")

# Relatório completo
visualizer.create_comprehensive_report(results_df, input_df, params_df)
```

## 📈 Modelo TRI

### Fórmula 3PL

```
P(θ) = c + (1-c)/(1 + e^(-1.7*a*(θ-b)))
```

Onde:
- **θ (theta)**: Proficiência do aluno
- **a**: Parâmetro de discriminação
- **b**: Parâmetro de dificuldade
- **c**: Parâmetro de acerto casual
- **1.7**: Constante de escala

### Estimação de Theta

- **Método**: Máxima Verossimilhança
- **Otimização**: Algoritmo bounded
- **Limites**: [-4, 4]
- **Pontos Iniciais**: Múltiplos para evitar mínimos locais

### Escala ENEM

```
Nota ENEM = 500 + 100 × θ
```

## 🐛 Solução de Problemas

### Problemas com Docker

#### Docker não está rodando
```bash
# macOS/Windows
# Inicie o Docker Desktop

# Linux
sudo systemctl start docker
sudo systemctl enable docker
```

#### Porta 8501 ocupada
```bash
# Parar containers
docker-compose down

# Verificar portas
lsof -i :8501

# Usar porta diferente
docker-compose up -p 8502:8501 tri-system
```

#### Problemas de permissão
```bash
# Dar permissão aos scripts
chmod +x scripts/*.sh

# Verificar permissões dos diretórios
ls -la data/
```

### Erros Comuns

1. **Arquivo não encontrado**
   - Verifique se o arquivo está em `data/input/`
   - Confirme a extensão (.csv, .xlsx)

2. **Colunas obrigatórias ausentes**
   - Verifique se o arquivo tem as colunas: CodPessoa, Questao, RespostaAluno, Gabarito
   - Confirme o separador (; para CSV)

3. **Erro na estimação de theta**
   - Verifique se há respostas válidas
   - Confirme os parâmetros dos itens

4. **Problemas de memória**
   - Reduza o número de estudantes processados por vez
   - Use processamento em lote

### Logs

Os logs são salvos em `logs/tri_system.log` com rotação automática.

```bash
# Ver logs em tempo real
docker-compose logs -f tri-system

# Ver logs locais
tail -f logs/tri_system.log
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 📞 Suporte

Para suporte e dúvidas:

- 📧 Email: suporte@tri-system.com
- 📖 Documentação: [Wiki do Projeto](https://github.com/seu-usuario/tri-system/wiki)
- 🐛 Issues: [GitHub Issues](https://github.com/seu-usuario/tri-system/issues)

## 🔄 Changelog

### v2.0.0 (2024)
- ✨ Interface unificada com menu interativo
- 🌐 Dashboard web com Streamlit
- 🔧 Sistema de configuração YAML
- 📊 Visualizações avançadas com Plotly
- 📝 Logging robusto com rotação
- 🔍 Validação completa de dados
- 📋 Relatórios HTML interativos
- ⚡ Processamento em lote
- 🎨 Interface moderna e responsiva
- 🐳 **Containerização Docker completa**
- 📜 Scripts de automação
- 🚀 Inicialização rápida

### v1.0.0 (2023)
- 🎯 Implementação básica do modelo TRI 3PL
- 📄 Suporte a arquivos CSV
- 📊 Gráficos básicos com matplotlib
- ⚙️ Parâmetros padrão

---

**Desenvolvido com ❤️ para a comunidade educacional**
