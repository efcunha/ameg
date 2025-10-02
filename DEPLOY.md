# Guia de Deploy - Sistema AMEG

## 🚀 Deploy com Docker (Recomendado)

### Pré-requisitos
- Docker e Docker Compose instalados
- Porta 80 disponível

### Deploy Rápido
```bash
# 1. Configurar ambiente
cp .env.example .env
# Edite o .env com suas configurações

# 2. Deploy automático
./deploy.sh
```

### Configuração Manual
```bash
# 1. Criar diretórios
mkdir -p data/uploads/saude

# 2. Configurar variáveis
cp .env.example .env
# Edite SECRET_KEY no .env

# 3. Iniciar aplicação
docker-compose up -d

# 4. Verificar status
docker-compose ps
```

## 🖥️ Deploy Tradicional (VPS/Servidor)

### Instalação
```bash
# 1. Instalar Python e dependências
sudo apt update
sudo apt install python3 python3-pip python3-venv nginx

# 2. Clonar projeto
git clone <seu-repositorio>
cd ameg

# 3. Configurar ambiente virtual
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Configurar banco
python -c "from app import init_db; init_db()"

# 5. Iniciar com Gunicorn
gunicorn --bind 0.0.0.0:5000 wsgi:app
```

### Configuração Nginx
```nginx
server {
    listen 80;
    server_name seu-dominio.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🔧 Configurações de Produção

### Variáveis de Ambiente (.env)
```bash
SECRET_KEY=sua-chave-secreta-super-forte
DATABASE_PATH=/app/data/ameg.db
UPLOAD_FOLDER=/app/data/uploads/saude
FLASK_ENV=production
```

### Segurança
- ✅ Altere SECRET_KEY
- ✅ Use HTTPS em produção
- ✅ Configure firewall
- ✅ Backup regular do banco

## 📊 Monitoramento

### Logs
```bash
# Docker
docker-compose logs -f

# Tradicional
tail -f /var/log/nginx/access.log
```

### Comandos Úteis
```bash
# Parar aplicação
docker-compose down

# Reiniciar
docker-compose restart

# Backup do banco
docker-compose exec ameg-app cp /app/data/ameg.db /app/data/backup-$(date +%Y%m%d).db
```

## 🆘 Troubleshooting

### Problemas Comuns
1. **Porta 80 ocupada**: Altere porta no docker-compose.yml
2. **Permissões**: Verifique ownership dos diretórios
3. **Banco não criado**: Execute `init_db()` manualmente

### Verificação de Saúde
```bash
curl http://localhost/
# Deve retornar página de login
```
