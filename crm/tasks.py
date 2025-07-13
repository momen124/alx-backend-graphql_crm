"""
Celery tasks for CRM application
"""
import os
import django
from datetime import datetime
from celery import shared_task

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'graphql_crm.settings')
django.setup()


@shared_task
def generatecrmreport():
    """
    Generate a weekly CRM report using GraphQL queries.
    Fetches total customers, orders, and revenue, then logs to file.
    """
    try:
        # Import GraphQL client
        from gql import gql, Client
        from gql.transport.requests import RequestsHTTPTransport
        
        # Setup GraphQL client
        transport = RequestsHTTPTransport(url="http://localhost:8000/graphql")
        client = Client(transport=transport, fetch_schema_from_transport=True)
        
        # Query for CRM statistics
        query = gql("""
            query GetCRMStats {
                customers {
                    id
                }
                orders {
                    id
                    totalAmount
                }
            }
        """)
        
        result = client.execute(query)
        
        # Calculate statistics
        customers = result.get('customers', [])
        orders = result.get('orders', [])
        
        total_customers = len(customers)
        total_orders = len(orders)
        total_revenue = sum(float(order.get('totalAmount', 0)) for order in orders)
        
        # Get current timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Create report message
        report_message = f"{timestamp} - Report: {total_customers} customers, {total_orders} orders, {total_revenue:.2f} revenue."
        
        # Log the report
        with open('/tmp/crmreportlog.txt', 'a') as log_file:
            log_file.write(report_message + '\n')
        
        print(f"CRM Report generated: {report_message}")
        return report_message
        
    except Exception as e:
        # Log errors
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        error_message = f"{timestamp} - ERROR generating CRM report: {str(e)}"
        
        try:
            with open('/tmp/crmreportlog.txt', 'a') as log_file:
                log_file.write(error_message + '\n')
        except Exception as log_error:
            print(f"Failed to write error log: {log_error}")
        
        print(error_message)
        return error_message


@shared_task
def test_celery():
    """Test task to verify Celery is working"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    message = f"{timestamp} - Celery test task executed successfully"
    
    try:
        with open('/tmp/celery_test_log.txt', 'a') as log_file:
            log_file.write(message + '\n')
    except Exception as e:
        print(f"Failed to write test log: {e}")
    
    print(message)
    return message