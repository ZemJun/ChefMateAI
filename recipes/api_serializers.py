# recipes/api_serializers.py

import json
from rest_framework import serializers
from .models import Ingredient, DietaryPreferenceTag, Recipe, RecipeIngredient, Review, RecipeStep

class IngredientSubstituteSerializer(serializers.ModelSerializer):
    """用于显示食材替代品的简化序列化器"""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'category', 'description')


class IngredientSerializer(serializers.ModelSerializer):
    """
    食材的完整序列化器，现在包含分类的显示名称。
    """
    common_substitutes = IngredientSubstituteSerializer(many=True, read_only=True)
    # 用于获取人类可读的分类名称
    category_display = serializers.SerializerMethodField()

    class Meta:
        model = Ingredient
        fields = (
            'id', 'name', 'category', 'category_display', 'description', 
            'image_url', 'common_substitutes'
        )
    
    def get_category_display(self, obj):

        return obj.get_category_display()


class DietaryPreferenceTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = DietaryPreferenceTag
        fields = ('id', 'name', 'description')

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

class RecipeStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeStep
        fields = ('id', 'step_number', 'description', 'image')

class RecipeListSerializer(serializers.ModelSerializer):
    """用于菜谱列表，显示摘要信息"""
    author_username = serializers.CharField(source='author.username', read_only=True, allow_null=True)
    dietary_tags = DietaryPreferenceTagSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'title', 'main_image', 'author_username',
            'cooking_time_minutes', 'difficulty', 'cuisine_type',
            'dietary_tags', 'description', 'is_favorited'
        )
        read_only_fields = fields

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user and user.is_authenticated:
            return obj in user.favorite_recipes.all()
        return False

class RecipeDetailSerializer(serializers.ModelSerializer):
    """用于菜谱详情，显示完整信息"""
    author_username = serializers.CharField(source='author.username', read_only=True, allow_null=True)
    recipe_ingredients = RecipeIngredientSerializer(source='recipeingredient_set', many=True, read_only=True)
    dietary_tags = DietaryPreferenceTagSerializer(many=True, read_only=True)
    steps = RecipeStepSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'title', 'description', 'author_username', 'created_at', 'updated_at',
            'cooking_time_minutes', 'difficulty', 'main_image',
            'recipe_ingredients', 
            'dietary_tags', 'status', 'cuisine_type',
            'steps', 'is_favorited'
        )
        read_only_fields = fields

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user and user.is_authenticated:
            return obj in user.favorite_recipes.all()
        return False

class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    """用于在创建菜谱时，接收食材数据的内部序列化器"""
    ingredient_id = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('ingredient_id', 'quantity', 'unit', 'notes')

class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """用于创建和更新菜谱的序列化器 (已优化)"""
    ingredients_data = serializers.CharField(write_only=True)
    steps_data = serializers.CharField(write_only=True, required=False)
    
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
            'main_image', 'cuisine_type', 'status', 'dietary_tags',
            'ingredients_data', 'steps_data', 'author_username'
        )

    def create(self, validated_data):
        ingredients_data = json.loads(validated_data.pop('ingredients_data'))
        steps_data = json.loads(validated_data.pop('steps_data', '[]'))
        dietary_tags = validated_data.pop('dietary_tags', [])
        
        recipe = Recipe.objects.create(**validated_data)
        
        if dietary_tags:
            recipe.dietary_tags.set(dietary_tags)

        recipe_ingredients = [RecipeIngredient(recipe=recipe, ingredient_id=data['ingredient_id'], quantity=data['quantity'], unit=data['unit'], notes=data.get('notes', '')) for data in ingredients_data]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

        recipe_steps = [RecipeStep(recipe=recipe, **data) for data in steps_data]
        if recipe_steps:
            RecipeStep.objects.bulk_create(recipe_steps)

        return recipe

    def update(self, instance, validated_data):
        if 'ingredients_data' in validated_data:
            ingredients_data = json.loads(validated_data.pop('ingredients_data'))
            instance.recipeingredient_set.all().delete()
            recipe_ingredients = [RecipeIngredient(recipe=instance, ingredient_id=data['ingredient_id'], quantity=data['quantity'], unit=data['unit'], notes=data.get('notes', '')) for data in ingredients_data]
            RecipeIngredient.objects.bulk_create(recipe_ingredients)

        if 'steps_data' in validated_data:
            steps_data = json.loads(validated_data.pop('steps_data'))
            instance.steps.all().delete()
            recipe_steps = [RecipeStep(recipe=instance, **data) for data in steps_data]
            if recipe_steps:
                RecipeStep.objects.bulk_create(recipe_steps)
        
        if 'dietary_tags' in validated_data:
            dietary_tags_data = validated_data.pop('dietary_tags')
            instance.dietary_tags.set(dietary_tags_data)

        return super().update(instance, validated_data)

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

class RecipeSimpleSerializer(serializers.ModelSerializer):
    """用于菜谱选择的极简序列化器"""
    class Meta:
        model = Recipe
        fields = ('id', 'title', 'cuisine_type') 