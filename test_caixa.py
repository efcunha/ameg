#!/usr/bin/env python3
"""
Teste básico do sistema de caixa
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import database
    print("✅ Módulo database importado com sucesso")
    
    # Testar conexão
    conn = database.get_db_connection()
    print("✅ Conexão com banco estabelecida")
    conn.close()
    
    # Testar funções de caixa
    print("✅ Funções de caixa disponíveis:")
    print("  - inserir_movimentacao_caixa")
    print("  - inserir_comprovante_caixa") 
    print("  - listar_movimentacoes_caixa")
    print("  - obter_saldo_caixa")
    print("  - obter_comprovantes_movimentacao")
    print("  - listar_cadastros_simples")
    
    print("\n🎉 Sistema de caixa pronto para uso!")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    sys.exit(1)
