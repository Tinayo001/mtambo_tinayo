from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import uuid
from django.utils import timezone

class CustomUserManager(BaseUserManager):
    def create_user(self, email, phone_number, password=None, **extra_fields):
        """
        Create and save a User with the given email, phone number, and password.
        """
        if not email:
            raise ValueError('Users must have an email address')
        
        email = self.normalize_email(email)
        
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

        return self.create_user(email, phone_number, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    ACCOUNT_TYPE_CHOICES = [
        ('developer', 'Developer'), 
        ('maintenance', 'Maintenance'), 
        ('technician', 'Technician'),
        ('admin', 'Administrator')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=16, unique=True)
    
    account_type = models.CharField(
        max_length=50, 
        choices=ACCOUNT_TYPE_CHOICES
    )
    
    created_at = models.DateTimeField(default=timezone.now)
    
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone_number', 'first_name', 'last_name', 'account_type']

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"