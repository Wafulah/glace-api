# urls.py

from django.urls import path
from .views import InitiateGoogleLoginView, GoogleCallbackView,test_auth

urlpatterns = [
    path('auth/google', InitiateGoogleLoginView.as_view(), name='initiate_google_login'),
    path('openid/callback/', GoogleCallbackView.as_view(), name='google_callback'),
    path('auth/test', test_auth, name='test_auth'),
    ]
