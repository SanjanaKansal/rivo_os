from django.contrib.auth.backends import ModelBackend


class RolePermissionBackend(ModelBackend):
    """
    Custom authentication backend that checks permissions from user roles.
    Integrates role-based permissions with Django's has_perm() system.
    """

    def _get_role_permissions(self, user_obj):
        """Get all permissions from the user's role."""
        if not hasattr(user_obj, 'role') or user_obj.role is None:
            return set()

        return set(
            f"{perm.content_type.app_label}.{perm.codename}"
            for perm in user_obj.role.permissions.select_related('content_type').all()
        )

    def get_all_permissions(self, user_obj, obj=None):
        """
        Return all permissions for the user, including role permissions.
        """
        if not user_obj.is_active or user_obj.is_anonymous:
            return set()

        if not hasattr(user_obj, '_role_perm_cache'):
            # Get permissions from groups and user_permissions (default Django behavior)
            user_obj._role_perm_cache = super().get_all_permissions(user_obj, obj)
            # Add permissions from role
            user_obj._role_perm_cache.update(self._get_role_permissions(user_obj))

        return user_obj._role_perm_cache

    def has_perm(self, user_obj, perm, obj=None):
        """
        Check if user has the specified permission, including role permissions.
        """
        if not user_obj.is_active:
            return False

        return perm in self.get_all_permissions(user_obj, obj)