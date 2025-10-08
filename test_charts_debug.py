#!/usr/bin/env python3
"""
Teste detalhado dos gráficos para identificar problemas
"""
import requests
import json
import logging

# Configurar logging detalhado
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_charts_api():
    """Testa a API de gráficos com logs detalhados"""
    
    base_url = "http://localhost:5000"
    
    print("🔍 TESTE DETALHADO DOS GRÁFICOS")
    print("=" * 50)
    
    # Teste 1: Verificar se a página de gráficos carrega
    print("\n1️⃣ Testando página de gráficos...")
    try:
        response = requests.get(f"{base_url}/charts")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Página de gráficos carrega")
        else:
            print(f"❌ Erro na página: {response.text}")
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return
    
    # Teste 2: API de filtros
    print("\n2️⃣ Testando API de filtros...")
    try:
        response = requests.get(f"{base_url}/api/charts/filters")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Filtros obtidos: {len(data.get('bairros', []))} bairros")
            print(f"Bairros: {[b['label'] for b in data.get('bairros', [])][:5]}...")
        else:
            print(f"❌ Erro nos filtros: {response.text}")
    except Exception as e:
        print(f"❌ Erro nos filtros: {e}")
    
    # Teste 3: Demografia com todos os períodos e bairros
    print("\n3️⃣ Testando Demografia - TODOS OS PERÍODOS E BAIRROS...")
    try:
        params = {'periodo': 'todos', 'bairro': 'todos'}
        response = requests.get(f"{base_url}/api/charts/demografia", params=params)
        print(f"Status: {response.status_code}")
        print(f"URL: {response.url}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Demografia obtida com sucesso!")
            print(f"Dados de idade: {len(data.get('idade', []))} registros")
            print(f"Dados de bairros: {len(data.get('bairros', []))} registros")
            print(f"Dados de evolução: {len(data.get('evolucao', []))} registros")
            
            # Mostrar dados detalhados
            if data.get('idade'):
                print(f"Idade: {data['idade']}")
            if data.get('bairros'):
                print(f"Bairros: {data['bairros'][:3]}...")
            if data.get('evolucao'):
                print(f"Evolução: {data['evolucao'][:3]}...")
        else:
            print(f"❌ Erro na demografia: {response.text}")
    except Exception as e:
        print(f"❌ Erro na demografia: {e}")
    
    # Teste 4: Saúde
    print("\n4️⃣ Testando Saúde - TODOS OS PERÍODOS E BAIRROS...")
    try:
        params = {'periodo': 'todos', 'bairro': 'todos'}
        response = requests.get(f"{base_url}/api/charts/saude", params=params)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Saúde obtida com sucesso!")
            print(f"Doenças: {len(data.get('doencas', []))} registros")
            print(f"Medicamentos: {len(data.get('medicamentos', []))} registros")
            print(f"Deficiências: {len(data.get('deficiencias', []))} registros")
        else:
            print(f"❌ Erro na saúde: {response.text}")
    except Exception as e:
        print(f"❌ Erro na saúde: {e}")
    
    # Teste 5: Socioeconômico
    print("\n5️⃣ Testando Socioeconômico - TODOS OS PERÍODOS E BAIRROS...")
    try:
        params = {'periodo': 'todos', 'bairro': 'todos'}
        response = requests.get(f"{base_url}/api/charts/socioeconomico", params=params)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Socioeconômico obtido com sucesso!")
            print(f"Renda: {len(data.get('renda', []))} registros")
            print(f"Moradia: {len(data.get('moradia', []))} registros")
            print(f"Benefícios: {len(data.get('beneficios', []))} registros")
        else:
            print(f"❌ Erro no socioeconômico: {response.text}")
    except Exception as e:
        print(f"❌ Erro no socioeconômico: {e}")
    
    # Teste 6: Trabalho
    print("\n6️⃣ Testando Trabalho - TODOS OS PERÍODOS E BAIRROS...")
    try:
        params = {'periodo': 'todos', 'bairro': 'todos'}
        response = requests.get(f"{base_url}/api/charts/trabalho", params=params)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Trabalho obtido com sucesso!")
            print(f"Tipos: {len(data.get('tipos', []))} registros")
            print(f"Locais: {len(data.get('locais', []))} registros")
        else:
            print(f"❌ Erro no trabalho: {response.text}")
    except Exception as e:
        print(f"❌ Erro no trabalho: {e}")

if __name__ == "__main__":
    test_charts_api()
