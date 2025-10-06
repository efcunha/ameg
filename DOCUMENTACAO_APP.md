# Documentação Detalhada - app.py

## Visão Geral
O arquivo `app.py` é o núcleo da aplicação AMEG, uma aplicação Flask que gerencia cadastros familiares para a Associação dos Ambulantes e Trabalhadores em Geral da Paraíba.

## Estrutura Geral

### 1. Importações e Configurações Iniciais
```python
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, send_from_directory
from database import get_db_connection, init_db_tables, create_admin_user
from psycopg2.extras import RealDictCursor
```

**Principais dependências:**
- **Flask**: Framework web principal
- **database**: Módulo customizado para conexão com PostgreSQL/SQLite
- **psycopg2**: Driver PostgreSQL
- **werkzeug**: Utilitários para segurança (hash de senhas, upload de arquivos)

### 2. Configuração da Aplicação
```python
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'ameg_secret_2024_fallback_key_change_in_production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB máximo para uploads
```

**Configurações importantes:**
- **SECRET_KEY**: Chave secreta para sessões (obtida de variável de ambiente)
- **MAX_CONTENT_LENGTH**: Limite de 16MB para uploads de arquivos
- **Logging**: Configurado em nível DEBUG para monitoramento detalhado

### 3. Inicialização do Banco de Dados
```python
if os.environ.get('RAILWAY_ENVIRONMENT'):
    init_db_tables()
    create_admin_user()
```

**Comportamento:**
- **Railway (Produção)**: Inicializa tabelas e cria usuário admin automaticamente
- **Local**: Usa configuração manual do banco

## Funções Utilitárias

### 1. `is_admin_user(username)`
**Propósito**: Verifica se um usuário tem privilégios administrativos
**Retorno**: Boolean
**Uso**: Controle de acesso a funcionalidades administrativas

### 2. `validate_field_lengths(form_data)`
**Propósito**: Valida se os campos do formulário não excedem os limites da tabela
**Parâmetros**: Dados do formulário
**Retorno**: Lista de erros de validação

### 3. `login_required(f)`
**Propósito**: Decorator para proteger rotas que requerem autenticação
**Uso**: `@login_required` antes de funções de rota

### 4. `allowed_file(filename)`
**Propósito**: Verifica se o arquivo tem extensão permitida
**Extensões permitidas**: pdf, png, jpg, jpeg, gif, doc, docx

## Limites de Campos (FIELD_LIMITS)
Dicionário que define os limites máximos de caracteres para cada campo do cadastro:

```python
FIELD_LIMITS = {
    'nome_completo': 255,
    'cpf': 14,
    'telefone': 20,
    'bairro': 100,
    # ... mais campos
}
```

## Rotas Principais

### 1. Autenticação

#### `GET /` e `GET /login`
- **Função**: Exibe página de login
- **Comportamento**: Redireciona para dashboard se já autenticado

#### `POST /login`
- **Função**: Processa login do usuário
- **Validação**: Verifica hash da senha com `check_password_hash()`
- **Sessão**: Armazena usuário na sessão Flask

#### `GET /logout`
- **Função**: Encerra sessão do usuário
- **Comportamento**: Remove dados da sessão e redireciona para login

### 2. Dashboard

#### `GET /dashboard`
- **Função**: Página principal após login
- **Dados exibidos**:
  - Total de cadastros
  - 5 últimos cadastros realizados
- **Proteção**: Requer autenticação

### 3. Gestão de Cadastros

#### `GET /cadastrar`
- **Função**: Exibe formulário de novo cadastro
- **Template**: `cadastrar.html`
- **Proteção**: Requer autenticação

#### `POST /cadastrar`
- **Função**: Processa novo cadastro
- **Validações**:
  - Limites de caracteres dos campos
  - Formato de CPF
  - Arquivos de saúde (opcional)
- **Comportamento**: Salva no banco e processa uploads

