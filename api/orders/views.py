
from django.shortcuts import redirect, get_object_or_404

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

import logging


from . import africastalking_api
from api.utils import SendSMS, get_product_details, send_email
from api.models import Store, Product, Order, OrderItem, Customer
from api.serializers import (
    OrderSerializer
)

logger = logging.getLogger(__name__)

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
            sms_sender = SendSMS()
            sms_sender.send_message(order.phone, message)

            #africa's talking function for sending sms, returns 101 - success
            # response = africastalking_api.send_sms(order.phone, message)
            
    
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