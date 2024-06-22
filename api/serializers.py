from rest_framework import serializers
from django.shortcuts import get_object_or_404
from .models import Store, Image, Product, Category, County,Order,OrderItem,Customer

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(many=True, read_only=True)
    customer = CustomerSerializer(read_only=True)

    class Meta:
        model = Order
        fields = '__all__'

    def create(self, validated_data):
        order_items_data = self.context['request'].data.get('orderItems', [])
        customer_data = self.context['request'].data.get('customer', {})
        store_id = validated_data.pop('store').id
        customer = get_object_or_404(Customer, id=customer_data['id'])

        order = Order.objects.create(**validated_data, customer=customer)
        for item_data in order_items_data:
            product = get_object_or_404(Product, id=item_data['product']['id'])
            quantity = item_data['quantity']
            price = item_data['price']
            OrderItem.objects.create(order=order, product=product, quantity=quantity, price=price)
        return order


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ['id', 'url']

class ProductSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'store', 'category', 'name', 'price', 'quantity', 'rating', 'description', 'is_archived', 'created_at', 'updated_at', 'images']
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']

class CountySerializer(serializers.ModelSerializer):
    class Meta:
        model = County
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']

class StoreSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, read_only=True)
    products = ProductSerializer(many=True, read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    counties = CountySerializer(many=True, read_only=True)

    class Meta:
        model = Store
        fields = ['id', 'name', 'description', 'created_at', 'updated_at', 'latitude', 'longitude', 'paybill', 'images', 'products', 'categories', 'counties']



class OrderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['is_delivered', 'delivery_date','is_paid']

        