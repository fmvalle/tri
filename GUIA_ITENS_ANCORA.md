# 🎯 Guia Prático - Itens Âncora no Sistema TRI

## 🆕 **Atualizações v3.0**

### **Melhorias Implementadas:**
- ✅ **Algoritmo de calibração otimizado**: Problema "theta travado" corrigido
- ✅ **Escala theta expandida**: De (-4,4) para (-5,5) - 5 desvios padrão
- ✅ **Conversão ENEM corrigida**: Sem limite máximo, apenas mínimo 0
- ✅ **Interface reorganizada**: Sub-abas no Processamento TRI
- ✅ **Percentual de acertos**: Nova coluna nos resultados
- ✅ **Estimativa robusta de theta**: Baseada na proporção observada
- ✅ **Múltiplos pontos iniciais**: Evita mínimos locais na otimização

## 📋 O que são Itens Âncora?

**Itens âncora** são questões que já foram calibradas e validadas em aplicações anteriores, servindo como referência para calibrar novos itens e manter a consistência da escala entre diferentes aplicações de um teste.

### **Por que usar Itens Âncora?**

- ✅ **Consistência**: Mantém a mesma escala entre aplicações
- ✅ **Qualidade**: Valida novos itens usando referências conhecidas
- ✅ **Eficiência**: Reduz o número de itens a serem calibrados
- ✅ **Padrão**: Segue metodologia aceita internacionalmente (ENEM/SAEB)

## 🔧 Como Implementar no Sistema

### **1. Preparar Arquivo de Itens Âncora**

#### **Formato CSV:**
```csv
Questao,a,b,c
1,1.23614,3.66465,0.19831
5,0.93375,2.50839,0.21717
9,1.73057,-1.06602,0.16058
14,7.5943,0.41937,0.17211
20,1.83324,-0.62632,0.12133
```

#### **Colunas Obrigatórias:**
- **Questao**: Número da questão (deve corresponder ao arquivo de respostas)
- **a**: Parâmetro de discriminação (deve ser > 0)
- **b**: Parâmetro de dificuldade (recomendado entre -3 e +3)
- **c**: Parâmetro de acerto casual (recomendado ≤ 0.25)

### **2. Critérios de Qualidade para Âncoras**

#### **Quantidade Mínima:**
- **Mínimo**: 5 itens âncora por domínio
- **Recomendado**: 10-15 itens âncora
- **Ideal**: 20% do total de itens

#### **Distribuição de Dificuldade:**
- **Fácil**: 2-3 itens (b < -1.0)
- **Médio**: 4-6 itens (-1.0 ≤ b ≤ 1.0)
- **Difícil**: 2-3 itens (b > 1.0)

#### **Qualidade dos Parâmetros:**
- **a ≥ 0.5**: Discriminação adequada
- **0.1 ≤ c ≤ 0.25**: Acerto casual aceitável
- **Estabilidade**: Parâmetros bem estimados

### **3. Uso no Dashboard**

#### **Passo a Passo:**

1. **Acessar Dashboard**: `streamlit run dashboard.py`

2. **Selecionar Fonte**: Escolher "Arquivo de Âncoras (CSV)"

3. **Upload de Âncoras**: Fazer upload do arquivo CSV de âncoras

4. **Upload de Respostas**: Fazer upload do arquivo de respostas dos alunos

5. **Calibração**: O sistema automaticamente:
   - Identifica itens âncora
   - Calibra novos itens usando os âncoras como referência
   - Valida a qualidade dos parâmetros estimados

6. **Resultados**: Visualizar parâmetros com indicação de tipo (âncora vs. calibrado)

### **4. Exemplo Prático**

#### **Cenário:**
- **Prova**: Matemática 3º ano
- **Total de itens**: 30
- **Itens âncora**: 6 (20% do total)
- **Novos itens**: 24

