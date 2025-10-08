// Gráficos funcionais com Chart.js
console.log('🚀 Iniciando gráficos funcionais...');

document.addEventListener('DOMContentLoaded', function() {
    // Aguardar Chart.js carregar
    setTimeout(initCharts, 1000);
});

async function initCharts() {
    if (typeof Chart === 'undefined') {
        console.warn('Chart.js não carregou, mantendo modo texto');
        return;
    }
    
    console.log('✅ Chart.js carregado, criando gráficos visuais');
    await loadAllCharts();
}

async function loadAllCharts() {
    try {
        const periodo = document.getElementById('filtro-periodo')?.value || 'todos';
        const bairro = document.getElementById('filtro-bairro')?.value || 'todos';
        
        const params = new URLSearchParams();
        if (periodo !== 'todos') params.append('periodo', periodo);
        if (bairro !== 'todos') params.append('bairro', bairro);
        
        const suffix = params.toString() ? `?${params.toString()}` : '';
        
        // Carregar dados
        const [demo, saude, socio, trabalho] = await Promise.all([
            fetch(`/api/charts/demografia${suffix}`).then(r => r.json()),
            fetch(`/api/charts/saude${suffix}`).then(r => r.json()),
            fetch(`/api/charts/socioeconomico${suffix}`).then(r => r.json()),
            fetch(`/api/charts/trabalho${suffix}`).then(r => r.json())
        ]);
        
        // Criar gráficos
        createChart('idadeChart', 'doughnut', demo.idade, 'faixa', 'total');
        createChart('bairrosChart', 'bar', demo.bairros, 'bairro', 'total');
        createChart('evolucaoChart', 'line', demo.evolucao, 'mes', 'total');
        
        // Remover modo texto
        const textMode = document.querySelector('.container > div');
        if (textMode && textMode.innerHTML.includes('Modo Texto')) {
            textMode.remove();
        }
        
    } catch (error) {
        console.error('Erro ao carregar gráficos:', error);
    }
}

function createChart(canvasId, type, data, labelKey, valueKey) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !data || data.length === 0) return;
    
    new Chart(canvas, {
        type: type,
        data: {
            labels: data.map(d => d[labelKey]),
            datasets: [{
                data: data.map(d => d[valueKey]),
                backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF'],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { position: 'bottom' } }
        }
    });
}

function aplicarFiltros() {
    loadAllCharts();
}
