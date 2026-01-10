#Django Models
from django.contrib.admin import (
    ModelAdmin,
    register,
) 

#Project Models
from auths.models import CustomUser

@register(CustomUser)
class CustomUserAdmin(ModelAdmin):
    list_display = (
        'email',
        'full_name',
        'is_staff',
        'is_active',
        'is_superuser',
    )
    search_fields = ('email','full_name')
    ordering = ('email',)
    list_filter = ('is_superuser',)
    list_display_links = ('email','full_name')

