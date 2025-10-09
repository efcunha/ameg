# Sistema de Alertas e Notificações AMEG

Sistema completo de notificações em tempo real para o sistema AMEG, com níveis de prioridade, histórico e interface intuitiva.

## 📋 Visão Geral

O sistema de alertas do AMEG permite criar, gerenciar e visualizar notificações importantes para os usuários do sistema, garantindo que informações críticas sejam comunicadas de forma eficiente.

## 🎯 Funcionalidades Principais

### **Criação de Notificações**
- **Interface simples** - Formulário intuitivo para criar alertas
- **Níveis de prioridade** - 4 níveis distintos com cores e ícones
- **Validação automática** - Campos obrigatórios e limites de caracteres
- **Timestamp automático** - Data e hora de criação registradas

### **Visualização e Controle**
- **Histórico completo** - Lista todas as notificações criadas
- **Marcação de leitura** - Sistema de visualização individual
- **Filtros visuais** - Cores e ícones por prioridade
- **Interface responsiva** - Funciona em desktop e mobile

### **Gerenciamento**
- **Persistência** - Armazenamento em banco PostgreSQL
- **Auditoria** - Log de criação e visualização
- **Segurança** - Acesso controlado por login

## 🚨 Níveis de Prioridade

### **🔴 URGENT (Urgente)**
- **Cor**: Vermelho (#dc3545)
- **Ícone**: ⚠️
- **Uso**: Problemas críticos, falhas de sistema, emergências
- **Exemplo**: "Sistema de backup falhou - ação imediata necessária"

### **🟠 HIGH (Alta)**
- **Cor**: Laranja (#fd7e14)
- **Ícone**: 🔥
- **Uso**: Problemas importantes que precisam de atenção rápida
- **Exemplo**: "Espaço em disco baixo - 85% utilizado"

### **🟡 MEDIUM (Média)**
- **Cor**: Amarelo (#ffc107)
- **Ícone**: 📢
- **Uso**: Informações importantes mas não críticas
- **Exemplo**: "Nova funcionalidade disponível no sistema"

### **🟢 LOW (Baixa)**
- **Cor**: Verde (#28a745)
- **Ícone**: ℹ️
- **Uso**: Informações gerais, lembretes, dicas
- **Exemplo**: "Lembrete: Backup semanal será executado hoje"

## 🛠️ Como Usar

### **1. Criar Nova Notificação**

1. Acesse a aba **🔔 Notificações** no menu principal
2. Clique em **"➕ Nova Notificação"**
3. Preencha os campos:
   - **Tipo**: Selecione o nível de prioridade
   - **Título**: Título conciso da notificação (máx. 200 caracteres)
   - **Mensagem**: Descrição detalhada (máx. 1000 caracteres)
4. Clique em **"Criar Notificação"**

### **2. Visualizar Notificações**

- **Lista completa**: Todas as notificações aparecem na página principal
- **Ordenação**: Mais recentes primeiro
- **Status visual**: 
  - **Não lida**: Fundo branco, texto normal
  - **Lida**: Fundo acinzentado, opacidade reduzida

### **3. Marcar como Lida**

- Clique no **ícone do olho** (👁️) ao lado da notificação
- A notificação será marcada como visualizada
- O status muda visualmente para indicar leitura

## 🗄️ Estrutura do Banco de Dados

### **Tabela: `historico_notificacoes`**

```sql
CREATE TABLE historico_notificacoes (
    id SERIAL PRIMARY KEY,
    tipo VARCHAR(20) NOT NULL,           -- urgent, high, medium, low
    titulo VARCHAR(200) NOT NULL,        -- Título da notificação
    mensagem TEXT NOT NULL,              -- Conteúdo da mensagem
    data_criacao TIMESTAMP DEFAULT NOW(), -- Data de criação
    visualizada BOOLEAN DEFAULT FALSE,   -- Status de leitura
    data_visualizacao TIMESTAMP,         -- Quando foi lida
    usuario_criador VARCHAR(100),        -- Quem criou
    usuario_visualizador VARCHAR(100)    -- Quem leu
);
```

### **Índices para Performance**
```sql
CREATE INDEX idx_notificacoes_tipo ON historico_notificacoes(tipo);
CREATE INDEX idx_notificacoes_data ON historico_notificacoes(data_criacao);
CREATE INDEX idx_notificacoes_visualizada ON historico_notificacoes(visualizada);
```

## 🎨 Interface Visual

### **Cores e Estilos**

```css
/* Urgent - Vermelho */
.notification-item.urgent {
    border-left: 4px solid #dc3545;
    background: #fff5f5;
}

/* High - Laranja */
.notification-item.high {
    border-left: 4px solid #fd7e14;
    background: #fff8f0;
}

/* Medium - Amarelo */
.notification-item.medium {
    border-left: 4px solid #ffc107;
    background: #fffbf0;
}

/* Low - Verde */
.notification-item.low {
    border-left: 4px solid #28a745;
    background: #f0fff4;
}

/* Visualizada */
.notification-item.visualizada {
    opacity: 0.7;
    background: #f8f9fa;
}
```

### **Ícones por Prioridade**
- **Urgent**: ⚠️ (Triângulo de aviso)
- **High**: 🔥 (Fogo)
- **Medium**: 📢 (Megafone)
- **Low**: ℹ️ (Informação)

## 🔧 Implementação Técnica

### **Backend (Flask)**

#### **Rota de Criação**
```python
@notifications_bp.route('/notificacoes', methods=['POST'])
@login_required
def criar_notificacao():
    # Validação e inserção no banco
    # Registro de auditoria
    # Redirecionamento com feedback
```

#### **Rota de Listagem**
```python
@notifications_bp.route('/notificacoes')
@login_required
def listar_notificacoes():
    # Busca paginada
    # Ordenação por data
    # Renderização do template
```

#### **Rota de Marcação**
```python
@notifications_bp.route('/api/marcar-visualizada/<int:notif_id>')
@login_required
def marcar_visualizada(notif_id):
    # Atualização do status
    # Registro de quem visualizou
    # Resposta JSON
```

### **Frontend (HTML/CSS/JS)**

#### **Formulário de Criação**
```html
<form method="POST">
    <select name="tipo" required>
        <option value="urgent">🔴 Urgente</option>
        <option value="high">🟠 Alta</option>
        <option value="medium">🟡 Média</option>
        <option value="low">🟢 Baixa</option>
    </select>
    <input name="titulo" maxlength="200" required>
    <textarea name="mensagem" maxlength="1000" required></textarea>
    <button type="submit">Criar Notificação</button>
</form>
```

#### **Lista de Notificações**
```html
<div class="notification-item {{ notificacao.tipo }} {{ 'visualizada' if notificacao.visualizada }}">
    <div class="notification-header">
        <span class="notification-icon">{{ icon }}</span>
        <span class="notification-title">{{ notificacao.titulo }}</span>
        <span class="notification-date">{{ notificacao.data_criacao }}</span>
    </div>
    <div class="notification-message">{{ notificacao.mensagem }}</div>
    <div class="notification-actions">
        <button onclick="marcarVisualizada({{ notificacao.id }})">👁️</button>
    </div>
</div>
```

## 📊 Estatísticas e Métricas

### **Dados Coletados**
- **Total de notificações** por período
- **Distribuição por prioridade** (urgent, high, medium, low)
- **Taxa de visualização** (lidas vs não lidas)
- **Tempo médio** entre criação e visualização
- **Usuários mais ativos** na criação de alertas

### **Relatórios Disponíveis**
- **Dashboard de notificações** - Visão geral em tempo real
- **Histórico detalhado** - Lista completa com filtros
- **Análise de engajamento** - Quais tipos são mais visualizados

## 🔒 Segurança e Permissões

### **Controle de Acesso**
- **Login obrigatório** - Apenas usuários autenticados
- **Criação livre** - Qualquer usuário logado pode criar
- **Visualização própria** - Cada usuário vê suas próprias marcações
- **Auditoria completa** - Log de todas as ações

### **Validações**
- **Campos obrigatórios** - Tipo, título e mensagem
- **Limites de caracteres** - Título (200), Mensagem (1000)
- **Sanitização** - Prevenção de XSS e injeção
- **Rate limiting** - Prevenção de spam (futuro)

## 🚀 Melhorias Futuras

### **Funcionalidades Planejadas**
- [ ] **Notificações push** - Alertas em tempo real no navegador
- [ ] **Filtros avançados** - Por data, tipo, status
- [ ] **Notificações por email** - Envio automático para urgent/high
- [ ] **Templates** - Modelos pré-definidos para tipos comuns
- [ ] **Agendamento** - Notificações programadas
- [ ] **Anexos** - Suporte a arquivos nas notificações
- [ ] **Menções** - Notificar usuários específicos (@usuario)
- [ ] **Categorias** - Agrupamento por área (sistema, usuários, etc.)

### **Melhorias Técnicas**
- [ ] **WebSockets** - Notificações em tempo real
- [ ] **Cache Redis** - Performance para grandes volumes
- [ ] **API REST** - Integração com sistemas externos
- [ ] **Webhooks** - Notificações para serviços externos
- [ ] **Métricas avançadas** - Dashboard analítico

## 📚 Exemplos de Uso

### **Cenários Comuns**

#### **1. Manutenção do Sistema**
```
Tipo: HIGH
Título: Manutenção programada - Sistema indisponível
Mensagem: O sistema ficará indisponível das 02:00 às 04:00 para manutenção dos servidores. Planeje suas atividades adequadamente.
```

#### **2. Nova Funcionalidade**
```
Tipo: MEDIUM
Título: Nova funcionalidade: Gráficos interativos
Mensagem: Agora você pode visualizar dados demográficos em gráficos interativos. Acesse a aba "📊 Gráficos" no menu principal.
```

#### **3. Problema Crítico**
```
Tipo: URGENT
Título: Falha no backup automático
Mensagem: O backup automático falhou nas últimas 24h. Verifique os logs e execute backup manual imediatamente.
```

#### **4. Lembrete Geral**
```
Tipo: LOW
Título: Lembrete: Atualização de dados
Mensagem: Lembre-se de manter os dados dos cadastros sempre atualizados para garantir a qualidade das informações.
```

## 🎯 Boas Práticas

### **Para Criadores de Notificações**
1. **Use o nível correto** - Urgent apenas para emergências
2. **Seja claro e conciso** - Títulos objetivos, mensagens detalhadas
3. **Inclua ações** - O que o usuário deve fazer
4. **Evite spam** - Não crie notificações desnecessárias
5. **Teste a mensagem** - Releia antes de enviar

### **Para Administradores**
1. **Monitore o uso** - Verifique estatísticas regularmente
2. **Eduque usuários** - Treine sobre os níveis de prioridade
3. **Limpe histórico** - Remova notificações antigas periodicamente
4. **Analise engajamento** - Veja quais tipos são mais eficazes
5. **Mantenha atualizado** - Acompanhe melhorias do sistema

---

**Sistema de Alertas AMEG** - Comunicação eficiente e organizada para toda a equipe.
