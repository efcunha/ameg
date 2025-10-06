#!/usr/bin/env python3
"""
Módulo de segurança para proteção de senhas e dados sensíveis
"""
import os
import hashlib
import secrets
from cryptography.fernet import Fernet
from werkzeug.security import generate_password_hash, check_password_hash
import base64

class SecurityManager:
    def __init__(self):
        self.salt = os.environ.get('SECURITY_SALT', 'ameg_security_2024_salt_change_in_production')
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
    
    def _get_or_create_encryption_key(self):
        """Obtém ou cria chave de criptografia"""
        key = os.environ.get('ENCRYPTION_KEY')
        if not key:
            key = Fernet.generate_key().decode()
            # Em produção, salvar em variável de ambiente
        return key.encode() if isinstance(key, str) else key
    
    def hash_admin_password(self, password):
        """Cria hash seguro para senha do admin com salt adicional"""
        salted_password = password + self.salt
        return generate_password_hash(salted_password, method='pbkdf2:sha256', salt_length=16)
    
    def verify_admin_password(self, password, hash_stored):
        """Verifica senha do admin com salt adicional"""
        salted_password = password + self.salt
        return check_password_hash(hash_stored, salted_password)
    
    def encrypt_sensitive_data(self, data):
        """Criptografa dados sensíveis"""
        if isinstance(data, str):
            data = data.encode()
        return self.cipher.encrypt(data).decode()
    
    def decrypt_sensitive_data(self, encrypted_data):
        """Descriptografa dados sensíveis"""
        if isinstance(encrypted_data, str):
            encrypted_data = encrypted_data.encode()
        return self.cipher.decrypt(encrypted_data).decode()
    
    def generate_secure_password(self, length=12):
        """Gera senha segura aleatória"""
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def is_admin_protected(self, user_id):
        """Verifica se usuário é admin protegido (ID 1)"""
        return str(user_id) == "1"

# Instância global
security_manager = SecurityManager()
