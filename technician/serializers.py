from rest_framework import serializers
from django.db import transaction
from django.contrib.auth.password_validation import validate_password

from Account_User.models import User
from Account_User.serializers import UserDetailSerializer, UserCreateSerializer
from .models import TechnicianProfile


class TechnicianProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for TechnicianProfile model.
    Includes nested user information.
    """
    user = UserDetailSerializer(read_only=True)
    user_data = UserCreateSerializer(write_only=True, required=False)
    maintenance_company_name = serializers.CharField(
        source='maintenance_company.company_name', 
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = TechnicianProfile
        fields = [
            'id', 'user', 'user_data', 'specialization',
            'maintenance_company', 'maintenance_company_name'
        ]
        read_only_fields = ['id', 'user', 'maintenance_company']
    
    @transaction.atomic
    def create(self, validated_data):
        """
        Create a new technician profile with associated user.
        """
        user_data = validated_data.pop('user_data', None)
        
        if user_data:
            user_serializer = UserCreateSerializer(data=user_data)
            user_serializer.is_valid(raise_exception=True)
            user = user_serializer.save(account_type='technician')
            validated_data['user'] = user
        
        instance = super().create(validated_data)
        return instance
    
    @transaction.atomic
    def update(self, instance, validated_data):
        """
        Update an existing technician profile.
        """
        user_data = validated_data.pop('user_data', None)
        
        if user_data and instance.user:
            user = instance.user
            user_serializer = UserDetailSerializer(user, data=user_data, partial=True)
            user_serializer.is_valid(raise_exception=True)
            user_serializer.save()
        
        return super().update(instance, validated_data)


class TechnicianCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a new technician user and profile.
    """
    email = serializers.EmailField()
    phone_number = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    password = serializers.CharField(write_only=True)
    specialization = serializers.CharField(required=False, allow_blank=True)
    
    def validate_password(self, value):
        """
        Validate password complexity.
        """
        validate_password(value)
        return value
    
    def validate_email(self, value):
        """
        Validate email uniqueness.
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate_phone_number(self, value):
        """
        Validate phone number uniqueness.
        """
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("A user with this phone number already exists.")
        return value
    
    @transaction.atomic
    def create(self, validated_data):
        """
        Create a new technician user and profile.
        """
        maintenance_company = self.context.get('maintenance_company')
        specialization = validated_data.pop('specialization', '')
        
        # Create user with technician account type
        user = User.objects.create_user(
            email=validated_data['email'],
            phone_number=validated_data['phone_number'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            account_type='technician'
        )
        
        # Create technician profile
        technician = TechnicianProfile.objects.create(
            user=user,
            specialization=specialization,
            maintenance_company=maintenance_company
        )
        
        return {
            'user': user,
            'technician_profile': technician
        }