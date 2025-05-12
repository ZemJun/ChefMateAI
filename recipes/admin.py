# recipes\admin.py
from django.contrib import admin
from .models import Ingredient, DietaryPreferenceTag, Recipe ,RecipeIngredient ,Review 

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'description')
    list_filter = ('category',)
    search_fields = ('name', 'description')
    # 对于 ManyToManyField ('self')，Admin界面默认提供了不错的选择器
    # 如果 common_substitutes 很多，可以考虑使用 filter_horizontal 或 filter_vertical
    # filter_horizontal = ('common_substitutes',)

@admin.register(DietaryPreferenceTag)
class DietaryPreferenceTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

class RecipeIngredientInline(admin.TabularInline): # 或者 admin.StackedInline，TabularInline 更紧凑
    model = RecipeIngredient
    extra = 1  # 默认显示几个空的表单行供添加，比如默认显示1行
    autocomplete_fields = ['ingredient'] # 如果食材很多，使用自动完成搜索框会更好
    # fields = ('ingredient', 'quantity', 'unit', 'notes') # 可以明确指定显示的字段和顺序
    # readonly_fields = (...) # 如果有需要只读的内联字段


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'difficulty', 'cooking_time_minutes', 'updated_at')
    list_filter = ('status', 'difficulty', 'author', 'cuisine_type', 'dietary_tags')
    search_fields = ('title', 'description', 'author__username', 'ingredients__name') # 现在可以按食材名称搜索菜谱了
    
    filter_horizontal = ('dietary_tags',)
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (None, {
            'fields': ('title', 'author', 'description', 'main_image_url')
        }),
        ('Details', {
            'fields': ('cooking_time_minutes', 'difficulty', 'cuisine_type', 'dietary_tags')
        }),
        ('Status & Timestamps', {
            'fields': ('status', 'created_at', 'updated_at')
        }),
        # 注意：我们不再直接在 fieldsets 中管理 'ingredients'，因为它将通过 Inline 来处理
    )
    
    inlines = [RecipeIngredientInline] # 将 RecipeIngredientInline 添加到 RecipeAdmin
    
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'user', 'rating', 'comment_summary', 'created_at', 'updated_at')
    list_filter = ('rating', 'user', 'recipe__title') # 按评分、用户、菜谱标题过滤
    search_fields = ('recipe__title', 'user__username', 'comment')
    autocomplete_fields = ['recipe', 'user'] # 方便选择菜谱和用户
    readonly_fields = ('created_at', 'updated_at') # 创建和更新时间通常只读
    date_hierarchy = 'created_at' # 按创建时间进行日期层级导航

    # fieldsets 可以用来组织编辑页面的字段
    fieldsets = (
        (None, {'fields': ('recipe', 'user')}),
        ('Review Details', {'fields': ('rating', 'comment')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

    # 自定义一个方法在列表页显示评论摘要
    def comment_summary(self, obj):
        if obj.comment:
            return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
        return "-"
    comment_summary.short_description = "评论摘要" # 设置列的显示名称