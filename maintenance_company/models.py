import uuid
from django.db import models
from django.conf import settings

class MaintenanceCompanyProfile(models.Model):
    # Use UUID as primary key
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the maintenance company"
    )
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='maintenance_profile'
    )
        
    company_name = models.CharField(
        max_length=255, 
        help_text="Official name of the maintenance company"
    )
        
    registration_number = models.CharField(
        max_length=100, 
        blank=True,
        help_text="Company registration or license number"
    )
        
    # New field to explicitly track admin
    admin_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL,
        related_name='administered_maintenance_companies', 
        null=True, 
        blank=True
    )
    
    def save(self, *args, **kwargs):
        # Automatically set admin user if not set
        if not self.admin_user:
            self.admin_user = self.user
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Maintenance Company: {self.company_name}"
