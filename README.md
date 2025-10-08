# Sistema de Cadastro AMEG

Sistema web completo para cadastro familiar da Associação dos Ambulantes e Trabalhadores em Geral da Paraíba com funcionalidades avançadas de auditoria, segurança e performance.

## 🚀 Funcionalidades Principais

### **Autenticação e Segurança**
- **Login seguro** com hash de senhas PBKDF2 + salt personalizado
- **Proteção admin ID 1** - apenas eles podem modificar própria senha
- **Sistema de auditoria completo** - rastreamento de todas as ações
- **Validação de senhas** - 8 caracteres mínimo, maiúscula/minúscula/número
- **Criptografia avançada** - dados sensíveis protegidos com Fernet
- **Headers de segurança** - proteção contra XSS, clickjacking, MIME sniffing

### **Gestão de Cadastros**
- **Formulário completo** baseado no documento oficial AMEG (58 campos)
- **Captura de foto 3x4** via webcam com API getUserMedia ou upload
- **Validação unificada** - sistema centralizado em JavaScript
- **Edição completa** - todos os campos editáveis
- **Proteção de dados** - validação de limites e sanitização

### **Sistema de Relatórios Avançado**
- **6 tipos de relatórios** especializados
- **Fichas individuais completas** - PDFs com todos os dados + foto 3x4
- **Exportação múltipla** - CSV, PDF, DOC
- **Formatação otimizada** - Orientação paisagem para relatório de saúde
- **Paginação otimizada** - 50 registros por página
- **Filtros avançados** - busca e ordenação
- **Estatísticas em tempo real** - dashboard com métricas

### **Gestão de Arquivos de Saúde**
- **Upload seguro** - laudos, receitas, exames (16MB máximo)
- **Múltiplos formatos** - PDF, DOC, DOCX, imagens
- **Download protegido** - controle de acesso
- **Organização por cadastro** - arquivos vinculados

### **Administração Avançada**
- **Gestão de usuários** - criação, edição, exclusão
- **Sistema de auditoria** - log completo de ações
- **Reset administrativo** - limpeza completa do sistema
- **Proteções especiais** - admin ID 1 não pode ser removido/rebaixado

### **Performance e Otimização**
- **Compressão automática** - CSS/JS minificados + Gzip (60-70% redução)
- **Lazy loading** - carregamento inteligente de imagens
- **Cache de estatísticas** - TTL de 5 minutos
- **Índices de banco** - queries 70-85% mais rápidas
- **Flask-Compress** - compressão HTTP automática

## 🛠️ Como Usar

