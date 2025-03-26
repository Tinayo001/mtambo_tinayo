"""
URL configuration for Mtambo_BackendApis project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)
from Account_User.views import UserAuthViewSet

urlpatterns = [
    # Authentication Endpoints (JWT)
    path('admin/', admin.site.urls),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/logout/', UserAuthViewSet.as_view({'post': 'user_logout'}), name='token_logout'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # Include user-related URLs
    path('api/', include('Account_User.urls')),  # 🔥 Add this and remove direct `UserViewSet` registration

    # Additional Authentication Endpoints
    path('auth/change-password/', 
         include('Account_User.urls')),  # 🔥 Ensure change-password is handled inside `Account_User`
]
