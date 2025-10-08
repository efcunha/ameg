# API REST - Sistema AMEG

API REST segura para integração com o sistema de cadastros da AMEG.

## 🔐 Configuração e Ativação

### **Variáveis de Ambiente**
```bash
# Railway - Adicionar estas variáveis
API_ENABLED=true                    # Habilitar API (padrão: false)
API_SECRET_KEY=<chave_jwt_segura>   # Chave para JWT
API_MASTER_KEY=<chave_mestre>       # Chave para gerar tokens
```

### **Ativação Segura**
1. **Desenvolvimento**: Adicionar no `.env.secure`
2. **Produção**: Configurar no Railway Dashboard
3. **Rollback**: Mudar `API_ENABLED=false` (sem downtime)

## 🚀 Endpoints Disponíveis

### **Base URL**
- **Local**: `http://localhost:5000/api/v1`
- **Produção**: `https://ameg-production-013f.up.railway.app/api/v1`

### **1. Health Check**
```http
GET /api/v1/health
```
**Resposta:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-08T13:36:54.185Z",
  "version": "1.0.0"
}
```

### **2. Gerar Token JWT**
```http
POST /api/v1/token
Content-Type: application/json

{
  "api_key": "sua_api_master_key"
}
```
**Resposta:**
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### **3. Listar Cadastros**
```http
GET /api/v1/cadastros?page=1&per_page=50
Authorization: Bearer <token>
```
**Parâmetros:**
- `page`: Página (padrão: 1)
- `per_page`: Registros por página (máximo: 100)

**Resposta:**
```json
{
  "cadastros": [
    {
      "id": 1,
      "nome_completo": "João Silva",
      "cpf": "123.456.789-00",
      "telefone": "(83) 99999-9999",
      "data_cadastro": "2025-10-08T10:30:00",
      "endereco": "Rua das Flores, 123",
      "bairro": "Centro",
      "cep": "58000-000"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 150,
    "pages": 3
  }
}
```

### **4. Obter Cadastro Específico**
```http
GET /api/v1/cadastros/123
Authorization: Bearer <token>
```
**Resposta:**
```json
{
  "cadastro": {
    "id": 123,
    "nome_completo": "João Silva",
    "cpf": "123.456.789-00",
    "rg": "1234567",
    "telefone": "(83) 99999-9999",
    "data_nascimento": "1980-01-01",
    "endereco": "Rua das Flores, 123",
    "bairro": "Centro",
    "cep": "58000-000",
    "tem_doenca_cronica": "Não",
    "trabalho_tipo": "Ambulante",
    "renda_individual": "1500.00"
  }
}
```

### **5. Estatísticas do Sistema**
```http
GET /api/v1/stats
Authorization: Bearer <token>
```
**Resposta:**
```json
{
  "total_cadastros": 150,
  "cadastros_por_mes": [
    {"mes": "2025-10-01T00:00:00", "total": 25},
    {"mes": "2025-09-01T00:00:00", "total": 30}
  ],
  "saude": {
    "com_doenca_cronica": 45,
    "percentual_doenca_cronica": 30.0
  }
}
```

## 🔒 Autenticação

### **Fluxo de Autenticação**
1. **Obter Token**: POST `/api/v1/token` com `api_key`
2. **Usar Token**: Header `Authorization: Bearer <token>`
3. **Token Expira**: 24 horas (renovar conforme necessário)

### **Exemplo com cURL**
```bash
# 1. Gerar token
curl -X POST https://ameg-production-013f.up.railway.app/api/v1/token \
  -H "Content-Type: application/json" \
  -d '{"api_key": "sua_master_key"}'

# 2. Usar token
curl -X GET https://ameg-production-013f.up.railway.app/api/v1/cadastros \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

## 🛡️ Segurança Implementada

### **Proteções**
- ✅ **Autenticação JWT** com expiração de 24h
- ✅ **API Key mestre** para gerar tokens
- ✅ **Rate limiting** implícito via JWT
- ✅ **Dados sensíveis** removidos (foto_base64)
- ✅ **Validação de entrada** em todos os endpoints
- ✅ **Logs de acesso** automáticos

### **Limitações de Segurança**
- **Apenas leitura** - sem endpoints de escrita
- **Paginação obrigatória** - máximo 100 registros
- **Sem dados de foto** - removidos para performance
- **Token único** - um token por API key

## 📊 Casos de Uso

### **Integração com Sistemas Externos**
```javascript
// Exemplo em JavaScript
const API_BASE = 'https://ameg-production-013f.up.railway.app/api/v1';
let token = null;

async function getToken() {
  const response = await fetch(`${API_BASE}/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ api_key: 'sua_master_key' })
  });
  const data = await response.json();
  token = data.token;
}

async function getCadastros(page = 1) {
  const response = await fetch(`${API_BASE}/cadastros?page=${page}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return await response.json();
}
```

### **Aplicativo Mobile**
- Sincronização de dados offline
- Consulta de cadastros em campo
- Estatísticas em tempo real

### **Relatórios Automatizados**
- Integração com Power BI
- Dashboards externos
- Análises personalizadas

## 🚀 Ativação Passo a Passo

### **1. Gerar Chaves Seguras**
```bash
# Gerar API_SECRET_KEY (32 bytes)
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Gerar API_MASTER_KEY (32 bytes)  
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### **2. Configurar no Railway**
```bash
# Adicionar variáveis no Railway Dashboard
API_ENABLED=true
API_SECRET_KEY=<chave_gerada_1>
API_MASTER_KEY=<chave_gerada_2>
```

### **3. Deploy Automático**
```bash
git add .
git commit -m "Add API REST with JWT authentication"
git push origin main
```

### **4. Testar API**
```bash
# Health check (sem autenticação)
curl https://ameg-production-013f.up.railway.app/api/v1/health

# Gerar token
curl -X POST https://ameg-production-013f.up.railway.app/api/v1/token \
  -H "Content-Type: application/json" \
  -d '{"api_key": "sua_master_key"}'
```

## 🔄 Rollback e Manutenção

### **Desabilitar API (Zero Downtime)**
```bash
# No Railway Dashboard
API_ENABLED=false
```

### **Logs e Monitoramento**
- Logs automáticos no Railway
- Health check em `/api/v1/health`
- Métricas de uso via JWT

## 📈 Próximas Melhorias

### **Fase 2 - Rate Limiting**
- Implementar Flask-Limiter
- Limites por IP e por token
- Throttling inteligente

### **Fase 3 - Endpoints de Escrita**
- POST/PUT/DELETE com validação
- Auditoria de mudanças via API
- Webhooks para notificações

### **Fase 4 - Documentação Interativa**
- Swagger/OpenAPI
- Playground da API
- SDKs para linguagens populares

---

**API REST AMEG** - Integração segura e performática para o sistema de cadastros da Associação dos Ambulantes e Trabalhadores em Geral da Paraíba.
