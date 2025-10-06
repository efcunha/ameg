# Sistema de Cadastro AMEG

Sistema web para cadastro familiar da Associação dos Ambulantes e Trabalhadores em Geral da Paraíba.

## Funcionalidades

- **Autenticação**: Login com usuário e senha
- **Dashboard**: Visão geral dos cadastros
- **Cadastro**: Formulário completo baseado no documento AMEG
- **Relatórios**: Listagem e estatísticas dos cadastrados
- **Exportação**: Download dos dados em CSV
- **Deploy**: Suporte para Railway com PostgreSQL

## Como usar

### 1. Desenvolvimento Local
```bash
cd /home/efcunha/GitHub/ameg
python app.py
```

### 2. Produção Local
```bash
cd /home/efcunha/GitHub/ameg
python app.py
```

### 3. Deploy no Railway
```bash
cd /home/efcunha/GitHub/ameg
git add .
git commit -m "Deploy updates"
git push
```

## Acesso ao Sistema

### Local
- **URL**: http://localhost:5000
- **Usuário**: `admin`
- **Senha**: `admin123`

### Railway (Produção)
- **URL**: https://ameg-production-013f.up.railway.app/
- **Usuário**: `admin`
- **Senha**: `Admin@2024!Secure`

## Estrutura do Projeto

```
ameg/
├── app.py                    # Aplicação principal Flask
├── database.py               # Módulo de banco PostgreSQL/SQLite
├── config.py                 # Configurações por ambiente
├── reset_counter.py          # Script para zerar contador do banco
├── requirements.txt          # Dependências Python
├── Dockerfile                # Dockerfile para Railway
├── start.sh                  # Script de inicialização
├── railway.toml              # Configuração Railway
├── railway.json              # Configuração Railway (legacy)
├── .railwayignore            # Arquivos ignorados no deploy
├── .dockerignore             # Arquivos ignorados no Docker
├── .env.example              # Exemplo de variáveis de ambiente
├── .gitignore                # Arquivos ignorados no Git
├── templates/                # Templates HTML
│   ├── login.html            # Página de login
│   ├── dashboard.html        # Dashboard principal
│   ├── cadastrar.html        # Formulário de cadastro
│   ├── editar_cadastro.html  # Edição de cadastros
│   ├── relatorios.html       # Menu de relatórios
│   ├── tipos_relatorios.html # Tipos de relatórios
│   ├── relatorio_*.html      # Diversos relatórios
│   ├── arquivos_*.html       # Gestão de arquivos
│   ├── usuarios.html         # Gestão de usuários
│   ├── criar_usuario.html    # Criação de usuários
│   ├── editar_usuario.html   # Edição de usuários
│   └── ficha.html            # Ficha individual
├── static/                   # Arquivos estáticos
│   ├── css/
│   │   └── mobile.css        # Estilos responsivos
│   └── img/
│       └── logo-ameg.jpeg    # Logo da AMEG
├── imagens/                  # Imagens do projeto
│   └── LOGO AMEG.jpeg        # Logo original
├── data/                     # Dados e uploads
├── __pycache__/              # Cache Python
└── .git/                     # Controle de versão Git
```

## Banco de Dados

### Local (SQLite)
- Arquivo: `ameg.db`
- Criado automaticamente

### Produção (PostgreSQL)
- Railway PostgreSQL
- Inicializado automaticamente no primeiro deploy
- Persistente e confiável

### Tabelas
- `usuarios`: Controle de acesso
- `cadastros`: Dados completos dos cadastrados (57 campos)
- `arquivos_saude`: Arquivos médicos enviados

## Deploy no Railway

### Pré-requisitos
```bash
npm install -g @railway/cli
railway login
```

### Deploy Automático
```bash
git add .
git commit -m "Deploy updates"
git push
```

### Variáveis de Ambiente (Railway)
- `RAILWAY_ENVIRONMENT=true`
- `ADMIN_PASSWORD=Admin@2024!Secure`
- `SECRET_KEY=<gerada-automaticamente>`
- `DATABASE_URL=<configurada-automaticamente>`

## Campos do Cadastro

- Dados pessoais: Nome, endereço, telefone, CPF, RG
- Dados familiares: Companheiro, filhos, renda
- Dados habitacionais: Casa, energia, água, esgoto
- **Dados de Saúde**: Doenças, medicamentos, deficiências
- **Upload de Arquivos**: Laudos médicos, receitas

## Testes Automatizados

```bash
./testar.sh
```

### Cobertura
- ✅ Estrutura de arquivos
- ✅ Banco de dados
- ✅ Templates HTML
- ✅ Autenticação
- ✅ Rotas da aplicação
- ✅ Integração completa

## Tecnologias

- **Backend**: Flask (Python)
- **Banco Local**: SQLite
- **Banco Produção**: PostgreSQL (Railway)
- **Deploy**: Railway com auto-deploy
- **Frontend**: HTML/CSS/JavaScript
- **Dependências**: psycopg2-binary, gunicorn, reportlab
