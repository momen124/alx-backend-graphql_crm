from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from datetime import datetime, timedelta
import json

# GraphQL endpoint
transport = RequestsHTTPTransport(url='http://localhost:8000/graphql')
client = Client(transport=transport, fetch_schema_from_transport=True)

# Query for orders from the last 7 days
query = gql('''
query {
  orders(orderDate_Gte: "%s") {
    edges {
      node {
        id
        customer {
          email
        }
      }
    }
  }
}
''' % (datetime.now() - timedelta(days=7)).isoformat())

# Execute query
result = client.execute(query)

# Log results
log_file = '/tmp/order_reminders_log.txt'
timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

with open(log_file, 'a') as f:
    for edge in result['orders']['edges']:
        order_id = edge['node']['id']
        email = edge['node']['customer']['email']
        f.write(f'[{timestamp}] Order ID: {order_id}, Customer Email: {email}\n')

print("Order reminders processed!")