#### **Arquivo de Âncoras (`ancoras_MT_3ano.csv`):**
```csv
Questao,a,b,c
3,1.45,-0.8,0.15
7,2.1,0.2,0.12
12,1.8,1.1,0.18
18,0.9,-1.2,0.22
25,1.6,0.5,0.14
29,2.3,1.8,0.16
```

#### **Arquivo de Respostas (`respostas_MT_3ano.csv`):**
```csv
CodPessoa;Questao;RespostaAluno;Gabarito
12345;1;A;A
12345;2;B;B
12345;3;C;A
...
```

#### **Processo:**
1. **Upload**: Ambos os arquivos no dashboard
2. **Calibração**: Sistema calibra itens 1,2,4,5,6,8,9,10,11,13,14,15,16,17,19,20,21,22,23,24,26,27,28,30
3. **Validação**: Verifica qualidade dos parâmetros estimados
4. **Resultado**: 30 itens com parâmetros na mesma escala

## 📊 Validação e Qualidade

### **1. Verificação Automática**

O sistema valida automaticamente:

- ✅ **Parâmetros válidos**: a > 0, 0 ≤ c ≤ 1
- ✅ **Limites razoáveis**: -5 ≤ b ≤ 5, a ≤ 10
- ✅ **Consistência**: Parâmetros dentro dos padrões aceitáveis

### **2. Indicadores de Qualidade**

#### **Para Itens Âncora:**
- **Discriminação**: a ≥ 0.5 (preferencialmente a ≥ 1.0)
- **Dificuldade**: Distribuição equilibrada na escala
- **Acerto casual**: c ≤ 0.25

#### **Para Itens Calibrados:**
- **Convergência**: Otimização bem-sucedida
- **Estabilidade**: Parâmetros dentro dos limites esperados
- **Consistência**: Coerência com itens âncora

### **3. Relatórios de Qualidade**

O sistema gera relatórios incluindo:

- 📈 **Distribuição dos parâmetros**
- 🔍 **Análise de outliers**
- 📊 **Comparação com padrões de referência**
- ⚠️ **Alertas de qualidade**

## 🚨 Problemas Comuns e Soluções

### **1. Falha na Calibração**

#### **Sintomas:**
- Parâmetros com valores extremos
- Mensagens de erro na otimização
- Resultados inconsistentes
- **CORRIGIDO v3.0**: Theta "travado" com mesmo valor para todos os itens

#### **Soluções:**
- **Verificar âncoras**: Garantir qualidade dos itens âncora
- **Aumentar âncoras**: Adicionar mais itens de referência
- **Ajustar dados**: Verificar qualidade das respostas
- **v3.0**: Algoritmo otimizado com múltiplos pontos iniciais resolve o problema

### **2. Parâmetros Extremos**

#### **Sintomas:**
- a > 10 (discriminação muito alta)
- b < -5 ou b > 5 (dificuldade extrema) - **v3.0**: Escala expandida permite até ±5
- c > 0.5 (acerto casual muito alto)

#### **Soluções:**
- **Revisar âncoras**: Verificar se os âncoras são adequados
- **Ajustar bounds**: Modificar limites de otimização
- **Validar dados**: Verificar qualidade das respostas

### **3. Inconsistência de Escala**

#### **Sintomas:**
- Parâmetros b muito diferentes entre aplicações
- Theta estimado fora dos limites esperados
- Notas ENEM inconsistentes
- **CORRIGIDO v3.0**: Alunos com 0 acertos recebendo nota > 0

#### **Soluções:**
- **Padronizar âncoras**: Usar mesmos âncoras entre aplicações
- **Verificar calibração**: Recalibrar se necessário
- **Validar processo**: Revisar todo o processo de calibração
- **v3.0**: Escala expandida e conversão ENEM corrigida resolvem inconsistências

### **4. Problemas de Interface**

#### **Sintomas:**
- **CORRIGIDO v3.0**: Erro "StreamlitDuplicateElementId" com botões de download
- Gráficos duplicados na aba Processamento TRI
- Navegação confusa entre diferentes visualizações

