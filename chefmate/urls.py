# chefmate\urls.py
from django.contrib import admin
from django.urls import path, include # 确保导入 include

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from django.conf import settings
from django.conf.urls.static import static

# ---配置 Schema View ---
schema_view = get_schema_view(
   openapi.Info(
      title="ChefMate AI API",
      default_version='v1',
      description="个性化菜谱生成与智能购物清单助手 (ChefMate AI) 的官方 API 文档",
      terms_of_service="https://www.google.com/policies/terms/", # 替换成你自己的服务条款URL
      contact=openapi.Contact(email="contact@chefmate.local"), # 替换成你的联系邮箱
      license=openapi.License(name="BSD License"), # 替换成你项目的许可证
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    # 为我们的 users 应用的 API 设置路由
    path('api/users/', include('users.api_urls')), 
    # 为我们的 recipes 应用的 API 设置路由
    path('api/recipes/', include('recipes.api_urls')), 
    # 测试路由 
    # path('recipes/',include('recipes.urls'))
    
    # --- 文档路由  ---
    
    # Swagger UI 界面
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    # Redoc UI 界面
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    # 原始的 swagger.json 文件
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    
]# 在开发环境下，让 Django 能够提供媒体文件服务
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)