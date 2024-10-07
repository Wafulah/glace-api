
from django.shortcuts import get_object_or_404

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

import logging

from api.models import Store, Customer
from api.serializers import (
    CustomerSerializer
)

logger = logging.getLogger(__name__)

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