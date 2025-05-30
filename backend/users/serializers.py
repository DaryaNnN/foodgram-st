from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password')

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)  # Хэшируем пароль
        user.save()
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email')
        read_only_fields = ('id', 'username', 'first_name', 'last_name', 'email')


from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from users.models import Subscription

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для пользователя (без пароля)"""

    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name", "email")



class UserDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детального просмотра пользователя"""

    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name", "email", "avatar")


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для изменения аватара"""

    class Meta:
        model = User
        fields = ("avatar",)

    def update(self, instance, validated_data):
        instance.avatar = validated_data.get("avatar", instance.avatar)
        instance.save()
        return instance


class SetPasswordSerializer(serializers.Serializer):
    """Сериализатор для изменения пароля"""

    new_password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    def validate_new_password(self, value):
        validate_password(value)
        return value


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок"""

    subscriber = UserSerializer(read_only=True)
    author = UserSerializer(read_only=True)

    class Meta:
        model = Subscription
        fields = ("id", "subscriber", "author")
