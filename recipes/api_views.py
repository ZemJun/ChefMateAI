from rest_framework import generics, permissions, viewsets
from django_filters.rest_framework import DjangoFilterBackend # 用于强大的过滤
from rest_framework.filters import SearchFilter, OrderingFilter # 用于搜索和排序
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import models

from .models import Ingredient, DietaryPreferenceTag, Recipe
from .api_serializers import (
    IngredientSerializer,
    IngredientSubstituteSerializer,
    DietaryPreferenceTagSerializer,
    RecipeListSerializer,
    RecipeDetailSerializer,
    RecipeCreateUpdateSerializer
)
from .permissions import IsOwnerOrReadOnly

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
class RecipeViewSet(viewsets.ModelViewSet):
    """
    提供菜谱的完整CRUD操作。
    支持基于多种条件的筛选。
    """
    queryset = Recipe.objects.all().select_related('author').prefetch_related(
        'dietary_tags',
        'recipeingredient_set__ingredient'
    )
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        'cooking_time_minutes': ['lte', 'gte', 'exact'],
        'difficulty': ['exact'],
        'cuisine_type': ['exact', 'icontains'],
        'author__username': ['exact'],
        'dietary_tags__name': ['exact', 'in'],
        'status': ['exact'],
    }
    search_fields = ['title', 'description', 'ingredients__name', 'dietary_tags__name']
    ordering_fields = ['cooking_time_minutes', 'difficulty', 'updated_at', 'title']
    ordering = ['-updated_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # 如果用户未登录，只显示已发布的菜谱
        if not user.is_authenticated:
            return queryset.filter(status='published')

        # 如果用户已登录，显示：
        # 1. 所有已发布的菜谱
        # 2. 用户自己的草稿和待审核的菜谱
        return queryset.filter(
            models.Q(status='published') |
            models.Q(author=user, status__in=['draft', 'pending_review'])
        ).distinct()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateUpdateSerializer
        if self.action == 'list':
            return RecipeListSerializer
        if self.action == 'retrieve':
            return RecipeDetailSerializer
        return RecipeListSerializer

    def perform_create(self, serializer):
        """创建菜谱时自动设置作者"""
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'])
    def submit_for_review(self, request, pk=None):
        """将草稿提交审核"""
        recipe = self.get_object()
        if recipe.status != 'draft':
            return Response(
                {"detail": "只有草稿状态的菜谱可以提交审核"},
                status=400
            )
        recipe.status = 'pending_review'
        recipe.save()
        return Response({"status": "success"})

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """发布菜谱（仅管理员可用）"""
        if not request.user.is_staff:
            return Response(
                {"detail": "只有管理员可以发布菜谱"},
                status=403
            )
        recipe = self.get_object()
        if recipe.status != 'pending_review':
            return Response(
                {"detail": "只有待审核状态的菜谱可以发布"},
                status=400
            )
        recipe.status = 'published'
        recipe.save()
        return Response({"status": "success"})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """拒绝菜谱（仅管理员可用）"""
        if not request.user.is_staff:
            return Response(
                {"detail": "只有管理员可以拒绝菜谱"},
                status=403
            )
        recipe = self.get_object()
        if recipe.status != 'pending_review':
            return Response(
                {"detail": "只有待审核状态的菜谱可以被拒绝"},
                status=400
            )
        recipe.status = 'rejected'
        recipe.save()
        return Response({"status": "success"})

class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    提供食材相关的API接口，包括获取替代品列表
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'category', 'description']
    ordering_fields = ['name', 'category']
    ordering = ['name']

    @action(detail=True, methods=['get'])
    def substitutes(self, request, pk=None):
        """
        获取指定食材的替代品列表
        """
        ingredient = self.get_object()
        substitutes = ingredient.common_substitutes.all()
        serializer = IngredientSubstituteSerializer(substitutes, many=True)
        return Response(serializer.data)