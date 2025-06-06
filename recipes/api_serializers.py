# ChefMateAI/recipes/api_serializers.py

from rest_framework import serializers
from .models import Ingredient, DietaryPreferenceTag, Recipe, RecipeIngredient, Review
from django.contrib.auth import get_user_model

User = get_user_model()

class IngredientSubstituteSerializer(serializers.ModelSerializer):
    """用于显示食材替代品的简化序列化器"""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'category', 'description')

class IngredientSerializer(serializers.ModelSerializer):
    common_substitutes = IngredientSubstituteSerializer(many=True, read_only=True)
    
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'category', 'description', 'image_url', 'common_substitutes')

class DietaryPreferenceTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = DietaryPreferenceTag
        fields = ('id', 'name', 'description')

# --- 菜谱相关序列化器 ---

class RecipeIngredientSerializer(serializers.ModelSerializer):
    """用于在菜谱详情中显示食材及其用量"""
    ingredient_name = serializers.CharField(source='ingredient.name', read_only=True)
    ingredient_id = serializers.IntegerField(source='ingredient.id', read_only=True)
    ingredient_category = serializers.CharField(source='ingredient.category', read_only=True)
    substitutes = serializers.SerializerMethodField()

    class Meta:
        model = RecipeIngredient
        fields = ('ingredient_id', 'ingredient_name', 'ingredient_category', 'quantity', 'unit', 'notes', 'substitutes')

    def get_substitutes(self, obj):
        """获取食材的替代品列表"""
        substitutes = obj.ingredient.common_substitutes.all()
        return IngredientSubstituteSerializer(substitutes, many=True).data

class RecipeListSerializer(serializers.ModelSerializer):
    """用于菜谱列表，显示摘要信息"""
    author_username = serializers.CharField(source='author.username', read_only=True, allow_null=True)
    dietary_tags = DietaryPreferenceTagSerializer(many=True, read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'title', 'main_image_url', 'author_username',
            'cooking_time_minutes', 'difficulty', 'cuisine_type',
            'dietary_tags', 'description'
        )
        read_only_fields = fields

class RecipeDetailSerializer(serializers.ModelSerializer):
    """用于菜谱详情，显示完整信息"""
    author_username = serializers.CharField(source='author.username', read_only=True, allow_null=True)
    recipe_ingredients = RecipeIngredientSerializer(source='recipeingredient_set', many=True, read_only=True)
    dietary_tags = DietaryPreferenceTagSerializer(many=True, read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'title', 'description', 'author_username', 'created_at', 'updated_at',
            'cooking_time_minutes', 'difficulty', 'main_image_url',
            'recipe_ingredients',
            'dietary_tags', 'status', 'cuisine_type'
        )
        read_only_fields = fields

# --- 新增的序列化器 ---

class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    """用于在创建菜谱时，接收食材数据的内部序列化器"""
    ingredient_id = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('ingredient_id', 'quantity', 'unit', 'notes')

class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """用于创建和更新菜谱的序列化器"""
    ingredients_data = RecipeIngredientCreateSerializer(many=True, write_only=True)
    dietary_tags = serializers.PrimaryKeyRelatedField(
        queryset=DietaryPreferenceTag.objects.all(),
        many=True,
        required=False
    )
    author_username = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'title', 'description', 'cooking_time_minutes', 'difficulty',
            'main_image_url', 'cuisine_type', 'status', 'dietary_tags',
            'ingredients_data', 'author_username'
        )

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients_data')
        dietary_tags = validated_data.pop('dietary_tags')
        
        recipe = Recipe.objects.create(**validated_data)
        recipe.dietary_tags.set(dietary_tags)

        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=ingredient_data['ingredient_id'],
                quantity=ingredient_data['quantity'],
                unit=ingredient_data['unit'],
                notes=ingredient_data.get('notes', '')
            ) for ingredient_data in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients_data', None)
        dietary_tags_data = validated_data.pop('dietary_tags', None)

        # 更新 Recipe 实例的常规字段
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if dietary_tags_data is not None:
            instance.dietary_tags.set(dietary_tags_data)
        
        if ingredients_data is not None:
            instance.recipeingredient_set.all().delete()
            recipe_ingredients = [
                RecipeIngredient(
                    recipe=instance,
                    ingredient_id=data['ingredient_id'],
                    quantity=data['quantity'],
                    unit=data['unit'],
                    notes=data.get('notes', '')
                ) for data in ingredients_data
            ]
            RecipeIngredient.objects.bulk_create(recipe_ingredients)

        return instance


class ReviewSerializer(serializers.ModelSerializer):
    """用于评价的创建、列表和详情"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Review
        fields = ('id', 'user', 'user_username', 'recipe', 'rating', 'comment', 'created_at', 'updated_at')
        read_only_fields = ('user', 'recipe', 'created_at', 'updated_at', 'user_username')

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("评分必须在 1 到 5 之间。")
        return value