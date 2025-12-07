from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model.
    Returns basic user information and permissions for API responses.
    """
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'permissions')

    def get_permissions(self, obj):
        """Get user's permissions."""
        return {
            'can_edit_leads': obj.has_perm('leads.change_rawlead'),
            'can_view_leads': obj.has_perm('leads.view_rawlead'),
            'can_view_sources': obj.has_perm('leads.view_source'),
            'can_change_sources': obj.has_perm('leads.change_source'),
        }


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