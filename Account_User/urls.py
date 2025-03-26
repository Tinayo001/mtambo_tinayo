from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import UserViewSet
from rest_framework.authtoken.views import obtain_auth_token

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('api/auth/login/', obtain_auth_token, name='api_token_auth'),
    path('', include(router.urls)),
]