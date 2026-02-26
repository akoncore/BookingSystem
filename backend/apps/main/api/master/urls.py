from django.urls import path,include
from rest_framework.routers import DefaultRouter

from apps.main.api.master.view import MasterViewSet

router = DefaultRouter()

router.register(r'master',MasterViewSet,basename='master')

urlpatterns = [
    path('',include(router.urls))
]