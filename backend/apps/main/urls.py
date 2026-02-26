
from django.urls import path, include

urlpatterns = [
    path('salon/', include('apps.main.api.salon.urls')),
    path('booking/', include('apps.main.api.booking.urls')),
    path('master/', include('apps.main.api.master.urls')),
    path('service/', include('apps.main.api.service.urls')),
    path('admin_view/', include('apps.main.api.admin_view.urls')),
    path('work-schedule/', include('apps.main.api.work_schedule.urls')),
    path('analytics', include('apps.main.api.analytics.urls')),
    path('payment', include('apps.main.api.payment.urls'))
]