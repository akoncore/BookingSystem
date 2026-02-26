from django.urls import path,include
from rest_framework.routers import DefaultRouter

from apps.main.api.analytics.view import AnalyticsViewSet

router = DefaultRouter()

router.register(r'analytics',AnalyticsViewSet,basename='analytics')

urlpatterns = [
    path('',include(router.urls))
]