#!/usr/bin/env python3
import os
import re
import gzip
from pathlib import Path

def minify_css(content):
    """Minifica CSS removendo espaços, comentários e quebras de linha"""
    # Remove comentários
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    # Remove espaços extras e quebras de linha
    content = re.sub(r'\s+', ' ', content)
    # Remove espaços ao redor de caracteres especiais
    content = re.sub(r'\s*([{}:;,>+~])\s*', r'\1', content)
    return content.strip()

def minify_js(content):
    """Minifica JS básico removendo espaços e comentários"""
    # Remove comentários de linha
    content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
    # Remove comentários de bloco
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    # Remove espaços extras
    content = re.sub(r'\s+', ' ', content)
    # Remove espaços ao redor de operadores
    content = re.sub(r'\s*([{}();,=])\s*', r'\1', content)
    return content.strip()

def compress_files():
    """Comprime arquivos CSS e JS"""
    static_dir = Path(__file__).parent
    
    # CSS
    css_files = static_dir.glob('../css/*.css')
    for css_file in css_files:
        if '.min.' not in css_file.name:
            content = css_file.read_text()
            minified = minify_css(content)
            
            # Salva versão minificada
            min_file = css_file.with_name(css_file.stem + '.min.css')
            min_file.write_text(minified)
            
            # Cria versão gzip
            with gzip.open(str(min_file) + '.gz', 'wt') as f:
                f.write(minified)
    
    # JS
    js_files = static_dir.glob('*.js')
    for js_file in js_files:
        if '.min.' not in js_file.name and js_file.name != 'compress.py':
            content = js_file.read_text()
            minified = minify_js(content)
            
            # Salva versão minificada
            min_file = js_file.with_name(js_file.stem + '.min.js')
            min_file.write_text(minified)
            
            # Cria versão gzip
            with gzip.open(str(min_file) + '.gz', 'wt') as f:
                f.write(minified)

if __name__ == '__main__':
    compress_files()
    print("✅ Arquivos CSS/JS comprimidos com sucesso!")
