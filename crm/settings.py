
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'graphene_django',  # For GraphQL support
    'crm',  # Your app
    'django_crontab',  # For cron jobs
]

# Other settings (e.g., DATABASES, MIDDLEWARE, TEMPLATES) should be here as needed

# Configure Graphene for GraphQL
GRAPHENE = {
    'SCHEMA': 'crm.schema.schema',  # Points to the schema defined in crm/schema.py
}

# Define cron jobs for django-crontab
CRONJOBS = [
    ('*/5 * * * *', 'crm.cron.log_crm_heartbeat'),  # Task 2: Run every 5 minutes
    ('0 */12 * * *', 'crm.cron.update_low_stock'),  # Task 3: Run every 12 hours
]