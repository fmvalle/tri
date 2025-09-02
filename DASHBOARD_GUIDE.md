# 📊 Guia do Sistema TRI Dashboard

## 🚀 Como Usar

### 1. **Acesso e Login**
- **URL:** http://localhost:8501 (ou porta indicada no terminal)
- **Usuário:** admin
- **Senha:** tri2025

### 2. **Funcionalidades Principais**

#### 🔐 **Sistema de Autenticação**
- Login obrigatório para acessar o sistema
- Botão de logout na barra lateral
- Controle de acesso implementado

#### 📁 **Upload de Dados**
- **Excel (Cartão de Resposta):** Formato padrão com abas "Datos" e "Matriz"
- **CSV:** Formato simples com colunas: CodPessoa, Questao, RespostaAluno, Gabarito
- Validação automática de dados
- Preview dos dados carregados

#### 🔧 **Calibração de Itens**
- Calibração automática de parâmetros TRI (a, b, c)
- Suporte a itens âncora pré-calibrados
- Múltiplos métodos de calibração (3PL, 2PL)
- Validação e visualização dos parâmetros
- Download dos parâmetros calibrados

#### ⚙️ **Processamento TRI**
- Configuração de parâmetros TRI (a, b, c)
- Uso de parâmetros calibrados ou customizados
- Nota base ENEM configurável
- Processamento com barra de progresso
- Resultados em tempo real

#### 📈 **Análise e Visualizações**
- **Distribuições:** Histogramas, boxplots, distribuição cumulativa
- **Correlações:** Scatter plots entre variáveis
- **Parâmetros dos Itens:** Análise detalhada dos parâmetros TRI
- **Análise Comparativa:** Percentis e comparações

#### 📋 **Relatórios**
- **Relatório Completo:** Visão geral com todos os gráficos
- **Resumo Estatístico:** Métricas detalhadas
- **Relatório de Qualidade:** Validação e métricas de qualidade

#### 💾 **Histórico de Resultados**
- **Salvar Resultados:** Salva processamentos com nome personalizado
- **Carregar Resultados:** Recupera análises anteriores
- **Gerenciar Histórico:** Visualizar, carregar e deletar resultados
- **Estatísticas do Histórico:** Resumo de todos os processamentos

### 3. **Como Calibrar Parâmetros dos Itens**

#### 🔧 **Calibração com Itens Âncora**
1. Carregue dados de respostas na aba "📁 Upload de Dados"
2. Vá para a aba "🔧 Calibração de Itens"
3. Marque "Usar itens âncora" e carregue arquivo CSV com parâmetros já calibrados
4. Escolha o método de calibração (3PL recomendado)
5. Clique em "🔧 Calibrar Itens"
6. Visualize os resultados e faça download dos parâmetros

#### 🔧 **Calibração Completa**
1. Carregue dados de respostas na aba "📁 Upload de Dados"
2. Vá para a aba "🔧 Calibração de Itens"
3. Desmarque "Usar itens âncora" para calibrar todos os itens
4. Escolha o método de calibração
5. Clique em "🔧 Calibrar Itens"
6. Os parâmetros calibrados serão usados automaticamente no processamento TRI

### 4. **Como Salvar e Recuperar Resultados**

#### 💾 **Salvando um Resultado**
1. Processe dados TRI na aba "⚙️ Processamento TRI"
2. Após o processamento, aparecerá uma seção "Salvar Resultados"
3. Digite um nome para o resultado (ex: "SFB_3ano_MT_2024")
4. Clique em "💾 Salvar Resultado"

#### 📂 **Acessando o Histórico**
1. Vá para a aba "💾 Histórico"
2. Veja todos os resultados salvos
3. Clique em "🔄 Carregar" para recuperar um resultado
4. Use "🗑️ Deletar" para remover resultados antigos

### 4. **Estrutura de Arquivos**

```
saved_results/
├── metadata.json          # Metadados dos resultados salvos
├── Resultado_20240828_143022.csv
├── SFB_3ano_MT_2024.csv
└── ...
```

### 5. **Configurações Avançadas**

#### 🔧 **Parâmetros TRI (Sidebar)**
- **a (discriminação):** Padrão 1.0
- **b (dificuldade):** Padrão 0.0
- **c (acerto casual):** Padrão 0.2
- **Nota base ENEM:** Padrão 500

#### 📋 **Parâmetros dos Itens**
- **Calibração Automática:** Calibre parâmetros usando dados de respostas
- **Arquivo Customizado:** Carregue arquivo CSV/Excel com parâmetros já calibrados
- **Itens Âncora:** Use alguns itens pré-calibrados como referência
- **Colunas necessárias:** Questao, a, b, c

### 6. **Dicas de Uso**

#### 📊 **Para Melhor Performance**
- Use nomes descritivos ao salvar resultados
- Organize resultados por data ou projeto
- Delete resultados antigos regularmente

#### 🔍 **Para Análises Detalhadas**
- Compare múltiplos resultados no histórico
- Use diferentes parâmetros TRI para comparação
- Exporte relatórios para análise externa

#### 🛡️ **Segurança**
- Em produção, altere as credenciais padrão
- Configure autenticação robusta
- Use HTTPS em ambiente de produção

### 7. **Solução de Problemas**

#### ❌ **Erro de Upload**
- Verifique formato do arquivo Excel
- Confirme presença das abas "Datos" e "Matriz"
- Valide estrutura das colunas

#### 🔄 **Problemas de Carregamento**
- Verifique se o arquivo existe em `saved_results/`
- Confirme permissões de leitura/escrita
- Recarregue a página se necessário

#### 📈 **Gráficos Não Aparecem**
- Aguarde o processamento completo
- Verifique se há dados suficientes
- Recarregue a aba se necessário

### 8. **Comandos Úteis**

```bash
# Executar dashboard
streamlit run dashboard.py

# Parar dashboard
Ctrl+C

# Limpar histórico (manualmente)
rm -rf saved_results/
```

---

## 🎯 **Próximas Funcionalidades**

- [ ] Sistema de usuários múltiplos
- [ ] Backup automático de resultados
- [ ] Exportação para PDF
- [ ] Comparação entre múltiplos resultados
- [ ] Dashboard em tempo real
- [ ] API REST para integração

---

**📞 Suporte:** Para dúvidas ou problemas, consulte a documentação ou entre em contato com a equipe de desenvolvimento.
