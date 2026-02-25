from django.urls import path, include
from rest_framework.routers import DefaultRouter   
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
) 


#Project models
from .views import (
    UserViewSet,
    AuthViewSet,
)

router = DefaultRouter()
router.register(r'users',UserViewSet,basename='users')
router.register(r'auth',AuthViewSet,basename='auth')


urlpatterns = [
    path('',include(router.urls)),
    path('token/',TokenObtainPairView.as_view(),name='token_obtain_pair'),
    path('token/refresh/',TokenRefreshView.as_view(),name='token_refresh'),
    path('token/verify/',TokenVerifyView.as_view(),name='token_verify'),

]

