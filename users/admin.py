# users/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserInventoryItem, ShoppingListItem # 导入所有需要注册的模型

class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'nickname', 'avatar_url')}),
        # 将饮食偏好和不吃食材的字段组添加到用户编辑页面
        (_('Preferences'), {'fields': ('dietary_preferences', 'disliked_ingredients')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    # 在创建用户页面也添加这些自定义字段
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (_('Custom Fields'), {'fields': ('nickname', 'avatar_url')}),
        (_('Preferences'), {'fields': ('dietary_preferences', 'disliked_ingredients')}),
    )
    list_display = ('username', 'email', 'nickname', 'first_name', 'last_name', 'is_staff')
    search_fields = BaseUserAdmin.search_fields + ('nickname',)
    # 为 ManyToManyField 使用 filter_horizontal 以获得更好的用户体验
    filter_horizontal = ('groups', 'user_permissions', 'dietary_preferences', 'disliked_ingredients')

admin.site.register(User, UserAdmin)


@admin.register(UserInventoryItem)
class UserInventoryItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'ingredient', 'notes', 'added_at')
    list_filter = ('user', 'ingredient__name') # 按食材名称过滤更直观
    search_fields = ('user__username', 'ingredient__name', 'notes')
    autocomplete_fields = ['user', 'ingredient']
    date_hierarchy = 'added_at' # 添加日期层级导航

@admin.register(ShoppingListItem)
class ShoppingListItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'ingredient', 'quantity', 'unit', 'is_purchased', 'related_recipe', 'added_at')
    list_filter = ('user', 'is_purchased', 'ingredient__name', 'related_recipe__title')
    search_fields = ('user__username', 'ingredient__name', 'related_recipe__title')
    list_editable = ('is_purchased', 'quantity', 'unit') # 允许在列表页编辑更多字段
    autocomplete_fields = ['user', 'ingredient', 'related_recipe']
    date_hierarchy = 'added_at'
    actions = ['mark_as_purchased', 'mark_as_not_purchased']

    def mark_as_purchased(self, request, queryset):
        queryset.update(is_purchased=True)
    mark_as_purchased.short_description = "标记所选项为 已购买"

    def mark_as_not_purchased(self, request, queryset):
        queryset.update(is_purchased=False)
    mark_as_not_purchased.short_description = "标记所选项为 未购买"