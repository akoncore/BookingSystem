from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.main.api.admin_view.view import AdminViewSet

router = DefaultRouter()

# register with a simple prefix; endpoints are defined via @action
router.register(r'admin', AdminViewSet, basename='admin')

urlpatterns = [
    path('', include(router.urls)),
]
