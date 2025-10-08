// Versão com logs detalhados para debug
console.log('🚀 INICIANDO CHARTS-DEBUG.JS');

// Aguardar DOM carregar
document.addEventListener('DOMContentLoaded', function() {
    console.log('📋 DOM carregado - iniciando debug dos gráficos');
    
    // Verificar se Chart.js está disponível
    if (typeof Chart === 'undefined') {
        console.error('❌ Chart.js não está carregado!');
        showError('Chart.js não carregado');
        return;
    }
    
    console.log('✅ Chart.js disponível');
    
    // Carregar filtros primeiro
    loadFilterOptionsDebug();
    
    // Aguardar um pouco e carregar gráficos
    setTimeout(() => {
        console.log('⏰ Iniciando carregamento dos gráficos após timeout');
        loadAllChartsDebug();
    }, 1000);
});

async function loadFilterOptionsDebug() {
    console.log('🔍 CARREGANDO OPÇÕES DE FILTROS...');
    
    try {
        console.log('📡 Fazendo requisição para /api/charts/filters');
        const response = await fetch('/api/charts/filters');
        console.log('📊 Response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('📦 Dados de filtros recebidos:', data);
        
        // Preencher dropdown de bairros
        const bairroSelect = document.getElementById('filtro-bairro');
        if (bairroSelect && data.bairros) {
            console.log(`🏘️ Preenchendo ${data.bairros.length} bairros no dropdown`);
            
            // Limpar opções existentes (exceto "Todos")
            while (bairroSelect.children.length > 1) {
                bairroSelect.removeChild(bairroSelect.lastChild);
            }
            
            // Adicionar opções de bairros
            data.bairros.forEach((bairro, index) => {
                const option = document.createElement('option');
                option.value = bairro.value;
                option.textContent = bairro.label;
                bairroSelect.appendChild(option);
                console.log(`  ${index + 1}. ${bairro.label}`);
            });
            
            console.log('✅ Dropdown de bairros preenchido');
        } else {
            console.warn('⚠️ Elemento filtro-bairro não encontrado ou sem dados');
        }
        
    } catch (error) {
        console.error('❌ ERRO ao carregar filtros:', error);
        showError('Erro ao carregar filtros: ' + error.message);
    }
}

async function loadAllChartsDebug() {
    console.log('📊 CARREGANDO TODOS OS GRÁFICOS...');
    
    try {
        // Obter valores dos filtros
        const periodoElement = document.getElementById('filtro-periodo');
        const bairroElement = document.getElementById('filtro-bairro');
        
        const periodo = periodoElement?.value || 'todos';
        const bairro = bairroElement?.value || 'todos';
        
        console.log('🔍 Filtros aplicados:');
        console.log(`  📅 Período: ${periodo}`);
        console.log(`  🏘️ Bairro: ${bairro}`);
        
        // Construir query string
        const params = new URLSearchParams();
        if (periodo && periodo !== 'todos') {
            params.append('periodo', periodo);
            console.log(`  ➕ Adicionando período: ${periodo}`);
        }
        if (bairro && bairro !== 'todos') {
            params.append('bairro', bairro);
            console.log(`  ➕ Adicionando bairro: ${bairro}`);
        }
        
        const queryString = params.toString();
        const urlSuffix = queryString ? `?${queryString}` : '';
        
        console.log(`🔗 Query string: "${queryString}"`);
        console.log(`🔗 URL suffix: "${urlSuffix}"`);
        
        // Testar cada API individualmente
        console.log('\n1️⃣ TESTANDO API DEMOGRAFIA...');
        await testApiEndpoint('demografia', urlSuffix);
        
        console.log('\n2️⃣ TESTANDO API SAÚDE...');
        await testApiEndpoint('saude', urlSuffix);
        
        console.log('\n3️⃣ TESTANDO API SOCIOECONÔMICO...');
        await testApiEndpoint('socioeconomico', urlSuffix);
        
        console.log('\n4️⃣ TESTANDO API TRABALHO...');
        await testApiEndpoint('trabalho', urlSuffix);
        
    } catch (error) {
        console.error('❌ ERRO GERAL ao carregar gráficos:', error);
        showError('Erro geral: ' + error.message);
    }
}

async function testApiEndpoint(endpoint, urlSuffix) {
    try {
        const url = `/api/charts/${endpoint}${urlSuffix}`;
        console.log(`📡 Fazendo requisição para: ${url}`);
        
        const startTime = Date.now();
        const response = await fetch(url);
        const endTime = Date.now();
        
        console.log(`⏱️ Tempo de resposta: ${endTime - startTime}ms`);
        console.log(`📊 Status: ${response.status} ${response.statusText}`);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error(`❌ Erro HTTP ${response.status}:`, errorText);
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }
        
        const data = await response.json();
        console.log(`📦 Dados recebidos para ${endpoint}:`, data);
        
        // Verificar se há dados
        let totalRecords = 0;
        Object.keys(data).forEach(key => {
            if (Array.isArray(data[key])) {
                totalRecords += data[key].length;
                console.log(`  📋 ${key}: ${data[key].length} registros`);
                if (data[key].length > 0) {
                    console.log(`    🔍 Primeiro registro:`, data[key][0]);
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
        console.error(`❌ ERRO em ${endpoint}:`, error);
        throw error;
    }
}

function aplicarFiltros() {
    console.log('🔄 APLICANDO FILTROS...');
    
    const periodo = document.getElementById('filtro-periodo')?.value || 'todos';
    const bairro = document.getElementById('filtro-bairro')?.value || 'todos';
    
    console.log('🎯 Filtros selecionados:');
    console.log(`  📅 Período: ${periodo}`);
    console.log(`  🏘️ Bairro: ${bairro}`);
    
    // Recarregar gráficos
    loadAllChartsDebug();
}

function showError(message) {
    console.error('🚨 MOSTRANDO ERRO:', message);
    
    // Criar ou atualizar div de erro
    let errorDiv = document.getElementById('charts-error');
    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.id = 'charts-error';
        errorDiv.style.cssText = `
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            margin: 20px;
            border: 1px solid #f5c6cb;
            border-radius: 5px;
            font-weight: bold;
        `;
        
        const container = document.querySelector('.container');
        if (container) {
            container.insertBefore(errorDiv, container.firstChild);
        }
    }
    
    errorDiv.innerHTML = `
        <h3>❌ Erro nos Gráficos</h3>
        <p>${message}</p>
        <p><small>Verifique o console do navegador (F12) para mais detalhes.</small></p>
    `;
}

console.log('✅ CHARTS-DEBUG.JS carregado completamente');
