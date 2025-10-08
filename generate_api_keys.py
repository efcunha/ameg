#!/usr/bin/env python3
"""
Gerador de chaves seguras para API REST do Sistema AMEG
Gera chaves criptograficamente seguras para JWT e autenticação da API
"""

import secrets
import os

def generate_secure_key(length=32):
    """Gera uma chave segura usando secrets"""
    return secrets.token_urlsafe(length)

def main():
    print("🔐 Gerador de Chaves Seguras - API REST AMEG")
    print("=" * 50)
    
    # Gerar chaves
    api_secret_key = generate_secure_key(32)
    api_master_key = generate_secure_key(32)
    
    print("\n✅ Chaves geradas com sucesso!")
    print("\n📋 Variáveis de Ambiente:")
    print("-" * 30)
    print(f"API_SECRET_KEY={api_secret_key}")
    print(f"API_MASTER_KEY={api_master_key}")
    
    print("\n🚀 Para Railway (Produção):")
    print("-" * 30)
    print("1. Acesse o Railway Dashboard")
    print("2. Vá em Variables")
    print("3. Adicione as variáveis:")
    print(f"   API_ENABLED=true")
    print(f"   API_SECRET_KEY={api_secret_key}")
    print(f"   API_MASTER_KEY={api_master_key}")
    
    print("\n🏠 Para Desenvolvimento Local:")
    print("-" * 30)
    print("Adicione ao arquivo .env.secure:")
    print(f"API_ENABLED=true")
    print(f"API_SECRET_KEY={api_secret_key}")
    print(f"API_MASTER_KEY={api_master_key}")
    
    # Salvar em arquivo local se solicitado
    save_local = input("\n💾 Salvar chaves em .env.api? (s/N): ").lower().strip()
    if save_local == 's':
        with open('.env.api', 'w') as f:
            f.write(f"# Chaves da API REST - Geradas em {os.popen('date').read().strip()}\n")
            f.write(f"API_ENABLED=true\n")
            f.write(f"API_SECRET_KEY={api_secret_key}\n")
            f.write(f"API_MASTER_KEY={api_master_key}\n")
        print("✅ Chaves salvas em .env.api")
        print("⚠️  IMPORTANTE: Não commite este arquivo!")
    
    print("\n🔒 Segurança:")
    print("-" * 30)
    print("• Mantenha as chaves em segredo")
    print("• Use HTTPS em produção")
    print("• Tokens JWT expiram em 24h")
    print("• API desabilitada por padrão")
    
    print("\n📚 Documentação completa em API_REST.md")

if __name__ == "__main__":
    main()
