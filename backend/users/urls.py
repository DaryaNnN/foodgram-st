from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, subscribe, SubscriptionView

router = DefaultRouter()
router.register('users', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('users/<int:id>/subscribe/', subscribe, name='subscribe'),
    path('users/subscriptions/', SubscriptionView.as_view(), name='subscriptions'),
]
