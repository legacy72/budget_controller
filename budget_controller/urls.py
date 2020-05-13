from django.urls import path
from django.contrib import admin
from django.conf.urls import include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from core.urls import router as core_router
from core.views import registration_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('core/', include(core_router.urls)),
    path('accounts/', include('rest_registration.api.urls')),
    path('register', registration_view, name='register'),
]
