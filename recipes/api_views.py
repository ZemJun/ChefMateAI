# ChefMateAI/recipes/api_views.py

from rest_framework import generics, permissions, viewsets, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q, F, FloatField, ExpressionWrapper
from django.db.models.functions import Coalesce
from rest_framework import serializers
from .models import Ingredient, DietaryPreferenceTag, Recipe, RecipeIngredient, Review
from users.models import UserInventoryItem, ShoppingListItem # 导入用户模型
from .api_serializers import (
    IngredientSerializer,
    DietaryPreferenceTagSerializer,
    RecipeListSerializer,
    RecipeDetailSerializer,
    RecipeCreateUpdateSerializer,
    ReviewSerializer
)
from .permissions import IsOwnerOrReadOnly


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


class RecipeViewSet(viewsets.ModelViewSet):
    """
    提供菜谱的列表、详情、创建、更新和删除接口。
    - 支持基于多种条件的筛选。
    - 支持基于持有食材的智能推荐排序。
    - 支持一键将缺少食材加入购物清单。
    """
    queryset = Recipe.objects.filter(status='published').select_related('author').prefetch_related(
        'dietary_tags',
        'recipeingredient_set__ingredient'
    )
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
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

    def get_queryset(self):
        # 注意：原有的 available_ingredients 过滤逻辑已被移至 list 方法中进行智能排序
        queryset = super().get_queryset()
        user = self.request.user

        exclude_ingredients_str = self.request.query_params.get('exclude_ingredients')
        if exclude_ingredients_str:
            exclude_ingredient_ids = []
            try:
                id_list = [s for s in exclude_ingredients_str.split(',') if s.strip()]
                exclude_ingredient_ids = [int(id_str.strip()) for id_str in id_list]
            except ValueError:
                pass
            if exclude_ingredient_ids:
                queryset = queryset.exclude(ingredients__id__in=exclude_ingredient_ids)

        if user.is_authenticated:
            user_disliked_ids = list(user.disliked_ingredients.values_list('id', flat=True))
            if user_disliked_ids:
                queryset = queryset.exclude(ingredients__id__in=user_disliked_ids)

        return queryset.distinct()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        available_ingredients_str = request.query_params.get('available_ingredients')
        
        if available_ingredients_str:
            available_ingredient_ids = []
            try:
                id_list = [s for s in available_ingredients_str.split(',') if s.strip()]
                available_ingredient_ids = [int(id_str.strip()) for id_str in id_list]
            except ValueError:
                return Response({"error": "无效的 available_ingredients 参数格式。应为逗号分隔的ID。"}, status=status.HTTP_400_BAD_REQUEST)

            if available_ingredient_ids:
                queryset = queryset.annotate(
                    total_ingredients=Coalesce(Count('ingredients', distinct=True), 0),
                    matched_ingredients=Coalesce(Count('ingredients', filter=Q(ingredients__id__in=available_ingredient_ids), distinct=True), 0)
                ).annotate(
                    match_score=ExpressionWrapper(
                        F('matched_ingredients') * 1.0 / F('total_ingredients'),
                        output_field=FloatField()
                    )
                )
                queryset = queryset.filter(total_ingredients__gt=0, match_score__gt=0).order_by('-match_score', '-updated_at')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def add_to_shopping_list(self, request, pk=None):
        """
        将当前菜谱中用户缺少的食材添加到购物清单。
        API端点: POST /api/recipes/recipes/{pk}/add_to_shopping_list/
        """
        recipe = self.get_object()
        user = request.user
        
        required_ingredients = RecipeIngredient.objects.filter(recipe=recipe)
        required_ingredient_ids = required_ingredients.values_list('ingredient_id', flat=True)
        inventory_ingredient_ids = UserInventoryItem.objects.filter(user=user).values_list('ingredient_id', flat=True)
        shopping_list_ingredient_ids = ShoppingListItem.objects.filter(user=user).values_list('ingredient_id', flat=True)
        
        needed_ingredient_ids = set(required_ingredient_ids) - set(inventory_ingredient_ids) - set(shopping_list_ingredient_ids)
        
        if not needed_ingredient_ids:
            return Response({"detail": "太棒了！该菜谱所需食材您都已拥有或已在购物清单中。"}, status=status.HTTP_200_OK)
            
        items_to_create = []
        ingredients_with_details = required_ingredients.filter(ingredient_id__in=needed_ingredient_ids)
        
        for item in ingredients_with_details:
            items_to_create.append(
                ShoppingListItem(
                    user=user,
                    ingredient_id=item.ingredient_id,
                    quantity=item.quantity,
                    unit=item.unit,
                    related_recipe=recipe
                )
            )
            
        ShoppingListItem.objects.bulk_create(items_to_create)
        
        return Response(
            {"detail": f"成功将 {len(items_to_create)} 种缺少的食材添加到了您的购物清单。"},
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post', 'delete'], permission_classes=[permissions.IsAuthenticated])
    def favorite(self, request, pk=None):
        """用户收藏或取消收藏菜谱"""
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            if recipe in user.favorite_recipes.all():
                return Response({'detail': '已经收藏过了。'}, status=status.HTTP_400_BAD_REQUEST)
            user.favorite_recipes.add(recipe)
            return Response({'status': 'favorited'}, status=status.HTTP_200_OK)
        
        elif request.method == 'DELETE':
            if recipe not in user.favorite_recipes.all():
                return Response({'detail': '尚未收藏。'}, status=status.HTTP_400_BAD_REQUEST)
            user.favorite_recipes.remove(recipe)
            return Response({'status': 'unfavorited'}, status=status.HTTP_204_NO_CONTENT)
    def get_serializer_context(self):
        """确保 request 对象被传递到 serializer context 中"""
        return {'request': self.request}


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        recipe_pk = self.kwargs.get('recipe_pk')
        if recipe_pk:
            return self.queryset.filter(recipe_id=recipe_pk)
        return super().get_queryset()

    def perform_create(self, serializer):
        recipe_pk = self.kwargs.get('recipe_pk')
        try:
            recipe = Recipe.objects.get(pk=recipe_pk)
        except Recipe.DoesNotExist:
            raise serializers.ValidationError("菜谱不存在。")
            
        if Review.objects.filter(recipe=recipe, user=self.request.user).exists():
            raise serializers.ValidationError({"detail": "你已经评价过这个菜谱了。"})

        serializer.save(user=self.request.user, recipe=recipe)


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
        # 注意: 这里的序列化器在阶段一中并没有定义，如果需要请确保已定义
        # from .api_serializers import IngredientSubstituteSerializer
        # serializer = IngredientSubstituteSerializer(substitutes, many=True)
        # return Response(serializer.data)
        # 为确保能直接运行，暂时返回简化数据
        substitute_data = [{"id": s.id, "name": s.name} for s in substitutes]
        return Response(substitute_data)
    
    