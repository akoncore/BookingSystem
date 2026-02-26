from django.urls import path,include
from rest_framework.routers import DefaultRouter

from apps.main.api.payment.view import PaymentViewSet

router = DefaultRouter()

router.register(r'payment',PaymentViewSet,basename='payment')

urlpatterns = [
    path('',include(router.urls))
]