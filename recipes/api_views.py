# ChefMateAI/recipes/api_views.py

from rest_framework import generics, permissions, viewsets, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import serializers

from .models import Ingredient, DietaryPreferenceTag, Recipe, Review
from .api_serializers import (
    IngredientSerializer,
    IngredientSubstituteSerializer,
    DietaryPreferenceTagSerializer,
    RecipeListSerializer,
    RecipeDetailSerializer,
    RecipeCreateUpdateSerializer, # 新增
    ReviewSerializer              # 新增
)
from .permissions import IsOwnerOrReadOnly # 新增

class IngredientListView(generics.ListAPIView):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'category', 'description']
    ordering_fields = ['name', 'category']
    ordering = ['name']

class DietaryPreferenceTagListView(generics.ListAPIView):
    queryset = DietaryPreferenceTag.objects.all()
    serializer_class = DietaryPreferenceTagSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name']
    ordering = ['name']

# --- 菜谱视图 (已修改) ---
class RecipeViewSet(viewsets.ModelViewSet): # 从 ReadOnlyModelViewSet 改为 ModelViewSet
    """
    提供菜谱的列表、详情、创建、更新和删除接口。
    支持基于多种条件的筛选。
    """
    queryset = Recipe.objects.filter(status='published').select_related('author').prefetch_related(
        'dietary_tags',
        'recipeingredient_set__ingredient'
    )
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly] # 修改权限
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        'cooking_time_minutes': ['lte', 'gte', 'exact'],
        'difficulty': ['exact'],
        'cuisine_type': ['exact', 'icontains'],
        'author__username': ['exact'],
        'dietary_tags__name': ['exact', 'in'],
    }
    search_fields = ['title', 'description', 'ingredients__name', 'dietary_tags__name']
    ordering_fields = ['cooking_time_minutes', 'difficulty', 'updated_at', 'title']
    ordering = ['-updated_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return RecipeListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateUpdateSerializer
        return RecipeDetailSerializer

    def perform_create(self, serializer):
        """在创建菜谱时，自动将作者设置为当前登录用户"""
        serializer.save(author=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        available_ingredients_str = self.request.query_params.get('available_ingredients')
        if available_ingredients_str:
            try:
                id_list = [s for s in available_ingredients_str.split(',') if s.strip()]
                available_ingredient_ids = [int(id_str.strip()) for id_str in id_list]
                if available_ingredient_ids:
                    queryset = queryset.filter(ingredients__id__in=available_ingredient_ids).distinct()
            except ValueError:
                pass

        exclude_ingredients_str = self.request.query_params.get('exclude_ingredients')
        if exclude_ingredients_str:
            try:
                id_list = [s for s in exclude_ingredients_str.split(',') if s.strip()]
                exclude_ingredient_ids = [int(id_str.strip()) for id_str in id_list]
                if exclude_ingredient_ids:
                    queryset = queryset.exclude(ingredients__id__in=exclude_ingredient_ids)
            except ValueError:
                pass

        if user.is_authenticated:
            user_disliked_ids = list(user.disliked_ingredients.values_list('id', flat=True))
            if user_disliked_ids:
                queryset = queryset.exclude(ingredients__id__in=user_disliked_ids)

        return queryset.distinct()

class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'category', 'description']
    ordering_fields = ['name', 'category']
    ordering = ['name']

    @action(detail=True, methods=['get'])
    def substitutes(self, request, pk=None):
        ingredient = self.get_object()
        substitutes = ingredient.common_substitutes.all()
        serializer = IngredientSubstituteSerializer(substitutes, many=True)
        return Response(serializer.data)

# --- 新增的评价视图 ---
class ReviewViewSet(viewsets.ModelViewSet):
    """
    对菜谱的评价进行增删改查。
    - 列表和详情: 任何人可读
    - 创建: 需登录
    - 更新/删除: 只有评价所有者可操作
    """
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        """重写 get_queryset，使其只返回特定菜谱下的评价。"""
        recipe_pk = self.kwargs.get('recipe_pk')
        if recipe_pk:
            return self.queryset.filter(recipe_id=recipe_pk)
        # 如果不是嵌套访问，则不返回任何结果，或者可以根据需求返回所有评价
        return Review.objects.none()

    def perform_create(self, serializer):
        """在保存评价时自动关联当前用户和菜谱。"""
        recipe_pk = self.kwargs.get('recipe_pk')
        try:
            recipe = Recipe.objects.get(pk=recipe_pk)
        except Recipe.DoesNotExist:
            raise serializers.ValidationError({"recipe": "菜谱不存在。"})
            
        if Review.objects.filter(recipe=recipe, user=self.request.user).exists():
            raise serializers.ValidationError({"detail": "你已经评价过这个菜谱了。"})

        serializer.save(user=self.request.user, recipe=recipe)