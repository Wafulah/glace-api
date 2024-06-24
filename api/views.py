from django.shortcuts import redirect, get_object_or_404
from django.views import View
from django.conf import settings
from django.http import JsonResponse, HttpResponseRedirect,Http404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods

from oidc_provider.models import Client
from oidc_provider.lib.utils.oauth2 import protected_resource_view

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

import requests
import json
import logging
import urllib.parse

from . import africastalking_api
from .utils import create_or_update_user, SendSMS, get_product_details, send_email
from .models import Store, Image, County, Product, Category, Order, OrderItem, Customer
from .serializers import (
    StoreSerializer, OrderUpdateSerializer, ProductSerializer, 
    ImageSerializer, CategorySerializer, CountySerializer, 
    OrderSerializer, OrderItemSerializer, CustomerSerializer
)

logger = logging.getLogger(__name__)


class InitiateGoogleLoginView(APIView):
    @csrf_exempt  # Disable CSRF for this view
    def post(self, request):
        callback_url = request.data.get('callbackUrl', settings.LOGIN_REDIRECT_URL)
        frontend_redirect_url = settings.LOGIN_REDIRECT_URL + '/settings'
        try:
            client = Client.objects.get(client_id=settings.OIDC_CLIENT_ID)
            logger.info(f"Client found: {client}")

            auth_url = (
                f"{settings.OIDC_AUTHORIZATION_ENDPOINT}?response_type=code"
                f"&client_id={client.client_id}"
                f"&redirect_uri={client.redirect_uris[0]}"
                f"&scope=openid email profile"
                f"&state={frontend_redirect_url}"
            )
            logger.info(f"Generated auth URL: {auth_url}")

            return Response({'authUrl': auth_url})
        except Client.DoesNotExist:
            logger.error("OIDC Client not found.")
            return JsonResponse({'error': 'OIDC Client not found'}, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class GoogleCallbackView(View):
    def get(self, request, *args, **kwargs):
        code = request.GET.get('code')
        state = request.GET.get('state', settings.LOGIN_REDIRECT_URL)
        logger.info(f"Received code: {code} and state: {state}")

        if not code:
            return JsonResponse({'error': 'No code provided'}, status=400)

        token_data = {
            'code': code,
            'client_id': settings.OIDC_CLIENT_ID,
            'client_secret': settings.OIDC_CLIENT_SECRET,
            'redirect_uri': settings.OIDC_PROVIDERS['google']['redirect_uris'][0],
            'grant_type': 'authorization_code',
        }
        logger.info(f"Token data: {token_data}")

        # Exchange authorization code for access token
        try:
            token_response = requests.post(settings.OIDC_TOKEN_ENDPOINT, data=token_data)
            token_response.raise_for_status()
            token_response_data = token_response.json()
            logger.info(f"Token response: {token_response_data}")
        except requests.RequestException as e:
            logger.error(f"Token request failed: {e}")
            return JsonResponse({'error': 'Token request failed'}, status=400)

        if 'error' in token_response_data:
            logger.error(f"Token endpoint error: {token_response_data['error']}")
            return JsonResponse({'error': token_response_data['error']}, status=400)

        access_token = token_response_data.get('access_token')
        if not access_token:
            logger.error("No access token found in the response")
            return JsonResponse({'error': 'No access token found'}, status=400)

        # Retrieve user info using access token
        try:
            user_info_response = requests.get(
                settings.OIDC_USERINFO_ENDPOINT,
                headers={'Authorization': f"Bearer {access_token}"}
            )
            user_info_response.raise_for_status()
            user_info = user_info_response.json()
            logger.info(f"User info: {user_info}")
        except requests.RequestException as e:
            logger.error(f"User info request failed: {e}")
            return JsonResponse({'error': 'User info request failed'}, status=400)

        # Create or update the user in your database
        try:
            user = create_or_update_user(user_info)
            logger.info(f"User created/updated: {user}")
        except Exception as e:
            logger.error(f"Error creating/updating user: {e}")
            return JsonResponse({'error': 'Error creating/updating user'}, status=500)

        # Manage session here
        request.session['user'] = user_info
        request.session['session_token'] = access_token 
        # Redirect to the frontend with the user info or session token
        frontend_redirect_url = f"{settings.LOGIN_REDIRECT_URL}/api/loguser"
        redirect_url_with_params = f"{frontend_redirect_url}?session_token={access_token}&user_info={urllib.parse.quote_plus(json.dumps(user_info))}"
        return HttpResponseRedirect(redirect_url_with_params)

    
def logout_view(request):
    id_token_hint = request.session.get('id_token')
    post_logout_redirect_uri = settings.LOGIN_REDIRECT_URL + '/logged-out/'

    logout_url = (
        f"{settings.OIDC_LOGOUT_ENDPOINT}?"
        f"id_token_hint={id_token_hint}&"
        f"post_logout_redirect_uri={post_logout_redirect_uri}"
    )
    return redirect(logout_url)    

#Ignore this, refer to get-user-by-id
@csrf_exempt
@require_http_methods(["GET"])
def get_user_by_email(request):
    if request.method == "GET":
        email = request.GET.get("email", "")
        if not email:
            return JsonResponse({"error": "Email parameter is required"}, status=400)
       

        email = urllib.parse.unquote(email) 
        
 
        try:
            user = User.objects.get(email=email)
            user_data = {
                "id": str(user.id),
                "name": user.first_name,
                "email": user.email,
            }
            return JsonResponse(user_data)
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)

