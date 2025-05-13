# chefmate\urls.py
from django.contrib import admin
from django.urls import path, include # 确保导入 include

urlpatterns = [
    path('admin/', admin.site.urls),
    # 为我们的 users 应用的 API 设置路由 (稍后创建 users/api_urls.py)
    path('api/users/', include('users.api_urls')), 
    # 为我们的 recipes 应用的 API 设置路由 (稍后创建 recipes/api_urls.py)
    path('api/recipes/', include('recipes.api_urls')), 
    # 测试路由 
    path('recipes/',include('recipes.urls'))
]