from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Salon, Master, Service, Booking, WorkSchedule
from decimal import Decimal


@admin.register(Salon)
class SalonAdmin(admin.ModelAdmin):
    """Admin interface for Salon model"""
    
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
    
    list_filter = [
        'is_active',
        'created_at',
        'owner'
    ]
    
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
        'services_count',
        'bookings_count'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'salon_code', 'owner', 'is_active')
        }),
        ('Contact Information', {
            'fields': ('address', 'phone', 'description')
        }),
        ('Statistics', {
            'fields': ('masters_count', 'services_count', 'bookings_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    def owner_link(self, obj):
        """Link to owner in admin"""
        if obj.owner:
            url = reverse('admin:auths_customuser_change', args=[obj.owner.pk])
            return format_html('<a href="{}">{}</a>', url, obj.owner.full_name)
        return '-'
    owner_link.short_description = 'Owner'
    
    def masters_count(self, obj):
        """Count of masters in salon"""
        count = obj.masters.filter(is_approved=True).count()
        return format_html('<b>{}</b> masters', count)
    masters_count.short_description = 'Masters'
    
    def services_count(self, obj):
        """Count of services in salon"""
        count = obj.services.filter(is_active=True).count()
        return format_html('<b>{}</b> services', count)
    services_count.short_description = 'Services'
    
    def bookings_count(self, obj):
        """Count of bookings in salon"""
        count = obj.bookings.count()
        return format_html('<b>{}</b> bookings', count)
    bookings_count.short_description = 'Total Bookings'


@admin.register(Master)
class MasterAdmin(admin.ModelAdmin):
    """Admin interface for Master model"""
    
    list_display = [
        'user_link',
        'salon_link',
        'specialization',
        'experience_years',
        'is_approved',
        'appointments_count',
        'created_at'
    ]
    
    list_filter = [
        'is_approved',
        'salon',
        'experience_years',
        'created_at'
    ]
    
    search_fields = [
        'user__full_name',
        'user__email',
        'salon__name',
        'specialization'
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'appointments_count',
        'completed_appointments'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'salon', 'is_approved')
        }),
        ('Professional Details', {
            'fields': ('specialization', 'experience_years', 'bio')
        }),
        ('Statistics', {
            'fields': ('appointments_count', 'completed_appointments'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    actions = ['approve_masters', 'disapprove_masters']
    
    def user_link(self, obj):
        """Link to user in admin"""
        url = reverse('admin:auths_customuser_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.full_name)
    user_link.short_description = 'Master'
    
    def salon_link(self, obj):
        """Link to salon in admin"""
        url = reverse('admin:main_salon_change', args=[obj.salon.pk])
        return format_html('<a href="{}">{}</a>', url, obj.salon.name)
    salon_link.short_description = 'Salon'
    
    def appointments_count(self, obj):
        """Total appointments count"""
        count = obj.user.master_appointments.count()
        return format_html('<b>{}</b> appointments', count)
    appointments_count.short_description = 'Total Appointments'
    
    def completed_appointments(self, obj):
        """Completed appointments count"""
        count = obj.user.master_appointments.filter(status='completed').count()
        return format_html('<b>{}</b> completed', count)
    completed_appointments.short_description = 'Completed'
    
    def approve_masters(self, request, queryset):
        """Bulk approve masters"""
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} master(s) approved successfully.')
    approve_masters.short_description = 'Approve selected masters'
    
    def disapprove_masters(self, request, queryset):
        """Bulk disapprove masters"""
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} master(s) disapproved.')
    disapprove_masters.short_description = 'Disapprove selected masters'


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """Admin interface for Service model"""
    
    list_display = [
        'name',
        'salon_link',
        'price_formatted',
        'duration',
        'is_active',
        'bookings_count',
        'created_at'
    ]
    
    list_filter = [
        'is_active',
        'salon',
        'created_at'
    ]
    
    search_fields = [
        'name',
        'description',
        'salon__name'
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'bookings_count'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'salon', 'is_active')
        }),
        ('Service Details', {
            'fields': ('description', 'price', 'duration')
        }),
        ('Statistics', {
            'fields': ('bookings_count',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    actions = ['activate_services', 'deactivate_services']
    
    def salon_link(self, obj):
        """Link to salon in admin"""
        url = reverse('admin:main_salon_change', args=[obj.salon.pk])
        return format_html('<a href="{}">{}</a>', url, obj.salon.name)
    salon_link.short_description = 'Salon'
    
    def price_formatted(self, obj):
        """Formatted price"""
        formatted_price = f'{obj.price:,.0f}'
        return format_html('<b>{}</b> KZT', formatted_price)
    price_formatted.short_description = 'Price'
    
    def bookings_count(self, obj):
        """Count of bookings using this service"""
        count = obj.bookings.count()
        return format_html('<b>{}</b> bookings', count)
    bookings_count.short_description = 'Bookings'
    
    def activate_services(self, request, queryset):
        """Bulk activate services"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} service(s) activated.')
    activate_services.short_description = 'Activate selected services'
    
    def deactivate_services(self, request, queryset):
        """Bulk deactivate services"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} service(s) deactivated.')
    deactivate_services.short_description = 'Deactivate selected services'


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """Admin interface for Booking model"""
    
    list_display = [
        'booking_code',
        'client_link',
        'master_link',
        'salon_link',
        'appointment_datetime',
        'status_badge',
        'total_price_formatted',
        'created_at'
    ]
    
    list_filter = [
        'status',
        'appointment_date',
        'salon',
        'created_at'
    ]
    
    search_fields = [
        'booking_code',
        'client__full_name',
        'client__email',
        'master__full_name',
        'master__email',
        'salon__name'
    ]
    
    readonly_fields = [
        'booking_code',
        'total_price',
        'created_at',
        'updated_at',
        'services_list'
    ]
    
    filter_horizontal = ['services']
    
    fieldsets = (
        ('Booking Information', {
            'fields': ('booking_code', 'status')
        }),
        ('Participants', {
            'fields': ('client', 'master', 'salon')
        }),
        ('Appointment Details', {
            'fields': ('appointment_date', 'appointment_time', 'services', 'services_list')
        }),
        ('Payment', {
            'fields': ('total_price',)
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    list_per_page = 25
    date_hierarchy = 'appointment_date'
    
    actions = ['confirm_bookings', 'complete_bookings', 'cancel_bookings']
    
    def client_link(self, obj):
        """Link to client in admin"""
        url = reverse('admin:auths_customuser_change', args=[obj.client.pk])
        return format_html('<a href="{}">{}</a>', url, obj.client.full_name)
    client_link.short_description = 'Client'
    
    def master_link(self, obj):
        """Link to master in admin"""
        url = reverse('admin:auths_customuser_change', args=[obj.master.pk])
        return format_html('<a href="{}">{}</a>', url, obj.master.full_name)
    master_link.short_description = 'Master'
    
    def salon_link(self, obj):
        """Link to salon in admin"""
        url = reverse('admin:main_salon_change', args=[obj.salon.pk])
        return format_html('<a href="{}">{}</a>', url, obj.salon.name)
    salon_link.short_description = 'Salon'
    
    def appointment_datetime(self, obj):
        """Combined date and time"""
        return format_html(
            '<b>{}</b><br/><small>{}</small>',
            obj.appointment_date.strftime('%Y-%m-%d'),
            obj.appointment_time.strftime('%H:%M')
        )
    appointment_datetime.short_description = 'Date & Time'
    
    def status_badge(self, obj):
        """Colored status badge"""
        colors = {
            'pending': '#ffc107',
            'confirmed': '#17a2b8',
            'completed': '#28a745',
            'cancelled': '#dc3545'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def total_price_formatted(self, obj):
        """Formatted total price"""
        try:
            price = Decimal(obj.total_price)
        except Exception:
            return '-'
        formatted_price = f'{price:,.0f}'
        return format_html('<b>{}</b> KZT', formatted_price)

    total_price_formatted.short_description = 'Total Price'
    
    def services_list(self, obj):
        """List of services"""
        if obj.pk:
            services = obj.services.all()
            if services:
                items = '<br/>'.join([
                    f'• {s.name} ({Decimal(s.price):,.0f} KZT)'
                    for s in services
                ])
                return mark_safe(items)
        return '-'
    
    def confirm_bookings(self, request, queryset):
        """Bulk confirm bookings"""
        updated = queryset.update(status='confirmed')
        self.message_user(request, f'{updated} booking(s) confirmed.')
    confirm_bookings.short_description = 'Confirm selected bookings'
    
    def complete_bookings(self, request, queryset):
        """Bulk complete bookings"""
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} booking(s) marked as completed.')
    complete_bookings.short_description = 'Mark as completed'
    
    def cancel_bookings(self, request, queryset):
        """Bulk cancel bookings"""
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} booking(s) cancelled.')
    cancel_bookings.short_description = 'Cancel selected bookings'
    
    def save_model(self, request, obj, form, change):
        """Override to calculate total price after saving"""
        super().save_model(request, obj, form, change)
        if obj.pk:
            obj.calculate_total_price()
            obj.save()


@admin.register(WorkSchedule)
class WorkScheduleAdmin(admin.ModelAdmin):
    """Admin interface for WorkSchedule model"""
    
    list_display = [
        'master_link',
        'weekday_display',
        'time_range',
        'is_working_badge',
    ]
    
    list_filter = [
        'weekday',
        'is_working',
        'master'
    ]
    
    search_fields = [
        'master__full_name',
        'master__email'
    ]
    
    fieldsets = (
        ('Schedule Information', {
            'fields': ('master', 'weekday', 'is_working')
        }),
        ('Working Hours', {
            'fields': ('start_time', 'end_time')
        }),
    )
    
    list_per_page = 50
    
    def master_link(self, obj):
        """Link to master in admin"""
        url = reverse('admin:auths_customuser_change', args=[obj.master.pk])
        return format_html('<a href="{}">{}</a>', url, obj.master.full_name)
    master_link.short_description = 'Master'
    
    def weekday_display(self, obj):
        """Display weekday name"""
        return obj.get_weekday_display()
    weekday_display.short_description = 'Day'
    
    def time_range(self, obj):
        """Display time range"""
        if obj.is_working:
            return format_html(
                '<b>{}</b> - <b>{}</b>',
                obj.start_time.strftime('%H:%M'),
                obj.end_time.strftime('%H:%M')
            )
        return mark_safe('<i style="color: #999;">Day off</i>')
    time_range.short_description = 'Working Hours'
    
    def is_working_badge(self, obj):
        """Working status badge"""
        if obj.is_working:
            return mark_safe('<span style="color: #28a745;">✓ Working</span>')
        return mark_safe('<span style="color: #dc3545;">✗ Day Off</span>')
    is_working_badge.short_description = 'Status'


# Customize admin site header and title
admin.site.site_header = 'Salon Management System'
admin.site.site_title = 'Salon Admin'
admin.site.index_title = 'Welcome to Salon Management System'