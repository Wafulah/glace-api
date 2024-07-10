from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('oidc/', include('oidc_provider.urls', namespace='oidc_provider')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/', include('api.urls')),
    path('api/', include('api.customers.urls')),
    path('api/', include('api.products.urls')),
    path('api/', include('api.orders.urls')),
    path('api/', include('api.store.urls')),
]

LOGIN_URL = '/oidc/authorize/' 
LOGOUT_URL = '/oidc/end-session/' 
