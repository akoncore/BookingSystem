from django.urls import path,include
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from .views import (
    MasterViewSet
)

router = DefaultRouter()
router.register('master',MasterViewSet,basename='master')

urlpatterns = [
    path('', include(router.urls)),
]