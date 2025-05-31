from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, subscribe, SubscriptionView

router = DefaultRouter()
router.register("users", UserViewSet, basename="users")

users_custom_patterns = [
    path('subscriptions/', SubscriptionView.as_view(), name='subscriptions'),
    path('<int:id>/subscribe/', subscribe, name='subscribe'),
]

urlpatterns = [
    path("", include(router.urls)),
    path("users/", include(users_custom_patterns)),  # <--- Важно
]

