# users/api_serializers.py
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password # Django自带的密码验证器
from django.core.exceptions import ValidationError as DjangoValidationError # Django的验证错误
from .models import User # 导入我们的自定义User模型
from recipes.models import DietaryPreferenceTag, Ingredient # 确保导入
# from recipes.api_serializers import DietaryPreferenceTagSerializer, IngredientSerializer # 假设你会在recipes app中创建这些

class UserRegistrationSerializer(serializers.ModelSerializer):
    # 我们需要显式定义 password 和 password2 字段，因为它们不在 User 模型中直接作为可写字段
    # (User模型中的password是哈希后的，且AbstractUser不直接暴露原始密码字段用于ModelSerializer)
    password = serializers.CharField(
        write_only=True, # 此字段只用于写入(创建/更新)，不会在序列化输出中显示
        required=True,
        style={'input_type': 'password'} # 在Browsable API中显示为密码输入框
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        label="Confirm password", # 在Browsable API中显示的标签
        style={'input_type': 'password'}
    )
    email = serializers.EmailField(required=True) # 确保email是必填的

    class Meta:
        model = User
        # 指定序列化器应包含模型中的哪些字段
        # 在注册时，我们通常需要 username, email, password
        # nickname 和 avatar_url 可以是可选的，用户后续可以更新
        fields = ('id', 'username', 'email', 'password', 'password2', 'nickname', 'avatar_url')
        read_only_fields = ('id',) # id 是只读的，由数据库自动生成
        extra_kwargs = {
            'nickname': {'required': False, 'allow_blank': True},
            'avatar_url': {'required': False, 'allow_blank': True, 'allow_null': True},
        }

    def validate_email(self, value):
        """
        检查邮箱是否已存在。
        """
        if User.objects.filter(email__iexact=value).exists(): # iexact 表示不区分大小写比较
            raise serializers.ValidationError("A user with that email already exists.")
        return value

    def validate(self, attrs):
        """
        在所有字段都通过基本验证后，进行跨字段验证。
        这里我们检查 password 和 password2 是否匹配。
        并使用Django的密码验证器检查密码强度。
        """
        password = attrs.get('password')
        password2 = attrs.get('password2')

        if password != password2:
            raise serializers.ValidationError({"password2": "Passwords do not match."})

        # 移除 password2，因为它不需要保存到数据库
        attrs.pop('password2', None) 

        # 验证密码强度 (使用 Django 自带的验证器)
        try:
            # validate_password 会直接抛出 DjangoValidationError
            validate_password(password, user=User(**attrs)) # 创建一个临时的User实例传递给验证器
        except DjangoValidationError as e:
            # 将 DjangoValidationError 转换为 DRF 的 serializers.ValidationError
            # e.messages 是一个列表
            raise serializers.ValidationError({"password": list(e.messages)})
            
        return attrs # 必须返回验证后的属性字典

    def create(self, validated_data):
        """
        创建并返回一个新的 User 实例，使用验证过的数据。
        这个方法在调用 serializer.save() 时被执行 (当 serializer 没有 instance 时)。
        """
        # validated_data 中不应包含 'password2'，已经在 validate 方法中移除
        
        # 从 validated_data 中提取 password，因为它需要特殊处理 (哈希)
        password = validated_data.pop('password')
        
        # 使用其他字段创建用户实例
        # **validated_data 将字典解包为关键字参数
        user = User.objects.create_user(**validated_data)
        
        # user.set_password(password) # create_user 已经处理了密码哈希
        # 对于 create_user, 它内部会调用 set_password，所以上面这行不需要了。
        # 如果我们是直接 User.objects.create()，则需要手动 user.set_password() 和 user.save()
        
        return user
    
class UserDetailSerializer(serializers.ModelSerializer):
    # 为了在API中显示完整的关联对象信息，而不是仅仅ID
    # 你需要在 recipes.api_serializers 中先定义好 DietaryPreferenceTagSerializer 和 IngredientSerializer
    # 这里我们先假设它们已经存在，并且只显示名称
    dietary_preferences = serializers.SlugRelatedField(
        many=True,
        queryset=DietaryPreferenceTag.objects.all(),
        slug_field='name',
        required=False # 允许不选择
    )
    disliked_ingredients = serializers.SlugRelatedField(
        many=True,
        queryset=Ingredient.objects.all(),
        slug_field='name',
        required=False # 允许不选择
    )

    class Meta:
        model = User
        # username 通常不允许在个人资料中修改，如果允许，则去掉 read_only_fields 中的 username
        fields = ('id', 'username', 'email', 'nickname', 'avatar_url', 'dietary_preferences', 'disliked_ingredients', 'first_name', 'last_name')
        read_only_fields = ('id', 'username') # id 和 username 通常是只读的
        extra_kwargs = {
            'email': {'required': False}, # 假设用户可以在profile更新email，但注册时是必须的
            'nickname': {'required': False, 'allow_blank': True},
            'avatar_url': {'required': False, 'allow_blank': True, 'allow_null': True},
            'first_name': {'required': False, 'allow_blank': True},
            'last_name': {'required': False, 'allow_blank': True},
        }

    def validate_email(self, value):
        # 当用户更新邮箱时，检查新邮箱是否已被其他用户占用 (除了当前用户自己)
        user = self.instance # 获取当前正在被更新的用户实例
        if user and User.objects.filter(email__iexact=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("This email address is already in use by another user.")
        # 如果是创建新用户（虽然这个Serializer主要用于更新），也需要检查
        elif not user and User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

    # 如果 dietary_preferences 和 disliked_ingredients 是通过 ID 列表来更新，
    # 你可能不需要特别的 validate 方法，DRF 会处理。
    # 如果是通过名称列表，你可能需要在 update 方法中处理从名称到实例的转换。
    # SlugRelatedField 使得可以直接使用 slug_field (如名称) 来进行关联。