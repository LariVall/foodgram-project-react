from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as AuthUserAdmin

from users.models import User, UserSubscription


@admin.register(User)
class CustomUserAdmin(AuthUserAdmin):
    list_display = (
        'first_name',
        'last_name',
        'username',
        'email',
        'password',
    )
    list_filter = (
        'username',
        'email',
    )
    search_fields = (
        'first_name',
        'last_name',
        'username',
        'email',
    )


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    list_filter = ('user', 'author')
    search_fields = ('user__username', 'author__username')
