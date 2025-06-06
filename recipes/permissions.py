from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    自定义权限，只允许对象的所有者编辑它。
    对于读取操作 (GET, HEAD, OPTIONS)，总是允许。
    """

    def has_object_permission(self, request, view, obj):
        # 读取权限对任何人开放，
        # 所以我们总是允许 GET, HEAD, OPTIONS 请求。
        if request.method in permissions.SAFE_METHODS:
            return True

        # 写入权限只给对象的所有者。
        # 假设模型实例有一个 'author' 或 'user' 字段。
        # 我们会尝试检查 obj.author 和 obj.user
        owner = getattr(obj, 'author', None) or getattr(obj, 'user', None)

        return owner == request.user