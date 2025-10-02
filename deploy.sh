#!/bin/bash

echo "🚀 Deploy AMEG - Container Único"

# Criar diretórios necessários
mkdir -p data/uploads/saude

# Copiar arquivo de ambiente se não existir
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "⚠️  Arquivo .env criado. CONFIGURE AS VARIÁVEIS antes de continuar!"
    exit 1
fi

# Parar containers existentes
docker-compose down

# Construir e iniciar
docker-compose up --build -d

echo "✅ Deploy concluído!"
echo "📱 Acesse: http://localhost"
