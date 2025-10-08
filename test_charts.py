#!/usr/bin/env python3
"""
Script de teste para funcionalidade de gráficos interativos
"""

import requests
import json
from datetime import datetime

def test_charts_endpoints():
    """Testa os endpoints de gráficos"""
    base_url = "http://localhost:5000"
    
    # Endpoints para testar
    endpoints = [
        "/charts",
        "/api/charts/demografia", 
        "/api/charts/saude",
        "/api/charts/socioeconomico",
        "/api/charts/trabalho"
    ]
    
    print("🧪 Testando endpoints de gráficos...")
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}")
            status = "✅ OK" if response.status_code == 200 else f"❌ {response.status_code}"
            print(f"{endpoint}: {status}")
            
            if endpoint.startswith("/api/") and response.status_code == 200:
                data = response.json()
                print(f"  📊 Dados retornados: {len(data)} categorias")
                
        except Exception as e:
            print(f"{endpoint}: ❌ Erro - {str(e)}")
    
    print("\n✅ Teste de gráficos concluído!")

if __name__ == "__main__":
    test_charts_endpoints()
