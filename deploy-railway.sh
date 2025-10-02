#!/bin/bash

echo "🚂 Deploy AMEG no Railway"
echo ""
echo "⚠️  NOTA: Se houver problemas de timeout, use:"
echo "   1. Railway Dashboard: https://railway.app/dashboard"
echo "   2. Configure auto-deploy via GitHub"
echo ""

# Adicionar PATH do npm global
export PATH=$PATH:/home/efcunha/.npm-global/bin

# Verificar se railway CLI está instalado
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI não encontrado. Instale com:"
    echo "npm install -g @railway/cli"
    exit 1
fi

# Login no Railway (se necessário)
echo "🔑 Verificando login no Railway..."
if ! railway whoami &> /dev/null; then
    echo "⚠️  Você precisa fazer login no Railway primeiro:"
    echo "   railway login"
    echo ""
    echo "Depois execute novamente: ./deploy-railway.sh"
    exit 1
fi

# Deploy
echo "🚀 Fazendo deploy..."
if ! railway status &> /dev/null; then
    echo "🔗 Projeto não vinculado. Criando novo projeto..."
    railway init
fi
railway up

echo "✅ Deploy concluído!"
echo "🌐 Acesse sua aplicação no Railway Dashboard"
