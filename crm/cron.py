from datetime import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

def update_low_stock():
    # Log file
    log_file = '/tmp/low_stock_updates_log.txt'
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Execute GraphQL mutation
    transport = RequestsHTTPTransport(url='http://localhost:8000/graphql')
    client = Client(transport=transport, fetch_schema_from_transport=True)
    mutation = gql('''
    mutation {
        updateLowStockProducts {
            updatedProducts {
                name
                stock
            }
            message
        }
    }
    ''')
    
    result = client.execute(mutation)
    updated_products = result['updateLowStockProducts']['updatedProducts']
    message = result['updateLowStockProducts']['message']
    
    # Log updates
    with open(log_file, 'a') as f:
        for product in updated_products:
            f.write(f'[{timestamp}] Updated {product["name"]}: new stock {product["stock"]}\n')
        f.write(f'[{timestamp}] {message}\n')