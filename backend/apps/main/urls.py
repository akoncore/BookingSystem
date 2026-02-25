from django.urls import path, include



urlpatterns = [
    path('salon/', include('main.api.salon.urls')),
    path('booking/', include('main.api.booking.urls')),
    path('master/', include('main.api.master.urls')),
    path('service/', include('main.api.service.urls')),
    path('booking/', include('main.api.booking.urls')),
    path('admin_view/', include('main.api.admin_view.urls')),
    path('work-schedule/', include('main.api.work_schedule.urls')),
]