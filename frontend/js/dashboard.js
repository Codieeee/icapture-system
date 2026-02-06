// iCapture Multi-Page Dashboard JavaScript

const API_BASE = '/api';
let currentPage = 1;
const itemsPerPage = 10;
let currentFilters = {
    status: '',
    search: '',
    dateRange: '',
    location: ''
};
let lastViolationsData = null;
let lastAlertsData = null;

// ========== PAGE NAVIGATION ==========
function initPageNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    const pages = document.querySelectorAll('.page-content');
    const pageTitle = document.querySelector('.page-title');

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetPage = link.getAttribute('data-page');

            // Update active link
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');

            // Show target page
            pages.forEach(p => p.classList.remove('active'));
            const page = document.getElementById(`${targetPage}-page`);
            if (page) {
                page.classList.add('active');

                // Update page title
                const pageNames = {
                    'dashboard': 'Dashboard',
                    'violations': 'Violations',
                    'reports': 'Reports & Analytics',
                    'settings': 'Settings'
                };
                pageTitle.textContent = pageNames[targetPage] || 'Dashboard';

                // Load page-specific data
                if (targetPage === 'dashboard') {
                    fetchAlerts();
                } else if (targetPage === 'violations') {
                    fetchViolations();
                } else if (targetPage === 'reports') {
                    fetchReportsData();
                }
            }
        });
    });
}

