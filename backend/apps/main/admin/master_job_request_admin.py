# apps/main/admin.py - MasterJobRequest қосылды
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils import timezone
from decimal import Decimal

from apps.main.models import Master, MasterJobRequest
from apps.services.notifications import NotificationService


# ─── MasterJobRequest ─────────────────────────────────────────────────────────

@admin.register(MasterJobRequest)
class MasterJobRequestAdmin(admin.ModelAdmin):
    list_display = [
        'master_name', 'salon_link', 'specialization',
        'experience_years', 'expected_salary_formatted',
        'status_badge', 'reviewed_by_name', 'created_at'
    ]
    list_filter = ['status', 'salon', 'created_at']
    search_fields = [
        'master__full_name', 
        'master__email', 
        'salon__name', 
        'specialization'
    ]
    readonly_fields = [
        'master', 'salon', 'created_at', 'updated_at',
        'reviewed_at', 'reviewed_by',
        'offered_services_formatted', 'answers_formatted'
    ]
    list_per_page = 25
    date_hierarchy = 'created_at'
    actions = ['approve_requests', 'reject_requests']

    fieldsets = (
        ('Request Info', {'fields': ('master', 'salon', 'status')}),
        ('Resume', {
            'fields': (
                'specialization', 'experience_years', 'bio',
                'offered_services', 'offered_services_formatted',
                'expected_salary',
            )
        }),
        ('Salon Q&A', {'fields': ('answers', 'answers_formatted'), 'classes': ('collapse',)}),
        ('Review', {'fields': ('rejection_reason', 'reviewed_by', 'reviewed_at')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def master_name(self, obj):
        url = reverse('admin:auths_customuser_change', args=[obj.master.pk])
        return format_html('<a href="{}">{}</a>', url, obj.master.full_name)
    master_name.short_description = 'Master'

    def salon_link(self, obj):
        url = reverse('admin:main_salon_change', args=[obj.salon.pk])
        return format_html('<a href="{}">{}</a>', url, obj.salon.name)
    salon_link.short_description = 'Salon'

    def expected_salary_formatted(self, obj):
        if obj.expected_salary:
            return format_html('{:,.0f} KZT/mo', obj.expected_salary)
        return '—'
    expected_salary_formatted.short_description = 'Expected Salary'

    def status_badge(self, obj):
        colors = {'pending': '#ffc107', 'approved': '#28a745', 'rejected': '#dc3545'}
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background:{}; color:white; padding:3px 10px; '
            'border-radius:3px; font-weight:bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def reviewed_by_name(self, obj):
        return obj.reviewed_by.full_name if obj.reviewed_by else '—'
    reviewed_by_name.short_description = 'Reviewed By'

    def offered_services_formatted(self, obj):
        services = obj.get_offered_services_list()
        if services:
            items = ''.join([f'<li>{s}</li>' for s in services])
            return mark_safe(f'<ul style="margin:0;padding-left:15px">{items}</ul>')
        return '—'
    offered_services_formatted.short_description = 'Services (parsed)'

    def answers_formatted(self, obj):
        if obj.answers:
            rows = ''.join([
                f'<tr><td style="padding:4px 8px;font-weight:bold">{k}</td>'
                f'<td style="padding:4px 8px">{v}</td></tr>'
                for k, v in obj.answers.items()
            ])
            return mark_safe(
                f'<table style="border-collapse:collapse">{rows}</table>'
            )
        return '—'
    answers_formatted.short_description = 'Q&A (formatted)'

    def approve_requests(self, request, queryset):
        """Bulk approve — creates Master profiles"""
        approved = 0
        for job_request in queryset.filter(status='pending'):
            job_request.status = 'approved'
            job_request.reviewed_by = request.user
            job_request.reviewed_at = timezone.now()
            job_request.save()

            Master.objects.update_or_create(
                user=job_request.master,
                defaults={
                    'salon': job_request.salon,
                    'specialization': job_request.specialization,
                    'experience_years': job_request.experience_years,
                    'bio': job_request.bio,
                    'is_approved': True,
                }
            )
            NotificationService.send_job_request_approved(job_request)
            approved += 1

        self.message_user(request, f'{approved} request(s) approved and masters created.')
    approve_requests.short_description = '✅ Approve selected requests'

    def reject_requests(self, request, queryset):
        rejected = queryset.filter(status='pending').update(
            status='rejected',
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
            rejection_reason='Bulk rejected via admin'
        )
        self.message_user(request, f'{rejected} request(s) rejected.')
    reject_requests.short_description = '❌ Reject selected requests'

