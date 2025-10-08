// Versão limpa e única dos gráficos
console.log('🚀 GRÁFICOS LIMPOS - VERSÃO ÚNICA');

document.addEventListener('DOMContentLoaded', function() {
    console.log('📋 DOM carregado');
    
    // Limpar qualquer conteúdo existente primeiro
    setTimeout(function() {
        console.log('🧹 Limpando e criando gráficos únicos...');
        createSingleDashboard();
    }, 1000);
});

async function createSingleDashboard() {
    try {
        console.log('📡 Buscando dados...');
        const response = await fetch('/api/charts/demografia?periodo=todos&bairro=todos');
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        console.log('📦 Dados recebidos:', data);
        
        // Limpar TUDO e criar dashboard único
        const container = document.querySelector('.container');
        container.innerHTML = '';
        
        // Criar dashboard moderno único
        container.innerHTML = `
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 15px; margin-bottom: 30px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 2.5em; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
                    📊 Dashboard AMEG
                </h1>
                <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 1.2em;">
                    ${getTotalCadastros(data)} cadastros • Dados atualizados
                </p>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 25px;">
                
                <!-- Faixa Etária -->
                <div style="background: white; padding: 25px; border-radius: 15px; box-shadow: 0 8px 25px rgba(0,0,0,0.1);">
                    <h3 style="color: #3498db; margin-bottom: 20px; display: flex; align-items: center;">
                        <span style="background: #3498db; color: white; padding: 8px; border-radius: 50%; margin-right: 10px;">👥</span>
                        Faixa Etária
                    </h3>
                    ${createDataBars(data.idade, 'faixa', 'total', '#3498db')}
                </div>
                
                <!-- Bairros -->
                <div style="background: white; padding: 25px; border-radius: 15px; box-shadow: 0 8px 25px rgba(0,0,0,0.1);">
                    <h3 style="color: #e74c3c; margin-bottom: 20px; display: flex; align-items: center;">
                        <span style="background: #e74c3c; color: white; padding: 8px; border-radius: 50%; margin-right: 10px;">🏘️</span>
                        Bairros
                    </h3>
                    ${createDataBars(data.bairros, 'bairro', 'total', '#e74c3c')}
                </div>
                
                <!-- Evolução -->
                <div style="background: white; padding: 25px; border-radius: 15px; box-shadow: 0 8px 25px rgba(0,0,0,0.1); grid-column: 1 / -1;">
                    <h3 style="color: #27ae60; margin-bottom: 20px; display: flex; align-items: center;">
                        <span style="background: #27ae60; color: white; padding: 8px; border-radius: 50%; margin-right: 10px;">📈</span>
                        Evolução de Cadastros
                    </h3>
                    ${createDataBars(data.evolucao, 'mes', 'total', '#27ae60')}
                </div>
                
            </div>
            
            <div style="margin-top: 30px; padding: 20px; background: linear-gradient(45deg, #2ecc71, #27ae60); border-radius: 10px; color: white; text-align: center;">
                <strong>✅ Dashboard Carregado com Sucesso!</strong><br>
                <span style="opacity: 0.9;">Dados em tempo real do sistema AMEG</span>
            </div>
        `;
        
        console.log('✅ Dashboard único criado com sucesso!');
        
    } catch (error) {
        console.error('❌ Erro:', error);
        
        const container = document.querySelector('.container');
        container.innerHTML = `
            <div style="background: #f8d7da; color: #721c24; padding: 20px; border-radius: 10px; text-align: center;">
                <h3>❌ Erro ao Carregar Dashboard</h3>
                <p>Erro: ${error.message}</p>
                <button onclick="createSingleDashboard()" style="background: #dc3545; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">
                    🔄 Tentar Novamente
                </button>
            </div>
        `;
    }
}

function getTotalCadastros(data) {
    if (data.idade && data.idade.length > 0) {
        return data.idade.reduce((total, item) => total + item.total, 0);
    }
    return 0;
}

function createDataBars(data, labelKey, valueKey, color) {
    if (!data || data.length === 0) {
        return '<p style="color: #666; text-align: center; padding: 20px;">Nenhum dado disponível</p>';
    }
    
    const maxValue = Math.max(...data.map(d => d[valueKey]));
    
    let html = '';
    data.forEach(item => {
        const percentage = (item[valueKey] / maxValue) * 100;
        html += `
            <div style="margin-bottom: 15px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="font-weight: 600; color: #2c3e50;">${item[labelKey]}</span>
                    <span style="color: ${color}; font-weight: bold; background: ${color}20; padding: 2px 8px; border-radius: 12px; font-size: 0.9em;">${item[valueKey]}</span>
                </div>
                <div style="background: #f8f9fa; height: 12px; border-radius: 6px; overflow: hidden;">
                    <div style="background: linear-gradient(90deg, ${color}, ${color}aa); height: 100%; width: ${percentage}%; border-radius: 6px; transition: width 0.8s ease;"></div>
                </div>
            </div>
        `;
    });
    
    return html;
}

function aplicarFiltros() {
    console.log('🔄 Aplicando filtros...');
    createSingleDashboard();
}

console.log('✅ CHARTS-CLEAN.JS carregado');
