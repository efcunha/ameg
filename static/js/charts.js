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
    loadAllCharts();
});

async function loadAllCharts() {
    try {
        showLoading();
        
        // Carregar dados em paralelo
        const [demografiaData, saudeData, socioeconomicoData, trabalhoData] = await Promise.all([
            fetch('/api/charts/demografia').then(r => r.json()),
            fetch('/api/charts/saude').then(r => r.json()),
            fetch('/api/charts/socioeconomico').then(r => r.json()),
            fetch('/api/charts/trabalho').then(r => r.json())
        ]);

        // Criar gráficos de demografia
        createIdadeChart(demografiaData.idade);
        createBairrosChart(demografiaData.bairros);
        createEvolucaoChart(demografiaData.evolucao);

        // Criar gráficos de saúde
        createDoencasChart(saudeData.doencas);
        createMedicamentosChart(saudeData.medicamentos);
        createDeficienciasChart(saudeData.deficiencias);

        // Criar gráficos socioeconômicos
        createRendaChart(socioeconomicoData.renda);
        createMoradiaChart(socioeconomicoData.moradia);
        createBeneficiosChart(socioeconomicoData.beneficios);

        // Criar gráficos de trabalho
        createTiposTrabalhoChart(trabalhoData.tipos);
        createLocaisTrabalhoChart(trabalhoData.locais);

        hideLoading();
    } catch (error) {
        console.error('Erro ao carregar gráficos:', error);
        hideLoading();
    }
}

// Gráficos de Demografia
function createIdadeChart(data) {
    const ctx = document.getElementById('idadeChart').getContext('2d');
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
    const ctx = document.getElementById('doencasChart').getContext('2d');
    charts.doencas = new Chart(ctx, {
        type: 'horizontalBar',
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
    const ctx = document.getElementById('medicamentosChart').getContext('2d');
    charts.medicamentos = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: data.map(d => d.medicamentos_uso),
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
    const ctx = document.getElementById('deficienciasChart').getContext('2d');
    charts.deficiencias = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.map(d => d.deficiencia_tipo),
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
    const ctx = document.getElementById('beneficiosChart').getContext('2d');
    charts.beneficios = new Chart(ctx, {
        type: 'horizontalBar',
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
        card.innerHTML = '<div class="loading">Carregando gráfico...</div>';
    });
}

function hideLoading() {
    // Loading será removido quando os gráficos forem criados
}

function aplicarFiltros() {
    // Implementar filtros dinâmicos
    console.log('Aplicando filtros...');
    // Recarregar gráficos com filtros aplicados
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
