from rest_framework import viewsets, status, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from maintenance_company.permissions import IsSuperUser, IsMaintenanceCompanyAdmin, IsAccountOwnerOrAdmin, IsOwnerOrSuperuser
from .models import TechnicianProfile
from .serializers import TechnicianProfileSerializer, TechnicianCreateSerializer


class TechnicianViewSet(viewsets.ModelViewSet):
    """
    ViewSet for TechnicianProfile model.
    Provides CRUD operations with proper permission handling.
    """
    queryset = TechnicianProfile.objects.all()
    serializer_class = TechnicianProfileSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'specialization']
    filterset_fields = ['maintenance_company']
    ordering_fields = ['user__first_name', 'user__last_name', 'user__created_at']
    ordering = ['user__first_name']
    
    def get_queryset(self):
        """
        Filter queryset based on user permissions:
        - Superusers can see all technicians
        - Maintenance admins can only see technicians in their company
        - Technicians can only see themselves
        """
        queryset = super().get_queryset()
        
        if self.request.user.is_superuser:
            return queryset
            
        # For maintenance admins, show only technicians in their company
        if self.request.user.account_type == 'maintenance':
            from maintenance_company.models import MaintenanceCompanyProfile
            try:
                company = MaintenanceCompanyProfile.objects.get(admin_user=self.request.user)
                return queryset.filter(maintenance_company=company)
            except MaintenanceCompanyProfile.DoesNotExist:
                return TechnicianProfile.objects.none()
        
        # For technicians, show only their own profile
        if self.request.user.account_type == 'technician':
            return queryset.filter(user=self.request.user)
                
        return TechnicianProfile.objects.none()
    
    def get_permissions(self):
        """
        Set permissions based on the action:
        - list/retrieve: authenticated users with appropriate access rights
        - create: superuser or maintenance admin
        - update/delete: owner, maintenance admin, or superuser
        """
        if self.action == 'create':
            permission_classes = [IsAuthenticated, IsSuperUser | IsMaintenanceCompanyAdmin]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsAccountOwnerOrAdmin]
        elif self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated, IsAccountOwnerOrAdmin]
        else:
            permission_classes = [IsAuthenticated]
            
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        """
        When creating a technician from this viewset directly,
        associate with the maintenance company if applicable.
        """
        from maintenance_company.models import MaintenanceCompanyProfile
        
        # If created by a maintenance company admin
        if self.request.user.account_type == 'maintenance':
            try:
                company = MaintenanceCompanyProfile.objects.get(admin_user=self.request.user)
                serializer.save(maintenance_company=company)
                return
            except MaintenanceCompanyProfile.DoesNotExist:
                pass
                
        serializer.save()
    
    @action(detail=False, methods=['post'])
    def create_with_user(self, request):
        """
        Create a new technician with user account.
        Used by maintenance company admins to add technicians.
        """
        from maintenance_company.models import MaintenanceCompanyProfile
        
        # Get the maintenance company if applicable
        maintenance_company = None
        if request.user.account_type == 'maintenance':
            try:
                maintenance_company = MaintenanceCompanyProfile.objects.get(admin_user=request.user)
            except MaintenanceCompanyProfile.DoesNotExist:
                return Response(
                    {"error": "Maintenance company profile not found"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        serializer = TechnicianCreateSerializer(
            data=request.data,
            context={'maintenance_company': maintenance_company}
        )
        
        if serializer.is_valid():
            result = serializer.save()
            return Response(
                TechnicianProfileSerializer(result['technician_profile']).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)