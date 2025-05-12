from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView, # 用于获取 access 和 refresh token (登录)
    TokenRefreshView,    # 用于使用 refresh token 获取新的 access token
)
from .api_views import UserRegistrationView , UserProfileView # 导入 UserProfileView

app_name = 'users_api'

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', UserProfileView.as_view(), name='profile'), # <--- 新增个人资料接口
]