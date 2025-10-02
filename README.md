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
./testar.sh
```

### 2. Produção Local
```bash
cd /home/efcunha/GitHub/ameg
source venv/bin/activate
python run.py
```

### 3. Deploy no Railway
```bash
cd /home/efcunha/GitHub/ameg
./deploy-railway.sh
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
├── app.py                  # Aplicação principal Flask (corrigido)
├── run.py                  # Script para iniciar o servidor
├── database.py             # Módulo de banco PostgreSQL/SQLite
├── db_helper.py            # Helper para consultas híbridas
├── config.py               # Configurações por ambiente
├── test_ameg.py            # Testes automatizados
├── testar.sh               # Script executável para testes
├── deploy-railway.sh       # Script de deploy Railway
├── railway.json            # Configuração Railway
├── railway.dockerfile      # Dockerfile para Railway
├── requirements.txt        # Dependências Python (atualizado)
├── ameg.db                 # Banco SQLite (local)
├── templates/              # Templates HTML
├── uploads/saude/          # Arquivos de saúde enviados
└── venv/                   # Ambiente virtual Python
```

## Banco de Dados

### Local (SQLite)
- Arquivo: `ameg.db`
- Criado automaticamente

### Produção (PostgreSQL)
- Railway PostgreSQL
- Persistente e confiável
- Configurado automaticamente

### Tabelas
- `usuarios`: Controle de acesso
- `cadastros`: Dados dos cadastrados
- `arquivos_saude`: Arquivos médicos enviados

## Deploy no Railway

### Pré-requisitos
```bash
npm install -g @railway/cli
railway login
```

### Deploy Automático
```bash
./deploy-railway.sh
```

### Variáveis de Ambiente (Railway)
- `RAILWAY_ENVIRONMENT=true`
- `ADMIN_PASSWORD=Admin@2024!Secure`
- `SECRET_KEY=<gerada-automaticamente>`
- `DATABASE_URL=<configurada-automaticamente>`

## Campos do Cadastro

- Nome completo, endereço, telefone
- CPF, RG, data de nascimento
- Estado civil, profissão, renda
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
