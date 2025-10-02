#!/bin/bash

IMAGE_NAME="efcunha/ameg"
VERSION="latest"

echo "🚀 Deploy AMEG"

# Verificar se deve fazer build local ou usar imagem do Docker Hub
if [ "$1" = "--publish" ]; then
    echo "🔨 Fazendo build e publicando no Docker Hub..."
    docker build -t $IMAGE_NAME:$VERSION .
    docker login
    docker push $IMAGE_NAME:$VERSION
    echo "✅ Imagem publicada: https://hub.docker.com/r/$IMAGE_NAME"
    exit 0
fi

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

# Verificar se deve usar imagem local ou do Docker Hub
if [ "$1" = "--hub" ]; then
    echo "📦 Usando imagem do Docker Hub..."
    sed -i 's/build: \./image: efcunha\/ameg:latest/' docker-compose.yml
    docker-compose pull
else
    echo "🔨 Fazendo build local..."
    sed -i 's/image: efcunha\/ameg:latest/build: ./' docker-compose.yml
    docker-compose build
fi

# Iniciar containers
docker-compose up -d

echo "✅ Deploy concluído!"
echo "📱 Acesse: http://localhost"
