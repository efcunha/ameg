// Gráficos modernos e bonitos
console.log('🚀 CARREGANDO GRÁFICOS MODERNOS');

window.addEventListener('load', function() {
    setTimeout(function() {
        console.log('⏰ Iniciando gráficos modernos...');
        
        if (typeof Chart !== 'undefined') {
            console.log('✅ Chart.js disponível - criando gráficos modernos');
            createModernCharts();
        } else {
            console.log('❌ Chart.js não disponível - mantendo CSS');
        }
    }, 2000);
});

async function createModernCharts() {
    try {
        // Buscar dados
        const response = await fetch('/api/charts/demografia?periodo=todos&bairro=todos');
        const data = await response.json();
        
        console.log('📦 Dados para gráficos modernos:', data);
        
        // Substituir conteúdo com canvas modernos
        const container = document.querySelector('.container');
        container.innerHTML = `
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 15px; margin-bottom: 30px;">
                <h1 style="color: white; text-align: center; margin: 0; font-size: 2.5em; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
                    📊 Dashboard AMEG
                </h1>
                <p style="color: rgba(255,255,255,0.9); text-align: center; margin: 10px 0 0 0; font-size: 1.2em;">
                    Análise Visual dos Dados de Cadastro
                </p>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 25px; margin-bottom: 30px;">
                
                <!-- Faixa Etária -->
                <div style="background: white; padding: 25px; border-radius: 15px; box-shadow: 0 8px 25px rgba(0,0,0,0.1); border: 1px solid rgba(0,0,0,0.05);">
                    <h3 style="color: #2c3e50; margin-bottom: 20px; font-size: 1.4em; display: flex; align-items: center;">
                        <span style="background: linear-gradient(45deg, #3498db, #2980b9); color: white; padding: 8px; border-radius: 50%; margin-right: 10px; font-size: 0.8em;">👥</span>
                        Distribuição por Idade
                    </h3>
                    <canvas id="idadeChart" style="max-height: 300px;"></canvas>
                </div>
                
                <!-- Bairros -->
                <div style="background: white; padding: 25px; border-radius: 15px; box-shadow: 0 8px 25px rgba(0,0,0,0.1); border: 1px solid rgba(0,0,0,0.05);">
                    <h3 style="color: #2c3e50; margin-bottom: 20px; font-size: 1.4em; display: flex; align-items: center;">
                        <span style="background: linear-gradient(45deg, #e74c3c, #c0392b); color: white; padding: 8px; border-radius: 50%; margin-right: 10px; font-size: 0.8em;">🏘️</span>
                        Distribuição por Bairros
                    </h3>
                    <canvas id="bairrosChart" style="max-height: 300px;"></canvas>
                </div>
                
            </div>
            
            <!-- Evolução -->
            <div style="background: white; padding: 25px; border-radius: 15px; box-shadow: 0 8px 25px rgba(0,0,0,0.1); border: 1px solid rgba(0,0,0,0.05);">
                <h3 style="color: #2c3e50; margin-bottom: 20px; font-size: 1.4em; display: flex; align-items: center;">
                    <span style="background: linear-gradient(45deg, #27ae60, #229954); color: white; padding: 8px; border-radius: 50%; margin-right: 10px; font-size: 0.8em;">📈</span>
                    Evolução de Cadastros
                </h3>
                <canvas id="evolucaoChart" style="max-height: 400px;"></canvas>
            </div>
            
            <div style="margin-top: 30px; padding: 20px; background: linear-gradient(45deg, #2ecc71, #27ae60); border-radius: 10px; color: white; text-align: center;">
                <strong style="font-size: 1.2em;">✅ Gráficos Interativos Carregados!</strong><br>
                <span style="opacity: 0.9;">Dados em tempo real • Clique nos gráficos para interagir</span>
            </div>
        `;
        
        // Configurações modernas do Chart.js
        Chart.defaults.font.family = "'Segoe UI', 'Roboto', sans-serif";
        Chart.defaults.font.size = 12;
        Chart.defaults.color = '#2c3e50';
        
        // Criar gráficos modernos
        createModernChart('idadeChart', 'doughnut', data.idade, 'faixa', 'total', {
            colors: ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'],
            title: 'Distribuição Etária'
        });
        
        createModernChart('bairrosChart', 'bar', data.bairros, 'bairro', 'total', {
            colors: ['#6C5CE7', '#A29BFE', '#FD79A8', '#FDCB6E', '#E17055'],
            title: 'Cadastros por Bairro'
        });
        
        createModernChart('evolucaoChart', 'line', data.evolucao, 'mes', 'total', {
            colors: ['#00B894'],
            title: 'Crescimento Mensal'
        });
        
        console.log('✅ Gráficos modernos criados!');
        
    } catch (error) {
        console.error('❌ Erro nos gráficos modernos:', error);
    }
}

function createModernChart(canvasId, type, data, labelKey, valueKey, config) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !data || data.length === 0) return;
    
    const ctx = canvas.getContext('2d');
    
    const chartConfig = {
        type: type,
        data: {
            labels: data.map(d => d[labelKey]),
            datasets: [{
                label: config.title,
                data: data.map(d => d[valueKey]),
                backgroundColor: config.colors,
                borderColor: config.colors.map(color => color + 'CC'),
                borderWidth: type === 'line' ? 3 : 0,
                borderRadius: type === 'bar' ? 8 : 0,
                tension: type === 'line' ? 0.4 : 0,
                fill: type === 'line' ? {
                    target: 'origin',
                    above: config.colors[0] + '20'
                } : false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: type === 'doughnut' ? 'bottom' : 'top',
                    labels: {
                        padding: 20,
                        usePointStyle: true,
                        font: { size: 12, weight: '500' }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0,0,0,0.8)',
                    titleColor: 'white',
                    bodyColor: 'white',
                    borderColor: 'rgba(255,255,255,0.2)',
                    borderWidth: 1,
                    cornerRadius: 8,
                    displayColors: true
                }
            },
            scales: type !== 'doughnut' ? {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0,0,0,0.05)',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#666',
                        font: { size: 11 }
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: '#666',
                        font: { size: 11 }
                    }
                }
            } : {},
            animation: {
                duration: 1500,
                easing: 'easeInOutQuart'
            }
        }
    };
    
    new Chart(ctx, chartConfig);
}

function aplicarFiltros() {
    console.log('🔄 Aplicando filtros nos gráficos modernos...');
    createModernCharts();
}

console.log('✅ CHARTS-MODERN.JS carregado');
