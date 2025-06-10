from django.contrib import admin
from .models import Ingredient, DietaryPreferenceTag, Recipe, RecipeIngredient, Review, RecipeStep

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'description')
    list_filter = ('category',)
    search_fields = ('name', 'description')
    filter_horizontal = ('common_substitutes',)

@admin.register(DietaryPreferenceTag)
class DietaryPreferenceTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    autocomplete_fields = ['ingredient']

class RecipeStepInline(admin.TabularInline):
    model = RecipeStep
    extra = 1
    ordering = ('step_number',)
    # 如果希望在步骤中也能方便地上传图片
    fields = ('step_number', 'description', 'image')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'difficulty', 'cooking_time_minutes', 'updated_at')
    list_filter = ('status', 'difficulty', 'author', 'cuisine_type', 'dietary_tags')
    search_fields = ('title', 'description', 'author__username', 'ingredients__name')
    
    filter_horizontal = ('dietary_tags',)
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (None, {
            'fields': ('title', 'author', 'description', 'main_image') # 使用新的 main_image 字段
        }),
        ('Details', {
            'fields': ('cooking_time_minutes', 'difficulty', 'cuisine_type', 'dietary_tags')
        }),
        ('Status & Timestamps', {
            'fields': ('status', 'created_at', 'updated_at')
        }),
    )
    
    inlines = [RecipeIngredientInline, RecipeStepInline]
    
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'user', 'rating', 'comment_summary', 'created_at', 'updated_at')
    list_filter = ('rating', 'user', 'recipe__title')
    search_fields = ('recipe__title', 'user__username', 'comment')
    autocomplete_fields = ['recipe', 'user']
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'

    fieldsets = (
        (None, {'fields': ('recipe', 'user')}),
        ('Review Details', {'fields': ('rating', 'comment')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

    def comment_summary(self, obj):
        if obj.comment:
            return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
        return "-"
    comment_summary.short_description = "评论摘要"

# 如果你希望直接在Admin中管理步骤，可以注册RecipeStep模型
@admin.register(RecipeStep)
class RecipeStepAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'step_number', 'description')
    list_filter = ('recipe__title',)
    search_fields = ('description', 'recipe__title')
    autocomplete_fields = ['recipe']