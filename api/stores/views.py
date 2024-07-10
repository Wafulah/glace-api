
from django.shortcuts import get_object_or_404
from django.http import Http404

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

import logging

from api.models import Store, Image, County, Category
from api.serializers import (
    StoreSerializer 
  )

logger = logging.getLogger(__name__)

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