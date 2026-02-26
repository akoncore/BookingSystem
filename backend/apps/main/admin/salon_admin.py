# apps/main/admin.py - MasterJobRequest қосылды
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from apps.main.models import Salon


# ─── Salon ───────────────────────────────────────────────────────────────────

@admin.register(Salon)
class SalonAdmin(admin.ModelAdmin):
    list_display = [
        'name', 
        'salon_code', 
        'owner_link', 
        'phone', 
        'is_active', 
        'masters_count', 
        'services_count', 
        'created_at'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = [
        'name', 
        'salon_code', 
        'address', 
        'owner__full_name', 
        'owner__email'
    ]
    readonly_fields = [
        'salon_code', 
        'created_at', 
        'updated_at', 
        'masters_count', 
        'services_count'
    ]

    fieldsets = (
        ('Basic Information', {'fields': ('name', 'salon_code', 'owner', 'is_active')}),
        ('Contact Information', {'fields': ('address', 'phone', 'description')}),
        ('Statistics', {'fields': ('masters_count', 'services_count'), 'classes': ('collapse',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    list_per_page = 25
    date_hierarchy = 'created_at'

    def owner_link(self, obj):
        if obj.owner:
            url = reverse('admin:auths_customuser_change', args=[obj.owner.pk])
            return format_html('<a href="{}">{}</a>', url, obj.owner.full_name)
        return '-'
    owner_link.short_description = 'Owner'

    def masters_count(self, obj):
        count = obj.masters.filter(is_approved=True).count()
        return format_html('<b>{}</b>', count)
    masters_count.short_description = 'Approved Masters'

    def services_count(self, obj):
        count = obj.services.filter(is_active=True).count()
        return format_html('<b>{}</b>', count)
    services_count.short_description = 'Active Services'

