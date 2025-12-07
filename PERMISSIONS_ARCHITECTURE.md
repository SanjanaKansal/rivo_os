# Permission System Architecture

## Overview
Clean, extensible permission system with no hardcoding. Everything is dynamic and permission-driven.

## Core Principles
1. **Single Source of Truth**: All permissions defined in `UserSerializer.get_permissions()`
2. **Backend Security**: Django decorators + DRF permission classes
3. **Frontend UX**: Hide/show UI elements based on permissions
4. **No Hardcoding**: No role names in code, only permission checks

---

## Backend Layer (Security)

### 1. Permission Definitions
**File**: `account/serializers.py`
```python
def get_permissions(self, obj):
    return {
        'can_edit_leads': obj.has_perm('leads.change_rawlead'),
        'can_view_leads': obj.has_perm('leads.view_rawlead'),
        'can_view_sources': obj.has_perm('leads.view_source'),
        'can_change_sources': obj.has_perm('leads.change_source'),
    }
```
✅ **To extend**: Add new permission here and it's available everywhere

### 2. View Protection (Page Access)
**File**: `dashboard/views.py`
```python
@login_required(login_url='/login/')
@permission_required('leads.view_source', login_url='/', raise_exception=False)
def sources_page(request):
    return render(request, 'dashboard/sources.html')
```
✅ **To extend**: Add decorator for new pages

### 3. API Protection (Data Access)
**File**: `leads/views.py`
```python
class SourceViewSet(viewsets.ModelViewSet):
    permission_classes = [DjangoModelPermissions]  # Automatic

    @action(detail=True, methods=['patch'])
    def bulk_assign(self, request, pk=None):
        if not request.user.has_perm('leads.change_source'):  # Manual check
            raise PermissionDenied(...)
```
✅ **To extend**: Add permission check to custom actions

### 4. Data Filtering (Row-Level Security)
**File**: `leads/views.py`
```python
def get_queryset(self):
    if user.is_staff or user.is_superuser:
        return Source.objects.all()
    return Source.objects.filter(Q(owner=user) | Q(leads__assigned_to=user))
```
✅ **To extend**: Modify queryset logic for new models

---

## Frontend Layer (UX)

### 1. Navigation Links
**Pattern**: Hidden by default, shown if permission exists
```html
<a id="sources-link" href="/sources/" style="display: none;">Sources</a>
```
```javascript
permissionManager.loadPermissions().then(data => {
    if (data.permissions.can_view_sources) {
        document.getElementById('sources-link').style.display = '';
    }
});
```
✅ **To extend**: Add new link with same pattern

### 2. Action Buttons
**Pattern**: Conditional rendering based on permission
```javascript
${userPermissions.can_edit_leads ? `
    <button>Valid</button>
    <button>Spam</button>
` : '-'}
```
✅ **To extend**: Check permission before rendering button

---

## How to Add New Permission

### Example: Add "can_delete_sources"

1. **Backend** - Add to UserSerializer:
```python
def get_permissions(self, obj):
    return {
        # ... existing permissions
        'can_delete_sources': obj.has_perm('leads.delete_source'),
    }
```

2. **Frontend** - Check permission before showing delete button:
```javascript
${userPermissions.can_delete_sources ? `
    <button onclick="deleteSource()">Delete</button>
` : ''}
```

3. **API** - Protect delete action:
```python
@action(detail=True, methods=['delete'])
def delete_source(self, request, pk=None):
    if not request.user.has_perm('leads.delete_source'):
        raise PermissionDenied(...)
```

**That's it!** No role names, no hardcoding, fully dynamic.

---

## Permission Flow

```
┌─────────────────┐
│  Role Model     │  Has permissions assigned
└────────┬────────┘
         │
         v
┌─────────────────┐
│  Custom Backend │  Checks role.permissions
└────────┬────────┘
         │
         v
┌─────────────────┐
│  has_perm()     │  Returns True/False
└────────┬────────┘
         │
         ├──────────────────────┬──────────────────────┐
         v                      v                      v
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  View Decorator │    │ API ViewSet     │    │ UserSerializer  │
│  @permission_   │    │ permission_     │    │ get_permissions │
│  required       │    │ classes         │    │                 │
└─────────────────┘    └─────────────────┘    └────────┬────────┘
         │                      │                       │
         v                      v                       v
    Page Access           Data Access              Frontend UX
```

---

## Best Practices Followed

✅ **Django Decorators**: Use `@login_required` and `@permission_required`
✅ **DRF Permissions**: Use `DjangoModelPermissions` for ViewSets
✅ **Single Source**: All permissions in `UserSerializer`
✅ **Consistent Pattern**: Same check everywhere: `userPermissions.can_*`
✅ **No Hardcoding**: No role names in code
✅ **Row-Level Security**: Filter querysets by user
✅ **Defense in Depth**: Backend blocks even if frontend bypassed

---

## Files to Check

- **Permissions Source**: `account/serializers.py` → `get_permissions()`
- **View Protection**: `dashboard/views.py` → Decorators
- **API Protection**: `leads/views.py` → permission_classes + manual checks
- **Frontend Logic**: All templates → Check `userPermissions.can_*`
- **Auth Backend**: `account/backends.py` → Integrates Role with has_perm()