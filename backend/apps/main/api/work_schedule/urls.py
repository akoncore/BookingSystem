from django.urls import path,include
from rest_framework.routers import DefaultRouter

from main.api.work_schedule.view import WorkScheduleViewSet

router = DefaultRouter()

router.register(r'work-schedule',WorkScheduleViewSet,basename='work-schedule')

urlpatterns = [
    path('',include(router.urls))
]