# ChefMateAI/recipes/api_urls.py

from django.urls import path, include
from rest_framework_nested import routers
from . import api_views

app_name = 'recipes_api'

router = routers.DefaultRouter()
router.register(r'recipes', api_views.RecipeViewSet, basename='recipe')
router.register(r'ingredients', api_views.IngredientViewSet, basename='ingredient')

reviews_router = routers.NestedDefaultRouter(router, r'recipes', lookup='recipe')
reviews_router.register(r'reviews', api_views.ReviewViewSet, basename='recipe-reviews')

urlpatterns = [
    # 为了保持旧的简单列表URL可用，可以保留它们
    path('ingredients/list/', api_views.IngredientListView.as_view(), name='ingredient-list'),
    path('dietary-tags/', api_views.DietaryPreferenceTagListView.as_view(), name='dietary-tag-list'),
    
    # 包含主 router 和嵌套 router 的 URL
    path('', include(router.urls)),
    path('', include(reviews_router.urls)),
]