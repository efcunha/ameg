#!/bin/bash
# Script de deploy para produção

echo "🚀 Iniciando deploy do Sistema AMEG..."

# Criar diretórios necessários
mkdir -p data/uploads/saude

# Copiar arquivo de ambiente se não existir
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "⚠️  Arquivo .env criado. CONFIGURE AS VARIÁVEIS antes de continuar!"
    echo "Edite o arquivo .env com suas configurações de produção."
    exit 1
fi

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não encontrado. Instale o Docker primeiro."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose não encontrado. Instale o Docker Compose primeiro."
    exit 1
fi

# Parar containers existentes
echo "🛑 Parando containers existentes..."
docker-compose down

# Construir e iniciar
echo "🔨 Construindo aplicação..."
docker-compose build

echo "🚀 Iniciando aplicação..."
docker-compose up -d

# Verificar status
echo "📊 Verificando status..."
docker-compose ps

echo ""
echo "✅ Deploy concluído!"
echo "🌐 Aplicação disponível em: http://localhost"
echo "📋 Para ver logs: docker-compose logs -f"
echo "🛑 Para parar: docker-compose down"