#### `GET /editar_cadastro/<int:id>`
- **Função**: Exibe formulário de edição
- **Parâmetros**: ID do cadastro
- **Dados**: Carrega dados existentes do banco

#### `POST /editar_cadastro/<int:id>`
- **Função**: Atualiza cadastro existente
- **Validações**: Mesmas do cadastro novo
- **Comportamento**: Atualiza registro no banco

#### `POST /deletar_cadastro/<int:id>`
- **Função**: Remove cadastro do sistema
- **Proteção**: Confirmação via JavaScript
- **Comportamento**: Delete em cascata (remove arquivos associados)

### 4. Relatórios

#### `GET /relatorios`
- **Função**: Menu principal de relatórios
- **Template**: `relatorios.html`

#### `GET /tipos_relatorios`
- **Função**: Tipos de relatórios disponíveis
- **Opções**:
  - Relatório Completo
  - Relatório Simplificado
  - Relatório por Bairro
  - Relatório de Renda
  - Relatório de Saúde
  - Relatório Estatístico

#### Relatórios Específicos:
- `GET /relatorio_completo`: Todos os dados dos cadastros
- `GET /relatorio_simplificado`: Dados básicos
- `GET /relatorio_por_bairro`: Agrupado por bairro
- `GET /relatorio_renda`: Análise de renda familiar
- `GET /relatorio_saude`: Dados de saúde e deficiências
- `GET /relatorio_estatistico`: Estatísticas e gráficos

### 5. Exportação de Dados

#### `GET /exportar`
- **Parâmetros**: `formato` (csv, pdf, doc)
- **Função**: Exporta dados em diferentes formatos
- **Formatos suportados**:
  - **CSV**: Arquivo de texto separado por vírgulas
  - **PDF**: Documento formatado com ReportLab
  - **DOC**: Documento Word

### 6. Gestão de Arquivos

#### `GET /arquivos_cadastros`
- **Função**: Lista todos os cadastros com seus arquivos
- **Dados exibidos**:
  - Nome do cadastrado
  - CPF
  - Quantidade de arquivos
  - Lista de arquivos de saúde

#### `GET /arquivos_saude/<int:cadastro_id>`
- **Função**: Lista arquivos de saúde de um cadastro específico
- **Parâmetros**: ID do cadastro
- **Dados**: Arquivos médicos, laudos, receitas

#### `POST /upload_arquivo_saude/<int:cadastro_id>`
- **Função**: Upload de arquivos médicos
- **Validações**:
  - Extensões permitidas
  - Tamanho máximo (16MB)
  - Nome seguro do arquivo
- **Armazenamento**: Pasta `data/` com nome único

#### `GET /download_arquivo/<int:arquivo_id>`
- **Função**: Download de arquivo específico
- **Proteção**: Verifica se arquivo existe
- **Comportamento**: Serve arquivo via Flask

#### `POST /deletar_arquivo/<int:arquivo_id>`
- **Função**: Remove arquivo do sistema
- **Comportamento**: 
  - Remove registro do banco
  - Remove arquivo físico do disco

### 7. Gestão de Usuários (Admin)

#### `GET /usuarios`
- **Função**: Lista todos os usuários do sistema
- **Proteção**: Apenas administradores
- **Dados**: Lista usuários com tipos e status

#### `GET /criar_usuario`
- **Função**: Formulário de criação de usuário
- **Proteção**: Apenas administradores

#### `POST /criar_usuario`
- **Função**: Cria novo usuário
- **Validações**:
  - Nome de usuário único
  - Senha forte
  - Tipo de usuário (admin/usuario)
- **Segurança**: Hash da senha com Werkzeug

#### `GET /editar_usuario/<int:user_id>`
- **Função**: Formulário de edição de usuário
- **Proteção**: Apenas administradores

#### `POST /editar_usuario/<int:user_id>`
- **Função**: Atualiza dados do usuário
- **Campos editáveis**:
  - Nome de usuário
  - Senha (opcional)
  - Tipo de usuário

