# users/api_views.py (最终版)

from rest_framework import generics, status, permissions, viewsets
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import action
from .models import User, UserInventoryItem, ShoppingListItem
from .api_serializers import (
    UserRegistrationSerializer, 
    UserDetailSerializer,
    UserInventoryItemSerializer,
    ShoppingListItemSerializer
)

class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        response_data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserRegistrationSerializer(user, context=self.get_serializer_context()).data
        }
        if 'password' in response_data['user']:
            del response_data['user']['password']
        headers = self.get_success_headers(serializer.data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)

class UserProfileView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

class UserInventoryViewSet(viewsets.ModelViewSet):
    serializer_class = UserInventoryItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserInventoryItem.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ShoppingListItemViewSet(viewsets.ModelViewSet):
    serializer_class = ShoppingListItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = ShoppingListItem.objects.filter(user=user)
        is_purchased_str = self.request.query_params.get('is_purchased')
        if is_purchased_str is not None:
            is_purchased = is_purchased_str.lower() in ['true', '1', 't']
            queryset = queryset.filter(is_purchased=is_purchased)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['delete'], permission_classes=[permissions.IsAuthenticated])
    def clear_purchased(self, request):
        """清空当前用户购物清单中所有已购买的项目。"""
        user = request.user
        deleted_count, _ = ShoppingListItem.objects.filter(user=user, is_purchased=True).delete()
        if deleted_count > 0:
            return Response({'detail': f'成功清空 {deleted_count} 项已购买的商品。'}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({'detail': '没有已购买的商品可以清空。'}, status=status.HTTP_200_OK)