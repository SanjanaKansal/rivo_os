from django.db import models
from django.contrib.auth import login, logout
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import LoginSerializer, UserSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    User login endpoint.
    Sets session cookie and returns authentication token.
    """
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        # Set session cookie for Django's @login_required
        login(request, user)
        # Also return token for API calls
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    User logout endpoint.
    Clears session and deletes authentication token.
    """
    # Delete token
    if hasattr(request.user, 'auth_token'):
        request.user.auth_token.delete()
    # Clear session
    logout(request)
    return Response({'message': 'Successfully logged out.'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user_view(request):
    """
    Get current user information.
    Returns authenticated user's details.
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def lead_owners_view(request):
    """
    Get list of users who can be assigned leads.
    Returns users who have permission to work with leads (not based on role name).
    """
    from .models import User
    from django.contrib.auth.models import Permission

    # Get permission object for viewing leads
    view_lead_perm = Permission.objects.get(codename='view_rawlead', content_type__app_label='leads')

    # Get users who have this permission (through role or directly)
    users = User.objects.filter(
        is_active=True
    ).filter(
        models.Q(role__permissions=view_lead_perm) |  # Via role
        models.Q(user_permissions=view_lead_perm) |   # Direct permission
        models.Q(is_staff=True)                        # Staff always included
    ).distinct().order_by('username')

    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)


