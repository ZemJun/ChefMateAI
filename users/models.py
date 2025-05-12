from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    nickname = models.CharField(max_length=100, blank=True, verbose_name="昵称")
    avatar_url = models.URLField(blank=True, null=True, verbose_name="头像链接")
    
    dietary_preferences = models.ManyToManyField(
        'recipes.DietaryPreferenceTag', # 注意这里引用了 'app_name.ModelName'
        blank=True, 
        verbose_name="饮食偏好",
        related_name="users_with_preference" # 添加 related_name 以避免冲突
    )
    disliked_ingredients = models.ManyToManyField(
        'recipes.Ingredient', # 注意这里引用了 'app_name.ModelName'
        blank=True, 
        verbose_name="不吃的食材",
        related_name="users_disliking" # 添加 related_name 以避免冲突
    )

    def __str__(self):
        return self.username