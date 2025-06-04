from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, permissions, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import serializers

from users.models import Subscription, User
from users.serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserDetailSerializer,
    AvatarSerializer,
    SetPasswordSerializer,
    SubscriptionAuthorSerializer, UserShortSerializer,
)

User = get_user_model()


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ("subscriber", "author")

    def validate(self, data):
        if data["subscriber"] == data["author"]:
            raise serializers.ValidationError("Нельзя подписаться на самого себя.")
        if Subscription.objects.filter(
            subscriber=data["subscriber"], author=data["author"]
        ).exists():
            raise serializers.ValidationError("Вы уже подписаны на этого пользователя.")
        return data


class SubscriptionPagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = "limit"
    max_page_size = 1000


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        elif self.action in ["retrieve", "me", "list"]:
            return UserDetailSerializer
        return UserSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        recipes_limit = self.request.query_params.get("recipes_limit")
        if recipes_limit and recipes_limit.isdigit():
            context["recipes_limit"] = int(recipes_limit)
        else:
            context["recipes_limit"] = None
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        response_serializer = UserShortSerializer(
            user, context=self.get_serializer_context()
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=True, methods=["post", "delete"], permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, pk=None):
        author = get_object_or_404(User, pk=pk)
        user = request.user

        if request.method == "POST":
            serializer = SubscriptionCreateSerializer(
                data={"subscriber": user.id, "author": author.id}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

            serializer_response = SubscriptionAuthorSerializer(
                author, context=self.get_serializer_context()
            )
            return Response(serializer_response.data, status=status.HTTP_201_CREATED)

        elif request.method == "DELETE":
            subscription = Subscription.objects.filter(
                subscriber=user, author=author
            ).first()
            if not subscription:
                return Response(
                    {"error": "Вы не подписаны на этого пользователя."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        user = request.user
        queryset = User.objects.filter(subscribers__subscriber=user)
        paginator = SubscriptionPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = SubscriptionAuthorSerializer(
            page, many=True, context=self.get_serializer_context()
        )
        return paginator.get_paginated_response(serializer.data)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = UserDetailSerializer(
            request.user, context=self.get_serializer_context()
        )
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["put", "delete"],
        permission_classes=[IsAuthenticated],
        url_path="me/avatar",
    )
    def avatar(self, request):
        if request.method == "PUT":
            serializer = AvatarSerializer(
                request.user, data=request.data, context=self.get_serializer_context()
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        elif request.method == "DELETE":
            user = request.user
            user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="set_password",
    )
    def set_password(self, request):
        serializer = SetPasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SubscriptionAuthorSerializer
    pagination_class = SubscriptionPagination

    def get_queryset(self):
        return User.objects.filter(subscribers__subscriber=self.request.user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        recipes_limit = self.request.query_params.get("recipes_limit")
        if recipes_limit is not None and recipes_limit.isdigit():
            context["recipes_limit"] = int(recipes_limit)
        else:
            context["recipes_limit"] = None
        return context


@api_view(["POST", "DELETE"])
@permission_classes([IsAuthenticated])
def subscribe(request, id):
    author = get_object_or_404(User, id=id)
    user = request.user

    if request.method == "POST":
        serializer = SubscriptionCreateSerializer(
            data={"subscriber": user.id, "author": author.id}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        serializer_response = SubscriptionAuthorSerializer(
            author,
            context={
                "request": request,
                "recipes_limit": request.query_params.get("recipes_limit"),
            },
        )
        return Response(serializer_response.data, status=status.HTTP_201_CREATED)

    elif request.method == "DELETE":
        subscription = Subscription.objects.filter(
            subscriber=user, author=author
        ).first()
        if not subscription:
            return Response(
                {"error": "Вы не подписаны на этого пользователя."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
