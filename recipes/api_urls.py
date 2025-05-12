from django.urls import path, include # 确保导入 include
from rest_framework.routers import DefaultRouter
from .api_views import (
    IngredientListView,
    DietaryPreferenceTagListView,
    RecipeViewSet
)

app_name = 'recipes_api'

router = DefaultRouter()
router.register(r'recipes', RecipeViewSet, basename='recipe') # 'recipe' 是 URL 名称的前缀

urlpatterns = [
    path('ingredients/', IngredientListView.as_view(), name='ingredient-list'),
    path('dietary-tags/', DietaryPreferenceTagListView.as_view(), name='dietary-tag-list'),
    path('', include(router.urls)), # 将 router 生成的菜谱 URL 包含进来
    # 例如会生成:
    # /api/recipes/recipes/ (列表)
    # /api/recipes/recipes/<pk>/ (详情)
]