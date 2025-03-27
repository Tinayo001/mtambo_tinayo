from rest_framework import serializers
from django.contrib.auth import get_user_model
from maintenance_company.models import MaintenanceCompanyProfile
from technician.models import TechnicianProfile
from developer.models import DeveloperProfile

User = get_user_model()

# Profile Serializers (Reused for Update)
class BaseTechnicianProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechnicianProfile
        fields = ['specialization']

class BaseMaintenanceProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceCompanyProfile
        fields = ['company_name', 'registration_number']
        extra_kwargs = {
            'company_name': {'required': True},
            'registration_number': {'required': True},
        }


class BaseDeveloperProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeveloperProfile
        fields = [
            'developer_name', 
            'address', 
        ]
        extra_kwargs = {
            'developer_name': {'required': True},
            'additional_data': {'required': False}
        }

class UserCreateSerializer(serializers.ModelSerializer):
    technician_profile = BaseTechnicianProfileSerializer(required=False)
    maintenance_profile = BaseMaintenanceProfileSerializer(required=False)
    developer_profile = BaseDeveloperProfileSerializer(required=False)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'phone_number', 'first_name', 'last_name', 
            'account_type', 'password',
            'technician_profile', 'maintenance_profile', 'developer_profile'
        ]
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, data):
        """
        Ensure only relevant fields are provided based on account_type
        """
        account_type = data.get('account_type')

        # Map account types to expected fields
        allowed_fields = {
            'technician': ['technician_profile'],
            'maintenance': ['maintenance_profile'],
            'developer': ['developer_profile'],
        }

        if account_type not in allowed_fields:
            raise serializers.ValidationError({"account_type": "Invalid account type."})

        # Ensure only the expected fields are present
        for field in allowed_fields.keys():
            if field != account_type and data.get(f"{field}_profile"):
                raise serializers.ValidationError({f"{field}_profile": "This field should not be provided."})

        return data

    def create(self, validated_data):
        """
        Create user and remove profile data from user creation
        """
        # Extract profile data
        profile_data = {}
        account_type = validated_data.pop('account_type')
        
        if account_type == "technician":
            profile_data = validated_data.pop('technician_profile', {})
        elif account_type == "maintenance":
            profile_data = validated_data.pop('maintenance_profile', {})
        elif account_type == "developer":
            profile_data = validated_data.pop('developer_profile', {})

        # Create the user
        user = User.objects.create_user(account_type=account_type, **validated_data)

        # Create profile using factory
        if profile_data:
            from .factory import UserProfileFactory
            UserProfileFactory.create_profile(user, profile_data)

        return user


# ✅ User Update Serializer (NEW)
class UserUpdateSerializer(serializers.ModelSerializer):
    technician_profile = BaseTechnicianProfileSerializer(required=False)
    maintenance_profile = BaseMaintenanceProfileSerializer(required=False)
    developer_profile = BaseDeveloperProfileSerializer(required=False)

    class Meta:
        model = User
        fields = [
            'email', 'phone_number', 'first_name', 'last_name',
            'technician_profile', 'maintenance_profile', 'developer_profile'
        ]
        extra_kwargs = {
            'email': {'read_only': True},  # Email should not be updated
        }

    def update(self, instance, validated_data):
        # Handle profile updates
        profile_data = {
            'technician': validated_data.pop('technician_profile', {}),
            'maintenance': validated_data.pop('maintenance_profile', {}),
            'developer': validated_data.pop('developer_profile', {})
        }

        # Update User fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update the appropriate profile
        if instance.account_type in profile_data:
            profile = getattr(instance, f"{instance.account_type}_profile", None)
            if profile:
                for attr, value in profile_data[instance.account_type].items():
                    setattr(profile, attr, value)
                profile.save()

        return instance

# ✅ User Detail Serializer (for fetching user data)
class UserDetailSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'phone_number', 'first_name', 'last_name', 
            'account_type', 'profile'
        ]

    def get_profile(self, obj):
        # Mapping of account types to human-readable profile names
        PROFILE_NAMES = {
            'technician': 'Technician Profile',
            'maintenance': 'Maintenance Company Profile',
            'developer': 'Developer Profile',
            'admin': 'Administrator Profile'
        }

        # Get the appropriate profile serializer
        profile_map = {
            'technician': BaseTechnicianProfileSerializer,
            'maintenance': BaseMaintenanceProfileSerializer,
            'developer': BaseDeveloperProfileSerializer
        }

        profile_serializer = profile_map.get(obj.account_type)
        if not profile_serializer:
            return {
                'type': PROFILE_NAMES.get(obj.account_type, 'Unknown Profile'),
                'details': None
            }

        try:
            profile = getattr(obj, f'{obj.account_type}_profile')
            profile_data = profile_serializer(profile).data
            
            return {
                'type': PROFILE_NAMES.get(obj.account_type, 'Unknown Profile'),
                'details': profile_data
            }
        except Exception:
            return {
                'type': PROFILE_NAMES.get(obj.account_type, 'Unknown Profile'),
                'details': None
            }

class UserPasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)
    confirm_new_password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError({"confirm_new_password": "New passwords must match."})
        return data

    def update_password(self, user):
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user