@csrf_exempt
@require_http_methods(["GET"])
def get_user_by_id(request):
    if request.method == "GET":
        user_id = request.GET.get("id", "")
        access_token = request.GET.get("access_token", "")
        if not user_id:
            return JsonResponse({"error": "User ID parameter is required"}, status=400)

        try:
            
            user = User.objects.get(username=user_id)
            
            #store access token into session
            if (access_token):
                request.session['session_token'] = access_token 
                
            #not neccessary, just checking if session works
            session_token = request.session.get('session_token')
 
            
            # Generate JWT token for the user
            refresh = RefreshToken.for_user(user)
            jwt_token = str(refresh.access_token)

            user_data = {
                "id": str(user.id),
                "name": user.first_name,
                "email": user.email,
                "session_token": session_token,
                "jwt_token": jwt_token
                           }
            
            return JsonResponse(user_data)
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)



class StoreView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            stores = Store.objects.filter(user=user)
            serializer = StoreSerializer(stores, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("[STORES_GET] %s", e)
            return Response({"detail": "Internal error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            user = request.user
            name = request.data.get('name')

            if not name:
                return Response({"detail": "Name is required"}, status=status.HTTP_400_BAD_REQUEST)

            store = Store.objects.create(
                name=name,
                user=user
            )

            serializer = StoreSerializer(store)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error("[STORES_POST] %s", e)
            return Response({"detail": "Internal error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)   
class StoreDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, store_id):
        try:
            user = request.user
            store = get_object_or_404(Store, id=store_id, user=user)
            serializer = StoreSerializer(store)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("[SPECIFIC_STORE_GET] %s", str(e))
            return Response({"detail": "Internal error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, store_id):
        try:
            user = request.user
            data = request.data
            name = data.get('name')
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            images = data.get('images', [])
            paybill = data.get('paybill')
            description = data.get('description')
            categories = data.get('categories', [])
            counties = data.get('counties', [])

            if not user.id:
                return Response({"detail": "Unauthenticated"}, status=status.HTTP_403_FORBIDDEN)

            if not name:
                return Response({"detail": "Name is required"}, status=status.HTTP_400_BAD_REQUEST)

            store = get_object_or_404(Store, id=store_id, user=user)

            update_data = {
                'name': name,
                'description': description,
                'paybill': paybill,
            }

            if latitude is not None:
                update_data['latitude'] = latitude

            if longitude is not None:
                update_data['longitude'] = longitude

            serializer = StoreSerializer(store, data=update_data, partial=True)
            if serializer.is_valid():
                serializer.save()

                # Handle images separately
                store.images.all().delete()
                for image_data in images:
                    Image.objects.create(store=store, **image_data)

                # Handle categories and counties separately
                if categories:
                    try:
                        store.categories.clear()  # Disconnect all existing categories
                        for category_data in categories:
                            category = get_object_or_404(Category, id=category_data['id'])
                            store.categories.add(category)
                    except Http404 as e:
                        logger.error("Category not found with id %s", category_data['id'])
                        return Response({"detail": f"Category not found with id {category_data['id']}"},
                                        status=status.HTTP_404_NOT_FOUND)

                if counties:
                    try:
                        store.counties.clear()  # Disconnect all existing counties
                        for county_data in counties:
                            county = get_object_or_404(County, id=county_data['id'])
                            store.counties.add(county)
                    except Http404 as e:
                        logger.error("County not found with id %s", county_data['id'])
                        return Response({"detail": f"County not found with id {county_data['id']}"},
                                        status=status.HTTP_404_NOT_FOUND)

                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error("[STORE_PATCH] %s", str(e))
            return Response({"detail": "Internal error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, store_id):
        try:
            user = request.user
            store = get_object_or_404(Store, id=store_id, user=user)
            store.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error("[STORE_DELETE] %s", str(e))
            return Response({"detail": "Internal error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class StoreProductView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, store_id):
        try:
            user = request.user
            data = request.data
            name = data.get('name')
            price = data.get('price')
            category_id = data.get('categoryId')
            images = data.get('images', [])
            is_archived = data.get('isArchived', False)
            quantity = data.get('quantity')
            rating = data.get('rating')
            description = data.get('description')

            if not name:
                return Response({"detail": "Name is required"}, status=status.HTTP_400_BAD_REQUEST)
            if not images:
                return Response({"detail": "Images are required"}, status=status.HTTP_400_BAD_REQUEST)
            if not price:
                return Response({"detail": "Price is required"}, status=status.HTTP_400_BAD_REQUEST)
            if not quantity:
                return Response({"detail": "Quantity is required"}, status=status.HTTP_400_BAD_REQUEST)
            if not rating:
                return Response({"detail": "Rating is required"}, status=status.HTTP_400_BAD_REQUEST)
            if not description:
                return Response({"detail": "Description is required"}, status=status.HTTP_400_BAD_REQUEST)
            if not category_id:
                return Response({"detail": "Category id is required"}, status=status.HTTP_400_BAD_REQUEST)

            store = get_object_or_404(Store, id=store_id, user=user)
            category = get_object_or_404(Category, id=category_id)

            product = Product.objects.create(
                store=store,
                name=name,
                price=price,
                quantity=quantity,
                rating=rating,
                description=description,
                is_archived=is_archived,
                category=category
            )

            for image_data in images:
                Image.objects.create(product=product, url=image_data['url'])

            serializer = ProductSerializer(product)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error("[PRODUCTS_POST] %s", e)
            return Response({"detail": "Internal error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, store_id):
        try:
            category_id = request.GET.get('categoryId', None)
            is_archived = request.GET.get('isArchived', None)
            logger.error("[Filters archive] %s",is_archived) 
            store = get_object_or_404(Store, id=store_id)
            filters = {
                'store': store,
                            }

            if is_archived is not None:
                filters['is_archived'] = is_archived.lower() == 'false'


            if category_id:
                filters['category_id'] = category_id

            logger.error("[Filters] %s",filters)
            products = Product.objects.filter(**filters).order_by('-created_at')
            serializer = ProductSerializer(products, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error("[PRODUCTS_GET] %s", e)
            return Response({"detail": "Internal error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class StoreProductDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, store_id, product_id):
        try:
            if not product_id:
                return Response({"detail": "Product id is required"}, status=status.HTTP_400_BAD_REQUEST)

            product = get_object_or_404(Product, id=product_id, store__id=store_id)
            serializer = ProductSerializer(product)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error("[PRODUCT_GET] %s", e)
            return Response({"detail": "Internal error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, store_id, product_id):
        try:
            user = request.user
            if not user.id:
                return Response({"detail": "Unauthenticated"}, status=status.HTTP_403_FORBIDDEN)

            if not product_id:
                return Response({"detail": "Product id is required"}, status=status.HTTP_400_BAD_REQUEST)

            store = get_object_or_404(Store, id=store_id, user=user)
            product = get_object_or_404(Product, id=product_id, store=store)
            product.delete()

            return Response({"detail": "Product deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            logger.error("[PRODUCT_DELETE] %s", e)
            return Response({"detail": "Internal error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, store_id, product_id):
        try:
            user = request.user
            data = request.data

            if not user.id:
                return Response({"detail": "Unauthenticated"}, status=status.HTTP_403_FORBIDDEN)

            if not product_id:
                return Response({"detail": "Product id is required"}, status=status.HTTP_400_BAD_REQUEST)

            store = get_object_or_404(Store, id=store_id, user=user)
            product = get_object_or_404(Product, id=product_id, store=store)

            name = data.get('name')
            price = data.get('price')
            category_id = data.get('categoryId')
            images = data.get('images', [])
            is_archived = data.get('isArchived', False)
            quantity = data.get('quantity')
            rating = data.get('rating')
            description = data.get('description')

            if not name:
                return Response({"detail": "Name is required"}, status=status.HTTP_400_BAD_REQUEST)
            if not images or len(images) == 0:
                return Response({"detail": "Images are required"}, status=status.HTTP_400_BAD_REQUEST)
            if not price:
                return Response({"detail": "Price is required"}, status=status.HTTP_400_BAD_REQUEST)
            if not quantity:
                return Response({"detail": "Quantity is required"}, status=status.HTTP_400_BAD_REQUEST)
            if not description:
                return Response({"detail": "Description is required"}, status=status.HTTP_400_BAD_REQUEST)
            if not category_id:
                return Response({"detail": "Category id is required"}, status=status.HTTP_400_BAD_REQUEST)

            category = get_object_or_404(Category, id=category_id)

            product.name = name
            product.price = price
            product.category = category
            product.quantity = quantity
            product.rating = rating
            product.description = description
            product.is_archived = is_archived
            product.save()

            # Delete existing images and create new ones
            product.images.all().delete()
            for image_data in images:
                Image.objects.create(product=product, url=image_data['url'])

            serializer = ProductSerializer(product)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error("[PRODUCT_PATCH] %s", e)
            return Response({"detail": "Internal error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CategoryDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, store_id, category_id):
        try:
            if not category_id:
                return Response({"detail": "Category id is required"}, status=status.HTTP_400_BAD_REQUEST)

            category = get_object_or_404(Category, id=category_id, store__id=store_id)
            serializer = CategorySerializer(category)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error("[CATEGORY_GET] %s", e)
            return Response({"detail": "Internal error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, store_id, category_id):
        try:
            user = request.user

            if not user.id:
                return Response({"detail": "Unauthenticated"}, status=status.HTTP_403_FORBIDDEN)

            if not category_id:
                return Response({"detail": "Category id is required"}, status=status.HTTP_400_BAD_REQUEST)

            store = get_object_or_404(Store, id=store_id, user=user)
            category = get_object_or_404(Category, id=category_id, store=store)
            category.delete()

            return Response({"detail": "Category deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            logger.error("[CATEGORY_DELETE] %s", e)
            return Response({"detail": "Internal error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, store_id, category_id):
        try:
            user = request.user
            data = request.data

            if not user.id:
                return Response({"detail": "Unauthenticated"}, status=status.HTTP_403_FORBIDDEN)

            if not category_id:
                return Response({"detail": "Category id is required"}, status=status.HTTP_400_BAD_REQUEST)

            store = get_object_or_404(Store, id=store_id, user=user)
            category = get_object_or_404(Category, id=category_id, store=store)

            name = data.get('name')
            description = data.get('description')
            image_url = data.get('imageUrl')

            if not name:
                return Response({"detail": "Name is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            if not image_url:
                return Response({"detail": "Image URL is required"}, status=status.HTTP_400_BAD_REQUEST)

            category.name = name
            category.description = description
            category.image_url = image_url
            category.save()

            serializer = CategorySerializer(category)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error("[CATEGORY_PATCH] %s", e)
            return Response({"detail": "Internal error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CategoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, store_id):
        try:
            categories = Category.objects.all()
            serializer = CategorySerializer(categories, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("[CATEGORY_GET] %s", e)
            return Response({"detail": "Internal error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, store_id):
        try:
            user = request.user
            name = request.data.get('name')
            image_url = request.data.get('imageUrl')
            description = request.data.get('description')

            if not name or not image_url:
                return Response({"detail": "Name and Image URL are required"}, status=status.HTTP_400_BAD_REQUEST)

            store = get_object_or_404(Store, id=store_id, user=user)

            category = Category.objects.create(
                name=name,
                image_url=image_url,
                description=description,
                store=store,
            )

            serializer = CategorySerializer(category)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error("[CATEGORY_POST] %s", e)
            return Response({"detail": "Internal error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class CountyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, store_id):
        try:
            user = request.user
            if not user.id:
                return Response({"detail": "Unauthenticated"}, status=status.HTTP_403_FORBIDDEN)

            body = request.data
            name = body.get('name')
            description = body.get('description')

            if not name:
                return Response({"detail": "Name is required"}, status=status.HTTP_400_BAD_REQUEST)

            if not store_id:
                return Response({"detail": "Store id is required"}, status=status.HTTP_400_BAD_REQUEST)

            store = get_object_or_404(Store, id=store_id, user=user)

            county = County.objects.create(
                name=name,
                description=description,
                store=store
            )

            serializer = CountySerializer(county)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error("[COUNTIES_POST] %s", e)
            return Response({"detail": "Internal error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request,store_id):
        try:
            counties = County.objects.all()
            serializer = CountySerializer(counties, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error("[ALL_COUNTIES_GET] %s", e)
            return Response({"detail": "Internal error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CountyDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, store_id, county_id):
        try:
            if not county_id:
                return Response({"detail": "County id is required"}, status=status.HTTP_400_BAD_REQUEST)

            user = request.user
            if not user.id:
                return Response({"detail": "Unauthenticated"}, status=status.HTTP_403_FORBIDDEN)

            store = get_object_or_404(Store, id=store_id, user=user)
            county = get_object_or_404(County, id=county_id, store=store)
            serializer = CountySerializer(county)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error("[COUNTY_GET] %s", e)
            return Response({"detail": "Internal error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, store_id, county_id):
        try:
            user = request.user
            if not user.id:
                return Response({"detail": "Unauthenticated"}, status=status.HTTP_403_FORBIDDEN)

            if not county_id:
                return Response({"detail": "County id is required"}, status=status.HTTP_400_BAD_REQUEST)

            store = get_object_or_404(Store, id=store_id, user=user)
            county = get_object_or_404(County, id=county_id, store=store)
            county.delete()

            return Response({"detail": "County deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            logger.error("[COUNTY_DELETE] %s", e)
            return Response({"detail": "Internal error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, store_id, county_id):
        try:
            user = request.user
            if not user.id:
                return Response({"detail": "Unauthenticated"}, status=status.HTTP_403_FORBIDDEN)

            if not county_id:
                return Response({"detail": "County id is required"}, status=status.HTTP_400_BAD_REQUEST)

            store = get_object_or_404(Store, id=store_id, user=user)
            county = get_object_or_404(County, id=county_id, store=store)
            
            serializer = CountySerializer(county, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error("[COUNTY_PATCH] %s", e)
            return Response({"detail": "Internal error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OrderView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, store_id):
        try:
            user = request.user
            if not user.id:
                return Response({"detail": "Unauthenticated"}, status=status.HTTP_403_FORBIDDEN)

            store = get_object_or_404(Store, id=store_id, user=user)
            
            # Retrieve the isPaid query parameter
            is_paid = request.query_params.get('isPaid')
            
            # Filter orders based on isPaid if the parameter is provided
            if is_paid is not None:
                is_paid = is_paid.lower() == 'true'  # Convert to boolean
                orders = Order.objects.filter(store=store, is_paid=is_paid).order_by('-created_at')
            else:
                orders = Order.objects.filter(store=store).order_by('-created_at')
            serializer = OrderSerializer(orders, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error("[ORDERS_GET] %s", e)
            return Response({"detail": "Internal error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, store_id):
        try:
            user = request.user
            if not user.id:
                return Response({"detail": "Unauthenticated"}, status=status.HTTP_403_FORBIDDEN)
    
            store = get_object_or_404(Store, id=store_id, user=user)
            data = request.data
            data['store'] = store.id  # Ensure the store id is set
    
            customer_id = data.get('customerId')
            customer = get_object_or_404(Customer, id=customer_id, store=store)
    
            # Create the order
            order = Order.objects.create(
                store=store,
                customer=customer,
                is_paid=data.get('is_paid', False),
                is_delivered=data.get('is_delivered', False),
                phone=data.get('phone', ''),
                address=data.get('address', ''),
                delivery_date=data.get('delivery_date', None)
            )
    
            # Create order items
            order_items_data = data.get('orderItems', [])
            for item_data in order_items_data:
                product_id = item_data.get('product')
                product = get_object_or_404(Product, id=product_id)
                
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item_data.get('quantity', 1),
                    price=item_data.get('price', 0.00)
                )
    
            # Calculate the total price
            order.calculate_total_price()
    
            # Serialize the created order with its items
            serializer = OrderSerializer(order, context={'request': request})
    
            # Get product details for SMS
            product_details, total_price = get_product_details(order_items_data)
            products_info = "\n".join(
                [f"{item['quantity']} x {item['name']} @ {item['price']} each = {item['total']}" for item in product_details]
            )
            message = (
                f"Order received! \n"
                f"Items: \n{products_info}\n"
                f"Total: {total_price}\n"
                f"Thank you for shopping with us at {store.name}\n"
                f"Glace your Health care partner!"
            )
            subject="Order Received!"
            recipient=customer.email
            send_email(message,subject,recipient)
            # Send SMS using vonage, has free tier for live testing purposes
            # sms_sender = SendSMS()
            # sms_sender.send_message(order.phone, message)

            #africa's talking function for sending sms, returns 101 - success
            response = africastalking_api.send_sms(order.phone, message)
            
    
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    
        except Exception as e:
            logger.error("[ORDER_POST] %s", e)
            return Response({"detail": "Internal error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
#For integrity issues only update is_delivered,is_paid and delivery date.
class OrderDetailUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, store_id, order_id):
        try:
            user = request.user
            if not user.id:
                return Response({"detail": "Unauthenticated"}, status=status.HTTP_403_FORBIDDEN)

            # Retrieve the store
            store = get_object_or_404(Store, id=store_id, user=user)

            # Retrieve the order belonging to the store
            order = get_object_or_404(Order, id=order_id, store=store)

            # Serialize the order data
            serializer = OrderSerializer(order)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error("[ORDER_GET] %s", e)
            return Response({"detail": "Internal error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, store_id, order_id):
        try:
            user = request.user
            if not user.id:
                return Response({"detail": "Unauthenticated"}, status=status.HTTP_403_FORBIDDEN)

            # Retrieve the store
            store = get_object_or_404(Store, id=store_id, user=user)

            # Retrieve the order belonging to the store
            order = get_object_or_404(Order, id=order_id, store=store)

            # Update the order fields
            data = request.data
            is_delivered = data.get('is_delivered', order.is_delivered)
            delivery_date = data.get('delivery_date', order.delivery_date)
            is_paid = data.get('is_paid', order.is_paid)

            order.is_delivered = is_delivered
            order.delivery_date = delivery_date
            order.is_paid = is_paid
            order.save()
                        
            return Response({"detail": "Order updated successfully"}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error("[ORDER_UPDATE] %s", e)
            return Response({"detail": "Internal error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class CustomerView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, store_id):
        try:
            user = request.user
            store = get_object_or_404(Store, id=store_id, user=user)

            customers = Customer.objects.filter(store=store)
            serializer = CustomerSerializer(customers, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error("[CUSTOMERS_GET] %s", e)
            return Response({"detail": "Internal error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def post(self, request, store_id):
        try:
            user = request.user
            store = get_object_or_404(Store, id=store_id, user=user)

            first_name = request.data.get('first_name')
            last_name = request.data.get('last_name')
            email = request.data.get('email')
            phone_number = request.data.get('phone_number')

            # Create the customer with the store field
            customer = Customer.objects.create(
                store=store,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone_number=phone_number
            )

            # Serialize the created customer
            serializer = CustomerSerializer(customer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error("[CUSTOMERS_POST] %s", e)
            return Response({"detail": "Internal error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CustomerDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, store_id, customer_id):
        try:
            user = request.user
            store = get_object_or_404(Store, id=store_id, user=user)

            customer = get_object_or_404(Customer, id=customer_id, store=store)
            serializer = CustomerSerializer(customer)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error("[CUSTOMER_GET] %s", e)
            return Response({"detail": "Internal error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, store_id, customer_id):
        try:
            user = request.user
            store = get_object_or_404(Store, id=store_id, user=user)

            customer = get_object_or_404(Customer, id=customer_id, store=store)
            data = request.data

            serializer = CustomerSerializer(customer, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error("[CUSTOMER_PATCH] %s", e)
            return Response({"detail": "Internal error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, store_id, customer_id):
        try:
            user = request.user
            store = get_object_or_404(Store, id=store_id, user=user)

            customer = get_object_or_404(Customer, id=customer_id, store=store)
            customer.delete()

            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception as e:
            logger.error("[CUSTOMER_DELETE] %s", e)
            return Response({"detail": "Internal error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)