import graphene
from graphene_django.types import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django.core.exceptions import ValidationError
from django.db import transaction
from decimal import Decimal
from .models import Customer, Product, Order
from .filters import CustomerFilter, AdvancedCustomerFilter, ProductFilter, AdvancedProductFilter, OrderFilter, AdvancedOrderFilter


# CRM Statistics Type
class CRMStatsType(graphene.ObjectType):
    total_customers = graphene.Int()
    total_orders = graphene.Int()
    total_revenue = graphene.Float()


# Django Object Types
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = "__all__"
        # Enable filtering for this type
        filterset_class = CustomerFilter
        interfaces = (graphene.relay.Node, )


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = "__all__"
        # Enable filtering for this type
        filterset_class = ProductFilter
        interfaces = (graphene.relay.Node, )


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = "__all__"
        # Enable filtering for this type
        filterset_class = OrderFilter
        interfaces = (graphene.relay.Node, )


# Input Types
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()


class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Float(required=True)  # Changed back to Float for easier input
    stock = graphene.Int()


class OrderInput(graphene.InputObjectType):
    customerId = graphene.ID(required=True)  # Changed to match checkpoint format
    productIds = graphene.List(graphene.ID, required=True)  # Changed to match checkpoint format
    order_date = graphene.DateTime()


# Custom Error Type
class ErrorType(graphene.ObjectType):
    field = graphene.String()
    message = graphene.String()


