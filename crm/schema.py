import graphene
from graphene_django import DjangoObjectType
from graphene import relay
from django.db import transaction
from django.utils import timezone
from django.core.validators import validate_email
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from decimal import Decimal
from graphene_django.filter import DjangoFilterConnectionField
from graphql import GraphQLError
from .filters import CustomerFilter, ProductFilter, OrderFilter
from .models import Customer, Product, Order

# ==============================
# GraphQL Types
# ==============================

class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        interfaces = (relay.Node,)


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        interfaces = (relay.Node,)


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        interfaces = (relay.Node,)


# ==============================
# Input Types
# ==============================

class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()


class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Decimal(required=True)
    stock = graphene.Int(default_value=0)


class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)
    order_date = graphene.DateTime()


# ==============================
# Mutations
# ==============================

class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()

    def mutate(self, info, input):
        try:
            if Customer.objects.filter(email=input.email).exists():
                raise GraphQLError("Email already exists.")
            validate_email(input.email)
            customer = Customer(
                name=input.name,
                email=input.email,
                phone=input.phone or ''
            )
            customer.save()  # explicitly called
            return CreateCustomer(customer=customer, message="Customer created successfully.")
        except ValidationError:
            raise GraphQLError("Invalid email format.")
        except Exception as e:
            raise GraphQLError(str(e))


class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, input):
        created = []
        errors = []
        with transaction.atomic():
            for i, cust in enumerate(input):
                try:
                    validate_email(cust.email)
                    if Customer.objects.filter(email=cust.email).exists():
                        raise GraphQLError("Email already exists.")

                    customer = Customer(
                        name=cust.name,
                        email=cust.email,
                        phone=cust.phone or ''
                    )
                    customer.save()  # explicitly called
                    created.append(customer)
                except ValidationError:
                    errors.append(f"Entry {i + 1}: Invalid email format.")
                except Exception as e:
                    errors.append(f"Entry {i + 1}: {str(e)}")

        return BulkCreateCustomers(customers=created, errors=errors)


class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    product = graphene.Field(ProductType)

    def mutate(self, info, input):
        try:
            if input.price <= Decimal("0.00"):
                raise GraphQLError("Price must be greater than 0.")
            if input.stock < 0:
                raise GraphQLError("Stock cannot be negative.")

            product = Product(
                name=input.name,
                price=input.price,
                stock=input.stock
            )
            product.save()  # explicitly called
            return CreateProduct(product=product)
        except Exception as e:
            raise GraphQLError(str(e))


class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)

    order = graphene.Field(OrderType)

    def mutate(self, info, input):
        try:
            customer = Customer.objects.get(id=input.customer_id)
        except ObjectDoesNotExist:
            raise GraphQLError("Invalid customer ID.")

        products = Product.objects.filter(id__in=input.product_ids)
        if not products.exists():
            raise GraphQLError("No valid products found for order.")

        if products.count() != len(input.product_ids):
            raise GraphQLError("Some product IDs are invalid.")

        total_amount = sum([product.price for product in products])
        order = Order(
            customer=customer,
            order_date=input.order_date or timezone.now(),
            total_amount=total_amount
        )
        order.save()  # explicitly called
        order.products.set(products)

        return CreateOrder(order=order)


# ==============================
# Main Mutation & Query classes
# ==============================

class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()


class Query(graphene.ObjectType):
    hello = graphene.String()
    all_customers = DjangoFilterConnectionField(CustomerType, filterset_class=CustomerFilter)
    all_products = DjangoFilterConnectionField(ProductType, filterset_class=ProductFilter)
    all_orders = DjangoFilterConnectionField(OrderType, filterset_class=OrderFilter)

    def resolve_hello(self, info):
        return "Hello, GraphQL!"
