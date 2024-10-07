# urls.py

from django.urls import path

from . import views

urlpatterns = [
    path('<uuid:store_id>/customers/', views.CustomerView.as_view(), name='customer-create'),
    path('<uuid:store_id>/customers/<uuid:customer_id>/', views.CustomerDetailView.as_view(), name='customer-detail'),
    ]
