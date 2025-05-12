from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin # 重命名以避免冲突
from .models import User

class UserAdmin(BaseUserAdmin):
    # fieldsets 定义了在编辑用户时，表单中字段的分组和顺序
    # 我们需要在现有的 fieldsets 基础上增加我们的自定义字段
    # BaseUserAdmin.fieldsets 是一个元组，每个元素也是一个元组 (组名, {'fields': (字段1, 字段2, ...)})
    
    # 查看 BaseUserAdmin.fieldsets 的默认结构可以帮助我们决定把新字段放在哪里
    # 默认通常有 'Personal info', 'Permissions', 'Important dates' 等组
    # 我们可以选择将自定义字段加入 'Personal info' 组，或者创建一个新组
    
    # 方式一：加入到 'Personal info' 组
    # 找到 'Personal info' 组并添加字段
    # 注意：BaseUserAdmin.fieldsets 是元组，元组不可直接修改，需要重建
    
    # 我们需要复制并修改原始的fieldsets
    # 原始的UserAdmin.fieldsets大概是这样的（版本不同可能略有差异）：
    # (
    #     (None, {'fields': ('username', 'password')}),
    #     (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
    #     (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    #     (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    # )
    # 我们想把 nickname 和 avatar_url 加到 'Personal info' 字段组里

    # 我们可以通过重新定义 fieldsets 来包含我们的字段
    # 为了国际化，Django Admin 常用 gettext_lazy as _
    from django.utils.translation import gettext_lazy as _

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'nickname', 'avatar_url')}), # 在这里添加
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    # add_fieldsets 定义了在添加新用户时，表单中字段的分组和顺序
    # 我们也需要在这里添加自定义字段，如果希望创建用户时就能填的话
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (_('Custom Fields'), {'fields': ('nickname', 'avatar_url')}),
    )

    # list_display 定义了在用户列表页显示的字段
    list_display = ('username', 'email', 'nickname', 'first_name', 'last_name', 'is_staff')
    
    # 如果希望列表页的 nickname 可编辑 (不推荐直接在列表页编辑太多内容)
    # list_editable = ('nickname',)

    # 如果希望可以根据 nickname 搜索
    search_fields = BaseUserAdmin.search_fields + ('nickname',)


admin.site.register(User, UserAdmin) # 注册时使用我们自定义的 UserAdmin