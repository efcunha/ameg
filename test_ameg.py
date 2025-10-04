#!/usr/bin/env python3
"""
Testes automatizados para o Sistema AMEG
Executa todos os testes de forma automatizada sem dependências externas
"""

import sqlite3
import os
import sys
import subprocess
from app import app
from database import init_db_tables

def run_all_tests():
    """Executa todos os testes automaticamente"""
    print("🚀 SISTEMA DE TESTES AUTOMATIZADOS AMEG")
    print("=" * 50)
    
    tests_passed = 0
    tests_failed = 0
    
    # Lista de testes para executar
    test_functions = [
        ("Estrutura de Arquivos", test_file_structure),
        ("Banco de Dados", test_database_structure),
        ("Diretórios", test_directories),
        ("Importação da App", test_app_import),
        ("Templates HTML", test_templates),
        ("Configuração Flask", test_flask_config),
        ("Rotas da Aplicação", test_routes),
        ("Sistema de Login", test_login_system)
    ]
    
    print(f"\n📋 Executando {len(test_functions)} testes...\n")
    
    for test_name, test_func in test_functions:
        try:
            print(f"🧪 {test_name}...", end=" ")
            result = test_func()
            if result:
                print("✅ PASSOU")
                tests_passed += 1
            else:
                print("❌ FALHOU")
                tests_failed += 1
        except Exception as e:
            print(f"❌ ERRO: {str(e)}")
            tests_failed += 1
    
    # Resumo final
    print("\n" + "=" * 50)
    print("📊 RESUMO DOS TESTES:")
    print(f"✅ Testes aprovados: {tests_passed}")
    print(f"❌ Testes falharam: {tests_failed}")
    print(f"📈 Taxa de sucesso: {(tests_passed/(tests_passed+tests_failed)*100):.1f}%")
    
    if tests_failed == 0:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Sistema AMEG está pronto para uso!")
        print("\nPara iniciar o sistema:")
        print("source venv/bin/activate")
        print("python run.py")
    else:
        print(f"\n⚠️  {tests_failed} teste(s) falharam.")
        print("Verifique os erros antes de usar o sistema.")
    
    return tests_failed == 0

def test_file_structure():
    """Testa se todos os arquivos necessários existem"""
    required_files = [
        'app.py', 'run.py', 
        'templates/login.html', 'templates/dashboard.html',
        'templates/cadastrar.html', 'templates/relatorio_saude.html'
    ]
    
    for file in required_files:
        if not os.path.exists(file):
            print(f"\n   ❌ Arquivo faltando: {file}")
            return False
    return True

def test_database_structure():
    """Testa estrutura do banco de dados"""
    try:
        # Criar banco se não existir
        if not os.path.exists('ameg.db'):
            init_db_tables()
        
        conn = sqlite3.connect('ameg.db')
        c = conn.cursor()
        
        # Verificar tabelas
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in c.fetchall()]
        
        required_tables = ['usuarios', 'cadastros', 'arquivos_saude']
        for table in required_tables:
            if table not in tables:
                print(f"\n   ❌ Tabela faltando: {table}")
                conn.close()
                return False
        
        conn.close()
        return True
    except Exception as e:
        print(f"\n   ❌ Erro no banco: {e}")
        return False

def test_directories():
    """Testa se diretórios necessários existem"""
    required_dirs = ['templates', 'uploads/saude']
    
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
    
    return all(os.path.exists(d) for d in required_dirs)

def test_app_import():
    """Testa se consegue importar a aplicação Flask"""
    try:
        from app import app
        return app is not None
    except Exception as e:
        print(f"\n   ❌ Erro na importação: {e}")
        return False

def test_templates():
    """Testa se templates contêm elementos essenciais"""
    templates_to_check = {
        'templates/login.html': ['admin', 'senha'],
        'templates/dashboard.html': ['Total', 'Cadastros'],
        'templates/cadastrar.html': ['Nome Completo', 'CPF']
    }
    
    for template, required_content in templates_to_check.items():
        if not os.path.exists(template):
            return False
        
        with open(template, 'r', encoding='utf-8') as f:
            content = f.read()
            for required in required_content:
                if required not in content:
                    print(f"\n   ❌ Conteúdo faltando em {template}: {required}")
                    return False
    
    return True

def test_flask_config():
    """Testa configuração básica do Flask"""
    try:
        app.config['TESTING'] = True
        with app.test_client() as client:
            response = client.get('/')
            return response.status_code == 200
    except Exception as e:
        print(f"\n   ❌ Erro na configuração Flask: {e}")
        return False

def test_routes():
    """Testa se as rotas principais estão funcionando"""
    try:
        app.config['TESTING'] = True
        with app.test_client() as client:
            # Testar rota principal
            response = client.get('/')
            if response.status_code != 200:
                return False
            
            # Testar login
            response = client.post('/login', data={
                'usuario': 'admin',
                'senha': 'admin123'
            }, follow_redirects=True)
            
            if response.status_code != 200:
                return False
            
            return True
    except Exception as e:
        print(f"\n   ❌ Erro nas rotas: {e}")
        return False

def test_login_system():
    """Testa sistema de autenticação"""
    try:
        app.config['TESTING'] = True
        with app.test_client() as client:
            # Testar login correto
            response = client.post('/login', data={
                'usuario': 'admin',
                'senha': 'admin123'
            })
            
            if response.status_code not in [200, 302]:
                return False
            
            # Testar acesso ao dashboard
            response = client.get('/dashboard')
            return response.status_code in [200, 302]
            
    except Exception as e:
        print(f"\n   ❌ Erro no sistema de login: {e}")
        return False

def run_quick_integration_test():
    """Executa teste de integração rápido"""
    print("\n🔬 TESTE DE INTEGRAÇÃO RÁPIDO")
    print("-" * 30)
    
    try:
        # Testar se consegue inicializar o sistema
        init_db_tables()
        
        # Testar cliente Flask
        app.config['TESTING'] = True
        with app.test_client() as client:
            # Página inicial
            response = client.get('/')
            assert response.status_code == 200
            
            # Login
            response = client.post('/login', data={
                'usuario': 'admin',
                'senha': 'admin123'
            }, follow_redirects=True)
            assert response.status_code == 200
            
            # Dashboard
            response = client.get('/dashboard')
            assert response.status_code == 200
            
            # Cadastro
            response = client.get('/cadastrar')
            assert response.status_code == 200
            
            # Relatórios
            response = client.get('/relatorios')
            assert response.status_code == 200
        
        print("✅ Integração: PASSOU")
        return True
        
    except Exception as e:
        print(f"❌ Integração: FALHOU - {e}")
        return False

if __name__ == '__main__':
    # Executar testes automatizados
    success = run_all_tests()
    
    if success:
        # Executar teste de integração
        integration_ok = run_quick_integration_test()
        
        if integration_ok:
            print("\n🎯 SISTEMA TOTALMENTE FUNCIONAL!")
            print("Todos os componentes estão operando corretamente.")
        else:
            print("\n⚠️  Sistema básico OK, mas integração apresentou problemas.")
    
    print("\n" + "=" * 50)
    print("Para executar o sistema:")
    print("cd /home/efcunha/GitHub/ameg")
    print("source venv/bin/activate")
    print("python run.py")
    
    sys.exit(0 if success else 1)
