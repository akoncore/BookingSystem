
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from apps.main.models import  Booking



# ─── Booking ──────────────────────────────────────────────────────────────────

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        'booking_code', 'client_link', 'master_link', 'salon_link',
        'appointment_datetime', 'status_badge', 'total_price_formatted', 'created_at'
    ]
    list_filter = ['status', 'appointment_date', 'salon', 'created_at']
    search_fields = ['booking_code', 'client__full_name', 'master__full_name', 'salon__name']
    readonly_fields = ['booking_code', 'total_price', 'created_at', 'updated_at']
    filter_horizontal = ['services']
    list_per_page = 25
    date_hierarchy = 'appointment_date'
    actions = ['confirm_bookings', 'complete_bookings', 'cancel_bookings']

    def client_link(self, obj):
        url = reverse('admin:auths_customuser_change', args=[obj.client.pk])
        return format_html('<a href="{}">{}</a>', url, obj.client.full_name)
    client_link.short_description = 'Client'

    def master_link(self, obj):
        url = reverse('admin:auths_customuser_change', args=[obj.master.pk])
        return format_html('<a href="{}">{}</a>', url, obj.master.full_name)
    master_link.short_description = 'Master'

    def salon_link(self, obj):
        url = reverse('admin:main_salon_change', args=[obj.salon.pk])
        return format_html('<a href="{}">{}</a>', url, obj.salon.name)
    salon_link.short_description = 'Salon'

    def appointment_datetime(self, obj):
        return format_html(
            '<b>{}</b><br/><small>{}</small>',
            obj.appointment_date.strftime('%Y-%m-%d'),
            obj.appointment_time.strftime('%H:%M')
        )
    appointment_datetime.short_description = 'Date & Time'

    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107', 'confirmed': '#17a2b8',
            'completed': '#28a745', 'cancelled': '#dc3545'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background:{};color:white;padding:3px 10px;'
            'border-radius:3px;font-weight:bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def total_price_formatted(self, obj):
        return format_html('<b>{:,.0f}</b> KZT', obj.total_price)
    total_price_formatted.short_description = 'Total Price'

    def confirm_bookings(self, request, queryset):
        updated = queryset.update(status='confirmed')
        self.message_user(request, f'{updated} booking(s) confirmed.')
    confirm_bookings.short_description = 'Confirm selected'

    def complete_bookings(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} booking(s) completed.')
    complete_bookings.short_description = 'Mark as completed'

    def cancel_bookings(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} booking(s) cancelled.')
    cancel_bookings.short_description = 'Cancel selected'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.pk:
            obj.calculate_total_price()
            obj.save()

