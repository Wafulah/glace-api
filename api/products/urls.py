# urls.py

from django.urls import path

from . import views

urlpatterns = [
    path('<uuid:store_id>/products/', views.StoreProductView.as_view(), name='store-products'),
    path('<uuid:store_id>/products/<uuid:product_id>/', views.StoreProductDetailView.as_view(), name='store-product-detail'),
]
