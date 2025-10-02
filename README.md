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
├── ameg.db             # Banco de dados SQLite (criado automaticamente)
├── ameg.csv            # Arquivo CSV original
├── templates/          # Templates HTML
│   ├── login.html
│   ├── dashboard.html
│   ├── cadastrar.html
│   └── relatorios.html
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

## Banco de Dados

O sistema usa SQLite com duas tabelas:
- `usuarios`: Controle de acesso
- `cadastros`: Dados dos cadastrados

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

## Relatórios

- Total de cadastros
- Renda média familiar
- Listagem completa
- Exportação para CSV
