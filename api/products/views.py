
from django.shortcuts import get_object_or_404

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

import logging

from api.models import Store, Image,Product, Category
from api.serializers import (ProductSerializer)

logger = logging.getLogger(__name__)

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
            
            store = get_object_or_404(Store, id=store_id)
            filters = {
                'store': store,
                            }
  
            if is_archived is not None:
               filters['is_archived'] = is_archived.lower() == 'true'


            if category_id:
                filters['category_id'] = category_id

            
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
