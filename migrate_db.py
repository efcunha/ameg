#!/usr/bin/env python3
import os
from database import get_db_connection

def migrate_arquivos_saude():
    """Adiciona coluna arquivo_dados se não existir"""
    try:
        conn = get_db_connection()
        cursor = conn[0].cursor() if isinstance(conn, tuple) else conn.cursor()
        
        # Verificar se a coluna já existe
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'arquivos_saude' 
            AND column_name = 'arquivo_dados'
        """)
        
        if not cursor.fetchone():
            print("Adicionando coluna arquivo_dados...")
            cursor.execute("ALTER TABLE arquivos_saude ADD COLUMN arquivo_dados BYTEA")
            conn.commit()
            print("✅ Migração concluída")
        else:
            print("✅ Coluna arquivo_dados já existe")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro na migração: {e}")

if __name__ == '__main__':
    migrate_arquivos_saude()
