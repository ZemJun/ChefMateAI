# recipes/models.py
from django.db import models
from django.conf import settings # 用于引用 AUTH_USER_MODEL

class Ingredient(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="食材名称")

    CATEGORY_CHOICES = [
        ('vegetable', '蔬菜'),        # （保留，但部分内容会移到新分类）
        ('fruit', '水果'),
        ('meat', '肉类'),            # （包括红肉：猪、牛、羊等）
        ('poultry', '禽类'),          # （鸡、鸭、鹅等）
        ('seafood', '海鲜'),
        ('egg', '蛋类'),             # <-- 新增 (从 dairy 中分离)
        ('dairy', '乳制品'),          # （牛奶、奶酪、黄油等，不含蛋）
        ('mushroom', '菌菇'),         # <-- 新增 (从 vegetable 中分离)
        ('legume', '豆类'),           # <-- 新增 (如黄豆、绿豆、扁豆、鹰嘴豆、毛豆等)
        ('nut_seed', '坚果与籽类'),   # <-- 新增 (花生、核桃、杏仁、芝麻、瓜子等)
        ('grain', '谷物/主食'),      # （米、面、燕麦、玉米等）
        ('spice', '香料/调料'),      # （非新鲜香草的干香料、酱料等）
        ('herb', '香草'),           # （新鲜或干的植物叶、花、茎，如薄荷、罗勒、香菜）
        ('oil', '油类'),
        ('other', '其他'),           # （酵母、泡打粉、豆腐等不易归入上述明确分类的）
    ]
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        blank=True, # 允许为空，如果某些食材初期难以分类
        null=True,  # 数据库中也允许为空
        verbose_name="分类"
    )
    description = models.TextField(blank=True, null=True, verbose_name="描述")
    image_url = models.URLField(blank=True, null=True, verbose_name="图片链接")
    common_substitutes = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=True, # symmetrical=True 更适合替代品关系，如果是 False 则 A替B 不等于 B替A
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
    
    main_image = models.ImageField(
        upload_to='recipe_main_images/', 
        blank=True, 
        null=True, 
        verbose_name="主图"
    )
    
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        through_fields=('recipe', 'ingredient'),
        related_name='recipes_using_ingredient',
        verbose_name="所需食材"
    )

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
        on_delete=models.CASCADE,
        verbose_name="菜谱"
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name="食材"
    )
    quantity = models.FloatField(verbose_name="用量")

    # VVVVVVVV  这就是修改的核心 VVVVVVVV
    UNIT_CHOICES = [
        ('g', '克 (g)'),
        ('kg', '千克 (kg)'),
        ('ml', '毫升 (ml)'),
        ('l', '升 (l)'),
        ('tsp', '茶匙 (tsp)'),
        ('tbsp', '汤匙 (tbsp)'),
        ('cup', '杯 (cup)'),
        ('piece', '个/只/颗'),
        ('slice', '片'),
        ('pinch', '撮'),
        ('dash', '少量/几滴'),
        ('to_taste', '适量'),
    ]

    unit = models.CharField(
        max_length=10, 
        choices=UNIT_CHOICES, 
        default='g', # 提供一个默认值，'克' 是最常用的
        verbose_name="单位"
    )
    notes = models.CharField(max_length=255, blank=True, null=True, verbose_name="备注", help_text="例如：切碎, 去籽, 融化")

    def __str__(self):
        return f"{self.quantity} {self.unit} of {self.ingredient.name} for {self.recipe.title}"

    class Meta:
        verbose_name = "菜谱食材"
        verbose_name_plural = "菜谱食材"
        unique_together = ('recipe', 'ingredient')
        ordering = ['recipe', 'id']


class Review(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name="菜谱"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews_made',
        verbose_name="用户"
    )
    rating = models.PositiveSmallIntegerField(
        verbose_name="评分",
        help_text="评分 (例如1-5星)"
    )
    comment = models.TextField(blank=True, null=True, verbose_name="评论内容")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    def __str__(self):
        return f"Review for {self.recipe.title} by {self.user.username} ({self.rating} stars)"

    class Meta:
        verbose_name = "菜谱评价"
        verbose_name_plural = "菜谱评价"
        unique_together = ('recipe', 'user')
        ordering = ['-created_at']
        
        
class RecipeStep(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='steps',  # 使用 'steps' 作为反向关联名，更简洁
        verbose_name="所属菜谱"
    )
    step_number = models.PositiveSmallIntegerField(verbose_name="步骤序号")
    description = models.TextField(verbose_name="步骤描述")
    image = models.ImageField(
        upload_to='recipe_steps/', # 图片将上传到 media/recipe_steps/ 目录
        blank=True, 
        null=True, 
        verbose_name="步骤图片 (可选)"
    )

    class Meta:
        verbose_name = "菜谱步骤"
        verbose_name_plural = "菜谱步骤"
        ordering = ['step_number'] # 确保步骤总是按序号排序
        unique_together = ('recipe', 'step_number') # 同一菜谱的步骤序号不能重复

    def __str__(self):
        return f"{self.recipe.title} - 步骤 {self.step_number}"