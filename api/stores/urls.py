# urls.py

from django.urls import path

from . import views

urlpatterns = [
    path('stores/', views.StoreView.as_view(), name='store-list'),
    path('stores/<uuid:store_id>/', views.StoreDetailView.as_view(), name='store-detail'),
]
