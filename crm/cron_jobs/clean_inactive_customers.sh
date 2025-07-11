#!/bin/bash

# Absolute path to the Django project directory
PROJECT_DIR="/path/to/alx-backend-graphql_crm"
MANAGE_PY="$PROJECT_DIR/manage.py"
LOG_FILE="/tmp/customer_cleanup_log.txt"

# Get current timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Run Django command to delete inactive customers (no orders in the last year)
DELETED_COUNT=$(python3 $MANAGE_PY shell -c "
from django.utils import timezone
from datetime import timedelta
from crm.models import Customer, Order
from django.db.models import Count

one_year_ago = timezone.now() - timedelta(days=365)
customers = Customer.objects.annotate(order_count=Count('orders')).filter(order_count=0, created_at__lt=one_year_ago)
count = customers.count()
customers.delete()
print(count)
" 2>&1)

# Log the result with timestamp
echo "[$TIMESTAMP] Deleted $DELETED_COUNT inactive customers" >> $LOG_FILE