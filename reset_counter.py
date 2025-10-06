#!/usr/bin/env python3
import psycopg2
import os

# URL do banco do Railway
DATABASE_URL = "postgresql://postgres:vsUVlnroTXYzxckTWhdtoyTlKvPhooDj@postgres-ni2o.railway.internal:5432/railway"

try:
    # Conectar ao banco
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Zerar o contador da sequência
    cursor.execute("ALTER SEQUENCE cadastros_id_seq RESTART WITH 1;")
    
    # Confirmar a transação
    conn.commit()
    
    print("Contador da tabela cadastros zerado com sucesso!")
    
except Exception as e:
    print(f"Erro: {e}")
    
finally:
    if 'conn' in locals():
        conn.close()
