# ChefMateAI/recipes/api_urls.py (最终修正版)

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

app_name = 'recipes_api'

router = DefaultRouter()
router.register(r'recipes', api_views.RecipeViewSet, basename='recipe')
router.register(r'ingredients', api_views.IngredientViewSet, basename='ingredient')

urlpatterns = [
    # 包含 /recipes/, /recipes/<pk>/, /ingredients/ 等
    path('', include(router.urls)),
    
    # 单独为 dietary-tags 定义路径
    path('dietary-tags/', api_views.DietaryPreferenceTagListView.as_view(), name='dietary-tag-list'),
    
    # 评价的列表和创建
    path('recipes/<int:recipe_pk>/reviews/', api_views.ReviewViewSet.as_view({
        'get': 'list', 
        'post': 'create'
    }), name='recipe-reviews-list'),
    
    # 评价的详情、更新、删除路径
    path('recipes/<int:recipe_pk>/reviews/<int:pk>/', api_views.ReviewViewSet.as_view({
        'get': 'retrieve', 
        'put': 'update', 
        'patch': 'partial_update', 
        'delete': 'destroy'
    }), name='recipe-reviews-detail'),
]