#### `POST /deletar_usuario/<int:user_id>`
- **Função**: Remove usuário do sistema
- **Proteção**: Não permite deletar próprio usuário

### 8. Visualização Individual

#### `GET /ficha/<int:id>`
- **Função**: Exibe ficha completa de um cadastro
- **Dados exibidos**:
  - Todos os dados pessoais
  - Dados familiares
  - Dados habitacionais
  - Dados de saúde
  - Arquivos anexados
- **Template**: `ficha.html`

## Segurança Implementada

### 1. Headers de Segurança
```python
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
```

### 2. Proteção de Rotas
- Decorator `@login_required` em rotas sensíveis
- Verificação de privilégios administrativos
- Validação de sessão Flask

### 3. Upload Seguro
- Validação de extensões de arquivo
- Nomes de arquivo seguros com `secure_filename()`
- Limite de tamanho de arquivo (16MB)

### 4. Validação de Dados
- Validação de limites de caracteres
- Sanitização de entrada de dados
- Proteção contra SQL injection (uso de parâmetros)

## Tratamento de Erros

### 1. Logging Detalhado
- Logs em nível DEBUG para desenvolvimento
- Logs de erro com traceback completo
- Monitoramento de operações críticas

### 2. Fallbacks
- Fallback para usuário admin em caso de erro
- Continuação da aplicação mesmo com erros de inicialização
- Mensagens de erro amigáveis para usuários

## Estrutura de Dados

### 1. Sessão Flask
```python
session['usuario']  # Nome do usuário logado
```

### 2. Campos do Cadastro (57 campos)
- **Dados Pessoais**: nome, CPF, RG, telefone, endereço
- **Dados Familiares**: companheiro, filhos, renda
- **Dados Habitacionais**: tipo de casa, energia, água, esgoto
- **Dados de Saúde**: doenças, medicamentos, deficiências
- **Dados de Trabalho**: tipo, local, condições

### 3. Arquivos de Saúde
- **Tipos**: laudo, receita, exame, imagem
- **Metadados**: nome original, descrição, data upload
- **Armazenamento**: Pasta `data/` com nomes únicos

## Inicialização da Aplicação

### 1. Desenvolvimento Local
```bash
python app.py
```

### 2. Produção (Railway)
- Inicialização automática do banco
- Criação do usuário admin
- Configuração de variáveis de ambiente

## Dependências Principais

### 1. Flask e Extensões
- `Flask`: Framework web
- `werkzeug`: Utilitários de segurança

### 2. Banco de Dados
- `psycopg2-binary`: Driver PostgreSQL
- Módulo `database`: Abstração de conexão

### 3. Geração de Documentos
- `reportlab`: Geração de PDFs
- `python-docx`: Geração de documentos Word

### 4. Utilitários
- `csv`: Exportação CSV
- `datetime`: Manipulação de datas
- `os`: Variáveis de ambiente
- `logging`: Sistema de logs

## Considerações de Performance

### 1. Conexões de Banco
- Conexões abertas e fechadas por requisição
- Uso de cursors apropriados (RealDictCursor para dados estruturados)

### 2. Upload de Arquivos
- Limite de 16MB por arquivo
- Armazenamento em disco local
- Nomes únicos para evitar conflitos

### 3. Consultas Otimizadas
- JOINs para buscar dados relacionados
- LIMITs em consultas de listagem
- Índices implícitos em chaves primárias

## Manutenção e Monitoramento

### 1. Logs
- Logs detalhados de operações
- Rastreamento de erros
- Monitoramento de performance

### 2. Backup
- Dados no PostgreSQL (Railway)
- Arquivos na pasta `data/`
- Configurações em variáveis de ambiente

### 3. Atualizações
- Deploy automático via Git push
- Migrações de banco automáticas
- Compatibilidade com versões anteriores
