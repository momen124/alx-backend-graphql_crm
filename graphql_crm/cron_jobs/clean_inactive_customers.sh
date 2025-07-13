cat > crm/cron_jobs/clean_inactive_customers.sh << 'EOF'
#!/bin/bash

# Get the script directory using BASH_SOURCE
SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"

# Navigate to the Django project directory (two levels up from cron_jobs)
cd "$SCRIPT_DIR/../.."

# Verify we're in the correct directory
pwd

# Change working directory to project root
cwd=$(pwd)

# Get the current timestamp
timestamp=$(date '+%Y-%m-%d %H:%M:%S')

# Execute Django shell command to delete inactive customers
deleted_count=$(python manage.py shell << 'PYTHON_EOF'
import django
from django.utils import timezone
from datetime import timedelta
from crm.models import Customer

# Calculate the date one year ago
one_year_ago = timezone.now() - timedelta(days=365)

# Find customers with no orders in the last year
inactive_customers = Customer.objects.filter(
    orders__isnull=True
) | Customer.objects.exclude(
    orders__order_date__gte=one_year_ago
).distinct()

# Count and delete inactive customers
count = inactive_customers.count()
if count > 0:
    inactive_customers.delete()
    print(f"Deleted {count} inactive customers")
else:
    print("No inactive customers found")
    
print(count)
PYTHON_EOF
)

# Log the result with timestamp
echo "[$timestamp] Deleted $deleted_count inactive customers" >> /tmp/customer_cleanup_log.txt
EOF