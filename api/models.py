from django.db import models
import uuid
from django.contrib.auth.models import User
from django.db.models import Sum, F, DecimalField

"""
Models representing entities in the system where a user must own a store to operate:

1. Store:
   - Represents a store owned by a user.
   - Each store can create its own products and manage customers.

2. Category:
   - Represents a category within a store for organizing products.

3. County:
   - Represents administrative divisions associated with a store.

4. Product:
   - Represents a product available in a store's inventory.

5. Customer:
   - Represents a customer associated with a specific store.

6. Order:
   - Represents an order created by a store using products and customers in its database.

7. OrderItem:
   - Represents individual items within an order linked to specific products.

8. Image:
   - Represents images associated with products or stores.
"""



class Store(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    paybill = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    store = models.ForeignKey(Store, related_name='categories', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    image_url = models.URLField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.name
    class Meta:
        indexes = [
            models.Index(fields=['store']),
        ]

class County(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    store = models.ForeignKey(Store, related_name='counties', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.name
    class Meta:
        indexes = [
            models.Index(fields=['store']),
        ]

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    store = models.ForeignKey(Store, related_name='products', on_delete=models.CASCADE)
    category = models.ForeignKey('Category', related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    rating = models.IntegerField()
    description = models.TextField()
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        indexes = [
            models.Index(fields=['store']),
            models.Index(fields=['category']),
        ]

class Customer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    store = models.ForeignKey(Store, related_name='customer', on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
  
    def __str__(self):
        return self.first_name

class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    store = models.ForeignKey(Store, related_name='orders', on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, related_name='orders', on_delete=models.CASCADE)
    is_paid = models.BooleanField(default=False)
    is_delivered = models.BooleanField(default=False)
    phone = models.CharField(max_length=20, default="")
    address = models.CharField(max_length=255, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    delivery_date = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
     
    class Meta:
        indexes = [
            models.Index(fields=['store']),
            models.Index(fields=['customer']),
        ]

    def calculate_total_price(self):
        total_price = self.order_items.aggregate(
            total=Sum(F('price'), output_field=DecimalField())
        )['total'] or 0
        self.total_price = total_price
        self.save()    

class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, related_name='order_items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['product']),
        ]

class Image(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE, null=True, blank=True)
    store = models.ForeignKey(Store, related_name='images', on_delete=models.CASCADE, null=True, blank=True)
    url = models.URLField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['product']),
            models.Index(fields=['store']),
        ]
