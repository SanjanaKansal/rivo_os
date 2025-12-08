/**
 * Permission management for Rivo OS
 */
function getCookie(name) {
    if (!document.cookie) return null;
    const match = document.cookie.split(';').find(c => c.trim().startsWith(name + '='));
    return match ? decodeURIComponent(match.split('=')[1]) : null;
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
            const res = await fetch('/account/api/user/', {
                headers: { 'Authorization': `Token ${this.token}` }
            });
            if (!res.ok) throw new Error('Unauthorized');
            const data = await res.json();
            this.permissions = data.permissions || {};
            return data;
        } catch (e) {
            localStorage.removeItem('auth_token');
            window.location.href = '/login/';
        }
    }

    hasPermission(perm) {
        return this.permissions[perm] === true;
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

const permissionManager = new PermissionManager();