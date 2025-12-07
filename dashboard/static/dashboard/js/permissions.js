/**
 * Centralized permission management and utilities for Rivo OS
 */

// Utility: Get CSRF cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

class PermissionManager {
    constructor() {
        this.permissions = {};
        this.token = localStorage.getItem('auth_token');
    }

    async loadPermissions() {
        if (!this.token) {
            window.location.href = '/login/';
            return;
        }

        try {
            const response = await fetch('/account/api/user/', {
                headers: { 'Authorization': `Token ${this.token}` }
            });

            if (!response.ok) throw new Error('Unauthorized');

            const data = await response.json();
            this.permissions = data.permissions || {};
            return data;
        } catch (error) {
            localStorage.removeItem('auth_token');
            window.location.href = '/login/';
        }
    }

    hasPermission(permission) {
        return this.permissions[permission] === true;
    }

    async logout() {
        try {
            await fetch('/account/api/logout/', {
                method: 'POST',
                headers: {
                    'Authorization': `Token ${this.token}`,
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });
        } catch (e) {}
        localStorage.removeItem('auth_token');
        window.location.href = '/login/';
    }
}

// Create global instance
const permissionManager = new PermissionManager();