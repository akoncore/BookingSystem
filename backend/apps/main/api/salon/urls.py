from django.urls import path,include
from rest_framework.routers import DefaultRouter

from apps.main.api.salon.view import SalonViewSet

router = DefaultRouter()

router.register(r'salon',SalonViewSet,basename='salon')

urlpatterns = [
    path('',include(router.urls))
]