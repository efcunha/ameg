#!/usr/bin/env python3
"""
Script para testar se o CDN está funcionando
"""
import requests
import os

def test_cdn():
    github_user = "efcunha"
    base_url = f"https://cdn.jsdelivr.net/gh/{github_user}/ameg@main"
    
    files_to_test = [
        "/static/css/mobile.css",
        "/static/css/mobile.min.css", 
        "/static/js/validators.js",
        "/static/js/validators.min.js",
        "/static/js/lazy-load.js",
        "/static/img/logo-ameg.jpeg"
    ]
    
    print("🧪 Testando CDN do jsDelivr...")
    print(f"Base URL: {base_url}")
    print("-" * 50)
    
    for file_path in files_to_test:
        url = base_url + file_path
        try:
            response = requests.head(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ {file_path} - OK ({response.headers.get('content-length', 'N/A')} bytes)")
            else:
                print(f"❌ {file_path} - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ {file_path} - Erro: {e}")
    
    print("-" * 50)
    print("🔗 URLs de teste:")
    for file_path in files_to_test:
        print(f"   {base_url}{file_path}")

if __name__ == "__main__":
    test_cdn()
