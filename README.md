# Sistema de Cadastro AMEG

Sistema web para cadastro familiar da Associação dos Ambulantes e Trabalhadores em Geral da Paraíba.

## Funcionalidades

- **Autenticação**: Login com usuário e senha
- **Dashboard**: Visão geral dos cadastros
- **Cadastro**: Formulário completo baseado no documento AMEG
- **Relatórios**: Listagem e estatísticas dos cadastrados
- **Exportação**: Download dos dados em CSV

## Como usar

1. **Testar o sistema (recomendado):**
```bash
cd /home/efcunha/GitHub/ameg
./testar.sh
```

2. **Iniciar o sistema:**
```bash
cd /home/efcunha/GitHub/ameg
source venv/bin/activate
python run.py
```

3. **Acessar o sistema:**
- URL: http://localhost:5000
- Usuário: `admin`
- Senha: `admin123`

## Estrutura do Projeto

```
ameg/
├── app.py              # Aplicação principal Flask
├── run.py              # Script para iniciar o servidor
├── test_ameg.py        # Testes automatizados
├── testar.sh           # Script executável para testes
├── ameg.db             # Banco de dados SQLite (criado automaticamente)
├── templates/          # Templates HTML
│   ├── login.html
│   ├── dashboard.html
│   ├── cadastrar.html
│   ├── relatorios.html
│   └── relatorio_saude.html
├── uploads/saude/      # Arquivos de saúde enviados
└── venv/               # Ambiente virtual Python
```

## Campos do Cadastro

- Nome completo
- Endereço e bairro
- Telefone
- Gênero e idade
- CPF, RG, data de nascimento
- Estado civil
- Profissão
- Renda familiar
- Número de pessoas na família
- **Dados de Saúde**: Doenças crônicas, medicamentos, deficiências
- **Upload de Arquivos**: Laudos médicos, receitas, imagens

## Banco de Dados

O sistema usa SQLite com três tabelas:
- `usuarios`: Controle de acesso
- `cadastros`: Dados dos cadastrados
- `arquivos_saude`: Arquivos médicos enviados

## Testes Automatizados

O sistema inclui uma suíte completa de testes automatizados:

### Executar Testes
```bash
# Método mais simples
./testar.sh

# Ou manualmente
source venv/bin/activate
python test_ameg.py
```

### Testes Incluídos
- ✅ Estrutura de arquivos
- ✅ Banco de dados SQLite
- ✅ Templates HTML
- ✅ Sistema de autenticação
- ✅ Rotas da aplicação
- ✅ Integração completa

### Resultado dos Testes
- Taxa de sucesso: 100%
- 8 testes automatizados
- Validação completa do sistema

## Deploy em Produção

### Deploy Rápido com Docker
```bash
# 1. Configurar ambiente
cp .env.example .env
# Edite o SECRET_KEY no arquivo .env

# 2. Deploy automático
./deploy.sh

# 3. Acessar aplicação
# http://localhost (ou seu domínio)
```

### Deploy Manual
Consulte o arquivo [DEPLOY.md](DEPLOY.md) para instruções detalhadas.

## Relatórios

- Total de cadastros
- Renda média familiar
- Listagem completa
- Exportação para CSV
