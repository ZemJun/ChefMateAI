# chefmate/urls.py (最终版本)

from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static

# 导入所有你需要用到的 API 视图
from users import api_views as user_api_views
from recipes import api_views as recipe_api_views
from recipes.api_views import RecipeSimpleListView # <--- 导入新的视图

# 导入 simplejwt 的视图
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# 导入 drf-yasg 的视图
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# --- 配置 Schema View ---
schema_view = get_schema_view(
   openapi.Info(
      title="ChefMate AI API",
      default_version='v1',
      description="...",
      contact=openapi.Contact(email="contact@chefmate.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)


# 创建一个唯一的、顶级的 API Router
router = DefaultRouter()

# 在这个唯一的 router 中注册所有 ViewSet
router.register(r'users/inventory', user_api_views.UserInventoryViewSet, basename='inventory')
router.register(r'users/shopping-list', user_api_views.ShoppingListItemViewSet, basename='shopping-list')
router.register(r'recipes', recipe_api_views.RecipeViewSet, basename='recipe')
router.register(r'ingredients', recipe_api_views.IngredientViewSet, basename='ingredient')


# 定义 urlpatterns
urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- 将所有非 router 管理的 API 路径放在这里 ---
    path('api/users/register/', user_api_views.UserRegistrationView.as_view(), name='register'),
    path('api/users/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/users/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/users/profile/', user_api_views.UserProfileView.as_view(), name='profile'),
    
    # 简化菜谱列表API
    path('api/recipes/simple-list/', RecipeSimpleListView.as_view(), name='recipe-simple-list'),
    
    path('api/dietary-tags/', recipe_api_views.DietaryPreferenceTagListView.as_view(), name='dietary-tag-list'),
    
    # 手动定义 reviews 的路径
    path('api/recipes/<int:recipe_pk>/reviews/', recipe_api_views.ReviewViewSet.as_view({'get': 'list', 'post': 'create'}), name='recipe-reviews-list'),
    path('api/recipes/<int:recipe_pk>/reviews/<int:pk>/', recipe_api_views.ReviewViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='recipe-reviews-detail'),

    path('api/', include(router.urls)),
    
    # --- 文档路由 ---
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# 在开发环境下，让 Django 能够提供媒体文件服务
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)