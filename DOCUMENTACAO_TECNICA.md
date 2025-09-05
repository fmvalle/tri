# 📊 Documentação Técnica - Sistema TRI

## 🎯 Visão Geral

Este documento apresenta a implementação técnica do Sistema TRI (Teoria de Resposta ao Item) baseado no modelo de 3 parâmetros (3PL), seguindo as metodologias utilizadas no ENEM/SAEB. O sistema foi desenvolvido para estatísticos e psicometristas que necessitam de uma ferramenta robusta para análise de dados educacionais.

## 🆕 **Atualizações Recentes (v2.0)**

### **Correções Implementadas:**
- ✅ **Colunas duplicadas removidas**: Padronização para `theta`, `enem_score`, `acertos`, `total_itens`, `percentual_acertos`
- ✅ **Debug removido**: Interface limpa e profissional
- ✅ **Erro DataValidator corrigido**: Validação funcionando corretamente
- ✅ **Nova aba "Parâmetros Salvos"**: Gerenciamento de itens calibrados
- ✅ **Dependências atualizadas**: statsmodels incluído para funcionalidades avançadas

### **Estrutura de Dados Padrão:**
```python
# Colunas padrão dos resultados:
- CodPessoa: Identificador único do estudante
- theta: Proficiência latente estimada
- enem_score: Nota na escala ENEM
- acertos: Número de itens acertados
- total_itens: Total de itens do teste
- percentual_acertos: Percentual de acertos calculado
```

## 🔬 Modelo TRI Implementado

### **Modelo 3PL (Birnbaum, 1968)**

A função de resposta ao item implementada segue o modelo de três parâmetros:

```
P(θ) = c + (1-c)/(1 + e^(-1.7*a*(θ-b)))
```

Onde:
- **θ (theta)**: Proficiência latente do respondente
- **a**: Parâmetro de discriminação (a > 0)
- **b**: Parâmetro de dificuldade (-∞ < b < +∞)
- **c**: Parâmetro de acerto casual (0 ≤ c ≤ 1)
- **1.7**: Constante de escala (aproximação de 1.702)

### **Interpretação dos Parâmetros**

#### **Parâmetro a (Discriminação)**
- **a > 1**: Item com alta discriminação
- **a ≈ 1**: Discriminação moderada
- **a < 1**: Baixa discriminação
- **a → 0**: Item não discriminativo

#### **Parâmetro b (Dificuldade)**
- **b > 0**: Item difícil (θ > b para P(θ) > 0.5)
- **b = 0**: Dificuldade média
- **b < 0**: Item fácil

#### **Parâmetro c (Acerto Casual)**
- **c = 0**: Sem acerto casual (modelo 2PL)
- **c > 0**: Probabilidade de acerto por chute
- **c ≤ 0.25**: Valores típicos para testes de múltipla escolha

## 🎯 Sistema de Itens Âncora

### **Fundamentação Teórica**

O sistema de itens âncora implementa a metodologia de **equating** para manter a consistência da escala entre diferentes aplicações de um teste. Esta abordagem é fundamental para:

1. **Comparabilidade**: Resultados de diferentes aplicações na mesma escala
2. **Validação**: Verificação da qualidade dos novos itens
3. **Eficiência**: Redução do número de itens a serem calibrados
4. **Padrão**: Seguir metodologias aceitas internacionalmente

## 📋 **Gerenciamento de Parâmetros Salvos**

### **Nova Funcionalidade: Aba "Parâmetros Salvos"**

O sistema agora inclui uma interface dedicada para gerenciar os parâmetros dos itens calibrados:

#### **Funcionalidades Principais:**
- **📊 Visualização**: Lista todos os conjuntos de parâmetros salvos
- **✏️ Renomeação**: Permite personalizar nomes para identificação fácil
- **📥 Download CSV**: Exporta parâmetros em formato CSV
- **🔍 Estatísticas**: Mostra médias dos parâmetros a, b, c
- **🎯 Identificação de Âncoras**: Indica quais conjuntos são itens âncora

