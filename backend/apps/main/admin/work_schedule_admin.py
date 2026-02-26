from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from apps.main.models import WorkSchedule

# ─── WorkSchedule ─────────────────────────────────────────────────────────────

@admin.register(WorkSchedule)
class WorkScheduleAdmin(admin.ModelAdmin):
    list_display = ['master_link', 'weekday_display', 'time_range', 'is_working_badge']
    list_filter = ['weekday', 'is_working', 'master']
    search_fields = ['master__full_name', 'master__email']

    def master_link(self, obj):
        url = reverse('admin:auths_customuser_change', args=[obj.master.pk])
        return format_html('<a href="{}">{}</a>', url, obj.master.full_name)
    master_link.short_description = 'Master'

    def weekday_display(self, obj):
        return obj.get_weekday_display()
    weekday_display.short_description = 'Day'

    def time_range(self, obj):
        if obj.is_working:
            return format_html('{} — {}', obj.start_time.strftime('%H:%M'), obj.end_time.strftime('%H:%M'))
        return mark_safe('<i style="color:#999">Day off</i>')
    time_range.short_description = 'Working Hours'

    def is_working_badge(self, obj):
        if obj.is_working:
            return mark_safe('<span style="color:#28a745">✓ Working</span>')
        return mark_safe('<span style="color:#dc3545">✗ Day Off</span>')
    is_working_badge.short_description = 'Status'


