from rest_framework import serializers
from .models import Ingredient, DietaryPreferenceTag, Recipe, RecipeIngredient, Review

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

# --- 下面是即将用到的菜谱相关序列化器 ---

class RecipeIngredientSerializer(serializers.ModelSerializer):
    """用于在菜谱详情中显示食材及其用量"""
    # 直接显示 ingredient 的名称，而不是嵌套整个 Ingredient 对象
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

class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """用于创建和更新菜谱的序列化器"""
    recipe_ingredients = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        help_text="食材列表，每个食材包含 id, quantity, unit, notes"
    )
    dietary_tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=DietaryPreferenceTag.objects.all(),
        required=False
    )

    class Meta:
        model = Recipe
        fields = (
            'id', 'title', 'description', 'cooking_time_minutes', 'difficulty',
            'main_image_url', 'cuisine_type', 'status', 'recipe_ingredients',
            'dietary_tags'
        )
        read_only_fields = ('id',)

    def validate_recipe_ingredients(self, value):
        """验证食材列表的格式"""
        if not value:
            raise serializers.ValidationError("至少需要一个食材")
        
        for ingredient_data in value:
            if not all(k in ingredient_data for k in ['id', 'quantity', 'unit']):
                raise serializers.ValidationError("每个食材必须包含 id, quantity 和 unit")
            
            try:
                ingredient_id = int(ingredient_data['id'])
                if not Ingredient.objects.filter(id=ingredient_id).exists():
                    raise serializers.ValidationError(f"食材ID {ingredient_id} 不存在")
            except (ValueError, TypeError):
                raise serializers.ValidationError("食材ID必须是整数")
            
            try:
                quantity = float(ingredient_data['quantity'])
                if quantity <= 0:
                    raise serializers.ValidationError("食材数量必须大于0")
            except (ValueError, TypeError):
                raise serializers.ValidationError("食材数量必须是数字")
        
        return value

    def create(self, validated_data):
        """创建菜谱及其关联的食材"""
        recipe_ingredients = validated_data.pop('recipe_ingredients', [])
        dietary_tags = validated_data.pop('dietary_tags', [])
        
        # 设置作者为当前用户
        validated_data['author'] = self.context['request'].user
        
        # 创建菜谱
        recipe = Recipe.objects.create(**validated_data)
        
        # 添加食材
        for ingredient_data in recipe_ingredients:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient_id=ingredient_data['id'],
                quantity=ingredient_data['quantity'],
                unit=ingredient_data['unit'],
                notes=ingredient_data.get('notes', '')
            )
        
        # 添加饮食标签
        if dietary_tags:
            recipe.dietary_tags.set(dietary_tags)
        
        return recipe

    def update(self, instance, validated_data):
        """更新菜谱及其关联的食材"""
        recipe_ingredients = validated_data.pop('recipe_ingredients', None)
        dietary_tags = validated_data.pop('dietary_tags', None)
        
        # 更新菜谱基本信息
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # 如果提供了新的食材列表，则更新
        if recipe_ingredients is not None:
            # 删除旧的食材关联
            instance.recipeingredient_set.all().delete()
            # 添加新的食材
            for ingredient_data in recipe_ingredients:
                RecipeIngredient.objects.create(
                    recipe=instance,
                    ingredient_id=ingredient_data['id'],
                    quantity=ingredient_data['quantity'],
                    unit=ingredient_data['unit'],
                    notes=ingredient_data.get('notes', '')
                )
        
        # 如果提供了新的饮食标签，则更新
        if dietary_tags is not None:
            instance.dietary_tags.set(dietary_tags)
        
        return instance