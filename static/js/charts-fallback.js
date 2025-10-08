// Fallback simples sem Chart.js
console.log('🚀 Iniciando fallback dos gráficos...');

document.addEventListener('DOMContentLoaded', function() {
    console.log('📋 DOM carregado');
    
    // Verificar se Chart.js carregou
    if (typeof Chart === 'undefined') {
        console.warn('⚠️ Chart.js não disponível, usando fallback');
        loadDataOnly();
    } else {
        console.log('✅ Chart.js disponível');
        loadChartsWithLibrary();
    }
});

async function loadDataOnly() {
    console.log('📊 Carregando apenas dados...');
    
    try {
        // Testar API de demografia
        const response = await fetch('/api/charts/demografia?periodo=todos&bairro=todos');
        console.log('📡 Status:', response.status);
        
        if (response.ok) {
            const data = await response.json();
            console.log('📦 Dados recebidos:', data);
            showDataAsText(data);
        } else {
            const error = await response.text();
            console.error('❌ Erro na API:', error);
            showError('Erro na API: ' + error);
        }
    } catch (error) {
        console.error('❌ Erro de rede:', error);
        showError('Erro de rede: ' + error.message);
    }
}

function showDataAsText(data) {
    const container = document.querySelector('.container');
    
    let html = '<div style="background: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 5px;">';
    html += '<h3>📊 Dados dos Gráficos (Modo Texto)</h3>';
    
    if (data.idade && data.idade.length > 0) {
        html += '<h4>👥 Faixa Etária:</h4><ul>';
        data.idade.forEach(item => {
            html += `<li>${item.faixa}: ${item.total} pessoas</li>`;
        });
        html += '</ul>';
    }
    
    if (data.bairros && data.bairros.length > 0) {
        html += '<h4>🏘️ Bairros:</h4><ul>';
        data.bairros.forEach(item => {
            html += `<li>${item.bairro}: ${item.total} pessoas</li>`;
        });
        html += '</ul>';
    }
    
    if (data.evolucao && data.evolucao.length > 0) {
        html += '<h4>📈 Evolução:</h4><ul>';
        data.evolucao.forEach(item => {
            html += `<li>${item.mes}: ${item.total} cadastros</li>`;
        });
        html += '</ul>';
    }
    
    html += '</div>';
    
    container.innerHTML = html;
}

function showError(message) {
    const container = document.querySelector('.container');
    container.innerHTML = `
        <div style="background: #f8d7da; color: #721c24; padding: 20px; margin: 20px 0; border-radius: 5px;">
            <h3>❌ Erro nos Gráficos</h3>
            <p>${message}</p>
            <p><small>Verifique o console (F12) para mais detalhes.</small></p>
        </div>
    `;
}

async function loadChartsWithLibrary() {
    // Implementação com Chart.js quando disponível
    console.log('📊 Carregando com Chart.js...');
    // Por enquanto, usar fallback mesmo com Chart.js
    loadDataOnly();
}
