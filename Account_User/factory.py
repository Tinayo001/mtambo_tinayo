from django.db import IntegrityError
from maintenance_company.models import MaintenanceCompanyProfile
from technician.models import TechnicianProfile
from developer.models import DeveloperProfile

class UserProfileFactory:
    """
    Factory for creating user profiles based on account type.
    """
    PROFILE_MAP = {
        'maintenance': MaintenanceCompanyProfile,
        'technician': TechnicianProfile,
        'developer': DeveloperProfile
    }

    @classmethod
    def create_profile(cls, user, profile_data=None):
        """
        Create a profile for a user based on their account type.
        """
        profile_class = cls.PROFILE_MAP.get(user.account_type)

        if not profile_class:
            return None

        profile_data = profile_data or {}

        try:
            # Create profile with admin user set for maintenance companies
            if user.account_type == 'maintenance':
                profile = profile_class.objects.create(
                    user=user, 
                    admin_user=user,
                    **profile_data
                )
            else:
                profile = profile_class.objects.create(user=user, **profile_data)

            return profile

        except IntegrityError:
            # If profile exists, return existing
            return profile_class.objects.get(user=user)
