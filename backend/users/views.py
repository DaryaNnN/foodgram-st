from rest_framework import viewsets, status, generics, mixins, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from .models import Subscription
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserDetailSerializer,
    AvatarSerializer,
    SetPasswordSerializer,
    SubscriptionSerializer,
)
from rest_framework.permissions import IsAuthenticated

User = get_user_model()


from rest_framework import status
from rest_framework.response import Response

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['retrieve', 'me']:
            return UserDetailSerializer
        return UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        response_serializer = UserSerializer(user)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'delete'], permission_classes=[IsAuthenticated], url_path='me/avatar')
    def avatar(self, request):
        if request.method == 'PUT':
            serializer = AvatarSerializer(request.user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        elif request.method == 'DELETE':
            user = request.user
            user.avatar.delete()
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated], url_path='set_password')
    def set_password(self, request):
        serializer = SetPasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)



class SubscriptionView(generics.ListAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(subscribers__subscriber=self.request.user)


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def subscribe(request, id):
    author = get_object_or_404(User, id=id)
    user = request.user

    if request.method == 'POST':
        if author == user:
            return Response({'error': 'Нельзя подписаться на самого себя.'}, status=status.HTTP_400_BAD_REQUEST)
        if Subscription.objects.filter(subscriber=user, author=author).exists():
            return Response({'error': 'Вы уже подписаны.'}, status=status.HTTP_400_BAD_REQUEST)
        subscription = Subscription.objects.create(subscriber=user, author=author)
        serializer = SubscriptionSerializer(author, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    elif request.method == 'DELETE':
        subscription = Subscription.objects.filter(subscriber=user, author=author).first()
        if not subscription:
            return Response({'error': 'Вы не подписаны.'}, status=status.HTTP_400_BAD_REQUEST)
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
