// ============================================
// CHARTS & ANALYTICS
// ============================================

let trendsChart = null;
let locationsChart = null;

async function initializeCharts() {
    await initTrendsChart();
    await initLocationsChart();
}

async function initTrendsChart() {
    const ctx = document.getElementById('trendsChart');
    if (!ctx) return;

    try {
        // Fetch violation trends data
        const response = await fetch(`${API_BASE}/violations/trends?days=7`);
        const result = await response.json();

        let labels = [];
        let data = [];

        if (result.success && result.data) {
            labels = result.data.map(item => item.date);
            data = result.data.map(item => item.count);
        } else {
            // Fallback: Generate sample data for last 7 days
            const today = new Date();
            for (let i = 6; i >= 0; i--) {
                const date = new Date(today);
                date.setDate(date.getDate() - i);
                labels.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
                data.push(Math.floor(Math.random() * 15) + 5); // Random 5-20
            }
        }

        if (trendsChart) {
            trendsChart.destroy();
        }

        trendsChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Violations Detected',
                    data: data,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#3b82f6',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        labels: {
                            color: '#e2e8f0',
                            font: { size: 12 }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.9)',
                        titleColor: '#f1f5f9',
                        bodyColor: '#e2e8f0',
                        borderColor: '#334155',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: '#94a3b8',
                            stepSize: 5
                        },
                        grid: {
                            color: 'rgba(148, 163, 184, 0.1)'
                        }
                    },
                    x: {
                        ticks: { color: '#94a3b8' },
                        grid: { display: false }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error initializing trends chart:', error);
    }
}

async function initLocationsChart() {
    const ctx = document.getElementById('locationsChart');
    if (!ctx) return;

    try {
        // Fetch violations by location
        const response = await fetch(`${API_BASE}/violations/by-location`);
        const result = await response.json();

        let labels = [];
        let data = [];
        let backgroundColors = [];

        if (result.success && result.data) {
            labels = result.data.map(item => item.location);
            data = result.data.map(item => item.count);
            // Generate colors
            backgroundColors = result.data.map((_, i) => {
                const colors = ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981'];
                return colors[i % colors.length];
            });
        } else {
            // Fallback: Sample data
            labels = ['National Road, Odiongan', 'Gate 3, RSU', 'Main Highway'];
            data = [45, 28, 12];
            backgroundColors = ['#3b82f6', '#8b5cf6', '#ec4899'];
        }

        if (locationsChart) {
            locationsChart.destroy();
        }

        locationsChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: backgroundColors,
                    borderColor: '#1e293b',
                    borderWidth: 2,
                    hoverOffset: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom',
                        labels: {
                            color: '#e2e8f0',
                            font: { size: 11 },
                            padding: 15,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.9)',
                        titleColor: '#f1f5f9',
                        bodyColor: '#e2e8f0',
                        borderColor: '#334155',
                        borderWidth: 1,
                        padding: 12,
                        callbacks: {
                            label: function (context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error initializing locations chart:', error);
    }
}

// Update stats cards
async function updateStatsCards() {
    try {
        const response = await fetch(`${API_BASE}/violations/stats`);
        const result = await response.json();

        if (result.success && result.data) {
            const stats = result.data;

            // Update stat cards
            const totalViolationsEl = document.getElementById('totalViolationsToday');
            if (totalViolationsEl) {
                totalViolationsEl.textContent = stats.today || 0;
            }

            const activeAlertsEl = document.getElementById('activeAlerts');
            if (activeAlertsEl) {
                activeAlertsEl.textContent = stats.pending || 0;
            }

            const citationsEl = document.getElementById('citationsIssued');
            if (citationsEl) {
                citationsEl.textContent = stats.verified || 0;
            }
        }
    } catch (error) {
        console.error('Error updating stats:', error);
    }
}
