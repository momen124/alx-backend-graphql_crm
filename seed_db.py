#!/usr/bin/env python
"""
Seed script to populate the database with sample data
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'graphql_crm.settings')
django.setup()

from crm.models import Customer, Product, Order


def seed_database():
    """Seed the database with sample data"""
    print("🌱 Seeding database...")

    # Create customers
    customers_data = [
        {"name": "Alice Johnson", "email": "alice@example.com", "phone": "+1234567890"},
        {"name": "Bob Smith", "email": "bob@example.com", "phone": "123-456-7890"},
        {"name": "Carol Brown", "email": "carol@example.com", "phone": "+1987654321"},
        {"name": "David Wilson", "email": "david@example.com"},
    ]

    customers = []
    for data in customers_data:
        customer, created = Customer.objects.get_or_create(
            email=data['email'],
            defaults=data
        )
        customers.append(customer)
        if created:
            print(f"✅ Created customer: {customer.name}")
        else:
            print(f"ℹ️  Customer already exists: {customer.name}")

    # Create products
    products_data = [
        {"name": "Laptop", "price": 999.99, "stock": 10},
        {"name": "Mouse", "price": 29.99, "stock": 50},
        {"name": "Keyboard", "price": 79.99, "stock": 30},
        {"name": "Monitor", "price": 299.99, "stock": 15},
        {"name": "Headphones", "price": 199.99, "stock": 25},
    ]

    products = []
    for data in products_data:
        product, created = Product.objects.get_or_create(
            name=data['name'],
            defaults=data
        )
        products.append(product)
        if created:
            print(f"✅ Created product: {product.name}")
        else:
            print(f"ℹ️  Product already exists: {product.name}")

    # Create sample orders
    if customers and products:
        # Order 1: Alice buys laptop and mouse
        order1, created = Order.objects.get_or_create(
            customer=customers[0],
            defaults={}
        )
        if created:
            order1.products.set([products[0], products[1]])  # Laptop + Mouse
            order1.calculate_total()
            order1.save()
            print(f"✅ Created order for {customers[0].name}: ${order1.total_amount}")

        # Order 2: Bob buys keyboard and headphones
        order2, created = Order.objects.get_or_create(
            customer=customers[1],
            defaults={}
        )
        if created:
            order2.products.set([products[2], products[4]])  # Keyboard + Headphones
            order2.calculate_total()
            order2.save()
            print(f"✅ Created order for {customers[1].name}: ${order2.total_amount}")

    print("\nDatabase seeding completed!")
    print(f"Total customers: {Customer.objects.count()}")
    print(f"Total products: {Product.objects.count()}")
    print(f"Total orders: {Order.objects.count()}")


if __name__ == '__main__':
    seed_database()