### **1. Desenvolvimento Local**
```bash
cd /home/efcunha/GitHub/ameg
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

### **2. Gerar Credenciais Seguras**
```bash
python3 generate_admin_credentials.py
```

### **3. Deploy no Railway**
```bash
git add .
git commit -m "Deploy updates"
git push origin main
```

## 🔐 Acesso ao Sistema

### **Local**
- **URL**: http://localhost:5000
- **Usuário**: `admin`
- **Senha**: Gerada pelo script de credenciais

### **Railway (Produção)**
- **URL**: https://ameg-production-013f.up.railway.app/
- **Usuário**: `admin`
- **Senha**: Configurada via variáveis de ambiente

## 📁 Estrutura Completa do Projeto

```
ameg/
├── app.py                        # 🆕 Orquestrador principal (127 linhas)
├── database.py                   # Módulo PostgreSQL + security manager
├── security.py                   # Sistema de segurança avançado
├── generate_admin_credentials.py # Gerador de credenciais seguras
├── requirements.txt              # Dependências atualizadas (segurança)
├── SECURITY.md                   # Documentação de segurança
├── DOCUMENTACAO_APP.md           # Documentação técnica detalhada
├── SISTEMA_CAIXA.md              # Documentação do sistema financeiro
├── ANALISE_SEGURANCA.md          # Análise completa de segurança
├── ANALISE_DOCUMENTACAO.md       # Análise da documentação
├── Dockerfile                    # Container para Railway
├── start.sh                      # Script de inicialização
├── railway.toml                  # Configuração Railway
├── .env.secure                   # Credenciais locais (não commitado)
├── .env.example                  # Exemplo de configuração
├── .gitignore                    # Arquivos protegidos
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
│   ├── login.html                # Login com validação
│   ├── dashboard.html            # Dashboard + lazy loading
│   ├── cadastrar.html            # Formulário + foto + validação
│   ├── editar_cadastro.html      # Edição completa
│   ├── relatorios.html           # Menu de relatórios
│   ├── tipos_relatorios.html     # 6 tipos de relatórios
│   ├── relatorio_*.html          # Relatórios especializados
│   ├── arquivos_*.html           # Gestão de arquivos
│   ├── usuarios.html             # Gestão de usuários
│   ├── criar_usuario.html        # Criação com validação
│   ├── editar_usuario.html       # Edição de usuários
│   ├── auditoria.html            # Sistema de auditoria
│   ├── admin_reset.html          # Reset administrativo
│   ├── caixa.html                # Sistema de caixa
│   └── ficha.html                # Ficha individual completa
├── static/                       # Arquivos estáticos otimizados
│   ├── css/
│   │   ├── mobile.css            # Estilos responsivos
│   │   ├── mobile.min.css        # Versão minificada
│   │   └── mobile.min.css.gz     # Versão comprimida
│   ├── js/
│   │   ├── validators.js         # Validação unificada
│   │   ├── validators.min.js     # Versão minificada
│   │   ├── lazy-load.js          # Lazy loading inteligente
│   │   ├── lazy-load.min.js      # Versão minificada
│   │   └── *.gz                  # Arquivos comprimidos
│   └── img/
│       └── logo-ameg.jpeg        # Logo da AMEG
├── data/                         # Uploads e dados
└── imagens/                      # Recursos do projeto
```

## 🗄️ Banco de Dados

### **Produção (PostgreSQL - Railway)**
- **Inicialização automática** no primeiro deploy
- **Persistência garantida** e backup automático
- **Performance otimizada** com índices

### **Tabelas Principais**
- **`usuarios`**: Controle de acesso com tipos (admin/usuario)
- **`cadastros`**: 58 campos + foto_base64 + índices otimizados
- **`arquivos_saude`**: Arquivos médicos com metadados
- **`auditoria`**: Log completo de todas as ações do sistema

### **Índices de Performance**
```sql
-- Índices para queries 70-85% mais rápidas
CREATE INDEX idx_cadastros_cpf ON cadastros(cpf);
CREATE INDEX idx_cadastros_nome ON cadastros(nome_completo);
CREATE INDEX idx_cadastros_data ON cadastros(data_cadastro);
CREATE INDEX idx_auditoria_usuario ON auditoria(usuario);
CREATE INDEX idx_auditoria_data ON auditoria(data_acao);
CREATE INDEX idx_arquivos_cadastro ON arquivos_saude(cadastro_id);
```

## 🚀 Deploy e Configuração

### **Variáveis de Ambiente (Railway)**
```bash
RAILWAY_ENVIRONMENT=true
ADMIN_PASSWORD=<senha_segura_gerada>
ENCRYPTION_KEY=<chave_criptografia>
SECURITY_SALT=<salt_personalizado>
SECRET_KEY=<chave_sessao>
DATABASE_URL=<configurada_automaticamente>
```

### **Deploy Automático**
- **Git push** → Deploy automático no Railway
- **Migrações** automáticas de banco
- **Inicialização** de tabelas e usuário admin
- **Compressão** automática de assets

## 📊 Campos do Cadastro (58 + Foto)

### **Dados Pessoais**
- Foto 3x4 (webcam ou upload)
- Nome completo, CPF, RG, telefone
- Endereço completo, bairro, CEP

### **Dados Familiares**
- Companheiro(a), filhos, dependentes
- Renda familiar, benefícios sociais

### **Dados Habitacionais**
- Tipo de moradia, energia, água, esgoto
- Condições de habitação

### **Dados de Saúde**
- Doenças crônicas, medicamentos
- Deficiências, necessidades especiais
- Upload de laudos e receitas

### **Dados de Trabalho**
- Tipo de trabalho, local, condições
- Renda individual, benefícios

## 🔒 Segurança Implementada

### **Proteção de Senhas**
- **Hash PBKDF2** com salt personalizado
- **Criptografia Fernet** para dados sensíveis
- **Geração automática** de senhas seguras
- **Admin ID 1 protegido** contra alterações

### **Sistema de Auditoria**
- **Log completo** de INSERT, UPDATE, DELETE, LOGIN
- **Rastreamento** de usuário, IP, user-agent
- **Dados anteriores/novos** para comparação
- **Interface administrativa** para consulta

### **Validações e Proteções**
- **Headers de segurança** (XSS, clickjacking, MIME)
- **Validação unificada** frontend/backend
- **Upload seguro** com validação de tipos
- **Proteção CSRF** via Flask sessions

## 🚀 Performance e Otimização

### **Fase 1 - Otimizações Críticas**
- ✅ **Índices de banco** - 70-85% melhoria em queries
- ✅ **Cache de estatísticas** - TTL 5 minutos
- ✅ **Paginação** - 50 registros por página
- ✅ **Queries otimizadas** - LIMIT/OFFSET

### **Fase 2 - Compressão e Loading**
- ✅ **Compressão CSS/JS** - 60-70% redução de tamanho
- ✅ **Lazy loading** - carregamento inteligente de imagens
- ✅ **Flask-Compress** - compressão HTTP automática
- ✅ **Cache headers** - 1 ano para assets estáticos

### **Resultados Obtidos**
- **Queries**: 70-85% mais rápidas
- **Assets**: 60-70% menores
- **Loading**: Carregamento progressivo
- **Cache**: Redução de carga no servidor

## 🧪 Testes e Qualidade

### **Testes Automatizados**
```bash
./testar.sh
```

### **Cobertura Completa**
- ✅ Estrutura de arquivos
- ✅ Conexão com banco de dados
- ✅ Templates HTML válidos
- ✅ Sistema de autenticação
- ✅ Todas as rotas da aplicação
- ✅ Integração end-to-end

## 🛠️ Tecnologias e Dependências

### **Backend**
- **Flask 3.0.3** - Framework web
- **Flask-Compress 1.15** - Compressão HTTP
- **Werkzeug 3.1.3** - Utilitários web (atualizado por segurança)
- **psycopg2-binary 2.9.9** - Driver PostgreSQL
- **cryptography 44.0.0** - Criptografia (atualizado por segurança)

### **Frontend**
- **HTML5/CSS3/JavaScript** - Interface responsiva
- **Lazy Loading** - Carregamento inteligente
- **Validação unificada** - Sistema centralizado
- **Compressão automática** - Assets otimizados

### **Segurança**
- **Jinja2 3.1.5** - Templates (atualizado por segurança)
- **PBKDF2 + Salt** - Hash de senhas
- **Fernet** - Criptografia simétrica
- **Headers de segurança** - Proteções HTTP

### **Documentos e Relatórios**
- **ReportLab 4.2.5** - Geração de PDFs
- **python-docx 1.1.2** - Documentos Word
- **CSV nativo** - Exportação de dados

### **Deploy e Produção**
- **Railway** - Plataforma de deploy
- **PostgreSQL** - Banco de dados
- **Gunicorn 23.0.0** - Servidor WSGI
- **Docker** - Containerização

## 📚 Documentação Adicional

- **SECURITY.md** - Guia completo de segurança
- **DOCUMENTACAO_APP.md** - Documentação técnica detalhada
- **Comentários no código** - Documentação inline
- **README.md** - Este arquivo (visão geral)

## 🔄 Atualizações Recentes

### **Melhorias nos Relatórios (Outubro 2025)**
- **Fichas individuais completas**: Relatórios completos e estatísticos agora geram PDFs com fichas completas incluindo foto 3x4
- **Formatação otimizada**: Correção de sobreposição de texto e ajuste de larguras de colunas
- **Orientação paisagem**: Relatório de saúde usa layout paisagem para melhor legibilidade
- **Campos corrigidos**: Uso de campos reais da tabela (casa_tipo, energia, agua, esgoto, etc.)
- **Dados de saúde precisos**: Correção para usar campos corretos (tem_doenca_cronica, doencas_cronicas, etc.)

### **Arquitetura de Blueprints**
- Migração completa para arquitetura modular
- App.py reduzido de 3.900+ para 127 linhas (96.7% redução)
- 7 blueprints especializados implementados
- Preservação de 100% das funcionalidades (42→43 rotas)
- Limpeza de arquivos não utilizados

### **Segurança**
- Correção de vulnerabilidades Jinja2 e Cryptography
- Implementação de Security Manager
- Proteção avançada da senha do admin
- Sistema de auditoria completo

### **Performance**
- Compressão automática de assets
- Lazy loading de imagens
- Cache de estatísticas
- Índices de banco otimizados

## 🎯 Próximos Passos

### **Fase 3 - Funcionalidades Avançadas**
- [ ] Dashboard com gráficos interativos
- [ ] Notificações em tempo real
- [ ] API REST para integração
- [ ] Backup automático de arquivos

### **Fase 4 - Escalabilidade**
- [ ] Cache Redis para sessões
- [ ] CDN para assets estáticos
- [ ] Load balancing
- [ ] Monitoramento avançado

---

**Sistema AMEG** - Desenvolvido com foco em segurança, performance e usabilidade para atender às necessidades da Associação dos Ambulantes e Trabalhadores em Geral da Paraíba.
