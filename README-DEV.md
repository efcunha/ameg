# 🐳 Desenvolvimento Local - AMEG Blueprints

Ambiente Docker para testar e debugar a versão blueprints localmente.

## 🚀 Como usar

### **Iniciar ambiente**
```bash
./dev-local.sh
```

### **Parar ambiente**
```bash
./dev-stop.sh
```

### **Acesso**
- **Aplicação**: http://localhost:5000
- **PostgreSQL**: localhost:5432
- **Usuário**: admin
- **Senha**: admin123

## 🔧 Estrutura

### **Containers**
- **ameg_postgres**: PostgreSQL 15 com dados persistentes
- **ameg_app**: Aplicação Flask com blueprints

### **Volumes**
- **postgres_data**: Dados do PostgreSQL persistem entre reinicializações
- **Código**: Montado como volume para hot-reload

## 🛠️ Debug

### **Ver logs**
```bash
docker-compose logs -f app
```

### **Acessar container**
```bash
docker exec -it ameg_app bash
```

### **Conectar no PostgreSQL**
```bash
docker exec -it ameg_postgres psql -U ameg_user -d ameg_local
```

## 📝 Variáveis de Ambiente

- `DATABASE_URL`: postgresql://ameg_user:ameg_password@postgres:5432/ameg_local
- `FLASK_ENV`: development
- `FLASK_DEBUG`: 1
- `ADMIN_PASSWORD`: admin123

## 🔄 Workflow

1. **Edite os blueprints** na pasta `blueprints/`
2. **Salve o arquivo** - hot-reload automático
3. **Teste no navegador**: http://localhost:5000
4. **Veja logs** em tempo real
5. **Debug** conforme necessário

## 🗄️ Banco de Dados

- **Inicialização automática** na primeira execução
- **Dados persistentes** em volume Docker
- **Reset**: `docker-compose down -v` (remove dados)

## ✅ Vantagens

- ✅ **Isolamento**: Não interfere com produção
- ✅ **Consistência**: Mesmo ambiente para todos
- ✅ **Debug**: Logs detalhados e acesso direto
- ✅ **Hot-reload**: Mudanças refletem automaticamente
- ✅ **PostgreSQL**: Mesmo banco da produção
