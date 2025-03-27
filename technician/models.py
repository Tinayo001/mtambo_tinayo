from django.db import models
from django.conf import settings

class TechnicianProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='technician_profile'
    )
    specialization = models.CharField(max_length=100, blank=True)
    certification = models.CharField(max_length=100, blank=True)
    years_of_experience = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"Technician: {self.user.email}"