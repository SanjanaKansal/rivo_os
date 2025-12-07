# Scalable Navigation System

## Overview
Modern sidebar navigation that grows with your app. Clean, professional, and permission-driven.

---

## Features

✅ **Scalable**: Easy to add unlimited menu items
✅ **Permission-Driven**: Auto-hides based on user permissions
✅ **Responsive**: Sidebar on desktop, collapsible on mobile
✅ **Clean Design**: Modern, professional look
✅ **Active States**: Highlights current page
✅ **Icons**: Professional icons for each menu item

---

## How to Use

### 1. Include Navigation in Your Template

```django
{% include 'dashboard/navigation.html' %}

<div class="lg:pl-64 pt-16">
    <!-- Your page content here -->
</div>
```

### 2. Initialize on Page Load

```javascript
// Load permissions and setup navigation
permissionManager.loadPermissions().then(data => {
    if (data) {
        // Show navigation based on permissions
        navigationManager.renderNavigation(data.permissions);

        // Set active page
        navigationManager.setActivePage('dashboard'); // or 'sources', 'leads'

        // Set page title
        navigationManager.setPageTitle('Dashboard');

        // Set user info in sidebar
        navigationManager.setUserInfo(data);
    }
});

// Logout handler
document.getElementById('logout-btn').addEventListener('click', async () => {
    // ... logout logic
});
```

---

## Adding New Menu Items

### Simple 3-Step Process:

#### 1. Add Permission (if needed)

**File**: `account/serializers.py`
```python
def get_permissions(self, obj):
    return {
        # ... existing
        'can_view_reports': obj.has_perm('app.view_report'),
    }
```

#### 2. Add Menu Item to Navigation

**File**: `dashboard/templates/dashboard/navigation.html`
```html
<a href="/reports/" class="nav-item"
   data-page="reports"
   data-permission="can_view_reports"
   style="display: none;">
    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
    </svg>
    <span>Reports</span>
</a>
```

#### 3. That's It!

The navigation automatically:
- ✅ Shows/hides based on permission
- ✅ Highlights when active
- ✅ Works on mobile
- ✅ No additional configuration needed

---

## Menu Item Attributes

### Required:
- `class="nav-item"` - Styling
- `data-page="page-name"` - For active state
- `href="/path/"` - Navigation link

### Optional (for permission-controlled items):
- `data-permission="can_view_*"` - Permission key
- `style="display: none;"` - Hidden by default

### Items Without Permissions:
Don't include `data-permission` or `style="display: none;"` - they'll always be visible.

```html
<!-- Always visible (no permission check) -->
<a href="/help/" class="nav-item" data-page="help">
    <svg>...</svg>
    <span>Help</span>
</a>
```

---

## Example: Complete Page Setup

```django
{% extends 'dashboard/base.html' %}
{% load static %}

{% block title %}Reports - Rivo{% endblock %}

{% block content %}
{% include 'dashboard/navigation.html' %}

<div class="lg:pl-64 pt-16">
    <main class="max-w-7xl mx-auto px-6 lg:px-8 py-8">
        <h1>Reports</h1>
        <!-- Your content here -->
    </main>
</div>

<script src="{% static 'dashboard/js/permissions.js' %}"></script>
<script>
    permissionManager.loadPermissions().then(data => {
        if (data) {
            navigationManager.renderNavigation(data.permissions);
            navigationManager.setActivePage('reports');
            navigationManager.setPageTitle('Reports');
            navigationManager.setUserInfo(data);
        }
    });

    document.getElementById('logout-btn').addEventListener('click', async () => {
        await fetch('/account/api/logout/', {
            method: 'POST',
            headers: {
                'Authorization': `Token ${permissionManager.token}`,
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        localStorage.removeItem('auth_token');
        window.location.href = '/login/';
    });

    function getCookie(name) {
        // ... same as before
    }
</script>
{% endblock %}
```

---

## Icons

Get more icons from [Heroicons](https://heroicons.com/). Copy the SVG code and paste it in the menu item.

Common icons already included:
- 🏠 Dashboard (Home)
- 📦 Sources (Archive)
- 👥 Leads (Users)

---

## Customization

### Change Sidebar Width:
```html
<!-- In navigation.html -->
<aside class="w-64">  <!-- Change from w-64 to w-48, w-72, etc. -->
```

### Add Sections/Dividers:
```html
<div class="pt-4 mt-4 border-t border-gray-200 dark:border-gray-800"></div>
<p class="px-4 text-xs font-semibold text-gray-400 uppercase">Admin</p>
```

### Add Badges/Counts:
```html
<a href="/notifications/" class="nav-item">
    <svg>...</svg>
    <span>Notifications</span>
    <span class="ml-auto bg-red-500 text-white text-xs px-2 py-0.5 rounded-full">5</span>
</a>
```

---

## Mobile Behavior

- **Desktop (≥1024px)**: Sidebar always visible
- **Mobile (<1024px)**:
  - Sidebar hidden by default
  - Click hamburger menu to open
  - Click overlay or X to close
  - Automatically hides navigation items

---

## Next Steps

1. ✅ Navigation component created
2. ✅ Permission system integrated
3. ⏭️ Update existing pages to use new navigation
4. ⏭️ Add new pages as needed

To migrate existing pages, replace the old navigation with `{% include 'dashboard/navigation.html' %}` and add the wrapper `<div class="lg:pl-64 pt-16">`.