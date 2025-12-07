from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Role


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Admin interface for Role model."""
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name',)
    filter_horizontal = ('permissions',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model."""
    list_display = ('username', 'email', 'phone', 'role', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'role')
    search_fields = ('username', 'email', 'phone')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('phone', 'role')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
