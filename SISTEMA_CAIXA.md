# 💰 Sistema de Caixa AMEG

Sistema completo de controle de caixa com entrada e saída, incluindo upload de comprovantes e integração com cadastros existentes.

## 🚀 Funcionalidades Implementadas

### **Controle Financeiro**
- ✅ **Entradas e Saídas** - Registro completo de movimentações
- ✅ **Saldo Automático** - Cálculo em tempo real
- ✅ **Integração com Cadastros** - Vinculação com pessoas cadastradas
- ✅ **Comprovantes** - Upload de recibos, notas e imagens
- ✅ **Auditoria** - Log completo de todas as operações

### **Interface Completa**
- ✅ **Dashboard de Caixa** - Visão geral com saldo e resumos
- ✅ **Formulários Inteligentes** - Entrada e saída com validação
- ✅ **Upload de Arquivos** - Drag & drop para comprovantes
- ✅ **Relatórios** - Visualização e exportação de dados
- ✅ **Responsivo** - Funciona em desktop e mobile

## 📁 Arquivos Criados/Modificados

### **Banco de Dados (database.py)**
```sql
-- Tabela principal de movimentações
CREATE TABLE movimentacoes_caixa (
    id SERIAL PRIMARY KEY,
    tipo VARCHAR(10) CHECK (tipo IN ('entrada', 'saida')),
    valor DECIMAL(10,2) NOT NULL,
    descricao TEXT NOT NULL,
    cadastro_id INTEGER REFERENCES cadastros(id),
    nome_pessoa VARCHAR(255),
    numero_recibo VARCHAR(50),
    observacoes TEXT,
    data_movimentacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario VARCHAR(100) NOT NULL
);

-- Tabela de comprovantes
CREATE TABLE comprovantes_caixa (
    id SERIAL PRIMARY KEY,
    movimentacao_id INTEGER REFERENCES movimentacoes_caixa(id),
    nome_arquivo VARCHAR(255) NOT NULL,
    tipo_arquivo VARCHAR(50),
    arquivo_dados BYTEA,
    data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### **Funções Implementadas**
- `inserir_movimentacao_caixa()` - Registra nova movimentação
- `inserir_comprovante_caixa()` - Salva comprovantes
- `listar_movimentacoes_caixa()` - Lista com paginação
- `obter_saldo_caixa()` - Calcula saldo atual
- `obter_comprovantes_movimentacao()` - Lista comprovantes
- `listar_cadastros_simples()` - Para selects de pessoas

### **Templates HTML**
- `templates/caixa.html` - Interface principal do caixa
- `templates/relatorio_caixa.html` - Relatórios e exportação

### **Rotas Flask (app.py)**
- `GET /caixa` - Exibe interface do caixa
- `POST /caixa` - Processa movimentações
- `GET /relatorio_caixa` - Relatórios com filtros

## 🎯 Como Usar

### **1. Acessar o Sistema**
```
http://localhost:5000/caixa
```

### **2. Registrar Entrada**
- Clique em "➕ Nova Entrada"
- Preencha valor e descrição
- Selecione pessoa (opcional) ou digite nome
- Adicione número do recibo
- Faça upload de comprovantes
- Clique em "💾 Registrar Entrada"

### **3. Registrar Saída**
- Clique em "➖ Nova Saída"
- Preencha valor e descrição
- Selecione pessoa/fornecedor ou digite nome
- Adicione número da nota/recibo
- Faça upload de comprovantes
- Clique em "💾 Registrar Saída"

### **4. Visualizar Relatórios**
- Clique em "📊 Relatório"
- Use filtros por tipo e data
- Exporte para CSV ou imprima

## 💡 Recursos Avançados

### **Upload de Comprovantes**
- **Drag & Drop** - Arraste arquivos para upload
- **Múltiplos Formatos** - PDF, DOC, DOCX, imagens
- **Validação** - Tamanho máximo 16MB
- **Segurança** - Tipos de arquivo validados

### **Integração com Cadastros**
- **Select Inteligente** - Lista pessoas cadastradas
- **Preenchimento Automático** - Nome preenchido ao selecionar
- **Flexibilidade** - Permite digitar nome manualmente

### **Auditoria Completa**
- **Log de Ações** - Todas as operações registradas
- **Rastreamento** - Usuário, IP, data/hora
- **Dados Completos** - Valores anteriores e novos

### **Relatórios Dinâmicos**
- **Filtros** - Por tipo, data, pessoa
- **Exportação** - CSV para análise externa
- **Impressão** - Layout otimizado para papel
- **Totalizadores** - Entradas, saídas e saldo

## 🔒 Segurança Implementada

### **Validações**
- ✅ **Valores** - Apenas números positivos
- ✅ **Arquivos** - Tipos e tamanhos validados
- ✅ **Sessões** - Acesso apenas para usuários logados
- ✅ **SQL Injection** - Queries parametrizadas

### **Auditoria**
- ✅ **Movimentações** - Todas as operações logadas
- ✅ **Usuário** - Identificação de quem fez a ação
- ✅ **Dados** - Valores anteriores e novos registrados

## 📊 Campos do Sistema

### **Movimentação**
- **Tipo**: Entrada ou Saída
- **Valor**: Valor em reais (R$)
- **Descrição**: Descrição detalhada (obrigatório)
- **Pessoa**: Vinculação com cadastro ou nome livre
- **Recibo/Nota**: Número de identificação
- **Observações**: Informações adicionais
- **Comprovantes**: Arquivos de comprovação

### **Relatórios**
- **Filtro por Tipo**: Entradas, saídas ou todas
- **Filtro por Data**: Período específico
- **Totalizadores**: Entradas, saídas e saldo
- **Exportação**: CSV para análise

## 🚀 Deploy

O sistema está integrado ao projeto AMEG e será deployado automaticamente no Railway junto com as outras funcionalidades.

### **Variáveis de Ambiente**
Nenhuma variável adicional necessária - usa as mesmas do sistema principal.

### **Banco de Dados**
As tabelas serão criadas automaticamente na próxima inicialização do sistema.

## 🎉 Pronto para Uso!

O sistema de caixa está completamente integrado ao AMEG e pronto para uso em produção. Todas as funcionalidades foram implementadas seguindo os padrões de segurança e performance do projeto.

### **Próximos Passos**
1. Fazer deploy no Railway
2. Testar funcionalidades em produção
3. Treinar usuários no novo sistema
4. Monitorar uso e performance

---

**Sistema de Caixa AMEG** - Controle financeiro completo e seguro para a Associação dos Ambulantes e Trabalhadores em Geral da Paraíba.
