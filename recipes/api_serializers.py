# ChefMateAI/recipes/api_serializers.py

from rest_framework import serializers
from .models import Ingredient, DietaryPreferenceTag, Recipe, RecipeIngredient, Review
from users.models import User # 如果有需要，可以导入User

# --- 原有序列化器 ---
class IngredientSubstituteSerializer(serializers.ModelSerializer):
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

class RecipeIngredientSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.CharField(source='ingredient.name', read_only=True)
    ingredient_id = serializers.IntegerField(source='ingredient.id', read_only=True)
    ingredient_category = serializers.CharField(source='ingredient.category', read_only=True)
    substitutes = serializers.SerializerMethodField()

    class Meta:
        model = RecipeIngredient
        fields = ('ingredient_id', 'ingredient_name', 'ingredient_category', 'quantity', 'unit', 'notes', 'substitutes')

    def get_substitutes(self, obj):
        substitutes = obj.ingredient.common_substitutes.all()
        return IngredientSubstituteSerializer(substitutes, many=True).data

# --- 修改 RecipeListSerializer ---
class RecipeListSerializer(serializers.ModelSerializer):
    """用于菜谱列表，显示摘要信息"""
    author_username = serializers.CharField(source='author.username', read_only=True, allow_null=True)
    dietary_tags = DietaryPreferenceTagSerializer(many=True, read_only=True)
    # 新增 match_score 字段
    match_score = serializers.FloatField(read_only=True, required=False, help_text="食材匹配度得分 (0.0 到 1.0)")

    class Meta:
        model = Recipe
        fields = (
            'id', 'title', 'main_image_url', 'author_username',
            'cooking_time_minutes', 'difficulty', 'cuisine_type',
            'dietary_tags', 'description',
            'match_score'  # 添加到字段列表
        )
        read_only_fields = fields


class RecipeDetailSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True, allow_null=True)
    recipe_ingredients = RecipeIngredientSerializer(source='recipeingredient_set', many=True, read_only=True)
    dietary_tags = DietaryPreferenceTagSerializer(many=True, read_only=True)
    
    class Meta:
        model = Recipe
        fields = (
            'id', 'title', 'description', 'author_username', 'created_at', 'updated_at',
            'cooking_time_minutes', 'difficulty', 'main_image_url',
            'recipe_ingredients', 'dietary_tags', 'status', 'cuisine_type'
        )
        read_only_fields = fields

# --- 阶段一中新增的序列化器 ---
class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    ingredient_id = serializers.IntegerField()
    class Meta:
        model = RecipeIngredient
        fields = ('ingredient_id', 'quantity', 'unit', 'notes')

class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
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
        recipe_ingredients = []
        for ingredient_data in ingredients_data:
            recipe_ingredients.append(
                RecipeIngredient(
                    recipe=recipe,
                    ingredient_id=ingredient_data['ingredient_id'],
                    quantity=ingredient_data['quantity'],
                    unit=ingredient_data['unit'],
                    notes=ingredient_data.get('notes', '')
                )
            )
        RecipeIngredient.objects.bulk_create(recipe_ingredients)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients_data', None)
        dietary_tags_data = validated_data.pop('dietary_tags', None)
        
        # 使用 setattr 更新所有常规字段
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if dietary_tags_data is not None:
            instance.dietary_tags.set(dietary_tags_data)
        
        if ingredients_data is not None:
            instance.recipeingredient_set.all().delete()
            recipe_ingredients = []
            for ingredient_data in ingredients_data:
                recipe_ingredients.append(
                    RecipeIngredient(
                        recipe=instance,
                        ingredient_id=ingredient_data['ingredient_id'],
                        quantity=ingredient_data['quantity'],
                        unit=ingredient_data['unit'],
                        notes=ingredient_data.get('notes', '')
                    )
                )
            RecipeIngredient.objects.bulk_create(recipe_ingredients)

        return instance

class ReviewSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Review
        fields = ('id', 'user', 'user_username', 'recipe', 'rating', 'comment', 'created_at', 'updated_at')
        read_only_fields = ('user', 'recipe', 'created_at', 'updated_at', 'user_username')

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError("评分必须在 1 到 5 之间。")
        return value