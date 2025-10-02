#!/bin/bash
# Script para executar testes automatizados do Sistema AMEG

echo "🚀 Iniciando testes automatizados do Sistema AMEG..."
echo ""

# Verificar se está no diretório correto
if [ ! -f "app.py" ]; then
    echo "❌ Erro: Execute este script no diretório do projeto AMEG"
    exit 1
fi

# Ativar ambiente virtual se existir
if [ -d "venv" ]; then
    echo "📦 Ativando ambiente virtual..."
    source venv/bin/activate
else
    echo "⚠️  Ambiente virtual não encontrado, usando Python do sistema"
fi

# Executar testes
echo "🧪 Executando testes..."
python test_ameg.py

# Verificar resultado
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Testes concluídos com sucesso!"
    echo "Sistema está pronto para uso."
else
    echo ""
    echo "❌ Alguns testes falharam."
    echo "Verifique os erros antes de usar o sistema."
fi
