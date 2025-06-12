# users/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class User(AbstractUser):
    nickname = models.CharField(max_length=100, blank=True, verbose_name="昵称")
    avatar_url = models.URLField(blank=True, null=True, verbose_name="头像链接")
    
    dietary_preferences = models.ManyToManyField(
        'recipes.DietaryPreferenceTag', 
        blank=True, 
        verbose_name="饮食偏好",
        related_name="users_with_preference" 
    )
    disliked_ingredients = models.ManyToManyField(
        'recipes.Ingredient', 
        blank=True, 
        verbose_name="不吃的食材",
        related_name="users_disliking"
    )
    

    favorite_recipes = models.ManyToManyField(
        'recipes.Recipe',
        blank=True,
        verbose_name="收藏的菜谱",
        related_name="favorited_by"
    )


    def __str__(self):
        return self.username


class UserInventoryItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        verbose_name="用户"
    )
    ingredient = models.ForeignKey(
        'recipes.Ingredient', 
        on_delete=models.CASCADE,
        verbose_name="食材"
    )
    notes = models.CharField(max_length=255, blank=True, null=True, verbose_name="备注")
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")

    def __str__(self):
        return f"{self.user.username}'s inventory: {self.ingredient.name}"

    class Meta:
        verbose_name = "用户库存食材"
        verbose_name_plural = "用户库存食材"
        unique_together = ('user', 'ingredient')
        ordering = ['user', 'added_at']


class ShoppingListItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        verbose_name="用户"
    )
    ingredient = models.ForeignKey(
        'recipes.Ingredient', 
        on_delete=models.CASCADE, 
        verbose_name="食材"
    )
    quantity = models.FloatField(blank=True, null=True, verbose_name="建议数量")
    unit = models.CharField(max_length=50, blank=True, null=True, verbose_name="建议单位")
    is_purchased = models.BooleanField(default=False, verbose_name="已购买")
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="添加时间")
    
    related_recipe = models.ForeignKey(
        'recipes.Recipe',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="关联菜谱"
    )

    def __str__(self):
        status = "Purchased" if self.is_purchased else "To Buy"
        return f"{self.user.username}'s list: {self.ingredient.name} ({status})"

    class Meta:
        verbose_name = "购物清单项"
        verbose_name_plural = "购物清单项"
        ordering = ['user', 'is_purchased', 'added_at']