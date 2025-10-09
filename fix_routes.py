#!/usr/bin/env python3
"""
Script para adicionar variáveis de permissão nas rotas de relatórios
"""
import re

def fix_relatorios_routes():
    """Corrige as rotas no arquivo relatorios.py"""
    file_path = 'blueprints/relatorios.py'
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Padrões para substituir render_template sem variáveis
        patterns_to_fix = [
            (r"return render_template\('tipos_relatorios\.html'\)", 
             "tem_permissao_caixa = session.get('tipo_usuario') == 'admin' or session.get('usuario') == 'admin'\n    return render_template('tipos_relatorios.html', tem_permissao_caixa=tem_permissao_caixa)"),
            
            (r"return render_template\('relatorio_completo\.html', \n\s+cadastros=cadastros, total=len\(cadastros\)\)", 
             "tem_permissao_caixa = session.get('tipo_usuario') == 'admin' or session.get('usuario') == 'admin'\n        return render_template('relatorio_completo.html', \n                             cadastros=cadastros, total=len(cadastros), tem_permissao_caixa=tem_permissao_caixa)"),
            
            (r"return render_template\('relatorio_simplificado\.html', cadastros=cadastros\)", 
             "tem_permissao_caixa = session.get('tipo_usuario') == 'admin' or session.get('usuario') == 'admin'\n        return render_template('relatorio_simplificado.html', cadastros=cadastros, tem_permissao_caixa=tem_permissao_caixa)"),
            
            (r"return render_template\('relatorio_estatistico\.html', stats=stats\)", 
             "tem_permissao_caixa = session.get('tipo_usuario') == 'admin' or session.get('usuario') == 'admin'\n        return render_template('relatorio_estatistico.html', stats=stats, tem_permissao_caixa=tem_permissao_caixa)"),
            
            (r"return render_template\('relatorio_por_bairro\.html', bairros=bairros\)", 
             "tem_permissao_caixa = session.get('tipo_usuario') == 'admin' or session.get('usuario') == 'admin'\n        return render_template('relatorio_por_bairro.html', bairros=bairros, tem_permissao_caixa=tem_permissao_caixa)"),
            
            (r"return render_template\('relatorio_por_bairro\.html', bairros=\[\], erro=f\"Erro: \{str\(e\)\}\"\)", 
             "tem_permissao_caixa = session.get('tipo_usuario') == 'admin' or session.get('usuario') == 'admin'\n        return render_template('relatorio_por_bairro.html', bairros=[], erro=f\"Erro: {str(e)}\", tem_permissao_caixa=tem_permissao_caixa)"),
            
            (r"return render_template\('relatorio_renda\.html', faixas_renda=faixas_renda, renda_bairro=renda_bairro\)", 
             "tem_permissao_caixa = session.get('tipo_usuario') == 'admin' or session.get('usuario') == 'admin'\n    return render_template('relatorio_renda.html', faixas_renda=faixas_renda, renda_bairro=renda_bairro, tem_permissao_caixa=tem_permissao_caixa)"),
            
            (r"return render_template\('relatorio_saude\.html', stats=stats, cadastros=cadastros_saude\)", 
             "tem_permissao_caixa = session.get('tipo_usuario') == 'admin' or session.get('usuario') == 'admin'\n    return render_template('relatorio_saude.html', stats=stats, cadastros=cadastros_saude, tem_permissao_caixa=tem_permissao_caixa)")
        ]
        
        modified = False
        for pattern, replacement in patterns_to_fix:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                modified = True
                print(f"✅ Corrigido padrão: {pattern[:50]}...")
        
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Arquivo {file_path} atualizado")
        else:
            print(f"⚠️  Nenhuma alteração necessária em {file_path}")
            
    except Exception as e:
        print(f"❌ Erro ao corrigir {file_path}: {e}")

def fix_caixa_routes():
    """Corrige as rotas no arquivo caixa.py"""
    file_path = 'blueprints/caixa.py'
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Procurar render_template para relatorio_caixa.html
        pattern = r"return render_template\('relatorio_caixa\.html',\s*([^)]+)\)"
        
        if re.search(pattern, content):
            # Adicionar tem_permissao_caixa=True (já que está na rota do caixa)
            replacement = r"return render_template('relatorio_caixa.html',\n                             \1,\n                             tem_permissao_caixa=True)"
            content = re.sub(pattern, replacement, content)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Arquivo {file_path} atualizado")
        else:
            print(f"⚠️  Padrão não encontrado em {file_path}")
            
    except Exception as e:
        print(f"❌ Erro ao corrigir {file_path}: {e}")

def main():
    print("🔧 Corrigindo rotas de relatórios...")
    print("-" * 50)
    
    fix_relatorios_routes()
    fix_caixa_routes()
    
    print("-" * 50)
    print("✅ Correção de rotas concluída")

if __name__ == "__main__":
    main()
