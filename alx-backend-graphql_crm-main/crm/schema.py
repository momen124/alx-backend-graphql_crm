import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from .models import Customer, Product, Order
from .filters import CustomerFilter, ProductFilter, OrderFilter
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP


# FILTER INPUT TYPES

class CustomerFilterInput(graphene.InputObjectType):
    nameIcontains = graphene.String()
    emailIcontains = graphene.String()
    createdAtGte = graphene.String()
    createdAtLte = graphene.String()
    phonePattern = graphene.String()

class ProductFilterInput(graphene.InputObjectType):
    nameIcontains = graphene.String()
    priceGte = graphene.Float()
    priceLte = graphene.Float()
    stockGte = graphene.Int()
    stockLte = graphene.Int()

class OrderFilterInput(graphene.InputObjectType):
    totalAmountGte = graphene.Float()
    totalAmountLte = graphene.Float()
    orderDateGte = graphene.String()
    orderDateLte = graphene.String()
    customerNameIcontains = graphene.String()
    productNameIcontains = graphene.String()
    productId = graphene.Int()


# FILTER NODES
class CustomerNode(DjangoObjectType):
    class Meta:
        model = Customer
        interfaces = (graphene.relay.Node,)
        filterset_class = CustomerFilter


class ProductNode(DjangoObjectType):
    class Meta:
        model = Product
        interfaces = (graphene.relay.Node,)
        filterset_class = ProductFilter


class OrderNode(DjangoObjectType):
    class Meta:
        model = Order
        interfaces = (graphene.relay.Node,)
        filterset_class = OrderFilter


# TYPES
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = '__all__'


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = '__all__'


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = '__all__'


# INPUTS
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()


class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Float(required=True)
    stock = graphene.Int()


class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)


# CUSTOM FILTERED CONNECTION FIELD 

class FilteredConnectionField(DjangoFilterConnectionField):
    def __init__(self, type, *args, **kwargs):
        filter_class = kwargs.pop('filter_class', None)
        if filter_class:
            kwargs.setdefault('args', {})
            kwargs['args']['filter'] = graphene.Argument(filter_class)
            kwargs['args']['orderBy'] = graphene.String()
        super().__init__(type, *args, **kwargs)

    def get_queryset(self, queryset, info, **args):
        filter_data = args.get('filter')
        order_by = args.get('orderBy')

        if filter_data:
            django_filters = {}

            for key, value in filter_data.items():
                if value is None:
                    continue

                # Convert camelCase filter keys to Django ORM keys:
                # e.g. nameIcontains -> name__icontains
                django_key = key

                # Mapping replacements
                django_key = django_key.replace('Icontains', '__icontains')
                django_key = django_key.replace('Gte', '__gte')
                django_key = django_key.replace('Lte', '__lte')
                django_key = django_key.replace('Pattern', '__startswith')
                django_key = django_key.replace('Id', '_id')
                django_key = django_key.replace('At', '_at')
                django_key = django_key.replace('Amount', '_amount')
                django_key = django_key.replace('Date', '_date')
                django_key = django_key.replace('Name', '_name')

                # Convert first char to lowercase for field name consistency
                django_key = django_key[0].lower() + django_key[1:]

                django_filters[django_key] = value

            queryset = queryset.filter(**django_filters)

        if order_by:
            queryset = queryset.order_by(order_by)

        return queryset


#  MUTATIONS 
class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()

    def mutate(self, info, input):
        if Customer.objects.filter(email=input.email).exists():
            raise Exception("Email already exists")

        customer = Customer(name=input.name, email=input.email, phone=input.phone or "")
        customer.full_clean()
        customer.save()
        return CreateCustomer(customer=customer, message="Customer created successfully.")


class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, input):
        valid_customers = []
        errors = []

        for index, data in enumerate(input):
            try:
                if Customer.objects.filter(email=data.email).exists():
                    raise Exception(f"Duplicate email: {data.email}")
                cust = Customer(name=data.name, email=data.email, phone=data.phone or "")
                cust.full_clean()
                valid_customers.append(cust)
            except Exception as e:
                errors.append(f"Entry {index + 1}: {str(e)}")

        created = Customer.objects.bulk_create(valid_customers)
        return BulkCreateCustomers(customers=created, errors=errors)


class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    product = graphene.Field(ProductType)

    def mutate(self, info, input):
        try:
            price = float(input.price)
        except (ValueError, TypeError):
            raise Exception("Price must be a valid number.")

        if price <= 0:
            raise Exception("Price must be positive.")

        if input.stock is not None and input.stock < 0:
            raise Exception("Stock cannot be negative.")

        price = Decimal(str(price)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        product = Product(name=input.name, price=price, stock=input.stock or 0)
        product.full_clean()
        product.save()
        return CreateProduct(product=product)


class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)

    order = graphene.Field(OrderType)

    def mutate(self, info, input):
        try:
            customer = Customer.objects.get(pk=input.customer_id)
        except Customer.DoesNotExist:
            raise Exception("Invalid customer ID")

        if not input.product_ids:
            raise Exception("At least one product must be selected")

        products = []
        total = 0
        for pid in input.product_ids:
            try:
                product = Product.objects.get(pk=pid)
                products.append(product)
                total += float(product.price)
            except Product.DoesNotExist:
                raise Exception(f"Invalid product ID: {pid}")

        order = Order(customer=customer, total_amount=total, order_date=timezone.now())
        order.save()
        order.products.set(products)
        return CreateOrder(order=order)


# QUERY EXPORT 
class Query(graphene.ObjectType):
    hello = graphene.String(default_value="Hello from CRM schema!")

    all_customers = FilteredConnectionField(
        CustomerNode,
        filter_class=CustomerFilterInput
    )
    all_products = FilteredConnectionField(
        ProductNode,
        filter_class=ProductFilterInput
    )
    all_orders = FilteredConnectionField(
        OrderNode,
        filter_class=OrderFilterInput
    )


#  MUTATION EXPORT
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
