from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model.
    Returns basic user information and permissions for API responses.
    """
    permissions = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'full_name', 'permissions')

    def get_full_name(self, obj):
        """Get user's readable display name."""
        if obj.get_full_name():
            return obj.get_full_name()
        if obj.username:
            return obj.username.replace('.', ' ').replace('_', ' ').title()
        return obj.email or str(obj.id)

    def get_permissions(self, obj):
        """Get all user permissions dynamically from Django's permission system."""
        perms = {}
        # Get all permissions from user (includes role/group permissions)
        all_perms = obj.get_all_permissions()
        for perm in all_perms:
            # Convert 'app.codename' to 'app_codename' for JS compatibility
            key = perm.replace('.', '_')
            perms[key] = True
        return perms


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user authentication.
    Validates username and password, returns user object on success.
    """
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        """Authenticate user with provided credentials."""
        username = data.get('username')
        password = data.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                if not user.is_active:
                    raise serializers.ValidationError('User account is disabled.')
                data['user'] = user
            else:
                raise serializers.ValidationError('Unable to log in with provided credentials.')
        else:
            raise serializers.ValidationError('Must include "username" and "password".')

        return data