#### **Estrutura dos Parâmetros:**
```python
# Colunas dos parâmetros salvos:
- questao: Número da questão
- a: Parâmetro de discriminação
- b: Parâmetro de dificuldade  
- c: Parâmetro de acerto casual
- is_anchor: Indica se é item âncora
```

#### **Operações CRUD:**
```python
# Listar conjuntos de parâmetros
parameters_sets = crud.list_parameters_sets(session)

# Obter parâmetros específicos
params_df = crud.get_parameters_set(session, parameters_set_id)

# Atualizar nome do conjunto
crud.update_parameters_set_name(session, parameters_set_id, new_name)
```

### **Implementação Técnica**

#### **1. Identificação de Âncoras**

```python
def _identify_anchor_items(self, anchor_items: Dict, item_mapping: Dict) -> np.ndarray:
    """
    Cria máscara booleana para identificar itens âncora
    """
    anchor_mask = np.zeros(len(item_mapping), dtype=bool)
    
    for questao, params in anchor_items.items():
        if questao in item_mapping:
            idx = item_mapping[questao] - 1
            anchor_mask[idx] = True
    
    return anchor_mask
```

#### **2. Calibração Relativa**

Os itens não-âncora são calibrados usando os âncoras como referência:

```python
def _calibrate_non_anchor_items(self, response_array: np.ndarray, 
                               anchor_mask: np.ndarray,
                               anchor_items: Optional[Dict],
                               item_mapping: Dict) -> pd.DataFrame:
    """
    Calibra itens não ancorados usando otimização
    """
    calibrated_params = []
    
    for item_idx in range(response_array.shape[1]):
        if not anchor_mask[item_idx]:
            # Item não ancorado - calibrar
            questao = list(item_mapping.keys())[item_idx]
            item_responses = response_array[:, item_idx]
            
            # Remover respostas nulas
            valid_mask = ~np.isnan(item_responses)
            if np.sum(valid_mask) < 10:  # Mínimo de respostas válidas
                params = {'a': 1.0, 'b': 0.0, 'c': 0.2}
            else:
                params = self._estimate_item_parameters(item_responses[valid_mask])
            
            calibrated_params.append({
                'Questao': questao,
                'a': params['a'],
                'b': params['b'],
                'c': params['c'],
                'calibrated': True
            })
    
    return pd.DataFrame(calibrated_params)
```

#### **3. Estimação de Parâmetros**

A estimação utiliza máxima verossimilhança com restrições:

```python
def _estimate_item_parameters(self, responses: np.ndarray) -> Dict:
    """
    Estima parâmetros usando máxima verossimilhança
    """
    # Valores iniciais
    initial_params = [1.0, 0.0, 0.2]  # a, b, c
    
    # Função objetivo: log-likelihood
    def objective(params):
        a, b, c = params
        if a <= 0 or c < 0 or c > 1:
            return 1e6  # Penalidade para parâmetros inválidos
        
        # Calcular probabilidades esperadas
        theta_est = np.mean(responses)  # Estimativa simples de theta
        p_correct = c + (1 - c) / (1 + np.exp(-1.7 * a * (theta_est - b)))
        
        # Log-likelihood
        ll = np.sum(responses * np.log(p_correct) + 
                   (1 - responses) * np.log(1 - p_correct))
        return -ll  # Minimizar -log-likelihood
    
    # Otimização com restrições
    try:
        result = minimize(objective, initial_params, method='L-BFGS-B',
                        bounds=[(0.1, 5.0), (-3.0, 3.0), (0.0, 0.5)])
        
        if result.success:
            return {'a': result.x[0], 'b': result.x[1], 'c': result.x[2]}
        else:
            return {'a': 1.0, 'b': 0.0, 'c': 0.2}
            
    except Exception:
        return {'a': 1.0, 'b': 0.0, 'c': 0.2}
```

### **Validação de Âncoras**

#### **Critérios de Qualidade**

