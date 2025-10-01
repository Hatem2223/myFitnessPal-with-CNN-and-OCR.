/**
 * Student CRM System - Main JavaScript Application
 * Handles authentication, routing, and API interactions
 */

// API Base URL
const API_BASE = '/api';

// Global state
const AppState = {
    currentUser: null,
    currentPage: 'dashboard',
    students: [],
    notifications: []
};

// Authentication Service
const AuthService = {
    async login(email, password) {
        try {
            const response = await fetch(`${API_BASE}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ email, password })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                AppState.currentUser = data.user;
                localStorage.setItem('user', JSON.stringify(data.user));
                return { success: true, user: data.user };
            } else {
                return { success: false, error: data.error };
            }
        } catch (error) {
            return { success: false, error: 'Network error' };
        }
    },
    
    async logout() {
        try {
            await fetch(`${API_BASE}/auth/logout`, {
                method: 'POST',
                credentials: 'include'
            });
            
            AppState.currentUser = null;
            localStorage.removeItem('user');
            showPage('login');
        } catch (error) {
            console.error('Logout error:', error);
        }
    },
    
    async getCurrentUser() {
        try {
            const response = await fetch(`${API_BASE}/auth/me`, {
                credentials: 'include'
            });
            
            if (response.ok) {
                const data = await response.json();
                AppState.currentUser = data.user;
                localStorage.setItem('user', JSON.stringify(data.user));
                return data.user;
            } else {
                return null;
            }
        } catch (error) {
            return null;
        }
    },
    
    isAuthenticated() {
        return AppState.currentUser !== null;
    },
    
    hasRole(...roles) {
        if (!AppState.currentUser) return false;
        return roles.includes(AppState.currentUser.role);
    }
};

// API Service
const API = {
    async request(endpoint, options = {}) {
        const config = {
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };
        
        try {
            const response = await fetch(`${API_BASE}${endpoint}`, config);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Request failed');
            }
            
            return { success: true, data };
        } catch (error) {
            return { success: false, error: error.message };
        }
    },
    
    // Students
    async getStudents(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this.request(`/students?${queryString}`);
    },
    
    async getStudent(id) {
        return this.request(`/students/${id}`);
    },
    
    async createStudent(data) {
        return this.request('/students', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    
    async updateStudent(id, data) {
        return this.request(`/students/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },
    
    async getDashboard() {
        return this.request('/students/dashboard');
    },
    
    // Documents
    async uploadDocument(formData) {
        return fetch(`${API_BASE}/documents/upload`, {
            method: 'POST',
            credentials: 'include',
            body: formData
        }).then(r => r.json());
    },
    
    async getStudentDocuments(studentId) {
        return this.request(`/documents/student/${studentId}`);
    },
    
    // Notifications
    async getNotifications(unreadOnly = false) {
        const params = unreadOnly ? '?unread_only=true' : '';
        return this.request(`/notifications${params}`);
    },
    
    async markNotificationAsRead(id) {
        return this.request(`/notifications/${id}/read`, { method: 'POST' });
    }
};

// UI Utilities
const UI = {
    showAlert(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type}`;
        alertDiv.textContent = message;
        alertDiv.setAttribute('role', 'alert');
        
        const container = document.getElementById('alertContainer');
        if (container) {
            container.appendChild(alertDiv);
            
            setTimeout(() => {
                alertDiv.remove();
            }, 5000);
        }
    },
    
    showModal(title, content, actions = []) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-labelledby', 'modalTitle');
        modal.setAttribute('aria-modal', 'true');
        
        modal.innerHTML = `
            <div class="modal">
                <div class="modal-header">
                    <h2 id="modalTitle" class="modal-title">${title}</h2>
                </div>
                <div class="modal-body">
                    ${content}
                </div>
                <div class="modal-footer">
                    ${actions.map(action => `
                        <button class="btn ${action.class || 'btn-primary'}" onclick="${action.handler}">
                            ${action.label}
                        </button>
                    `).join('')}
                    <button class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">
                        Close
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Focus management
        modal.querySelector('button').focus();
        
        // Close on escape
        modal.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                modal.remove();
            }
        });
        
        // Close on backdrop click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    },
    
    formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleDateString('en-MY', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    },
    
    getStageBadge(stage) {
        const badges = {
            'inquiry': 'badge-info',
            'documents_collection': 'badge-warning',
            'application_submitted': 'badge-info',
            'offer_received': 'badge-success',
            'visa_processing': 'badge-warning',
            'visa_approved': 'badge-success',
            'arrival_scheduled': 'badge-info',
            'arrived': 'badge-success',
            'enrolled': 'badge-success',
            'rejected': 'badge-danger',
            'cancelled': 'badge-danger'
        };
        
        return badges[stage] || 'badge-info';
    }
};

