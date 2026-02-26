# apps/main/admin.py - MasterJobRequest қосылды
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from apps.main.models import Service



# ─── Service ──────────────────────────────────────────────────────────────────

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = [
        'name', 
        'salon_link', 
        'price_formatted', 
        'duration', 
        'is_active', 
        'created_at'
    ]
    list_filter = ['is_active', 'salon', 'created_at']
    search_fields = ['name', 'salon__name']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['activate_services', 'deactivate_services']

    def salon_link(self, obj):
        url = reverse('admin:main_salon_change', args=[obj.salon.pk])
        return format_html('<a href="{}">{}</a>', url, obj.salon.name)
    salon_link.short_description = 'Salon'

    def price_formatted(self, obj):
        return format_html('<b>{:,.0f}</b> KZT', obj.price)
    price_formatted.short_description = 'Price'

    def activate_services(self, request, queryset):
        queryset.update(is_active=True)
    activate_services.short_description = 'Activate selected'

    def deactivate_services(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_services.short_description = 'Deactivate selected'

