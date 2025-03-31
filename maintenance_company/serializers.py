from rest_framework import serializers
from django.db import transaction

from Account_User.models import User
from Account_User.serializers import UserDetailSerializer, UserCreateSerializer
from .models import MaintenanceCompanyProfile
from technician.models import TechnicianProfile
from technician.serializers import TechnicianProfileSerializer


class MaintenanceCompanyProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the MaintenanceCompanyProfile model.
    Includes user information through a nested UserSerializer.
    """
    user = UserDetailSerializer(read_only=True)
    user_data = UserCreateSerializer(write_only=True, required=False)
    admin_email = serializers.EmailField(source='admin_user.email', read_only=True)
    technician_count = serializers.SerializerMethodField()
    
    class Meta:
        model = MaintenanceCompanyProfile
        fields = '__all__'
        read_only_fields = ['id', 'user', 'admin_user', 'admin_email', 'created_at', 'updated_at']
    
    def get_technician_count(self, obj):
        """
        Get the count of technicians associated with this company.
        """
        return TechnicianProfile.objects.filter(maintenance_company=obj).count()
    
    @transaction.atomic
    def create(self, validated_data):
        """
        Create a new maintenance company profile with associated user.
        """
        user_data = validated_data.pop('user_data', None)
        admin_user = validated_data.get('admin_user')
        
        if user_data and not admin_user:
            # If creating a new user for this company
            user_serializer = UserCreateSerializer(data=user_data)
            user_serializer.is_valid(raise_exception=True)
            user = user_serializer.save(account_type='maintenance')
            validated_data['user'] = user
            validated_data['admin_user'] = user
        
        instance = super().create(validated_data)
        return instance
    
    @transaction.atomic
    def update(self, instance, validated_data):
        """
        Update an existing maintenance company profile.
        """
        user_data = validated_data.pop('user_data', None)
        
        if user_data and instance.user:
            user = instance.user
            user_serializer = UserDetailSerializer(user, data=user_data, partial=True)
            user_serializer.is_valid(raise_exception=True)
            user_serializer.save()
        
        return super().update(instance, validated_data)


class MaintenanceCompanyDetailSerializer(MaintenanceCompanyProfileSerializer):
    """
    Extended serializer with more details about the maintenance company,
    including a list of associated technicians.
    """
    technicians = serializers.SerializerMethodField()

    class Meta:
        model = MaintenanceCompanyProfile
        fields = MaintenanceCompanyProfileSerializer.Meta.fields  # Keep '__all__'
        read_only_fields = MaintenanceCompanyProfileSerializer.Meta.read_only_fields

    def get_technicians(self, obj):
        """
        Get a list of all technicians associated with this company.
        """
        technicians = TechnicianProfile.objects.filter(maintenance_company=obj)
        return TechnicianProfileSerializer(technicians, many=True).data
