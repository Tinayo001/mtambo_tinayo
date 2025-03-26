from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.db import IntegrityError

from .models import TechnicianProfile, MaintenanceProfile, DeveloperProfile

class UserProfileFactory:
    """
    Factory for creating user profiles based on account type.
    """
    PROFILE_MAP = {
        'technician': TechnicianProfile,
        'maintenance': MaintenanceProfile,
        'developer': DeveloperProfile
    }

    @classmethod
    def create_profile(cls, user, profile_data=None):
        """
        Create a profile for a user based on their account type.
        Handles potential duplicate profile creation.
        """
        profile_class = cls.PROFILE_MAP.get(user.account_type)

        if not profile_class:
            return None

        profile_data = profile_data or {}  # Ensure profile_data is not None

        try:
            # Check if profile already exists before creating
            existing_profile = profile_class.objects.filter(user=user).first()
            if existing_profile:
                return existing_profile

            # Create the appropriate profile
            return profile_class.objects.create(user=user, **profile_data)
        except IntegrityError:
            # If a profile already exists, return the existing one
            return profile_class.objects.get(user=user)

# Disable the signal to prevent automatic profile creation
# @receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Deprecated: Profile creation now handled by serializer
    """
    pass
