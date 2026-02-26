from django.urls import path,include
from rest_framework.routers import DefaultRouter

from apps.main.api.booking.view import BookingViewSet

router = DefaultRouter()

router.register(r'booking',BookingViewSet,basename='booking')

urlpatterns = [
    path('',include(router.urls))
]