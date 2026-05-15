globalThis.charts = globalThis.charts || {};

// Función helper para validar datos del gráfico
function hasValidChartData(series) {
    if (!series || series.length === 0) return false;
    
    const firstSeries = series[0];
    if (!firstSeries?.data || firstSeries.data.length === 0) return false;
    
    const allDataIsZero = firstSeries.data.every(value => value === 0);
    return !allDataIsZero;
}

// Función helper para mostrar mensaje de "sin datos"
function showNoDataMessage(containerId) {
    const container = document.querySelector(`#${containerId}`);
    if (container) {
        container.innerHTML = `
            <div class="flex flex-col items-center justify-center h-full text-gray-400 text-sm">
                <svg class="w-12 h-12 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
                </svg>
                <p>Sin datos para mostrar</p>
            </div>
        `;
    }
}

// Función para descargar gráfico como imagen
function downloadChart(chartId, format = 'png') {
    const chart = globalThis.charts[chartId];
    if (!chart) {
        console.warn(`Chart ${chartId} not found`);
        return;
    }
    
    const formats = ['png', 'jpg', 'svg'];
    if (!formats.includes(format)) {
        console.warn(`Invalid format: ${format}. Using png.`);
        format = 'png';
    }
    
    chart.dataURI().then(uri => {
        const link = document.createElement('a');
        link.download = `chart-${chartId}-${new Date().toISOString().slice(0, 19)}.${format}`;
        link.href = uri;
        link.click();
    }).catch(error => {
        console.error('Error downloading chart:', error);
    });
}

// Función para actualizar gráfico con nuevos datos
function updateChartData(chartId, newData) {
    const chart = globalThis.charts[chartId];
    if (!chart) {
        console.warn(`Chart ${chartId} not found`);
        return false;
    }
    
    try {
        const series = newData.series || [];
        const categories = newData.categories || [];
        
        // Validar nuevos datos
        if (!hasValidChartData(series)) {
            showNoDataMessage(chartId);
            return false;
        }
        
        chart.updateSeries(series);
        
        if (categories && categories.length > 0) {
            chart.updateOptions({
                xaxis: { categories: categories }
            });
        }
        
        return true;
    } catch (error) {
        console.error('Error updating chart data:', error);
        return false;
    }
}

// Función para cambiar tema del gráfico
function setChartTheme(chartId, theme = 'dark') {
    const chart = globalThis.charts[chartId];
    if (!chart) {
        console.warn(`Chart ${chartId} not found`);
        return false;
    }
    
    const validThemes = ['dark', 'light'];
    if (!validThemes.includes(theme)) {
        console.warn(`Invalid theme: ${theme}. Using dark.`);
        theme = 'dark';
    }
    
    chart.updateOptions({
        tooltip: { theme: theme }
    });
    
    return true;
}