// ========== DATE/TIME ==========
function updateDateTime() {
    const now = new Date();
    const options = {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    const dateTimeEl = document.getElementById('currentDateTime');
    if (dateTimeEl) {
        dateTimeEl.textContent = now.toLocaleDateString('en-US', options);
    }
}

// ========== DASHBOARD - ALERTS TABLE ==========
async function fetchAlerts() {
    try {
        const response = await fetch(`${API_BASE}/violations?limit=5&status=pending`);
        const result = await response.json();

        if (result.success) {
            const dataString = JSON.stringify(result.data);
            if (dataString !== lastAlertsData) {
                lastAlertsData = dataString;
                displayAlerts(result.data);
            }
        }
    } catch (error) {
        console.error('Error fetching alerts:', error);
    }
}

function displayAlerts(alerts) {
    const tbody = document.getElementById('alertsTableBody');
    if (!tbody) return;

    if (alerts.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="no-data">No active alerts</td></tr>';
        return;
    }

    tbody.innerHTML = alerts.map(alert => `
        <tr>
            <td>${formatDateTime(alert.violation_datetime)}</td>
            <td><strong>${alert.plate_number || 'Not detected'}</strong></td>
            <td><span class="badge badge-no-helmet">No Helmet</span></td>
            <td>${alert.camera_id}</td>
        </tr>
    `).join('');
}

// ========== VIOLATIONS PAGE ==========
async function fetchViolations() {
    try {
        const params = new URLSearchParams({
            limit: itemsPerPage,
            offset: (currentPage - 1) * itemsPerPage
        });

        if (currentFilters.status) params.append('status', currentFilters.status);
        if (currentFilters.search) params.append('plate_number', currentFilters.search);

        const response = await fetch(`${API_BASE}/violations?${params}`);
        const result = await response.json();

        if (result.success) {
            const dataString = JSON.stringify(result.data);
            if (dataString !== lastViolationsData) {
                lastViolationsData = dataString;
                displayViolationsGrid(result.data);
            }
            updatePageInfo(result.count);
        }
    } catch (error) {
        console.error('Error fetching violations:', error);
    }
}

function displayViolationsGrid(violations) {
    const grid = document.getElementById('violationsGrid');
    if (!grid) return;

    if (violations.length === 0) {
        grid.innerHTML = '<div class="no-data" style="grid-column: 1/-1; padding: 3rem; text-align: center;">No violations found</div>';
        return;
    }

    grid.innerHTML = violations.map(v => `
        <div class="violation-card">
            <div class="violation-thumbnail">
                ${v.rider_image_path
            ? `<img src="${v.rider_image_path}" alt="Rider" class="thumbnail-img">`
            : '<div class="thumbnail-placeholder">📷</div>'
        }
            </div>
            
            <div class="violation-info">
                <div class="violation-time">${formatDateTime(v.violation_datetime)}</div>
                <div class="violation-location">${v.camera_location}</div>
            </div>
            
            <div class="violation-plate">
                ${v.plate_number || '<span style="color: var(--text-muted)">Not detected</span>'}
            </div>
            
            <span class="badge badge-${v.status}">${v.status.toUpperCase()}</span>
            
            <button class="btn-view" onclick="viewViolation(${v.id})">View Details</button>
        </div>
    `).join('');
}

// ========== VIEW VIOLATION MODAL ==========
async function viewViolation(id) {
    try {
        const response = await fetch(`${API_BASE}/violations/${id}`);
        const result = await response.json();

        if (result.success) {
            // Also fetch LTO data if plate number exists
            let ltoData = null;
            if (result.data.plate_number) {
                try {
                    const ltoResponse = await fetch(`${API_BASE}/lto/lookup/${result.data.plate_number}`);
                    const ltoResult = await ltoResponse.json();
                    if (ltoResult.success && ltoResult.found) {
                        ltoData = ltoResult.data;
                    }
                } catch (ltoError) {
                    console.log('LTO lookup unavailable:', ltoError);
                }
            }

            showViolationModal(result.data, ltoData);
        }
    } catch (error) {
        console.error('Error fetching violation:', error);
        showToast('Failed to load violation details');
    }
}


function showViolationModal(violation, ltoData = null) {
    const modal = document.getElementById('violationModal');
    const modalBody = document.getElementById('modalBody');

    modalBody.innerHTML = `
        <div class="modal-layout">
            <div class="modal-left">
                <h3 class="modal-section-title">Rider Identification</h3>
                <div class="evidence-image-large">
                    ${violation.rider_image_path
            ? `<img src="${violation.rider_image_path}" alt="Rider" class="modal-img">`
            : '<div class="modal-img-placeholder"><span style="font-size: 4rem">📷</span><p>No rider image</p></div>'
        }
                </div>
                
                <h3 class="modal-section-title">Plate Number</h3>
                <div class="evidence-image-large">
                    ${violation.plate_image_path
            ? `<img src="${violation.plate_image_path}" alt="Plate" class="modal-img">`
            : '<div class="modal-img-placeholder"><span style="font-size: 4rem">🚗</span><p>No plate image</p></div>'
        }
                </div>
            </div>
            
            <div class="modal-right">
                <h3 class="modal-section-title">Violation Details</h3>
                
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Plate Number</label>
                        <div class="detail-value">${violation.plate_number || 'Not detected'}</div>
                    </div>
                    
                    <div class="detail-item">
                        <label>Date & Time</label>
                        <div class="detail-value">${new Date(violation.violation_datetime).toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        })}</div>
                    </div>
                    
                    <div class="detail-item">
                        <label>Location</label>
                        <div class="detail-value">${violation.camera_location}</div>
                    </div>
                    
                    <div class="detail-item">
                        <label>Violation Type</label>
                        <div class="detail-value">
                            <span class="badge badge-${violation.violation_type === 'no_helmet' ? 'no-helmet' : 'nutshell'}">
                                ${violation.violation_type.replace('_', ' ').toUpperCase()}
                            </span>
                        </div>
                    </div>
                </div>
                
                ${ltoData ? `
                    <div style="background: var(--bg-primary); padding: 1rem; border-radius: var(--radius-md); margin: 1rem 0; border-left: 3px solid ${ltoData.is_fully_registered ? 'var(--success)' : 'var(--warning)'};">
                        <h4 style="font-size: 0.9375rem; margin-bottom: 0.75rem; color: var(--accent-secondary);">📋 LTO Registration Info</h4>
                        <div style="display: grid; gap: 0.5rem; font-size: 0.875rem;">
                            <div style="display: flex; justify-content: space-between;">
                                <span style="color: var(--text-muted);">Owner:</span>
                                <strong>${ltoData.owner_name}</strong>
                            </div>
                            <div style="display: flex; justify-content: space-between;">
                                <span style="color: var(--text-muted);">Status:</span>
                                <span style="color: ${ltoData.is_fully_registered ? 'var(--success)' : 'var(--warning)'}; font-weight: 600;">
                                    ${ltoData.validity_status}
                                </span>
                            </div>
                            ${!ltoData.is_fully_registered ? `
                                <div style="display: flex; justify-content: space-between;">
                                    <span style="color: var(--text-muted);">Missing:</span>
                                    <span style="color: var(--danger); font-weight: 600;">${ltoData.document_status}</span>
                                </div>
                            ` : ''}
                            ${ltoData.total_unpaid_fines > 0 ? `
                                <div style="display: flex; justify-content: space-between; margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px solid var(--border);">
                                    <span style="color: var(--text-muted);">Unpaid Fines:</span>
                                    <span style="color: var(--danger); font-weight: 600;">₱${parseFloat(ltoData.total_unpaid_fines).toLocaleString()}</span>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                ` : (violation.plate_number ? `
                    <div style="background: rgba(245, 158, 11, 0.1); padding: 1rem; border-radius: var(--radius-md); margin: 1rem 0; border-left: 3px solid var(--warning);">
                        <p style="font-size: 0.875rem; color: var(--text-muted); margin: 0;">ℹ️ No LTO record found</p>
                    </div>
                ` : '')}
                
                <h3 class="modal-section-title">Actions</h3>
                
                <button class="modal-btn modal-btn-primary">📋 Issue Citation</button>
                <button class="modal-btn modal-btn-warning">⚠️ Mark as False Positive</button>
                <button class="modal-btn modal-btn-secondary">📥 Export Data</button>
                
                <div style="margin-top: 1.5rem;">
                    <label style="display: block; margin-bottom: 0.5rem; font-weight: 600; color: var(--text-secondary);">Update Status</label>
                    <select id="statusUpdate" style="width: 100%; padding: 0.75rem; background: var(--bg-primary); border: 1px solid var(--border); border-radius: var(--radius-md); color: var(--text-primary); font-size: 0.875rem;">
                        <option value="pending" ${violation.status === 'pending' ? 'selected' : ''}>Pending Review</option>
                        <option value="verified" ${violation.status === 'verified' ? 'selected' : ''}>Citation Issued</option>
                        <option value="dismissed" ${violation.status === 'dismissed' ? 'selected' : ''}>Dismissed</option>
                    </select>
                    <button onclick="updateViolationStatus(${violation.id})" style="margin-top: 1rem; width: 100%; padding: 0.75rem; background: var(--accent-primary); color: white; border: none; border-radius: var(--radius-md); cursor: pointer; font-weight: 600; transition: background 0.2s;">
                        Update Status
                    </button>
                </div>
            </div>
        </div>
    `;

    modal.classList.add('active');
}

function closeModal() {
    document.getElementById('violationModal').classList.remove('active');
}

// ========== UPDATE VIOLATION STATUS ==========
async function updateViolationStatus(id) {
    const newStatus = document.getElementById('statusUpdate').value;

    try {
        const response = await fetch(`${API_BASE}/violations/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus })
        });

        const result = await response.json();

        if (result.success) {
            showToast('Status updated successfully');
            closeModal();
            fetchViolations();
            fetchAlerts();
        } else {
            showToast('Failed to update status');
        }
    } catch (error) {
        console.error('Error updating status:', error);
        showToast('Error updating status');
    }
}

