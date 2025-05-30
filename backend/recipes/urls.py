from django.urls import path

from .views import IngredientListView, IngredientDetailView, RecipeListCreateView

urlpatterns = [
    # path('dishes/', views.DishListView.as_view(), name='dish-list'),
    path("ingredients/", IngredientListView.as_view(), name="ingredient-list"),
    path(
        "ingredients/<int:pk>/",
        IngredientDetailView.as_view(),
        name="ingredient-detail",
    ),
    path('recipes/', RecipeListCreateView.as_view(), name='recipe-list-create'),

]