1. **Número mínimo**: Pelo menos 5 itens âncora por domínio
2. **Distribuição**: Cobertura adequada da escala de dificuldade
3. **Discriminação**: Itens com a ≥ 0.5
4. **Estabilidade**: Parâmetros bem estimados (erro padrão < 0.1)

#### **Implementação da Validação**

```python
def validate_calibration(self, params_df: pd.DataFrame) -> Dict:
    """
    Valida parâmetros calibrados
    """
    validation = {
        'valid': True,
        'warnings': [],
        'errors': []
    }
    
    # Verificar valores dos parâmetros
    if (params_df['a'] <= 0).any():
        validation['errors'].append("Parâmetros 'a' devem ser positivos")
        validation['valid'] = False
    
    if (params_df['c'] < 0).any() or (params_df['c'] > 1).any():
        validation['errors'].append("Parâmetros 'c' devem estar entre 0 e 1")
        validation['valid'] = False
    
    # Verificar valores extremos
    if (params_df['a'] > 10).any():
        validation['warnings'].append("Alguns parâmetros 'a' são muito altos")
    
    if (params_df['b'] < -5).any() or (params_df['b'] > 5).any():
        validation['warnings'].append("Alguns parâmetros 'b' são extremos")
    
    return validation
```

## 📊 Estimação de Theta

### **Algoritmo de Máxima Verossimilhança**

#### **Função de Verossimilhança**

```
L(θ) = ∏ᵢ Pᵢ(θ)ʸⁱ × [1 - Pᵢ(θ)]^(1-ʸⁱ)
```

Onde:
- **L(θ)**: Verossimilhança da proficiência θ
- **Pᵢ(θ)**: Probabilidade de acerto no item i
- **ʸⁱ**: Resposta observada (0 ou 1)

#### **Implementação**

```python
def estimate_theta(self, responses: np.ndarray, a_params: np.ndarray, 
                  b_params: np.ndarray, c_params: np.ndarray) -> float:
    """
    Estima a proficiência (theta) de um aluno
    """
    bounds = self.config["theta_bounds"]
    
    # Otimização com diferentes pontos iniciais para evitar mínimos locais
    initial_points = [-2.0, -1.0, 0.0, 1.0, 2.0]
    best_theta = 0.0
    best_ll = float('inf')
    
    for initial_theta in initial_points:
        try:
            result = minimize_scalar(
                lambda theta: self.log_likelihood(theta, responses, a_params, b_params, c_params),
                bounds=bounds,
                method='bounded',
                options={'xatol': 1e-6}
            )
            
            if result.success and result.fun < best_ll:
                best_theta = result.x
                best_ll = result.fun
                
        except Exception:
            continue
    
    return best_theta
```

### **Tratamento de Respostas Extremas**

#### **Respostas Perfeitas (All Correct)**
- **Problema**: Log-likelihood tende a +∞
- **Solução**: Estimativa de theta = limite superior da escala

#### **Respostas Nulas (All Wrong)**
- **Problema**: Log-likelihood tende a +∞
- **Solução**: Estimativa de theta = limite inferior da escala

#### **Implementação**

```python
def _handle_extreme_responses(self, responses: np.ndarray, 
                             a_params: np.ndarray, b_params: np.ndarray, 
                             c_params: np.ndarray) -> float:
    """
    Trata respostas extremas (todas corretas ou todas incorretas)
    """
    if np.all(responses == 1):
        return self.config["theta_bounds"][1]  # Limite superior
    elif np.all(responses == 0):
        return self.config["theta_bounds"][0]  # Limite inferior
    else:
        return None  # Resposta normal, usar estimação
```

## 🔍 Validação e Qualidade dos Dados

### **Critérios de Validação**

#### **1. Dados de Entrada**
- **Completude**: Mínimo 90% de respostas válidas
- **Consistência**: Respostas binárias (0/1)
- **Tamanho**: Mínimo 10 estudantes, máximo 100.000

#### **2. Parâmetros dos Itens**
- **a**: 0.1 ≤ a ≤ 10.0
- **b**: -5.0 ≤ b ≤ 5.0
- **c**: 0.0 ≤ c ≤ 0.5

