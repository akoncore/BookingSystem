# apps/main/urls.py - COMPLETE VERSION

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    MasterViewSet,
    SalonViewSet,
    ServiceViewSet,
    BookingViewSet,
    WorkScheduleViewSet,
    AnalyticsViewSet,      
    PaymentViewSet,        
)

router = DefaultRouter()

# Негізгі endpoints
router.register('master', MasterViewSet, basename='master')
router.register('salon', SalonViewSet, basename='salon')
router.register('service', ServiceViewSet, basename='service')
router.register('booking', BookingViewSet, basename='booking')
router.register('work-schedule', WorkScheduleViewSet, basename='work-schedule')

# ✨ ЖАҢА: Analytics endpoints
router.register('analytics', AnalyticsViewSet, basename='analytics')

# ✨ ЖАҢА: Payment endpoints
router.register('payments', PaymentViewSet, basename='payments')

urlpatterns = [
    path('', include(router.urls)),
]