// ========== REPORTS PAGE ==========
async function fetchReportsData() {
    try {
        const response = await fetch(`${API_BASE}/dashboard/stats`);
        const result = await response.json();

        if (result.success) {
            displayReportsStats(result.data);
        }
    } catch (error) {
        console.error('Error fetching reports data:', error);
    }
}

function displayReportsStats(data) {
    // Update stat cards
    const totalEl = document.getElementById('totalViolationsToday');
    const alertsEl = document.getElementById('activeAlerts');
    const citationsEl = document.getElementById('citationsIssued');

    if (totalEl) totalEl.textContent = data.today?.total_violations || 0;
    if (alertsEl) alertsEl.textContent = data.pending_count || 0;
    if (citationsEl) citationsEl.textContent = data.today?.verified || 0;

    // Initialize charts (placeholder - would use Chart.js in production)
    initCharts();
}

function initCharts() {
    // Placeholder for chart initialization
    // In production, you would use Chart.js here
    console.log('Charts initialized');
}

// ========== UTILITIES ==========
function formatDateTime(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleString('en-US', {
        month: '2-digit',
        day: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function showToast(message) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.add('show');

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

function updatePageInfo(count) {
    const pageInfo = document.getElementById('pageInfo');
    if (pageInfo) {
        pageInfo.textContent = `Page ${currentPage}`;
    }

    const prevBtn = document.getElementById('prevPage');
    const nextBtn = document.getElementById('nextPage');

    if (prevBtn) prevBtn.disabled = currentPage === 1;
    if (nextBtn) nextBtn.disabled = count < itemsPerPage;
}

// ========== INITIALIZATION ==========
document.addEventListener('DOMContentLoaded', () => {
    // Initialize page navigation
    initPageNavigation();

    // Update datetime
    updateDateTime();
    setInterval(updateDateTime, 60000);

    // Load initial data for dashboard
    fetchAlerts();

    // Auto-refresh alerts every 5 seconds
    setInterval(fetchAlerts, 5000);

    // Search and filters
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            currentFilters.search = e.target.value;
            currentPage = 1;
            fetchViolations();
        });
    }

    const statusFilter = document.getElementById('statusFilter');
    if (statusFilter) {
        statusFilter.addEventListener('change', (e) => {
            currentFilters.status = e.target.value;
            currentPage = 1;
            fetchViolations();
        });
    }

    // Pagination
    const prevBtn = document.getElementById('prevPage');
    const nextBtn = document.getElementById('nextPage');

    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            if (currentPage > 1) {
                currentPage--;
                fetchViolations();
            }
        });
    }

    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            currentPage++;
            fetchViolations();
        });
    }

    // Modal close
    const closeModalBtn = document.getElementById('closeModal');
    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', closeModal);
    }

    const modal = document.getElementById('violationModal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target.id === 'violationModal') {
                closeModal();
            }
        });
    }
});

