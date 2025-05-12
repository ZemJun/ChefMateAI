from rest_framework import serializers
from .models import Ingredient, DietaryPreferenceTag, Recipe, RecipeIngredient, Review # 按需导入

class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'category', 'description', 'image_url', 'common_substitutes')
        # common_substitutes 也是 M2M 到 self，可以用 SlugRelatedField 或嵌套自身
        # 这里为了简单，先不处理 common_substitutes 的深度序列化

class DietaryPreferenceTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = DietaryPreferenceTag
        fields = ('id', 'name', 'description')

# ... 其他 Recipe 相关的 Serializer 之后会添加 ...