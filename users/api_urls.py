# ChefMateAI/users/api_urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .api_views import (
    UserRegistrationView, 
    UserProfileView,
    UserInventoryViewSet,
    ShoppingListItemViewSet
)

app_name = 'users_api'

router = DefaultRouter()
router.register(r'inventory', UserInventoryViewSet, basename='inventory')
router.register(r'shopping-list', ShoppingListItemViewSet, basename='shopping-list')

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    
    path('', include(router.urls)),
]