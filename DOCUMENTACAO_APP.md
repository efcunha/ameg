# Documentação Técnica Detalhada - Sistema AMEG

## Visão Geral
O Sistema AMEG é uma aplicação Flask modular para cadastro familiar da Associação dos Ambulantes e Trabalhadores em Geral da Paraíba, com arquitetura de blueprints e funcionalidades avançadas de segurança, auditoria e performance.

## Arquitetura do Sistema

### 1. Estrutura de Arquivos (Arquitetura de Blueprints)
```
ameg/
├── app.py                        # 🆕 Orquestrador principal (50 linhas)
├── app.py.backup                 # Backup da versão monolítica anterior
├── database.py                   # Módulo PostgreSQL + security manager
├── security.py                   # Sistema de segurança avançado
├── generate_admin_credentials.py # Gerador de credenciais seguras
├── requirements.txt              # Dependências atualizadas (segurança)
├── SECURITY.md                   # Documentação de segurança
├── blueprints/                   # 🆕 ARQUITETURA MODULAR
│   ├── __init__.py               # Inicialização dos blueprints
│   ├── auth.py                   # Autenticação e login
│   ├── dashboard.py              # Dashboard e estatísticas
│   ├── cadastros.py              # CRUD de cadastros
│   ├── arquivos.py               # Gestão de arquivos de saúde
│   ├── relatorios.py             # Sistema de relatórios
│   ├── usuarios.py               # Gestão de usuários e auditoria
│   ├── caixa.py                  # Sistema financeiro
│   └── utils.py                  # Funções auxiliares compartilhadas
├── templates/                    # Templates HTML otimizados
├── static/                       # Arquivos estáticos otimizados
└── data/                         # Uploads e dados
```

### 2. Principais Módulos

#### **app.py - Orquestrador Principal (50 linhas)**
- Framework Flask 3.0.3 com Flask-Compress
- Registro de 7 blueprints especializados
- Headers de segurança globais
- Inicialização automática do banco PostgreSQL
- Compressão HTTP automática
- **98.7% redução** de código (3.900+ → 50 linhas)

#### **blueprints/ - Arquitetura Modular (44 rotas)**
- **auth.py**: Sistema de autenticação e login
- **dashboard.py**: Dashboard e estatísticas em tempo real
- **cadastros.py**: CRUD completo de cadastros (58 campos + foto)
- **arquivos.py**: Upload e gestão de arquivos de saúde
- **relatorios.py**: 6 tipos de relatórios com exportação
- **usuarios.py**: Gestão de usuários e sistema de auditoria
- **caixa.py**: Sistema financeiro completo
- **utils.py**: Funções auxiliares compartilhadas

#### **database.py - Camada de Dados**
- Conexão PostgreSQL otimizada
- Inicialização automática de tabelas
- Índices de performance
- Integração com Security Manager
- Cache de estatísticas (TTL 5 minutos)
- Auditoria completa de ações

#### **security.py - Módulo de Segurança**
- SecurityManager com hash duplo
- Criptografia Fernet para dados sensíveis
- Geração de senhas seguras
- Proteção especial admin ID 1
- Salt personalizado para senhas

### 3. Tecnologias Implementadas

#### **Backend**
- **Flask 3.0.3**: Framework web principal
- **Flask-Compress 1.15**: Compressão HTTP automática
- **Werkzeug 3.1.3**: Utilitários web (atualizado por segurança)
- **psycopg2-binary 2.9.9**: Driver PostgreSQL
- **cryptography 44.0.0**: Criptografia (atualizado por segurança)
- **Jinja2 3.1.5**: Templates (atualizado por segurança)

#### **Frontend**
- **HTML5/CSS3/JavaScript**: Interface responsiva
- **Lazy Loading**: Carregamento inteligente de imagens
- **Validação unificada**: Sistema centralizado em JavaScript
- **Compressão automática**: Assets otimizados (60-70% redução)

#### **Segurança**
- **PBKDF2 + Salt**: Hash de senhas
- **Fernet**: Criptografia simétrica
- **Headers de segurança**: XSS, clickjacking, MIME protection
- **CSRF Protection**: Via Flask sessions

## Funcionalidades por Blueprint

### 1. auth.py - Sistema de Autenticação
- **Login seguro** com hash PBKDF2 + salt personalizado
- **Proteção admin ID 1** - apenas eles podem modificar própria senha
- **Sessões Flask** com timeout configurável
- **Headers de segurança** implementados

### 2. cadastros.py - Gestão de Cadastros
- **58 campos** baseados no documento oficial AMEG
- **Foto 3x4** via webcam (getUserMedia) ou upload
- **Validação unificada** frontend/backend
- **Edição completa** de todos os campos
- **Proteção de dados** com sanitização

### 3. relatorios.py - Sistema de Relatórios
- **6 tipos especializados**: Completo, Simplificado, por Bairro, Renda, Saúde, Estatístico
- **Exportação múltipla**: CSV, PDF, DOC
- **Paginação otimizada**: 50 registros por página
- **Filtros avançados**: busca e ordenação

### 4. arquivos.py - Gestão de Arquivos de Saúde
- **Upload seguro**: laudos, receitas, exames (16MB máximo)
- **Múltiplos formatos**: PDF, DOC, DOCX, imagens
- **Download protegido**: controle de acesso
- **Organização**: arquivos vinculados por cadastro

### 5. usuarios.py - Administração Avançada
- **Gestão de usuários**: criação, edição, exclusão
- **Sistema de auditoria**: log completo de ações
- **Reset administrativo**: limpeza completa do sistema
- **Proteções especiais**: admin ID 1 não pode ser removido

