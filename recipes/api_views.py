# ChefMateAI/recipes/api_views.py (最终版)

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
from users.models import UserInventoryItem, ShoppingListItem
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
    queryset = Recipe.objects.all().select_related('author').prefetch_related(
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
        if self.action == 'list' or self.action == 'favorites': # 让 favorites action 也用 ListSerializer
            return RecipeListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateUpdateSerializer
        return RecipeDetailSerializer

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user

        if user.is_authenticated:
            queryset = queryset.filter(
                Q(status='published') | Q(author=user)
            )
        else:
            queryset = queryset.filter(status='published')

        if user.is_authenticated and user.disliked_ingredients.exists():
            user_disliked_ids = list(user.disliked_ingredients.values_list('id', flat=True))
            queryset = queryset.exclude(ingredients__id__in=user_disliked_ids)
            
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

        return queryset.distinct()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        available_ingredients_str = request.query_params.get('available_ingredients')
        
        if available_ingredients_str is not None:
            if not available_ingredients_str:
                queryset = queryset.none()
            else:
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
                    ).filter(total_ingredients__gt=0, match_score__gt=0).order_by('-match_score', '-updated_at')
                else:
                    queryset = queryset.none()

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
        recipe = self.get_object()
        user = request.user
        required_ingredients = RecipeIngredient.objects.filter(recipe=recipe)
        required_ingredient_ids = required_ingredients.values_list('ingredient_id', flat=True)
        inventory_ingredient_ids = UserInventoryItem.objects.filter(user=user).values_list('ingredient_id', flat=True)
        shopping_list_ingredient_ids = ShoppingListItem.objects.filter(user=user).values_list('ingredient_id', flat=True)
        needed_ingredient_ids = set(required_ingredient_ids) - set(inventory_ingredient_ids) - set(shopping_list_ingredient_ids)
        if not needed_ingredient_ids:
            return Response({"detail": "太棒了！该菜谱所需食材您都已拥有或已在购物清单中。"}, status=status.HTTP_200_OK)
        items_to_create = [
            ShoppingListItem(
                user=user,
                ingredient_id=item.ingredient_id,
                quantity=item.quantity,
                unit=item.unit,
                related_recipe=recipe
            ) for item in required_ingredients.filter(ingredient_id__in=needed_ingredient_ids)
        ]
        ShoppingListItem.objects.bulk_create(items_to_create)
        return Response({"detail": f"成功将 {len(items_to_create)} 种缺少的食材添加到了您的购物清单。"}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[permissions.IsAuthenticated])
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user
        if request.method == 'POST':
            user.favorite_recipes.add(recipe)
            return Response({'status': 'favorited'}, status=status.HTTP_200_OK)
        elif request.method == 'DELETE':
            user.favorite_recipes.remove(recipe)
            return Response({'status': 'unfavorited'}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def favorites(self, request):
        """返回当前用户收藏的所有菜谱。"""
        user = request.user
        favorited_recipes = user.favorite_recipes.all()
        page = self.paginate_queryset(favorited_recipes)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(favorited_recipes, many=True)
        return Response(serializer.data)

    def get_serializer_context(self):
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
        substitute_data = [{"id": s.id, "name": s.name} for s in substitutes]
        return Response(substitute_data)