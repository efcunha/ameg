// Versão simples que substitui o texto por gráficos
console.log('🚀 Carregando gráficos simples...');

// Aguardar tudo carregar
window.addEventListener('load', function() {
    setTimeout(function() {
        console.log('⏰ Tentando criar gráficos...');
        
        if (typeof Chart !== 'undefined') {
            console.log('✅ Chart.js disponível, criando gráficos');
            replaceTextWithCharts();
        } else {
            console.log('❌ Chart.js não disponível');
        }
    }, 2000);
});

async function replaceTextWithCharts() {
    try {
        // Buscar dados
        const response = await fetch('/api/charts/demografia?periodo=todos&bairro=todos');
        const data = await response.json();
        
        console.log('📊 Dados para gráficos:', data);
        
        // Limpar container e adicionar canvas
        const container = document.querySelector('.container');
        container.innerHTML = `
            <h2>📊 Gráficos Interativos</h2>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0;">
                <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h3>👥 Faixa Etária</h3>
                    <canvas id="idadeChart" width="300" height="200"></canvas>
                </div>
                <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h3>🏘️ Bairros</h3>
                    <canvas id="bairrosChart" width="300" height="200"></canvas>
                </div>
            </div>
            <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin: 20px 0;">
                <h3>📈 Evolução de Cadastros</h3>
                <canvas id="evolucaoChart" width="600" height="200"></canvas>
            </div>
        `;
        
        // Criar gráficos
        if (data.idade && data.idade.length > 0) {
            new Chart(document.getElementById('idadeChart'), {
                type: 'doughnut',
                data: {
                    labels: data.idade.map(d => d.faixa),
                    datasets: [{
                        data: data.idade.map(d => d.total),
                        backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0']
                    }]
                },
                options: { responsive: true }
            });
        }
        
        if (data.bairros && data.bairros.length > 0) {
            new Chart(document.getElementById('bairrosChart'), {
                type: 'bar',
                data: {
                    labels: data.bairros.map(d => d.bairro),
                    datasets: [{
                        data: data.bairros.map(d => d.total),
                        backgroundColor: '#36A2EB'
                    }]
                },
                options: { 
                    responsive: true,
                    scales: { y: { beginAtZero: true } }
                }
            });
        }
        
        if (data.evolucao && data.evolucao.length > 0) {
            new Chart(document.getElementById('evolucaoChart'), {
                type: 'line',
                data: {
                    labels: data.evolucao.map(d => d.mes),
                    datasets: [{
                        label: 'Cadastros',
                        data: data.evolucao.map(d => d.total),
                        borderColor: '#FF6384',
                        fill: false
                    }]
                },
                options: { 
                    responsive: true,
                    scales: { y: { beginAtZero: true } }
                }
            });
        }
        
        console.log('✅ Gráficos criados com sucesso!');
        
    } catch (error) {
        console.error('❌ Erro ao criar gráficos:', error);
    }
}