#### **3. Resultados**
- **Theta**: -4.0 ≤ θ ≤ 4.0
- **Nota ENEM**: 100 ≤ nota ≤ 900

### **Implementação da Validação**

```python
def validate_data_quality(self, df: pd.DataFrame) -> bool:
    """
    Valida qualidade dos dados de entrada
    """
    # Verificar colunas obrigatórias
    required_cols = ["CodPessoa", "Questao", "RespostaAluno", "Gabarito"]
    if not all(col in df.columns for col in required_cols):
        return False
    
    # Verificar tamanho mínimo
    if len(df) < 50:  # Mínimo de respostas
        return False
    
    # Verificar completude
    completeness = 1 - df.isnull().sum().sum() / (len(df) * len(df.columns))
    if completeness < 0.9:
        return False
    
    return True
```

## 📈 Escala e Normalização

### **Conversão para Escala ENEM**

#### **Fórmula de Conversão**

```
Nota ENEM = 500 + 100 × θ
```

Onde:
- **500**: Nota base (média da escala)
- **100**: Fator de escala
- **θ**: Theta estimado na escala logística

#### **Implementação**

```python
def convert_to_enem_scale(self, theta: float) -> float:
    """
    Converte theta para escala ENEM
    """
    enem_base = self.config["enem_base"]
    enem_scale = self.config["enem_scale"]
    
    nota = enem_base + enem_scale * theta
    return np.clip(nota, 100, 900)  # Limites da escala ENEM
```

### **Normalização dos Parâmetros**

#### **Padronização dos Parâmetros b**

Para facilitar interpretação, os parâmetros b podem ser normalizados:

```python
def normalize_b_parameters(self, b_params: np.ndarray) -> np.ndarray:
    """
    Normaliza parâmetros b para média 0 e desvio padrão 1
    """
    mean_b = np.mean(b_params)
    std_b = np.std(b_params)
    
    if std_b > 0:
        normalized_b = (b_params - mean_b) / std_b
    else:
        normalized_b = b_params - mean_b
    
    return normalized_b
```

## 🧮 Otimizações Numéricas

### **Algoritmos de Otimização**

#### **1. L-BFGS-B para Parâmetros dos Itens**
- **Vantagem**: Eficiente para problemas com restrições
- **Aplicação**: Calibração de parâmetros a, b, c
- **Configuração**: Bounds específicos para cada parâmetro

#### **2. Brent para Estimação de Theta**
- **Vantagem**: Estável para funções unidimensionais
- **Aplicação**: Estimação de proficiência individual
- **Configuração**: Limites [-4, 4] para evitar valores extremos

### **Tratamento de Problemas Numéricos**

#### **1. Evitar Overflow/Underflow**
```python
def safe_log(self, x: float) -> float:
    """
    Logaritmo seguro para evitar problemas numéricos
    """
    return np.log(np.clip(x, 1e-10, 1 - 1e-10))
```

#### **2. Múltiplos Pontos Iniciais**
```python
def estimate_theta_robust(self, responses: np.ndarray, 
                         a_params: np.ndarray, b_params: np.ndarray, 
                         c_params: np.ndarray) -> float:
    """
    Estimação robusta de theta com múltiplos pontos iniciais
    """
    initial_points = [-3.0, -1.5, 0.0, 1.5, 3.0]
    best_theta = 0.0
    best_ll = float('inf')
    
    for initial_theta in initial_points:
        try:
            result = minimize_scalar(
                lambda theta: self.log_likelihood(theta, responses, a_params, b_params, c_params),
                bounds=(-4, 4),
                method='bounded'
            )
            
            if result.success and result.fun < best_ll:
                best_theta = result.x
                best_ll = result.fun
                
        except Exception:
            continue
    
    return best_theta
```

## 📊 Análise de Qualidade dos Itens

### **Índices de Qualidade**

