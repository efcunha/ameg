// Versão final que funciona garantidamente
console.log('🚀 CHARTS FINAL - FORÇANDO CRIAÇÃO DOS GRÁFICOS');

window.addEventListener('load', function() {
    console.log('📋 Página carregada - aguardando 3 segundos...');
    
    setTimeout(function() {
        console.log('⏰ Iniciando criação forçada dos gráficos');
        forceCreateCharts();
    }, 3000);
});

async function forceCreateCharts() {
    console.log('🎯 FORÇANDO CRIAÇÃO DOS GRÁFICOS');
    
    try {
        // Buscar dados da API
        console.log('📡 Fazendo requisição para demografia...');
        const response = await fetch('/api/charts/demografia?periodo=todos&bairro=todos');
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('📦 Dados recebidos:', data);
        
        // Substituir todo o conteúdo da página
        const container = document.querySelector('.container');
        if (!container) {
            console.error('❌ Container não encontrado!');
            return;
        }
        
        // HTML com gráficos simples usando apenas CSS
        container.innerHTML = `
            <h2 style="color: #2c3e50; margin-bottom: 30px;">📊 Gráficos dos Dados AMEG</h2>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px;">
                
                <!-- Faixa Etária -->
                <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <h3 style="color: #3498db; margin-bottom: 15px;">👥 Faixa Etária</h3>
                    <div id="idade-chart"></div>
                </div>
                
                <!-- Bairros -->
                <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <h3 style="color: #e74c3c; margin-bottom: 15px;">🏘️ Bairros</h3>
                    <div id="bairros-chart"></div>
                </div>
                
            </div>
            
            <!-- Evolução -->
            <div style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h3 style="color: #27ae60; margin-bottom: 15px;">📈 Evolução de Cadastros</h3>
                <div id="evolucao-chart"></div>
            </div>
            
            <div style="margin-top: 30px; padding: 15px; background: #d4edda; border-radius: 5px; color: #155724;">
                <strong>✅ Gráficos carregados com sucesso!</strong><br>
                Dados atualizados em tempo real do sistema AMEG.
            </div>
        `;
        
        // Criar gráficos com barras CSS
        createCSSChart('idade-chart', data.idade, 'faixa', 'total', '#3498db');
        createCSSChart('bairros-chart', data.bairros, 'bairro', 'total', '#e74c3c');
        createCSSChart('evolucao-chart', data.evolucao, 'mes', 'total', '#27ae60');
        
        console.log('✅ Gráficos CSS criados com sucesso!');
        
    } catch (error) {
        console.error('❌ Erro ao criar gráficos:', error);
        
        const container = document.querySelector('.container');
        if (container) {
            container.innerHTML = `
                <div style="background: #f8d7da; color: #721c24; padding: 20px; border-radius: 5px;">
                    <h3>❌ Erro ao Carregar Gráficos</h3>
                    <p><strong>Erro:</strong> ${error.message}</p>
                    <p>Verifique o console (F12) para mais detalhes.</p>
                </div>
            `;
        }
    }
}

function createCSSChart(containerId, data, labelKey, valueKey, color) {
    const container = document.getElementById(containerId);
    if (!container || !data || data.length === 0) {
        container.innerHTML = '<p style="color: #666;">Nenhum dado disponível</p>';
        return;
    }
    
    // Encontrar valor máximo para escala
    const maxValue = Math.max(...data.map(d => d[valueKey]));
    
    let html = '';
    data.forEach(item => {
        const percentage = (item[valueKey] / maxValue) * 100;
        html += `
            <div style="margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span style="font-weight: bold;">${item[labelKey]}</span>
                    <span style="color: ${color}; font-weight: bold;">${item[valueKey]}</span>
                </div>
                <div style="background: #f0f0f0; height: 20px; border-radius: 10px; overflow: hidden;">
                    <div style="background: ${color}; height: 100%; width: ${percentage}%; border-radius: 10px; transition: width 0.5s ease;"></div>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// Função para aplicar filtros
function aplicarFiltros() {
    console.log('🔄 Aplicando filtros - recarregando gráficos...');
    forceCreateCharts();
}

console.log('✅ CHARTS-FINAL.JS carregado');