// Page Rendering Functions
async function renderDashboard() {
    const result = await API.getDashboard();
    
    if (!result.success) {
        UI.showAlert('Failed to load dashboard', 'error');
        return;
    }
    
    const stats = result.data;
    const main = document.getElementById('mainContent');
    
    main.innerHTML = `
        <div class="page-header">
            <h1 class="page-title">Dashboard</h1>
        </div>
        
        <div id="alertContainer"></div>
        
        <div class="dashboard-grid">
            <div class="stat-card">
                <div class="stat-card-header">
                    <span class="stat-label">Total Students</span>
                    <span class="stat-icon" aria-hidden="true">👥</span>
                </div>
                <div class="stat-value">${stats.total_students}</div>
            </div>
            
            ${Object.entries(stats.by_stage).map(([stage, count]) => `
                <div class="stat-card">
                    <div class="stat-card-header">
                        <span class="stat-label">${stage.replace(/_/g, ' ')}</span>
                    </div>
                    <div class="stat-value">${count}</div>
                </div>
            `).join('')}
        </div>
        
        <div class="table-container">
            <div class="table-header">
                <h2 class="table-title">Recent Students</h2>
            </div>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Student Number</th>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Stage</th>
                        <th>Created</th>
                    </tr>
                </thead>
                <tbody>
                    ${stats.recent_students.map(student => `
                        <tr>
                            <td>${student.student_number}</td>
                            <td>${student.full_name}</td>
                            <td>${student.email}</td>
                            <td>
                                <span class="badge ${UI.getStageBadge(student.current_stage)}">
                                    ${student.current_stage.replace(/_/g, ' ')}
                                </span>
                            </td>
                            <td>${UI.formatDate(student.created_at)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

async function renderStudents() {
    const result = await API.getStudents();
    
    if (!result.success) {
        UI.showAlert('Failed to load students', 'error');
        return;
    }
    
    const students = result.data.students;
    const main = document.getElementById('mainContent');
    
    main.innerHTML = `
        <div class="page-header">
            <h1 class="page-title">Students</h1>
            ${AuthService.hasRole('super_admin', 'admin', 'counsellor') ? `
                <button class="btn btn-primary" onclick="showCreateStudentModal()">
                    + Add Student
                </button>
            ` : ''}
        </div>
        
        <div id="alertContainer"></div>
        
        <div class="table-container">
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Student Number</th>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Nationality</th>
                        <th>Stage</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${students.map(student => `
                        <tr>
                            <td>${student.student_number}</td>
                            <td>${student.full_name}</td>
                            <td>${student.email}</td>
                            <td>${student.nationality || 'N/A'}</td>
                            <td>
                                <span class="badge ${UI.getStageBadge(student.current_stage)}">
                                    ${student.current_stage.replace(/_/g, ' ')}
                                </span>
                            </td>
                            <td>
                                <button class="btn btn-sm btn-primary" onclick="viewStudent(${student.id})">
                                    View
                                </button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

async function renderNotifications() {
    const result = await API.getNotifications();
    
    if (!result.success) {
        UI.showAlert('Failed to load notifications', 'error');
        return;
    }
    
    const notifications = result.data.notifications;
    const main = document.getElementById('mainContent');
    
    main.innerHTML = `
        <div class="page-header">
            <h1 class="page-title">Notifications</h1>
            <span class="badge badge-info">${result.data.unread_count} Unread</span>
        </div>
        
        <div id="alertContainer"></div>
        
        <div class="table-container">
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Title</th>
                        <th>Message</th>
                        <th>Priority</th>
                        <th>Date</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    ${notifications.map(notif => `
                        <tr style="${notif.is_read ? '' : 'font-weight: bold;'}">
                            <td>${notif.title}</td>
                            <td>${notif.message}</td>
                            <td>
                                <span class="badge badge-${notif.priority === 'urgent' ? 'danger' : 'info'}">
                                    ${notif.priority}
                                </span>
                            </td>
                            <td>${UI.formatDate(notif.created_at)}</td>
                            <td>
                                ${!notif.is_read ? `
                                    <button class="btn btn-sm btn-primary" 
                                        onclick="markAsRead(${notif.id})">
                                        Mark Read
                                    </button>
                                ` : '<span class="badge badge-success">Read</span>'}
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

// Navigation
function showPage(pageName) {
    AppState.currentPage = pageName;
    
    // Update active nav link
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
        if (link.dataset.page === pageName) {
            link.classList.add('active');
        }
    });
    
    // Render page
    switch (pageName) {
        case 'dashboard':
            renderDashboard();
            break;
        case 'students':
            renderStudents();
            break;
        case 'notifications':
            renderNotifications();
            break;
        case 'login':
            window.location.href = '/login.html';
            break;
    }
}

// Event Handlers
async function handleLogin(event) {
    event.preventDefault();
    
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    
    const result = await AuthService.login(email, password);
    
    if (result.success) {
        window.location.href = '/index.html';
    } else {
        UI.showAlert(result.error, 'error');
    }
}

async function markAsRead(notificationId) {
    const result = await API.markNotificationAsRead(notificationId);
    
    if (result.success) {
        renderNotifications();
    }
}

// Initialize Application
async function initApp() {
    // Check authentication
    const user = await AuthService.getCurrentUser();
    
    if (!user) {
        window.location.href = '/login.html';
        return;
    }
    
    // Set up navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            showPage(link.dataset.page);
        });
    });
    
    // Set up logout
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => AuthService.logout());
    }
    
    // Load initial page
    showPage('dashboard');
}

// Wait for DOM to be ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}
