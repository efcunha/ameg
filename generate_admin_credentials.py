#!/usr/bin/env python3
"""
Script para gerar credenciais seguras do admin
Execute apenas localmente - NUNCA commitar as credenciais geradas
"""
import os
import secrets
import string
from security import security_manager

def generate_secure_admin_credentials():
    """Gera credenciais seguras para o admin"""
    print("🔐 Gerando credenciais seguras para admin...")
    
    # Gerar senha segura
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    secure_password = ''.join(secrets.choice(alphabet) for _ in range(16))
    
    # Gerar hash da senha
    password_hash = security_manager.hash_admin_password(secure_password)
    
    # Gerar chave de criptografia
    encryption_key = security_manager._get_or_create_encryption_key().decode()
    
    print("\n" + "="*60)
    print("CREDENCIAIS SEGURAS GERADAS")
    print("="*60)
    print(f"Senha do Admin: {secure_password}")
    print(f"Hash da Senha: {password_hash}")
    print(f"Chave de Criptografia: {encryption_key}")
    print("="*60)
    
    # Salvar em arquivo local (não commitado)
    with open('.env.secure', 'w') as f:
        f.write(f"# Credenciais seguras - NÃO COMMITAR\n")
        f.write(f"ADMIN_PASSWORD={secure_password}\n")
        f.write(f"ADMIN_PASSWORD_HASH={password_hash}\n")
        f.write(f"ENCRYPTION_KEY={encryption_key}\n")
        f.write(f"SECURITY_SALT=ameg_security_2024_salt_change_in_production\n")
    
    print("\n✅ Credenciais salvas em .env.secure")
    print("⚠️  IMPORTANTE: Mantenha este arquivo seguro e fora do Git!")
    print("⚠️  Para produção, configure as variáveis de ambiente no Railway")

if __name__ == '__main__':
    generate_secure_admin_credentials()
