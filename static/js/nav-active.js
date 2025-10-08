// Script para destacar aba ativa na navegação
document.addEventListener('DOMContentLoaded', function() {
    const navLinks = document.querySelectorAll('.nav a');
    const currentPath = window.location.pathname;
    
    navLinks.forEach(link => {
        link.classList.remove('active');
        
        // Verificar se o href do link corresponde ao caminho atual
        const linkPath = link.getAttribute('href');
        if (linkPath === currentPath) {
            link.classList.add('active');
        }
        
        // Casos especiais para rotas que começam com o mesmo prefixo
        if (currentPath.startsWith('/relatorios') && linkPath === '/relatorios') {
            link.classList.add('active');
        }
        if (currentPath.startsWith('/arquivos') && linkPath === '/arquivos_cadastros') {
            link.classList.add('active');
        }
        if (currentPath.startsWith('/usuarios') && linkPath === '/usuarios') {
            link.classList.add('active');
        }
        if (currentPath.startsWith('/auditoria') && linkPath === '/auditoria') {
            link.classList.add('active');
        }
        if (currentPath.startsWith('/caixa') && linkPath === '/caixa') {
            link.classList.add('active');
        }
        if (currentPath.startsWith('/charts') && linkPath === '/charts') {
            link.classList.add('active');
        }
    });
});