#### **Soluções:**
- **v3.0**: Chaves únicas para todos os elementos Streamlit
- **v3.0**: Sub-abas organizadas eliminam redundância
- **v3.0**: Mensagens explicativas melhoram navegação

## 🔬 Configurações Avançadas

### **1. Ajuste de Parâmetros de Otimização**

#### **No arquivo `config/settings.py`:**
```python
TRI_CONFIG = {
    "default_a": 1.0,      # Discriminação padrão
    "default_b": 0.0,      # Dificuldade padrão
    "default_c": 0.2,      # Acerto casual padrão
    "theta_bounds": (-5, 5),  # Limites para theta (5 desvios padrão)
    "enem_base": 500,      # Nota base ENEM
    "enem_scale": 100,     # Escala ENEM
    "constant": 1.7,       # Constante do modelo 3PL
    "max_iterations": 1000,  # Máximo de iterações
    "tolerance": 1e-6      # Tolerância para convergência
}
```

### **2. Bounds de Otimização**

#### **Para parâmetros dos itens:**
```python
# No método _estimate_item_parameters
bounds = [
    (0.1, 5.0),    # a: discriminação
    (-3.0, 3.0),   # b: dificuldade
    (0.0, 0.5)     # c: acerto casual
]
```

### **3. Critérios de Validação**

#### **Personalizar validação:**
```python
def validate_calibration(self, params_df: pd.DataFrame) -> Dict:
    validation = {
        'valid': True,
        'warnings': [],
        'errors': []
    }
    
    # Critérios personalizados
    if (params_df['a'] > 8).any():
        validation['warnings'].append("Alguns parâmetros 'a' são muito altos")
    
    if (params_df['b'] < -5).any() or (params_df['b'] > 5).any():
        validation['warnings'].append("Alguns parâmetros 'b' são extremos")
    
    return validation
```

## 📈 Monitoramento e Manutenção

### **1. Controle de Qualidade**

#### **Métricas a Monitorar:**
- **Taxa de convergência**: % de itens calibrados com sucesso
- **Qualidade dos parâmetros**: Distribuição dos valores
- **Consistência**: Estabilidade entre aplicações
- **Performance**: Tempo de processamento

### **2. Atualização de Âncoras**

#### **Quando Atualizar:**
- **Mudança de currículo**: Novos padrões educacionais
- **Melhoria de qualidade**: Âncoras com melhor discriminação
- **Expansão de domínio**: Novas áreas de conhecimento
- **Validação externa**: Comparação com outros sistemas

#### **Processo de Atualização:**
1. **Avaliar âncoras atuais**: Qualidade e distribuição
2. **Identificar lacunas**: Áreas que precisam de novos âncoras
3. **Selecionar candidatos**: Itens com boa qualidade
4. **Validar**: Comparar com padrões de referência
5. **Implementar**: Substituir ou adicionar âncoras

### **3. Backup e Versionamento**

#### **Estratégias:**
- **Versionar âncoras**: Controle de versão dos arquivos
- **Backup automático**: Cópia de segurança antes de mudanças
- **Documentação**: Registrar mudanças e justificativas
- **Testes**: Validar novas configurações antes de produção

## 🎨 Melhorias na Interface (v3.0)

### **1. Reorganização do Processamento TRI**

#### **Sub-abas Organizadas:**
- **📊 Gráficos Principais**: Histogramas, boxplots e distribuição cumulativa
- **📈 Estatísticas**: Estatísticas descritivas detalhadas e percentis
- **🔗 Correlações**: Análises de correlação entre variáveis
- **📋 Tabela de Dados**: Resultados completos com download

#### **Benefícios:**
- ✅ **Navegação intuitiva**: Conteúdo agrupado logicamente
- ✅ **Redução de redundância**: Eliminação de gráficos duplicados
- ✅ **Melhor organização**: Informações mais acessíveis

