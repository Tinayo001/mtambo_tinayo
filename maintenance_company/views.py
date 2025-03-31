from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404

from Account_User.models import User
from .permissions import IsSuperUser, IsMaintenanceCompanyAdmin, IsOwnerOrSuperuser
from .models import MaintenanceCompanyProfile
from .serializers import MaintenanceCompanyProfileSerializer, MaintenanceCompanyDetailSerializer
from technician.models import TechnicianProfile
from technician.serializers import TechnicianProfileSerializer, TechnicianCreateSerializer
import uuid



class MaintenanceCompanyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for MaintenanceCompanyProfile model.
    Provides CRUD operations with proper permission handling.
    """
    queryset = MaintenanceCompanyProfile.objects.all()
    serializer_class = MaintenanceCompanyProfileSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['company_name', 'registration_number', 'user__email', 'user__first_name', 'user__last_name']
    ordering_fields = ['company_name', 'user__created_at']
    ordering = ['-user__created_at']
    # Add this if your MaintenanceCompanyProfile uses UUIDs
    lookup_field = 'id'  # or 'uuid' if that's what your model uses
    
    def get_serializer_class(self):
        """
        Return appropriate serializer class based on action.
        """
        if self.action == 'retrieve':
            return MaintenanceCompanyDetailSerializer
        return MaintenanceCompanyProfileSerializer
    
    def get_queryset(self):
        """
        Filter queryset based on user permissions:
        - Superusers can see all maintenance companies
        - Maintenance admins can only see their own company
        """
        queryset = super().get_queryset()
        
        if self.request.user.is_superuser:
            return queryset
            
        # Regular users can only see their own maintenance company profile
        return queryset.filter(admin_user=self.request.user)
    
    def get_permissions(self):
        """
        Set permissions based on the action.
        """
        if self.action == 'create':
            # Only superusers can create maintenance companies
            permission_classes = [IsAuthenticated, IsSuperUser]
        elif self.action in ['update', 'partial_update', 'destroy']:
            # Only the owner or superuser can modify/delete
            permission_classes = [IsAuthenticated, IsOwnerOrSuperuser]
        elif self.action == 'list':
            # Superusers can see all, maintenance admins see their own
            permission_classes = [IsAuthenticated, IsSuperUser | IsMaintenanceCompanyAdmin]
        elif self.action == 'retrieve':
            # Superusers can see any, others only their own
            permission_classes = [IsAuthenticated, IsOwnerOrSuperuser]
        elif self.action in ['technicians', 'add_technician', 'remove_technician', 'create_technician']:
            # Only company admins can manage their technicians
            permission_classes = [IsAuthenticated, IsMaintenanceCompanyAdmin]
        else:
            permission_classes = [IsAuthenticated]
            
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """
        When creating a new maintenance company, set the admin_user
        """
        serializer.save(admin_user=self.request.user)
    
    @action(detail=True, methods=['get'])
    def technicians(self, request, id=None):
        """
        List all technicians belonging to this maintenance company
        """
        company = self.get_object()
        
        # Extra security check - only admins of this company or superusers can access
        if not request.user.is_superuser and company.admin_user != request.user:
            return Response(
                {"detail": "You are not authorized to view technicians for this company."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        technicians = TechnicianProfile.objects.filter(maintenance_company=company)
        serializer = TechnicianProfileSerializer(technicians, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_technician(self, request, id=None):
        """
        Add an existing technician to this maintenance company
        """
        company = self.get_object()
        
        # Extra security check - only admins of this company or superusers can add technicians
        if not request.user.is_superuser and company.admin_user != request.user:
            return Response(
                {"detail": "You are not authorized to add technicians to this company."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Get the technician by user ID or email
            user_id = request.data.get('user_id')
            email = request.data.get('email')
            
            if user_id:
                user = get_object_or_404(User, id=user_id, account_type='technician')
            elif email:
                user = get_object_or_404(User, email=email, account_type='technician')
            else:
                return Response(
                    {"error": "Either user_id or email must be provided"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Get or create technician profile
            technician, created = TechnicianProfile.objects.get_or_create(user=user)
            
            # Assign to this maintenance company
            technician.maintenance_company = company
            technician.save()
            
            serializer = TechnicianProfileSerializer(technician)
            return Response(serializer.data)
            
        except User.DoesNotExist:
            return Response(
                {"error": "Technician not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def remove_technician(self, request, id=None):
        """
        Remove a technician from this maintenance company
        """
        company = self.get_object()
        
        # Extra security check - only admins of this company or superusers can remove technicians
        if not request.user.is_superuser and company.admin_user != request.user:
            return Response(
                {"detail": "You are not authorized to remove technicians from this company."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Get the technician by user ID or email
            user_id = request.data.get('user_id')
            email = request.data.get('email')
            
            if user_id:
                technician = get_object_or_404(
                    TechnicianProfile, 
                    user__id=user_id, 
                    maintenance_company=company
                )
            elif email:
                technician = get_object_or_404(
                    TechnicianProfile, 
                    user__email=email, 
                    maintenance_company=company
                )
            else:
                return Response(
                    {"error": "Either user_id or email must be provided"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Remove from this maintenance company
            technician.maintenance_company = None
            technician.save()
            
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except TechnicianProfile.DoesNotExist:
            return Response(
                {"error": "Technician not found in this company"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def create_technician(self, request, id=None):
        """
        Create a new technician and associate them with this maintenance company
        """
        company = self.get_object()
        
        # Extra security check - only admins of this company or superusers can create technicians
        if not request.user.is_superuser and company.admin_user != request.user:
            return Response(
                {"detail": "You are not authorized to create technicians for this company."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = TechnicianCreateSerializer(
            data=request.data,
            context={'maintenance_company': company}
        )
        
        if serializer.is_valid():
            result = serializer.save()
            return Response(
                TechnicianProfileSerializer(result['technician_profile']).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='by-email')
    def get_company_by_email(self, request):
        """
        Retrieve a maintenance company by either the company email or the admin email.
        """
        email = request.query_params.get('email')

        if not email:
            return Response(
                {"error": "Email parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Try fetching the company using admin's email
        user = User.objects.filter(email=email, account_type='maintenance').first()
        if user:
            company = MaintenanceCompanyProfile.objects.filter(admin_user=user).first()
        else:
            # Try fetching using the company email
            company = MaintenanceCompanyProfile.objects.filter(company_email=email).first()

        if not company:
            return Response(
                {"error": "No maintenance company found with this email"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = MaintenanceCompanyDetailSerializer(company)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'], permission_classes=[IsSuperUser | IsMaintenanceCompanyAdmin])
    def technicians(self, request, id=None): 
        try:
            company_uuid = uuid.UUID(id)
            company = get_object_or_404(MaintenanceCompanyProfile, id=company_uuid)
        except ValueError:
            return Response({"detail": "Invalid UUID format."}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Ensure the user is authorized
        if request.user.account_type != "superuser" and request.user.maintenance_profile != company:
            return Response({"detail": "You are not authorized."}, status=status.HTTP_403_FORBIDDEN)

        # ✅ Get all technicians under the company
        technicians = TechnicianProfile.objects.filter(maintenance_company=company)
        serializer = TechnicianProfileSerializer(technicians, many=True)
        return Response({"technicians": serializer.data}, status=status.HTTP_200_OK)
    
    