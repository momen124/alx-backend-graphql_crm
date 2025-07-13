"""
Django-crontab job definitions for CRM application
"""
import os
import django
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'graphql_crm.settings')
django.setup()


def log_crm_heartbeat():
    """
    Log a heartbeat message to confirm CRM application health.
    Logs in format: DD/MM/YYYY-HH:MM:SS CRM is alive
    Optionally queries GraphQL hello field to verify endpoint responsiveness.
    """
    # Get current timestamp in required format
    timestamp = datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
    
    # Create heartbeat message
    heartbeat_message = f"{timestamp} CRM is alive"
    
    try:
        # Optional: Test GraphQL endpoint responsiveness
        from gql import gql, Client
        from gql.transport.requests import RequestsHTTPTransport
        
        # Setup GraphQL client
        transport = RequestsHTTPTransport(url="http://localhost:8000/graphql")
        client = Client(transport=transport, fetch_schema_from_transport=True)
        
        # Query the hello field
        query = gql("""
            query {
                hello
            }
        """)
        
        result = client.execute(query)
        hello_response = result.get('hello', 'No response')
        
        # Enhanced message with GraphQL response
        heartbeat_message += f" - GraphQL hello: {hello_response}"
        
    except Exception as e:
        # If GraphQL query fails, log the error but continue with basic heartbeat
        heartbeat_message += f" - GraphQL check failed: {str(e)}"
    
    # Append heartbeat message to log file
    try:
        with open('/tmp/crm_heartbeat_log.txt', 'a') as log_file:
            log_file.write(heartbeat_message + '\n')
    except Exception as e:
        # Fallback logging if file write fails
        print(f"Failed to write heartbeat log: {e}")
        print(heartbeat_message)


def updatelowstock():
    """
    Execute UpdateLowStockProducts mutation via GraphQL endpoint.
    Logs updated product names and new stock levels with timestamp.
    """
    # Get current timestamp
    timestamp = datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
    
    try:
        # Import GraphQL client
        from gql import gql, Client
        from gql.transport.requests import RequestsHTTPTransport
        
        # Setup GraphQL client
        transport = RequestsHTTPTransport(url="http://localhost:8000/graphql")
        client = Client(transport=transport, fetch_schema_from_transport=True)
        
        # First, query products with stock < 10
        query = gql("""
            query {
                lowStockProducts {
                    id
                    name
                    stock
                }
            }
        """)
        
        query_result = client.execute(query)
        low_stock_products = query_result.get('lowStockProducts', [])
        
        # Execute UpdateLowStockProducts mutation to increment stock by 10
        mutation = gql("""
            mutation {
                updateLowStockProducts {
                    success
                    message
                    count
                    updatedProducts {
                        id
                        name
                        stock
                    }
                }
            }
        """)
        
        result = client.execute(mutation)
        mutation_result = result.get('updateLowStockProducts', {})
        
        # Log the results
        log_entries = []
        log_entries.append(f"[{timestamp}] Low stock update executed")
        log_entries.append(f"Success: {mutation_result.get('success', False)}")
        log_entries.append(f"Message: {mutation_result.get('message', 'No message')}")
        log_entries.append(f"Products updated: {mutation_result.get('count', 0)}")
        
        # Log individual product updates
        updated_products = mutation_result.get('updatedProducts', [])
        if updated_products:
            log_entries.append("Updated products:")
            for product in updated_products:
                log_entries.append(f"  - {product['name']}: New stock level = {product['stock']}")
        else:
            log_entries.append("No products were updated")
        
        # Write to log file
        with open('/tmp/lowstockupdates_log.txt', 'a') as log_file:
            for entry in log_entries:
                log_file.write(entry + '\n')
            log_file.write('\n')  # Add blank line for readability
            
    except Exception as e:
        # Log errors
        error_message = f"[{timestamp}] ERROR in update_low_stock: {str(e)}"
        try:
            with open('/tmp/lowstockupdates_log.txt', 'a') as log_file:
                log_file.write(error_message + '\n\n')
        except Exception as log_error:
            print(f"Failed to write error log: {log_error}")
            print(error_message)