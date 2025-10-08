// Debug detalhado para identificar problema
console.log('🚀 INICIANDO DEBUG DETALHADO DOS GRÁFICOS');

window.addEventListener('load', function() {
    console.log('📋 Página carregada completamente');
    
    // Aguardar um pouco e testar
    setTimeout(function() {
        console.log('⏰ Iniciando testes após timeout');
        testAllAPIs();
    }, 1000);
});

async function testAllAPIs() {
    console.log('🔍 TESTANDO TODAS AS APIs DOS GRÁFICOS');
    
    // Testar cada API individualmente
    await testAPI('demografia');
    await testAPI('saude'); 
    await testAPI('socioeconomico');
    await testAPI('trabalho');
    await testAPI('filters');
}

async function testAPI(endpoint) {
    console.log(`\n🎯 TESTANDO API: ${endpoint}`);
    console.log('=' + '='.repeat(30));
    
    try {
        const url = endpoint === 'filters' 
            ? '/api/charts/filters'
            : `/api/charts/${endpoint}?periodo=todos&bairro=todos`;
            
        console.log(`📡 URL: ${url}`);
        console.log(`⏰ Timestamp: ${new Date().toISOString()}`);
        
        const startTime = performance.now();
        const response = await fetch(url);
        const endTime = performance.now();
        
        console.log(`⚡ Tempo de resposta: ${Math.round(endTime - startTime)}ms`);
        console.log(`📊 Status: ${response.status} ${response.statusText}`);
        console.log(`🔗 URL final: ${response.url}`);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error(`❌ ERRO HTTP ${response.status}:`);
            console.error(errorText);
            
            showError(`Erro na API ${endpoint}: HTTP ${response.status}`);
            return null;
        }
        
        const data = await response.json();
        console.log(`📦 Dados recebidos para ${endpoint}:`);
        console.log(JSON.stringify(data, null, 2));
        
        // Verificar se há dados
        let totalRecords = 0;
        Object.keys(data).forEach(key => {
            if (Array.isArray(data[key])) {
                totalRecords += data[key].length;
                console.log(`  📋 ${key}: ${data[key].length} registros`);
                
                if (data[key].length > 0) {
                    console.log(`    🔍 Primeiro item:`, data[key][0]);
                }
            }
        });
        
        if (totalRecords === 0) {
            console.warn(`⚠️ NENHUM DADO RETORNADO para ${endpoint}!`);
        } else {
            console.log(`✅ ${endpoint} OK - ${totalRecords} registros totais`);
        }
        
        return data;
        
    } catch (error) {
        console.error(`❌ ERRO DE REDE em ${endpoint}:`, error);
        console.error('Stack trace:', error.stack);
        
        showError(`Erro de rede na API ${endpoint}: ${error.message}`);
        return null;
    }
}

function showError(message) {
    console.error('🚨 MOSTRANDO ERRO NA TELA:', message);
    
    const container = document.querySelector('.container');
    if (!container) {
        console.error('❌ Container não encontrado!');
        return;
    }
    
    // Criar div de erro se não existir
    let errorDiv = document.getElementById('debug-error');
    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.id = 'debug-error';
        errorDiv.style.cssText = `
            background: #f8d7da;
            color: #721c24;
            padding: 20px;
            margin: 20px 0;
            border: 1px solid #f5c6cb;
            border-radius: 5px;
            font-family: monospace;
        `;
        container.insertBefore(errorDiv, container.firstChild);
    }
    
    errorDiv.innerHTML += `
        <div style="margin-bottom: 10px;">
            <strong>🕐 ${new Date().toLocaleTimeString()}</strong><br>
            ${message}
        </div>
    `;
}

// Função para aplicar filtros com debug
function aplicarFiltros() {
    console.log('\n🔄 APLICANDO FILTROS COM DEBUG');
    console.log('=' + '='.repeat(40));
    
    const periodoElement = document.getElementById('filtro-periodo');
    const bairroElement = document.getElementById('filtro-bairro');
    
    console.log('🔍 Elementos de filtro:');
    console.log('  📅 Período element:', periodoElement);
    console.log('  🏘️ Bairro element:', bairroElement);
    
    const periodo = periodoElement?.value || 'todos';
    const bairro = bairroElement?.value || 'todos';
    
    console.log('🎯 Valores selecionados:');
    console.log(`  📅 Período: "${periodo}"`);
    console.log(`  🏘️ Bairro: "${bairro}"`);
    
    // Testar APIs com filtros
    testAllAPIs();
}

console.log('✅ CHARTS-DEBUG-DETAILED.JS carregado completamente');
