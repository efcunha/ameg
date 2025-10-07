#!/bin/bash

echo "🛑 Parando ambiente de desenvolvimento local AMEG"

# Parar e remover containers
docker-compose down

# Opcional: remover volumes (descomente se quiser limpar dados)
# docker-compose down -v

echo "✅ Ambiente parado"
