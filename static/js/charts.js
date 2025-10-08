// Configurações globais dos gráficos
Chart.defaults.font.family = 'Arial, sans-serif';
Chart.defaults.font.size = 12;

// Paleta de cores AMEG
const colors = {
    primary: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40'],
    success: '#28a745',
    warning: '#ffc107',
    danger: '#dc3545',
    info: '#17a2b8'
};

// Variáveis globais para os gráficos
let charts = {};

// Inicializar gráficos ao carregar a página
document.addEventListener('DOMContentLoaded', function() {
    console.log('Iniciando carregamento dos gráficos...');
    loadFilterOptions();
    loadAllCharts();
});

async function loadFilterOptions() {
    try {
        const response = await fetch('/api/charts/filters');
        const data = await response.json();
        
        // Preencher dropdown de bairros
        const bairroSelect = document.getElementById('filtro-bairro');
        if (bairroSelect && data.bairros) {
            // Limpar opções existentes (exceto "Todos")
            while (bairroSelect.children.length > 1) {
                bairroSelect.removeChild(bairroSelect.lastChild);
            }
            
            // Adicionar opções de bairros
            data.bairros.forEach(bairro => {
                const option = document.createElement('option');
                option.value = bairro.value;
                option.textContent = bairro.label;
                bairroSelect.appendChild(option);
            });
        }
        
        console.log('Opções de filtros carregadas:', data);
    } catch (error) {
        console.error('Erro ao carregar opções de filtros:', error);
    }
}

async function loadAllCharts() {
    try {
        showLoading();
        console.log('Carregando dados dos gráficos...');
        
        // Obter valores dos filtros
        const periodo = document.getElementById('filtro-periodo')?.value || 'todos';
        const bairro = document.getElementById('filtro-bairro')?.value || 'todos';
        
        // Construir query string com filtros apenas se não for "todos"
        const params = new URLSearchParams();
        if (periodo && periodo !== 'todos') params.append('periodo', periodo);
        if (bairro && bairro !== 'todos') params.append('bairro', bairro);
        
        const queryString = params.toString();
        const urlSuffix = queryString ? `?${queryString}` : '';
        
        console.log('Aplicando filtros:', { periodo, bairro, queryString, urlSuffix });
        
        // Carregar dados em paralelo
        const [demografiaData, saudeData, socioeconomicoData, trabalhoData] = await Promise.all([
            fetch(`/api/charts/demografia${urlSuffix}`).then(r => {
                console.log('Demografia response:', r.status);
                return r.json();
            }),
            fetch(`/api/charts/saude${urlSuffix}`).then(r => {
                console.log('Saude response:', r.status);
                return r.json();
            }),
            fetch(`/api/charts/socioeconomico${urlSuffix}`).then(r => {
                console.log('Socioeconomico response:', r.status);
                return r.json();
            }),
            fetch(`/api/charts/trabalho${urlSuffix}`).then(r => {
                console.log('Trabalho response:', r.status);
                return r.json();
            })
        ]);

        console.log('Dados carregados:', {demografiaData, saudeData, socioeconomicoData, trabalhoData});

        // Destruir gráficos existentes antes de criar novos
        Object.values(charts).forEach(chart => {
            if (chart) chart.destroy();
        });
        charts = {};

        // Criar gráficos de demografia
        if (demografiaData.idade) createIdadeChart(demografiaData.idade);
        if (demografiaData.bairros) createBairrosChart(demografiaData.bairros);
        if (demografiaData.evolucao) createEvolucaoChart(demografiaData.evolucao);

        // Criar gráficos de saúde
        if (saudeData.doencas) createDoencasChart(saudeData.doencas);
        if (saudeData.medicamentos) createMedicamentosChart(saudeData.medicamentos);
        if (saudeData.deficiencias) createDeficienciasChart(saudeData.deficiencias);

        // Criar gráficos socioeconômicos
        if (socioeconomicoData.renda) createRendaChart(socioeconomicoData.renda);
        if (socioeconomicoData.moradia) createMoradiaChart(socioeconomicoData.moradia);
        if (socioeconomicoData.beneficios) createBeneficiosChart(socioeconomicoData.beneficios);

        // Criar gráficos de trabalho
        if (trabalhoData.tipos) createTiposTrabalhoChart(trabalhoData.tipos);
        if (trabalhoData.locais) createLocaisTrabalhoChart(trabalhoData.locais);

        hideLoading();
        console.log('Gráficos carregados com sucesso!');
    } catch (error) {
        console.error('Erro ao carregar gráficos:', error);
        hideLoading();
        showError('Erro ao carregar gráficos: ' + error.message);
    }
}

