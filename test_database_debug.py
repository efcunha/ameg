#!/usr/bin/env python3
"""
Teste de conexão com banco e verificação de dados
"""
import os
import sys
from database import get_db_connection

def test_database():
    """Testa conexão e dados do banco"""
    
    print("🔍 TESTE DE CONEXÃO E DADOS DO BANCO")
    print("=" * 50)
    
    try:
        # Testar conexão
        print("\n1️⃣ Testando conexão com banco...")
        conn = get_db_connection()
        print("✅ Conexão estabelecida")
        
        cursor = conn.cursor()
        
        # Verificar se tabela cadastros existe
        print("\n2️⃣ Verificando se tabela cadastros existe...")
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'cadastros'
            );
        """)
        table_exists = cursor.fetchone()[0]
        print(f"Tabela cadastros existe: {table_exists}")
        
        if not table_exists:
            print("❌ Tabela cadastros não existe!")
            return
        
        # Contar total de registros
        print("\n3️⃣ Contando registros na tabela cadastros...")
        cursor.execute("SELECT COUNT(*) FROM cadastros")
        total_registros = cursor.fetchone()[0]
        print(f"Total de registros: {total_registros}")
        
        if total_registros == 0:
            print("⚠️ Nenhum registro encontrado na tabela cadastros!")
            return
        
        # Verificar campos importantes
        print("\n4️⃣ Verificando campos importantes...")
        
        # Data de nascimento
        cursor.execute("SELECT COUNT(*) FROM cadastros WHERE data_nascimento IS NOT NULL")
        com_data_nasc = cursor.fetchone()[0]
        print(f"Registros com data_nascimento: {com_data_nasc}")
        
        # Bairros
        cursor.execute("SELECT COUNT(DISTINCT bairro) FROM cadastros WHERE bairro IS NOT NULL AND bairro != ''")
        total_bairros = cursor.fetchone()[0]
        print(f"Bairros únicos: {total_bairros}")
        
        # Listar alguns bairros
        cursor.execute("SELECT DISTINCT bairro FROM cadastros WHERE bairro IS NOT NULL AND bairro != '' LIMIT 5")
        bairros = cursor.fetchall()
        print(f"Exemplos de bairros: {[b[0] for b in bairros]}")
        
        # Data de cadastro
        cursor.execute("SELECT COUNT(*) FROM cadastros WHERE data_cadastro IS NOT NULL")
        com_data_cad = cursor.fetchone()[0]
        print(f"Registros com data_cadastro: {com_data_cad}")
        
        # Testar query de faixa etária
        print("\n5️⃣ Testando query de faixa etária...")
        idade_query = """
        SELECT 
            CASE 
                WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, data_nascimento)) < 18 THEN 'Menor 18'
                WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, data_nascimento)) < 30 THEN '18-29'
                WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, data_nascimento)) < 50 THEN '30-49'
                ELSE '50+'
            END as faixa,
            COUNT(*) as total
        FROM cadastros 
        WHERE data_nascimento IS NOT NULL AND 1=1
        GROUP BY faixa
        ORDER BY faixa
        """
        cursor.execute(idade_query)
        idade_data = cursor.fetchall()
        print(f"Dados de faixa etária: {idade_data}")
        
        # Testar query de bairros
        print("\n6️⃣ Testando query de bairros...")
        bairro_query = """
        SELECT bairro, COUNT(*) as total
        FROM cadastros 
        WHERE bairro IS NOT NULL AND bairro != '' AND 1=1
        GROUP BY bairro
        ORDER BY total DESC
        LIMIT 10
        """
        cursor.execute(bairro_query)
        bairro_data = cursor.fetchall()
        print(f"Dados de bairros: {bairro_data}")
        
        # Testar query de evolução
        print("\n7️⃣ Testando query de evolução...")
        evolucao_query = """
        SELECT 
            TO_CHAR(data_cadastro, 'YYYY-MM') as mes,
            COUNT(*) as total
        FROM cadastros 
        WHERE data_cadastro IS NOT NULL AND 1=1
        GROUP BY mes
        ORDER BY mes DESC
        LIMIT 12
        """
        cursor.execute(evolucao_query)
        evolucao_data = cursor.fetchall()
        print(f"Dados de evolução: {evolucao_data}")
        
        cursor.close()
        conn.close()
        
        print("\n✅ TESTE CONCLUÍDO COM SUCESSO!")
        
    except Exception as e:
        print(f"❌ ERRO no teste: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_database()
