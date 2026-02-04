from django.urls import path,include
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from .views import (
    MasterViewSet,
    SalonViewSet
)

router = DefaultRouter()
router.register('master',MasterViewSet,basename='master')
router.register('salon',SalonViewSet,basename='salon')


urlpatterns = [
    path('', include(router.urls)),
]