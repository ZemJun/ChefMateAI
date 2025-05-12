# recipes/api_urls.py
from django.urls import path
# from .api_views import ... (稍后会导入 recipes 的 API 视图)

app_name = 'recipes_api'

urlpatterns = [
    # 例如:
    # path('list/', RecipeListView.as_view(), name='recipe-list'),
    # path('<int:pk>/', RecipeDetailView.as_view(), name='recipe-detail'),
]