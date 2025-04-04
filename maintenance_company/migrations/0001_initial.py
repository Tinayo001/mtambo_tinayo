# Generated by Django 5.1.7 on 2025-03-31 08:04

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MaintenanceCompanyProfile',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, help_text='Unique identifier for the maintenance company', primary_key=True, serialize=False)),
                ('company_name', models.CharField(help_text='Official name of the maintenance company', max_length=255)),
                ('registration_number', models.CharField(blank=True, help_text='Company registration or license number', max_length=100)),
                ('admin_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='administered_maintenance_companies', to=settings.AUTH_USER_MODEL)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='maintenance_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
