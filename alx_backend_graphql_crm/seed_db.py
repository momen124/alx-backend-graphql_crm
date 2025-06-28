import os
import django
from decimal import Decimal
from datetime import datetime, timedelta
import random

# Setup Django environment for standalone script usage
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_backend_graphql_crm.settings')
django.setup()

from crm.models import Customer, Product, Order

def seed_customers():
    sample_customers = [
        {"name": "Alice Johnson", "email": "alice@example.com", "phone": "+1234567890"},
        {"name": "Bob Smith", "email": "bob@example.com", "phone": "123-456-7890"},
        {"name": "Carol White", "email": "carol@example.com", "phone": "+1987654321"},
        {"name": "David Lee", "email": "david@example.com", "phone": "+11234567890"},
        {"name": "Eve Adams", "email": "eve@example.com", "phone": "123-123-1234"},
    ]

    created_customers = []
    for cust in sample_customers:
        customer, created = Customer.objects.get_or_create(
            email=cust['email'],
            defaults={"name": cust['name'], "phone": cust['phone']}
        )
        created_customers.append(customer)
    print(f"Seeded {len(created_customers)} customers")
    return created_customers

def seed_products():
    sample_products = [
        {"name": "Laptop", "price": Decimal("999.99"), "stock": 10},
        {"name": "Smartphone", "price": Decimal("599.99"), "stock": 25},
        {"name": "Headphones", "price": Decimal("199.99"), "stock": 50},
        {"name": "Keyboard", "price": Decimal("49.99"), "stock": 100},
        {"name": "Monitor", "price": Decimal("299.99"), "stock": 20},
    ]

    created_products = []
    for prod in sample_products:
        product, created = Product.objects.get_or_create(
            name=prod['name'],
            defaults={"price": prod['price'], "stock": prod['stock']}
        )
        created_products.append(product)
    print(f"Seeded {len(created_products)} products")
    return created_products

def seed_orders(customers, products):
    order_count = 0
    for customer in customers:
        # Each customer places 1-3 orders randomly
        num_orders = random.randint(1, 3)
        for _ in range(num_orders):
            chosen_products = random.sample(products, random.randint(1, min(3, len(products))))
            total_amount = sum(p.price for p in chosen_products)
            order_date = datetime.now() - timedelta(days=random.randint(0, 365))

            order = Order.objects.create(
                customer=customer,
                total_amount=total_amount,
                order_date=order_date
            )
            order.products.set(chosen_products)
            order_count += 1
    print(f"Seeded {order_count} orders")

if __name__ == '__main__':
    print("Starting DB seed...")
    customers = seed_customers()
    products = seed_products()
    seed_orders(customers, products)
    print("DB seed complete!")
