# urls.py

from django.urls import path

from . import views

urlpatterns = [
    path('auth/google', views.InitiateGoogleLoginView.as_view(), name='initiate_google_login'),
    path('openid/callback/', views.GoogleCallbackView.as_view(), name='google_callback'),
    path('get-user-by-email/', views.get_user_by_email, name='get_user_by_email'),
    path('get-user-by-id/', views.get_user_by_id, name='get_user_by_id'),
    path('stores/', views.StoreView.as_view(), name='store-list'),
    path('stores/<uuid:store_id>/', views.StoreDetailView.as_view(), name='store-detail'),
    path('<uuid:store_id>/products/', views.StoreProductView.as_view(), name='store-products'),
    path('<uuid:store_id>/products/<uuid:product_id>/', views.StoreProductDetailView.as_view(), name='store-product-detail'),
    path('<uuid:store_id>/categories/', views.CategoryView.as_view(), name='store-categories'),
    path('<uuid:store_id>/categories/<uuid:category_id>/', views.CategoryDetailView.as_view(), name='store-detail-categories'),
    path('<uuid:store_id>/counties/<uuid:county_id>/', views.CountyDetailView.as_view(), name='county-detail'),
    path('<uuid:store_id>/counties/', views.CountyView.as_view(), name='counties'),
    path('<uuid:store_id>/orders/', views.OrderView.as_view(), name='orders'),
    path('<uuid:store_id>/orders/<uuid:order_id>/', views.OrderDetailUpdateView.as_view(), name='order-update'),
    path('<uuid:store_id>/customers/', views.CustomerView.as_view(), name='customer-create'),
    path('<uuid:store_id>/customers/<uuid:customer_id>/', views.CustomerDetailView.as_view(), name='customer-detail'),
    ]
