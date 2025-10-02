#!/usr/bin/env python3
import sqlite3
import os
from werkzeug.security import generate_password_hash

# Conectar ao banco
db_path = os.environ.get('DATABASE_PATH', '/app/data/ameg.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Nova senha
nova_senha = "Admin@2024!Secure"
senha_hash = generate_password_hash(nova_senha)

# Resetar senha do admin
c.execute('DELETE FROM usuarios WHERE usuario = ?', ('admin',))
c.execute('INSERT INTO usuarios (usuario, senha) VALUES (?, ?)', ('admin', senha_hash))

conn.commit()
conn.close()

print(f"Senha do admin resetada para: {nova_senha}")
