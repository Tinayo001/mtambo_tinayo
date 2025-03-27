

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from maintenance_company.models import MaintenanceCompanyProfile
from developer.models import DeveloperProfile
from technician.models import TechnicianProfile

from .serializers import (
    UserCreateSerializer, 
    UserDetailSerializer, 
    UserUpdateSerializer,
    UserPasswordChangeSerializer
)
from .factory import UserProfileFactory
from .permissions import UserPermission
import logging

logger = logging.getLogger(__name__)

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    """
    Comprehensive User Profile Management ViewSet
    Supports full CRUD operations with fine-grained permissions
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [UserPermission]
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer

    def get_queryset(self):
        """
        Filter users based on authentication and role
        - Superusers see all users
        - Regular users see only themselves
        """
        user = self.request.user

        # Superusers can see all users, regular users only see themselves
        if user.is_superuser:
            return self.queryset
        
        return self.queryset.filter(pk=user.pk)

    def get_serializer_class(self):
        """Return different serializers based on action"""
        serializer_map = {
            "create": UserCreateSerializer,
            "update": UserUpdateSerializer,
            "partial_update": UserUpdateSerializer,
        }
        return serializer_map.get(self.action, UserDetailSerializer)

    def perform_create(self, serializer):
        """Handle user creation and associated profile setup"""
        # Extract profile data if it exists
        profile_data = {}
        account_type = serializer.validated_data.get('account_type')
    
        if account_type == 'technician':
            profile_data = serializer.validated_data.pop('technician_profile', {})
        elif account_type == 'maintenance':
            profile_data = serializer.validated_data.pop('maintenance_profile', {})
        elif account_type == 'developer':
            profile_data = serializer.validated_data.pop('developer_profile', {})
    
        # Create the user with the serializer
        user = serializer.save()
    
        # Create profile with the extracted data
        if profile_data:
            UserProfileFactory.create_profile(user, profile_data)

    @action(detail=False, methods=["POST"], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """Allow authenticated users to change passwords"""
        serializer = UserPasswordChangeSerializer(data=request.data, context={"request": request})
        
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["GET"])
    def profile(self, request, pk=None):
        """Retrieve detailed user profile"""
        user = get_object_or_404(User, pk=pk)
        
        # Ensure user can only access their own profile or is a superuser
        if user != request.user and not request.user.is_superuser:
            return Response(
                {"detail": "You do not have permission to view this profile"},
                status=status.HTTP_403_FORBIDDEN
            )

        profile_model = self.get_profile_model(user.account_type)

        profile = profile_model.objects.filter(user=user).first() if profile_model else None
        profile_data = profile.additional_data if profile else None

        return Response({"user": UserDetailSerializer(user).data, "profile": profile_data})

    def get_profile_model(self, account_type):
        """Return the appropriate profile model based on account type"""
        profile_map = {
            "technician": TechnicianProfile,
            "maintenance": MaintenanceCompanyProfile,
            "developer": DeveloperProfile,
        }
        return profile_map.get(account_type)
    
class UserAuthViewSet(viewsets.ViewSet):
    """
    Comprehensive Authentication ViewSet
    Supports user login, token refresh, and logout functionality
    """
    permission_classes = [AllowAny]

    @action(detail=False, methods=['POST'], url_path='login', permission_classes=[AllowAny])
    def user_login(self, request):
        """
        Handle user login with email and password
        Returns JWT tokens and user details
        """
        email = request.data.get('email')
        password = request.data.get('password')

        # Validate input
        if not email or not password:
            return Response({
                'error': 'Both email and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Authenticate user
        user = authenticate(request, username=email, password=password)

        if user is not None:
            # Generate tokens
            try:
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                   'user': {
                        'id': user.id,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'account_type': user.account_type
                    }
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({
                    'error': 'Token generation failed',
                    'details': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            # Failed authentication
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=False, methods=['POST'], url_path='refresh', permission_classes=[IsAuthenticated])
    def token_refresh(self, request):
        """
        Refresh access token using a valid refresh token
        """
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response({
                'error': 'Refresh token is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Attempt to refresh the token
            refresh = RefreshToken(refresh_token)
            return Response({
                'access': str(refresh.access_token)
            }, status=status.HTTP_200_OK)
        except (TokenError, InvalidToken):
            return Response({
                'error': 'Invalid or expired refresh token'
            }, status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=False, methods=['POST'], url_path='logout', permission_classes=[IsAuthenticated])
    def user_logout(self, request):
        """
        Logout user by blacklisting refresh token
        """
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response({
                'error': 'Refresh token is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Blacklist the refresh token
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({
                'message': 'Successfully logged out'
            }, status=status.HTTP_200_OK)
        except (TokenError, InvalidToken):
            return Response({
                'error': 'Invalid refresh token'
            }, status=status.HTTP_401_UNAUTHORIZED)