# users/api_serializers.py

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import User, UserInventoryItem, ShoppingListItem
from recipes.models import DietaryPreferenceTag, Ingredient, RecipeIngredient # 导入 RecipeIngredient

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        label="Confirm password",
        style={'input_type': 'password'}
    )
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'password2', 'nickname', 'avatar_url')
        read_only_fields = ('id',)
        extra_kwargs = {
            'nickname': {'required': False, 'allow_blank': True},
            'avatar_url': {'required': False, 'allow_blank': True, 'allow_null': True},
        }

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

    def validate(self, attrs):
        password = attrs.get('password')
        password2 = attrs.get('password2')

        if password != password2:
            raise serializers.ValidationError({"password2": "Passwords do not match."})

        attrs.pop('password2', None) 

        try:
            validate_password(password, user=User(**attrs))
        except DjangoValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})
            
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
    
class UserDetailSerializer(serializers.ModelSerializer):
    dietary_preferences = serializers.SlugRelatedField(
        many=True,
        queryset=DietaryPreferenceTag.objects.all(),
        slug_field='name',
        required=False
    )
    disliked_ingredients = serializers.SlugRelatedField(
        many=True,
        queryset=Ingredient.objects.all(),
        slug_field='name',
        required=False
    )

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'nickname', 'avatar_url', 'dietary_preferences', 'disliked_ingredients', 'first_name', 'last_name')
        read_only_fields = ('id', 'username')
        extra_kwargs = {
            'email': {'required': False},
            'nickname': {'required': False, 'allow_blank': True},
            'avatar_url': {'required': False, 'allow_blank': True, 'allow_null': True},
            'first_name': {'required': False, 'allow_blank': True},
            'last_name': {'required': False, 'allow_blank': True},
        }

    def validate_email(self, value):
        user = self.instance
        if user and User.objects.filter(email__iexact=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("This email address is already in use by another user.")
        elif not user and User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value



class UserInventoryItemSerializer(serializers.ModelSerializer):
    """用户库存物品序列化器"""
    ingredient_name = serializers.CharField(source='ingredient.name', read_only=True)
    
    class Meta:
        model = UserInventoryItem
        fields = ('id', 'ingredient', 'ingredient_name', 'notes', 'added_at')
        read_only_fields = ('id', 'added_at', 'user', 'ingredient_name')


class ShoppingListItemSerializer(serializers.ModelSerializer):
    """购物清单项目序列化器"""
    ingredient_name = serializers.CharField(source='ingredient.name', read_only=True)
    # 食材分类代码 (用于逻辑)
    ingredient_category = serializers.CharField(source='ingredient.category', read_only=True, allow_null=True)
    # 食材分类显示名称 (用于展示) - 依赖 models.py 里的 choices
    ingredient_category_display = serializers.SerializerMethodField(read_only=True)
    related_recipe_title = serializers.CharField(source='related_recipe.title', read_only=True, allow_null=True)
    # 显示单位文本
    unit_display = serializers.SerializerMethodField(read_only=True)

    def get_ingredient_category_display(self, obj):
        try:
            return obj.ingredient.get_category_display()
        except AttributeError:
            return "未知分类"
            
    def get_unit_display(self, obj):
        if not obj.unit:
            return ""
        unit_choices_dict = dict(RecipeIngredient.UNIT_CHOICES)
        return unit_choices_dict.get(obj.unit, obj.unit)

    class Meta:
        model = ShoppingListItem
        fields = (
            'id', 'ingredient', 'ingredient_name', 
            'ingredient_category',
            'ingredient_category_display',
            'quantity', 'unit', 'unit_display',
            'is_purchased',
            'related_recipe', 'related_recipe_title', 'added_at'
        )
        read_only_fields = (
            'id', 'added_at', 'user', 'ingredient_name', 
            'ingredient_category', 'ingredient_category_display', 
            'related_recipe_title', 'unit_display'
        )
        extra_kwargs = {
            'ingredient': {'required': True},
            'related_recipe': {'required': False, 'allow_null': True}
        }
