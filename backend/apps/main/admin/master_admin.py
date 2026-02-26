# apps/main/admin.py - MasterJobRequest қосылды
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from apps.main.models import Master



# ─── Master ───────────────────────────────────────────────────────────────────

@admin.register(Master)
class MasterAdmin(admin.ModelAdmin):
    list_display = [
        'user_link', 
        'salon_link', 
        'specialization', 
        'experience_years', 
        'is_approved', 
        'created_at'
    ]
    list_filter = ['is_approved', 'salon', 'created_at']
    search_fields = ['user__full_name', 'user__email', 'salon__name', 'specialization']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['approve_masters', 'disapprove_masters']

    def user_link(self, obj):
        url = reverse('admin:auths_customuser_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.full_name)
    user_link.short_description = 'Master'

    def salon_link(self, obj):
        url = reverse('admin:main_salon_change', args=[obj.salon.pk])
        return format_html('<a href="{}">{}</a>', url, obj.salon.name)
    salon_link.short_description = 'Salon'

    def approve_masters(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} master(s) approved.')
    approve_masters.short_description = 'Approve selected masters'

    def disapprove_masters(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} master(s) disapproved.')
    disapprove_masters.short_description = 'Disapprove selected masters'

