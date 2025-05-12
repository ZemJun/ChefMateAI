from rest_framework import serializers
from .models import Ingredient, DietaryPreferenceTag, Recipe, RecipeIngredient, Review

class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        # 先包含基本字段，后续可按需调整 'common_substitutes' 的序列化方式
        fields = ('id', 'name', 'category', 'description', 'image_url')

class DietaryPreferenceTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = DietaryPreferenceTag
        fields = ('id', 'name', 'description')

# --- 下面是即将用到的菜谱相关序列化器 ---

class RecipeIngredientSerializer(serializers.ModelSerializer):
    """用于在菜谱详情中显示食材及其用量"""
    # 直接显示 ingredient 的名称，而不是嵌套整个 Ingredient 对象
    ingredient_name = serializers.CharField(source='ingredient.name', read_only=True)
    ingredient_id = serializers.IntegerField(source='ingredient.id', read_only=True)
    ingredient_category = serializers.CharField(source='ingredient.category', read_only=True) # 可选

    class Meta:
        model = RecipeIngredient
        fields = ('ingredient_id', 'ingredient_name', 'ingredient_category', 'quantity', 'unit', 'notes')


class RecipeListSerializer(serializers.ModelSerializer):
    """用于菜谱列表，显示摘要信息"""
    author_username = serializers.CharField(source='author.username', read_only=True, allow_null=True)
    dietary_tags = DietaryPreferenceTagSerializer(many=True, read_only=True) # 嵌套显示标签信息
    # 你可能还想在这里添加平均评分等，暂时先省略

    class Meta:
        model = Recipe
        fields = (
            'id', 'title', 'main_image_url', 'author_username',
            'cooking_time_minutes', 'difficulty', 'cuisine_type',
            'dietary_tags', 'description' # description 也可以考虑截断显示
        )
        # 确保只读字段正确设置，因为这是列表展示
        read_only_fields = fields


class RecipeDetailSerializer(serializers.ModelSerializer):
    """用于菜谱详情，显示完整信息"""
    author_username = serializers.CharField(source='author.username', read_only=True, allow_null=True)
    # 使用 RecipeIngredientSerializer 嵌套显示食材列表
    recipe_ingredients = RecipeIngredientSerializer(source='recipeingredient_set', many=True, read_only=True)
    dietary_tags = DietaryPreferenceTagSerializer(many=True, read_only=True)
    # 之后还可以添加 reviews 的嵌套序列化器
    # reviews = ReviewSerializer(many=True, read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'title', 'description', 'author_username', 'created_at', 'updated_at',
            'cooking_time_minutes', 'difficulty', 'main_image_url',
            'recipe_ingredients', # 通过 source 关联到 RecipeIngredient 的 related_name (默认是 modelname_set)
            'dietary_tags', 'status', 'cuisine_type'
            # 菜谱步骤 (RecipeStep) 模型如果创建了，也需要在这里添加
        )
        read_only_fields = fields # 详情页通常也是只读，创建/更新会有单独的序列化器和视图