### **2. Nova Coluna: Percentual de Acertos**

#### **Cálculo Automático:**
```python
percentual_acertos = round((acertos / num_items) * 100, 1)
```

#### **Benefícios:**
- ✅ **Interpretação fácil**: Percentual mais intuitivo que número absoluto
- ✅ **Comparação direta**: Facilita análise entre diferentes provas
- ✅ **Análise de correlação**: Nova variável para estudos estatísticos

### **3. Escala Theta Expandida**

#### **Mudança de (-4,4) para (-5,5):**
- **Justificativa**: 5 desvios padrão seguindo padrão ENEM
- **Benefício**: Melhor cobertura de casos extremos
- **Resultado**: Alunos com 0 acertos recebem nota próxima de 0

### **4. Conversão ENEM Corrigida**

#### **Sem Limite Máximo:**
- **Antes**: Nota limitada a 1000
- **Agora**: Sem limite máximo, apenas mínimo 0
- **Justificativa**: Distribuição N(500,100) sem truncamento superior

## 🎓 Casos de Uso Educacionais

### **1. Avaliação Continuada**

#### **Cenário:**
- **Escola**: Aplicação trimestral de provas
- **Objetivo**: Acompanhar progresso dos alunos
- **Solução**: Usar mesmos âncoras para manter escala

#### **Benefícios:**
- ✅ **Comparabilidade**: Resultados entre trimestres
- ✅ **Progresso**: Acompanhar evolução individual
- ✅ **Intervenção**: Identificar necessidades específicas

### **2. Avaliação Nacional**

#### **Cenário:**
- **Sistema**: ENEM, SAEB, Prova Brasil
- **Objetivo**: Comparar escolas e regiões
- **Solução**: Itens âncora padronizados nacionalmente

#### **Benefícios:**
- ✅ **Equidade**: Mesma escala para todos
- ✅ **Transparência**: Critérios claros e objetivos
- ✅ **Políticas**: Base para decisões educacionais

### **3. Pesquisa Educacional**

#### **Cenário:**
- **Estudo**: Eficácia de metodologias de ensino
- **Objetivo**: Comparar grupos experimentais
- **Solução**: Testes com itens âncora para controle

#### **Benefícios:**
- ✅ **Validade**: Controle de variáveis externas
- ✅ **Confiabilidade**: Medidas consistentes
- ✅ **Generalização**: Resultados aplicáveis a outros contextos

## 🔍 Troubleshooting Avançado

### **1. Debug de Calibração**

#### **Logs Detalhados:**
```python
import logging

# Configurar logging detalhado
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# No processo de calibração
logger.debug(f"Calibrando item {questao}")
logger.debug(f"Respostas válidas: {np.sum(valid_mask)}")
logger.debug(f"Parâmetros iniciais: {initial_params}")
logger.debug(f"Resultado da otimização: {result}")
```

#### **Verificação de Dados:**
```python
def debug_item_data(self, responses: np.ndarray, questao: int):
    """
    Debug detalhado dos dados de um item
    """
    print(f"=== Debug Item {questao} ===")
    print(f"Total de respostas: {len(responses)}")
    print(f"Respostas válidas: {np.sum(~np.isnan(responses))}")
    print(f"Taxa de acerto: {np.nanmean(responses):.3f}")
    print(f"Desvio padrão: {np.nanstd(responses):.3f}")
    print(f"Valores únicos: {np.unique(responses[~np.isnan(responses)])}")
```

### **2. Análise de Convergência**

