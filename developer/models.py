from django.db import models
from django.conf import settings

class DeveloperProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='developer_profile'
    )
    developer_name = models.CharField(max_length=255, blank=False)
    address = models.TextField(blank=True)

    def __str__(self):
        return f"Developer: {self.user.email}"