from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.tokens import RefreshToken


from .models import TechnicianProfile, DeveloperProfile, MaintenanceProfile
from .serializers import (
    UserCreateSerializer, 
    UserDetailSerializer, 
    UserUpdateSerializer,
    UserPasswordChangeSerializer
)
from .factory import UserProfileFactory


User = get_user_model()

class UserPermission(permissions.BasePermission):
    """
    Custom permission to:
    - Allow anyone to create an account
    - Allow owners to update/edit/destroy/read their own profile
    - Allow admins to view all profiles
    """
    def has_permission(self, request, view):
        if view.action == 'create':
            return True  # Anyone can create an account

        if not request.user or not request.user.is_authenticated:
            return False  # Require authentication for all other actions

        if view.action in ['list', 'retrieve']:
            return request.user.is_staff or request.user.is_superuser

        return True

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or request.user.is_superuser:
            return True

        return obj == request.user  # Users can only access their own profile

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
        Customize queryset based on user type
        Admins see all users, others see only themselves
        """
        user = self.request.user
        if not user.is_authenticated:
            return User.objects.none()

        if user.is_staff or user.is_superuser:
            return User.objects.all()
        
        return User.objects.filter(pk=user.pk)

    def get_serializer_class(self):
        """
        Dynamic serializer selection based on action
        """
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserDetailSerializer

    def perform_create(self, serializer):
        """
        Custom user creation and profile initialization
        """
        user = serializer.save()
        UserProfileFactory.create_profile(user)

    def create(self, request, *args, **kwargs):
        """
        Custom user creation with proper response handling
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = serializer.save()
            UserProfileFactory.create_profile(user)
            response_data = UserDetailSerializer(user).data
            return Response(response_data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False, 
        methods=['POST'],
        permission_classes=[IsAuthenticated]
    )
    def change_password(self, request):
        """
        Custom action to change user password
        Requires authentication
        """
        serializer = UserPasswordChangeSerializer(
            data=request.data, 
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True, 
        methods=['GET'], 
        permission_classes=[UserPermission]
    )
    def profile(self, request, pk=None):
        """
        Retrieve detailed user profile based on account type
        """
        user = get_object_or_404(User, pk=pk)

        profile = None
        if user.account_type == "technician":
            profile = TechnicianProfile.objects.filter(user=user).first()
        elif user.account_type == "maintenance":
            profile = MaintenanceProfile.objects.filter(user=user).first()
        elif user.account_type == "developer":
            profile = DeveloperProfile.objects.filter(user=user).first()

        if profile:
            return Response({"user": UserDetailSerializer(user).data, "profile": profile.additional_data})
        else:
            return Response({"user": UserDetailSerializer(user).data, "profile": None})

class UserAuthViewSet(viewsets.ViewSet):
    """
    Comprehensive Authentication ViewSet
    Supports user login, token refresh, and logout functionality
    """
    permission_classes = [AllowAny]

    @action(detail=False, methods=['POST'], url_path='login')
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

    @action(detail=False, methods=['POST'], url_path='refresh')
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

    @action(detail=False, methods=['POST'], url_path='logout')
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