#### **Verificar Otimização:**
```python
def analyze_optimization(self, responses: np.ndarray, questao: int):
    """
    Análise detalhada da otimização
    """
    # Testar diferentes pontos iniciais (v3.0 otimizado)
    initial_points = [
        [1.0, 0.0, 0.2],   # Padrão
        [0.8, -0.5, 0.15], # Alternativo 1
        [1.2, 0.5, 0.25],  # Alternativo 2
        [0.6, -1.0, 0.1],  # Alternativo 3
        [1.5, 1.0, 0.3],   # Alternativo 4
    ]
    
    results = []
    for i, initial in enumerate(initial_points):
        try:
            result = minimize(self.objective, initial, method='L-BFGS-B',
                            bounds=[(0.1, 5.0), (-3.0, 3.0), (0.0, 0.5)])
            
            results.append({
                'initial': initial,
                'success': result.success,
                'x': result.x,
                'fun': result.fun,
                'iterations': result.nit
            })
            
        except Exception as e:
            results.append({
                'initial': initial,
                'success': False,
                'error': str(e)
            })
    
    return results
```

### **3. Validação Cruzada**

#### **Teste de Estabilidade:**
```python
def cross_validate_anchors(self, responses_df: pd.DataFrame, 
                          anchor_items: Dict, n_folds: int = 5):
    """
    Validação cruzada dos itens âncora
    """
    from sklearn.model_selection import KFold
    
    kf = KFold(n_splits=n_folds, shuffle=True, random_state=42)
    
    stability_results = []
    
    for fold, (train_idx, test_idx) in enumerate(kf.split(responses_df)):
        # Dividir dados
        train_df = responses_df.iloc[train_idx]
        test_df = responses_df.iloc[test_idx]
        
        # Calibrar com dados de treino
        train_params = self.calibrate_items_3pl(train_df, anchor_items)
        
        # Validar com dados de teste
        test_quality = self.validate_calibration(test_params)
        
        stability_results.append({
            'fold': fold,
            'train_size': len(train_df),
            'test_size': len(test_df),
            'quality': test_quality
        })
    
    return stability_results
```

## 📚 Recursos Adicionais

### **1. Bibliotecas Recomendadas**

#### **Para Análise Avançada:**
```bash
pip install mirtpy          # Calibração TRI avançada
pip install pyirt           # Implementação TRI em Python
pip install irt             # Teoria de resposta ao item
pip install psychometric    # Análise psicométrica
```

#### **Para Visualizações:**
```bash
pip install plotly          # Gráficos interativos
pip install seaborn         # Visualizações estatísticas
pip install matplotlib      # Gráficos básicos
```

### **2. Referências Técnicas**

- **Baker, F. B. (2001)**. *The basics of item response theory*
- **De Ayala, R. J. (2009)**. *The theory and practice of item response theory*
- **Hambleton, R. K. et al. (1991)**. *Fundamentals of item response theory*

### **3. Ferramentas de Validação**

- **R**: Pacotes `mirt`, `ltm`, `irtoys`
- **Python**: Bibliotecas mencionadas acima
- **Software comercial**: BILOG, PARSCALE, MULTILOG

## 🎯 Checklist de Implementação

### **✅ Preparação:**
- [ ] Selecionar itens âncora de qualidade
- [ ] Verificar distribuição de dificuldade
- [ ] Validar parâmetros dos âncoras
- [ ] Preparar arquivo CSV no formato correto

### **✅ Implementação:**
- [ ] Upload de âncoras no dashboard
- [ ] Upload de dados de respostas
- [ ] Executar calibração com âncoras
- [ ] Verificar resultados da calibração

### **✅ Validação:**
- [ ] Verificar qualidade dos parâmetros
- [ ] Analisar distribuição dos resultados
- [ ] Comparar com padrões de referência
- [ ] Documentar processo e resultados

### **✅ Manutenção:**
- [ ] Monitorar qualidade ao longo do tempo
- [ ] Atualizar âncoras quando necessário
- [ ] Manter backup e versionamento
- [ ] Treinar usuários no sistema

---

**Este guia deve ser usado em conjunto com a documentação técnica completa do sistema.**

*Para dúvidas técnicas, consulte `DOCUMENTACAO_TECNICA.md`*
*Para suporte geral, consulte `README.md`*

---

**Última atualização: Janeiro 2025 - v3.0**
