from datetime import datetime
import requests
import json
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

def log_crm_heartbeat():
    """Log a heartbeat to confirm CRM application's health"""
    LOG_FILE = "/tmp/crm_heartbeat_log.txt"
    timestamp = datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
    
    heartbeat_message = f"{timestamp} CRM is alive"
    
    # Optionally, query the GraphQL hello field to verify endpoint responsiveness
    try:
        # Setup GraphQL client with CSRF handling
        session = requests.Session()
        get_response = session.get("http://localhost:8000/graphql/")
        csrf_token = session.cookies.get('csrftoken')
        
        headers = {
            'X-CSRFToken': csrf_token,
            'Referer': 'http://localhost:8000/graphql/',
        }
        
        transport = RequestsHTTPTransport(
            url="http://localhost:8000/graphql/",
            use_json=True,
            headers=headers,
            cookies=session.cookies
        )
        
        client = Client(transport=transport, fetch_schema_from_transport=False)
        
        # GraphQL hello query using gql to check endpoint health
        query = gql("{ hello }")
        
        # Execute the query
        result = client.execute(query)
        
        if result and 'hello' in result:
            heartbeat_message += f" - GraphQL endpoint responsive: {result['hello']}"
        else:
            heartbeat_message += " - GraphQL endpoint reachable but no hello response"
            
    except Exception as e:
        heartbeat_message += f" - GraphQL check failed: {str(e)}"
    
    # Append to the log file
    with open(LOG_FILE, "a") as f:
        f.write(f"{heartbeat_message}\n")

def update_low_stock():
    """Update low stock items"""
    LOG_FILE = "/tmp/low_stock_updates_log.txt"
    timestamp = datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
    
    update_low_stock_message = "Low stock update started"

    try:
        # Setup GraphQL client with CSRF handling
        session = requests.Session()
        get_response = session.get("http://localhost:8000/graphql/")
        csrf_token = session.cookies.get('csrftoken')
        
        headers = {
            'X-CSRFToken': csrf_token,
            'Referer': 'http://localhost:8000/graphql/',
        }
        
        transport = RequestsHTTPTransport(
            url="http://localhost:8000/graphql/",
            use_json=True,
            headers=headers,
            cookies=session.cookies
        )
        
        client = Client(transport=transport, fetch_schema_from_transport=False)
        
        # GraphQL mutation to update low stock products
        query = gql("""
            mutation UpdateLowStockProducts {
                updateLowStockProducts {
                    updatedProducts {
                        name
                        stock
                    }
                    successMessage
                    count
                }
            }
        """)
        
        # Execute the mutation
        result = client.execute(query)
        
        if result and 'updateLowStockProducts' in result:
            mutation_result = result['updateLowStockProducts']
            update_low_stock_message = f"Low stock update completed: {mutation_result['successMessage']}"
            
            # Log each updated product
            if mutation_result['updatedProducts']:
                with open(LOG_FILE, "a") as f:
                    f.write(f"{timestamp} {update_low_stock_message}\n")
                    for product in mutation_result['updatedProducts']:
                        f.write(f"{timestamp} Updated product: {product['name']} - New stock: {product['stock']}\n")
                return  # Exit early since we've already written to the file
            else:
                update_low_stock_message = f"Low stock update completed: {mutation_result['successMessage']}"
        else:
            update_low_stock_message = "Low stock update failed: No response from mutation"
            
    except Exception as e:
        update_low_stock_message = f"Low stock update failed: {str(e)}"

    # Append to the log file (for cases where no products were updated or errors occurred)
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} {update_low_stock_message}\n")

def generate_crm_report_task():
    """Generate a CRM report"""
    LOG_FILE = '/tmp/crm_report_log.txt'
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        # Setup GraphQL client with CSRF handling
        session = requests.Session()
        get_response = session.get("http://localhost:8000/graphql/")
        csrf_token = session.cookies.get('csrftoken')
        
        headers = {
            'X-CSRFToken': csrf_token,
            'Referer': 'http://localhost:8000/graphql/',
        }
        
        transport = RequestsHTTPTransport(
            url="http://localhost:8000/graphql/",
            use_json=True,
            headers=headers,
            cookies=session.cookies
        )
        
        client = Client(transport=transport, fetch_schema_from_transport=False)

        # GraphQL query to fetch CRM statistics
        query = gql("""
            query CRMReport {
                crmStats {
                    totalCustomers
                    totalOrders
                    totalRevenue
                }
            }
        """)
        
        # Execute the query
        result = client.execute(query)
        
        if result and 'crmStats' in result:
            stats = result['crmStats']
            total_customers = stats['totalCustomers']
            total_orders = stats['totalOrders']
            total_revenue = stats['totalRevenue']
            
            report_message = f"{timestamp} - Report: {total_customers} customers, {total_orders} orders, ${total_revenue} revenue"
        else:
            report_message = f"{timestamp} - Report generation failed: No response from CRM stats query"
            
    except Exception as e:
        report_message = f"{timestamp} - Report generation failed: {str(e)}"

    # Append to the log file
    with open(LOG_FILE, "a") as f:
        f.write(f"{report_message}\n")


def main():
    """Main function to run cron jobs"""
    log_crm_heartbeat()
    update_low_stock()
    generate_crm_report_task()