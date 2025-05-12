# users/api_views.py
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken # 用于注册后直接返回token
from .api_serializers import UserRegistrationSerializer, UserDetailSerializer
from .models import User

class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all() # CreateAPIView 需要一个 queryset，尽管我们这里主要用它来创建
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny] # 允许任何人访问此端点进行注册

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True) # 如果验证失败，自动抛出异常并返回400响应
        user = serializer.save() # 调用 serializer 的 create() 方法

        # ---- 注册成功后，为用户生成并返回JWT ----
        refresh = RefreshToken.for_user(user)
        
        response_data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserRegistrationSerializer(user, context=self.get_serializer_context()).data # 返回用户信息
        }
        # 从返回的用户信息中移除密码字段 (虽然序列化器已设为write_only，但以防万一)
        if 'password' in response_data['user']:
            del response_data['user']['password']
        # ------------------------------------------

        headers = self.get_success_headers(serializer.data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)
    
class UserProfileView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all() # RetrieveUpdateAPIView 需要 queryset
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAuthenticated] # 只有登录用户才能访问

    def get_object(self):
        # 返回当前请求的用户对象
        return self.request.user

    # 如果你希望在更新成功后返回更新后的用户信息，DRF 默认就会这样做
    # 如果需要特殊处理，可以重写 update 方法
    # def update(self, request, *args, **kwargs):
    #     partial = kwargs.pop('partial', False)
    #     instance = self.get_object()
    #     serializer = self.get_serializer(instance, data=request.data, partial=partial)
    #     serializer.is_valid(raise_exception=True)
    #     self.perform_update(serializer)
    #     return Response(serializer.data)