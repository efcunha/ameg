// Versão simplificada e robusta dos gráficos
console.log('🚀 Iniciando gráficos simplificados...');

// Aguardar DOM e Chart.js carregarem
document.addEventListener('DOMContentLoaded', function() {
    console.log('📋 DOM carregado');
    
    // Verificar se Chart.js está disponível
    if (typeof Chart === 'undefined') {
        console.error('❌ Chart.js não carregado');
        return;
    }
    
    console.log('✅ Chart.js disponível');
    
    // Aguardar um pouco para garantir que tudo carregou
    setTimeout(loadChartsSimple, 1000);
});

async function loadChartsSimple() {
    console.log('📊 Carregando gráficos...');
    
    try {
        // Carregar dados
        const response = await fetch('/api/charts/demografia');
        const data = await response.json();
        
        console.log('📦 Dados recebidos:', data);
        
        // Criar gráfico de idade
        createSimpleChart('idadeChart', 'doughnut', data.idade, 'faixa', 'total');
        
        // Criar gráfico de bairros
        createSimpleChart('bairrosChart', 'bar', data.bairros, 'bairro', 'total');
        
        // Criar gráfico de evolução
        createSimpleChart('evolucaoChart', 'line', data.evolucao, 'mes', 'total');
        
        console.log('✅ Gráficos criados com sucesso!');
        
    } catch (error) {
        console.error('❌ Erro ao carregar gráficos:', error);
        showSimpleError('Erro ao carregar dados: ' + error.message);
    }
}

function createSimpleChart(canvasId, type, data, labelKey, valueKey) {
    console.log(`🎨 Criando gráfico ${canvasId}...`);
    
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        console.error(`❌ Canvas ${canvasId} não encontrado`);
        return;
    }
    
    if (!data || data.length === 0) {
        console.log(`⚠️ Sem dados para ${canvasId}`);
        return;
    }
    
    const ctx = canvas.getContext('2d');
    
    const chartData = {
        labels: data.map(d => d[labelKey]),
        datasets: [{
            label: 'Dados',
            data: data.map(d => d[valueKey]),
            backgroundColor: [
                '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', 
                '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF'
            ],
            borderColor: '#fff',
            borderWidth: 2
        }]
    };
    
    const options = {
        responsive: true,
        plugins: {
            legend: {
                position: type === 'line' ? 'top' : 'bottom'
            }
        }
    };
    
    if (type === 'bar' || type === 'line') {
        options.scales = {
            y: { beginAtZero: true }
        };
    }
    
    new Chart(ctx, {
        type: type,
        data: chartData,
        options: options
    });
    
    console.log(`✅ Gráfico ${canvasId} criado`);
}

function showSimpleError(message) {
    document.querySelectorAll('.chart-card').forEach(card => {
        const canvas = card.querySelector('canvas');
        if (canvas) {
            canvas.style.display = 'none';
        }
        
        let errorDiv = card.querySelector('.error-message');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.style.cssText = 'color: red; text-align: center; padding: 20px;';
            card.appendChild(errorDiv);
        }
        
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    });
}