// Función principal para inicializar gráfico
function initChart(chartId, chartData, chartType, yaxisLabel = 'COP') {
    if (typeof ApexCharts === 'undefined') {
        setTimeout(() => initChart(chartId, chartData, chartType, yaxisLabel), 200);
        return;
    }
    
    let series = [];
    let categories = [];
    
    if (chartType === 'donut') {
        series = chartData.series || [];
        categories = chartData.labels || [];
    } else {
        series = chartData.series || [];
        categories = chartData.categories || [];
    }
    
    // Validar datos
    if (!hasValidChartData(series)) {
        showNoDataMessage(chartId);
        return;
    }
    
    const options = {
        series: series,
        chart: {
            type: chartType,
            height: '100%',
            toolbar: {
                show: true,
                tools: {
                    download: false, // Deshabilitamos el nativo para usar el personalizado
                    selection: true,
                    zoom: true,
                    zoomin: true,
                    zoomout: true,
                    pan: true,
                    reset: true
                }
            },
            zoom: { enabled: true },
            fontFamily: 'Inter, sans-serif',
            background: 'transparent',
            events: {
                mounted: function(chart) {
                    // Agregar botón de descarga personalizado
                    const toolbar = chart.w.globals.dom.baseEl.querySelector('.apexcharts-toolbar');
                    if (toolbar && !toolbar.querySelector('.custom-download-btn')) {
                        const downloadBtn = document.createElement('button');
                        downloadBtn.className = 'custom-download-btn';
                        downloadBtn.innerHTML = '💾';
                        downloadBtn.title = 'Descargar como PNG';
                        downloadBtn.style.cssText = `
                            background: none;
                            border: none;
                            cursor: pointer;
                            font-size: 16px;
                            padding: 4px;
                            margin-left: 8px;
                        `;
                        downloadBtn.onclick = () => downloadChart(chartId, 'png');
                        toolbar.appendChild(downloadBtn);
                    }
                }
            }
        },
        title: { text: undefined },
        xaxis: {
            categories: categories,
            labels: {
                rotate: -45,
                style: { fontSize: '11px' },
                formatter: function(val) {
                    return val;
                }
            },
            title: {
                text: 'Fecha'
            }
        },
        yaxis: {
            title: { text: yaxisLabel },
            labels: {
                formatter: function(val) {
                    if (yaxisLabel === 'COP') {
                        return '$' + val.toLocaleString('es-CO');
                    }
                    return val.toLocaleString('es-CO');
                }
            }
        },
        colors: ['#a91600', '#f59e0b', '#10b981', '#3b82f6'],
        stroke: { curve: 'smooth', width: 2 },
        fill: {
            type: chartType === 'donut' ? 'solid' : 'gradient',
            gradient: {
                shadeIntensity: 0.5,
                opacityFrom: 0.7,
                opacityTo: 0.3
            }
        },
        tooltip: {
            theme: 'dark',
            y: {
                formatter: function(val) {
                    if (yaxisLabel === 'COP') {
                        return '$' + val.toLocaleString('es-CO') + ' COP';
                    }
                    return val.toLocaleString('es-CO');
                }
            }
        },
        grid: { borderColor: '#f1f5f9' },
        responsive: [{
            breakpoint: 480,
            options: {
                chart: {
                    height: 250
                },
                legend: {
                    position: 'bottom'
                }
            }
        }]
    };
    
    if (chartType === 'donut') {
        options.labels = categories;
        options.plotOptions = {
            donut: {
                size: '65%',
                labels: {
                    show: true,
                    total: {
                        show: true,
                        label: 'Total',
                        formatter: function(w) {
                            return w.globals.seriesTotals.reduce((a, b) => a + b, 0);
                        }
                    }
                }
            }
        };
    }
    
    if (chartType === 'bar') {
        options.plotOptions = {
            bar: {
                horizontal: false,
                columnWidth: '55%',
                borderRadius: 4
            }
        };
    }
    
    try {
        const chart = new ApexCharts(document.querySelector(`#${chartId}`), options);
        chart.render();
        
        // Guardar referencia del gráfico
        globalThis.charts[chartId] = chart;
        
        // Agregar evento de resize automático
        if (!globalThis.chartsResizeHandler) {
            globalThis.chartsResizeHandler = true;
            globalThis.addEventListener('resize', () => {
                Object.values(globalThis.charts).forEach(chart => {
                    if (chart && typeof chart.updateOptions === 'function') {
                        chart.updateOptions({ chart: { width: '100%' } });
                    }
                });
            });
        }
        
    } catch (error) {
        console.error('Error rendering chart:', chartId, error);
    }
}

// Inicializar todos los gráficos al cargar la página
document.addEventListener('DOMContentLoaded', function() {
    const scriptElements = document.querySelectorAll('script[type="application/json"]');
    
    if (scriptElements.length === 0) {
        return;
    }
    
    scriptElements.forEach(script => {
        const chartId = script.id;
        if (!chartId) return;
        
        try {
            const chartData = JSON.parse(script.textContent);
            const chartContainer = document.getElementById(chartId);
            
            const hasContainer = chartContainer !== null;
            const hasChartType = hasContainer && 'chartType' in chartContainer.dataset;
            
            if (hasContainer && hasChartType) {
                const chartType = chartContainer.dataset.chartType || 'line';
                const yaxisLabel = chartContainer.dataset.yaxisLabel || 'COP';
                initChart(chartId, chartData, chartType, yaxisLabel);
            }
        } catch (error) {
            console.error('Error parsing chart data for', chartId, error);
        }
    });
});

globalThis.ZicadaCharts = {
    download: downloadChart,
    update: updateChartData,
    setTheme: setChartTheme
};