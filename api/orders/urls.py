# urls.py

from django.urls import path

from . import views

urlpatterns = [
    path('<uuid:store_id>/orders/', views.OrderView.as_view(), name='orders'),
    path('<uuid:store_id>/orders/<uuid:order_id>/', views.OrderDetailUpdateView.as_view(), name='order-update'),
]
