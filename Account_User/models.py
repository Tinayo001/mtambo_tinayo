import uuid
import re
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.conf import settings

class CustomUserManager(BaseUserManager):
    def create_user(self, email, phone_number, password=None, **extra_fields):
        """
        Create and save a User with the given email, phone number, and password.
        """
        if not email:
            raise ValueError('Users must have an email address')
        
        # Validate email
        email = self.normalize_email(email)
        
        # Validate phone number
        phone_validator = RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )
        phone_validator(phone_number)
        
        user = self.model(
            email=email, 
            phone_number=phone_number, 
            **extra_fields
        )
        
        user.set_password(password)
        user.full_clean()  # Validate model constraints
        user.save(using=self._db)
        return user

    def create_superuser(self, email, phone_number, password=None, **extra_fields):
        """
        Create a superuser with admin privileges
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, phone_number, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model with enhanced fields and validation
    """
    ACCOUNT_TYPE_CHOICES = [
        ('developer', 'Developer'), 
        ('maintenance', 'Maintenance'), 
        ('technician', 'Technician'),
        ('admin', 'Administrator')
    ]

    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False
    )
    
    first_name = models.CharField(
        max_length=100, 
        help_text="User's first name"
    )
    
    last_name = models.CharField(
        max_length=100, 
        help_text="User's last name"
    )
    
    email = models.EmailField(
        unique=True, 
        help_text="Unique email address for the user"
    )
    
    phone_number = models.CharField(
        max_length=16,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$', 
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ],
        help_text="User's contact phone number"
    )
    
    account_type = models.CharField(
        max_length=50,
        choices=ACCOUNT_TYPE_CHOICES,
        help_text="Type of user account"
    )
    
    created_at = models.DateTimeField(
        default=timezone.now, 
        help_text="Timestamp of user account creation"
    )
    
    last_login = models.DateTimeField(
        null=True, 
        blank=True, 
        help_text="Timestamp of last user login"
    )
    
    is_staff = models.BooleanField(
        default=False, 
        help_text="Designates whether the user can access the admin site"
    )
    
    is_superuser = models.BooleanField(
        default=False, 
        help_text="Designates that this user has all permissions without explicitly assigning them"
    )
    
    is_active = models.BooleanField(
        default=True, 
        help_text="Designates whether this user account should be treated as active"
    )
    
    profile_picture = models.ImageField(
        upload_to='profile_pictures/', 
        null=True, 
        blank=True, 
        help_text="Optional profile picture for the user"
    )

    # Add related_name to resolve reverse accessor clash
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        help_text='The groups this user belongs to.'
    )
    
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',
        blank=True,
        help_text='Specific permissions for this user.'
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone_number', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        """
        Returns the first_name.
        """
        return self.first_name

    def has_perm(self, perm, obj=None):
        """
        Always return True for active staff and superusers
        """
        return self.is_active and (self.is_staff or self.is_superuser)

    def has_module_perms(self, app_label):
        """
        Always return True for active staff and superusers
        """
        return self.is_active and (self.is_staff or self.is_superuser)

# Profile Models
class BaseProfile(models.Model):
    """
    Abstract base class for all user profiles
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='%(class)s_profile'
    )
    created_at = models.DateTimeField(
        default=timezone.now, 
        help_text="Profile creation timestamp"
    )

    class Meta:
        abstract = True

class TechnicianProfile(BaseProfile):
    """
    Specific profile for Technician users
    """
    specialization = models.CharField(
        max_length=100, 
        blank=True, 
        help_text="Technician's area of expertise"
    )
    def __str__(self):
        return f"Technician: {self.user.get_full_name()}"

class MaintenanceProfile(BaseProfile):
    """
    Specific profile for Maintenance Company users
    """
    company_name = models.CharField(
        max_length=255, 
        blank=True,
        help_text="Official name of the maintenance company"
    )
    registration_number = models.CharField(
        max_length=100, 
        blank=True,
        help_text="Company registration or license number"
    )

    def __str__(self):
        return f"Maintenance Company: {self.company_name}"

class DeveloperProfile(BaseProfile):
    """
    Specific profile for Building Developer users
    """
    developer_name = models.CharField(
        max_length=255,
        blank=True,  # ✅ Allow empty values
        null=True,   # ✅ Allow NULL in the database
        help_text="Full name of the building developer"
    )

    
    address = models.TextField(
        help_text="Primary business or residential address",
        blank=True,
        null=True
    )
    company_name = models.CharField(
        max_length=255, 
        blank=True,
        null=True,  # Make nullable if not always required
        help_text="Developer's company name (if applicable)"
    )
    

    def __str__(self):
        return f"Developer: {self.developer_name}"
    
class SpecializationType(models.TextChoices):
    """
    Predefined specialization types for technicians
    """
    ELEVATORS = 'ELEVATORS', 'Elevator Systems'
    HVAC = 'HVAC', 'HVAC Systems'
    GENERATORS = 'GENERATORS', 'Power Generators'