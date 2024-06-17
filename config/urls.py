from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('oidc/', include('oidc_provider.urls', namespace='oidc_provider')),
    path('api/', include('api.urls')),
]

LOGIN_URL = '/oidc/authorize/' 
LOGOUT_URL = '/oidc/end-session/' 
