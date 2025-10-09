#!/usr/bin/env python3
"""
Script para corrigir navegação em todos os templates de relatórios
"""
import os
import re

# Navegação padrão completa
NAVEGACAO_COMPLETA = '''    <div class="nav">
        <a href="/dashboard">Dashboard</a>
        <a href="/cadastrar">Novo Cadastro</a>
        <a href="/relatorios">Relatórios</a>
        <a href="/notificacoes">🔔 Notificações</a>
        <a href="/charts">📊 Gráficos</a>
        {% if tem_permissao_caixa %}
        <a href="/caixa">💰 Caixa</a>
        {% endif %}
        <a href="/arquivos_cadastros">📁 Arquivos</a>
        {% if is_admin_user(session.usuario) %}
        <a href="/usuarios">👥 Usuários</a>
        <a href="/auditoria">🔍 Auditoria</a>
        <a href="/admin_reset">🔄 Reset</a>
        {% endif %}
    </div>'''

# Templates para corrigir
templates_relatorios = [
    'relatorios.html',
    'tipos_relatorios.html',
    'relatorio_completo.html',
    'relatorio_simplificado.html',
    'relatorio_estatistico.html',
    'relatorio_por_bairro.html',
    'relatorio_renda.html',
    'relatorio_saude.html',
    'relatorio_caixa.html'
]

def corrigir_template(template_path):
    """Corrige a navegação de um template"""
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Padrão para encontrar div.nav
        pattern = r'<div class="nav">.*?</div>'
        
        if re.search(pattern, content, re.DOTALL):
            # Substituir navegação existente
            new_content = re.sub(pattern, NAVEGACAO_COMPLETA, content, flags=re.DOTALL)
            
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"✅ Corrigido: {template_path}")
            return True
        else:
            print(f"⚠️  Navegação não encontrada: {template_path}")
            return False
            
    except Exception as e:
        print(f"❌ Erro em {template_path}: {e}")
        return False

def main():
    templates_dir = 'templates'
    corrigidos = 0
    
    print("🔧 Corrigindo navegação nos templates de relatórios...")
    print("-" * 50)
    
    for template in templates_relatorios:
        template_path = os.path.join(templates_dir, template)
        if os.path.exists(template_path):
            if corrigir_template(template_path):
                corrigidos += 1
        else:
            print(f"⚠️  Template não encontrado: {template_path}")
    
    print("-" * 50)
    print(f"✅ {corrigidos} templates corrigidos")

if __name__ == "__main__":
    main()
