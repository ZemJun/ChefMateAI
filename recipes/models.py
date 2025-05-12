from django.db import models
from django.conf import settings # 用于引用 AUTH_USER_MODEL

class Ingredient(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="食材名称")
    
    CATEGORY_CHOICES = [
        ('vegetable', '蔬菜'),
        ('meat', '肉类'),
        ('poultry', '禽类'),
        ('seafood', '海鲜'),
        ('dairy', '乳制品'),
        ('fruit', '水果'),
        ('grain', '谷物/主食'),
        ('spice', '香料/调料'),
        ('herb', '香草'),
        ('oil', '油类'),
        ('other', '其他'),
    ]
    category = models.CharField(
        max_length=50, 
        choices=CATEGORY_CHOICES, 
        blank=True, 
        null=True, 
        verbose_name="分类"
    )
    description = models.TextField(blank=True, null=True, verbose_name="描述")
    image_url = models.URLField(blank=True, null=True, verbose_name="图片链接")
    common_substitutes = models.ManyToManyField(
        'self', 
        blank=True, 
        symmetrical=True,
        verbose_name="常见替代品"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "食材"
        verbose_name_plural = "食材"
        ordering = ['name']
        
# 注意 DietaryPreferenceTag 的位置，它现在是顶层类，在 Ingredient 外部
class DietaryPreferenceTag(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="饮食偏好标签名称")
    description = models.TextField(blank=True, null=True, verbose_name="描述")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "饮食偏好标签"
        verbose_name_plural = "饮食偏好标签"
        ordering = ['name']
            
            
class Recipe(models.Model):
    title = models.CharField(max_length=200, verbose_name="菜谱标题")
    description = models.TextField(blank=True, null=True, verbose_name="简介")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recipes',
        verbose_name="作者"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    cooking_time_minutes = models.PositiveIntegerField(blank=True, null=True, verbose_name="烹饪时长(分钟)")
    DIFFICULTY_CHOICES = [
        (1, '简单'),
        (2, '中等'),
        (3, '困难'),
    ]
    difficulty = models.PositiveSmallIntegerField(
        choices=DIFFICULTY_CHOICES, 
        blank=True, 
        null=True, 
        verbose_name="难度"
    )
    main_image_url = models.URLField(blank=True, null=True, verbose_name="主图链接")

    # ------------------- 在这里添加 ingredients 字段 -------------------
    ingredients = models.ManyToManyField(
        Ingredient, 
        through='RecipeIngredient', # 指定使用 RecipeIngredient 作为中间表
        through_fields=('recipe', 'ingredient'), # 可选但明确
        related_name='recipes_using_ingredient', 
        verbose_name="所需食材"
    )
    # -----------------------------------------------------------------
    
    dietary_tags = models.ManyToManyField(
        DietaryPreferenceTag, 
        blank=True, 
        related_name='recipes',
        verbose_name="饮食标签"
    )
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('pending_review', '待审核'),
        ('published', '已发布'),
        ('rejected', '已拒绝'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name="状态"
    )
    cuisine_type = models.CharField(max_length=100, blank=True, null=True, verbose_name="菜系")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "菜谱"
        verbose_name_plural = "菜谱"
        ordering = ['-updated_at', 'title']
        


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe, 
        on_delete=models.CASCADE, # 如果菜谱被删除，相关的食材条目也应删除
        verbose_name="菜谱"
    )
    ingredient = models.ForeignKey(
        Ingredient, 
        on_delete=models.CASCADE, # 如果食材被删除，相关的菜谱食材条目也应删除 (或者 models.PROTECT 阻止删除)
        verbose_name="食材"
    )
    quantity = models.FloatField(verbose_name="用量")
    unit = models.CharField(max_length=50, verbose_name="单位", help_text="例如：克, 个, 勺, 毫升, 杯")
    notes = models.CharField(max_length=255, blank=True, null=True, verbose_name="备注", help_text="例如：切碎, 去籽, 融化")

    def __str__(self):
        return f"{self.quantity} {self.unit} of {self.ingredient.name} for {self.recipe.title}"

    class Meta:
        verbose_name = "菜谱食材"
        verbose_name_plural = "菜谱食材"
        # 确保在一个菜谱中，同一种食材只出现一次
        unique_together = ('recipe', 'ingredient')
        ordering = ['recipe', 'id'] # 按菜谱排序，然后在菜谱内按添加顺序