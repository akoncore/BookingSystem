# apps/main/filters.py
"""
Filters for Salon, Master, Service, Booking, WorkSchedule
Uses django-filter for clean, reusable query-string filtering.
"""

import django_filters
from django_filters import rest_framework as filters
from django.db.models import Q

from .models import Salon, Master, Service, Booking, WorkSchedule


# ─── Salon Filter ─────────────────────────────────────────────────────────────

class SalonFilter(filters.FilterSet):
    """
    GET /api/v2/salon/?name=Elite&city=Almaty&is_active=true&owner_id=5
    """
    name        = filters.CharFilter(lookup_expr="icontains")
    address     = filters.CharFilter(lookup_expr="icontains")
    city        = filters.CharFilter(field_name="address", lookup_expr="icontains")
    owner_id    = filters.NumberFilter(field_name="owner__id")
    owner_name  = filters.CharFilter(field_name="owner__full_name", lookup_expr="icontains")
    is_active   = filters.BooleanFilter()

    # Date range
    created_after  = filters.DateFilter(field_name="created_at__date", lookup_expr="gte")
    created_before = filters.DateFilter(field_name="created_at__date", lookup_expr="lte")

    # Has active masters
    has_masters = filters.BooleanFilter(method="filter_has_masters")

    class Meta:
        model  = Salon
        fields = ["name", "address", "is_active", "owner_id"]

    def filter_has_masters(self, queryset, name, value):
        if value:
            return queryset.filter(masters__is_approved=True).distinct()
        return queryset.exclude(masters__is_approved=True).distinct()


# ─── Master Filter ────────────────────────────────────────────────────────────

class MasterFilter(filters.FilterSet):
    """
    GET /api/v2/master/?salon_id=1&specialization=Hair&min_exp=2&is_approved=true
    """
    salon_id        = filters.NumberFilter(field_name="salon__id")
    salon_name      = filters.CharFilter(field_name="salon__name", lookup_expr="icontains")
    specialization  = filters.CharFilter(lookup_expr="icontains")
    min_experience  = filters.NumberFilter(field_name="experience_years", lookup_expr="gte")
    max_experience  = filters.NumberFilter(field_name="experience_years", lookup_expr="lte")
    is_approved     = filters.BooleanFilter()
    name            = filters.CharFilter(field_name="user__full_name", lookup_expr="icontains")

    # Search across name + specialization
    search = filters.CharFilter(method="filter_search")

    class Meta:
        model  = Master
        fields = ["salon_id", "specialization", "is_approved"]

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(user__full_name__icontains=value) |
            Q(specialization__icontains=value) |
            Q(bio__icontains=value)
        )


# ─── Service Filter ───────────────────────────────────────────────────────────

class ServiceFilter(filters.FilterSet):
    """
    GET /api/v2/service/?salon_id=1&min_price=1000&max_price=5000&name=Cut
    """
    salon_id    = filters.NumberFilter(field_name="salon__id")
    name        = filters.CharFilter(lookup_expr="icontains")
    is_active   = filters.BooleanFilter()
    min_price   = filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price   = filters.NumberFilter(field_name="price", lookup_expr="lte")

    # Duration in minutes
    min_duration_min = filters.NumberFilter(method="filter_min_duration")
    max_duration_min = filters.NumberFilter(method="filter_max_duration")

    class Meta:
        model  = Service
        fields = ["salon_id", "name", "is_active"]

    def filter_min_duration(self, queryset, name, value):
        from datetime import timedelta
        return queryset.filter(duration__gte=timedelta(minutes=value))

    def filter_max_duration(self, queryset, name, value):
        from datetime import timedelta
        return queryset.filter(duration__lte=timedelta(minutes=value))


# ─── Booking Filter ───────────────────────────────────────────────────────────

class BookingFilter(filters.FilterSet):
    """
    GET /api/v2/booking/?status=pending&date_from=2026-01-01&salon_id=1&master_id=3
    """
    status       = filters.ChoiceFilter(choices=Booking.STATUS_CHOICES)
    salon_id     = filters.NumberFilter(field_name="salon__id")
    master_id    = filters.NumberFilter(field_name="master__id")
    client_id    = filters.NumberFilter(field_name="client__id")

    # Date range
    date_from    = filters.DateFilter(field_name="appointment_date", lookup_expr="gte")
    date_to      = filters.DateFilter(field_name="appointment_date", lookup_expr="lte")
    date         = filters.DateFilter(field_name="appointment_date")

    # Time range
    time_from    = filters.TimeFilter(field_name="appointment_time", lookup_expr="gte")
    time_to      = filters.TimeFilter(field_name="appointment_time", lookup_expr="lte")

    # Price range
    min_price    = filters.NumberFilter(field_name="total_price", lookup_expr="gte")
    max_price    = filters.NumberFilter(field_name="total_price", lookup_expr="lte")

    # Search by booking code or client name
    search       = filters.CharFilter(method="filter_search")

    # Ordering
    ordering     = filters.OrderingFilter(
        fields=(
            ("appointment_date", "date"),
            ("appointment_time", "time"),
            ("total_price",      "price"),
            ("created_at",       "created"),
            ("status",           "status"),
        )
    )

    class Meta:
        model  = Booking
        fields = ["status", "salon_id", "master_id", "client_id"]

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(booking_code__icontains=value) |
            Q(client__full_name__icontains=value) |
            Q(master__full_name__icontains=value)
        )


# ─── WorkSchedule Filter ─────────────────────────────────────────────────────

class WorkScheduleFilter(filters.FilterSet):
    """
    GET /api/v2/work-schedule/?master_id=3&weekday=1&is_working=true
    """
    master_id  = filters.NumberFilter(field_name="master__id")
    weekday    = filters.NumberFilter()
    is_working = filters.BooleanFilter()

    class Meta:
        model  = WorkSchedule
        fields = ["master_id", "weekday", "is_working"]