// ============================================
// REPORTS PAGE - CHARTS & ANALYTICS
// ============================================

let trendsChart = null;
let locationsChart = null;

async function updateReportsPage() {
    await updateStatsCards();
    await initializeCharts();
}

async function updateStatsCards() {
    try {
        const response = await fetch(`${API_BASE}/violations?limit=1000`);
        const result = await response.json();

        if (result.success && result.data) {
            const today = new Date().toDateString();
            const todayViolations = result.data.filter(v => {
                return new Date(v.violation_datetime).toDateString() === today;
            });

            const pending = result.data.filter(v => v.status === 'pending').length;
            const verified = result.data.filter(v => v.status === 'verified').length;

            const totalViolationsEl = document.getElementById('totalViolationsToday');
            if (totalViolationsEl) totalViolationsEl.textContent = todayViolations.length;

            const activeAlertsEl = document.getElementById('activeAlerts');
            if (activeAlertsEl) activeAlertsEl.textContent = pending;

            const citationsEl = document.getElementById('citationsIssued');
            if (citationsEl) citationsEl.textContent = verified;
        }
    } catch (error) {
        console.error('Error updating stats:', error);
    }
}

async function initializeCharts() {
    await initTrendsChart();
    await initLocationsChart();
}

async function initTrendsChart() {
    const ctx = document.getElementById('trendsChart');
    if (!ctx) return;

    try {
        const response = await fetch(`${API_BASE}/violations?limit=100`);
        const result = await response.json();

        let labels = [];
        let data = [];

        if (result.success && result.data && result.data.length > 0) {
            // Group violations by date
            const dateGroups = {};
            result.data.forEach(violation => {
                const date = new Date(violation.violation_datetime);
                const dateKey = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                dateGroups[dateKey] = (dateGroups[dateKey] || 0) + 1;
            });

            // Get last 7 unique dates
            labels = Object.keys(dateGroups).slice(-7);
            data = labels.map(label => dateGroups[label] || 0);
        } else {
            // Fallback: Generate sample data for last 7 days
            const today = new Date();
            for (let i = 6; i >= 0; i--) {
                const date = new Date(today);
                date.setDate(date.getDate() - i);
                labels.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
                data.push(Math.floor(Math.random() * 15) + 5);
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
                        padding: 12
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { color: '#94a3b8', stepSize: 5 },
                        grid: { color: 'rgba(148, 163, 184, 0.1)' }
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
        const response = await fetch(`${API_BASE}/violations?limit=100`);
        const result = await response.json();

        let labels = [];
        let data = [];

        if (result.success && result.data && result.data.length > 0) {
            // Group by location
            const locationGroups = {};
            result.data.forEach(violation => {
                const location = violation.camera_location || 'Unknown';
                locationGroups[location] = (locationGroups[location] || 0) + 1;
            });

            labels = Object.keys(locationGroups);
            data = labels.map(label => locationGroups[label]);
        } else {
            labels = ['National Road, Odiongan'];
            data = [100];
        }

        const backgroundColors = ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981'];

        if (locationsChart) {
            locationsChart.destroy();
        }

        locationsChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: backgroundColors.slice(0, data.length),
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