# Mutation Response Types
# class CreateCustomer(graphene.Mutation)
class CreateCustomerMutation(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()
    errors = graphene.List(ErrorType)

    def mutate(self, info, input):
        try:
            # Check if email already exists
            if Customer.objects.filter(email=input.email).exists():
                return CreateCustomerMutation(
                    errors=[ErrorType(field="email", message="Email already exists")]
                )
            
            # Validate phone format if provided
            if input.phone:
                customer = Customer(name=input.name, email=input.email, phone=input.phone)
                customer.full_clean()  # This will validate the phone regex
            else:
                customer = Customer(name=input.name, email=input.email)
                customer.full_clean()
            
            customer.save()
            return CreateCustomerMutation(
                customer=customer,
                message=f"Customer '{customer.name}' created successfully!"
            )
        except ValidationError as e:
            errors = []
            for field, messages in e.message_dict.items():
                for message in messages:
                    # Provide user-friendly error messages
                    if field == 'email' and 'unique' in message.lower():
                        errors.append(ErrorType(field=field, message="Email already exists"))
                    elif field == 'phone':
                        errors.append(ErrorType(field=field, message="Invalid phone format. Use +1234567890 or 123-456-7890"))
                    else:
                        errors.append(ErrorType(field=field, message=message))
            return CreateCustomerMutation(errors=errors)
        except Exception as e:
            return CreateCustomerMutation(
                errors=[ErrorType(field="general", message=str(e))]
            )


class BulkCreateCustomersMutation(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(ErrorType)

    def mutate(self, info, input):
        customers_created = []
        errors = []
        
        # Process each customer individually (not in a single transaction for partial success)
        for i, customer_input in enumerate(input):
            try:
                # Check if email already exists
                if Customer.objects.filter(email=customer_input.email).exists():
                    errors.append(ErrorType(
                        field=f"customer_{i}_email",
                        message="Email already exists"
                    ))
                    continue
                
                if customer_input.phone:
                    customer = Customer(
                        name=customer_input.name,
                        email=customer_input.email,
                        phone=customer_input.phone
                    )
                else:
                    customer = Customer(
                        name=customer_input.name,
                        email=customer_input.email
                    )
                
                customer.full_clean()
                customer.save()
                customers_created.append(customer)
                
            except ValidationError as e:
                for field, messages in e.message_dict.items():
                    for message in messages:
                        # Provide user-friendly error messages
                        if field == 'email' and 'unique' in message.lower():
                            error_message = "Email already exists"
                        elif field == 'phone':
                            error_message = "Invalid phone format. Use +1234567890 or 123-456-7890"
                        else:
                            error_message = message
                        
                        errors.append(ErrorType(
                            field=f"customer_{i}_{field}",
                            message=error_message
                        ))
            except Exception as e:
                errors.append(ErrorType(
                    field=f"customer_{i}",
                    message=str(e)
                ))
        
        return BulkCreateCustomersMutation(customers=customers_created, errors=errors)


class CreateProductMutation(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    product = graphene.Field(ProductType)
    errors = graphene.List(ErrorType)

    def mutate(self, info, input):
        try:
            # Convert price float to Decimal and validate it's positive
            try:
                price = Decimal(str(input.price))
            except (ValueError, TypeError):
                return CreateProductMutation(
                    errors=[ErrorType(field="price", message="Invalid price format")]
                )
            
            if price <= 0:
                return CreateProductMutation(
                    errors=[ErrorType(field="price", message="Price must be positive")]
                )
            
            # Validate stock is non-negative (allow 0)
            stock = input.stock if input.stock is not None else 0
            if stock < 0:
                return CreateProductMutation(
                    errors=[ErrorType(field="stock", message="Stock must be non-negative (0 or greater)")]
                )
            
            product = Product(
                name=input.name,
                price=price,  # Use the converted Decimal value
                stock=stock
            )
            product.full_clean()
            product.save()
            
            return CreateProductMutation(product=product)
            
        except ValidationError as e:
            errors = []
            for field, messages in e.message_dict.items():
                for message in messages:
                    errors.append(ErrorType(field=field, message=message))
            return CreateProductMutation(errors=errors)
        except Exception as e:
            return CreateProductMutation(
                errors=[ErrorType(field="general", message=str(e))]
            )


class UpdateLowStockProducts(graphene.Mutation):
    """
    Mutation to restock products with low inventory (stock < 10).
    Increments stock by 10 for all qualifying products.
    """
    
    updated_products = graphene.List(ProductType)
    success_message = graphene.String()
    count = graphene.Int()

    def mutate(self, info):
        try:
            # Query products with stock < 10
            low_stock_products = Product.objects.filter(stock__lt=10)
            
            if not low_stock_products.exists():
                return UpdateLowStockProducts(
                    updated_products=[],
                    success_message="No products found with low stock (< 10).",
                    count=0
                )
            
            # Update products by incrementing stock by 10
            updated_products = []
            count = 0
            
            for product in low_stock_products:
                old_stock = product.stock
                product.stock += 10
                product.save(update_fields=['stock'])
                updated_products.append(product)
                count += 1
            
            success_message = f"Successfully restocked {count} products. Added 10 units to each product with stock < 10."
            
            return UpdateLowStockProducts(
                updated_products=updated_products,
                success_message=success_message,
                count=count
            )
            
        except Exception as e:
            return UpdateLowStockProducts(
                updated_products=[],
                success_message=f"Error during restocking: {str(e)}",
                count=0
            )


class CreateOrderMutation(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)

    order = graphene.Field(OrderType)
    errors = graphene.List(ErrorType)

    def mutate(self, info, input):
        try:
            # Validate customer exists
            try:
                customer = Customer.objects.get(id=input.customerId)
            except Customer.DoesNotExist:
                return CreateOrderMutation(
                    errors=[ErrorType(field="customerId", message="Customer does not exist")]
                )
            
            # Validate products exist and at least one is selected
            if not input.productIds:
                return CreateOrderMutation(
                    errors=[ErrorType(field="productIds", message="At least one product must be selected")]
                )
            
            products = []
            invalid_product_ids = []
            
            for product_id in input.productIds:
                try:
                    product = Product.objects.get(id=product_id)
                    products.append(product)
                except Product.DoesNotExist:
                    invalid_product_ids.append(product_id)
            
            if invalid_product_ids:
                return CreateOrderMutation(
                    errors=[ErrorType(
                        field="productIds",
                        message=f"Invalid product IDs: {', '.join(invalid_product_ids)}"
                    )]
                )
            
            # Create order
            with transaction.atomic():
                order = Order(customer=customer)
                if input.order_date:
                    order.order_date = input.order_date
                
                order.save()
                order.products.set(products)
                
                # Calculate total amount
                total = sum(product.price for product in products)
                order.total_amount = total
                order.save(update_fields=['total_amount'])
            
            return CreateOrderMutation(order=order)
            
        except Exception as e:
            return CreateOrderMutation(
                errors=[ErrorType(field="general", message=str(e))]
            )


# Query class
class Query(graphene.ObjectType):
    # Health check field
    hello = graphene.String(default_value="Hello from CRM!")
    
    # CRM Statistics
    crm_stats = graphene.Field(CRMStatsType)
    
    # Basic queries (existing)
    all_customers = graphene.List(CustomerType)
    all_products = graphene.List(ProductType)
    all_orders = graphene.List(OrderType)
    customer = graphene.Field(CustomerType, id=graphene.ID(required=True))
    product = graphene.Field(ProductType, id=graphene.ID(required=True))
    order = graphene.Field(OrderType, id=graphene.ID(required=True))
    
    # NEW: Filtered customer queries
    # Method 1: Using DjangoFilterConnectionField (Recommended for Relay-style pagination)
    customers = DjangoFilterConnectionField(CustomerType, filterset_class=CustomerFilter)
    
    # NEW: Filtered product queries
    products = DjangoFilterConnectionField(ProductType, filterset_class=ProductFilter)
    
    # NEW: Filtered order queries
    orders = DjangoFilterConnectionField(OrderType, filterset_class=OrderFilter)
    
    # Method 2: Custom filtered query with manual filter arguments
    filtered_customers = graphene.List(
        CustomerType,
        # Filter arguments
        name=graphene.String(description="Filter by name (case-insensitive partial match)"),
        email=graphene.String(description="Filter by email (case-insensitive partial match)"),
        created_at_gte=graphene.DateTime(description="Filter customers created on or after this date"),
        created_at_lte=graphene.DateTime(description="Filter customers created on or before this date"),
        phone_pattern=graphene.String(description="Filter by phone pattern (e.g., '+1' for US numbers)"),
        email_domain=graphene.String(description="Filter by email domain (e.g., 'gmail.com')"),
        has_phone=graphene.Boolean(description="Filter customers who have/don't have phone numbers"),
        # Pagination
        limit=graphene.Int(description="Limit the number of results"),
        offset=graphene.Int(description="Offset for pagination")
    )
    
    # Method 3: Advanced filtering with ordering
    advanced_filtered_customers = graphene.List(
        CustomerType,
        # Include all filter arguments from AdvancedCustomerFilter
        name=graphene.String(),
        email=graphene.String(),
        created_at_gte=graphene.DateTime(),
        created_at_lte=graphene.DateTime(),
        phone_pattern=graphene.String(),
        email_domain=graphene.String(),
        has_phone=graphene.Boolean(),
        ordering=graphene.String(description="Order by field (use '-' for descending, e.g., '-created_at')"),
        limit=graphene.Int(),
        offset=graphene.Int()
    )
    
    # NEW: Product filtering queries
    filtered_products = graphene.List(
        ProductType,
        # Filter arguments for products
        name=graphene.String(description="Filter by product name (case-insensitive partial match)"),
        price_gte=graphene.Float(description="Filter products with price greater than or equal to this value"),
        price_lte=graphene.Float(description="Filter products with price less than or equal to this value"),
        stock=graphene.Int(description="Filter products with exact stock quantity"),
        stock_gte=graphene.Int(description="Filter products with stock greater than or equal to this value"),
        stock_lte=graphene.Int(description="Filter products with stock less than or equal to this value"),
        low_stock=graphene.Int(description="Filter products with stock below this threshold"),
        out_of_stock=graphene.Boolean(description="Filter products that are out of stock"),
        in_stock=graphene.Boolean(description="Filter products that are in stock"),
        price_category=graphene.String(description="Filter by price category (budget, mid-range, premium, luxury)"),
        # Pagination
        limit=graphene.Int(description="Limit the number of results"),
        offset=graphene.Int(description="Offset for pagination")
    )
    
    # NEW: Order filtering queries
    filtered_orders = graphene.List(
        OrderType,
        # Filter arguments for orders
        total_amount_gte=graphene.Float(description="Filter orders with total amount greater than or equal to this value"),
        total_amount_lte=graphene.Float(description="Filter orders with total amount less than or equal to this value"),
        order_date_gte=graphene.DateTime(description="Filter orders placed on or after this date"),
        order_date_lte=graphene.DateTime(description="Filter orders placed on or before this date"),
        customer_name=graphene.String(description="Filter orders by customer's name (case-insensitive partial match)"),
        customer_email=graphene.String(description="Filter orders by customer's email (case-insensitive partial match)"),
        product_name=graphene.String(description="Filter orders by product's name (case-insensitive partial match)"),
        product_id=graphene.ID(description="Filter orders containing a specific product ID (CHALLENGE)"),
        contains_product=graphene.String(description="Filter orders containing a specific product (by ID or name)"),
        customer_id=graphene.ID(description="Filter orders by specific customer ID"),
        high_value_orders=graphene.Boolean(description="Filter high-value orders (> $500)"),
        recent_orders=graphene.Boolean(description="Filter orders placed in the last 30 days"),
        min_products=graphene.Int(description="Filter orders containing at least this many products"),
        order_value_category=graphene.String(description="Filter by order value category (small, medium, large, enterprise)"),
        # Pagination
        limit=graphene.Int(description="Limit the number of results"),
        offset=graphene.Int(description="Offset for pagination")
    )

    def resolve_hello(self, info):
        """Health check resolver that confirms CRM GraphQL is working"""
        return "Hello from CRM GraphQL! System is operational."

    def resolve_crm_stats(self, info):
        """Resolver for CRM statistics"""
        from django.db.models import Sum
        
        total_customers = Customer.objects.count()
        total_orders = Order.objects.count()
        total_revenue = Order.objects.aggregate(total=Sum('total_amount'))['total'] or 0.0
        
        return CRMStatsType(
            total_customers=total_customers,
            total_orders=total_orders,
            total_revenue=float(total_revenue)
        )

    def resolve_all_customers(self, info):
        return Customer.objects.all()

    def resolve_all_products(self, info):
        return Product.objects.all()

    def resolve_all_orders(self, info):
        return Order.objects.all()

    def resolve_customer(self, info, id):
        try:
            return Customer.objects.get(pk=id)
        except Customer.DoesNotExist:
            return None

    def resolve_product(self, info, id):
        try:
            return Product.objects.get(pk=id)
        except Product.DoesNotExist:
            return None

    def resolve_order(self, info, id):
        try:
            return Order.objects.get(pk=id)
        except Order.DoesNotExist:
            return None
    
    # NEW: Resolver for filtered_customers
    def resolve_filtered_customers(self, info, **kwargs):
        """
        Custom resolver that manually applies filters to the Customer queryset.
        
        This demonstrates how to manually implement filtering logic in resolvers.
        """
        queryset = Customer.objects.all()
        
        # Apply the CustomerFilter
        filter_instance = CustomerFilter(kwargs, queryset=queryset)
        filtered_queryset = filter_instance.qs
        
        # Handle pagination
        limit = kwargs.get('limit')
        offset = kwargs.get('offset', 0)
        
        if offset:
            filtered_queryset = filtered_queryset[offset:]
        
        if limit:
            filtered_queryset = filtered_queryset[:limit]
            
        return filtered_queryset
    
    # NEW: Resolver for advanced_filtered_customers  
    def resolve_advanced_filtered_customers(self, info, **kwargs):
        """
        Advanced resolver with ordering and comprehensive filtering.
        
        This shows how to use the AdvancedCustomerFilter with ordering capabilities.
        """
        queryset = Customer.objects.all()
        
        # Apply the AdvancedCustomerFilter
        filter_instance = AdvancedCustomerFilter(kwargs, queryset=queryset)
        filtered_queryset = filter_instance.qs
        
        # Handle manual ordering if not handled by filter
        ordering = kwargs.get('ordering')
        if ordering and not kwargs.get('ordering'):  # If ordering not in filter params
            try:
                filtered_queryset = filtered_queryset.order_by(ordering)
            except Exception:
                # Invalid ordering field, ignore
                pass
        
        # Handle pagination
        limit = kwargs.get('limit')
        offset = kwargs.get('offset', 0)
        
        if offset:
            filtered_queryset = filtered_queryset[offset:]
            
        if limit:
            filtered_queryset = filtered_queryset[:limit]
            
        return filtered_queryset
    
    # NEW: Resolver for filtered_products
    def resolve_filtered_products(self, info, **kwargs):
        """
        Custom resolver for filtering products.
        
        This demonstrates how to apply ProductFilter to the Product queryset.
        """
        queryset = Product.objects.all()
        
        # Apply the ProductFilter
        filter_instance = ProductFilter(kwargs, queryset=queryset)
        filtered_queryset = filter_instance.qs
        
        # Handle pagination
        limit = kwargs.get('limit')
        offset = kwargs.get('offset', 0)
        
        if offset:
            filtered_queryset = filtered_queryset[offset:]
        
        if limit:
            filtered_queryset = filtered_queryset[:limit]
            
        return filtered_queryset
    
    # NEW: Resolver for filtered_orders
    def resolve_filtered_orders(self, info, **kwargs):
        """
        Custom resolver for filtering orders.
        
        This demonstrates how to apply OrderFilter to the Order queryset,
        including complex related field filtering.
        """
        queryset = Order.objects.all()
        
        # Apply the OrderFilter
        filter_instance = OrderFilter(kwargs, queryset=queryset)
        filtered_queryset = filter_instance.qs
        
        # Handle pagination
        limit = kwargs.get('limit')
        offset = kwargs.get('offset', 0)
        
        if offset:
            filtered_queryset = filtered_queryset[offset:]
        
        if limit:
            filtered_queryset = filtered_queryset[:limit]
            
        return filtered_queryset


# Mutation class
class Mutation(graphene.ObjectType):
    #create_customer = CreateCustomer.Field()
    create_customer = CreateCustomerMutation.Field()
    bulk_create_customers = BulkCreateCustomersMutation.Field()
    create_product = CreateProductMutation.Field()
    create_order = CreateOrderMutation.Field()
    update_low_stock_products = UpdateLowStockProducts.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)