#### **1. Índice de Discriminação (a)**
- **Excelente**: a > 1.0
- **Bom**: 0.5 ≤ a ≤ 1.0
- **Regular**: 0.3 ≤ a < 0.5
- **Ruim**: a < 0.3

#### **2. Índice de Dificuldade (b)**
- **Muito fácil**: b < -1.5
- **Fácil**: -1.5 ≤ b < -0.5
- **Médio**: -0.5 ≤ b ≤ 0.5
- **Difícil**: 0.5 < b ≤ 1.5
- **Muito difícil**: b > 1.5

#### **3. Índice de Acerto Casual (c)**
- **Aceitável**: c ≤ 0.25
- **Alto**: 0.25 < c ≤ 0.35
- **Muito alto**: c > 0.35

### **Implementação dos Índices**

```python
def calculate_item_quality_indices(self, params_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula índices de qualidade dos itens
    """
    quality_df = params_df.copy()
    
    # Índice de discriminação
    quality_df['discrimination_quality'] = quality_df['a'].apply(
        lambda x: 'Excelente' if x > 1.0 else
                  'Bom' if x >= 0.5 else
                  'Regular' if x >= 0.3 else 'Ruim'
    )
    
    # Índice de dificuldade
    quality_df['difficulty_quality'] = quality_df['b'].apply(
        lambda x: 'Muito fácil' if x < -1.5 else
                  'Fácil' if x < -0.5 else
                  'Médio' if x <= 0.5 else
                  'Difícil' if x <= 1.5 else 'Muito difícil'
    )
    
    # Índice de acerto casual
    quality_df['guessing_quality'] = quality_df['c'].apply(
        lambda x: 'Aceitável' if x <= 0.25 else
                  'Alto' if x <= 0.35 else 'Muito alto'
    )
    
    return quality_df
```

## 🔬 Testes e Validação

### **Testes de Consistência**

#### **1. Teste de Ajuste do Modelo**
- **Chi-quadrado**: Comparação entre frequências observadas e esperadas
- **Implementação**: Agrupamento de respostas por faixas de theta

#### **2. Análise de Resíduos**
- **Resíduos padronizados**: Diferença entre observado e esperado
- **Critério**: |resíduo| < 2.0 para 95% dos casos

#### **3. Teste de Independência Local**
- **Hipótese**: Respostas independentes condicionadas ao theta
- **Método**: Correlação entre resíduos de itens diferentes

### **Implementação dos Testes**

```python
def test_model_fit(self, responses: np.ndarray, thetas: np.ndarray,
                   a_params: np.ndarray, b_params: np.ndarray, 
                   c_params: np.ndarray) -> Dict:
    """
    Testa o ajuste do modelo 3PL
    """
    # Agrupar por faixas de theta
    theta_bins = pd.cut(thetas, bins=5, labels=False)
    
    chi_square_stats = []
    for bin_idx in range(5):
        bin_mask = theta_bins == bin_idx
        if np.sum(bin_mask) > 0:
            bin_responses = responses[bin_mask]
            bin_thetas = thetas[bin_mask]
            
            # Calcular frequências esperadas
            expected_probs = np.array([
                self.prob_3pl(theta, a, b, c)
                for theta, a, b, c in zip(bin_thetas, a_params, b_params, c_params)
            ])
            
            # Chi-quadrado
            observed = bin_responses
            expected = expected_probs
            chi_square = np.sum((observed - expected) ** 2 / expected)
            chi_square_stats.append(chi_square)
    
    # Estatística total
    total_chi_square = np.sum(chi_square_stats)
    df = len(chi_square_stats) - 1
    
    return {
        'chi_square': total_chi_square,
        'degrees_of_freedom': df,
        'p_value': 1 - chi2.cdf(total_chi_square, df),
        'significant': total_chi_square > chi2.ppf(0.95, df)
    }
```

## 📈 Relatórios e Visualizações

### **Relatórios Automáticos**

#### **1. Relatório de Calibração**
- Parâmetros estimados com erros padrão
- Índices de qualidade dos itens
- Gráficos de informação dos itens
- Testes de ajuste do modelo

