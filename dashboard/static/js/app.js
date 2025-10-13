// Echerga Stats Dashboard - Main JavaScript

let waitTimeChart = null;
let vehicleCountChart = null;
let checkpoints = [];

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeDateInput();
    loadCheckpoints();
    loadLatestStatus();
    setupEventListeners();
});

function initializeDateInput() {
    const dateInput = document.getElementById('dateInput');
    const today = new Date().toISOString().split('T')[0];
    dateInput.value = today;
    dateInput.max = today;
}

function setupEventListeners() {
    document.getElementById('loadBtn').addEventListener('click', loadCheckpointData);
    document.getElementById('checkpointSelect').addEventListener('change', () => {
        if (document.getElementById('checkpointSelect').value) {
            loadCheckpointData();
        }
    });
}

async function loadCheckpoints() {
    try {
        const response = await fetch('/api/checkpoints');
        checkpoints = await response.json();

        const select = document.getElementById('checkpointSelect');
        select.innerHTML = '<option value="">Оберіть пункт пропуску...</option>';

        checkpoints.forEach(checkpoint => {
            const option = document.createElement('option');
            option.value = checkpoint.id;
            option.textContent = checkpoint.title;
            select.appendChild(option);
        });

        // Auto-select first checkpoint and load data
        if (checkpoints.length > 0) {
            select.value = checkpoints[0].id;
            loadCheckpointData();
        }
    } catch (error) {
        console.error('Error loading checkpoints:', error);
        showError('Помилка завантаження пунктів пропуску');
    }
}

async function loadLatestStatus() {
    try {
        const response = await fetch('/api/latest');
        const data = await response.json();

        const container = document.getElementById('latestStatus');
        container.innerHTML = '';

        data.forEach(item => {
            const card = createStatusCard(item);
            container.appendChild(card);
        });
    } catch (error) {
        console.error('Error loading latest status:', error);
    }
}

function createStatusCard(item) {
    const div = document.createElement('div');
    div.className = 'status-card border rounded-lg p-4 hover:shadow-lg transition-shadow';

    const waitTimeHours = Math.round(item.wait_time / 3600);
    const statusBadge = getStatusBadge(item.is_paused, waitTimeHours);

    div.innerHTML = `
        <div class="flex justify-between items-start mb-2">
            <h3 class="font-semibold text-sm text-gray-800">${item.title}</h3>
            ${statusBadge}
        </div>
        <div class="space-y-1 text-sm">
            <div class="flex justify-between">
                <span class="text-gray-600">Очікування:</span>
                <span class="font-medium">${waitTimeHours}г</span>
            </div>
            <div class="flex justify-between">
                <span class="text-gray-600">Транспорт:</span>
                <span class="font-medium">${item.vehicle_in_active_queues_counts}</span>
            </div>
        </div>
    `;

    return div;
}

function getStatusBadge(isPaused, waitTimeHours) {
    if (isPaused) {
        return '<span class="badge badge-gray">Зупинено</span>';
    }
    if (waitTimeHours < 2) {
        return '<span class="badge badge-green">Вільно</span>';
    }
    if (waitTimeHours < 6) {
        return '<span class="badge badge-yellow">Помірно</span>';
    }
    return '<span class="badge badge-red">Затор</span>';
}

async function loadCheckpointData() {
    const checkpointId = document.getElementById('checkpointSelect').value;
    const date = document.getElementById('dateInput').value;

    if (!checkpointId || !date) {
        return;
    }

    try {
        // Get timezone offset in minutes
        const timezoneOffset = new Date().getTimezoneOffset();
        const response = await fetch(`/api/checkpoint/${checkpointId}/day/${date}?tz_offset=${timezoneOffset}`);
        const data = await response.json();

        if (data.error) {
            showError(data.error);
            return;
        }

        if (data.length === 0) {
            showError('Немає даних за обрану дату');
            return;
        }

        updateCharts(data);
        updateStatsCards(data);
    } catch (error) {
        console.error('Error loading checkpoint data:', error);
        showError('Помилка завантаження даних');
    }
}

function updateCharts(data) {
    const labels = data.map(item => {
        const date = new Date(item.created_at);
        return date.toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' });
    });

    const waitTimes = data.map(item => Math.round(item.wait_time / 3600)); // Convert to hours
    const vehicleCounts = data.map(item => item.vehicle_in_active_queues_counts);

    // Wait Time Chart
    if (waitTimeChart) {
        waitTimeChart.destroy();
    }

    const waitTimeCtx = document.getElementById('waitTimeChart').getContext('2d');
    waitTimeChart = new Chart(waitTimeCtx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Час очікування (години)',
                data: waitTimes,
                borderColor: 'rgb(59, 130, 246)',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value + 'г';
                        }
                    }
                }
            }
        }
    });

    // Vehicle Count Chart
    if (vehicleCountChart) {
        vehicleCountChart.destroy();
    }

    const vehicleCtx = document.getElementById('vehicleCountChart').getContext('2d');
    vehicleCountChart = new Chart(vehicleCtx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Кількість транспорту',
                data: vehicleCounts,
                backgroundColor: 'rgba(16, 185, 129, 0.6)',
                borderColor: 'rgb(16, 185, 129)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

function updateStatsCards(data) {
    const container = document.getElementById('statsCards');

    const avgWaitTime = Math.round(data.reduce((sum, item) => sum + item.wait_time, 0) / data.length / 3600);
    const maxWaitTime = Math.round(Math.max(...data.map(item => item.wait_time)) / 3600);
    const avgVehicles = Math.round(data.reduce((sum, item) => sum + item.vehicle_in_active_queues_counts, 0) / data.length);
    const maxVehicles = Math.max(...data.map(item => item.vehicle_in_active_queues_counts));

    container.innerHTML = `
        <div class="stat-card">
            <div class="stat-label">Середній час</div>
            <div class="stat-value">${avgWaitTime}г</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Макс. час</div>
            <div class="stat-value">${maxWaitTime}г</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Середньо авто</div>
            <div class="stat-value">${avgVehicles}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Макс. авто</div>
            <div class="stat-value">${maxVehicles}</div>
        </div>
    `;
}

function showError(message) {
    alert(message);
}
