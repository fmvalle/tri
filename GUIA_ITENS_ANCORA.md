# 📋 Guia de Uso - Itens Âncora

## 🔧 Como Usar Itens Já Calibrados

### **1. Formato do Arquivo CSV**

O sistema aceita **dois formatos** de separador:

#### **Formato 1: Vírgula (recomendado)**
```csv
Questao,a,b,c
3,4.90988,0.22751,0.27811
7,4.754,0.37548,0.20003
11,2.74981,-0.23035,0.22434
```

#### **Formato 2: Ponto e Vírgula**
```csv
Questao;a;b;c
3;4.90988;0.22751;0.27811
7;4.754;0.37548;0.20003
11;2.74981;-0.23035;0.22434
```

### **2. Estrutura dos Dados**

| Coluna | Descrição | Exemplo |
|--------|-----------|---------|
| `Questao` | Número da questão | 3, 7, 11, 15... |
| `a` | Parâmetro de discriminação | 4.90988 |
| `b` | Parâmetro de dificuldade | 0.22751 |
| `c` | Parâmetro de acerto casual | 0.27811 |

### **3. Passo a Passo**

#### **3.1. Preparar o Arquivo**
1. Crie um arquivo CSV com os itens já calibrados
2. Use apenas os itens que você tem certeza dos parâmetros
3. Não precisa incluir todos os itens da prova

#### **3.2. No Dashboard**
1. **Carregue dados** na aba "📁 Upload de Dados"
2. **Vá para** aba "🔧 Calibração de Itens"
3. **Marque** "Usar itens âncora"
4. **Carregue** seu arquivo CSV
5. **Clique** "🔧 Calibrar Itens"

### **4. Exemplo Prático**

#### **Seu arquivo atual (corrigido):**
```csv
Questao,a,b,c
3,4.90988,0.22751,0.27811
7,4.754,0.37548,0.20003
11,2.74981,-0.23035,0.22434
15,2.10838,0.80678,0.16725
25,1.72676,2.00908,0.22638
33,4.83287,0.36217,0.2041
36,2.2557,0.15138,0.16304
40,3.11338,0.48212,0.18723
45,3.70482,0.50693,0.20999
```

#### **O que acontece:**
- ✅ **9 itens âncora** serão usados como referência
- ✅ **36 itens restantes** serão calibrados automaticamente
- ✅ **Parâmetros finais** combinarão âncora + calibrados

### **5. Dicas Importantes**

#### **✅ Faça:**
- Use itens com parâmetros bem calibrados
- Inclua itens de diferentes níveis de dificuldade
- Verifique se os valores estão dentro dos limites esperados

#### **❌ Evite:**
- Usar itens com parâmetros duvidosos
- Incluir todos os itens (deixe alguns para calibração)
- Usar valores extremos ou inconsistentes

### **6. Validação dos Parâmetros**

#### **Limites Esperados:**
- **Parâmetro 'a':** 0.1 a 5.0 (discriminação)
- **Parâmetro 'b':** -3.0 a 3.0 (dificuldade)
- **Parâmetro 'c':** 0.0 a 0.5 (acerto casual)

#### **Seus valores estão OK:**
- ✅ Todos os 'a' estão entre 1.7 e 4.9
- ✅ Todos os 'b' estão entre -0.2 e 2.0
- ✅ Todos os 'c' estão entre 0.16 e 0.28

### **7. Arquivos de Exemplo**

- **`itens_calibrados_corrigido.csv`** - Seu arquivo corrigido
- **`exemplo_itens_ancora.csv`** - Exemplo genérico

### **8. Troubleshooting**

#### **Erro: "Erro ao carregar itens âncora"**
- ✅ Verifique se o arquivo é CSV
- ✅ Use vírgula ou ponto e vírgula como separador
- ✅ Verifique se as colunas são: Questao,a,b,c

#### **Erro: "Parâmetros inválidos"**
- ✅ Verifique se os valores estão nos limites esperados
- ✅ Não use valores negativos para 'a' ou 'c'
- ✅ Verifique se não há células vazias

---

**🎯 Agora você pode usar seus itens já calibrados com sucesso!**
