# urls.py

from django.urls import path

from . import views

urlpatterns = [
    path('auth/google', views.InitiateGoogleLoginView.as_view(), name='initiate_google_login'),
    path('openid/callback/', views.GoogleCallbackView.as_view(), name='google_callback'),
    path('get-user-by-email/', views.get_user_by_email, name='get_user_by_email'),
    path('get-user-by-id/', views.get_user_by_id, name='get_user_by_id'),
    path('<uuid:store_id>/categories/', views.CategoryView.as_view(), name='store-categories'),
    path('<uuid:store_id>/categories/<uuid:category_id>/', views.CategoryDetailView.as_view(), name='store-detail-categories'),
    path('<uuid:store_id>/counties/<uuid:county_id>/', views.CountyDetailView.as_view(), name='county-detail'),
    path('<uuid:store_id>/counties/', views.CountyView.as_view(), name='counties'),
]