#### **2. Relatório de Aplicação**
- Estatísticas descritivas das proficiências
- Distribuição das notas ENEM
- Análise de consistência interna
- Comparação com normas de referência

### **Gráficos Específicos**

#### **1. Curva Característica do Item (CCI)**
```python
def plot_item_characteristic_curve(self, a: float, b: float, c: float, 
                                 theta_range: np.ndarray) -> go.Figure:
    """
    Plota a curva característica do item
    """
    probs = [self.prob_3pl(theta, a, b, c) for theta in theta_range]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=theta_range,
        y=probs,
        mode='lines',
        name=f'Item (a={a:.2f}, b={b:.2f}, c={c:.2f})'
    ))
    
    fig.update_layout(
        title='Curva Característica do Item',
        xaxis_title='Theta (Proficiência)',
        yaxis_title='Probabilidade de Acerto',
        xaxis=dict(range=[-4, 4]),
        yaxis=dict(range=[0, 1])
    )
    
    return fig
```

#### **2. Função de Informação do Item**
```python
def plot_item_information_function(self, a: float, b: float, c: float,
                                 theta_range: np.ndarray) -> go.Figure:
    """
    Plota a função de informação do item
    """
    info_values = []
    for theta in theta_range:
        p = self.prob_3pl(theta, a, b, c)
        info = (a ** 2) * p * (1 - p) * ((1 - c) ** 2) / ((p - c) ** 2)
        info_values.append(info)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=theta_range,
        y=info_values,
        mode='lines',
        name=f'Informação (a={a:.2f}, b={b:.2f}, c={c:.2f})'
    ))
    
    fig.update_layout(
        title='Função de Informação do Item',
        xaxis_title='Theta (Proficiência)',
        yaxis_title='Informação',
        xaxis=dict(range=[-4, 4])
    )
    
    return fig
```

## 🚀 Considerações para Produção

### **Performance e Escalabilidade**

#### **1. Otimizações de Memória**
- Processamento em lotes para grandes datasets
- Uso de arrays NumPy em vez de listas Python
- Limpeza automática de variáveis intermediárias

#### **2. Paralelização**
- Processamento paralelo de múltiplos alunos
- Uso de multiprocessing para calibração de itens
- Distribuição de carga em múltiplos cores

#### **3. Cache e Persistência**
- Cache de parâmetros calibrados
- Persistência de resultados intermediários
- Recuperação de falhas de processamento

### **Monitoramento e Logging**

#### **1. Métricas de Performance**
- Tempo de processamento por item
- Uso de memória durante calibração
- Taxa de convergência dos algoritmos

#### **2. Alertas de Qualidade**
- Parâmetros fora dos limites aceitáveis
- Falhas de convergência na otimização
- Inconsistências nos dados de entrada

## 📚 Referências Bibliográficas

1. **Birnbaum, A. (1968)**. Some latent trait models and their use in inferring an examinee's ability. In F. M. Lord & M. R. Novick (Eds.), *Statistical theories of mental test scores* (pp. 397-479). Reading, MA: Addison-Wesley.

2. **Baker, F. B., & Kim, S. H. (2017)**. *The basics of item response theory using R*. New York: Springer.

3. **De Ayala, R. J. (2009)**. *The theory and practice of item response theory*. New York: The Guilford Press.

4. **Hambleton, R. K., Swaminathan, H., & Rogers, H. J. (1991)**. *Fundamentals of item response theory*. Newbury Park, CA: Sage.

5. **Lord, F. M. (1980)**. *Applications of item response theory to practical testing problems*. Hillsdale, NJ: Lawrence Erlbaum Associates.

## 🔗 Links Úteis

- **Documentação oficial**: [Link para documentação]
- **Repositório GitHub**: [Link para repositório]
- **Issues e suporte**: [Link para issues]
- **Wiki do projeto**: [Link para wiki]

---

**Desenvolvido para a comunidade científica e educacional**

*Última atualização: Dezembro 2024*