// Gráficos de Demografia
function createIdadeChart(data) {
    if (!data || data.length === 0) {
        console.log('Sem dados para gráfico de idade');
        return;
    }
    
    const canvasElement = document.getElementById('idadeChart');
    if (!canvasElement) {
        console.error('Elemento idadeChart não encontrado');
        return;
    }
    
    const ctx = canvasElement.getContext('2d');
    charts.idade = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.map(d => d.faixa),
            datasets: [{
                data: data.map(d => d.total),
                backgroundColor: colors.primary,
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom' },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.parsed * 100) / total).toFixed(1);
                            return `${context.label}: ${context.parsed} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

function createBairrosChart(data) {
    if (!data || data.length === 0) {
        console.log('Sem dados para gráfico de bairros');
        return;
    }
    
    const ctx = document.getElementById('bairrosChart').getContext('2d');
    charts.bairros = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.bairro),
            datasets: [{
                label: 'Cadastros',
                data: data.map(d => d.total),
                backgroundColor: colors.info,
                borderColor: colors.info,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: true }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

function createEvolucaoChart(data) {
    if (!data || data.length === 0) {
        console.log('Sem dados para gráfico de evolução');
        return;
    }
    
    const ctx = document.getElementById('evolucaoChart').getContext('2d');
    charts.evolucao = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => d.mes),
            datasets: [{
                label: 'Novos Cadastros',
                data: data.map(d => d.total),
                borderColor: colors.success,
                backgroundColor: colors.success + '20',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

// Gráficos de Saúde
function createDoencasChart(data) {
    if (!data || data.length === 0) {
        console.log('Sem dados para gráfico de doenças');
        return;
    }
    
    const ctx = document.getElementById('doencasChart').getContext('2d');
    charts.doencas = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.doencas_cronicas),
            datasets: [{
                label: 'Casos',
                data: data.map(d => d.total),
                backgroundColor: colors.danger,
                borderColor: colors.danger,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            indexAxis: 'y',
            scales: {
                x: { beginAtZero: true }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

function createMedicamentosChart(data) {
    if (!data || data.length === 0) {
        console.log('Sem dados para gráfico de medicamentos');
        return;
    }
    
    const canvasElement = document.getElementById('medicamentosChart');
    if (!canvasElement) {
        console.error('Elemento medicamentosChart não encontrado');
        return;
    }
    
    const ctx = canvasElement.getContext('2d');
    charts.medicamentos = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: data.map(d => d.medicamentos_continuos),
            datasets: [{
                data: data.map(d => d.total),
                backgroundColor: colors.primary
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
}

function createDeficienciasChart(data) {
    if (!data || data.length === 0) {
        console.log('Sem dados para gráfico de deficiências');
        return;
    }
    
    const canvasElement = document.getElementById('deficienciasChart');
    if (!canvasElement) {
        console.error('Elemento deficienciasChart não encontrado');
        return;
    }
    
    const ctx = canvasElement.getContext('2d');
    charts.deficiencias = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.map(d => d.tipo_deficiencia),
            datasets: [{
                data: data.map(d => d.total),
                backgroundColor: colors.primary
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
}

// Gráficos Socioeconômicos
function createRendaChart(data) {
    if (!data || data.length === 0) {
        console.log('Sem dados para gráfico de renda');
        return;
    }
    
    const ctx = document.getElementById('rendaChart').getContext('2d');
    charts.renda = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.faixa_renda),
            datasets: [{
                label: 'Famílias',
                data: data.map(d => d.total),
                backgroundColor: colors.warning,
                borderColor: colors.warning,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: true }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

function createMoradiaChart(data) {
    if (!data || data.length === 0) {
        console.log('Sem dados para gráfico de moradia');
        return;
    }
    
    const ctx = document.getElementById('moradiaChart').getContext('2d');
    charts.moradia = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: data.map(d => d.casa_tipo),
            datasets: [{
                data: data.map(d => d.total),
                backgroundColor: colors.primary
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
}

function createBeneficiosChart(data) {
    if (!data || data.length === 0) {
        console.log('Sem dados para gráfico de benefícios');
        return;
    }
    
    const ctx = document.getElementById('beneficiosChart').getContext('2d');
    charts.beneficios = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.beneficios_sociais),
            datasets: [{
                label: 'Beneficiários',
                data: data.map(d => d.total),
                backgroundColor: colors.success,
                borderColor: colors.success,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            indexAxis: 'y',
            scales: {
                x: { beginAtZero: true }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

// Gráficos de Trabalho
function createTiposTrabalhoChart(data) {
    if (!data || data.length === 0) {
        console.log('Sem dados para gráfico de tipos de trabalho');
        return;
    }
    
    const ctx = document.getElementById('tiposTrabalhoChart').getContext('2d');
    charts.tiposTrabalho = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.map(d => d.tipo_trabalho),
            datasets: [{
                data: data.map(d => d.total),
                backgroundColor: colors.primary
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
}

function createLocaisTrabalhoChart(data) {
    if (!data || data.length === 0) {
        console.log('Sem dados para gráfico de locais de trabalho');
        return;
    }
    
    const ctx = document.getElementById('locaisTrabalhoChart').getContext('2d');
    charts.locaisTrabalho = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.local_trabalho),
            datasets: [{
                label: 'Trabalhadores',
                data: data.map(d => d.total),
                backgroundColor: colors.info,
                borderColor: colors.info,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: true }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

// Funções auxiliares
function showLoading() {
    document.querySelectorAll('.chart-card').forEach(card => {
        const canvas = card.querySelector('canvas');
        if (canvas) {
            canvas.style.display = 'none';
        }
        
        // Adicionar loading sem usar innerHTML
        let loadingDiv = card.querySelector('.loading');
        if (!loadingDiv) {
            loadingDiv = document.createElement('div');
            loadingDiv.className = 'loading';
            loadingDiv.textContent = 'Carregando gráfico...';
            card.appendChild(loadingDiv);
        }
        loadingDiv.style.display = 'block';
    });
}

function hideLoading() {
    document.querySelectorAll('.chart-card').forEach(card => {
        const canvas = card.querySelector('canvas');
        const loadingDiv = card.querySelector('.loading');
        
        if (canvas) {
            canvas.style.display = 'block';
        }
        if (loadingDiv) {
            loadingDiv.style.display = 'none';
        }
    });
}

function showError(message) {
    document.querySelectorAll('.chart-card').forEach(card => {
        card.innerHTML = `<div class="loading" style="color: red;">❌ ${message}</div>`;
    });
}

function aplicarFiltros() {
    console.log('Aplicando filtros...');
    
    // Obter valores dos filtros
    const periodo = document.getElementById('filtro-periodo')?.value || 'todos';
    const bairro = document.getElementById('filtro-bairro')?.value || 'todos';
    
    console.log('Filtros selecionados:', { periodo, bairro });
    
    // Recarregar gráficos com filtros
    loadAllCharts();
}

// Função para exportar gráfico
function exportChart(chartName) {
    const chart = charts[chartName];
    if (chart) {
        const url = chart.toBase64Image();
        const link = document.createElement('a');
        link.download = `grafico_${chartName}.png`;
        link.href = url;
        link.click();
    }
}
