from rest_framework import generics, permissions, viewsets
from django_filters.rest_framework import DjangoFilterBackend # 用于强大的过滤
from rest_framework.filters import SearchFilter, OrderingFilter # 用于搜索和排序

from .models import Ingredient, DietaryPreferenceTag, Recipe
from .api_serializers import (
    IngredientSerializer,
    DietaryPreferenceTagSerializer,
    RecipeListSerializer,
    RecipeDetailSerializer
)
# from .permissions import IsOwnerOrReadOnly # 如果之后需要对象级别的权限

class IngredientListView(generics.ListAPIView):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.AllowAny] # 通常食材列表是公开的
    filter_backends = [SearchFilter, OrderingFilter] # 允许搜索和排序
    search_fields = ['name', 'category', 'description'] # 可以按这些字段搜索
    ordering_fields = ['name', 'category'] # 可以按这些字段排序
    ordering = ['name'] # 默认排序

class DietaryPreferenceTagListView(generics.ListAPIView):
    queryset = DietaryPreferenceTag.objects.all()
    serializer_class = DietaryPreferenceTagSerializer
    permission_classes = [permissions.AllowAny] # 通常标签列表也是公开的
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name']
    ordering = ['name']

# --- 菜谱视图 ---
class RecipeViewSet(viewsets.ReadOnlyModelViewSet): # 使用 ReadOnlyModelViewSet 因为暂时只提供列表和详情
    """
    提供菜谱的列表和详情接口。
    支持基于多种条件的筛选。
    """
    queryset = Recipe.objects.filter(status='published').select_related('author').prefetch_related(
        'dietary_tags',
        'recipeingredient_set__ingredient' # 优化查询，预取关联的食材信息
    ) # 只显示已发布的菜谱，并优化查询
    permission_classes = [permissions.AllowAny] # 浏览菜谱通常是公开的
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    # DjangoFilterBackend 的 filterset_fields 用于精确匹配
    filterset_fields = {
        'cooking_time_minutes': ['lte', 'gte', 'exact'], # lte: 小于等于, gte: 大于等于
        'difficulty': ['exact'],
        'cuisine_type': ['exact', 'icontains'],
        'author__username': ['exact'], # 按作者用户名筛选
        'dietary_tags__name': ['exact', 'in'], # 按饮食标签名称筛选 (in 用于多个标签)
        # 'ingredients__name': ['exact', 'in'], # 按包含的食材名称筛选 (这个会更复杂，下面单独处理)
    }
    search_fields = ['title', 'description', 'ingredients__name', 'dietary_tags__name'] # 模糊搜索
    ordering_fields = ['cooking_time_minutes', 'difficulty', 'updated_at', 'title'] # 可排序字段
    ordering = ['-updated_at'] # 默认按更新时间倒序

    def get_serializer_class(self):
        if self.action == 'list':
            return RecipeListSerializer
        if self.action == 'retrieve':
            return RecipeDetailSerializer
        return RecipeListSerializer # 默认或备用

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # 1. 根据用户拥有的食材进行筛选 (available_ingredients)
        #    参数格式: available_ingredients=番茄,鸡蛋  (逗号分隔的食材名称)
        #    或 available_ingredients=1,2 (逗号分隔的食材ID) -> 推荐用ID，更精确
        available_ingredients_str = self.request.query_params.get('available_ingredients')
        if available_ingredients_str:
            available_ingredient_ids = []
            try:
                # 假设前端传递的是食材ID列表
                available_ingredient_ids = [int(id_str.strip()) for id_str in available_ingredients_str.split(',')]
            except ValueError:
                # 如果传递的是名称，需要先查询ID，这里简化处理，推荐前端传ID
                pass

            if available_ingredient_ids:
                # 这是一个复杂的查询：找到那些 *主要* 食材是用户拥有的菜谱
                # 这里简化为：至少包含一个用户拥有的食材的菜谱
                # 更高级的匹配（例如：拥有食材占菜谱总食材的比例）会更复杂
                queryset = queryset.filter(ingredients__id__in=available_ingredient_ids).distinct()


        # 2. 根据用户不吃的食材进行排除 (exclude_ingredients)
        #    参数格式: exclude_ingredients=香菜,洋葱 (逗号分隔的食材名称)
        #    或 exclude_ingredients=3,4 (逗号分隔的食材ID)
        exclude_ingredients_str = self.request.query_params.get('exclude_ingredients')
        if exclude_ingredients_str:
            exclude_ingredient_ids = []
            try:
                exclude_ingredient_ids = [int(id_str.strip()) for id_str in exclude_ingredients_str.split(',')]
            except ValueError:
                pass
            if exclude_ingredient_ids:
                queryset = queryset.exclude(ingredients__id__in=exclude_ingredient_ids)

        # 3. (可选) 如果用户已登录，自动应用其偏好 (disliked_ingredients, dietary_preferences)
        #    这个逻辑也可以放在前端，由前端读取用户profile后主动构造查询参数
        if user.is_authenticated:
            # 自动排除用户不吃的食材
            user_disliked_ids = list(user.disliked_ingredients.values_list('id', flat=True))
            if user_disliked_ids:
                queryset = queryset.exclude(ingredients__id__in=user_disliked_ids)

            # (可选) 自动筛选用户饮食偏好的菜谱
            # user_preference_ids = list(user.dietary_preferences.values_list('id', flat=True))
            # if user_preference_ids:
            #     # 要求菜谱 *至少* 包含一个用户的饮食偏好标签
            #     queryset = queryset.filter(dietary_tags__id__in=user_preference_ids).distinct()
            #     # 或者要求菜谱 *所有* 标签都在用户偏好内 (更严格，更复杂)

        return queryset.distinct() #确保结果不重复