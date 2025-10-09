# Sistema de Notificações AMEG

Sistema de histórico de notificações para alertas de saúde e eventos importantes do sistema AMEG.

## 📋 Visão Geral

O sistema de notificações do AMEG atualmente implementa um **histórico de notificações** que exibe alertas de saúde e outros eventos importantes quando disponíveis.

## 🎯 Funcionalidade Atual

### **Histórico de Notificações**
- **Página dedicada** - Aba "🔔 Notificações" no menu principal
- **Lista de notificações** - Exibe alertas quando disponíveis
- **Estado vazio** - Mensagem informativa quando não há notificações
- **Interface responsiva** - Funciona em desktop e mobile

## 🖥️ Interface Atual

### **Página de Notificações**
```
📋 Histórico de Notificações

📭 Nenhuma notificação encontrada

Quando houver alertas de saúde ou outros eventos importantes, 
eles aparecerão aqui.
```

### **Navegação**
- Acessível via aba **🔔 Notificações** no menu principal
- Disponível para todos os usuários logados
- Interface consistente com o resto do sistema

## 🗄️ Estrutura do Banco de Dados

### **Tabela: `historico_notificacoes`**

```sql
CREATE TABLE historico_notificacoes (
    id SERIAL PRIMARY KEY,
    tipo VARCHAR(20) NOT NULL,           -- Tipo da notificação
    titulo VARCHAR(200) NOT NULL,        -- Título da notificação
    mensagem TEXT NOT NULL,              -- Conteúdo da mensagem
    data_criacao TIMESTAMP DEFAULT NOW(), -- Data de criação
    visualizada BOOLEAN DEFAULT FALSE,   -- Status de leitura
    data_visualizacao TIMESTAMP,         -- Quando foi lida
    usuario_criador VARCHAR(100),        -- Quem criou
    usuario_visualizador VARCHAR(100)    -- Quem leu
);
```

## 🔧 Implementação Técnica

### **Backend (Flask)**

#### **Rota Principal**
```python
@notifications_bp.route('/notificacoes')
@login_required
def notificacoes_simples():
    # Busca notificações no banco
    # Renderiza template com lista
    # Exibe mensagem se vazio
```

#### **Blueprint: `notifications.py`**
- Localizado em `blueprints/notifications.py`
- Gerencia rotas de notificações
- Integrado ao sistema principal

### **Frontend**

#### **Template: `historico_notificacoes.html`**
- Interface para exibir notificações
- Estado vazio com mensagem informativa
- Navegação padronizada
- Estilos responsivos

#### **Navegação Integrada**
```html
<a href="/notificacoes">🔔 Notificações</a>
```

## 📊 Estado Atual

### **Funcionalidades Implementadas**
- ✅ **Página de histórico** - Interface completa
- ✅ **Navegação integrada** - Aba em todos os menus
- ✅ **Banco de dados** - Estrutura preparada
- ✅ **Template responsivo** - Interface adaptável
- ✅ **Estado vazio** - Mensagem quando sem notificações

### **Funcionalidades Preparadas (Estrutura Pronta)**
- 🔄 **Criação de notificações** - Banco preparado
- 🔄 **Tipos de prioridade** - Campo tipo implementado
- 🔄 **Marcação de leitura** - Campos visualizada/data_visualizacao
- 🔄 **Auditoria** - Campos usuario_criador/visualizador

## 🎯 Casos de Uso Planejados

### **Alertas de Saúde**
- Notificações sobre cadastros com condições críticas
- Lembretes de acompanhamento médico
- Alertas sobre medicamentos vencidos

### **Eventos do Sistema**
- Notificações de backup
- Alertas de manutenção
- Informações sobre atualizações

## 🚀 Próximos Passos

### **Funcionalidades a Implementar**
1. **Interface de criação** - Formulário para criar notificações
2. **Sistema de prioridades** - Cores e ícones por tipo
3. **Marcação de leitura** - Controle de visualização
4. **Filtros** - Por tipo, data, status
5. **Integração automática** - Alertas baseados em dados de saúde

### **Melhorias Planejadas**
- **Notificações automáticas** - Baseadas em regras de saúde
- **Dashboard de alertas** - Visão geral no painel principal
- **Configurações** - Preferências de notificação por usuário
- **Exportação** - Relatórios de notificações

## 🔒 Segurança

### **Controle de Acesso**
- **Login obrigatório** - Apenas usuários autenticados
- **Navegação protegida** - Verificação de sessão
- **Dados seguros** - Estrutura preparada para auditoria

### **Preparação para Expansão**
- **Campos de auditoria** - Rastreamento de criação/visualização
- **Validações** - Estrutura para limites e sanitização
- **Permissões** - Base para controles granulares

---

**Sistema de Notificações AMEG** - Estrutura implementada e pronta para expansão com alertas de saúde e eventos importantes.
