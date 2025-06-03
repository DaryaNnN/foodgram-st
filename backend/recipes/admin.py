from django.contrib import admin
from .models import Recipe, Ingredient, RecipeIngredient, Favorite, ShoppingList


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "measurement_unit")
    search_fields = ("name",)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("name", "author", "cooking_time", "pub_date")
    search_fields = ("name", "author__email", "author__username")
    list_filter = ("author",)
    inlines = [RecipeIngredientInline]


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ("recipe", "component", "amount")
    search_fields = ("recipe__name", "component__name")


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe")
    search_fields = ("user__email", "recipe__name")


@admin.register(ShoppingList)
class ShoppingListAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe")
    search_fields = ("user__email", "recipe__name")
