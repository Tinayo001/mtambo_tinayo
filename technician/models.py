import uuid
from django.db import models
from django.conf import settings
from maintenance_company.models import MaintenanceCompanyProfile

class TechnicianProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='technician_profile'
    )
    specialization = models.CharField(max_length=100, blank=True)
    maintenance_company = models.ForeignKey(
        MaintenanceCompanyProfile, 
        on_delete=models.CASCADE, 
        related_name="technicians",
        null=True,
        blank=True
    )

    def __str__(self):
        return f"Technician: {self.user.email}"