### 6. caixa.py - Sistema Financeiro
- **Controle de entradas e saídas**: movimentações completas
- **Upload de comprovantes**: recibos e notas fiscais
- **Integração com cadastros**: vinculação de pessoas
- **Relatórios financeiros**: saldo e movimentações

### 7. dashboard.py - Performance e Otimização
- **Compressão automática**: CSS/JS minificados + Gzip
- **Lazy loading**: carregamento inteligente de imagens
- **Cache de estatísticas**: TTL de 5 minutos
- **Índices de banco**: queries 70-85% mais rápidas
- **Flask-Compress**: compressão HTTP automática

## Banco de Dados

### 1. Estrutura de Tabelas

#### **usuarios**
```sql
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    usuario VARCHAR(50) UNIQUE NOT NULL,
    senha VARCHAR(255) NOT NULL,
    tipo VARCHAR(20) DEFAULT 'usuario',
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **cadastros** (58 campos + foto)
```sql
CREATE TABLE cadastros (
    id SERIAL PRIMARY KEY,
    nome_completo VARCHAR(255) NOT NULL,
    cpf VARCHAR(14) UNIQUE,
    foto_base64 TEXT,
    -- ... 55 campos adicionais
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **arquivos_saude**
```sql
CREATE TABLE arquivos_saude (
    id SERIAL PRIMARY KEY,
    cadastro_id INTEGER REFERENCES cadastros(id) ON DELETE CASCADE,
    nome_arquivo VARCHAR(255) NOT NULL,
    nome_original VARCHAR(255) NOT NULL,
    tipo_arquivo VARCHAR(50),
    descricao TEXT,
    data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **auditoria**
```sql
CREATE TABLE auditoria (
    id SERIAL PRIMARY KEY,
    usuario VARCHAR(50) NOT NULL,
    acao VARCHAR(20) NOT NULL,
    tabela VARCHAR(50) NOT NULL,
    registro_id INTEGER,
    dados_anteriores TEXT,
    dados_novos TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    data_acao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. Índices de Performance
```sql
-- Índices para queries 70-85% mais rápidas
CREATE INDEX idx_cadastros_cpf ON cadastros(cpf);
CREATE INDEX idx_cadastros_nome ON cadastros(nome_completo);
CREATE INDEX idx_cadastros_data ON cadastros(data_cadastro);
CREATE INDEX idx_auditoria_usuario ON auditoria(usuario);
CREATE INDEX idx_auditoria_data ON auditoria(data_acao);
CREATE INDEX idx_arquivos_cadastro ON arquivos_saude(cadastro_id);
```

### 3. Cache de Estatísticas
```python
stats_cache = {
    'data': None,
    'timestamp': None,
    'ttl': 300  # 5 minutos
}
```

## Segurança Implementada

### 1. Proteção de Senhas
- **Hash duplo**: Senha + salt personalizado + PBKDF2
- **Criptografia Fernet**: Para dados sensíveis
- **Geração automática**: Senhas aleatórias de 16 caracteres
- **Admin protegido**: ID 1 tem proteções especiais

### 2. Sistema de Auditoria
- **Log completo**: INSERT, UPDATE, DELETE, LOGIN
- **Rastreamento**: usuário, IP, user-agent
- **Dados anteriores/novos**: para comparação
- **Interface administrativa**: para consulta

### 3. Validações e Proteções
- **Headers de segurança**: XSS, clickjacking, MIME
- **Validação unificada**: frontend/backend
- **Upload seguro**: validação de tipos
- **Proteção CSRF**: via Flask sessions

### 4. Arquivos Protegidos
```gitignore
# Arquivos de segurança - NUNCA COMMITAR
.env.secure
.env.local
admin_credentials.txt
security_keys.txt
*.key
*.pem
```

## Performance e Otimização

### 1. Compressão de Assets
- **Script automático**: minifica CSS/JS
- **Compressão Gzip**: 60-70% redução
- **Cache headers**: 1 ano para assets estáticos
- **Flask-Compress**: compressão HTTP automática

### 2. Lazy Loading
- **Intersection Observer**: detecção eficiente
- **Placeholder SVG**: leve enquanto carrega
- **Fallback**: para navegadores antigos
- **Pré-carregamento**: 50px antes da imagem

### 3. Otimizações de Banco
- **Índices estratégicos**: 70-85% melhoria
- **Cache de estatísticas**: TTL 5 minutos
- **Paginação**: 50 registros por página
- **Queries otimizadas**: LIMIT/OFFSET

## Deploy e Configuração

### 1. Variáveis de Ambiente (Railway)
```bash
RAILWAY_ENVIRONMENT=true
ADMIN_PASSWORD=<senha_segura_gerada>
ENCRYPTION_KEY=<chave_criptografia>
SECURITY_SALT=<salt_personalizado>
SECRET_KEY=<chave_sessao>
DATABASE_URL=<configurada_automaticamente>
```

### 2. Deploy Automático
- **Git push** → Deploy automático no Railway
- **Migrações** automáticas de banco
- **Inicialização** de tabelas e usuário admin
- **Compressão** automática de assets

### 3. Monitoramento
- **Logs detalhados** em nível DEBUG
- **Rastreamento de erros** com traceback
- **Monitoramento de performance** via auditoria
- **Estatísticas em tempo real** no dashboard

---

**Documentação atualizada em:** 2025-10-07
**Versão do sistema:** Arquitetura de Blueprints - 98.7% redução de código
**Status de segurança:** Vulnerabilidades críticas corrigidas
**Arquitetura:** 7 blueprints especializados + orquestrador principal
